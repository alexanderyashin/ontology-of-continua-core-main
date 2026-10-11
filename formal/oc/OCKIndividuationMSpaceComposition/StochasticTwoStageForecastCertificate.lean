import OCKIndividuationMSpaceComposition.StochasticInhomogeneousTransportEnvelope
import Mathlib.Tactic.Linarith

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

/-!
# Two-stage prospective forecast certificates

The quotient transport envelope controls disagreement between a fine model
and its task quotient. It does not by itself control disagreement between
reality and the fine model. A predictive certificate therefore has two
separately falsifiable stages: `reality -> fine model` and
`fine model -> task quotient`. The deployable bound is their sum.
-/

/-- Scalar two-stage horizon envelope: calibration/model error plus quotient
transport error. -/
def twoStageForecastEnvelope
    (realityToFineRho realityToFineEpsilon : Nat → ℚ)
    (realityToFineInitial : ℚ)
    (fineToQuotientRho fineToQuotientEpsilon : Nat → ℚ)
    (fineToQuotientInitial : ℚ) (horizon : Nat) : ℚ :=
  inhomogeneousRobustErrorEnvelope
      realityToFineRho realityToFineEpsilon realityToFineInitial horizon +
    inhomogeneousRobustErrorEnvelope
      fineToQuotientRho fineToQuotientEpsilon fineToQuotientInitial horizon

/-- A registered reality-to-fine error and fine-to-quotient error imply a
reality-to-quotient forecast bound after typed pushforward. -/
theorem quotientForecastError_le_realityToFine_add_fineToQuotient
    {Outcome : Type uState}
    [Fintype Outcome]
    (observed fineForecast quotientForecast : FiniteProbabilityMass Outcome)
    (realityToFine fineToQuotient : ℚ)
    (realityToFineBound :
      finiteTotalVariation observed fineForecast ≤ realityToFine)
    (fineToQuotientBound :
      finiteTotalVariation fineForecast quotientForecast ≤ fineToQuotient) :
    finiteTotalVariation observed quotientForecast ≤
      realityToFine + fineToQuotient := by
  have triangle :=
    finiteTotalVariation_triangle observed fineForecast quotientForecast
  linarith

/-- A prospective violation of the summed certificate refutes at least one
stage premise. -/
theorem quotientForecastViolation_refutes_twoStageContract
    {Outcome : Type uState}
    [Fintype Outcome]
    (observed fineForecast quotientForecast : FiniteProbabilityMass Outcome)
    (realityToFine fineToQuotient : ℚ)
    (violation :
      realityToFine + fineToQuotient <
        finiteTotalVariation observed quotientForecast) :
    ¬ (finiteTotalVariation observed fineForecast ≤ realityToFine ∧
       finiteTotalVariation fineForecast quotientForecast ≤ fineToQuotient) := by
  intro premises
  have certified :=
    quotientForecastError_le_realityToFine_add_fineToQuotient
      observed fineForecast quotientForecast realityToFine fineToQuotient
      premises.1 premises.2
  exact (not_lt_of_ge certified) violation

/-- Horizon-indexed form used by a preregistered forecasting packet. -/
theorem quotientForecastError_le_twoStageForecastEnvelope
    {Outcome : Type uState}
    [Fintype Outcome]
    (observed fineForecast quotientForecast :
      Nat → FiniteProbabilityMass Outcome)
    (realityToFineRho realityToFineEpsilon : Nat → ℚ)
    (realityToFineInitial : ℚ)
    (fineToQuotientRho fineToQuotientEpsilon : Nat → ℚ)
    (fineToQuotientInitial : ℚ)
    (realityToFineBound : ∀ horizon,
      finiteTotalVariation (observed horizon) (fineForecast horizon) ≤
        inhomogeneousRobustErrorEnvelope
          realityToFineRho realityToFineEpsilon realityToFineInitial horizon)
    (fineToQuotientBound : ∀ horizon,
      finiteTotalVariation (fineForecast horizon) (quotientForecast horizon) ≤
        inhomogeneousRobustErrorEnvelope
          fineToQuotientRho fineToQuotientEpsilon fineToQuotientInitial horizon) :
    ∀ horizon,
      finiteTotalVariation (observed horizon) (quotientForecast horizon) ≤
        twoStageForecastEnvelope
          realityToFineRho realityToFineEpsilon realityToFineInitial
          fineToQuotientRho fineToQuotientEpsilon fineToQuotientInitial
          horizon := by
  intro horizon
  exact quotientForecastError_le_realityToFine_add_fineToQuotient
    (observed horizon) (fineForecast horizon) (quotientForecast horizon)
    (inhomogeneousRobustErrorEnvelope
      realityToFineRho realityToFineEpsilon realityToFineInitial horizon)
    (inhomogeneousRobustErrorEnvelope
      fineToQuotientRho fineToQuotientEpsilon fineToQuotientInitial horizon)
    (realityToFineBound horizon) (fineToQuotientBound horizon)

/-- Exact negative verifier at a registered horizon. -/
theorem observedViolation_refutes_twoStageForecastEnvelope
    {Outcome : Type uState}
    [Fintype Outcome]
    (observed fineForecast quotientForecast :
      Nat → FiniteProbabilityMass Outcome)
    (realityToFineRho realityToFineEpsilon : Nat → ℚ)
    (realityToFineInitial : ℚ)
    (fineToQuotientRho fineToQuotientEpsilon : Nat → ℚ)
    (fineToQuotientInitial : ℚ)
    (horizon : Nat)
    (violation :
      twoStageForecastEnvelope
          realityToFineRho realityToFineEpsilon realityToFineInitial
          fineToQuotientRho fineToQuotientEpsilon fineToQuotientInitial
          horizon <
        finiteTotalVariation (observed horizon) (quotientForecast horizon)) :
    ¬ (finiteTotalVariation (observed horizon) (fineForecast horizon) ≤
          inhomogeneousRobustErrorEnvelope
            realityToFineRho realityToFineEpsilon realityToFineInitial horizon ∧
       finiteTotalVariation (fineForecast horizon) (quotientForecast horizon) ≤
          inhomogeneousRobustErrorEnvelope
            fineToQuotientRho fineToQuotientEpsilon fineToQuotientInitial
            horizon) := by
  exact quotientForecastViolation_refutes_twoStageContract
    (observed horizon) (fineForecast horizon) (quotientForecast horizon)
    (inhomogeneousRobustErrorEnvelope
      realityToFineRho realityToFineEpsilon realityToFineInitial horizon)
    (inhomogeneousRobustErrorEnvelope
      fineToQuotientRho fineToQuotientEpsilon fineToQuotientInitial horizon)
    violation

end OCKIndividuationMSpaceComposition
