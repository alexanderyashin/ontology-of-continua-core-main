import OCKIndividuationMSpaceComposition.QuantitativeContextTransport

namespace OCKIndividuationMSpaceComposition

universe uFamily

/-!
# Robust evidence-transport defect under calibration uncertainty

The heterogeneous coordinates of an evidence potential need explicit
calibration weights.  A single guessed weight vector gives false precision.
This module registers a componentwise uncertainty box and proves that its
lower and upper corners are the exact best- and worst-case defects.  It also
gives threshold certificates, an unresolved-zone theorem, and a robust
composition law.
-/

/-- Componentwise order on evidence-transport calibration weights. -/
def EvidenceTransportWeights.ComponentwiseLE
    (first second : EvidenceTransportWeights) : Prop :=
  first.lookWeight ≤ second.lookWeight ∧
    first.spendWeight ≤ second.spendWeight ∧
    first.debtWeight ≤ second.debtWeight

namespace EvidenceTransportWeights

theorem componentwiseLE_refl (weights : EvidenceTransportWeights) :
    weights.ComponentwiseLE weights :=
  ⟨le_rfl, le_rfl, le_rfl⟩

theorem componentwiseLE_trans
    {first middle last : EvidenceTransportWeights}
    (firstMiddle : first.ComponentwiseLE middle)
    (middleLast : middle.ComponentwiseLE last) :
    first.ComponentwiseLE last :=
  ⟨firstMiddle.1.trans middleLast.1,
    firstMiddle.2.1.trans middleLast.2.1,
    firstMiddle.2.2.trans middleLast.2.2⟩

theorem nonnegative_of_nonnegative_of_componentwiseLE
    {first second : EvidenceTransportWeights}
    (firstNonnegative : first.Nonnegative)
    (ordered : first.ComponentwiseLE second) :
    second.Nonnegative :=
  ⟨firstNonnegative.1.trans ordered.1,
    firstNonnegative.2.1.trans ordered.2.1,
    firstNonnegative.2.2.trans ordered.2.2⟩

end EvidenceTransportWeights

/-- Registered interval uncertainty for every heterogeneous defect weight. -/
structure EvidenceTransportWeightBox where
  lower : EvidenceTransportWeights
  upper : EvidenceTransportWeights
  lowerNonnegative : lower.Nonnegative
  lower_le_upper : lower.ComponentwiseLE upper

namespace EvidenceTransportWeightBox

/-- A calibration is admissible exactly when it lies in the registered box. -/
def Admissible
    (box : EvidenceTransportWeightBox)
    (weights : EvidenceTransportWeights) : Prop :=
  box.lower.ComponentwiseLE weights ∧ weights.ComponentwiseLE box.upper

theorem lower_admissible (box : EvidenceTransportWeightBox) :
    box.Admissible box.lower :=
  ⟨EvidenceTransportWeights.componentwiseLE_refl _, box.lower_le_upper⟩

theorem upper_admissible (box : EvidenceTransportWeightBox) :
    box.Admissible box.upper :=
  ⟨box.lower_le_upper,
    EvidenceTransportWeights.componentwiseLE_refl _⟩

theorem upperNonnegative (box : EvidenceTransportWeightBox) :
    box.upper.Nonnegative :=
  EvidenceTransportWeights.nonnegative_of_nonnegative_of_componentwiseLE
    box.lowerNonnegative box.lower_le_upper

theorem admissible_nonnegative
    (box : EvidenceTransportWeightBox)
    {weights : EvidenceTransportWeights}
    (admissible : box.Admissible weights) :
    weights.Nonnegative :=
  EvidenceTransportWeights.nonnegative_of_nonnegative_of_componentwiseLE
    box.lowerNonnegative admissible.1

end EvidenceTransportWeightBox

/-- Increasing any nonnegative calibration weight cannot decrease defect. -/
theorem weightedEvidenceTransportDefect_mono_weights
    {Family : Type uFamily} [PseudoMetricSpace Family]
    {lower upper : EvidenceTransportWeights}
    (ordered : lower.ComponentwiseLE upper)
    (source target : EvidencePotential Family) :
    weightedEvidenceTransportDefect lower source target ≤
      weightedEvidenceTransportDefect upper source target := by
  have look := mul_le_mul_of_nonneg_right ordered.1
    (directedDrop_nonnegative source.look target.look)
  have spend := mul_le_mul_of_nonneg_right ordered.2.1
    (directedDrop_nonnegative source.cumulativeAlphaSpend
      target.cumulativeAlphaSpend)
  have debt := mul_le_mul_of_nonneg_right ordered.2.2
    (directedDrop_nonnegative source.calibrationDebt target.calibrationDebt)
  unfold weightedEvidenceTransportDefect
  linarith

def robustLowerEvidenceTransportDefect
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (source target : EvidencePotential Family) : ℝ :=
  weightedEvidenceTransportDefect box.lower source target

def robustUpperEvidenceTransportDefect
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (source target : EvidencePotential Family) : ℝ :=
  weightedEvidenceTransportDefect box.upper source target

/-- Every admissible calibration lies in the exact corner-defined defect
interval.  Both endpoints are attainable because both corners are admissible. -/
theorem admissible_weight_defect_sandwich
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    {weights : EvidenceTransportWeights}
    (admissible : box.Admissible weights)
    (source target : EvidencePotential Family) :
    robustLowerEvidenceTransportDefect box source target ≤
        weightedEvidenceTransportDefect weights source target ∧
      weightedEvidenceTransportDefect weights source target ≤
        robustUpperEvidenceTransportDefect box source target := by
  exact ⟨
    weightedEvidenceTransportDefect_mono_weights admissible.1 source target,
    weightedEvidenceTransportDefect_mono_weights admissible.2 source target⟩

/-- A worst-corner pass certifies the threshold for every admissible
calibration. -/
theorem robust_upper_threshold_certifies_all_weights
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (source target : EvidencePotential Family)
    (threshold : ℝ)
    (upperPass : robustUpperEvidenceTransportDefect box source target ≤ threshold) :
    ∀ weights, box.Admissible weights →
      weightedEvidenceTransportDefect weights source target ≤ threshold := by
  intro weights admissible
  exact (admissible_weight_defect_sandwich box admissible source target).2.trans
    upperPass

/-- A best-corner failure refutes the threshold for every admissible
calibration. -/
theorem robust_lower_threshold_refutes_all_weights
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (source target : EvidencePotential Family)
    (threshold : ℝ)
    (lowerFails : threshold < robustLowerEvidenceTransportDefect box source target) :
    ∀ weights, box.Admissible weights →
      threshold < weightedEvidenceTransportDefect weights source target := by
  intro weights admissible
  exact lowerFails.trans_le
    (admissible_weight_defect_sandwich box admissible source target).1

/-- If the threshold cuts the robust interval, admissible calibrations support
opposite decisions.  The model must report unresolved calibration dependence. -/
theorem threshold_inside_weight_uncertainty_is_unresolved
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (source target : EvidencePotential Family)
    (threshold : ℝ)
    (lowerPass : robustLowerEvidenceTransportDefect box source target ≤ threshold)
    (upperFails : threshold < robustUpperEvidenceTransportDefect box source target) :
    (∃ weights, box.Admissible weights ∧
        weightedEvidenceTransportDefect weights source target ≤ threshold) ∧
      (∃ weights, box.Admissible weights ∧
        threshold < weightedEvidenceTransportDefect weights source target) := by
  exact ⟨⟨box.lower, box.lower_admissible, lowerPass⟩,
    ⟨box.upper, box.upper_admissible, upperFails⟩⟩

/-- Exact uncertainty width.  This turns calibration improvement into a
numerical prediction: shrinking a weight interval reduces uncertainty in
proportion to the corresponding observed directed drop. -/
theorem robustEvidenceTransportDefect_width_eq
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (source target : EvidencePotential Family) :
    robustUpperEvidenceTransportDefect box source target -
        robustLowerEvidenceTransportDefect box source target =
      (box.upper.lookWeight - box.lower.lookWeight) *
          directedDrop source.look target.look +
        (box.upper.spendWeight - box.lower.spendWeight) *
          directedDrop source.cumulativeAlphaSpend
            target.cumulativeAlphaSpend +
        (box.upper.debtWeight - box.lower.debtWeight) *
          directedDrop source.calibrationDebt target.calibrationDebt := by
  unfold robustUpperEvidenceTransportDefect
    robustLowerEvidenceTransportDefect weightedEvidenceTransportDefect
  ring

/-- Robust endpoint defect composes through an intermediate state; therefore
the sum of worst-corner local defects is a sound global certificate. -/
theorem robustUpperEvidenceTransportDefect_triangle
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (first middle last : EvidencePotential Family) :
    robustUpperEvidenceTransportDefect box first last ≤
      robustUpperEvidenceTransportDefect box first middle +
        robustUpperEvidenceTransportDefect box middle last := by
  exact weightedEvidenceTransportDefect_triangle box.upper
    box.upperNonnegative first middle last

/-- A composed worst-corner budget controls the end-to-end defect for every
single admissible calibration. -/
theorem every_admissible_weight_end_to_end_le_robust_path_sum
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    {weights : EvidenceTransportWeights}
    (admissible : box.Admissible weights)
    (first middle last : EvidencePotential Family) :
    weightedEvidenceTransportDefect weights first last ≤
      robustUpperEvidenceTransportDefect box first middle +
        robustUpperEvidenceTransportDefect box middle last := by
  exact (admissible_weight_defect_sandwich box admissible first last).2.trans
    (robustUpperEvidenceTransportDefect_triangle box first middle last)

/-- Sum of worst-corner defects along a finite registered path. -/
def robustEvidenceTransportPathBudget
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (path : ℕ → EvidencePotential Family)
    (steps : ℕ) : ℝ :=
  ∑ step ∈ Finset.range steps,
    robustUpperEvidenceTransportDefect box (path step) (path (step + 1))

/-- The robust endpoint defect is bounded by the complete finite path budget,
not only by a two-step witness. -/
theorem robustUpperEvidenceTransportDefect_le_finite_pathBudget
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    (path : ℕ → EvidencePotential Family) :
    ∀ steps,
      robustUpperEvidenceTransportDefect box (path 0) (path steps) ≤
        robustEvidenceTransportPathBudget box path steps := by
  intro steps
  induction steps with
  | zero =>
      simp [robustEvidenceTransportPathBudget,
        robustUpperEvidenceTransportDefect,
        weightedEvidenceTransportDefect, directedDrop]
  | succ steps inductionHypothesis =>
      calc
        robustUpperEvidenceTransportDefect box (path 0) (path (steps + 1)) ≤
            robustUpperEvidenceTransportDefect box (path 0) (path steps) +
              robustUpperEvidenceTransportDefect box (path steps)
                (path (steps + 1)) :=
          robustUpperEvidenceTransportDefect_triangle box
            (path 0) (path steps) (path (steps + 1))
        _ ≤ robustEvidenceTransportPathBudget box path steps +
              robustUpperEvidenceTransportDefect box (path steps)
                (path (steps + 1)) :=
          add_le_add inductionHypothesis le_rfl
        _ = robustEvidenceTransportPathBudget box path (steps + 1) := by
          simp [robustEvidenceTransportPathBudget, Finset.sum_range_succ]

/-- One finite path budget controls every admissible calibration at its
endpoint.  This is the executable M6 path-level verifier. -/
theorem every_admissible_weight_endpoint_le_finite_pathBudget
    {Family : Type uFamily} [PseudoMetricSpace Family]
    (box : EvidenceTransportWeightBox)
    {weights : EvidenceTransportWeights}
    (admissible : box.Admissible weights)
    (path : ℕ → EvidencePotential Family)
    (steps : ℕ) :
    weightedEvidenceTransportDefect weights (path 0) (path steps) ≤
      robustEvidenceTransportPathBudget box path steps := by
  exact (admissible_weight_defect_sandwich box admissible
      (path 0) (path steps)).2.trans
    (robustUpperEvidenceTransportDefect_le_finite_pathBudget box path steps)

end OCKIndividuationMSpaceComposition
