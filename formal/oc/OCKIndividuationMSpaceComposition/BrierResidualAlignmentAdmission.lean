import OCKIndividuationMSpaceComposition.ResidualAlignmentContextAdmission

namespace OCKIndividuationMSpaceComposition

/-!
# Multiclass Brier residual-alignment admission

This module lifts the scalar residual-alignment gate to a finite outcome
vector.  It supplies the proper-score bridge needed by the external OCEL
replay: a typed context is predictively admissible only when its probability
shift aligns with the residual left by the base predictor strongly enough to
pay for the shift's squared energy.

No simplex assumption is needed for the algebraic result.  Probability-simplex
and clipping constraints belong to the estimator/implementation contract; the
theorems below isolate the exact predictive contribution of the added context.
-/

/-- Multiclass Brier risk after adding `weight * shift` to a base forecast. -/
def BrierContextRisk {n : ℕ}
    (truth base shift : Fin n → ℝ) (weight : ℝ) : ℝ :=
  ∑ i, (truth i - (base i + weight * shift i)) ^ 2

/-- Multiclass Brier risk of the unaugmented base forecast. -/
def BrierBaseRisk {n : ℕ} (truth base : Fin n → ℝ) : ℝ :=
  ∑ i, (truth i - base i) ^ 2

/-- Inner product between the base residual and the proposed context shift. -/
def BrierResidualAlignment {n : ℕ}
    (truth base shift : Fin n → ℝ) : ℝ :=
  ∑ i, (truth i - base i) * shift i

/-- Squared Euclidean energy of the proposed context shift. -/
def BrierShiftEnergy {n : ℕ} (shift : Fin n → ℝ) : ℝ :=
  ∑ i, (shift i) ^ 2

/-- The multiclass Brier change is exactly the scalar context-gate quadratic. -/
theorem brierContextRisk_exact_quadratic {n : ℕ}
    (truth base shift : Fin n → ℝ) (weight : ℝ) :
    BrierContextRisk truth base shift weight =
      ContextGateQuadraticRisk
        (BrierBaseRisk truth base)
        (BrierResidualAlignment truth base shift)
        (BrierShiftEnergy shift)
        weight := by
  unfold BrierContextRisk BrierBaseRisk BrierResidualAlignment BrierShiftEnergy
    ContextGateQuadraticRisk
  calc
    ∑ i, (truth i - (base i + weight * shift i)) ^ 2 =
        ∑ i, ((truth i - base i) ^ 2 -
          2 * weight * ((truth i - base i) * shift i) +
          weight ^ 2 * (shift i) ^ 2) := by
      apply Finset.sum_congr rfl
      intro i _
      ring
    _ = (∑ i, (truth i - base i) ^ 2) -
          2 * weight * (∑ i, (truth i - base i) * shift i) +
          weight ^ 2 * (∑ i, (shift i) ^ 2) := by
      simp only [Finset.sum_add_distrib, Finset.sum_sub_distrib,
        Finset.mul_sum]

/-- Positive theorem: a positive context weight improves multiclass Brier risk
exactly when residual alignment exceeds half its weighted shift energy. -/
theorem positive_brier_context_improves_iff_residual_alignment {n : ℕ}
    (truth base shift : Fin n → ℝ) (weight : ℝ)
    (weightPositive : 0 < weight) :
    BrierContextRisk truth base shift weight <
        BrierContextRisk truth base shift 0 ↔
      weight * BrierShiftEnergy shift <
        2 * BrierResidualAlignment truth base shift := by
  rw [brierContextRisk_exact_quadratic, brierContextRisk_exact_quadratic]
  exact positive_context_weight_improves_iff_energy_below_alignment
    (BrierBaseRisk truth base)
    (BrierResidualAlignment truth base shift)
    (BrierShiftEnergy shift)
    weight weightPositive

/-- No-go theorem: nonpositive residual alignment makes every positive-energy,
positive-weight context gate strictly worse under multiclass Brier risk. -/
theorem nonpositive_brier_alignment_rejects_every_positive_gate {n : ℕ}
    (truth base shift : Fin n → ℝ) (weight : ℝ)
    (alignmentNonpositive : BrierResidualAlignment truth base shift ≤ 0)
    (energyPositive : 0 < BrierShiftEnergy shift)
    (weightPositive : 0 < weight) :
    BrierContextRisk truth base shift 0 <
      BrierContextRisk truth base shift weight := by
  rw [brierContextRisk_exact_quadratic, brierContextRisk_exact_quadratic]
  exact nonpositive_alignment_rejects_every_positive_gate
    (BrierBaseRisk truth base)
    (BrierResidualAlignment truth base shift)
    (BrierShiftEnergy shift)
    weight alignmentNonpositive energyPositive weightPositive

/-- The residual-alignment weight globally minimizes the unconstrained
multiclass Brier risk whenever the context shift has positive energy. -/
theorem brierResidualAlignmentWeight_globally_minimizes {n : ℕ}
    (truth base shift : Fin n → ℝ) (weight : ℝ)
    (energyPositive : 0 < BrierShiftEnergy shift) :
    BrierContextRisk truth base shift
        (ResidualAlignmentWeight
          (BrierResidualAlignment truth base shift)
          (BrierShiftEnergy shift)) ≤
      BrierContextRisk truth base shift weight := by
  rw [brierContextRisk_exact_quadratic, brierContextRisk_exact_quadratic]
  exact residualAlignmentWeight_globally_minimizes
    (BrierBaseRisk truth base)
    (BrierResidualAlignment truth base shift)
    (BrierShiftEnergy shift)
    weight energyPositive

/-- Operational theorem: the calibration rule obtained by clamping residual
alignment divided by shift energy to `[0,1]` minimizes multiclass Brier risk
among every admissible mixture weight. -/
theorem clampedBrierResidualAlignmentWeight_globally_minimizes {n : ℕ}
    (truth base shift : Fin n → ℝ) (weight : ℝ)
    (energyPositive : 0 < BrierShiftEnergy shift)
    (weightNonnegative : 0 ≤ weight)
    (weightAtMostOne : weight ≤ 1) :
    BrierContextRisk truth base shift
        (ClampedResidualAlignmentWeight
          (BrierResidualAlignment truth base shift)
          (BrierShiftEnergy shift)) ≤
      BrierContextRisk truth base shift weight := by
  rw [brierContextRisk_exact_quadratic, brierContextRisk_exact_quadratic]
  exact clampedResidualAlignmentWeight_globally_minimizes
    (BrierBaseRisk truth base)
    (BrierResidualAlignment truth base shift)
    (BrierShiftEnergy shift)
    weight energyPositive weightNonnegative weightAtMostOne

/-- A zero shift is predictively neutral at every weight. -/
theorem zero_brier_shift_is_neutral {n : ℕ}
    (truth base : Fin n → ℝ) (weight : ℝ) :
    BrierContextRisk truth base (fun _ ↦ 0) weight =
      BrierContextRisk truth base (fun _ ↦ 0) 0 := by
  simp [BrierContextRisk]

end OCKIndividuationMSpaceComposition
