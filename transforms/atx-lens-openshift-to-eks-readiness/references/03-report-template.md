# Report Template

> Loaded at Step 8. Defines the Markdown report structure.

The Markdown report **renders** values that were already decided and emitted in the JSON. It
never re-derives a count, a band or a severity. Re-deriving in the template is how MOD's header
came to disagree with its own findings, and that bug is filed in the reference repo.

---

## Structure

```markdown
# OpenShift to Amazon EKS Migration Readiness

**Application:** <repo name>
**Analysed:** <ISO-8601 UTC>
**Migration target:** <eks-standard | eks-auto-mode | eks-hybrid>
**OpenShift version detected:** <version or "not detected">

## Readiness

| | |
|---|---|
| **Tier** | <tier> |
| Blockers | <blocker_count> |
| Safety risks | <risk_safety_count> |
| Quality risks | <risk_quality_count> |
| Informational | <info_count> |
| Questions evaluated | 38 |
| Portability ratio | <n>% of manifests carry no OpenShift API group |

<one paragraph stating the tier and the specific constructs that drove it. Name them.
Never "several issues were found".>

## Blockers

<one subsection per BLOCKER finding, ordered by category>

### <question_id>: <title>

**Construct:** <what was found>
**Evidence:** `<file>:<lines>`
**EKS equivalent:** <the mapping, or an explicit statement that none exists>
**What breaks if ignored:** <concrete failure mode>
**Remediation:** <the change>
<if ⚡: **Target resolution:** <migration_target> - <resolution_reasoning>>

## Safety Risks

<same shape. These are the findings where the application STARTS on EKS and a property is
silently lost. State the lost property explicitly - that is the whole value of the section.>

## Quality Risks

<condensed table: question_id | construct | evidence | effort>

## Informational

<condensed table>

## Not Applicable

<table of every question that resolved to an evaluation, with the reason. This section is
mandatory: it is the reader's proof that a question was considered and dismissed on evidence,
rather than skipped. A rubric that hides its non-findings cannot be audited.>

| question_id | Resolution | Why |
|---|---|---|

## Remediation Sequence

<ordered list, P0 first, grouped so that items sharing a root cause appear together. State
dependencies: APP-Q3 cannot be resolved before a registry exists (APP-Q2).>

## Evidence Index

<every file cited, with the question ids that cited it. Lets a reviewer walk the repo once.>
```

---

## Rules

1. **Every finding names its evidence file.** A finding with no file is incomplete. For an
   absence finding, the file is where you looked.
2. **Never write "several" or "various".** Name the constructs and count them.
3. **The Not Applicable section is not optional.** It is what makes the report auditable.
4. **⚡ findings state the target resolution inline**, in the finding, not only in the header.
   A reader looking at one blocker must see why it is a blocker for this target.
5. **No emoji.** These reports are read by customer stakeholders.
6. **Severity words come from the rubric.** Do not paraphrase `RISK-SAFETY` as "medium risk".
