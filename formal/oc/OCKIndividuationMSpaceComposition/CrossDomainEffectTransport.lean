import OCKIndividuationMSpaceComposition.InterventionalContrastIdentification

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe uContext

/-!
# Cross-domain transport of intervention effects

This module separates three quantities which are frequently conflated:
population composition, context-conditional intervention effect, and the
evidence contract connecting source and target domains.  Reweighting and
selection-diagram transportability are mature prior art.  The definitions here
make their error budgets composable with the OC observation layer without
claiming those antecedents as OC novelty.
-/

/-- Average context-conditional intervention effect in a domain. -/
def domainAverageEffect
    {Context : Type uContext} [Fintype Context]
    (weight effect : Context → ℚ) : ℚ :=
  ∑ context, weight context * effect context

/-- Source effect reweighted to the target context distribution. -/
def reweightedSourceEffect
    {Context : Type uContext} [Fintype Context]
    (sourceWeight targetWeight sourceEffect : Context → ℚ) : ℚ :=
  ∑ context,
    sourceWeight context * (targetWeight context / sourceWeight context) *
      sourceEffect context

/--
Explicit static transport contract.  Positivity is not hidden: every target
context must be represented in the source.  Conditional effect stability is a
separate field from population composition.
-/
structure StaticEffectTransportContract
    (Context : Type uContext) [Fintype Context] where
  sourceWeight : Context → ℚ
  targetWeight : Context → ℚ
  sourceEffect : Context → ℚ
  targetEffect : Context → ℚ
  sourceWeightPositive : ∀ context, 0 < sourceWeight context
  targetWeightNonnegative : ∀ context, 0 ≤ targetWeight context
  targetWeightNormalized : ∑ context, targetWeight context = 1
  conditionalEffectStable : ∀ context, targetEffect context = sourceEffect context

/-- Exact standardization: source effects plus target weights identify target ATE. -/
theorem stable_conditional_effect_standardization_exact
    {Context : Type uContext} [Fintype Context]
    (contract : StaticEffectTransportContract Context) :
    domainAverageEffect contract.targetWeight contract.sourceEffect =
      domainAverageEffect contract.targetWeight contract.targetEffect := by
  unfold domainAverageEffect
  apply Finset.sum_congr rfl
  intro context _
  rw [contract.conditionalEffectStable]

/-- Exact inverse-odds reweighting under source overlap. -/
theorem positive_overlap_reweighting_exact
    {Context : Type uContext} [Fintype Context]
    (contract : StaticEffectTransportContract Context) :
    reweightedSourceEffect contract.sourceWeight contract.targetWeight
        contract.sourceEffect =
      domainAverageEffect contract.targetWeight contract.targetEffect := by
  unfold reweightedSourceEffect domainAverageEffect
  apply Finset.sum_congr rfl
  intro context _
  have sourceNonzero : contract.sourceWeight context ≠ 0 :=
    (contract.sourceWeightPositive context).ne'
  rw [contract.conditionalEffectStable]
  field_simp

/-! ## Quantitative misspecification and population-shift budgets -/

/-- Exact target-scale decomposition into transported source effect plus drift. -/
theorem target_effect_transport_decomposition
    {Context : Type uContext} [Fintype Context]
    (targetWeight sourceEffect targetEffect : Context → ℚ) :
    domainAverageEffect targetWeight targetEffect -
        domainAverageEffect targetWeight sourceEffect =
      ∑ context, targetWeight context *
        (targetEffect context - sourceEffect context) := by
  unfold domainAverageEffect
  rw [← Finset.sum_sub_distrib]
  apply Finset.sum_congr rfl
  intro context _
  ring

/-- Uniform conditional-effect drift `delta` gives target ATE error at most `delta`. -/
theorem conditional_effect_drift_bound
    {Context : Type uContext} [Fintype Context]
    (targetWeight sourceEffect targetEffect : Context → ℚ)
    (delta : ℚ)
    (weightNonnegative : ∀ context, 0 ≤ targetWeight context)
    (weightNormalized : ∑ context, targetWeight context = 1)
    (driftBound : ∀ context,
      |targetEffect context - sourceEffect context| ≤ delta) :
    |domainAverageEffect targetWeight targetEffect -
      domainAverageEffect targetWeight sourceEffect| ≤ delta := by
  rw [target_effect_transport_decomposition]
  calc
    |∑ context, targetWeight context *
        (targetEffect context - sourceEffect context)| ≤
      ∑ context, |targetWeight context *
        (targetEffect context - sourceEffect context)| :=
          Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ context, targetWeight context * delta := by
      apply Finset.sum_le_sum
      intro context _
      rw [abs_mul, abs_of_nonneg (weightNonnegative context)]
      exact mul_le_mul_of_nonneg_left (driftBound context)
        (weightNonnegative context)
    _ = delta := by
      rw [← Finset.sum_mul, weightNormalized]
      ring

/-- Population-composition shift is controlled by effect magnitude and L1 shift. -/
theorem population_shift_effect_bound
    {Context : Type uContext} [Fintype Context]
    (sourceWeight targetWeight effect : Context → ℚ)
    (effectBound : ℚ)
    (boundedEffect : ∀ context, |effect context| ≤ effectBound) :
    |domainAverageEffect targetWeight effect -
      domainAverageEffect sourceWeight effect| ≤
        effectBound * ∑ context, |targetWeight context - sourceWeight context| := by
  have difference :
      domainAverageEffect targetWeight effect -
          domainAverageEffect sourceWeight effect =
        ∑ context, (targetWeight context - sourceWeight context) * effect context := by
    unfold domainAverageEffect
    rw [← Finset.sum_sub_distrib]
    apply Finset.sum_congr rfl
    intro context _
    ring
  rw [difference]
  calc
    |∑ context, (targetWeight context - sourceWeight context) * effect context| ≤
      ∑ context, |(targetWeight context - sourceWeight context) * effect context| :=
        Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ context,
        |targetWeight context - sourceWeight context| * effectBound := by
      apply Finset.sum_le_sum
      intro context _
      rw [abs_mul]
      exact mul_le_mul_of_nonneg_left (boundedEffect context) (abs_nonneg _)
    _ = effectBound * ∑ context,
        |targetWeight context - sourceWeight context| := by
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro context _
      ring

/--
Combined robust transport bound.  It exposes distinct levers: conditional
mechanism drift `delta` and population-composition shift in L1 distance.
-/
theorem combined_cross_domain_transport_bound
    {Context : Type uContext} [Fintype Context]
    (sourceWeight targetWeight sourceEffect targetEffect : Context → ℚ)
    (delta effectBound : ℚ)
    (targetWeightNonnegative : ∀ context, 0 ≤ targetWeight context)
    (targetWeightNormalized : ∑ context, targetWeight context = 1)
    (driftBound : ∀ context,
      |targetEffect context - sourceEffect context| ≤ delta)
    (sourceEffectBounded : ∀ context, |sourceEffect context| ≤ effectBound) :
    |domainAverageEffect targetWeight targetEffect -
      domainAverageEffect sourceWeight sourceEffect| ≤
        delta + effectBound *
          ∑ context, |targetWeight context - sourceWeight context| := by
  have split :
      domainAverageEffect targetWeight targetEffect -
          domainAverageEffect sourceWeight sourceEffect =
        (domainAverageEffect targetWeight targetEffect -
          domainAverageEffect targetWeight sourceEffect) +
        (domainAverageEffect targetWeight sourceEffect -
          domainAverageEffect sourceWeight sourceEffect) := by ring
  rw [split]
  calc
    |(domainAverageEffect targetWeight targetEffect -
        domainAverageEffect targetWeight sourceEffect) +
      (domainAverageEffect targetWeight sourceEffect -
        domainAverageEffect sourceWeight sourceEffect)| ≤
      |domainAverageEffect targetWeight targetEffect -
        domainAverageEffect targetWeight sourceEffect| +
      |domainAverageEffect targetWeight sourceEffect -
        domainAverageEffect sourceWeight sourceEffect| := abs_add_le _ _
    _ ≤ delta + effectBound *
        ∑ context, |targetWeight context - sourceWeight context| :=
      add_le_add
        (conditional_effect_drift_bound targetWeight sourceEffect targetEffect
          delta targetWeightNonnegative targetWeightNormalized driftBound)
        (population_shift_effect_bound sourceWeight targetWeight sourceEffect
          effectBound sourceEffectBounded)

/-! ## Composition and impossibility -/

/-- Conditional mechanism-drift budgets compose additively across domains. -/
theorem conditional_effect_drift_composes
    {Context : Type uContext}
    (effect0 effect1 effect2 : Context → ℚ)
    (delta01 delta12 : ℚ)
    (drift01 : ∀ context, |effect1 context - effect0 context| ≤ delta01)
    (drift12 : ∀ context, |effect2 context - effect1 context| ≤ delta12) :
    ∀ context, |effect2 context - effect0 context| ≤ delta01 + delta12 := by
  intro context
  have decompose :
      effect2 context - effect0 context =
        (effect1 context - effect0 context) +
          (effect2 context - effect1 context) := by ring
  rw [decompose]
  exact (abs_add_le _ _).trans (add_le_add (drift01 context) (drift12 context))

def sourcePointWeight (context : Bool) : ℚ := if context then 0 else 1
def targetPointWeight (context : Bool) : ℚ := if context then 1 else 0
def zeroContextEffect (_context : Bool) : ℚ := 0
def hiddenTargetEffect (context : Bool) : ℚ := if context then 1 else 0

/--
Overlap no-go: two effect worlds are identical on every source-supported
context and therefore have the same complete source average, but target ATEs
are zero and one.  Unconstrained target-only effect modification cannot be
repaired by additional source observations.
-/
theorem missing_overlap_blocks_cross_domain_effect_identification :
    (∀ context, sourcePointWeight context ≠ 0 →
      zeroContextEffect context = hiddenTargetEffect context) ∧
    domainAverageEffect sourcePointWeight zeroContextEffect =
      domainAverageEffect sourcePointWeight hiddenTargetEffect ∧
    domainAverageEffect targetPointWeight zeroContextEffect = 0 ∧
    domainAverageEffect targetPointWeight hiddenTargetEffect = 1 := by
  constructor
  · intro context supported
    cases context
    · norm_num [zeroContextEffect, hiddenTargetEffect]
    · simp [sourcePointWeight] at supported
  · norm_num [domainAverageEffect, sourcePointWeight, targetPointWeight,
      zeroContextEffect, hiddenTargetEffect]

/-- If model-error radius consumes the target gap, sampling cannot certify order. -/
theorem transport_model_error_floor_blocks_policy_order
    (samplingError transportError policyGap : ℚ)
    (samplingNonnegative : 0 ≤ samplingError)
    (errorFloorConsumesGap : policyGap ≤ 2 * transportError) :
    ¬ (2 * (samplingError + transportError) < policyGap) := by
  intro claimed
  linarith

end OCKIndividuationMSpaceComposition
