import OCKIndividuationMSpaceComposition.StochasticTwoStageForecastCertificate
import Mathlib.Tactic.Linarith

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

/-!
# Finite-sample validation-to-prospective forecast transfer

This is the deterministic theorem consumed after an external concentration
result supplies simultaneous radii. A frozen validation empirical law and a
future empirical law are connected only through an explicit common population
law. The theorem does not manufacture stationarity or independence: those are
premises of the statistical adapter and remain falsifiable.
-/

/-- If validation and prospective empirical laws are within registered radii
of the same population law, the prospective error of a frozen fine forecast
is bounded by validation error plus the two radii. -/
theorem prospectiveFineForecastError_le_validationError_add_radii
    {Outcome : Type uState}
    [Fintype Outcome]
    (truth validation prospective fineForecast :
      FiniteProbabilityMass Outcome)
    (validationRadius prospectiveRadius : ℚ)
    (validationConfidence :
      finiteTotalVariation validation truth ≤ validationRadius)
    (prospectiveConfidence :
      finiteTotalVariation prospective truth ≤ prospectiveRadius) :
    finiteTotalVariation prospective fineForecast ≤
      finiteTotalVariation validation fineForecast +
        validationRadius + prospectiveRadius := by
  have truthToValidation :
      finiteTotalVariation truth validation ≤ validationRadius := by
    rw [finiteTotalVariation_symm]
    exact validationConfidence
  have first := finiteTotalVariation_triangle prospective truth validation
  have second := finiteTotalVariation_triangle prospective validation fineForecast
  linarith

/-- Add a separately certified fine-to-quotient transport error. This is the
non-tautological finite-sample version of the two-stage forecast certificate. -/
theorem prospectiveQuotientForecastError_le_validationFineError_add_radii_add_transport
    {Outcome : Type uState}
    [Fintype Outcome]
    (truth validation prospective fineForecast quotientForecast :
      FiniteProbabilityMass Outcome)
    (validationRadius prospectiveRadius transportRadius : ℚ)
    (validationConfidence :
      finiteTotalVariation validation truth ≤ validationRadius)
    (prospectiveConfidence :
      finiteTotalVariation prospective truth ≤ prospectiveRadius)
    (transport :
      finiteTotalVariation fineForecast quotientForecast ≤ transportRadius) :
    finiteTotalVariation prospective quotientForecast ≤
      finiteTotalVariation validation fineForecast +
        validationRadius + prospectiveRadius + transportRadius := by
  have fineBound :=
    prospectiveFineForecastError_le_validationError_add_radii
      truth validation prospective fineForecast validationRadius
      prospectiveRadius validationConfidence prospectiveConfidence
  have combined :=
    quotientForecastError_le_realityToFine_add_fineToQuotient
      prospective fineForecast quotientForecast
      (finiteTotalVariation validation fineForecast +
        validationRadius + prospectiveRadius)
      transportRadius fineBound transport
  linarith

/-- An observed prospective excess refutes the conjunction of common-law
concentration and transport premises. Post-outcome widening is not a proof. -/
theorem prospectiveQuotientViolation_refutes_empiricalTransferContract
    {Outcome : Type uState}
    [Fintype Outcome]
    (truth validation prospective fineForecast quotientForecast :
      FiniteProbabilityMass Outcome)
    (validationRadius prospectiveRadius transportRadius : ℚ)
    (violation :
      finiteTotalVariation validation fineForecast +
          validationRadius + prospectiveRadius + transportRadius <
        finiteTotalVariation prospective quotientForecast) :
    ¬ (finiteTotalVariation validation truth ≤ validationRadius ∧
       finiteTotalVariation prospective truth ≤ prospectiveRadius ∧
       finiteTotalVariation fineForecast quotientForecast ≤ transportRadius) := by
  intro premises
  have certified :=
    prospectiveQuotientForecastError_le_validationFineError_add_radii_add_transport
      truth validation prospective fineForecast quotientForecast
      validationRadius prospectiveRadius transportRadius
      premises.1 premises.2.1 premises.2.2
  exact (not_lt_of_ge certified) violation

/-- Per-row budget frozen before prospective targets are opened. -/
def empiricalRowForecastBudget
    {Outcome : Type uState}
    [Fintype Outcome]
    (validation fineForecast : FiniteProbabilityMass Outcome)
    (validationRadius prospectiveRadius transportRadius : ℚ) : ℚ :=
  finiteTotalVariation validation fineForecast +
    validationRadius + prospectiveRadius + transportRadius

/-- Reality-to-fine part of a row budget, before quotient transport. -/
def empiricalFineRowForecastBudget
    {Outcome : Type uState}
    [Fintype Outcome]
    (validation fineForecast : FiniteProbabilityMass Outcome)
    (validationRadius prospectiveRadius : ℚ) : ℚ :=
  finiteTotalVariation validation fineForecast +
    validationRadius + prospectiveRadius

/-- The prospective mixture-to-fine-mixture error is bounded by the weighted
reality-to-fine row budgets. -/
theorem prospectiveMixtureFineError_le_weighted_empiricalFineRowBudgets
    {Index : Type uFineState}
    {Outcome : Type uState}
    [Fintype Index]
    [Fintype Outcome]
    (weight : FiniteProbabilityMass Index)
    (truth validation prospective fineForecast :
      Index → FiniteProbabilityMass Outcome)
    (validationRadius prospectiveRadius : Index → ℚ)
    (validationConfidence : ∀ index,
      finiteTotalVariation (validation index) (truth index) ≤
        validationRadius index)
    (prospectiveConfidence : ∀ index,
      finiteTotalVariation (prospective index) (truth index) ≤
        prospectiveRadius index) :
    finiteTotalVariation
        (finiteProbabilityMixture weight prospective)
        (finiteProbabilityMixture weight fineForecast) ≤
      ∑ index, weight.mass index *
        empiricalFineRowForecastBudget (validation index) (fineForecast index)
          (validationRadius index) (prospectiveRadius index) := by
  calc
    finiteTotalVariation
        (finiteProbabilityMixture weight prospective)
        (finiteProbabilityMixture weight fineForecast) ≤
      ∑ index, weight.mass index *
        finiteTotalVariation (prospective index) (fineForecast index) :=
      finiteProbabilityMixture_tv_le_weighted_row_tv weight prospective
        fineForecast
    _ ≤ ∑ index, weight.mass index *
        empiricalFineRowForecastBudget (validation index) (fineForecast index)
          (validationRadius index) (prospectiveRadius index) := by
      apply Finset.sum_le_sum
      intro index _
      apply mul_le_mul_of_nonneg_left _ (weight.nonnegative index)
      exact prospectiveFineForecastError_le_validationError_add_radii
        (truth index) (validation index) (prospective index)
        (fineForecast index) (validationRadius index)
        (prospectiveRadius index) (validationConfidence index)
        (prospectiveConfidence index)

/-- Tighter aggregate certificate: perform statistical transfer row-wise, but
pay the exactly computable aggregate fine-to-quotient discrepancy only once.
This retains cancellation between transported rows that a weighted sum of row
TV values discards. -/
theorem prospectiveMixtureQuotientError_le_weightedFineBudgets_add_exactAggregateTransport
    {Index : Type uFineState}
    {Outcome : Type uState}
    [Fintype Index]
    [Fintype Outcome]
    (weight : FiniteProbabilityMass Index)
    (truth validation prospective fineForecast quotientForecast :
      Index → FiniteProbabilityMass Outcome)
    (validationRadius prospectiveRadius : Index → ℚ)
    (validationConfidence : ∀ index,
      finiteTotalVariation (validation index) (truth index) ≤
        validationRadius index)
    (prospectiveConfidence : ∀ index,
      finiteTotalVariation (prospective index) (truth index) ≤
        prospectiveRadius index) :
    finiteTotalVariation
        (finiteProbabilityMixture weight prospective)
        (finiteProbabilityMixture weight quotientForecast) ≤
      (∑ index, weight.mass index *
        empiricalFineRowForecastBudget (validation index) (fineForecast index)
          (validationRadius index) (prospectiveRadius index)) +
      finiteTotalVariation
        (finiteProbabilityMixture weight fineForecast)
        (finiteProbabilityMixture weight quotientForecast) := by
  have fineBound :=
    prospectiveMixtureFineError_le_weighted_empiricalFineRowBudgets
      weight truth validation prospective fineForecast validationRadius
      prospectiveRadius validationConfidence prospectiveConfidence
  exact quotientForecastError_le_realityToFine_add_fineToQuotient
    (finiteProbabilityMixture weight prospective)
    (finiteProbabilityMixture weight fineForecast)
    (finiteProbabilityMixture weight quotientForecast)
    (∑ index, weight.mass index *
      empiricalFineRowForecastBudget (validation index) (fineForecast index)
        (validationRadius index) (prospectiveRadius index))
    (finiteTotalVariation
      (finiteProbabilityMixture weight fineForecast)
      (finiteProbabilityMixture weight quotientForecast))
    fineBound (le_refl _)

/-- Common-weight row mixture yields an aggregate prospective certificate.
The weight law may be the source-state frequencies known at forecast time. -/
theorem prospectiveMixtureQuotientError_le_weighted_empiricalRowBudgets
    {Index : Type uFineState}
    {Outcome : Type uState}
    [Fintype Index]
    [Fintype Outcome]
    (weight : FiniteProbabilityMass Index)
    (truth validation prospective fineForecast quotientForecast :
      Index → FiniteProbabilityMass Outcome)
    (validationRadius prospectiveRadius transportRadius : Index → ℚ)
    (validationConfidence : ∀ index,
      finiteTotalVariation (validation index) (truth index) ≤
        validationRadius index)
    (prospectiveConfidence : ∀ index,
      finiteTotalVariation (prospective index) (truth index) ≤
        prospectiveRadius index)
    (transport : ∀ index,
      finiteTotalVariation (fineForecast index) (quotientForecast index) ≤
        transportRadius index) :
    finiteTotalVariation
        (finiteProbabilityMixture weight prospective)
        (finiteProbabilityMixture weight quotientForecast) ≤
      ∑ index, weight.mass index *
        empiricalRowForecastBudget (validation index) (fineForecast index)
          (validationRadius index) (prospectiveRadius index)
          (transportRadius index) := by
  calc
    finiteTotalVariation
        (finiteProbabilityMixture weight prospective)
        (finiteProbabilityMixture weight quotientForecast) ≤
      ∑ index, weight.mass index *
        finiteTotalVariation (prospective index) (quotientForecast index) :=
      finiteProbabilityMixture_tv_le_weighted_row_tv weight prospective
        quotientForecast
    _ ≤ ∑ index, weight.mass index *
        empiricalRowForecastBudget (validation index) (fineForecast index)
          (validationRadius index) (prospectiveRadius index)
          (transportRadius index) := by
      apply Finset.sum_le_sum
      intro index _
      apply mul_le_mul_of_nonneg_left _ (weight.nonnegative index)
      exact
        prospectiveQuotientForecastError_le_validationFineError_add_radii_add_transport
          (truth index) (validation index) (prospective index)
          (fineForecast index) (quotientForecast index)
          (validationRadius index) (prospectiveRadius index)
          (transportRadius index) (validationConfidence index)
          (prospectiveConfidence index) (transport index)

/-- The minimum of the row-wise and exact-aggregate certificates is itself a
valid registered certificate. Neither constituent is called tighter in
advance: clipping, weighting, and aggregate cancellation can change their
ordering from one forecast horizon to another. -/
theorem prospectiveMixtureQuotientError_le_bestRegisteredAggregateBound
    {Index : Type uFineState}
    {Outcome : Type uState}
    [Fintype Index]
    [Fintype Outcome]
    (weight : FiniteProbabilityMass Index)
    (truth validation prospective fineForecast quotientForecast :
      Index → FiniteProbabilityMass Outcome)
    (validationRadius prospectiveRadius transportRadius : Index → ℚ)
    (validationConfidence : ∀ index,
      finiteTotalVariation (validation index) (truth index) ≤
        validationRadius index)
    (prospectiveConfidence : ∀ index,
      finiteTotalVariation (prospective index) (truth index) ≤
        prospectiveRadius index)
    (transport : ∀ index,
      finiteTotalVariation (fineForecast index) (quotientForecast index) ≤
        transportRadius index) :
    finiteTotalVariation
        (finiteProbabilityMixture weight prospective)
        (finiteProbabilityMixture weight quotientForecast) ≤
      min
        (∑ index, weight.mass index *
          empiricalRowForecastBudget (validation index) (fineForecast index)
            (validationRadius index) (prospectiveRadius index)
            (transportRadius index))
        ((∑ index, weight.mass index *
          empiricalFineRowForecastBudget (validation index) (fineForecast index)
            (validationRadius index) (prospectiveRadius index)) +
          finiteTotalVariation
            (finiteProbabilityMixture weight fineForecast)
            (finiteProbabilityMixture weight quotientForecast)) := by
  apply le_min
  · exact prospectiveMixtureQuotientError_le_weighted_empiricalRowBudgets
      weight truth validation prospective fineForecast quotientForecast
      validationRadius prospectiveRadius transportRadius
      validationConfidence prospectiveConfidence transport
  · exact
      prospectiveMixtureQuotientError_le_weightedFineBudgets_add_exactAggregateTransport
        weight truth validation prospective fineForecast quotientForecast
        validationRadius prospectiveRadius validationConfidence
        prospectiveConfidence

/-- Exceeding the best pre-registered aggregate certificate refutes the
conjunction of common-law concentration and row-transport premises. -/
theorem prospectiveMixtureBestBoundViolation_refutes_rowContracts
    {Index : Type uFineState}
    {Outcome : Type uState}
    [Fintype Index]
    [Fintype Outcome]
    (weight : FiniteProbabilityMass Index)
    (truth validation prospective fineForecast quotientForecast :
      Index → FiniteProbabilityMass Outcome)
    (validationRadius prospectiveRadius transportRadius : Index → ℚ)
    (violation :
      min
          (∑ index, weight.mass index *
            empiricalRowForecastBudget (validation index) (fineForecast index)
              (validationRadius index) (prospectiveRadius index)
              (transportRadius index))
          ((∑ index, weight.mass index *
            empiricalFineRowForecastBudget (validation index) (fineForecast index)
              (validationRadius index) (prospectiveRadius index)) +
            finiteTotalVariation
              (finiteProbabilityMixture weight fineForecast)
              (finiteProbabilityMixture weight quotientForecast)) <
        finiteTotalVariation
          (finiteProbabilityMixture weight prospective)
          (finiteProbabilityMixture weight quotientForecast)) :
    ¬ ((∀ index,
          finiteTotalVariation (validation index) (truth index) ≤
            validationRadius index) ∧
       (∀ index,
          finiteTotalVariation (prospective index) (truth index) ≤
            prospectiveRadius index) ∧
       (∀ index,
          finiteTotalVariation (fineForecast index) (quotientForecast index) ≤
            transportRadius index)) := by
  intro premises
  have certified :=
    prospectiveMixtureQuotientError_le_bestRegisteredAggregateBound
      weight truth validation prospective fineForecast quotientForecast
      validationRadius prospectiveRadius transportRadius
      premises.1 premises.2.1 premises.2.2
  exact (not_lt_of_ge certified) violation

/-- Aggregate excess refutes at least one registered row contract. -/
theorem prospectiveMixtureViolation_refutes_rowContracts
    {Index : Type uFineState}
    {Outcome : Type uState}
    [Fintype Index]
    [Fintype Outcome]
    (weight : FiniteProbabilityMass Index)
    (truth validation prospective fineForecast quotientForecast :
      Index → FiniteProbabilityMass Outcome)
    (validationRadius prospectiveRadius transportRadius : Index → ℚ)
    (violation :
      (∑ index, weight.mass index *
          empiricalRowForecastBudget (validation index) (fineForecast index)
            (validationRadius index) (prospectiveRadius index)
            (transportRadius index)) <
        finiteTotalVariation
          (finiteProbabilityMixture weight prospective)
          (finiteProbabilityMixture weight quotientForecast)) :
    ¬ ((∀ index,
          finiteTotalVariation (validation index) (truth index) ≤
            validationRadius index) ∧
       (∀ index,
          finiteTotalVariation (prospective index) (truth index) ≤
            prospectiveRadius index) ∧
       (∀ index,
          finiteTotalVariation (fineForecast index) (quotientForecast index) ≤
            transportRadius index)) := by
  intro premises
  have certified :=
    prospectiveMixtureQuotientError_le_weighted_empiricalRowBudgets
      weight truth validation prospective fineForecast quotientForecast
      validationRadius prospectiveRadius transportRadius
      premises.1 premises.2.1 premises.2.2
  exact (not_lt_of_ge certified) violation

end OCKIndividuationMSpaceComposition
