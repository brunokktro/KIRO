# Benchmark Results - OpenShift to EKS Migration Readiness (Lens)

## Executive Summary

| Metric | Result |
|--------|--------|
| Migration targets exercised | 3 (`eks-standard`, `eks-auto-mode`, `eks-hybrid`) |
| Fixture | `openshift-legacy-payments` - 29 YAML documents, 11 files, seeded with known constructs |
| Assertion result | **3/3 PASS** against `EXPECTED-FINDINGS.md` |
| Coverage invariant | 38/38 distinct question ids in all 3 runs, findings and evaluations disjoint |
| Count reconciliation | recomputed from `findings[]` == declared summary, in all 3 runs |
| Planted BLOCKERs detected | **9/9 in all 3 runs** |
| Planted RISK-SAFETY detected | **13/13 in all 3 runs** |
| False positives against the control file | **0 in all 3 runs** |
| Invented gaps (should-be-evaluations) | **0** - 6/6 correctly resolved as evaluations in all 3 runs |
| Read-only contract | **verified in all 3** - `git diff baseline..HEAD` contains only the 4 artifacts, zero source files |
| Scope marker (`⚡`) effect | **measured** - `blocker_count` moved 9 -> 11 -> 8 across targets |
| Artifact bundle | 4/4, 3/4, 4/4 (see Known Issues) |
| Total agent minutes | **139.46** |
| Total estimated cost | **~US$ 4.88** (at US$ 0.035 / agent minute) |
| Wall clock | ~35 min total, ~12 min per run |

### Methodology

The fixture was seeded with **known OpenShift constructs**, one or more per rubric question,
plus **control resources** that are already portable Kubernetes and must not be flagged. It was
committed to git as a baseline, then analysed via:

```bash
atx custom def exec -n openshift-to-eks-migration-readiness -p . -x -t \
  --configuration 'additionalPlanContext=migration_target: <target>' --limit 45
```

Three properties of this benchmark are worth stating because they are what make the numbers
mean anything:

1. **The analysed copy carries no answer key.** The authored fixture is annotated (`PLANTED:
   SEC-Q1`, and the `EXPECTED-FINDINGS.md` spec). Analysing that copy would let the agent read
   the answers and echo them back. `make-run-copy.sh` produces the run copy, strips every
   meta-test comment and the spec files, and **asserts zero references to any question id
   survive**, failing if one does. The first attempt at this benchmark was aborted for exactly
   this reason: 79 lines of answer key were present in the manifests.
2. **The assertion is independent of the run.** The report emits
   `reconciliation_check.agrees_with_summary`, but a guardrail that is the executor's own
   self-assessment is not a guardrail. `assert_lens_run.py` recomputes every count from
   `findings[]` and compares.
3. **Correct non-detection is asserted, not just detection.** A rubric that flags everything is
   as useless as one that flags nothing. Bucket B asserts zero findings against the control
   file and that six questions whose construct is genuinely absent resolve as evaluations.

---

## At-a-Glance Results

| Target | Status | Blockers | Risk-Safety | Findings / Evals | Tier | Artifacts | Read-only | Agent Min | Cost |
|---|---|---|---|---|---|---|---|---|---|
| `eks-standard` | PASS | 9 | 14 | 33 / 7 | Re-Platform-Required | 4/4 | OK | 46.79 | $1.64 |
| `eks-auto-mode` | PASS | **11** | 13 | 34 / 6 | Re-Platform-Required | 3/4 | OK | 45.81 | $1.60 |
| `eks-hybrid` | PASS | **8** | 14 | 34 / 6 | Re-Platform-Required | 4/4 | OK | 46.86 | $1.64 |
| **TOTAL** | **3/3** | | | | | **11/12** | **3/3** | **139.46** | **$4.88** |

---

## The `⚡` scope mechanism, measured

The 7 conditional questions are the mechanism most likely to be decorative: a marker that
changes nothing. Running the same fixture against three targets is what proves it is real. If
the three runs were identical, the marker would be doing no work.

| Question | `eks-standard` | `eks-auto-mode` | Declared resolution | Matches the table? |
|---|---|---|---|---|
| INF-Q1 (PerformanceProfile) | RISK-SAFETY | **BLOCKER** | `escalated` | yes |
| INF-Q2 (MachineConfig) | RISK-QUALITY | **RISK-SAFETY** | `escalated` | yes |
| INF-Q6 (CPU manager / hugepages) | RISK-SAFETY | **BLOCKER** | `escalated` | yes |
| INF-Q3 (SR-IOV / Multus) | BLOCKER | BLOCKER | `escalated` (now unconditional) | yes |
| DATA-Q1, SEC-Q2, OPS-Q3 | unchanged | unchanged | `as-written` | yes |

And in the opposite direction, which is the harder half to get right:

| Question | `eks-standard` | `eks-hybrid` | Declared resolution |
|---|---|---|---|
| INF-Q3 (SR-IOV / Multus) | BLOCKER | **RISK-SAFETY** | `de-escalated` - the node is customer-managed, so SR-IOV remains available |
| INF-Q6 (CPU manager) | RISK-SAFETY | **RISK-QUALITY** | `de-escalated` |

`blocker_count` therefore moves **9 -> 11 -> 8** across the three targets, driven entirely by
the resolution table. Every resolution matched.

---

## Per-question outcome (`eks-standard`)

### The three checks that matter most

**OPS-Q3 emitted one finding per operator bucket, with the fixed severities:**

```text
community                -> RISK-QUALITY   (Strimzi: Helm chart exists, effort not blocker)
certified-with-upstream  -> RISK-SAFETY    (rhbk-operator: Keycloak upstream, parity to validate)
openshift-only           -> BLOCKER        (openshift-pipelines-operator-rh: no equivalent)
```

This is the question that decides the tier. A collapsed single finding, or grading `community`
as BLOCKER, would over-report the migration.

**SEC-Q1 produced the correct SCC split:**

```json
{"psa_covered": ["RunAsAny (UID)", "RunAsAny (fsGroup)", "RunAsAny (supplementalGroups)"],
 "needs_admission_controller": []}
```

The fixture's SCC only uses `anyuid` semantics, so Pod Security Admission alone is sufficient
and no policy engine is needed. Mapping every SCC straight to Kyverno would import a component
the customer does not need.

**SEC-Q5 detected authorization granted without any RBAC object:**

```text
evidence: manifests/openshift-platform.yaml:16-17
"SCC users: list granting to system:serviceaccount:payments-prod:payments-api
 (implicit RBAC without RoleBinding). oc adm policy add-scc-to-user ... in deploy.sh"
```

---

## Defects this benchmark found

Three rubric defects were found by the **first** run and fixed before the three recorded runs.
This is the value of the fixture: none of them were visible to review of the rubric text.

| # | Defect | Root cause | Fix |
|---|---|---|---|
| 1 | `SEC-Q5` not detected (12/13 risk-safety) | The "look for" list only named RBAC objects. The fixture grants via the `users:` field of the SCC and via `oc adm policy add-scc-to-user`, so a repo can have **zero** `RoleBinding` and still depend on OpenShift authorization. The run's reasoning was factually correct. | Added the SCC `users:`/`groups:` fields and the imperative `oc adm policy` forms to the look-for list, with an explicit note that concluding `not-present` from missing RBAC objects is wrong. |
| 2 | `OPS-Q3` emitted 2 buckets instead of 3, and graded `community` as BLOCKER (`blocker_count` 10 instead of 9) | The calibration was prose that left severity to judgement. | Replaced with a fixed severity table per bucket, plus "a run that emits fewer findings than there are buckets present has failed this question". |
| 3 | `APP-Q8` cited `notifier.yaml` (the compliant file) as evidence for probes being absent on `payments-api` | The output contract said "cite where you looked", which is ambiguous for an absence finding. A reader following the evidence landed on a file that satisfies the question. | Contract now states that for an absence finding the evidence is the file where the construct is **missing**, never another file where it exists. |

Two further defects were found in the **assertion script itself**, both producing false
failures against a correct run. Recorded because a validator that cries wolf trains you to
ignore it:

- It used `next()` to read a question's severity, taking the first finding. Once `OPS-Q3`
  correctly emitted three findings with three different severities, it read `community`
  (RISK-QUALITY) and failed a correct run. Now asserts "at least one finding carries the
  expected severity", plus a dedicated per-bucket check.
- It hardcoded the `eks-standard` severity expectations, so the `eks-hybrid` run failed on
  `INF-Q3` being RISK-SAFETY - which is exactly what the resolution table demands there. The
  expected severity is now a function of the target.

---

## Exit Criteria Compliance (per SKILL.md)

| # | Exit criterion | standard | auto-mode | hybrid |
|---|---|---|---|---|
| 1 | 38 questions evaluated, findings ∪ evaluations covers each id once | PASS | PASS | PASS |
| 2 | Every finding carries evidence with a file path | PASS | PASS | PASS |
| 3 | Every ⚡ question carries its target resolution and reasoning | PASS | PASS | PASS |
| 4 | Summary counts recomputed from findings and reconciled | PASS | PASS | PASS |
| 5 | Readiness tier assigned per the count rules | PASS | PASS | PASS |
| 6 | Four artifacts written (MD, JSON, HTML, metadata.json) | PASS | **FAIL** (3/4) | PASS |
| 7 | Zero source files modified | PASS | PASS | PASS |

---

## Known Issues

1. **The artifact bundle is not deterministic.** `eks-auto-mode` produced 3 of 4 artifacts,
   omitting `metadata.json`; the other two runs produced all four. All three runs exceeded the
   `--limit 45` budget (46.79 / 45.81 / 46.86), so the fourth artifact is being written right
   at the cut-off. **A budget below ~55 agent minutes risks losing an artifact silently** - the
   run still exits and the other artifacts look complete. Raise the limit, and assert the
   artifact count rather than trusting the run to finish.
2. **Run-to-run variance on non-conditional questions.** `OPS-Q7` (CI/CD portability) resolved
   as an evaluation under `eks-standard` and as a RISK-QUALITY finding under the other two
   targets, despite not being a `⚡` question and the fixture being identical. Findings/
   evaluations split moved 33/7, 34/6, 34/6. The invariants (coverage, reconciliation, bucket A,
   bucket B) held in every run, which is the point of asserting invariants rather than exact
   finding text - but a benchmark that asserted an exact finding count would be flaky.
3. **AWS Transform stages results on its own branch.** It creates
   `atx-result-staging-<timestamp>` and commits the artifacts there. This is platform
   behaviour, not the analysis. `SKILL.md` originally forbade branch creation without
   distinguishing the two actors, which read as a violated constraint; the wording now names
   the platform behaviour explicitly and defines the read-only contract as
   `git diff <baseline> HEAD -- <source paths>` returning empty.

---

## Reproducing

```bash
# 1. generate the run copy without the answer key (asserts zero leakage, fails if any)
fixtures/openshift-legacy-payments/make-run-copy.sh \
  fixtures/openshift-legacy-payments /tmp/run-eks-standard

# 2. publish the rubric (staged copy: SKILL.md + references/ only;
#    a README.md at the definition root aborts the publish)
atx custom def publish -n openshift-to-eks-migration-readiness --sd <staged>

# 3. run, per target
cd /tmp/run-eks-standard && atx custom def exec \
  -n openshift-to-eks-migration-readiness -p . -x -t \
  --configuration 'additionalPlanContext=migration_target: eks-standard' --limit 55

# 4. assert the rubric structure parses in the reference harness
python3 validate_lens.py <definition-dir>

# 5. assert the run output against the spec, independently of the run
python3 assert_lens_run.py openshift-to-eks-readiness.json eks-standard
```

Both validators live in `OneDrive/LOPBRUNO/Scripts/atx-lens/`.
