import OCKIndividuationMSpaceComposition.ContinuousMobilityContextTransport

namespace OCKIndividuationMSpaceComposition

/-!
# Residual-alignment weight for evidence-adaptive context admission

After a base predictor is fitted without an added context gate, let `alignment`
be the gate's inner product with the base residual and let `energy` be its
squared magnitude.  Squared risk is an exact quadratic in the gate weight.
The ratio `alignment / energy` is therefore the unconstrained risk minimizer;
clipping it to an admissible interval is an implementation-level projection.
-/

/-- Squared risk of adding a context shift with scalar weight, expressed only
through base risk, residual alignment and shift energy. -/
def ContextGateQuadraticRisk
    (baseRisk alignment energy weight : ℝ) : ℝ :=
  baseRisk - 2 * weight * alignment + weight ^ 2 * energy

/-- Unconstrained empirical risk-minimizing gate weight when energy is nonzero. -/
noncomputable def ResidualAlignmentWeight
    (alignment energy : ℝ) : ℝ :=
  alignment / energy

/-- Operational residual-alignment weight projected onto the admissible
mixture interval `[0, 1]`. -/
noncomputable def ClampedResidualAlignmentWeight
    (alignment energy : ℝ) : ℝ :=
  min 1 (max 0 (ResidualAlignmentWeight alignment energy))

/-- Exact completed-square decomposition around the residual-alignment weight. -/
theorem contextGateQuadraticRisk_complete_square
    (baseRisk alignment energy weight : ℝ)
    (energyNonzero : energy ≠ 0) :
    ContextGateQuadraticRisk baseRisk alignment energy weight =
      ContextGateQuadraticRisk baseRisk alignment energy
          (ResidualAlignmentWeight alignment energy) +
        energy * (weight - ResidualAlignmentWeight alignment energy) ^ 2 := by
  unfold ContextGateQuadraticRisk ResidualAlignmentWeight
  field_simp
  ring

/-- Positive theorem: with positive gate energy, the residual-alignment weight
globally minimizes the quadratic risk over all real weights. -/
theorem residualAlignmentWeight_globally_minimizes
    (baseRisk alignment energy weight : ℝ)
    (energyPositive : 0 < energy) :
    ContextGateQuadraticRisk baseRisk alignment energy
        (ResidualAlignmentWeight alignment energy) ≤
      ContextGateQuadraticRisk baseRisk alignment energy weight := by
  rw [contextGateQuadraticRisk_complete_square baseRisk alignment energy weight
    (ne_of_gt energyPositive)]
  exact le_add_of_nonneg_right (mul_nonneg (le_of_lt energyPositive) (sq_nonneg _))

/-- Projection lemma: clamping the unconstrained optimum to `[0,1]` is at
least as close to it as every other admissible weight. -/
theorem clampedResidualAlignmentWeight_distance_minimizes
    (alignment energy weight : ℝ)
    (weightNonnegative : 0 ≤ weight)
    (weightAtMostOne : weight ≤ 1) :
    (ClampedResidualAlignmentWeight alignment energy -
        ResidualAlignmentWeight alignment energy) ^ 2 ≤
      (weight - ResidualAlignmentWeight alignment energy) ^ 2 := by
  by_cases ratioNegative : ResidualAlignmentWeight alignment energy < 0
  · have clampEq : ClampedResidualAlignmentWeight alignment energy = 0 := by
      unfold ClampedResidualAlignmentWeight
      rw [max_eq_left (le_of_lt ratioNegative)]
      norm_num
    rw [clampEq]
    have productNonpositive :
        weight * ResidualAlignmentWeight alignment energy ≤ 0 :=
      mul_nonpos_of_nonneg_of_nonpos weightNonnegative (le_of_lt ratioNegative)
    nlinarith [sq_nonneg weight]
  · have ratioNonnegative : 0 ≤ ResidualAlignmentWeight alignment energy :=
      le_of_not_gt ratioNegative
    by_cases ratioAboveOne : 1 < ResidualAlignmentWeight alignment energy
    · have clampEq : ClampedResidualAlignmentWeight alignment energy = 1 := by
        unfold ClampedResidualAlignmentWeight
        rw [max_eq_right ratioNonnegative, min_eq_left (le_of_lt ratioAboveOne)]
      rw [clampEq]
      have gapNonnegative : 0 ≤ 1 - weight := sub_nonneg.mpr weightAtMostOne
      have secondFactorNonnegative :
          0 ≤ 2 * ResidualAlignmentWeight alignment energy - weight - 1 := by
        nlinarith
      have productNonnegative :
          0 ≤ (1 - weight) *
            (2 * ResidualAlignmentWeight alignment energy - weight - 1) :=
        mul_nonneg gapNonnegative secondFactorNonnegative
      nlinarith
    · have ratioAtMostOne : ResidualAlignmentWeight alignment energy ≤ 1 :=
        le_of_not_gt ratioAboveOne
      have clampEq : ClampedResidualAlignmentWeight alignment energy =
          ResidualAlignmentWeight alignment energy := by
        unfold ClampedResidualAlignmentWeight
        rw [max_eq_right ratioNonnegative, min_eq_right ratioAtMostOne]
      rw [clampEq]
      simpa using sq_nonneg
        (weight - ResidualAlignmentWeight alignment energy)

/-- Positive constrained theorem: for positive shift energy, the clamped
residual-alignment weight globally minimizes risk over all weights in `[0,1]`. -/
theorem clampedResidualAlignmentWeight_globally_minimizes
    (baseRisk alignment energy weight : ℝ)
    (energyPositive : 0 < energy)
    (weightNonnegative : 0 ≤ weight)
    (weightAtMostOne : weight ≤ 1) :
    ContextGateQuadraticRisk baseRisk alignment energy
        (ClampedResidualAlignmentWeight alignment energy) ≤
      ContextGateQuadraticRisk baseRisk alignment energy weight := by
  rw [contextGateQuadraticRisk_complete_square baseRisk alignment energy
      (ClampedResidualAlignmentWeight alignment energy) (ne_of_gt energyPositive),
    contextGateQuadraticRisk_complete_square baseRisk alignment energy weight
      (ne_of_gt energyPositive)]
  have weightedDistanceLe := mul_le_mul_of_nonneg_left
    (clampedResidualAlignmentWeight_distance_minimizes alignment energy weight
      weightNonnegative weightAtMostOne)
    (le_of_lt energyPositive)
  linarith

/-- Exact admission rule for a positive proposed weight: it improves on zero
weight iff weighted gate energy is smaller than twice residual alignment. -/
theorem positive_context_weight_improves_iff_energy_below_alignment
    (baseRisk alignment energy weight : ℝ)
    (weightPositive : 0 < weight) :
    ContextGateQuadraticRisk baseRisk alignment energy weight <
        ContextGateQuadraticRisk baseRisk alignment energy 0 ↔
      weight * energy < 2 * alignment := by
  unfold ContextGateQuadraticRisk
  constructor <;> intro hypothesis <;> nlinarith [mul_pos weightPositive weightPositive]

/-- No-go theorem: if the estimated residual alignment is nonpositive, every
positive gate weight with positive energy strictly worsens quadratic risk. -/
theorem nonpositive_alignment_rejects_every_positive_gate
    (baseRisk alignment energy weight : ℝ)
    (alignmentNonpositive : alignment ≤ 0)
    (energyPositive : 0 < energy)
    (weightPositive : 0 < weight) :
    ContextGateQuadraticRisk baseRisk alignment energy 0 <
      ContextGateQuadraticRisk baseRisk alignment energy weight := by
  unfold ContextGateQuadraticRisk
  have weightSquaredPositive : 0 < weight ^ 2 := sq_pos_of_pos weightPositive
  nlinarith [mul_pos weightSquaredPositive energyPositive]

/-- Parameter rule: positive alignment below positive energy yields an interior
admission weight strictly between zero and one. -/
theorem residualAlignmentWeight_in_unit_interval
    (alignment energy : ℝ)
    (alignmentPositive : 0 < alignment)
    (alignmentBelowEnergy : alignment < energy) :
    0 < ResidualAlignmentWeight alignment energy ∧
      ResidualAlignmentWeight alignment energy < 1 := by
  have energyPositive : 0 < energy := lt_trans alignmentPositive alignmentBelowEnergy
  constructor
  · exact div_pos alignmentPositive energyPositive
  · rw [ResidualAlignmentWeight, div_lt_one energyPositive]
    exact alignmentBelowEnergy

end OCKIndividuationMSpaceComposition
