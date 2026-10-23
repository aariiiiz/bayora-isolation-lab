import re
import base64
from typing import List, Dict, Any
from app.engine.artifact_parser import ParsedArtifact

# Heuristic screening patterns
OVERRIDE_PATTERNS = [
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|guidelines)", "Direct instruction override attempt"),
    (r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|directions)", "Direct instruction disregard attempt"),
    (r"you\s+are\s+now\s+(in\s+)?(dan\s+mode|unfiltered|jailbroken|godmode|developer\s+mode)", "Persona jailbreak / DAN mode activation"),
    (r"system\s+(override|prompt\s+reset|bypass)", "System instruction reset command"),
    (r"forget\s+(everything\s+)?(you\s+were\s+told|all\s+instructions)", "Memory erasure / context reset directive"),
    (r"act\s+as\s+an\s+unrestricted\s+ai", "Uncensored agent coercion")
]

EXTRACTION_PATTERNS = [
    (r"(reveal|print|repeat|output|show)\s+(your\s+)?(system\s+prompt|initial\s+instructions|hidden\s+rules)", "System prompt extraction probe"),
    (r"what\s+(is|are)\s+the\s+words\s+(above|prior\s+to\s+this)", "Context boundary extraction probe"),
    (r"output\s+the\s+above\s+text\s+verbatim", "Verbatim instruction extraction probe")
]

DELIMITER_PATTERNS = [
    (r"<\|im_start\|>", "ChatML delimiter injection (<|im_start|>)"),
    (r"<\|im_end\|>", "ChatML delimiter injection (<|im_end|>)"),
    (r"\[INST\]", "Llama instruction tag injection ([INST])"),
    (r"\[/INST\]", "Llama instruction tag injection ([/INST])"),
    (r"###\s*(System|Instruction|Assistant):", "Markdown pseudo-header injection"),
    (r"(Human|Assistant):\s*\n", "Dialog turn spoofing")
]

TOOL_ABUSE_PATTERNS = [
    (r"(curl|wget)\s+https?://[^\s]+(\s*\|\s*(sh|bash))?", "Arbitrary remote fetch / pipe to shell"),
    (r"(rm\s+-rf|del\s+/f|format\s+c:)", "Destructive file system command injection"),
    (r"(select\s+.+\s+from\s+.+\s+where|drop\s+table|;\s*--)", "SQL injection payload pattern"),
    (r"(os\.system|subprocess\.Popen|eval\s*\(|exec\s*\()", "Arbitrary code execution primitive")
]

def check_prompt_security(parsed: ParsedArtifact, profile: str = "strict", active_policies: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Operation C: Prompt-injection and adversarial input review.
    Inspects prompt datasets for suspicious instruction-override patterns and risky inputs.
    Labels results as heuristic screening, not proof of successful runtime exploitation.
    """
    findings = []
    active_policies = active_policies or {}

    def is_rule_enabled(rule_id: str) -> bool:
        if rule_id in active_policies:
            return active_policies[rule_id].get("is_enabled", True)
        return True

    # Extract text items with line index
    items = []
    raw_lines = parsed.raw_lines

    if parsed.artifact_type in ("jsonl", "csv"):
        for entry in parsed.structured_data:
            idx = entry.get("line_number") or entry.get("row_number", 1)
            row_dict = entry.get("data", {})
            # extract string fields
            for k, v in row_dict.items():
                if isinstance(v, str):
                    items.append((idx, f"{k}: {v}", v))
    elif parsed.artifact_type == "json":
        def extract_strings(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    extract_strings(v, f"{path}.{k}" if path else k)
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    extract_strings(v, f"{path}[{i}]")
            elif isinstance(obj, str):
                items.append((1, path, obj))
        extract_strings(parsed.structured_data)
    else: # txt or yaml
        for idx, line in enumerate(raw_lines, 1):
            if line.strip():
                items.append((idx, f"line {idx}", line))

    for line_no, context_label, text in items:
        # 1. PRM-001: Instruction Override Patterns
        if is_rule_enabled("PRM-001"):
            for pattern, pattern_desc in OVERRIDE_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    findings.append({
                        "rule_id": "PRM-001",
                        "title": f"Adversarial Instruction Override Detected ({pattern_desc})",
                        "severity": "HIGH",
                        "description": f"Heuristic screening flagged an instruction override attempt in {context_label}. The input instructs the AI model to disregard safety constraints.",
                        "evidence": {
                            "matched_phrase": match.group(0),
                            "line_number": line_no,
                            "excerpt": text[:200]
                        },
                        "remediation": "Apply prompt isolation (e.g. structured delimiters, dual-LLM verification, or dedicated input filtering). Do not interpolate untrusted input directly into privileged system instructions.",
                        "detection_method": "regex_heuristic_screening",
                        "confidence": "HIGH",
                        "limitations": "Heuristic pattern match. Does not simulate LLM response or confirm successful model compliance."
                    })
                    break

        # 2. PRM-002: System Prompt Extraction
        if is_rule_enabled("PRM-002"):
            for pattern, pattern_desc in EXTRACTION_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    findings.append({
                        "rule_id": "PRM-002",
                        "title": f"System Prompt Extraction Probe Detected",
                        "severity": "MEDIUM",
                        "description": f"Heuristic screening flagged a prompt extraction probe in {context_label} attempting to leak confidential system instructions.",
                        "evidence": {
                            "matched_phrase": match.group(0),
                            "line_number": line_no,
                            "excerpt": text[:200]
                        },
                        "remediation": "Instruct model never to recite its system prompt, and post-filter model outputs for confidential instruction fragments.",
                        "detection_method": "regex_heuristic_screening",
                        "confidence": "HIGH",
                        "limitations": "Screening flags intent. Resistance depends on model system prompt steering."
                    })
                    break

        # 3. PRM-003: Obfuscated or Base64 Encoded Payloads
        if is_rule_enabled("PRM-003"):
            # Check for base64 blocks > 32 chars
            b64_matches = re.findall(r"(?:[A-Za-z0-9+/]{4}){8,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?", text)
            for b64 in b64_matches:
                try:
                    decoded = base64.b64decode(b64).decode("utf-8")
                    if any(c in decoded.lower() for c in ("ignore", "override", "system", "password", "token", "exec")):
                        findings.append({
                            "rule_id": "PRM-003",
                            "title": "Obfuscated Base64 Encoded Instruction Detected",
                            "severity": "HIGH",
                            "description": f"An obfuscated base64 block was identified that decodes to suspicious instructions: '{decoded[:80]}...'",
                            "evidence": {
                                "encoded_excerpt": b64[:40] + "...",
                                "decoded_preview": decoded[:120],
                                "line_number": line_no
                            },
                            "remediation": "Decode and analyze encoded payloads prior to model ingestion, or strip unrecognized base64 blocks from untrusted user inputs.",
                            "detection_method": "decoding_and_payload_heuristics",
                            "confidence": "HIGH",
                            "limitations": "Only decodes UTF-8 base64 segments longer than 32 characters."
                        })
                        break
                except Exception:
                    pass

        # 4. PRM-004: Delimiter & Context Escape Injection
        if is_rule_enabled("PRM-004"):
            for pattern, pattern_desc in DELIMITER_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    findings.append({
                        "rule_id": "PRM-004",
                        "title": f"Structural Delimiter Injection Detected ({pattern_desc})",
                        "severity": "HIGH",
                        "description": f"Untrusted input contains LLM protocol tokens or structural markdown headers designed to hijack the conversational role.",
                        "evidence": {
                            "matched_delimiter": match.group(0),
                            "line_number": line_no,
                            "excerpt": text[:200]
                        },
                        "remediation": "Escape or strip internal chat markup delimiters (<|im_start|>, [INST], etc.) before rendering prompts to the model.",
                        "detection_method": "token_boundary_analysis",
                        "confidence": "HIGH",
                        "limitations": "Targets common open-source and proprietary token delimiters."
                    })
                    break

        # 5. PRM-005: Tool Abuse & Code Execution Injection
        if is_rule_enabled("PRM-005"):
            for pattern, pattern_desc in TOOL_ABUSE_PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    findings.append({
                        "rule_id": "PRM-005",
                        "title": f"Dangerous Command Execution Primitive ({pattern_desc})",
                        "severity": "CRITICAL",
                        "description": f"Prompt contains high-risk shell, file system, or code execution syntax intended for autonomous tool exploitation.",
                        "evidence": {
                            "matched_pattern": match.group(0),
                            "line_number": line_no,
                            "excerpt": text[:200]
                        },
                        "remediation": "Implement strict sandboxing on all LLM tool execution agents (e.g. read-only file systems, network egress blocking, and human-in-the-loop approval).",
                        "detection_method": "signature_matching",
                        "confidence": "HIGH",
                        "limitations": "Flags known command patterns; obfuscated syntax may evade static signatures."
                    })
                    break

    return findings
