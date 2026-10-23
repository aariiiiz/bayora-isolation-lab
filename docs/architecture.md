# Bayora Isolation Lab: Architecture & Technical Specification

Bayora Isolation Lab is an evidence-based security validation platform designed to assess whether AI safety testing infrastructure correctly isolates tenants, sessions, test artifacts, access permissions, and audit evidence.

## System Architecture

```mermaid
graph TD
    User["Security Analyst / Red Team"] -->|Interacts with UI| Frontend["React 18 + Vite + Tailwind Frontend<br/>(Vertical Sidebar Navigation)"]
    Frontend -->|REST API Requests / JSON| Backend["FastAPI REST Backend Service<br/>(Python 3.12+)"]
    
    subgraph "Validation & Security Engines"
        Backend --> FileVal["File Validator & Parser<br/>(JSON, JSONL, CSV, YAML, TXT)"]
        FileVal --> RuleEngine["Rule Execution Engine"]
        RuleEngine --> IsoChecks["Operation A: Isolation & Access Review<br/>(ISO-001 to ISO-005)"]
        RuleEngine --> AuditChecks["Operation B: Audit Integrity Review<br/>(AUD-001 to AUD-005)"]
        RuleEngine --> PromptChecks["Operation C: Prompt Security Screening<br/>(PRM-001 to PRM-005)"]
        RuleEngine --> ConfigChecks["Operation D: Configuration Risk Review<br/>(CFG-001 to CFG-005)"]
        
        RuleEngine --> Scorer["Risk Scorer (0-100 Weighted Score)"]
    end

    subgraph "Cryptographic Ledger & Persistence"
        Backend --> DB[(SQLite Database via SQLAlchemy 2.x)]
        DB --> ExpTable["Experiments & Findings"]
        DB --> PolTable["Baseline & Custom Policies"]
        DB --> AuditChain["Audit Ledger with SHA-256 Hash Chaining"]
    end

    subgraph "AI Threat Modeling & Sandbox Adapter"
        Backend --> GroqAI["Groq Fast LLM Advisory<br/>(LLaMA 3.3 70B Versatile)"]
        Backend --> SandboxAdapter["Local Synthetic Sandbox Adapter<br/>(5 Deterministic Enforced Scenarios)"]
    end
```

## Core Subsystems

### 1. Analysis Engine & Operations
- **Operation A (Isolation & Access-Control Review):** Analyzes tenant boundaries, wildcard grants, shared memory flags, and storage directory path scoping.
- **Operation B (Audit Log Integrity Review):** Enforces mandatory schema attributes, ISO-8601 timestamps, duplicate ID collision detection, and sequential SHA-256 hash chaining.
- **Operation C (Prompt-Injection Review):** Heuristic screening for instruction overrides, ChatML/Llama delimiter injections, and tool command execution attempts.
- **Operation D (Configuration Risk Review):** Scans for exposed API keys, unencrypted HTTP endpoints, and 0.0.0.0 bindings.

### 2. Cryptographic Audit Hash Chaining
Every meaningful event generates an audit entry where:
$$H_i = \text{SHA-256}(\text{CanonicalJSON}(\text{Payload}_i \parallel H_{i-1}))$$
Any deletion, alteration, or reordering breaks the chain and is flagged immediately by the `/api/audit-events/verify-chain` endpoint.

### 3. Controlled Synthetic Sandbox Adapter
Implements a dedicated in-memory test fixture proving cross-tenant denial, session memory partition, and identity enforcement with zero third-party network egress.
