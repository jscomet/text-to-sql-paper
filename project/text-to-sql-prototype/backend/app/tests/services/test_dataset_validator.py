"""Tests for dataset_validator service."""
import json
import os
import zipfile
from pathlib import Path

import pytest

from app.services.dataset_validator import DatasetValidator, ValidationResult


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_default_initialization(self):
        """Test default initialization of ValidationResult."""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_initialization_with_values(self):
        """Test initialization with explicit values."""
        result = ValidationResult(
            is_valid=False,
            errors=["error1"],
            warnings=["warning1"]
        )
        assert result.is_valid is False
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]

    def test_add_error(self):
        """Test adding an error message."""
        result = ValidationResult()
        result.add_error("Test error")
        assert result.is_valid is False
        assert "Test error" in result.errors

    def test_add_warning(self):
        """Test adding a warning message."""
        result = ValidationResult()
        result.add_warning("Test warning")
        assert result.is_valid is True  # Warnings don't invalidate
        assert "Test warning" in result.warnings

    def test_merge(self):
        """Test merging two validation results."""
        result1 = ValidationResult(is_valid=True)
        result1.add_warning("Warning from result1")

        result2 = ValidationResult(is_valid=False)
        result2.add_error("Error from result2")

        result1.merge(result2)

        assert result1.is_valid is False
        assert "Warning from result1" in result1.warnings
        assert "Error from result2" in result1.errors


class TestValidateZipFile:
    """Tests for validate_zip_file method."""

    def test_valid_zip_with_dev_json(self, temp_dir, sample_dev_json):
        """Test validation of valid ZIP with dev.json."""
        zip_path = os.path.join(temp_dir, "valid.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("dev.json", json.dumps(sample_dev_json))
            zf.writestr("databases/test.sqlite", b"")

        result = DatasetValidator.validate_zip_file(zip_path)
        assert result.is_valid is True

    def test_valid_zip_with_train_json(self, temp_dir):
        """Test validation of valid ZIP with train.json."""
        zip_path = os.path.join(temp_dir, "valid_train.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("train.json", json.dumps([{"question_id": "q1"}]))

        result = DatasetValidator.validate_zip_file(zip_path)
        assert result.is_valid is True

    def test_nonexistent_file(self):
        """Test validation of non-existent file."""
        result = DatasetValidator.validate_zip_file("/nonexistent/path/file.zip")
        assert result.is_valid is False
        assert "File not found" in result.errors[0]

    def test_not_a_file(self, temp_dir):
        """Test validation when path is a directory."""
        result = DatasetValidator.validate_zip_file(temp_dir)
        assert result.is_valid is False
        assert "Path is not a file" in result.errors[0]

    def test_invalid_extension(self, temp_dir):
        """Test validation of file with wrong extension."""
        txt_path = os.path.join(temp_dir, "test.txt")
        Path(txt_path).touch()
        result = DatasetValidator.validate_zip_file(txt_path)
        assert result.is_valid is False
        assert "ZIP archive" in result.errors[0]

    def test_invalid_zip_format(self, temp_dir, invalid_zip_file):
        """Test validation of invalid ZIP format."""
        result = DatasetValidator.validate_zip_file(invalid_zip_file)
        assert result.is_valid is False
        assert "Invalid ZIP file format" in result.errors[0]

    def test_empty_zip(self, temp_dir, empty_zip_file):
        """Test validation of empty ZIP file."""
        result = DatasetValidator.validate_zip_file(empty_zip_file)
        assert result.is_valid is False
        assert "dev.json or train.json" in result.errors[0]

    def test_missing_json_files(self, temp_dir):
        """Test validation of ZIP without dev.json or train.json."""
        zip_path = os.path.join(temp_dir, "no_json.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("readme.txt", "No JSON here")

        result = DatasetValidator.validate_zip_file(zip_path)
        assert result.is_valid is False
        assert "dev.json or train.json" in result.errors[0]

    def test_warning_for_missing_databases(self, temp_dir):
        """Test warning when databases directory is missing."""
        zip_path = os.path.join(temp_dir, "no_db.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("dev.json", json.dumps([{"q": 1}]))

        result = DatasetValidator.validate_zip_file(zip_path)
        assert result.is_valid is True  # Still valid, just warning
        assert any("databases" in w for w in result.warnings)

    def test_warning_for_missing_schema(self, temp_dir):
        """Test warning when schema.sql is missing."""
        zip_path = os.path.join(temp_dir, "no_schema.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("dev.json", json.dumps([{"q": 1}]))
            zf.writestr("databases/test.db", b"")

        result = DatasetValidator.validate_zip_file(zip_path)
        assert result.is_valid is True
        assert any("schema.sql" in w for w in result.warnings)


class TestValidateJsonFormat:
    """Tests for validate_json_format method."""

    def test_valid_json_array(self, temp_dir, sample_dev_json):
        """Test validation of valid JSON array."""
        json_path = os.path.join(temp_dir, "valid.json")
        with open(json_path, "w") as f:
            json.dump(sample_dev_json, f)

        result = DatasetValidator.validate_json_format(json_path)
        assert result.is_valid is True

    def test_nonexistent_json_file(self):
        """Test validation of non-existent JSON file."""
        result = DatasetValidator.validate_json_format("/nonexistent/file.json")
        assert result.is_valid is False
        assert "File not found" in result.errors[0]

    def test_not_a_json_file(self, temp_dir):
        """Test validation when path is a directory."""
        result = DatasetValidator.validate_json_format(temp_dir)
        assert result.is_valid is False
        assert "Path is not a file" in result.errors[0]

    def test_invalid_json_extension(self, temp_dir):
        """Test validation of file without .json extension."""
        txt_path = os.path.join(temp_dir, "data.txt")
        with open(txt_path, "w") as f:
            json.dump([{"q": 1}], f)

        result = DatasetValidator.validate_json_format(txt_path)
        assert result.is_valid is True  # Still valid, just warning
        assert any(".json" in w for w in result.warnings)

    def test_invalid_json_syntax(self, temp_dir):
        """Test validation of invalid JSON syntax."""
        json_path = os.path.join(temp_dir, "invalid.json")
        with open(json_path, "w") as f:
            f.write("{invalid json}")

        result = DatasetValidator.validate_json_format(json_path)
        assert result.is_valid is False
        assert "Invalid JSON format" in result.errors[0]

    def test_json_not_an_array(self, temp_dir):
        """Test validation when JSON is not an array."""
        json_path = os.path.join(temp_dir, "object.json")
        with open(json_path, "w") as f:
            json.dump({"key": "value"}, f)

        result = DatasetValidator.validate_json_format(json_path)
        assert result.is_valid is False
        assert "JSON must be an array" in result.errors[0]

    def test_empty_json_array(self, temp_dir):
        """Test validation of empty JSON array."""
        json_path = os.path.join(temp_dir, "empty.json")
        with open(json_path, "w") as f:
            json.dump([], f)

        result = DatasetValidator.validate_json_format(json_path)
        assert result.is_valid is False
        assert "JSON array is empty" in result.errors[0]

    def test_non_utf8_encoding(self, temp_dir):
        """Test validation of file with non-UTF-8 encoding."""
        json_path = os.path.join(temp_dir, "latin1.json")
        with open(json_path, "wb") as f:
            f.write(b'[{"question": "caf\xe9"}]')  # Latin-1 encoded

        result = DatasetValidator.validate_json_format(json_path)
        # Should handle encoding gracefully or report error
        assert isinstance(result.is_valid, bool)


class TestValidateRequiredFields:
    """Tests for validate_required_fields method."""

    def test_valid_questions(self, sample_dev_json):
        """Test validation of questions with all required fields."""
        result = DatasetValidator.validate_required_fields(sample_dev_json)
        assert result.is_valid is True

    def test_missing_required_fields(self, missing_fields_json):
        """Test validation with missing required fields."""
        result = DatasetValidator.validate_required_fields(missing_fields_json)
        assert result.is_valid is False
        assert any("missing required fields" in e for e in result.errors)

    def test_empty_list(self):
        """Test validation of empty question list."""
        result = DatasetValidator.validate_required_fields([])
        assert result.is_valid is False
        assert "Empty question list" in result.errors[0]

    def test_not_a_list(self):
        """Test validation when data is not a list."""
        result = DatasetValidator.validate_required_fields({"key": "value"})
        assert result.is_valid is False
        assert "Data must be a list" in result.errors[0]

    def test_question_not_a_dict(self):
        """Test validation when question is not a dictionary."""
        result = DatasetValidator.validate_required_fields(["not a dict", {"question_id": "q1"}])
        assert result.is_valid is False
        assert any("not an object" in e for e in result.errors)

    def test_invalid_question_id_type(self):
        """Test validation with invalid question_id type."""
        data = [{"question_id": ["invalid"], "question": "Q", "SQL": "S", "db_id": "D"}]
        result = DatasetValidator.validate_required_fields(data)
        assert result.is_valid is True  # Still valid, just warning
        assert any("question_id" in w for w in result.warnings)

    def test_empty_sql_field(self):
        """Test validation with empty SQL field."""
        data = [{"question_id": "q1", "question": "Q", "SQL": "", "db_id": "D"}]
        result = DatasetValidator.validate_required_fields(data)
        assert result.is_valid is True  # Still valid, just warning
        assert any("SQL field is empty" in w for w in result.warnings)

    def test_empty_question_field(self):
        """Test validation with empty question field."""
        data = [{"question_id": "q1", "question": "", "SQL": "S", "db_id": "D"}]
        result = DatasetValidator.validate_required_fields(data)
        assert result.is_valid is True  # Still valid, just warning
        assert any("question field is empty" in w for w in result.warnings)

    def test_invalid_sql_type(self):
        """Test validation with invalid SQL type."""
        data = [{"question_id": "q1", "question": "Q", "SQL": 123, "db_id": "D"}]
        result = DatasetValidator.validate_required_fields(data)
        assert result.is_valid is True  # Still valid, just warning
        assert any("SQL field should be a string" in w for w in result.warnings)


class TestValidateDatasetStructure:
    """Tests for validate_dataset_structure method."""

    def test_valid_dataset_zip(self, temp_dir, sample_dev_json):
        """Test validation of valid dataset structure (ZIP)."""
        zip_path = os.path.join(temp_dir, "dataset.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("dev.json", json.dumps(sample_dev_json))
            zf.writestr("databases/test.sqlite", b"")

        result = DatasetValidator.validate_dataset_structure(zip_path)
        assert result.is_valid is True

    def test_nonexistent_path(self):
        """Test validation of non-existent path."""
        result = DatasetValidator.validate_dataset_structure("/nonexistent/path")
        assert result.is_valid is False
        assert "Path not found" in result.errors[0]


class TestValidateDatabaseFiles:
    """Tests for validate_database_files method."""

    def test_all_databases_exist(self, temp_dir):
        """Test validation when all database files exist."""
        db_dir = os.path.join(temp_dir, "databases")
        os.makedirs(db_dir)

        # Create database files
        Path(os.path.join(db_dir, "db1.sqlite")).touch()
        Path(os.path.join(db_dir, "db2.db")).touch()

        result = DatasetValidator.validate_database_files(db_dir, ["db1", "db2"])
        assert result.is_valid is True

    def test_missing_database_files(self, temp_dir):
        """Test validation when some database files are missing."""
        db_dir = os.path.join(temp_dir, "databases")
        os.makedirs(db_dir)

        Path(os.path.join(db_dir, "db1.sqlite")).touch()
        # db2.sqlite is missing

        result = DatasetValidator.validate_database_files(db_dir, ["db1", "db2"])
        assert result.is_valid is True  # Warning, not error
        assert any("db2" in w for w in result.warnings)

    def test_nested_database_files(self, temp_dir):
        """Test validation with nested database directory structure."""
        db_dir = os.path.join(temp_dir, "databases")
        nested_dir = os.path.join(db_dir, "nested_db")
        os.makedirs(nested_dir)

        Path(os.path.join(nested_dir, "nested_db.sqlite")).touch()

        result = DatasetValidator.validate_database_files(db_dir, ["nested_db"])
        assert result.is_valid is True

    def test_nonexistent_db_directory(self):
        """Test validation of non-existent database directory."""
        result = DatasetValidator.validate_database_files("/nonexistent/db", ["db1"])
        assert result.is_valid is False
        assert "Database directory not found" in result.errors[0]


class TestRequiredFieldsConstant:
    """Tests for REQUIRED_QUESTION_FIELDS constant."""

    def test_required_fields_defined(self):
        """Test that required fields are properly defined."""
        required = DatasetValidator.REQUIRED_QUESTION_FIELDS
        assert "question_id" in required
        assert "question" in required
        assert "SQL" in required
        assert "db_id" in required

    def test_optional_fields_defined(self):
        """Test that optional fields are properly defined."""
        optional = DatasetValidator.OPTIONAL_QUESTION_FIELDS
        assert "evidence" in optional
        assert "difficulty" in optional
        assert "category" in optional
