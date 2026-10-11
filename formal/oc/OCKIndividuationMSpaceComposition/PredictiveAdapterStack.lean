import OCKIndividuationMSpaceComposition.ContextTypingRefinement
import OCKIndividuationMSpaceComposition.SupportConditionedCorrectionTransport

namespace OCKIndividuationMSpaceComposition

/-!
# Predictive adapter stack, collision ceiling, and stable fallback

OC does not obtain a numerical prediction from a bare object identifier.  A
prediction is produced by a typed stack: core representation, domain
interpretation, observation, experimental design, dataset binding, task
projection, fitted calibration, and finally a decision adapter.

The layer names are OC-specific; composition, squared-loss geometry, and
safe fallback are reused mathematics.  The substantive boundary is explicit:
information erased by any upstream adapter cannot be recovered by a more
powerful downstream estimator.
-/

universe uReality uCore uDomain uObserved uDesigned uBound uTaskInput
  uPrediction uDecision

/-- The complete pointwise surface of an OC predictive application.  Population
sampling and fitting procedures instantiate `design`, `bind`, and `calibrate`;
the abstract functions record what information their fitted output retains. -/
structure PredictiveAdapterStack
    (Reality : Type uReality) (Core : Type uCore) (Domain : Type uDomain)
    (Observed : Type uObserved) (Designed : Type uDesigned)
    (Bound : Type uBound) (TaskInput : Type uTaskInput)
    (Prediction : Type uPrediction) (Decision : Type uDecision) where
  core : Reality → Core
  domain : Core → Domain
  observe : Domain → Observed
  design : Observed → Designed
  bind : Designed → Bound
  task : Bound → TaskInput
  calibrate : TaskInput → Prediction
  decide : Prediction → Decision

namespace PredictiveAdapterStack

variable {Reality : Type uReality} {Core : Type uCore} {Domain : Type uDomain}
  {Observed : Type uObserved} {Designed : Type uDesigned}
  {Bound : Type uBound} {TaskInput : Type uTaskInput}
  {Prediction : Type uPrediction} {Decision : Type uDecision}

/-- Information visible after the domain and observation adapters. -/
def observed
    (stack : PredictiveAdapterStack Reality Core Domain Observed Designed Bound
      TaskInput Prediction Decision) : Reality → Observed :=
  stack.observe ∘ stack.domain ∘ stack.core

/-- End-to-end decision produced by the full adapter stack. -/
def run
    (stack : PredictiveAdapterStack Reality Core Domain Observed Designed Bound
      TaskInput Prediction Decision) : Reality → Decision :=
  stack.decide ∘ stack.calibrate ∘ stack.task ∘ stack.bind ∘ stack.design ∘
    stack.observed

/-- Every collision introduced by the observation-side prefix survives all
downstream model capacity, calibration, and decision logic. -/
theorem run_eq_of_observation_collision
    (stack : PredictiveAdapterStack Reality Core Domain Observed Designed Bound
      TaskInput Prediction Decision)
    {left right : Reality}
    (collision : stack.observed left = stack.observed right) :
    stack.run left = stack.run right := by
  simp only [run, Function.comp_apply]
  rw [collision]

/-- No end-to-end deterministic adapter stack can be exact on two realities
that its observation prefix identifies but whose required decisions differ. -/
theorem observation_collision_blocks_exact_decision
    (stack : PredictiveAdapterStack Reality Core Domain Observed Designed Bound
      TaskInput Prediction Decision)
    (target : Reality → Decision) {left right : Reality}
    (collision : stack.observed left = stack.observed right)
    (targetDifferent : target left ≠ target right) :
    ¬ (stack.run left = target left ∧ stack.run right = target right) := by
  intro exactness
  apply targetDifferent
  rw [← exactness.1, ← exactness.2]
  exact stack.run_eq_of_observation_collision collision

end PredictiveAdapterStack

/-! ## Sharp finite collision ceiling under squared loss -/

/-- Mean squared loss forced on two observation-colliding outcomes when one
common scalar prediction must be used. -/
noncomputable def CollisionPairMSE (first second prediction : ℝ) : ℝ :=
  ((first - prediction) ^ 2 + (second - prediction) ^ 2) / 2

/-- Exact bias-plus-irreducible decomposition for one collision pair. -/
theorem collisionPairMSE_decomposition (first second prediction : ℝ) :
    CollisionPairMSE first second prediction =
      (first - second) ^ 2 / 4 +
        (prediction - (first + second) / 2) ^ 2 := by
  unfold CollisionPairMSE
  ring

/-- Sharp no-go: a collision whose outcomes differ by `first-second` forces
at least one quarter of their squared separation as mean squared loss. -/
theorem collisionPairMSE_lower_bound (first second prediction : ℝ) :
    (first - second) ^ 2 / 4 ≤
      CollisionPairMSE first second prediction := by
  rw [collisionPairMSE_decomposition]
  exact le_add_of_nonneg_right (sq_nonneg _)

/-- Positive matching theorem: the midpoint prediction attains the collision
lower bound exactly, so the bound is not an artefact of a weak estimator. -/
theorem collisionPairMSE_midpoint_attains_bound (first second : ℝ) :
    CollisionPairMSE first second ((first + second) / 2) =
      (first - second) ^ 2 / 4 := by
  rw [collisionPairMSE_decomposition]
  ring

/-- Explained-variance score relative to a positive registered scale. -/
noncomputable def CollisionPairR2
    (first second prediction scale : ℝ) : ℝ :=
  1 - CollisionPairMSE first second prediction / scale

/-- Numerical ceiling: an observation collision places an estimator-independent
upper bound on every deterministic R²-like score using the same scale. -/
theorem collisionPairR2_upper_bound
    (first second prediction scale : ℝ) (scalePositive : 0 < scale) :
    CollisionPairR2 first second prediction scale ≤
      1 - ((first - second) ^ 2 / 4) / scale := by
  have scaled :
      ((first - second) ^ 2 / 4) / scale ≤
        CollisionPairMSE first second prediction / scale := by
    exact (div_le_div_iff_of_pos_right scalePositive).2
      (collisionPairMSE_lower_bound first second prediction)
  unfold CollisionPairR2
  linarith

/-! ## Block-stable admission with exact fallback -/

/-- Realized gain relative to a safe baseline.  Rejected blocks use the
baseline exactly and therefore have zero gain. -/
def GatedBlockGain {Block : Type*}
    (admit : Block → Bool) (candidateGain : Block → ℝ) (block : Block) : ℝ :=
  if admit block then candidateGain block else 0

/-- A sound local certificate makes every admitted-or-fallback block safe. -/
theorem gatedBlockGain_nonnegative
    {Block : Type*} (admit : Block → Bool) (candidateGain : Block → ℝ)
    (certificateSound : ∀ block, admit block = true → 0 ≤ candidateGain block) :
    ∀ block, 0 ≤ GatedBlockGain admit candidateGain block := by
  intro block
  by_cases admitted : admit block = true
  · simpa [GatedBlockGain, admitted] using certificateSound block admitted
  · have rejected : admit block = false := Bool.eq_false_of_not_eq_true admitted
    simp [GatedBlockGain, rejected]

/-- Consequently, no nonnegative mixture of certified blocks can hide a loss
in a minority regime.  This is the formal stability guarantee required before
reporting aggregate predictive gain. -/
theorem gatedMixtureGain_nonnegative
    {Block : Type*} [Fintype Block]
    (mass : Block → ℝ) (admit : Block → Bool)
    (candidateGain : Block → ℝ)
    (massNonnegative : ∀ block, 0 ≤ mass block)
    (certificateSound : ∀ block, admit block = true → 0 ≤ candidateGain block) :
    0 ≤ ∑ block, mass block * GatedBlockGain admit candidateGain block := by
  exact Finset.sum_nonneg fun block _ =>
    mul_nonneg (massNonnegative block)
      (gatedBlockGain_nonnegative admit candidateGain certificateSound block)

end OCKIndividuationMSpaceComposition
