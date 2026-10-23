# Bayora Isolation Lab: Automated Testing & QA

## Test Suite Overview

Bayora Isolation Lab includes automated unit, integration, and security tests located in `backend/tests/`.

### Executing Backend Tests
From the `backend` folder:
```bash
python -m pytest tests -v
```
Or from the project root:
```bash
python -m pytest backend/tests -v
```

### Verified Test Matrix (21 Passing Tests)
| Test Module | Coverage Description | Status |
| :--- | :--- | :--- |
| `test_health.py` | Health endpoint and service status check | ✅ PASSED |
| `test_file_validator.py` | Path traversal prevention, extension whitelist, empty/oversized file handling, safe parsing | ✅ PASSED |
| `test_rule_engine.py` | Operation A, B, C, D deterministic rule checks, regex signatures, and weighted risk scorer | ✅ PASSED |
| `test_audit_hash_chain.py` | Cryptographic SHA-256 hash chaining, sequential linking, and tampering break detection | ✅ PASSED |
| `test_policies_api.py` | Policy CRUD operations, baseline policy deletion safeguards | ✅ PASSED |
| `test_synthetic_adapter.py` | In-tenant access, cross-tenant denial (403), cross-session isolation (403), unauthenticated denial (401) | ✅ PASSED |
| `test_experiments_api.py` | Full experiment lifecycle: upload, parse, analyze, persist findings, and export formal report | ✅ PASSED |

### Frontend Build Verification
From `frontend` folder:
```bash
npm run build
```
Compiles TypeScript and bundles production assets with zero errors.
