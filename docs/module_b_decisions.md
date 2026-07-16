# Module B Decision Record

**Frozen:** 2026-07-16  
**Scope:** Phase 4 onward  
**Sources of truth:** `task.md` Phase 4 locked assumptions and the Module B updates in `FYP_PROJECT_DESCRIPTION_AND_IMPLEMENTATION_PLAN.md`

These decisions keep the placeholder vertical slice and the later trained-model work on one architecture. A decision is changed only when its reversal condition is met and the change is recorded here before code is changed.

## 1. Label design: Option A

- **Decision:** Train an honest binary Good/Poor classifier from REHAB24-6 labels. Surface Fair only when the calibrated prediction is inside the low-confidence margin. Option B—a genuinely learned three-class model—is documented as the alternative and is not implemented.
- **Rationale:** The selected dataset supports binary correctness labels but does not provide a defensible fault-severity target. Manufacturing a third training label would overstate what the data contains.
- **What would reverse it:** A suitably licensed dataset with subject identifiers and independently validated ordinal or continuous movement-quality labels that can support three classes without synthetic relabelling.

## 2. Exercise order: squat first

- **Decision:** Complete and verify squat before starting lunge. Lunge remains committed Phase 5B scope.
- **Rationale:** Squat has the larger usable REHAB24-6 cohort and lets the shared registry, feature contract, inference, and persistence path be proven once before adding another exercise.
- **What would reverse it:** The Phase 5 data audit finds that the usable side-view squat cohort cannot support honest subject-wise training, while another in-scope exercise has a materially stronger compatible cohort.

## 3. Camera view: side only; valgus dropped

- **Decision:** Module B squat uses MediaPipe world landmarks from a side/sagittal camera view. Frontal knee-valgus features, rules, labels, and error tags are excluded.
- **Rationale:** A single side-view camera can support sagittal knee/hip/ankle motion but cannot also provide a reliable frontal-plane valgus measurement. Keeping valgus would create a view-dependent signal that the selected runtime and dataset cannot reproduce consistently.
- **What would reverse it:** A separately validated multi-view or depth-aware capture design, backed by compatible training data and a revised user protocol. That would be a new architecture decision rather than an inline threshold change.

## 4. Extension shape: registry of exercise plugins

- **Decision:** One thin generic `/api/module-b/*` router resolves `exercise_code` through a registry of `ModuleBExercise` plugins. Exercise-specific behavior lives in its own package; the router contains no exercise-name branching.
- **Rationale:** Module B shares a preprocessing, feature-schema, model, fusion, and persistence pipeline while each exercise owns segmentation, feature assembly, rules, and configuration. The registry keeps those boundaries explicit without duplicating the shared HTTP and storage layers.
- **What would reverse it:** Evidence that the exercise contracts no longer share a meaningful pipeline and require incompatible request or persistence semantics. Any change would require an architecture review; a one-off branch in the router is not an acceptable reversal.

## 5. After-set LLM default: Groq / Llama 3.3 70B

- **Decision:** The planned optional after-set prose adapter defaults to Groq with Llama 3.3 70B. Deterministic template feedback remains the base layer and fallback; the LLM never changes a grade.
- **Rationale:** This is the locked provider choice for the FYP plan, while keeping the provider behind an adapter and making failure non-blocking.
- **What would reverse it:** The required Phase 6 live documentation check finds that the model is unavailable or unsuitable, provider terms conflict with the project, deployment egress is rejected, or measured latency/reliability fails the project gate. A provider change must preserve the template fallback and grading firewall.

## 6. Model artifacts: committed for reproducibility

- **Decision:** Trained model bundles, their feature schema, version metadata, and reproducibility reports are committed to the repository.
- **Rationale:** Examiners must be able to run the exact evaluated artifact, and the backend must verify its feature-schema version before inference.
- **What would reverse it:** Dataset or artifact licensing prohibits redistribution, or an artifact exceeds practical repository limits. The replacement must be a pinned, checksummed, reproducible build/download process—not an unversioned external file.
