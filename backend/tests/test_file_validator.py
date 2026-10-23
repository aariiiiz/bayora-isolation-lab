import pytest
from app.engine.file_validator import validate_uploaded_file, sanitize_filename
from app.core.errors import FileValidationError
from app.engine.artifact_parser import parse_artifact
from app.core.errors import ParsingError

def test_sanitize_filename_prevents_traversal():
    bad_name = "../../../etc/passwd.json"
    cleaned = sanitize_filename(bad_name)
    assert ".." not in cleaned
    assert "/" not in cleaned
    assert cleaned.endswith(".json")

def test_validate_uploaded_file_valid():
    name, ext = validate_uploaded_file("eval_config.yaml", 1024)
    assert name == "eval_config.yaml"
    assert ext == "yaml"

def test_validate_uploaded_file_unsupported_extension():
    with pytest.raises(FileValidationError) as exc:
        validate_uploaded_file("malicious_script.exe", 2048)
    assert "Unsupported file format" in str(exc.value)

def test_validate_uploaded_file_empty():
    with pytest.raises(FileValidationError) as exc:
        validate_uploaded_file("empty.json", 0)
    assert "empty" in str(exc.value)

def test_validate_uploaded_file_oversized():
    with pytest.raises(FileValidationError) as exc:
        validate_uploaded_file("huge.json", 20 * 1024 * 1024)
    assert "exceeds maximum" in str(exc.value)

def test_parse_artifact_json():
    content = b'{"tenant_id": "test-tenant", "enabled": true}'
    parsed = parse_artifact(content, "json")
    assert parsed.structured_data["tenant_id"] == "test-tenant"
    assert len(parsed.raw_lines) == 1

def test_parse_artifact_malformed_json():
    content = b'{"tenant_id": "test-tenant", broken}'
    with pytest.raises(ParsingError):
        parse_artifact(content, "json")
