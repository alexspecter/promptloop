# Ironclad Security Protocol for AI Agents

**Layer:** 1 (Directive)
**Enforcement:** Layer 2 (Orchestration)
**Scope:** All code generation, package installation, and execution on the local M4 Max environment.

---

## 0. Core Security Philosophy

Security is not an afterthought; it is a hard constraint on Layer 3 execution. We operate on a specific local machine, meaning malicious code or bad dependencies can compromise the host system directly.

* **Principle:** If a solution requires an unverified package or risky syntax, **find another solution**.
* **Principle:** "Fast" is secondary to "Safe".
* **Principle:** You are the Gatekeeper. You must self-correct *before* execution.

---

## 1. Package & Dependency Management (Supply Chain Security)

You are strictly prohibited from hallucinating or installing arbitrary packages.

### Rule 1.1: The "Standard Library First" Policy
Before requesting a third-party package, you **MUST** attempt to solve the problem using Python's standard library (e.g., `json`, `urllib`, `subprocess`, `csv`, `pathlib`). 

### Rule 1.2: The "Trusted Sources" Whitelist
You may only suggest installation of packages that meet **ALL** of the following criteria:
* **High Reputation:** The package is a top-tier industry standard (e.g., `pandas`, `numpy`, `requests`, `fastapi`, `pytorch`, `scikit-learn`). 
* **Verified Source:** The package exists on PyPI or a simplified GitHub repository with >1k stars. 
* **No Typosquatting:** You must verify the spelling matches the official documentation exactly (e.g., ensure `requests` not `request`).

### Rule 1.3: Immutable Versioning
When generating `requirements.txt`, `pyproject.toml` or uv installation commands, you **MUST** use version pinning (e.g., `pandas==2.2.0`) or rely on a uv.lock to prevent supply chain attacks via malicious updates. 

### Rule 1.4: Explicit Human Approval
If a directive requires a niche or obscure library:
1.  Pause execution.
2.  Explain **why** the standard library or major packages are insufficient.
3.  Wait for the human to install it or approve the risk. 

---

## 2. Code Generation Safeguards (Application Security)

Your "Layer 3: Execution" scripts must be deterministic and secure by design. 

### Rule 2.1: Zero-Trust Secret Management
* **NEVER** hardcode API keys, passwords, or tokens in Python scripts or Markdown plans.
* **ALWAYS** use `os.getenv()` and load secrets from the `.env` file defined in the architecture.

### Rule 2.2: Input Sanitization & Injection Prevention
* **SQL:** Never use f-strings or string concatenation for SQL queries. Always use parameterized queries (e.g., `cursor.execute("SELECT * FROM users WHERE name=?", (name,))`).
* **Shell:** Avoid `shell=True` in `subprocess` calls unless absolutely necessary. Use list arguments instead (e.g., `subprocess.run(["ls", "-l"])` instead of `subprocess.run("ls -l", shell=True)`).
* **Eval:** The use of `eval()` or `exec()` is **STRICTLY PROHIBITED**. 

### Rule 2.3: Artifact Isolation
All file operations (read/write) must be confined to the specific project directory or `.tmp/` folder. Do not write to system root or user home directories outside the project scope. 

---

## 3. Verification & Testing (The Defense Loop)

You are already required to write verification scripts. You must now upgrade these to "Security Verification Scripts." 

### Rule 3.1: The "Malicious Intent" Test
Your `tests/` scripts must not only check if the code works, but if it fails safely.
* **Example:** If writing a CSV parser, include a test case with a malformed CSV to ensure it doesn't crash the script or leak memory. 

### Rule 3.2: Mandatory Pre-Commit Validation
Before marking a task complete, you must pass the automated pre-commit pipeline defined in `.pre-commit-config.yaml`. This enforces deterministic security checks:
* **Ruff:** For continuous linting and formatting.
* **Gitleaks:** To automate the enforcement of Rule 2.1 (Zero-Trust Secret Management) by preventing hardcoded secrets.
* **Trivy:** To scan the filesystem for vulnerabilities, strictly gating commits on `HIGH` or `CRITICAL` severity findings.
* **Semgrep:** For advanced static analysis and enforcing secure code patterns.

---

## 4. Self-Annealing Security

If a security error occurs (e.g., a package fails to install due to hash mismatch, or a script tries to access a restricted file):
1.  **DO NOT** simply bypass the error. 
2.  **Update the Directive:** Record the security constraint in the relevant `directives/` file so future iterations know this path is blocked. 

---

## 5. Incident Response & Monitoring

### Rule 5.1: Incident Detection
Establish a process for detecting and reporting potential security incidents, such as unauthorized file access attempts or unverified package requests. 

### Rule 5.2: Incident Review
Conduct thorough reviews of security incidents to identify root causes and implement corrective actions in the `directives/` to prevent recurrence. 

---

## Summary Checklist for Agents

Before submitting a script to `execution/`, ask:

- [ ] Did I check if `sys` or `os` can do this before asking for `uv add`?
- [ ] Are all secrets pulled from `.env`?
- [ ] Is `shell=True` disabled?
- [ ] Did I pin my package versions?
- [ ] Does my verification script test for failure/safety?
- [ ] Do all pre-commit hooks (Ruff, Gitleaks, Trivy, Semgrep) pass successfully?