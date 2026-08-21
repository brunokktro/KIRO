# Output Contract

> Loaded at Step 8. The machine-readable contract a portfolio aggregator consumes.

Four artifacts, written to the repository root:

| Artifact | Name |
|---|---|
| Markdown report | `OPENSHIFT_TO_EKS_READINESS.md` |
| Machine-readable | `openshift-to-eks-readiness.json` |
| HTML view | `openshift-to-eks-readiness.html` |
| Run metadata | `metadata.json` |

---

## Per-finding required fields

Every finding in `findings[]` MUST carry these 12 fields. A missing field fails the analysis
and names the offending `question_id`.

| Field | Type | Description |
|---|---|---|
| `question_id` | string | e.g. `"SEC-Q1"` |
| `category` | string | Display name, e.g. `"Security Posture & Identity"` |
| `category_id` | string | e.g. `"SEC"` |
| `title` | string | Short finding title |
| `description` | string | What was found |
| `gap` | string | What is missing or incompatible on EKS |
| `recommendation` | string | The change to make |
| `severity` | enum | `"High"` / `"Medium"` / `"Low"` - unified display severity |
| `priority` | enum | `"P0"` / `"P1"` / `"P2"` / `"P3"` - per the scoring model |
| `effort` | enum | `"High"` / `"Medium"` / `"Low"` |
| `phase` | integer | `1`-`4`, derived remediation phase |
| `evidence` | object | `{file: string, lines: string|null}`. **For an ABSENCE finding, `file` is the file where the construct is MISSING - never a different file where it happens to exist.** A finding that `payments-api` has no probes cites `payments-api`'s manifest, not the compliant workload next to it. Citing the compliant file makes the report actively misleading: a reader following the evidence lands on a file that satisfies the question. Reserve `null` for a genuinely repo-wide finding with no representative path. |

**Repo-wide findings MUST use `evidence: {"file": null, "lines": null}`.** `APP-Q9`
(portability ratio) is the canonical case: its subject is the whole repository, so no file
represents it. Citing an arbitrary file for a repo-wide finding is misleading - a reader
follows the evidence expecting to see the problem there and lands somewhere unrelated, often
on a compliant file. Any finding whose subject is the repository rather than a specific
resource uses a null file.

## The `openshift_metadata` subobject
Every finding MUST also carry `openshift_metadata`, which preserves the rubric depth that the
12 flat fields flatten away.

| Field | Presence | Description |
|---|---|---|
| `native_severity` | always | `"BLOCKER"` / `"RISK-SAFETY"` / `"RISK-QUALITY"` / `"INFO"`. The join key back to the counts. |
| `safety_impact` | always | boolean. `true` for RISK-SAFETY and for any BLOCKER that is a security or data hazard. |
| `openshift_construct` | always | The API kind found, e.g. `"SecurityContextConstraints"`. |
| `openshift_api_group` | always | e.g. `"security.openshift.io/v1"`, or `null` when the finding is not object-based (a Dockerfile, a script). |
| `eks_equivalent` | always | The target construct, or the string `"none"` when there is genuinely no equivalent. `"none"` is a valid and important value - `OPS-Q8` uses it. |
| `conditional` | always | boolean. `true` for the 7 ⚡ questions. |
| `migration_target` | ⚡ only | The resolved target. |
| `target_resolution` | ⚡ only | `"as-written"` / `"escalated"` / `"de-escalated"`. |
| `resolution_reasoning` | ⚡ only | Prose explaining the resolution. |
| `operator_bucket` | `OPS-Q3` only | `"community"` / `"certified-with-upstream"` / `"openshift-only"`. **OPS-Q3 emits one finding per bucket present, never one collapsed finding.** |
| `scc_split` | `SEC-Q1` only | `{psa_covered: string[], needs_admission_controller: string[]}`. Which SCC capabilities Pod Security Admission covers and which genuinely need Kyverno or Gatekeeper. |

The three ⚡ fields are mandatory on every conditional finding. A ⚡ finding without them is
incomplete, because the reader cannot tell a correct scope downgrade from an understatement.

## `evaluations[]`

Questions that produce no finding (pass, not applicable, not present) go here.

| Field | Description |
|---|---|
| `question_id` | e.g. `"SEC-Q4"` |
| `category_id` | e.g. `"SEC"` |
| `title` | Question title |
| `resolution` | `"pass"` / `"not-applicable"` / `"not-present"` |
| `reason` | Why. Must cite where you looked when the resolution is `not-present`. |

## Coverage invariant

```text
|findings[] ∪ evaluations[]| == 38
findings[] ∩ evaluations[] == ∅
```

Every one of the 38 ids appears exactly once. Coverage is a **membership** check, not a count
check: a report answering every real question passes even if it also emits a grounded extra id,
while a report that drops a real question fails even if a fabricated id keeps the total looking
right.

A fabricated id carrying BLOCKER or RISK-SAFETY is a **hard fail**, because it would feed
`blocker_count` and move the tier.

## Summary block and reconciliation

```json
{
  "summary": {
    "tier": "Re-Platform-Required",
    "blocker_count": 9,
    "risk_safety_count": 13,
    "risk_quality_count": 12,
    "info_count": 4,
    "questions_evaluated": 38,
    "portability_ratio": 0.31,
    "migration_target": "eks-standard",
    "reconciliation_check": {
      "recomputed_from_findings": true,
      "agrees_with_summary": true
    }
  }
}
```

`blocker_count` and `risk_safety_count` are **recomputed from the emitted `findings[]`** and
compared against the summary. Disagreement fails the analysis and names the offending id. No
exclusion rule may lower a counter below the number of enumerated findings carrying that
severity.

## `metadata.json`

```json
{
  "analysis_type": "openshift-to-eks-migration-readiness",
  "analysis_version": "0.1.0",
  "repository": "<name>",
  "analysed_at": "<ISO-8601 UTC>",
  "migration_target": "eks-standard",
  "openshift_version_detected": "4.14",
  "app_criticality": "P0",
  "tags": [],
  "rubric_question_count": 38
}
```

## HTML visual contract

Single self-contained file, no external CDN. Sections in the same order as the Markdown.
Severity conveyed by **text label plus shape or icon, never by colour alone** - the primary
reader is colourblind. No emoji.

## Error handling

If a question cannot be evaluated (unparseable manifest, unreadable file), emit it as an
evaluation with `resolution: "not-applicable"` and a reason naming the file and the parse
error. **Never silently drop a question** - a dropped question breaks the coverage invariant
and is indistinguishable from a rubric that shrank.
