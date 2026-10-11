import OCMaturityCompletionCycle.QuantitativeComposition
import Mathlib.Tactic.NormNum

/-!
# Finite countermodels delimiting the quantitative API
-/

namespace OCMaturityCompletionCycle

/-! ## Correlated parallel laws -/

def correlatedPairMass : Bool × Bool → ℚ
  | (false, false) => 1 / 2
  | (true, true) => 1 / 2
  | _ => 0

def anticorrelatedPairMass : Bool × Bool → ℚ
  | (false, true) => 1 / 2
  | (true, false) => 1 / 2
  | _ => 0

def correlatedPairProbability : FiniteProbabilityMass (Bool × Bool) where
  mass := correlatedPairMass
  nonnegative outcome := by
    rcases outcome with ⟨left, right⟩
    cases left <;> cases right <;> norm_num [correlatedPairMass]
  normalized := by
    norm_num [Fintype.sum_prod_type, Fintype.sum_bool, correlatedPairMass]

def anticorrelatedPairProbability : FiniteProbabilityMass (Bool × Bool) where
  mass := anticorrelatedPairMass
  nonnegative outcome := by
    rcases outcome with ⟨left, right⟩
    cases left <;> cases right <;> norm_num [anticorrelatedPairMass]
  normalized := by
    norm_num [Fintype.sum_prod_type, Fintype.sum_bool, anticorrelatedPairMass]

/-- Equal one-coordinate marginals do not control a correlated joint law. -/
theorem correlatedParallel_equalMarginals_but_jointTVOne :
    (∀ left,
      (∑ right, correlatedPairMass (left, right)) =
        ∑ right, anticorrelatedPairMass (left, right)) ∧
    (∀ right,
      (∑ left, correlatedPairMass (left, right)) =
        ∑ left, anticorrelatedPairMass (left, right)) ∧
    finiteTotalVariation correlatedPairProbability
      anticorrelatedPairProbability = 1 := by
  constructor
  · intro left
    cases left <;> norm_num [correlatedPairMass, anticorrelatedPairMass]
  constructor
  · intro right
    cases right <;> norm_num [correlatedPairMass, anticorrelatedPairMass]
  · norm_num [finiteTotalVariation, correlatedPairProbability,
      anticorrelatedPairProbability, correlatedPairMass,
      anticorrelatedPairMass, Fintype.sum_prod_type, Fintype.sum_bool,
      abs_of_nonneg]

/-! ## Unconstrained feedback -/

def tenthError (_ : Nat) : ℚ := 1 / 10

/-- A positive local error can exceed one under an unconstrained finite loop. -/
theorem unconstrainedFeedback_localTenth_accumulatesPastOne :
    accumulatedLocalError tenthError 20 = 2 ∧
      ¬ accumulatedLocalError tenthError 20 ≤ 1 := by
  norm_num [accumulatedLocalError, tenthError]

/-! ## Metric tolerance is not an identity quotient -/

/-- Radius-one tolerance on the line is not transitive. -/
theorem unitTolerance_on_rationals_is_not_transitive :
    |(0 : ℚ) - 1| ≤ 1 ∧ |(1 : ℚ) - 2| ≤ 1 ∧ ¬ |(0 : ℚ) - 2| ≤ 1 := by
  norm_num

/-! ## Hidden common cause -/

/-- Existing finite hidden-cause fixture, exposed as a quantitative no-go input. -/
theorem hiddenCommonCause_requires_joint_state :
    (∀ value, firstMarginal .correlated value = firstMarginal .anticorrelated value) ∧
    (∀ value, secondMarginal .correlated value = secondMarginal .anticorrelated value) ∧
    jointMass .correlated (false, false) ≠
      jointMass .anticorrelated (false, false) :=
  hidden_common_cause_breaks_local_composition

/-! ## Identity/state incompatibility -/

def boolIdentityKernel : FiniteControlledKernel Bool (Unit × Unit × Unit) where
  mass state _ target := if target = state then 1 else 0
  nonnegative state input target := by
    split <;> norm_num
  normalized state input := by
    cases state <;> simp

def emptyCapabilityProfile : DynamicsCapabilityProfile :=
  ⟨fun _ => False⟩

def boolOpenProcess : FiniteOpenProcess Bool Unit Unit Unit where
  transition := boolIdentityKernel
  capabilities := emptyCapabilityProfile

def boolIdentityAbstraction : ContextualAbstraction
    Bool Unit Unit Unit Bool Unit Unit Unit where
  fine := boolOpenProcess
  abstract := boolOpenProcess
  stateMap := id
  historyEncoder _ _ := false
  contextMap := id
  boundaryMap := id
  actionMap := id

def incompatibleBoolIdentity : IdentityPresentation Bool Bool where
  stateOf := id
  continuationEvidence _ _ := False
  assembledTogether _ _ := True

/-- An assembly that merges distinct abstract states fails the required gate. -/
theorem identityStateMismatch_failsCompatibilityGate :
    ¬ IdentityStateCompatibility boolIdentityAbstraction
      incompatibleBoolIdentity := by
  intro compatible
  have impossible := compatible (left := false) (right := true) trivial
  exact Bool.false_ne_true impossible

/-! ## A normalized but independently supplied path law can be wrong -/

def zeroHorizonBoolExperiment : FinitePathExperiment Bool Unit Unit Unit where
  process := boolOpenProcess
  horizon := 0
  initial := finiteDirac false
  policy _ := ((), (), ())

def wrongZeroHorizonBoolPathLaw :
    FiniteProbabilityMass (FiniteStatePath Bool 0) :=
  finiteDirac true

/-- Normalization alone cannot replace kernel-induced law realization. -/
theorem independentlySuppliedWrongPathLaw_failsRealization :
    ¬ LawRealization zeroHorizonBoolExperiment
      wrongZeroHorizonBoolPathLaw := by
  intro realized
  have atFalse := congrFun realized false
  change (0 : ℚ) = 1 at atFalse
  norm_num at atFalse

end OCMaturityCompletionCycle
