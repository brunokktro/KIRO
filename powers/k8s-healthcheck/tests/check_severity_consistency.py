#!/usr/bin/env python3
"""Severity consistency gate for the k8s-healthcheck Power.

Every check has three severity sources that must not contradict each other:

  catalog   POWER.md Check Catalog "Default severity" column + the **Severity:** line
  enforce   the **FAIL when:** line, severities in parentheses
  detailed  the **Finding logic:** rows, "<condition> -> <SEVERITY>"

Rules (deterministic, stdlib only):
  R1  every steering check is in the catalog and vice versa
  R2  catalog default == first severity of the **Severity:** line; when that line names
      no severity ("Varies"), catalog default == highest FAIL when severity
  R3  a **Severity:** line that names more than one severity ("A (if x) / B (if y)") is a
      per-condition rule: every severity it names must be produced by FAIL when and by
      Finding logic, when those sections carry severities
  R4  LOCKS: a named condition keeps one severity in every source that mentions it, and
      it must be mentioned in every required source

Usage:  python3 tests/check_severity_consistency.py [--self-test]
Exit 0 = consistent, 1 = contradictions found (each printed with check ID and source).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEV = r"(CRITICAL|HIGH|MEDIUM|LOW|INFO)"
RANK = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

# (check_id, keyword) -> (severity, sources that must mention the keyword)
LOCKS = {
    ("SEC-01", "baseline"): ("MEDIUM", ("catalog", "enforce", "detailed")),
}


def parse_catalog(text):
    return {m[1]: m[2] for m in re.finditer(
        r"^\| ([A-Z]+-\d{2}) \|[^|]*\|[^|]*\| " + SEV + r" \|", text, re.M)}


def parse_checks(files):
    """{check_id: {"file", "severity_line", "fail_when", "logic": [(text, sev)]}}"""
    checks = {}
    for name, text in files.items():
        for block in re.split(r"^## Check: ", text, flags=re.M)[1:]:
            cid = block.split()[0]
            sev = re.search(r"^\*\*Severity:\*\*(.*)$", block, re.M)
            fail = re.search(r"^\*\*FAIL when:\*\*(.*)$", block, re.M)
            logic = []
            fl = re.search(r"^\*\*Finding logic:\*\*\n((?:- .*\n?)+)", block, re.M)
            if fl:
                for row in fl[1].splitlines():
                    m = re.match(r"- (.*?)\s*(?:->|→)\s*(?:map to )?" + SEV + r"\b", row)
                    if m:
                        logic.append((m[1], m[2]))
            checks[cid] = {
                "file": name,
                "severity_line": sev[1].strip() if sev else "",
                "fail_when": fail[1].strip() if fail else "",
                "logic": logic,
            }
    return checks


def clauses(text):
    """**Severity:** line: 'A (if x) / B (if y)', the condition follows its severity."""
    return [(m[0], m[1]) for m in re.finditer(r"\b" + SEV + r"\b(?:\s*\([^)]*\))?", text)]


def fail_when_clauses(text):
    """FAIL when severities live in parentheses: '... condition (HIGH, note)'."""
    out, start = [], 0
    for m in re.finditer(r"\(" + SEV + r"\b[^)]*\)", text):
        out.append((text[start:m.end()], m[1]))
        start = m.end()
    return out


def validate(catalog, checks):
    errors = []
    for cid in sorted(set(catalog) ^ set(checks)):
        where = "catalog only" if cid in catalog else "steering only"
        errors.append(f"R1 {cid}: present in {where}")

    for cid, c in sorted(checks.items()):
        if cid not in catalog:
            continue
        sev_cl = clauses(c["severity_line"])
        enf_cl = fail_when_clauses(c["fail_when"])
        enf = {s for _, s in enf_cl}
        det = {s for _, s in c["logic"]}

        if sev_cl:
            if sev_cl[0][1] != catalog[cid]:
                errors.append(f"R2 {cid}: catalog {catalog[cid]} != **Severity:** "
                              f"first severity {sev_cl[0][1]} ({c['severity_line']!r})")
        elif enf and catalog[cid] != max(enf, key=RANK.get):
            errors.append(f"R2 {cid}: catalog {catalog[cid]} != highest FAIL when "
                          f"severity {max(enf, key=RANK.get)} (no severity on **Severity:** line)")

        if len({s for _, s in sev_cl}) > 1:
            for _, s in sev_cl:
                if enf and s not in enf:
                    errors.append(f"R3 {cid}: **Severity:** names {s}, FAIL when produces "
                                  f"only {sorted(enf, key=RANK.get)}")
                if det and s not in det:
                    errors.append(f"R3 {cid}: **Severity:** names {s}, Finding logic produces "
                                  f"only {sorted(det, key=RANK.get)}")

    for (cid, key), (want, required) in LOCKS.items():
        c = checks.get(cid)
        if not c:
            errors.append(f"R4 {cid}: locked check not found")
            continue
        sources = {"catalog": clauses(c["severity_line"]),
                   "enforce": fail_when_clauses(c["fail_when"]),
                   "detailed": c["logic"]}
        for src, pairs in sources.items():
            hits = [s for text, s in pairs if key in text.lower()]
            if src in required and not hits:
                errors.append(f"R4 {cid}: '{key}' not mentioned in {src}")
            for s in hits:
                if s != want:
                    errors.append(f"R4 {cid}: '{key}' is {s} in {src}, locked at {want}")
    return errors


def load(overrides=None):
    files = {p.name: p.read_text(encoding="utf-8") for p in sorted((ROOT / "steering").glob("*-checks.md"))}
    for name, (old, new) in (overrides or {}).items():
        assert old in files[name], f"self-test anchor missing in {name}: {old!r}"
        files[name] = files[name].replace(old, new, 1)
    return parse_catalog((ROOT / "POWER.md").read_text(encoding="utf-8")), parse_checks(files)


def self_test():
    """Paired control: the gate must pass on the tree and fail on the known bad SEC-01 line."""
    catalog, checks = load()
    assert len(checks) == len(catalog) == 68, f"expected 68 checks, got {len(checks)}/{len(catalog)}"
    assert not validate(catalog, checks), "clean tree must pass"
    bad = {"security-checks.md": ("/ MEDIUM (if only baseline)", "/ HIGH (if only baseline)")}
    errs = validate(*load(bad))
    assert any(e.startswith("R3 SEC-01") for e in errs), errs
    assert any(e.startswith("R4 SEC-01") and "catalog" in e for e in errs), errs
    print(f"self-test OK: clean tree passes, regressed SEC-01 caught ({len(errs)} errors)")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
        sys.exit(0)
    catalog, checks = load()
    errors = validate(catalog, checks)
    for e in errors:
        print(e)
    print(f"{len(checks)} checks, {len(errors)} contradictions")
    sys.exit(1 if errors else 0)
