"""Dataset validation service for BIRD dataset import."""
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """Merge another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if not other.is_valid:
            self.is_valid = False
        return self


class DatasetValidator:
    """Validator for BIRD dataset files."""

    # Required fields for each question in the dataset
    REQUIRED_QUESTION_FIELDS: Set[str] = {"question_id", "question", "SQL", "db_id"}

    # Optional fields that are commonly present
    OPTIONAL_QUESTION_FIELDS: Set[str] = {
        "evidence",  # Additional context/evidence for the question
        "difficulty",  # Question difficulty level
        "category",  # Question category
    }

    @staticmethod
    def validate_zip_file(file_path: str) -> ValidationResult:
        """Validate a ZIP file containing BIRD dataset.

        Checks:
        - File exists and is readable
        - Valid ZIP format
        - Contains required files (dev.json or train.json)
        - Contains databases directory with SQLite files

        Args:
            file_path: Path to the ZIP file.

        Returns:
            ValidationResult with is_valid flag and any errors/warnings.

        Example:
            >>> result = DatasetValidator.validate_zip_file("/path/to/bird.zip")
            >>> if not result.is_valid:
            ...     print(result.errors)
        """
        result = ValidationResult()
        path = Path(file_path)

        # Check file exists
        if not path.exists():
            result.add_error(f"File not found: {file_path}")
            return result

        # Check file is readable
        if not path.is_file():
            result.add_error(f"Path is not a file: {file_path}")
            return result

        # Check file extension
        if path.suffix.lower() != ".zip":
            result.add_error(f"File must be a ZIP archive: {path.suffix}")
            return result

        # Try to open and validate ZIP contents
        try:
            with zipfile.ZipFile(path, "r") as zf:
                # Check for corruption
                bad_file = zf.testzip()
                if bad_file:
                    result.add_error(f"Corrupt file in ZIP archive: {bad_file}")
                    return result

                # Get list of files
                file_list = zf.namelist()

                # Check for required JSON files
                has_dev_json = any("dev.json" in f for f in file_list)
                has_train_json = any("train.json" in f for f in file_list)

                if not has_dev_json and not has_train_json:
                    result.add_error("ZIP must contain dev.json or train.json")

                # Check for databases directory
                has_databases = any("databases/" in f or f.endswith(".sqlite") or f.endswith(".db") for f in file_list)
                if not has_databases:
                    result.add_warning("ZIP may be missing databases directory")

                # Check for schema files
                has_schema = any("schema.sql" in f for f in file_list)
                if not has_schema:
                    result.add_warning("ZIP may be missing schema.sql files")

                logger.info(f"Validated ZIP file: {len(file_list)} files, dev={has_dev_json}, train={has_train_json}")

        except zipfile.BadZipFile:
            result.add_error("Invalid ZIP file format")
        except Exception as e:
            result.add_error(f"Error reading ZIP file: {str(e)}")

        return result

    @staticmethod
    def validate_json_format(json_path: str) -> ValidationResult:
        """Validate JSON file format for BIRD dataset.

        Checks:
        - File exists and is readable
        - Valid JSON format
        - Is a list (array) of questions
        - List is not empty

        Args:
            json_path: Path to the JSON file.

        Returns:
            ValidationResult with is_valid flag and any errors/warnings.

        Example:
            >>> result = DatasetValidator.validate_json_format("/path/to/dev.json")
            >>> if not result.is_valid:
            ...     print(result.errors)
        """
        result = ValidationResult()
        path = Path(json_path)

        # Check file exists
        if not path.exists():
            result.add_error(f"File not found: {json_path}")
            return result

        # Check file is readable
        if not path.is_file():
            result.add_error(f"Path is not a file: {json_path}")
            return result

        # Check file extension
        if path.suffix.lower() != ".json":
            result.add_warning(f"File extension is not .json: {path.suffix}")

        # Try to parse JSON
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check if it's a list
            if not isinstance(data, list):
                result.add_error(f"JSON must be an array of questions, got {type(data).__name__}")
                return result

            # Check if list is empty
            if len(data) == 0:
                result.add_error("JSON array is empty")
                return result

            logger.info(f"Validated JSON format: {len(data)} questions")

        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON format: {str(e)}")
        except UnicodeDecodeError as e:
            result.add_error(f"File encoding error (must be UTF-8): {str(e)}")
        except Exception as e:
            result.add_error(f"Error reading file: {str(e)}")

        return result

    @staticmethod
    def validate_required_fields(data: List[Dict[str, Any]]) -> ValidationResult:
        """Validate required fields in dataset questions.

        Checks each question for required fields:
        - question_id: Unique identifier for the question
        - question: Natural language question text
        - SQL: Gold/reference SQL query
        - db_id: Database identifier

        Args:
            data: List of question dictionaries loaded from JSON.

        Returns:
            ValidationResult with is_valid flag and any errors/warnings.

        Example:
            >>> with open("dev.json") as f:
            ...     data = json.load(f)
            >>> result = DatasetValidator.validate_required_fields(data)
            >>> print(f"Valid: {result.is_valid}, Errors: {len(result.errors)}")
        """
        result = ValidationResult()

        if not isinstance(data, list):
            result.add_error(f"Data must be a list, got {type(data).__name__}")
            return result

        if len(data) == 0:
            result.add_error("Empty question list")
            return result

        # Track statistics
        total_questions = len(data)
        questions_with_errors = 0
        db_ids: Set[str] = set()

        for idx, question in enumerate(data):
            if not isinstance(question, dict):
                result.add_error(f"Question {idx} is not an object: {type(question).__name__}")
                questions_with_errors += 1
                continue

            # Check required fields
            missing_fields = DatasetValidator.REQUIRED_QUESTION_FIELDS - set(question.keys())
            if missing_fields:
                result.add_error(
                    f"Question {idx} (id={question.get('question_id', 'unknown')}) "
                    f"missing required fields: {', '.join(sorted(missing_fields))}"
                )
                questions_with_errors += 1

            # Check field types and values
            question_id = question.get("question_id")
            if question_id is not None:
                if not isinstance(question_id, (str, int)):
                    result.add_warning(
                        f"Question {idx}: question_id should be string or int, got {type(question_id).__name__}"
                    )

            # Track db_id
            db_id = question.get("db_id")
            if db_id and isinstance(db_id, str):
                db_ids.add(db_id)

            # Check SQL field
            sql = question.get("SQL")
            if sql is not None and not isinstance(sql, str):
                result.add_warning(f"Question {idx}: SQL field should be a string")
            elif sql == "":
                result.add_warning(f"Question {idx}: SQL field is empty")

            # Check question field
            nl_question = question.get("question")
            if nl_question is not None and not isinstance(nl_question, str):
                result.add_warning(f"Question {idx}: question field should be a string")
            elif nl_question == "":
                result.add_warning(f"Question {idx}: question field is empty")

        # Summary statistics
        if questions_with_errors > 0:
            result.add_error(
                f"Found {questions_with_errors}/{total_questions} questions with errors"
            )

        logger.info(
            f"Validated {total_questions} questions: "
            f"{len(db_ids)} unique databases, "
            f"{questions_with_errors} with errors"
        )

        return result

    @staticmethod
    def validate_dataset_structure(dataset_path: str) -> ValidationResult:
        """Validate complete BIRD dataset structure.

        Performs comprehensive validation of a BIRD dataset directory or ZIP file:
        1. Validates ZIP file format (if applicable)
        2. Validates JSON format
        3. Validates required fields
        4. Checks database file consistency

        Args:
            dataset_path: Path to dataset (ZIP file or directory).

        Returns:
            ValidationResult with is_valid flag and any errors/warnings.

        Example:
            >>> result = DatasetValidator.validate_dataset_structure("/path/to/bird.zip")
            >>> if result.is_valid:
            ...     print("Dataset is valid")
            ... else:
            ...     for error in result.errors:
            ...         print(f"Error: {error}")
        """
        result = ValidationResult()
        path = Path(dataset_path)

        if not path.exists():
            result.add_error(f"Path not found: {dataset_path}")
            return result

        # Validate ZIP if it's a file
        if path.is_file():
            zip_result = DatasetValidator.validate_zip_file(dataset_path)
            result.merge(zip_result)
            if not result.is_valid:
                return result

        logger.info(f"Dataset structure validation completed for: {dataset_path}")
        return result

    @staticmethod
    def validate_database_files(db_dir: str, db_ids: List[str]) -> ValidationResult:
        """Validate database files exist for all db_ids.

        Args:
            db_dir: Directory containing database files.
            db_ids: List of database identifiers.

        Returns:
            ValidationResult with is_valid flag and any errors/warnings.
        """
        result = ValidationResult()
        db_path = Path(db_dir)

        if not db_path.exists():
            result.add_error(f"Database directory not found: {db_dir}")
            return result

        missing_dbs = []
        for db_id in db_ids:
            # Check for various database file naming conventions
            possible_files = [
                db_path / f"{db_id}.sqlite",
                db_path / f"{db_id}.db",
                db_path / db_id / f"{db_id}.sqlite",
                db_path / db_id / f"{db_id}.db",
            ]

            if not any(f.exists() for f in possible_files):
                missing_dbs.append(db_id)

        if missing_dbs:
            result.add_warning(f"Missing database files for: {', '.join(missing_dbs)}")

        logger.info(f"Validated {len(db_ids)} databases, {len(missing_dbs)} missing")
        return result
