import OCKIndividuationMSpaceComposition.BrierResidualAlignmentAdmission

namespace OCKIndividuationMSpaceComposition

/-!
# Brier risk with a partially identified binary outcome

A missing event indicator is not a negative event.  When the available carrier
evidence identifies only the binary set `{0,1}`, the Brier loss is an interval.
This module gives its exact endpoints and the corresponding model-comparison
obstruction.  It is the formal bridge used by the UR3 CobotOps missing-outcome
diagnostic.
-/

/-- Scalar Brier loss for a binary outcome encoded in `ℝ`. -/
def BinaryBrierLoss (truth prediction : ℝ) : ℝ :=
  (truth - prediction) ^ 2

/-- The only outcome information retained by an unresolved binary carrier. -/
def CompatibleBinaryLabel (truth : ℝ) : Prop :=
  truth = 0 ∨ truth = 1

/-- Sharp lower endpoint of Brier loss when the label is known only to be binary. -/
def PartialBinaryBrierLower (prediction : ℝ) : ℝ :=
  min (BinaryBrierLoss 0 prediction) (BinaryBrierLoss 1 prediction)

/-- Sharp upper endpoint of Brier loss when the label is known only to be binary. -/
def PartialBinaryBrierUpper (prediction : ℝ) : ℝ :=
  max (BinaryBrierLoss 0 prediction) (BinaryBrierLoss 1 prediction)

/-- Positive theorem: every compatible completion lies inside the partial-label
Brier interval. -/
theorem compatible_binary_label_brier_bounded
    (truth prediction : ℝ) (compatible : CompatibleBinaryLabel truth) :
    PartialBinaryBrierLower prediction ≤ BinaryBrierLoss truth prediction ∧
      BinaryBrierLoss truth prediction ≤ PartialBinaryBrierUpper prediction := by
  rcases compatible with rfl | rfl
  · exact ⟨min_le_left _ _, le_max_left _ _⟩
  · exact ⟨min_le_right _ _, le_max_right _ _⟩

/-- Sharpness theorem: every interval covering both binary completions must
contain the stated lower and upper endpoints. -/
theorem partial_binary_brier_interval_is_sharp
    (prediction lower upper : ℝ)
    (coversZeroLower : lower ≤ BinaryBrierLoss 0 prediction)
    (coversOneLower : lower ≤ BinaryBrierLoss 1 prediction)
    (coversZeroUpper : BinaryBrierLoss 0 prediction ≤ upper)
    (coversOneUpper : BinaryBrierLoss 1 prediction ≤ upper) :
    lower ≤ PartialBinaryBrierLower prediction ∧
      PartialBinaryBrierUpper prediction ≤ upper := by
  exact ⟨le_min coversZeroLower coversOneLower,
    max_le coversZeroUpper coversOneUpper⟩

/-- Exact sensitivity formula for completing one missing binary label. -/
theorem binary_brier_label_flip_difference (prediction : ℝ) :
    BinaryBrierLoss 1 prediction - BinaryBrierLoss 0 prediction =
      1 - 2 * prediction := by
  unfold BinaryBrierLoss
  ring

/-- A missing binary label has a unique Brier loss only for the uninformative
half-probability forecast. -/
theorem missing_binary_label_has_unique_brier_iff_half
    (prediction : ℝ) :
    BinaryBrierLoss 0 prediction = BinaryBrierLoss 1 prediction ↔
      prediction = (1 / 2 : ℝ) := by
  constructor
  · intro equalLoss
    have difference := binary_brier_label_flip_difference prediction
    rw [← equalLoss] at difference
    simp only [sub_self] at difference
    linarith
  · intro predictionHalf
    rw [predictionHalf]
    norm_num [BinaryBrierLoss]

/-- No-go theorem for model adjudication: for two distinct probability
forecasts inside `[0,1]`, the unresolved label can reverse which forecast has
smaller Brier loss. -/
theorem missing_binary_label_can_reverse_forecast_ranking
    (lowerPrediction upperPrediction : ℝ)
    (lowerNonnegative : 0 ≤ lowerPrediction)
    (strictlyOrdered : lowerPrediction < upperPrediction)
    (upperAtMostOne : upperPrediction ≤ 1) :
    BinaryBrierLoss 0 lowerPrediction < BinaryBrierLoss 0 upperPrediction ∧
      BinaryBrierLoss 1 upperPrediction < BinaryBrierLoss 1 lowerPrediction := by
  unfold BinaryBrierLoss
  constructor <;> nlinarith

/-- Lower endpoint of total Brier loss for a finite family of independently
unresolved binary labels. -/
def PartialBinaryBrierTotalLower {n : ℕ} (prediction : Fin n → ℝ) : ℝ :=
  ∑ i, PartialBinaryBrierLower (prediction i)

/-- Upper endpoint of total Brier loss for a finite family of independently
unresolved binary labels. -/
def PartialBinaryBrierTotalUpper {n : ℕ} (prediction : Fin n → ℝ) : ℝ :=
  ∑ i, PartialBinaryBrierUpper (prediction i)

/-- Positive finite-sample theorem: every compatible label completion has
total Brier loss between the computable endpoint sums. -/
theorem compatible_binary_labels_total_brier_bounded {n : ℕ}
    (truth prediction : Fin n → ℝ)
    (compatible : ∀ i, CompatibleBinaryLabel (truth i)) :
    PartialBinaryBrierTotalLower prediction ≤
        ∑ i, BinaryBrierLoss (truth i) (prediction i) ∧
      (∑ i, BinaryBrierLoss (truth i) (prediction i)) ≤
        PartialBinaryBrierTotalUpper prediction := by
  constructor
  · apply Finset.sum_le_sum
    intro i _
    exact (compatible_binary_label_brier_bounded
      (truth i) (prediction i) (compatible i)).1
  · apply Finset.sum_le_sum
    intro i _
    exact (compatible_binary_label_brier_bounded
      (truth i) (prediction i) (compatible i)).2

end OCKIndividuationMSpaceComposition
