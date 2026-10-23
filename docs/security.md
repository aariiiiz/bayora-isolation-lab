# Bayora Isolation Lab: Security Architecture & Controls

## Threat Model & Security Boundaries

Bayora Isolation Lab is designed to validate safety testing infrastructure without introducing new security vulnerabilities into the testing host.

### 1. Safe Artifact Parsing
- **Zero Arbitrary Execution:** Uploaded files (JSON, JSONL, CSV, TXT, YAML) are parsed purely as declarative data trees. YAML is parsed strictly via `yaml.safe_load()` to prevent object deserialization attacks.
- **No Shell Interpolation:** Filenames and file contents are never interpolated into shell scripts or `eval()` primitives.
- **Path Traversal Prevention:** Uploaded filenames are sanitized through regex whitelisting (`[^\w\-.]`) and `os.path.basename()` to eliminate `../`, null bytes, and path injections.
- **Upload Size Bounds:** Hard 10MB limit enforced on both client and server sides.

### 2. Forensic Audit Non-Repudiation (Hash Chaining)
- Audit logs use deterministic canonical JSON serialization (alphabetically sorted keys, zero whitespace).
- Each record binds to the cryptographic hash of the prior record ($H_{i-1}$), beginning at `GENESIS`.
- Break detection verifies both payload authenticity and chronological link consistency.

### 3. Local Synthetic Sandbox Adapter
- Works exclusively against in-memory local fixtures (`tenant-alpha` and `tenant-beta`).
- Never transmits evaluation probes to arbitrary external IP addresses or third-party cloud accounts.
- Enforces session memory isolation and token verification deterministically.

### 4. Zero Fabricated Claims Policy
- No metric is hardcoded or mocked in the dashboard.
- Findings are reported only if backed by exact ground-truth excerpts and line numbers from the inspected artifact.
