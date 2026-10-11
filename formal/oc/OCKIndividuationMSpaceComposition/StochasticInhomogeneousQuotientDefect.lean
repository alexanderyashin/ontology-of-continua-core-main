import OCKIndividuationMSpaceComposition.StochasticGradualNoncontractiveQuotientDefect

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

/-!
# Exact inhomogeneous quotient-defect accumulation

This module removes the constant-defect assumption.  For any registered
sequence of valid rational row defects `p_t`, a finite time-inhomogeneous
Markov process realizes the exact transported-law error

`TV_h = 1 - product_{t<h} (1-p_t)`.

The construction proves sharpness of the product/hazard calculus at the level
of actual OC quotient transport, rather than postulating a scalar adapter.
-/

def inhomogeneousQuotientFineSequence
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) :
    Nat → FiniteControlledKernel NoncontractiveQuotientFineState Unit :=
  fun step => gradualNoncontractiveKernel
    (defect step) (valid step).1 (valid step).2

def inhomogeneousQuotientAbstractSequence
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) :
    Nat → FiniteControlledKernel Bool Unit :=
  fun step => gradualNoncontractiveRepresentativeKernel
    (defect step) (valid step).1 (valid step).2

/-- At every step the operational same-cell row defect is the registered
time-local value, not merely bounded by it. -/
theorem inhomogeneous_same_cell_row_tv_exact
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) (step : Nat) :
    sameCellRowTV
      (inhomogeneousQuotientFineSequence defect valid step)
      noncontractiveQuotientEncode
      NoncontractiveQuotientFineState.hidden
      NoncontractiveQuotientFineState.representative () = defect step := by
  exact gradual_same_cell_row_tv_exact
    (defect step) (valid step).1 (valid step).2

/-- Exact unresolved hidden mass is the product survival law. -/
theorem inhomogeneous_hidden_mass_exact
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) :
    ∀ horizon,
      (evolveMany (inhomogeneousQuotientFineSequence defect valid)
        noncontractiveActionSequence horizon noncontractiveHiddenInitial).mass
          NoncontractiveQuotientFineState.hidden =
        barrierSurvival defect horizon := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, barrierSurvival, noncontractiveHiddenInitial,
        finiteDirac]
  | succ horizon inductionHypothesis =>
      rw [barrierSurvival_succ]
      simp [evolveMany, evolveFiniteProbability,
        inhomogeneousQuotientFineSequence, gradualNoncontractiveKernel,
        noncontractiveQuotientFineState_univ, inductionHypothesis]

/-- The selected representative remains unreachable from the hidden initial
law under an arbitrary valid defect schedule. -/
theorem inhomogeneous_representative_mass_zero
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) :
    ∀ horizon,
      (evolveMany (inhomogeneousQuotientFineSequence defect valid)
        noncontractiveActionSequence horizon noncontractiveHiddenInitial).mass
          NoncontractiveQuotientFineState.representative = 0 := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, noncontractiveHiddenInitial, finiteDirac]
  | succ horizon inductionHypothesis =>
      simp [evolveMany, evolveFiniteProbability,
        inhomogeneousQuotientFineSequence, gradualNoncontractiveKernel,
        noncontractiveQuotientFineState_univ, inductionHypothesis]

/-- Exact escaped mass is the cumulative defect-hazard law. -/
theorem inhomogeneous_absorbed_mass_exact
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) :
    ∀ horizon,
      (evolveMany (inhomogeneousQuotientFineSequence defect valid)
        noncontractiveActionSequence horizon noncontractiveHiddenInitial).mass
          NoncontractiveQuotientFineState.absorbed =
        barrierCdf defect horizon := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, barrierCdf, barrierSurvival,
        noncontractiveHiddenInitial, finiteDirac]
  | succ horizon inductionHypothesis =>
      simp [evolveMany, evolveFiniteProbability,
        inhomogeneousQuotientFineSequence, gradualNoncontractiveKernel,
        noncontractiveQuotientFineState_univ,
        inhomogeneous_hidden_mass_exact defect valid horizon,
        inductionHypothesis, barrierCdf, barrierSurvival_succ]
      ring

/-- The representative quotient remains at its initial optic cell for every
valid inhomogeneous schedule. -/
theorem inhomogeneous_abstract_false_mass_one
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) :
    ∀ horizon,
      (evolveMany (inhomogeneousQuotientAbstractSequence defect valid)
        noncontractiveActionSequence horizon
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          noncontractiveHiddenInitial)).mass false = 1 := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, pushforwardFiniteProbability,
        noncontractiveHiddenInitial, finiteDirac,
        noncontractiveQuotientEncode,
        noncontractiveQuotientFineState_univ]
  | succ horizon inductionHypothesis =>
      simp [evolveMany, evolveFiniteProbability,
        inhomogeneousQuotientAbstractSequence,
        noncontractiveActionSequence,
        gradualRepresentativeKernel_mass_eq_dirac,
        inductionHypothesis]

theorem inhomogeneous_abstract_true_mass_zero
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) :
    ∀ horizon,
      (evolveMany (inhomogeneousQuotientAbstractSequence defect valid)
        noncontractiveActionSequence horizon
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          noncontractiveHiddenInitial)).mass true = 0 := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, pushforwardFiniteProbability,
        noncontractiveHiddenInitial, finiteDirac,
        noncontractiveQuotientEncode,
        noncontractiveQuotientFineState_univ]
  | succ horizon inductionHypothesis =>
      simp [evolveMany, evolveFiniteProbability,
        inhomogeneousQuotientAbstractSequence,
        noncontractiveActionSequence,
        gradualRepresentativeKernel_mass_eq_dirac,
        inductionHypothesis]

/-- Exact sharp product law for actual transported finite probabilities. -/
theorem inhomogeneous_noncontractive_tv_exact
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect)
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany (inhomogeneousQuotientFineSequence defect valid)
            noncontractiveActionSequence horizon
            noncontractiveHiddenInitial))
        (evolveMany (inhomogeneousQuotientAbstractSequence defect valid)
          noncontractiveActionSequence horizon
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) =
      barrierCdf defect horizon := by
  have survivalAtMostOne := (barrierSurvival_bounds defect valid horizon).2
  have actualFalse :
      (pushforwardFiniteProbability noncontractiveQuotientEncode
        (evolveMany (inhomogeneousQuotientFineSequence defect valid)
          noncontractiveActionSequence horizon
          noncontractiveHiddenInitial)).mass false =
        barrierSurvival defect horizon := by
    simp [pushforwardFiniteProbability,
      noncontractiveQuotientFineState_univ,
      noncontractiveQuotientEncode,
      inhomogeneous_hidden_mass_exact defect valid horizon,
      inhomogeneous_representative_mass_zero defect valid horizon,
      inhomogeneous_absorbed_mass_exact defect valid horizon,
      barrierCdf]
  have actualTrue :
      (pushforwardFiniteProbability noncontractiveQuotientEncode
        (evolveMany (inhomogeneousQuotientFineSequence defect valid)
          noncontractiveActionSequence horizon
          noncontractiveHiddenInitial)).mass true =
        barrierCdf defect horizon := by
    simp [pushforwardFiniteProbability,
      noncontractiveQuotientFineState_univ,
      noncontractiveQuotientEncode,
      inhomogeneous_hidden_mass_exact defect valid horizon,
      inhomogeneous_representative_mass_zero defect valid horizon,
      inhomogeneous_absorbed_mass_exact defect valid horizon]
  have abstractFalse :=
    inhomogeneous_abstract_false_mass_one defect valid horizon
  have abstractTrue :=
    inhomogeneous_abstract_true_mass_zero defect valid horizon
  simp [finiteTotalVariation, actualFalse, actualTrue,
    abstractFalse, abstractTrue, barrierCdf,
    abs_of_nonpos (sub_nonpos.mpr survivalAtMostOne),
    abs_of_nonneg (sub_nonneg.mpr survivalAtMostOne)]

/-- The observable transported-TV trace generated by a registered defect
schedule. -/
def inhomogeneousQuotientTVTrace
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) (horizon : Nat) : ℚ :=
  finiteTotalVariation
    (pushforwardFiniteProbability noncontractiveQuotientEncode
      (evolveMany (inhomogeneousQuotientFineSequence defect valid)
        noncontractiveActionSequence horizon noncontractiveHiddenInitial))
    (evolveMany (inhomogeneousQuotientAbstractSequence defect valid)
      noncontractiveActionSequence horizon
      (pushforwardFiniteProbability noncontractiveQuotientEncode
        noncontractiveHiddenInitial))

theorem inhomogeneousQuotientTVTrace_eq_cdf
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) (horizon : Nat) :
    inhomogeneousQuotientTVTrace defect valid horizon =
      barrierCdf defect horizon :=
  inhomogeneous_noncontractive_tv_exact defect valid horizon

/-- Algebraic inverse used to calibrate a time-local quotient defect from two
successive values of an observed TV trace. -/
def inferredQuotientDefectFromTV (tv : Nat → ℚ) (step : Nat) : ℚ :=
  (tv (step + 1) - tv step) / (1 - tv step)

/-- Before survival mass is exhausted, consecutive exact TV observations
identify the local quotient defect uniquely. -/
theorem inhomogeneous_defect_recovered_from_tv
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) (step : Nat)
    (survivalNonzero : barrierSurvival defect step ≠ 0) :
    inferredQuotientDefectFromTV
      (inhomogeneousQuotientTVTrace defect valid) step = defect step := by
  rw [inferredQuotientDefectFromTV,
    inhomogeneousQuotientTVTrace_eq_cdf,
    inhomogeneousQuotientTVTrace_eq_cdf,
    barrierCdf_succ_sub]
  simp [firstBarrierMass, barrierCdf, survivalNonzero]

/-- At probability-diameter saturation, the same inverse necessarily returns
zero, independently of the next declared defect. -/
theorem saturated_tv_trace_loses_next_defect
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) (step : Nat)
    (survivalZero : barrierSurvival defect step = 0) :
    inferredQuotientDefectFromTV
      (inhomogeneousQuotientTVTrace defect valid) step = 0 := by
  rw [inferredQuotientDefectFromTV,
    inhomogeneousQuotientTVTrace_eq_cdf,
    inhomogeneousQuotientTVTrace_eq_cdf,
    barrierCdf_succ_sub]
  simp [firstBarrierMass, barrierCdf, survivalZero]

/-- Sharp identifiability no-go after saturation: if the actual next defect is
positive, the trace inverse is provably wrong because all remaining optic mass
has already escaped. -/
theorem positive_defect_not_identifiable_after_saturation
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect) (step : Nat)
    (survivalZero : barrierSurvival defect step = 0)
    (nextDefectPositive : 0 < defect step) :
    inferredQuotientDefectFromTV
        (inhomogeneousQuotientTVTrace defect valid) step ≠ defect step := by
  rw [saturated_tv_trace_loses_next_defect defect valid step survivalZero]
  exact ne_of_lt nextDefectPositive

/-- Exact marginal prediction loss is the first-event mass induced by the
time-local defect schedule. -/
theorem inhomogeneous_noncontractive_tv_increment_exact
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect)
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany (inhomogeneousQuotientFineSequence defect valid)
            noncontractiveActionSequence (horizon + 1)
            noncontractiveHiddenInitial))
        (evolveMany (inhomogeneousQuotientAbstractSequence defect valid)
          noncontractiveActionSequence (horizon + 1)
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) -
      finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany (inhomogeneousQuotientFineSequence defect valid)
            noncontractiveActionSequence horizon
            noncontractiveHiddenInitial))
        (evolveMany (inhomogeneousQuotientAbstractSequence defect valid)
          noncontractiveActionSequence horizon
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) =
      firstBarrierMass defect horizon := by
  rw [inhomogeneous_noncontractive_tv_exact defect valid,
    inhomogeneous_noncontractive_tv_exact defect valid]
  exact barrierCdf_succ_sub defect horizon

/-- An exact finite-horizon falsifier for any claimed prediction threshold. -/
theorem inhomogeneous_noncontractive_threshold_falsifier
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect)
    (bound : ℚ) (horizon : Nat)
    (thresholdExceeded : bound < barrierCdf defect horizon) :
    ¬ finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany (inhomogeneousQuotientFineSequence defect valid)
            noncontractiveActionSequence horizon
            noncontractiveHiddenInitial))
        (evolveMany (inhomogeneousQuotientAbstractSequence defect valid)
          noncontractiveActionSequence horizon
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) ≤ bound := by
  rw [inhomogeneous_noncontractive_tv_exact defect valid horizon]
  exact not_le_of_gt thresholdExceeded

/-- Exact characterization of a uniform finite-horizon certificate over the
declared horizon range. -/
theorem inhomogeneous_uniform_bound_iff_survival_floor
    (defect : Nat → ℚ) (valid : ValidBarrierHazard defect)
    (bound : ℚ) (maximumHorizon : Nat) :
    (∀ horizon ≤ maximumHorizon,
      finiteTotalVariation
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            (evolveMany (inhomogeneousQuotientFineSequence defect valid)
              noncontractiveActionSequence horizon
              noncontractiveHiddenInitial))
          (evolveMany (inhomogeneousQuotientAbstractSequence defect valid)
            noncontractiveActionSequence horizon
            (pushforwardFiniteProbability noncontractiveQuotientEncode
              noncontractiveHiddenInitial)) ≤ bound) ↔
      ∀ horizon ≤ maximumHorizon,
        1 - bound ≤ barrierSurvival defect horizon := by
  constructor <;> intro hypothesis horizon horizonBound
  · have atHorizon := hypothesis horizon horizonBound
    rw [inhomogeneous_noncontractive_tv_exact defect valid horizon,
      barrierCdf] at atHorizon
    linarith
  · rw [inhomogeneous_noncontractive_tv_exact defect valid horizon,
      barrierCdf]
    linarith [hypothesis horizon horizonBound]

end OCKIndividuationMSpaceComposition
