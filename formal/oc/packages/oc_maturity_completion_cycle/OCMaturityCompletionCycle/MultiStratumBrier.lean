import OCMaturityCompletionCycle.EmpiricalCouplingPredictionR2
import Mathlib.Algebra.Order.BigOperators.Group.Finset

/-!
# Multi-stratum binary coupling Brier decomposition

Each stratum has its own frozen regime weight, conditional probabilities and
regime-blind report.  Stratum weights are left symbolic; probability validity
is required for empirical interpretation but not for the polynomial identity.
-/

namespace OCMaturityCompletionCycle

universe uStratum

def MultiStratumLocalOnlyBrierRisk
    {Stratum : Type uStratum}
    [Fintype Stratum]
    (stratumWeight regimeWeight probabilityLow probabilityHigh forecast :
      Stratum → ℚ) : ℚ :=
  ∑ stratum,
    stratumWeight stratum *
      LocalOnlyBrierRiskR2
        (regimeWeight stratum)
        (probabilityLow stratum)
        (probabilityHigh stratum)
        (forecast stratum)

def MultiStratumCouplingAwareBrierRisk
    {Stratum : Type uStratum}
    [Fintype Stratum]
    (stratumWeight regimeWeight probabilityLow probabilityHigh :
      Stratum → ℚ) : ℚ :=
  ∑ stratum,
    stratumWeight stratum *
      CouplingAwareBrierRiskR2
        (regimeWeight stratum)
        (probabilityLow stratum)
        (probabilityHigh stratum)

def MultiStratumCalibrationPenalty
    {Stratum : Type uStratum}
    [Fintype Stratum]
    (stratumWeight regimeWeight probabilityLow probabilityHigh forecast :
      Stratum → ℚ) : ℚ :=
  ∑ stratum,
    stratumWeight stratum *
      (forecast stratum -
        LocalMixtureMeanR2
          (regimeWeight stratum)
          (probabilityLow stratum)
          (probabilityHigh stratum)) ^ 2

def MultiStratumCouplingBrierGain
    {Stratum : Type uStratum}
    [Fintype Stratum]
    (stratumWeight regimeWeight probabilityLow probabilityHigh :
      Stratum → ℚ) : ℚ :=
  ∑ stratum,
    stratumWeight stratum *
      CouplingBrierGainR2
        (regimeWeight stratum)
        (probabilityLow stratum)
        (probabilityHigh stratum)

/-- Exact weighted decomposition across any finite frozen stratum family. -/
theorem multiStratumLocalOnlyBrierRisk_exact_decomposition
    {Stratum : Type uStratum}
    [Fintype Stratum]
    (stratumWeight regimeWeight probabilityLow probabilityHigh forecast :
      Stratum → ℚ) :
    MultiStratumLocalOnlyBrierRisk stratumWeight regimeWeight
        probabilityLow probabilityHigh forecast =
      MultiStratumCouplingAwareBrierRisk stratumWeight regimeWeight
          probabilityLow probabilityHigh +
        MultiStratumCalibrationPenalty stratumWeight regimeWeight
          probabilityLow probabilityHigh forecast +
        MultiStratumCouplingBrierGain stratumWeight regimeWeight
          probabilityLow probabilityHigh := by
  simp only [MultiStratumLocalOnlyBrierRisk,
    MultiStratumCouplingAwareBrierRisk,
    MultiStratumCalibrationPenalty,
    MultiStratumCouplingBrierGain]
  calc
    (∑ stratum,
      stratumWeight stratum *
        LocalOnlyBrierRiskR2
          (regimeWeight stratum)
          (probabilityLow stratum)
          (probabilityHigh stratum)
          (forecast stratum)) =
      ∑ stratum,
        stratumWeight stratum *
          (CouplingAwareBrierRiskR2
              (regimeWeight stratum)
              (probabilityLow stratum)
              (probabilityHigh stratum) +
            (forecast stratum -
              LocalMixtureMeanR2
                (regimeWeight stratum)
                (probabilityLow stratum)
                (probabilityHigh stratum)) ^ 2 +
            CouplingBrierGainR2
              (regimeWeight stratum)
              (probabilityLow stratum)
              (probabilityHigh stratum)) := by
        apply Finset.sum_congr rfl
        intro stratum _
        rw [localOnlyBrierRiskR2_exact_decomposition]
    _ =
      (∑ stratum,
        stratumWeight stratum *
          CouplingAwareBrierRiskR2
            (regimeWeight stratum)
            (probabilityLow stratum)
            (probabilityHigh stratum)) +
      (∑ stratum,
        stratumWeight stratum *
          (forecast stratum -
            LocalMixtureMeanR2
              (regimeWeight stratum)
              (probabilityLow stratum)
              (probabilityHigh stratum)) ^ 2) +
      ∑ stratum,
        stratumWeight stratum *
          CouplingBrierGainR2
            (regimeWeight stratum)
            (probabilityLow stratum)
            (probabilityHigh stratum) := by
        simp only [mul_add, Finset.sum_add_distrib]

end OCMaturityCompletionCycle
