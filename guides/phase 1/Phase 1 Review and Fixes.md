# Phase 1 — Review & Fixes (Member 3)


## Summary

Members 1 and 2 submitted Phase 1 work that needed to be moved into the
project's real source layout. The work was sound in design but had **one
critical correctness bug** and several gaps versus the spec (`Major Project
Planning.md` §11 and the Phase 1 Plan). All Phase 1 source files are now in
their correct locations and the bugs are fixed.

### Files now in their correct places

| Location | Source | Status |
| --- | --- | --- |
| `rules/spec.yaml` | Member 1 | Placed + clarified |
| `rules/s3_public_read.yaml` | Member 1 | Placed + compliance fixed |
| `rules/security_group_open.yaml` | Member 1 | Placed + compliance fixed |
| `rules/iam_wildcard.yaml` | Member 1 | Placed + compliance fixed |
| `rules/s3_encryption.yaml` | **Added** | New rule (CIS-AWS-004) |
| `rules/iam_wildcard_principal.yaml` | **Added** | New rule (CIS-AWS-005) |
| `rules/README.md` | Member 1 | Placed + updated |
| `backend/src/__init__.py` | **Added** | Makes `backend/src` importable |
| `backend/src/parser.py` | Member 2 | Placed + **critical fix** |
| `backend/src/rule_engine.py` | Member 2 | Placed + integration fix |

> The files listed above are now the source of truth for Phase 1. Any old
> handoff notes or plain-text drafts should be treated as superseded.

---

## Member 1 — Rule format & starter rules

### What was missed

1. **Compliance mapping was a flat string.** Every rule used
   `compliance: CIS AWS Foundations Benchmark` — no specific CIS control ID and
   **no NIST CSF ID at all**. The planning doc (§11) requires a structured block
   with both `cis_aws` and `nist_csf` IDs. Phase 7 (compliance mapping) cannot
   work without specific control IDs.
2. **Too few rules.** Only 3 rules were written; the Phase 1 Plan calls for
   **5–8 starter rules**.
3. **Files were never placed in `/rules/`.** They lived inside a `.txt` dump, so
   the engine had nothing to load.
4. **`spec.yaml` was slightly misleading** — it nested operators under an
   `operators:` key, but real rules place the operator directly inside
   `condition`. It also didn't state that the engine skips `spec.yaml`.

### What was fixed

- Converted `compliance` to the structured form on every rule:
  ```yaml
  compliance:
    cis_aws: "2.1.5"
    nist_csf: "PR.AC-3"
  ```
- Added two rules to reach the 5-rule minimum:
  - **CIS-AWS-004** — S3 bucket encryption disabled (`encryption_enabled: false`).
  - **CIS-AWS-005** — IAM policy wildcard *principal* (distinct from the existing
    wildcard *action* rule).
- Placed all rule files, `spec.yaml`, and `README.md` in `/rules/`.
- Rewrote `spec.yaml` to match the real rule shape and noted that the loader
  skips it.

> Action for the team: the exact CIS control numbers (e.g. `2.1.5`, `5.2`,
> `1.16`) should be re-verified against the specific CIS AWS Benchmark version we
> standardise on. The mappings are reasonable but version-sensitive.

---

## Member 2 — Secure parser & rule engine

### What was missed

1. **CRITICAL — the parser rejected every wildcard config.**
   `_reject_yaml_aliases()` rejected any line containing `*` or `&` as a raw
   substring. But `*` is exactly what the wildcard rules (CIS-AWS-003/005) exist
   to detect, and the check also ran on **JSON**. Result: a valid file such as
   `{"action": "s3:*"}` was thrown out with *"YAML aliases are not allowed"*
   **before it was ever parsed** — so the wildcard rules could never fire on real
   uploads. The engine only appeared to work because its `__main__` demo
   hand-fed Python dicts and bypassed the parser entirely.
2. **No parser → engine seam.** The parser returns the file's shape (usually a
   single dict), but `evaluate()` iterates a *list of resource dicts*. Passing
   parser output straight in would iterate dict keys and break. Nothing connected
   the two.
3. **Minor:** `from concurrent.futures import ... TimeoutError` shadowed the
   builtin; modules called `logging.basicConfig()` (libraries shouldn't configure
   root logging); engine raised `KeyError` on a malformed rule; only `*.yaml`
   (not `*.yml`) rule files were loaded.

### What was fixed

- **Rewrote anchor/alias detection to be precise.** It now walks the YAML event
  stream (`yaml.parse` with `SafeLoader`) and rejects only genuine anchors
  (`&name`) and aliases (`*name`), and only for YAML input. Legitimate wildcard
  *values* (`"s3:*"`, `"*"`) pass through; real alias abuse is still blocked.
- **Added `_normalize()` to the engine.** `evaluate()` now accepts a list, a
  single resource dict, or a `{"resources": [...]}` wrapper — bridging parser
  output to the evaluator.
- Hardening: aliased the futures `TimeoutError` and re-raise the builtin; removed
  `basicConfig` from module import; `evaluate()`/`load_rules()` skip malformed
  rules instead of crashing; loader now reads `*.yaml` and `*.yml`.
- Added `backend/src/__init__.py` so the module is importable as a package.

---

## Member 3 — what I built (in simple words)

My job was to prove the rule engine actually works by testing it. Here is what I
added:

1. **Test config files (fixtures).** For each of the 5 rules I made two example
   files: a "bad" one that *should* get flagged, and a "good" one that *should
   not*. They live in `backend/tests/fixtures/bad/` and `.../good/`. I used a mix
   of JSON and YAML so both parser paths get exercised.

2. **The test suite — `backend/tests/test_rules.py`.** It automatically:
   - feeds every **bad** file through the parser + engine and checks the right
     rule fires (and only that rule);
   - feeds every **good** file through and checks **nothing** is flagged;
   - checks all 5 rules load;
   - and tests the parser's safety limits: a too-big file, a too-deeply-nested
     file, a real YAML alias "bomb", and a missing file are all rejected — plus a
     **regression test** that locks in the Member 2 wildcard fix (so that bug can
     never come back unnoticed).

3. **A way to run the tests automatically.**
   - `scripts/run_tests.sh` — run all tests locally with one command.
   - `.github/workflows/phase1-tests.yml` — GitHub Actions runs the tests on
     every pull request, so broken code can't be merged.

4. **Dependency fixes so tests can run.** Added the missing `PyYAML` to
   `backend/requirements.txt` (the engine imports it but it wasn't listed) and
   created `backend/requirements-dev.txt` for `pytest`.

**Result: all 14 tests pass.** That confirms Members 1 & 2's work (with my fixes)
is correct end-to-end.

### Files I added

| Location | What it is |
| --- | --- |
| `backend/tests/fixtures/good/*` | 3 clean configs (no findings expected) |
| `backend/tests/fixtures/bad/*` | 5 bad configs (one per rule) |
| `backend/tests/test_rules.py` | The pytest suite (14 tests) |
| `backend/tests/conftest.py` | Lets the tests import the engine |
| `scripts/run_tests.sh` | One-command local test runner |
| `.github/workflows/phase1-tests.yml` | CI that runs tests on every PR |
| `backend/requirements-dev.txt` | Test dependencies |
| `backend/requirements.txt` | Added `PyYAML` (runtime dep) |

---

## Verification performed during this review

The corrected code was executed end-to-end. Confirmed:

- `./scripts/run_tests.sh` passes all Phase 1 tests: **14 passed, 0 failed**.
- Wildcard JSON (`action: "s3:*"`) now **parses** and triggers CIS-AWS-003.
- Genuine YAML anchor/alias abuse is **still rejected**.
- A 6-resource config produced exactly the 5 expected findings
  (001, 002, 003, 004, 005); a clean config produced **zero**.
- Oversized (>2 MB) file is rejected before parsing.

> Note on running locally: use Python 3.11 for the full backend dependency set.
> The Phase 1 test runner automatically uses `.venv/bin/python` when a local
> virtual environment exists.
