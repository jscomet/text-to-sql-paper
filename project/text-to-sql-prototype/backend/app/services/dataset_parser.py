"""Dataset parser service for BIRD dataset import."""
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DatasetQuestion:
    """Represents a single question from the BIRD dataset.

    Attributes:
        question_id: Unique identifier for the question.
        nl_question: Natural language question text.
        gold_sql: Gold/reference SQL query.
        db_id: Database identifier.
        evidence: Optional evidence/context for the question.
        difficulty: Optional difficulty level.
        category: Optional question category.
    """
    question_id: str
    nl_question: str
    gold_sql: str
    db_id: str
    evidence: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "question_id": self.question_id,
            "question": self.nl_question,
            "SQL": self.gold_sql,
            "db_id": self.db_id,
            "evidence": self.evidence,
            "difficulty": self.difficulty,
            "category": self.category,
        }


class DatasetParser:
    """Parser for BIRD dataset files."""

    @staticmethod
    def parse_dev_json(file_path: str) -> List[DatasetQuestion]:
        """Parse dev.json file and return list of questions.

        Args:
            file_path: Path to the dev.json file.

        Returns:
            List of DatasetQuestion objects.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file contains invalid JSON.

        Example:
            >>> questions = DatasetParser.parse_dev_json("/path/to/dev.json")
            >>> print(f"Loaded {len(questions)} questions")
            >>> print(f"First question: {questions[0].nl_question}")
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array, got {type(data).__name__}")

        questions: List[DatasetQuestion] = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                logger.warning(f"Skipping item {idx}: not a dictionary")
                continue

            try:
                question = DatasetQuestion(
                    question_id=str(item.get("question_id", f"q{idx}")),
                    nl_question=item.get("question", ""),
                    gold_sql=item.get("SQL", ""),
                    db_id=item.get("db_id", ""),
                    evidence=item.get("evidence"),
                    difficulty=item.get("difficulty"),
                    category=item.get("category"),
                )
                questions.append(question)
            except Exception as e:
                logger.warning(f"Error parsing question {idx}: {e}")
                continue

        logger.info(f"Parsed {len(questions)} questions from {file_path}")
        return questions

    @staticmethod
    def extract_db_ids(questions: List[DatasetQuestion]) -> List[str]:
        """Extract unique database IDs from questions.

        Args:
            questions: List of DatasetQuestion objects.

        Returns:
            Sorted list of unique database IDs.

        Example:
            >>> questions = DatasetParser.parse_dev_json("dev.json")
            >>> db_ids = DatasetParser.extract_db_ids(questions)
            >>> print(f"Databases: {db_ids}")
            ['california_schools', 'financial', 'sports']
        """
        db_ids: Set[str] = set()
        for question in questions:
            if question.db_id:
                db_ids.add(question.db_id)

        result = sorted(list(db_ids))
        logger.info(f"Extracted {len(result)} unique database IDs")
        return result

    @staticmethod
    def count_questions_by_db(questions: List[DatasetQuestion]) -> Dict[str, int]:
        """Count questions per database.

        Args:
            questions: List of DatasetQuestion objects.

        Returns:
            Dictionary mapping db_id to question count.

        Example:
            >>> questions = DatasetParser.parse_dev_json("dev.json")
            >>> counts = DatasetParser.count_questions_by_db(questions)
            >>> for db_id, count in counts.items():
            ...     print(f"{db_id}: {count} questions")
            california_schools: 150 questions
            financial: 130 questions
        """
        counts: Dict[str, int] = {}
        for question in questions:
            db_id = question.db_id
            if db_id:
                counts[db_id] = counts.get(db_id, 0) + 1

        # Sort by db_id for consistent output
        result = dict(sorted(counts.items()))
        logger.info(f"Counted questions for {len(result)} databases")
        return result

    @staticmethod
    def group_questions_by_db(questions: List[DatasetQuestion]) -> Dict[str, List[DatasetQuestion]]:
        """Group questions by database ID.

        Args:
            questions: List of DatasetQuestion objects.

        Returns:
            Dictionary mapping db_id to list of questions.

        Example:
            >>> questions = DatasetParser.parse_dev_json("dev.json")
            >>> grouped = DatasetParser.group_questions_by_db(questions)
            >>> for db_id, db_questions in grouped.items():
            ...     print(f"{db_id}: {len(db_questions)} questions")
        """
        grouped: Dict[str, List[DatasetQuestion]] = {}
        for question in questions:
            db_id = question.db_id
            if db_id:
                if db_id not in grouped:
                    grouped[db_id] = []
                grouped[db_id].append(question)

        # Sort by db_id for consistent output
        result = dict(sorted(grouped.items()))
        logger.info(f"Grouped questions into {len(result)} databases")
        return result

    @staticmethod
    def parse_from_zip(zip_path: str, json_filename: str = "dev.json") -> List[DatasetQuestion]:
        """Parse questions directly from a ZIP file.

        Args:
            zip_path: Path to the ZIP file.
            json_filename: Name of the JSON file to parse (default: dev.json).

        Returns:
            List of DatasetQuestion objects.

        Raises:
            FileNotFoundError: If the ZIP file does not exist.
            zipfile.BadZipFile: If the file is not a valid ZIP.
            ValueError: If the JSON file is not found in the ZIP.

        Example:
            >>> questions = DatasetParser.parse_from_zip("/path/to/bird.zip", "dev.json")
            >>> print(f"Loaded {len(questions)} questions from ZIP")
        """
        path = Path(zip_path)

        if not path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        with zipfile.ZipFile(path, "r") as zf:
            # Find the JSON file in the ZIP
            json_files = [f for f in zf.namelist() if f.endswith(json_filename)]

            if not json_files:
                raise ValueError(f"{json_filename} not found in ZIP archive")

            # Use the first match
            json_file = json_files[0]
            logger.info(f"Found {json_filename} in ZIP at: {json_file}")

            # Read and parse the JSON
            with zf.open(json_file) as f:
                data = json.load(f)

        if not isinstance(data, list):
            raise ValueError(f"Expected JSON array, got {type(data).__name__}")

        questions: List[DatasetQuestion] = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                logger.warning(f"Skipping item {idx}: not a dictionary")
                continue

            try:
                question = DatasetQuestion(
                    question_id=str(item.get("question_id", f"q{idx}")),
                    nl_question=item.get("question", ""),
                    gold_sql=item.get("SQL", ""),
                    db_id=item.get("db_id", ""),
                    evidence=item.get("evidence"),
                    difficulty=item.get("difficulty"),
                    category=item.get("category"),
                )
                questions.append(question)
            except Exception as e:
                logger.warning(f"Error parsing question {idx}: {e}")
                continue

        logger.info(f"Parsed {len(questions)} questions from ZIP: {zip_path}")
        return questions

    @staticmethod
    def extract_db_info(dataset_path: str) -> Dict[str, Any]:
        """Extract comprehensive database information from dataset.

        Args:
            dataset_path: Path to dev.json file or ZIP file.

        Returns:
            Dictionary containing:
                - total_questions: Total number of questions
                - db_count: Number of unique databases
                - db_ids: List of database IDs
                - questions_per_db: Dict of question counts per database
                - difficulties: Dict of question counts per difficulty level
                - categories: Dict of question counts per category

        Example:
            >>> info = DatasetParser.extract_db_info("/path/to/dev.json")
            >>> print(f"Total: {info['total_questions']} questions from {info['db_count']} DBs")
        """
        path = Path(dataset_path)

        # Parse questions from file or ZIP
        if path.suffix.lower() == ".zip":
            questions = DatasetParser.parse_from_zip(dataset_path)
        else:
            questions = DatasetParser.parse_dev_json(dataset_path)

        db_ids = DatasetParser.extract_db_ids(questions)
        questions_per_db = DatasetParser.count_questions_by_db(questions)

        # Analyze difficulties
        difficulties: Dict[str, int] = {}
        categories: Dict[str, int] = {}

        for q in questions:
            if q.difficulty:
                difficulties[q.difficulty] = difficulties.get(q.difficulty, 0) + 1
            if q.category:
                categories[q.category] = categories.get(q.category, 0) + 1

        result = {
            "total_questions": len(questions),
            "db_count": len(db_ids),
            "db_ids": db_ids,
            "questions_per_db": questions_per_db,
            "difficulties": difficulties,
            "categories": categories,
        }

        logger.info(
            f"Extracted DB info: {result['total_questions']} questions, "
            f"{result['db_count']} databases"
        )
        return result

    @staticmethod
    def validate_and_parse(file_path: str) -> Tuple[List[DatasetQuestion], List[str]]:
        """Validate and parse a dataset file in one operation.

        Args:
            file_path: Path to the dataset file (JSON or ZIP).

        Returns:
            Tuple of (questions, errors).
            If validation fails, questions will be empty and errors will contain messages.

        Example:
            >>> questions, errors = DatasetParser.validate_and_parse("/path/to/dev.json")
            >>> if errors:
            ...     print(f"Validation failed: {errors}")
            ... else:
            ...     print(f"Loaded {len(questions)} questions")
        """
        from app.services.dataset_validator import DatasetValidator

        errors: List[str] = []
        path = Path(file_path)

        try:
            if path.suffix.lower() == ".zip":
                # Validate ZIP
                result = DatasetValidator.validate_zip_file(file_path)
                if not result.is_valid:
                    errors.extend(result.errors)
                    return [], errors
                questions = DatasetParser.parse_from_zip(file_path)
            else:
                # Validate JSON
                result = DatasetValidator.validate_json_format(file_path)
                if not result.is_valid:
                    errors.extend(result.errors)
                    return [], errors
                questions = DatasetParser.parse_dev_json(file_path)

            # Validate required fields
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            result = DatasetValidator.validate_required_fields(data)
            if not result.is_valid:
                errors.extend(result.errors)

            return questions, errors

        except Exception as e:
            errors.append(f"Error parsing file: {str(e)}")
            return [], errors
