import OCKIndividuationMSpaceComposition.FiniteNoisyIdentifiability
import OCKIndividuationMSpaceComposition.DefectResponseRobustFalsification

namespace OCKIndividuationMSpaceComposition

universe uModel uTest

/-!
# Exact model competition under coordinatewise bounded observation error

`FiniteNoisyIdentifiability` gives a sufficient recovery theorem for a declared
sum discrepancy.  The present module supplies the complementary exact
worst-case result for coordinatewise rational error boxes.  It is deliberately
model-family agnostic: an affine law, threshold law, nonlinear response,
time-varying operator or domain adapter enters only through its registered
prediction signature.

The central boundary is exact.  Two model signatures have a common observation
within error `epsilon` of both exactly when their coordinatewise distance is at
most `2 * epsilon`.  Hence a coordinate with larger separation is both
sufficient and necessary for worst-case discrimination from these data alone.
-/

/-- A model is compatible with every coordinate of a registered observation. -/
def ModelWithinLInfError
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (model : Model) (observed : Test → ℚ) (epsilon : ℚ) : Prop :=
  ∀ test, |observed test - predict model test| ≤ epsilon

/-- One registered coordinate separates two models beyond both error boxes. -/
def ModelsSeparatedBeyondError
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (left right : Model) (epsilon : ℚ) : Prop :=
  ∃ test, 2 * epsilon < |predict left test - predict right test|

/-- Pointwise overlap condition for the two coordinatewise error boxes. -/
def ModelErrorBoxesOverlapPointwise
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (left right : Model) (epsilon : ℚ) : Prop :=
  ∀ test, |predict left test - predict right test| ≤ 2 * epsilon

/-- Rational absolute distance as an instance of the existing discrepancy API. -/
def rationalAbsoluteDiscrepancy : RatOutcomeDiscrepancy ℚ where
  distance := fun left right => |left - right|
  nonnegative := fun _ _ => abs_nonneg _
  self_zero := fun value => by simp
  symmetric := fun left right => abs_sub_comm left right
  triangle := fun first middle last => abs_sub_le first middle last
  zero_implies_eq := by
    intro left right zero
    exact sub_eq_zero.mp (abs_eq_zero.mp zero)

/-- Registered prediction signatures as the pre-existing finite-test family. -/
def modelPredictionTestFamily
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ) :
    FiniteTypedTestFamily Model Test ℚ where
  observe := predict

/--
Bridge to the older sum-discrepancy theorem: a pointwise `epsilon` certificate
implies total absolute discrepancy at most `card(Test) * epsilon`.
-/
theorem modelWithinLInfError_implies_sumDiscrepancyBound
    {Model : Type uModel} {Test : Type uTest} [Fintype Test]
    (predict : Model → Test → ℚ)
    (model : Model) (observed : Test → ℚ) (epsilon : ℚ)
    (compatible : ModelWithinLInfError predict model observed epsilon) :
    SignatureWithinRatError rationalAbsoluteDiscrepancy
      (modelPredictionTestFamily predict) model observed
      ((Fintype.card Test : ℚ) * epsilon) := by
  unfold SignatureWithinRatError ratSignatureDiscrepancy
  change (∑ test : Test, |predict model test - observed test|) ≤
    (Fintype.card Test : ℚ) * epsilon
  calc
    (∑ test : Test, |predict model test - observed test|) ≤
        ∑ _test : Test, epsilon := by
      apply Finset.sum_le_sum
      intro test _
      rw [abs_sub_comm]
      exact compatible test
    _ = (Fintype.card Test : ℚ) * epsilon := by simp

theorem two_compatible_models_have_pointwise_overlapping_error_boxes
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (left right : Model) (observed : Test → ℚ) (epsilon : ℚ)
    (leftCompatible : ModelWithinLInfError predict left observed epsilon)
    (rightCompatible : ModelWithinLInfError predict right observed epsilon) :
    ModelErrorBoxesOverlapPointwise predict left right epsilon := by
  intro test
  have leftError : |predict left test - observed test| ≤ epsilon := by
    rw [abs_sub_comm]
    exact leftCompatible test
  have rightError : |observed test - predict right test| ≤ epsilon :=
    rightCompatible test
  calc
    |predict left test - predict right test| ≤
        |predict left test - observed test| +
          |observed test - predict right test| :=
      abs_sub_le (predict left test) (observed test) (predict right test)
    _ ≤ epsilon + epsilon := add_le_add leftError rightError
    _ = 2 * epsilon := by ring

/-- Separation beyond `2 epsilon` makes simultaneous compatibility impossible. -/
theorem separated_models_have_no_common_bounded_error_observation
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (left right : Model) (epsilon : ℚ)
    (separated : ModelsSeparatedBeyondError predict left right epsilon) :
    ¬ ∃ observed : Test → ℚ,
      ModelWithinLInfError predict left observed epsilon ∧
      ModelWithinLInfError predict right observed epsilon := by
  rintro ⟨observed, leftCompatible, rightCompatible⟩
  obtain ⟨test, strictSeparation⟩ := separated
  have overlap := two_compatible_models_have_pointwise_overlapping_error_boxes
    predict left right observed epsilon leftCompatible rightCompatible test
  exact (not_lt_of_ge overlap) strictSeparation

/-- The coordinatewise midpoint observation of two model signatures. -/
def modelSignatureMidpoint
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (left right : Model) : Test → ℚ :=
  fun test => (predict left test + predict right test) / 2

theorem midpoint_distance_left
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (left right : Model) (test : Test) :
    |modelSignatureMidpoint predict left right test - predict left test| =
      |predict right test - predict left test| / 2 := by
  unfold modelSignatureMidpoint
  have identity :
      (predict left test + predict right test) / 2 - predict left test =
        (predict right test - predict left test) / 2 := by ring
  rw [identity, abs_div]
  norm_num

theorem midpoint_distance_right
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (left right : Model) (test : Test) :
    |modelSignatureMidpoint predict left right test - predict right test| =
      |predict left test - predict right test| / 2 := by
  unfold modelSignatureMidpoint
  have identity :
      (predict left test + predict right test) / 2 - predict right test =
        (predict left test - predict right test) / 2 := by ring
  rw [identity, abs_div]
  norm_num

/-- If every coordinate gap is at most `2 epsilon`, the midpoint fits both. -/
theorem pointwise_overlap_constructs_common_midpoint_observation
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (left right : Model) (epsilon : ℚ)
    (overlap : ModelErrorBoxesOverlapPointwise predict left right epsilon) :
    ModelWithinLInfError predict left
        (modelSignatureMidpoint predict left right) epsilon ∧
      ModelWithinLInfError predict right
        (modelSignatureMidpoint predict left right) epsilon := by
  constructor
  · intro test
    rw [midpoint_distance_left]
    have bound := overlap test
    rw [abs_sub_comm] at bound
    linarith
  · intro test
    rw [midpoint_distance_right]
    have bound := overlap test
    linarith

/--
Exact overlap theorem: a common bounded-error observation exists if and only if
the two prediction signatures are at most `2 epsilon` apart at every test.
-/
theorem common_bounded_error_observation_iff_pointwise_overlap
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (left right : Model) (epsilon : ℚ) :
    (∃ observed : Test → ℚ,
        ModelWithinLInfError predict left observed epsilon ∧
        ModelWithinLInfError predict right observed epsilon) ↔
      ModelErrorBoxesOverlapPointwise predict left right epsilon := by
  constructor
  · rintro ⟨observed, leftCompatible, rightCompatible⟩
    exact two_compatible_models_have_pointwise_overlapping_error_boxes
      predict left right observed epsilon leftCompatible rightCompatible
  · intro overlap
    exact ⟨modelSignatureMidpoint predict left right,
      pointwise_overlap_constructs_common_midpoint_observation
        predict left right epsilon overlap⟩

/--
Necessary-and-sufficient worst-case discrimination criterion.  This closes the
information-theoretic question for a fixed registered design and error radius.
-/
theorem no_common_observation_iff_separated_beyond_error
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (left right : Model) (epsilon : ℚ) :
    (¬ ∃ observed : Test → ℚ,
        ModelWithinLInfError predict left observed epsilon ∧
        ModelWithinLInfError predict right observed epsilon) ↔
      ModelsSeparatedBeyondError predict left right epsilon := by
  constructor
  · intro noCommon
    by_contra notSeparated
    apply noCommon
    rw [common_bounded_error_observation_iff_pointwise_overlap]
    intro test
    by_contra exceeds
    apply notSeparated
    exact ⟨test, lt_of_not_ge exceeds⟩
  · exact separated_models_have_no_common_bounded_error_observation
      predict left right epsilon

/-- Pairwise design separation makes the compatible model unique. -/
theorem pairwise_separation_gives_unique_compatible_model
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (trueModel : Model) (observed : Test → ℚ) (epsilon : ℚ)
    (trueCompatible :
      ModelWithinLInfError predict trueModel observed epsilon)
    (separatesCompetitors : ∀ competitor, competitor ≠ trueModel →
      ModelsSeparatedBeyondError predict trueModel competitor epsilon) :
    ∃! model : Model, ModelWithinLInfError predict model observed epsilon := by
  refine ⟨trueModel, trueCompatible, ?_⟩
  intro competitor competitorCompatible
  by_contra distinct
  have separated := separatesCompetitors competitor distinct
  exact separated_models_have_no_common_bounded_error_observation
    predict trueModel competitor epsilon separated
    ⟨observed, trueCompatible, competitorCompatible⟩

/--
Operational model-selection margin: a separated competitor has residual larger
than `epsilon` at the separating coordinate, while the true model is bounded by
`epsilon` everywhere.
-/
theorem separated_competitor_exceeds_true_error_tolerance
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (trueModel competitor : Model) (observed : Test → ℚ) (epsilon : ℚ)
    (trueCompatible :
      ModelWithinLInfError predict trueModel observed epsilon)
    (separated :
      ModelsSeparatedBeyondError predict trueModel competitor epsilon) :
    ∃ test, epsilon < |observed test - predict competitor test| := by
  obtain ⟨test, strictSeparation⟩ := separated
  refine ⟨test, ?_⟩
  have trueError : |predict trueModel test - observed test| ≤ epsilon := by
    rw [abs_sub_comm]
    exact trueCompatible test
  have triangle :
      |predict trueModel test - predict competitor test| ≤
        |predict trueModel test - observed test| +
          |observed test - predict competitor test| :=
    abs_sub_le (predict trueModel test) (observed test)
      (predict competitor test)
  linarith

/-- At any coordinate, one of two model residuals is at least half their gap. -/
theorem pairwise_half_gap_is_unavoidable
    {Model : Type uModel} {Test : Type uTest}
    (predict : Model → Test → ℚ)
    (left right : Model) (observed : Test → ℚ) (test : Test) :
    |predict left test - predict right test| / 2 ≤
        |observed test - predict left test| ∨
      |predict left test - predict right test| / 2 ≤
        |observed test - predict right test| := by
  by_contra neither
  push_neg at neither
  have leftError : |predict left test - observed test| <
      |predict left test - predict right test| / 2 := by
    rw [abs_sub_comm]
    exact neither.1
  have triangle :
      |predict left test - predict right test| ≤
        |predict left test - observed test| +
          |observed test - predict right test| :=
    abs_sub_le (predict left test) (observed test) (predict right test)
  linarith [neither.2]

/-!
## Concrete nonlinear and threshold competitors
-/

/-- The first nonlinear extension of the affine defect-response baseline. -/
def quadraticDefectResponse
    (baseline sensitivity curvature defect : ℚ) : ℚ :=
  baseline + sensitivity * defect + curvature * defect ^ 2

theorem quadratic_threePointResidual_exact
    (baseline sensitivity curvature
      firstDefect secondDefect thirdDefect : ℚ) :
    threePointAffineResidual firstDefect secondDefect thirdDefect
        (quadraticDefectResponse baseline sensitivity curvature firstDefect)
        (quadraticDefectResponse baseline sensitivity curvature secondDefect)
        (quadraticDefectResponse baseline sensitivity curvature thirdDefect) =
      curvature * (secondDefect - firstDefect) *
        (thirdDefect - firstDefect) * (secondDefect - thirdDefect) := by
  unfold threePointAffineResidual quadraticDefectResponse
  ring

theorem abs_quadratic_threePointResidual_exact
    (baseline sensitivity curvature
      firstDefect secondDefect thirdDefect : ℚ) :
    |threePointAffineResidual firstDefect secondDefect thirdDefect
        (quadraticDefectResponse baseline sensitivity curvature firstDefect)
        (quadraticDefectResponse baseline sensitivity curvature secondDefect)
        (quadraticDefectResponse baseline sensitivity curvature thirdDefect)| =
      |curvature| * |secondDefect - firstDefect| *
        |thirdDefect - firstDefect| * |thirdDefect - secondDefect| := by
  rw [quadratic_threePointResidual_exact, abs_mul, abs_mul, abs_mul,
    abs_sub_comm secondDefect thirdDefect]

/--
Power theorem for the nonlinear competitor: if its noiseless curvature signal
exceeds twice the sharp observation envelope, every admissible noisy
observation triggers the affine rejection rule.
-/
theorem quadratic_signal_above_twice_envelope_forces_affine_rejection
    (baseline sensitivity curvature
      firstDefect secondDefect thirdDefect
      observedFirst observedSecond observedThird epsilon : ℚ)
    (firstError : |observedFirst -
      quadraticDefectResponse baseline sensitivity curvature firstDefect| ≤ epsilon)
    (secondError : |observedSecond -
      quadraticDefectResponse baseline sensitivity curvature secondDefect| ≤ epsilon)
    (thirdError : |observedThird -
      quadraticDefectResponse baseline sensitivity curvature thirdDefect| ≤ epsilon)
    (signal :
      2 * threePointResidualErrorEnvelope
          epsilon firstDefect secondDefect thirdDefect <
        |curvature| * |secondDefect - firstDefect| *
          |thirdDefect - firstDefect| * |thirdDefect - secondDefect|) :
    RobustlyRejectsAffineResponse
      firstDefect secondDefect thirdDefect
      observedFirst observedSecond observedThird epsilon := by
  let trueFirst :=
    quadraticDefectResponse baseline sensitivity curvature firstDefect
  let trueSecond :=
    quadraticDefectResponse baseline sensitivity curvature secondDefect
  let trueThird :=
    quadraticDefectResponse baseline sensitivity curvature thirdDefect
  have residualError := observed_threePointResidual_error_bound
    firstDefect secondDefect thirdDefect
    trueFirst trueSecond trueThird
    observedFirst observedSecond observedThird epsilon
    firstError secondError thirdError
  have trueResidualMagnitude :
      |threePointAffineResidual firstDefect secondDefect thirdDefect
          trueFirst trueSecond trueThird| =
        |curvature| * |secondDefect - firstDefect| *
          |thirdDefect - firstDefect| * |thirdDefect - secondDefect| := by
    exact abs_quadratic_threePointResidual_exact
      baseline sensitivity curvature firstDefect secondDefect thirdDefect
  unfold RobustlyRejectsAffineResponse
  rw [← trueResidualMagnitude] at signal
  have triangle :
      |threePointAffineResidual firstDefect secondDefect thirdDefect
          trueFirst trueSecond trueThird| ≤
        |threePointAffineResidual firstDefect secondDefect thirdDefect
            trueFirst trueSecond trueThird -
          threePointAffineResidual firstDefect secondDefect thirdDefect
            observedFirst observedSecond observedThird| +
        |threePointAffineResidual firstDefect secondDefect thirdDefect
          observedFirst observedSecond observedThird| := by
    have := abs_add_le
      (threePointAffineResidual firstDefect secondDefect thirdDefect
          trueFirst trueSecond trueThird -
        threePointAffineResidual firstDefect secondDefect thirdDefect
          observedFirst observedSecond observedThird)
      (threePointAffineResidual firstDefect secondDefect thirdDefect
        observedFirst observedSecond observedThird)
    convert this using 1 <;> ring
  have reversedError :
      |threePointAffineResidual firstDefect secondDefect thirdDefect
          trueFirst trueSecond trueThird -
        threePointAffineResidual firstDefect secondDefect thirdDefect
          observedFirst observedSecond observedThird| ≤
        threePointResidualErrorEnvelope
          epsilon firstDefect secondDefect thirdDefect := by
    rw [abs_sub_comm]
    exact residualError
  linarith

/-- On the normalized half-grid, the sharp residual noise envelope is `2ε`. -/
theorem halfGrid_threePointResidualErrorEnvelope (epsilon : ℚ) :
    threePointResidualErrorEnvelope epsilon 0 (1 / 2) 1 = 2 * epsilon := by
  unfold threePointResidualErrorEnvelope
  norm_num
  ring

/-- On the normalized half-grid, quadratic curvature signal is `|c| / 4`. -/
theorem halfGrid_abs_quadraticResidual
    (baseline sensitivity curvature : ℚ) :
    |threePointAffineResidual 0 (1 / 2) 1
        (quadraticDefectResponse baseline sensitivity curvature 0)
        (quadraticDefectResponse baseline sensitivity curvature (1 / 2))
        (quadraticDefectResponse baseline sensitivity curvature 1)| =
      |curvature| / 4 := by
  rw [abs_quadratic_threePointResidual_exact]
  norm_num
  ring

/-- The midpoint maximizes the quadratic gap product on the normalized span. -/
theorem normalized_middle_gap_product_le_quarter
    (middle : ℚ) :
    middle * (1 - middle) ≤ 1 / 4 := by
  nlinarith [sq_nonneg (2 * middle - 1)]

/--
Optimal three-level design theorem for quadratic-vs-affine discrimination:
with endpoints fixed at `0` and `1`, no interior third point produces a larger
noiseless curvature residual than `1/2`.
-/
theorem halfGrid_maximizes_quadratic_curvature_signal
    (baseline sensitivity curvature middle : ℚ)
    (middleNonnegative : 0 ≤ middle)
    (middleAtMostOne : middle ≤ 1) :
    |threePointAffineResidual 0 middle 1
        (quadraticDefectResponse baseline sensitivity curvature 0)
        (quadraticDefectResponse baseline sensitivity curvature middle)
        (quadraticDefectResponse baseline sensitivity curvature 1)| ≤
      |curvature| / 4 := by
  rw [abs_quadratic_threePointResidual_exact]
  simp only [sub_zero, abs_one, mul_one]
  rw [abs_of_nonneg middleNonnegative,
    abs_of_nonneg (sub_nonneg.mpr middleAtMostOne)]
  have gap := normalized_middle_gap_product_le_quarter middle
  calc
    |curvature| * middle * (1 - middle) =
        |curvature| * (middle * (1 - middle)) := by ring
    _ ≤ |curvature| * (1 / 4) :=
      mul_le_mul_of_nonneg_left gap (abs_nonneg _)
    _ = |curvature| / 4 := by ring

/--
Concrete power certificate: on defects `0, 1/2, 1`, curvature magnitude greater
than `16 epsilon` forces rejection of every affine response for every
coordinatewise error realization bounded by `epsilon`.
-/
theorem halfGrid_curvature_above_sixteen_epsilon_forces_affine_rejection
    (baseline sensitivity curvature
      observedFirst observedSecond observedThird epsilon : ℚ)
    (firstError : |observedFirst -
      quadraticDefectResponse baseline sensitivity curvature 0| ≤ epsilon)
    (secondError : |observedSecond -
      quadraticDefectResponse baseline sensitivity curvature (1 / 2)| ≤ epsilon)
    (thirdError : |observedThird -
      quadraticDefectResponse baseline sensitivity curvature 1| ≤ epsilon)
    (detectable : 16 * epsilon < |curvature|) :
    RobustlyRejectsAffineResponse
      0 (1 / 2) 1 observedFirst observedSecond observedThird epsilon := by
  apply quadratic_signal_above_twice_envelope_forces_affine_rejection
    baseline sensitivity curvature 0 (1 / 2) 1
    observedFirst observedSecond observedThird epsilon
    firstError secondError thirdError
  rw [halfGrid_threePointResidualErrorEnvelope]
  norm_num
  linarith

/-- Hard threshold response used as a mature change-point baseline. -/
def hardThresholdResponse
    (low high threshold defect : ℚ) : ℚ :=
  if defect < threshold then low else high

/-- If all registered defects lie below both thresholds, the thresholds alias. -/
theorem unstraddled_thresholds_have_identical_predictions
    {Test : Type uTest}
    (defect : Test → ℚ) (low high firstThreshold secondThreshold : ℚ)
    (belowBoth : ∀ test,
      defect test < firstThreshold ∧ defect test < secondThreshold) :
    (∀ test, hardThresholdResponse low high firstThreshold (defect test) =
      hardThresholdResponse low high secondThreshold (defect test)) := by
  intro test
  simp [hardThresholdResponse, belowBoth test]

/-- A straddling test exposes the full response gap between two thresholds. -/
theorem straddling_test_separates_threshold_responses
    (low high firstThreshold secondThreshold defect : ℚ)
    (firstAtOrBelow : firstThreshold ≤ defect)
    (belowSecond : defect < secondThreshold) :
    |hardThresholdResponse low high firstThreshold defect -
        hardThresholdResponse low high secondThreshold defect| =
      |high - low| := by
  simp [hardThresholdResponse, not_lt.mpr firstAtOrBelow, belowSecond]

/-- Quantitative threshold-model discrimination under bounded error. -/
theorem straddling_gap_beyond_noise_separates_threshold_models
    (low high firstThreshold secondThreshold defect epsilon : ℚ)
    (firstAtOrBelow : firstThreshold ≤ defect)
    (belowSecond : defect < secondThreshold)
    (gap : 2 * epsilon < |high - low|) :
    2 * epsilon <
      |hardThresholdResponse low high firstThreshold defect -
        hardThresholdResponse low high secondThreshold defect| := by
  rw [straddling_test_separates_threshold_responses
    low high firstThreshold secondThreshold defect firstAtOrBelow belowSecond]
  exact gap

/-- A registered straddling coordinate separates the two threshold models. -/
theorem registered_straddle_separates_threshold_models
    {Test : Type uTest}
    (defect : Test → ℚ) (low high firstThreshold secondThreshold epsilon : ℚ)
    (test : Test)
    (firstAtOrBelow : firstThreshold ≤ defect test)
    (belowSecond : defect test < secondThreshold)
    (gap : 2 * epsilon < |high - low|) :
    ModelsSeparatedBeyondError
      (fun threshold test =>
        hardThresholdResponse low high threshold (defect test))
      firstThreshold secondThreshold epsilon := by
  refine ⟨test, ?_⟩
  exact straddling_gap_beyond_noise_separates_threshold_models
    low high firstThreshold secondThreshold (defect test) epsilon
    firstAtOrBelow belowSecond gap

/-- Without a straddling coordinate, threshold parameters remain aliased. -/
theorem unstraddled_thresholds_not_separated
    {Test : Type uTest}
    (defect : Test → ℚ) (low high firstThreshold secondThreshold epsilon : ℚ)
    (epsilonNonnegative : 0 ≤ epsilon)
    (belowBoth : ∀ test,
      defect test < firstThreshold ∧ defect test < secondThreshold) :
    ¬ ModelsSeparatedBeyondError
      (fun threshold test =>
        hardThresholdResponse low high threshold (defect test))
      firstThreshold secondThreshold epsilon := by
  rintro ⟨test, separated⟩
  have equalPredictions := unstraddled_thresholds_have_identical_predictions
    defect low high firstThreshold secondThreshold belowBoth test
  change 2 * epsilon <
    |hardThresholdResponse low high firstThreshold (defect test) -
      hardThresholdResponse low high secondThreshold (defect test)| at separated
  rw [equalPredictions, sub_self, abs_zero] at separated
  linarith

/--
Operational no-go: an unstraddled design admits a common bounded-error
observation for the two distinct threshold parameters.
-/
theorem unstraddled_thresholds_admit_common_observation
    {Test : Type uTest}
    (defect : Test → ℚ) (low high firstThreshold secondThreshold epsilon : ℚ)
    (epsilonNonnegative : 0 ≤ epsilon)
    (belowBoth : ∀ test,
      defect test < firstThreshold ∧ defect test < secondThreshold) :
    ∃ observed : Test → ℚ,
      ModelWithinLInfError
          (fun threshold test =>
            hardThresholdResponse low high threshold (defect test))
          firstThreshold observed epsilon ∧
        ModelWithinLInfError
          (fun threshold test =>
            hardThresholdResponse low high threshold (defect test))
          secondThreshold observed epsilon := by
  rw [common_bounded_error_observation_iff_pointwise_overlap]
  intro test
  have equalPredictions := unstraddled_thresholds_have_identical_predictions
    defect low high firstThreshold secondThreshold belowBoth test
  change |hardThresholdResponse low high firstThreshold (defect test) -
      hardThresholdResponse low high secondThreshold (defect test)| ≤
    2 * epsilon
  rw [equalPredictions, sub_self, abs_zero]
  linarith

end OCKIndividuationMSpaceComposition
