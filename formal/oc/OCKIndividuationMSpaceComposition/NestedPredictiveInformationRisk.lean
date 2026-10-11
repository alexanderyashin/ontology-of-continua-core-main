import Mathlib.Data.Set.Basic
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

/-!
# Nested predictive information and finite-estimator reversal

The hybrid BPI successor joins a local ordered-history model class with a
task-typed context class.  At the optimal-risk level, enlarging the admissible
class cannot increase risk.  A fitted finite-sample predictor can nevertheless
lose when its estimation or transport penalty exceeds the nonnegative
information gain.  The distinction is the mathematical boundary between the
positive refinement theorem and the observed finite-estimator counterexample.
-/

section

variable {Model : Type*}

/-- An attained optimum over a declared predictive model class. -/
structure OptimalRiskWitness (risk : Model → ℝ) (admissible : Set Model) where
  predictor : Model
  predictor_admissible : predictor ∈ admissible
  optimal : ∀ candidate ∈ admissible, risk predictor ≤ risk candidate

/-- The risk attained by an explicit optimal witness. -/
def OptimalRiskWitness.value
    {risk : Model → ℝ} {admissible : Set Model}
    (witness : OptimalRiskWitness risk admissible) : ℝ :=
  risk witness.predictor

/-- Joining predictive information enlarges the admissible class, so its
attained optimal risk cannot exceed the old attained optimum. -/
theorem optimal_risk_antitone_under_model_refinement
    (risk : Model → ℝ) (baseClass refinedClass : Set Model)
    (subset : baseClass ⊆ refinedClass)
    (localOptimal : OptimalRiskWitness risk baseClass)
    (jointOptimal : OptimalRiskWitness risk refinedClass) :
    jointOptimal.value ≤ localOptimal.value := by
  exact jointOptimal.optimal localOptimal.predictor
    (subset localOptimal.predictor_admissible)

/-- Strict improvement follows exactly when the refined class contains a
candidate strictly below the old optimum. -/
theorem strict_optimal_improvement_of_residual_signal
    (risk : Model → ℝ) (baseClass refinedClass : Set Model)
    (localOptimal : OptimalRiskWitness risk baseClass)
    (jointOptimal : OptimalRiskWitness risk refinedClass)
    (candidate : Model) (candidate_admissible : candidate ∈ refinedClass)
    (residualSignal : risk candidate < localOptimal.value) :
    jointOptimal.value < localOptimal.value := by
  exact lt_of_le_of_lt
    (jointOptimal.optimal candidate candidate_admissible) residualSignal

/-- Bayes/optimal information gain from the refined class. -/
def PredictiveInformationGain
    {risk : Model → ℝ} {baseClass refinedClass : Set Model}
    (localOptimal : OptimalRiskWitness risk baseClass)
    (jointOptimal : OptimalRiskWitness risk refinedClass) : ℝ :=
  localOptimal.value - jointOptimal.value

/-- Excess risk of a fitted predictor over the refined optimum.  It may include
finite-sample estimation, misspecification and transport error. -/
def PredictiveEstimationPenalty
    {risk : Model → ℝ} {refinedClass : Set Model}
    (jointOptimal : OptimalRiskWitness risk refinedClass) (fitted : Model) : ℝ :=
  risk fitted - jointOptimal.value

/-- Exact operational law: a fitted hybrid beats the old optimum iff its
estimation/transport penalty is smaller than the information gain. -/
theorem fitted_refinement_beats_local_iff_penalty_lt_gain
    (risk : Model → ℝ) (baseClass refinedClass : Set Model)
    (localOptimal : OptimalRiskWitness risk baseClass)
    (jointOptimal : OptimalRiskWitness risk refinedClass)
    (fitted : Model) :
    risk fitted < localOptimal.value ↔
      PredictiveEstimationPenalty jointOptimal fitted <
        PredictiveInformationGain localOptimal jointOptimal := by
  simp only [PredictiveEstimationPenalty, PredictiveInformationGain,
    OptimalRiskWitness.value]
  constructor <;> intro comparison <;> linarith

/-- Under a genuine model refinement the optimal information gain is
nonnegative. -/
theorem predictive_information_gain_nonnegative
    (risk : Model → ℝ) (baseClass refinedClass : Set Model)
    (subset : baseClass ⊆ refinedClass)
    (localOptimal : OptimalRiskWitness risk baseClass)
    (jointOptimal : OptimalRiskWitness risk refinedClass) :
    0 ≤ PredictiveInformationGain localOptimal jointOptimal := by
  unfold PredictiveInformationGain
  linarith [optimal_risk_antitone_under_model_refinement
    risk baseClass refinedClass subset localOptimal jointOptimal]

/-- No-go boundary: if refinement creates no optimal information gain and a
fitted predictor has nonnegative excess risk, strict empirical improvement is
impossible. -/
theorem no_strict_fitted_improvement_without_gain
    (risk : Model → ℝ) (baseClass refinedClass : Set Model)
    (localOptimal : OptimalRiskWitness risk baseClass)
    (jointOptimal : OptimalRiskWitness risk refinedClass)
    (fitted : Model)
    (noGain : PredictiveInformationGain localOptimal jointOptimal = 0)
    (nonnegativePenalty : 0 ≤ PredictiveEstimationPenalty jointOptimal fitted) :
    ¬ risk fitted < localOptimal.value := by
  rw [fitted_refinement_beats_local_iff_penalty_lt_gain
    risk baseClass refinedClass localOptimal jointOptimal fitted, noGain]
  exact not_lt_of_ge nonnegativePenalty

/-- Quantitative failure law: the fitted refinement is worse than the old
optimum exactly when its penalty exceeds the information gain. -/
theorem fitted_refinement_worse_iff_gain_lt_penalty
    (risk : Model → ℝ) (baseClass refinedClass : Set Model)
    (localOptimal : OptimalRiskWitness risk baseClass)
    (jointOptimal : OptimalRiskWitness risk refinedClass)
    (fitted : Model) :
    localOptimal.value < risk fitted ↔
      PredictiveInformationGain localOptimal jointOptimal <
        PredictiveEstimationPenalty jointOptimal fitted := by
  simp only [PredictiveEstimationPenalty, PredictiveInformationGain,
    OptimalRiskWitness.value]
  constructor <;> intro comparison <;> linarith

/-- Concrete countermodel: class refinement does not make every fitted member
safe.  The refined optimum equals the local optimum, while another admissible
refined predictor has strictly larger risk. -/
theorem exists_finite_estimator_reversal_under_refinement :
    ∃ (risk : Bool → ℝ) (baseClass refinedClass : Set Bool),
      baseClass ⊆ refinedClass ∧
      ∃ (localOptimal : OptimalRiskWitness risk baseClass)
        (jointOptimal : OptimalRiskWitness risk refinedClass) (fitted : Bool),
        jointOptimal.value = localOptimal.value ∧
        fitted ∈ refinedClass ∧
        localOptimal.value < risk fitted := by
  let risk : Bool → ℝ := fun model => if model then 1 else 0
  let baseClass : Set Bool := {false}
  let refinedClass : Set Bool := Set.univ
  have localOptimal : OptimalRiskWitness risk baseClass := by
    refine ⟨false, by simp [baseClass], ?_⟩
    intro candidate candidateLocal
    simp only [baseClass, Set.mem_singleton_iff] at candidateLocal
    subst candidate
    exact le_rfl
  have jointOptimal : OptimalRiskWitness risk refinedClass := by
    refine ⟨false, by simp [refinedClass], ?_⟩
    intro candidate _
    cases candidate <;> norm_num [risk]
  have localPredictor : localOptimal.predictor = false := by
    simpa [baseClass] using localOptimal.predictor_admissible
  have equalOptimalValues : jointOptimal.value = localOptimal.value := by
    unfold OptimalRiskWitness.value
    rw [localPredictor]
    apply le_antisymm
    · exact jointOptimal.optimal false (by simp [refinedClass])
    · cases jointOptimal.predictor <;> norm_num [risk]
  refine ⟨risk, baseClass, refinedClass,
    by intro candidate _; simp [refinedClass],
    localOptimal, jointOptimal, true, equalOptimalValues,
    by simp [refinedClass], ?_⟩
  unfold OptimalRiskWitness.value
  rw [localPredictor]
  norm_num [risk]

/-- A reserved open-world code makes a finite encoder total without learning a
new code from held-out outcomes. -/
def totalizeWithOOV {Symbol Code : Type*}
    (known : Symbol → Bool) (encodeKnown : Symbol → Code) (oov : Code)
    (symbol : Symbol) : Code :=
  if known symbol then encodeKnown symbol else oov

/-- Every symbol declared unknown is mapped to the reserved OOV code. -/
theorem totalizeWithOOV_of_unknown {Symbol Code : Type*}
    (known : Symbol → Bool) (encodeKnown : Symbol → Code) (oov : Code)
    (symbol : Symbol) (unknown : known symbol = false) :
    totalizeWithOOV known encodeKnown oov symbol = oov := by
  simp [totalizeWithOOV, unknown]

/-- No-go boundary of OOV totalization: any two unknown symbols collide unless
another observation refines the encoder. -/
theorem totalizeWithOOV_collision {Symbol Code : Type*}
    (known : Symbol → Bool) (encodeKnown : Symbol → Code) (oov : Code)
    (left right : Symbol)
    (leftUnknown : known left = false) (rightUnknown : known right = false) :
    totalizeWithOOV known encodeKnown oov left =
      totalizeWithOOV known encodeKnown oov right := by
  simp [totalizeWithOOV, leftUnknown, rightUnknown]

/-- Quantitative no-go theorem.  If two states with binary targets zero and one
have the same observable code, every real-valued predictor factoring through
that code has average squared error at least `1/4`.  Equality is attained by
the unresolved prediction `1/2`. -/
theorem binary_collision_average_squared_error_lower_bound
    {State Observation : Type*}
    (encode : State → Observation) (predict : Observation → ℝ)
    (zeroState oneState : State)
    (collision : encode zeroState = encode oneState) :
    ((predict (encode zeroState) - 0) ^ 2 +
        (predict (encode oneState) - 1) ^ 2) / 2 ≥ (1 : ℝ) / 4 := by
  rw [collision]
  nlinarith [sq_nonneg (predict (encode oneState) - (1 : ℝ) / 2)]

/-- A type-indexed OOV family totalizes an encoder while retaining the coarse
type needed by downstream operators. -/
def typedTotalizeWithOOV {Symbol Code TypeTag : Type*}
    (known : Symbol → Bool) (encodeKnown : Symbol → Code)
    (typeOf : Symbol → TypeTag) (oovFor : TypeTag → Code)
    (symbol : Symbol) : Code :=
  if known symbol then encodeKnown symbol else oovFor (typeOf symbol)

/-- If the known encoder and every reserved OOV code preserve the declared
type, then typed totalization preserves it for every symbol. -/
theorem typedTotalizeWithOOV_preserves_type
    {Symbol Code TypeTag : Type*}
    (known : Symbol → Bool) (encodeKnown : Symbol → Code)
    (typeOf : Symbol → TypeTag) (oovFor : TypeTag → Code)
    (codeType : Code → TypeTag)
    (knownPreserves : ∀ symbol, known symbol = true →
      codeType (encodeKnown symbol) = typeOf symbol)
    (oovPreserves : ∀ typeTag, codeType (oovFor typeTag) = typeTag)
    (symbol : Symbol) :
    codeType (typedTotalizeWithOOV known encodeKnown typeOf oovFor symbol) =
      typeOf symbol := by
  cases h : known symbol with
  | false => simpa [typedTotalizeWithOOV, h] using oovPreserves (typeOf symbol)
  | true => simpa [typedTotalizeWithOOV, h] using knownPreserves symbol h

/-- Type preservation does not recover within-type identity: two unknown
symbols of the same coarse type receive the same typed OOV code. -/
theorem typedTotalizeWithOOV_collision_of_same_type
    {Symbol Code TypeTag : Type*}
    (known : Symbol → Bool) (encodeKnown : Symbol → Code)
    (typeOf : Symbol → TypeTag) (oovFor : TypeTag → Code)
    (left right : Symbol)
    (leftUnknown : known left = false) (rightUnknown : known right = false)
    (sameType : typeOf left = typeOf right) :
    typedTotalizeWithOOV known encodeKnown typeOf oovFor left =
      typedTotalizeWithOOV known encodeKnown typeOf oovFor right := by
  simp [typedTotalizeWithOOV, leftUnknown, rightUnknown, sameType]

end

end OCKIndividuationMSpaceComposition
