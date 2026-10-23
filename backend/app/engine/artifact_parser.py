import json
import csv
import io
import yaml
from typing import Any, Dict, List, Tuple
from app.core.errors import ParsingError

class ParsedArtifact:
    def __init__(self, raw_text: str, artifact_type: str, structured_data: Any, raw_lines: List[str]):
        self.raw_text = raw_text
        self.artifact_type = artifact_type
        self.structured_data = structured_data
        self.raw_lines = raw_lines

def parse_artifact(raw_bytes: bytes, artifact_type: str) -> ParsedArtifact:
    """
    Safely parses byte content into text and structured data based on the artifact type.
    Never executes uploaded content. Safe YAML loader used.
    """
    try:
        raw_text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            raw_text = raw_bytes.decode("latin-1")
        except Exception as e:
            raise ParsingError(f"File encoding could not be decoded as UTF-8 or Latin-1: {str(e)}")

    raw_lines = raw_text.splitlines()
    structured_data = None

    if artifact_type == "json":
        try:
            structured_data = json.loads(raw_text)
        except json.JSONDecodeError as jde:
            raise ParsingError(
                f"Invalid JSON syntax at line {jde.lineno}, column {jde.colno}: {jde.msg}",
                details={"line": jde.lineno, "col": jde.colno}
            )

    elif artifact_type == "jsonl":
        structured_data = []
        for line_idx, line in enumerate(raw_lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                parsed_line = json.loads(stripped)
                structured_data.append({"line_number": line_idx, "data": parsed_line})
            except json.JSONDecodeError as jde:
                raise ParsingError(
                    f"Invalid JSONL record at line {line_idx}: {jde.msg}",
                    details={"line": line_idx}
                )

    elif artifact_type == "csv":
        try:
            reader = csv.DictReader(io.StringIO(raw_text))
            structured_data = []
            for row_idx, row in enumerate(reader, start=2): # header is row 1
                structured_data.append({"row_number": row_idx, "data": dict(row)})
        except Exception as e:
            raise ParsingError(f"Failed to parse CSV artifact: {str(e)}")

    elif artifact_type in ("yaml", "yml"):
        try:
            # Strictly use yaml.safe_load to avoid arbitrary object instantiation vulnerabilities
            structured_data = yaml.safe_load(raw_text)
        except yaml.YAMLError as ye:
            problem_mark = getattr(ye, "problem_mark", None)
            line = problem_mark.line + 1 if problem_mark else None
            raise ParsingError(
                f"Invalid YAML structure: {str(ye)}",
                details={"line": line}
            )

    elif artifact_type == "txt":
        # Raw text / logs parsed into indexed lines
        structured_data = [{"line_number": idx, "text": line} for idx, line in enumerate(raw_lines, start=1)]

    else:
        raise ParsingError(f"Unsupported artifact type for parsing: {artifact_type}")

    return ParsedArtifact(
        raw_text=raw_text,
        artifact_type=artifact_type,
        structured_data=structured_data,
        raw_lines=raw_lines
    )
