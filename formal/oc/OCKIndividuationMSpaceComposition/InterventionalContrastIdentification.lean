import OCKIndividuationMSpaceComposition.InformativeCensoringCorrection
import Mathlib.Algebra.Order.BigOperators.Group.Finset

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe uContext

/-!
# Interventional contrast identification and robust policy comparison

This module keeps three surfaces separate: latent potential outcomes,
observational assignment, and an identification contract.  The g-formula and
inverse-propensity algebra are mature causal-inference mathematics.  The OC
bridge supplied here composes their arm-level error with the observation and
visibility budgets proved in the preceding modules.
-/

/-- Population-weighted average treatment effect over registered contexts. -/
def weightedAverageTreatmentEffect
    {Context : Type uContext} [Fintype Context]
    (weight untreated treated : Context → ℚ) : ℚ :=
  ∑ context, weight context * (treated context - untreated context)

/--
Identification contract: within every registered context, observed conditional
arm means equal the corresponding potential-outcome means, and both arms have
positive assignment probability.
-/
structure StratifiedInterventionIdentification
    (Context : Type uContext) [Fintype Context] where
  weight : Context → ℚ
  weight_nonnegative : ∀ context, 0 ≤ weight context
  weight_normalized : ∑ context, weight context = 1
  untreatedPotential : Context → ℚ
  treatedPotential : Context → ℚ
  observedUntreated : Context → ℚ
  observedTreated : Context → ℚ
  propensity : Context → ℚ
  propensity_positive : ∀ context, 0 < propensity context
  propensity_below_one : ∀ context, propensity context < 1
  untreated_exchangeability_consistency :
    ∀ context, observedUntreated context = untreatedPotential context
  treated_exchangeability_consistency :
    ∀ context, observedTreated context = treatedPotential context

/-- The stratified observational g-formula equals the latent ATE under contract. -/
theorem stratified_g_formula_identifies_ate
    {Context : Type uContext} [Fintype Context]
    (contract : StratifiedInterventionIdentification Context) :
    weightedAverageTreatmentEffect contract.weight
        contract.observedUntreated contract.observedTreated =
      weightedAverageTreatmentEffect contract.weight
        contract.untreatedPotential contract.treatedPotential := by
  unfold weightedAverageTreatmentEffect
  apply Finset.sum_congr rfl
  intro context _
  rw [contract.untreated_exchangeability_consistency,
    contract.treated_exchangeability_consistency]

/-- Population inverse-propensity contrast under the registered strata. -/
def inversePropensityTreatmentEffect
    {Context : Type uContext} [Fintype Context]
    (weight propensity untreated treated : Context → ℚ) : ℚ :=
  ∑ context, weight context *
    (propensity context * treated context / propensity context -
      (1 - propensity context) * untreated context /
        (1 - propensity context))

/-- IPW and the g-formula coincide exactly under positivity. -/
theorem inverse_propensity_identifies_weighted_ate
    {Context : Type uContext} [Fintype Context]
    (weight propensity untreated treated : Context → ℚ)
    (positive : ∀ context, 0 < propensity context)
    (belowOne : ∀ context, propensity context < 1) :
    inversePropensityTreatmentEffect weight propensity untreated treated =
      weightedAverageTreatmentEffect weight untreated treated := by
  unfold inversePropensityTreatmentEffect weightedAverageTreatmentEffect
  apply Finset.sum_congr rfl
  intro context _
  have propensityNonzero : propensity context ≠ 0 := (positive context).ne'
  have complementNonzero : 1 - propensity context ≠ 0 := by
    linarith [belowOne context]
  field_simp

/-! ## Observational equivalence does not identify intervention effects -/

/-- Fixed observational assignment in a two-unit countermodel. -/
def twoUnitAssignment (unit : Bool) : Bool := unit

/-- Realized outcome selects only the assigned potential outcome. -/
def realizedPotentialOutcome
    (untreated treated : Bool → ℚ) (unit : Bool) : ℚ :=
  if twoUnitAssignment unit then treated unit else untreated unit

/-- Two-unit equally weighted causal contrast. -/
def twoUnitAverageTreatmentEffect
    (untreated treated : Bool → ℚ) : ℚ :=
  ((treated false - untreated false) +
    (treated true - untreated true)) / 2

def causalWorldAUntreated (unit : Bool) : ℚ := if unit then 1 else 0
def causalWorldATreated (unit : Bool) : ℚ := if unit then 1 else 0
def causalWorldBUntreated (_unit : Bool) : ℚ := 0
def causalWorldBTreated (_unit : Bool) : ℚ := 1

/--
Sharp no-go: complete observed outcomes under the fixed assignment are equal in
two causal worlds, while their average intervention effects are `0` and `1`.
-/
theorem observational_outcomes_do_not_identify_average_treatment_effect :
    (∀ unit,
      realizedPotentialOutcome causalWorldAUntreated causalWorldATreated unit =
        realizedPotentialOutcome causalWorldBUntreated causalWorldBTreated unit) ∧
      twoUnitAverageTreatmentEffect causalWorldAUntreated causalWorldATreated = 0 ∧
      twoUnitAverageTreatmentEffect causalWorldBUntreated causalWorldBTreated = 1 := by
  constructor
  · intro unit
    cases unit <;> norm_num [realizedPotentialOutcome, twoUnitAssignment,
      causalWorldAUntreated, causalWorldATreated, causalWorldBUntreated,
      causalWorldBTreated]
  · norm_num [twoUnitAverageTreatmentEffect, causalWorldAUntreated,
      causalWorldATreated, causalWorldBUntreated, causalWorldBTreated]

/-! ## Confounding can reverse the interpretation of association -/

def confoundingWeight (_context : Bool) : ℚ := 1 / 2
def confoundingRisk (context : Bool) : ℚ := if context then 1 else 0
def confoundingPropensity (context : Bool) : ℚ := if context then 3 / 4 else 1 / 4

def observationalTreatedMean
    {Context : Type uContext} [Fintype Context]
    (weight propensity treated : Context → ℚ) : ℚ :=
  (∑ context, weight context * propensity context * treated context) /
    ∑ context, weight context * propensity context

def observationalUntreatedMean
    {Context : Type uContext} [Fintype Context]
    (weight propensity untreated : Context → ℚ) : ℚ :=
  (∑ context, weight context * (1 - propensity context) * untreated context) /
    ∑ context, weight context * (1 - propensity context)

/--
Simpson-type countermodel: treatment has zero effect in both strata, but
selection into treatment creates an unadjusted association of `1/2`.
-/
theorem confounding_can_create_nonzero_association_with_zero_causal_effect :
    weightedAverageTreatmentEffect confoundingWeight confoundingRisk
        confoundingRisk = 0 ∧
      observationalTreatedMean confoundingWeight confoundingPropensity
          confoundingRisk -
        observationalUntreatedMean confoundingWeight confoundingPropensity
          confoundingRisk = 1 / 2 := by
  norm_num [weightedAverageTreatmentEffect, observationalTreatedMean,
    observationalUntreatedMean, confoundingWeight, confoundingRisk,
    confoundingPropensity]

/-! ## Arm-error propagation into causal contrasts -/

/-- Uniform arm-mean error `epsilon` yields ATE error at most `2*epsilon`. -/
theorem weighted_ate_estimation_error_bound
    {Context : Type uContext} [Fintype Context]
    (weight trueUntreated trueTreated estimatedUntreated estimatedTreated :
      Context → ℚ)
    (epsilon : ℚ)
    (weightNonnegative : ∀ context, 0 ≤ weight context)
    (weightNormalized : ∑ context, weight context = 1)
    (untreatedError : ∀ context,
      |estimatedUntreated context - trueUntreated context| ≤ epsilon)
    (treatedError : ∀ context,
      |estimatedTreated context - trueTreated context| ≤ epsilon) :
    |weightedAverageTreatmentEffect weight estimatedUntreated estimatedTreated -
      weightedAverageTreatmentEffect weight trueUntreated trueTreated| ≤
        2 * epsilon := by
  have pointwise : ∀ context,
      |weight context *
        ((estimatedTreated context - estimatedUntreated context) -
          (trueTreated context - trueUntreated context))| ≤
        weight context * (2 * epsilon) := by
    intro context
    rw [abs_mul, abs_of_nonneg (weightNonnegative context)]
    apply mul_le_mul_of_nonneg_left _ (weightNonnegative context)
    have rearranged :
        (estimatedTreated context - estimatedUntreated context) -
            (trueTreated context - trueUntreated context) =
          (estimatedTreated context - trueTreated context) -
            (estimatedUntreated context - trueUntreated context) := by ring
    rw [rearranged]
    have triangle := abs_sub_le
      (estimatedTreated context - trueTreated context) (0 : ℚ)
      (estimatedUntreated context - trueUntreated context)
    calc
      |(estimatedTreated context - trueTreated context) -
          (estimatedUntreated context - trueUntreated context)| ≤
        |estimatedTreated context - trueTreated context| +
          |estimatedUntreated context - trueUntreated context| :=
            by simpa only [sub_zero, zero_sub, abs_neg] using triangle
      _ ≤ epsilon + epsilon :=
        add_le_add (treatedError context) (untreatedError context)
      _ = 2 * epsilon := by ring
  have sumDifference :
      weightedAverageTreatmentEffect weight estimatedUntreated estimatedTreated -
          weightedAverageTreatmentEffect weight trueUntreated trueTreated =
        ∑ context, weight context *
          ((estimatedTreated context - estimatedUntreated context) -
            (trueTreated context - trueUntreated context)) := by
    unfold weightedAverageTreatmentEffect
    rw [← Finset.sum_sub_distrib]
    apply Finset.sum_congr rfl
    intro context _
    ring
  rw [sumDifference]
  calc
    |∑ context,
        weight context *
          ((estimatedTreated context - estimatedUntreated context) -
            (trueTreated context - trueUntreated context))| ≤
      ∑ context,
        |weight context *
          ((estimatedTreated context - estimatedUntreated context) -
            (trueTreated context - trueUntreated context))| :=
        Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ context, weight context * (2 * epsilon) := by
      apply Finset.sum_le_sum
      intro context _
      exact pointwise context
    _ = 2 * epsilon := by
      rw [← Finset.sum_mul, weightNormalized]
      ring

/-- Two estimated causal policies retain their true ordering beyond `4*epsilon`. -/
theorem causal_policy_order_stable_of_arm_error
    (truePreferred trueCompetitor estimatedPreferred estimatedCompetitor
      epsilon : ℚ)
    (preferredError : |estimatedPreferred - truePreferred| ≤ 2 * epsilon)
    (competitorError : |estimatedCompetitor - trueCompetitor| ≤ 2 * epsilon)
    (margin : trueCompetitor + 4 * epsilon < truePreferred) :
    estimatedCompetitor < estimatedPreferred := by
  have preferredLower := (abs_le.mp preferredError).1
  have competitorUpper := (abs_le.mp competitorError).2
  linarith

/-! ## Composition with censoring-adjusted observation error -/

/-- Causal-contrast radius from two arms with the same latent-scale radius. -/
noncomputable def censoringAdjustedCausalContrastRadius
    (observationError visibilityError visibilityFloor : ℝ) : ℝ :=
  2 * censoringAdjustedRadius observationError visibilityError visibilityFloor

/-- Exact causal-policy separation criterion after censoring adjustment. -/
theorem censoringAdjusted_causal_separation_iff
    (observationError visibilityError visibilityFloor causalGap : ℝ)
    (visibilityFloorPositive : 0 < visibilityFloor) :
    2 * censoringAdjustedCausalContrastRadius
          observationError visibilityError visibilityFloor < causalGap ↔
      4 * (observationError + visibilityError) <
        causalGap * visibilityFloor := by
  unfold censoringAdjustedCausalContrastRadius censoringAdjustedRadius
  rw [show 2 * (2 * ((observationError + visibilityError) / visibilityFloor)) =
      (4 * (observationError + visibilityError)) / visibilityFloor by ring,
    div_lt_iff₀ visibilityFloorPositive]

/-- Visibility-model error can consume the full causal-policy margin. -/
theorem visibility_error_can_make_causal_policy_comparison_impossible
    (observationError visibilityError visibilityFloor causalGap : ℝ)
    (observationErrorNonnegative : 0 ≤ observationError)
    (visibilityFloorPositive : 0 < visibilityFloor)
    (floorConsumesMargin : causalGap * visibilityFloor ≤ 4 * visibilityError) :
    ¬ 2 * censoringAdjustedCausalContrastRadius
        observationError visibilityError visibilityFloor < causalGap := by
  rw [censoringAdjusted_causal_separation_iff _ _ _ _ visibilityFloorPositive]
  linarith

end OCKIndividuationMSpaceComposition
