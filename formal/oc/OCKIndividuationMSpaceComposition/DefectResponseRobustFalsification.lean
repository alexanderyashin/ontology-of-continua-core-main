import OCKIndividuationMSpaceComposition.DefectResponseDynamics

namespace OCKIndividuationMSpaceComposition

/-!
## Noise-robust falsification of the affine defect-response adapter

Two points identify an affine response but cannot test its form.  Three points
can test the form, provided the observed curvature is compared with the error
envelope induced by the registered observation design.  This module makes that
comparison division-free, so it remains meaningful for rational fixtures and
does not become unstable when defect levels are close.
-/

/-- Signed division-free curvature residual for three defect/hazard pairs. -/
def threePointAffineResidual
    (firstDefect secondDefect thirdDefect
      firstHazard secondHazard thirdHazard : ℚ) : ℚ :=
  (secondHazard - firstHazard) * (thirdDefect - firstDefect) -
    (thirdHazard - firstHazard) * (secondDefect - firstDefect)

theorem threePointAffineCompatible_iff_residual_zero
    (firstDefect secondDefect thirdDefect
      firstHazard secondHazard thirdHazard : ℚ) :
    ThreePointAffineCompatible
        firstDefect secondDefect thirdDefect
        firstHazard secondHazard thirdHazard ↔
      threePointAffineResidual
        firstDefect secondDefect thirdDefect
        firstHazard secondHazard thirdHazard = 0 := by
  unfold ThreePointAffineCompatible threePointAffineResidual
  constructor
  · exact sub_eq_zero.mpr
  · exact sub_eq_zero.mp

theorem affine_response_has_zero_threePointResidual
    (baseline sensitivity firstDefect secondDefect thirdDefect : ℚ) :
    threePointAffineResidual firstDefect secondDefect thirdDefect
        (affineDefectResponse baseline sensitivity firstDefect)
        (affineDefectResponse baseline sensitivity secondDefect)
        (affineDefectResponse baseline sensitivity thirdDefect) = 0 := by
  rw [← threePointAffineCompatible_iff_residual_zero]
  exact affine_response_is_threePointCompatible
    baseline sensitivity firstDefect secondDefect thirdDefect

/-- Exact `L∞` support-function envelope for the three hazard errors. -/
def threePointResidualErrorEnvelope
    (epsilon firstDefect secondDefect thirdDefect : ℚ) : ℚ :=
  epsilon *
    (|thirdDefect - firstDefect| +
      |secondDefect - firstDefect| +
      |thirdDefect - secondDefect|)

/-- A reusable three-coordinate `L∞` linear-functional bound. -/
theorem abs_three_term_linear_bound
    (firstError secondError thirdError
      firstCoefficient secondCoefficient thirdCoefficient epsilon : ℚ)
    (firstBound : |firstError| ≤ epsilon)
    (secondBound : |secondError| ≤ epsilon)
    (thirdBound : |thirdError| ≤ epsilon) :
    |firstError * firstCoefficient +
        secondError * secondCoefficient +
        thirdError * thirdCoefficient| ≤
      epsilon *
        (|firstCoefficient| + |secondCoefficient| + |thirdCoefficient|) := by
  have firstTwoBound :
      |firstError * firstCoefficient + secondError * secondCoefficient| ≤
        |firstError * firstCoefficient| +
          |secondError * secondCoefficient| :=
    abs_add_le _ _
  have firstProductBound :
      |firstError * firstCoefficient| ≤ epsilon * |firstCoefficient| := by
    rw [abs_mul]
    exact mul_le_mul_of_nonneg_right firstBound (abs_nonneg _)
  have secondProductBound :
      |secondError * secondCoefficient| ≤ epsilon * |secondCoefficient| := by
    rw [abs_mul]
    exact mul_le_mul_of_nonneg_right secondBound (abs_nonneg _)
  have thirdProductBound :
      |thirdError * thirdCoefficient| ≤ epsilon * |thirdCoefficient| := by
    rw [abs_mul]
    exact mul_le_mul_of_nonneg_right thirdBound (abs_nonneg _)
  have outerTriangle :
      |(firstError * firstCoefficient + secondError * secondCoefficient) +
          thirdError * thirdCoefficient| ≤
        |firstError * firstCoefficient + secondError * secondCoefficient| +
          |thirdError * thirdCoefficient| :=
    abs_add_le _ _
  have expandedTriangle :
      |firstError * firstCoefficient + secondError * secondCoefficient| +
          |thirdError * thirdCoefficient| ≤
        (|firstError * firstCoefficient| +
          |secondError * secondCoefficient|) +
          |thirdError * thirdCoefficient| :=
    add_le_add firstTwoBound (le_refl _)
  have productBound :
      (|firstError * firstCoefficient| +
          |secondError * secondCoefficient|) +
          |thirdError * thirdCoefficient| ≤
        (epsilon * |firstCoefficient| +
          epsilon * |secondCoefficient|) +
          epsilon * |thirdCoefficient| :=
    add_le_add (add_le_add firstProductBound secondProductBound)
      thirdProductBound
  calc
    |firstError * firstCoefficient +
        secondError * secondCoefficient +
        thirdError * thirdCoefficient| ≤
      |firstError * firstCoefficient + secondError * secondCoefficient| +
        |thirdError * thirdCoefficient| := outerTriangle
    _ ≤ (|firstError * firstCoefficient| +
        |secondError * secondCoefficient|) +
        |thirdError * thirdCoefficient| := expandedTriangle
    _ ≤ epsilon * |firstCoefficient| +
        epsilon * |secondCoefficient| +
        epsilon * |thirdCoefficient| := productBound
    _ = epsilon *
        (|firstCoefficient| + |secondCoefficient| + |thirdCoefficient|) := by
      rw [mul_add, mul_add]

/-- A rational direction attaining the support function of an interval. -/
def rationalDirection (value : ℚ) : ℚ :=
  if 0 ≤ value then 1 else -1

theorem abs_rationalDirection (value : ℚ) :
    |rationalDirection value| = 1 := by
  unfold rationalDirection
  by_cases nonnegative : 0 ≤ value
  · simp [nonnegative]
  · simp [nonnegative]

theorem rationalDirection_mul_self_eq_abs (value : ℚ) :
    rationalDirection value * value = |value| := by
  unfold rationalDirection
  by_cases nonnegative : 0 ≤ value
  · rw [if_pos nonnegative, abs_of_nonneg nonnegative]
    ring
  · have nonpositive : value ≤ 0 := le_of_not_ge nonnegative
    rw [if_neg nonnegative, abs_of_nonpos nonpositive]
    ring

/--
The three-coordinate envelope is sharp: for every nonnegative `epsilon` there
are admissible coordinate errors that attain it exactly.  Consequently no
universally smaller rejection threshold can be justified from coordinatewise
`epsilon` bounds alone.
-/
theorem abs_three_term_linear_bound_is_sharp
    (firstCoefficient secondCoefficient thirdCoefficient epsilon : ℚ)
    (epsilonNonnegative : 0 ≤ epsilon) :
    ∃ firstError secondError thirdError : ℚ,
      |firstError| ≤ epsilon ∧
      |secondError| ≤ epsilon ∧
      |thirdError| ≤ epsilon ∧
      |firstError * firstCoefficient +
          secondError * secondCoefficient +
          thirdError * thirdCoefficient| =
        epsilon *
          (|firstCoefficient| +
            |secondCoefficient| + |thirdCoefficient|) := by
  refine ⟨epsilon * rationalDirection firstCoefficient,
    epsilon * rationalDirection secondCoefficient,
    epsilon * rationalDirection thirdCoefficient, ?_, ?_, ?_, ?_⟩
  · rw [abs_mul, abs_of_nonneg epsilonNonnegative,
      abs_rationalDirection, mul_one]
  · rw [abs_mul, abs_of_nonneg epsilonNonnegative,
      abs_rationalDirection, mul_one]
  · rw [abs_mul, abs_of_nonneg epsilonNonnegative,
      abs_rationalDirection, mul_one]
  · have sumIdentity :
        (epsilon * rationalDirection firstCoefficient) * firstCoefficient +
            (epsilon * rationalDirection secondCoefficient) * secondCoefficient +
            (epsilon * rationalDirection thirdCoefficient) * thirdCoefficient =
          epsilon *
            (|firstCoefficient| +
              |secondCoefficient| + |thirdCoefficient|) := by
        rw [mul_assoc epsilon, rationalDirection_mul_self_eq_abs,
          mul_assoc epsilon, rationalDirection_mul_self_eq_abs,
          mul_assoc epsilon, rationalDirection_mul_self_eq_abs]
        rw [mul_add, mul_add]
    have envelopeNonnegative :
        0 ≤ epsilon *
          (|firstCoefficient| +
            |secondCoefficient| + |thirdCoefficient|) :=
      mul_nonneg epsilonNonnegative
        (add_nonneg
          (add_nonneg (abs_nonneg _) (abs_nonneg _))
          (abs_nonneg _))
    rw [sumIdentity, abs_of_nonneg envelopeNonnegative]

/-- The residual-specific noise envelope is itself attainable. -/
theorem threePointResidualErrorEnvelope_is_attainable
    (epsilon firstDefect secondDefect thirdDefect : ℚ)
    (epsilonNonnegative : 0 ≤ epsilon) :
    ∃ firstError secondError thirdError : ℚ,
      |firstError| ≤ epsilon ∧
      |secondError| ≤ epsilon ∧
      |thirdError| ≤ epsilon ∧
      |secondError * (thirdDefect - firstDefect) -
          thirdError * (secondDefect - firstDefect) +
          firstError * (secondDefect - thirdDefect)| =
        threePointResidualErrorEnvelope
          epsilon firstDefect secondDefect thirdDefect := by
  obtain ⟨secondError, thirdError, firstError,
      secondBound, thirdBound, firstBound, attained⟩ :=
    abs_three_term_linear_bound_is_sharp
      (thirdDefect - firstDefect)
      (-(secondDefect - firstDefect))
      (secondDefect - thirdDefect)
      epsilon epsilonNonnegative
  refine ⟨firstError, secondError, thirdError,
    firstBound, secondBound, thirdBound, ?_⟩
  rw [abs_sub_comm secondDefect thirdDefect] at attained
  simpa only [threePointResidualErrorEnvelope, abs_neg,
    mul_neg, sub_eq_add_neg, neg_mul] using attained

/--
If each observed hazard is within `epsilon` of its true value, the induced
three-point curvature error is bounded by the exact `L∞` support-function
envelope

`epsilon * (|d₂-d₀| + |d₁-d₀| + |d₂-d₁|)`.

Unlike a repeated triangle bound, this keeps the shared first-point error only
once and therefore gives the strongest rejection threshold available from the
three coordinatewise error statements alone.
-/
theorem observed_threePointResidual_error_bound
    (firstDefect secondDefect thirdDefect
      trueFirst trueSecond trueThird
      observedFirst observedSecond observedThird epsilon : ℚ)
    (firstError : |observedFirst - trueFirst| ≤ epsilon)
    (secondError : |observedSecond - trueSecond| ≤ epsilon)
    (thirdError : |observedThird - trueThird| ≤ epsilon) :
    |threePointAffineResidual
          firstDefect secondDefect thirdDefect
          observedFirst observedSecond observedThird -
        threePointAffineResidual
          firstDefect secondDefect thirdDefect
          trueFirst trueSecond trueThird| ≤
      threePointResidualErrorEnvelope
        epsilon firstDefect secondDefect thirdDefect := by
  have identity :
      threePointAffineResidual
          firstDefect secondDefect thirdDefect
          observedFirst observedSecond observedThird -
        threePointAffineResidual
          firstDefect secondDefect thirdDefect
          trueFirst trueSecond trueThird =
        (observedSecond - trueSecond) *
            (thirdDefect - firstDefect) -
          (observedThird - trueThird) *
            (secondDefect - firstDefect) +
          (observedFirst - trueFirst) *
            (secondDefect - thirdDefect) := by
    unfold threePointAffineResidual
    ring
  rw [identity]
  have negThirdError :
      |-(observedThird - trueThird)| ≤ epsilon := by
    rw [abs_neg]
    exact thirdError
  have bound := abs_three_term_linear_bound
    (observedSecond - trueSecond)
    (-(observedThird - trueThird))
    (observedFirst - trueFirst)
    (thirdDefect - firstDefect)
    (secondDefect - firstDefect)
    (secondDefect - thirdDefect)
    epsilon secondError negThirdError firstError
  have signIdentity :
      (observedSecond - trueSecond) * (thirdDefect - firstDefect) -
          (observedThird - trueThird) * (secondDefect - firstDefect) +
          (observedFirst - trueFirst) * (secondDefect - thirdDefect) =
        (observedSecond - trueSecond) * (thirdDefect - firstDefect) +
          (-(observedThird - trueThird)) * (secondDefect - firstDefect) +
          (observedFirst - trueFirst) * (secondDefect - thirdDefect) := by
    ring
  rw [signIdentity]
  simpa only [threePointResidualErrorEnvelope,
    abs_neg, abs_sub_comm secondDefect thirdDefect] using bound

/-- For ordered defect levels, the exact envelope is twice the outer span. -/
theorem threePointResidualErrorEnvelope_of_ordered
    (epsilon firstDefect secondDefect thirdDefect : ℚ)
    (firstLeSecond : firstDefect ≤ secondDefect)
    (secondLeThird : secondDefect ≤ thirdDefect) :
    threePointResidualErrorEnvelope
        epsilon firstDefect secondDefect thirdDefect =
      2 * epsilon * (thirdDefect - firstDefect) := by
  unfold threePointResidualErrorEnvelope
  rw [abs_of_nonneg (sub_nonneg.mpr (firstLeSecond.trans secondLeThird)),
    abs_of_nonneg (sub_nonneg.mpr firstLeSecond),
    abs_of_nonneg (sub_nonneg.mpr secondLeThird)]
  ring

/-- The observable predicate used by a preregistered robust affine test. -/
def RobustlyRejectsAffineResponse
    (firstDefect secondDefect thirdDefect
      observedFirst observedSecond observedThird epsilon : ℚ) : Prop :=
  threePointResidualErrorEnvelope
      epsilon firstDefect secondDefect thirdDefect <
    |threePointAffineResidual
      firstDefect secondDefect thirdDefect
      observedFirst observedSecond observedThird|

/--
Positive robust no-go theorem: if the observed residual clears the exact
three-level error envelope, no affine response can lie within `epsilon` of all
three observations.
-/
theorem robust_threePoint_rejection_refutes_every_affine_response
    (firstDefect secondDefect thirdDefect
      observedFirst observedSecond observedThird epsilon : ℚ)
    (rejects : RobustlyRejectsAffineResponse
      firstDefect secondDefect thirdDefect
      observedFirst observedSecond observedThird epsilon) :
    ¬ ∃ baseline sensitivity : ℚ,
      |observedFirst -
          affineDefectResponse baseline sensitivity firstDefect| ≤ epsilon ∧
      |observedSecond -
          affineDefectResponse baseline sensitivity secondDefect| ≤ epsilon ∧
      |observedThird -
          affineDefectResponse baseline sensitivity thirdDefect| ≤ epsilon := by
  rintro ⟨baseline, sensitivity, firstError, secondError, thirdError⟩
  have errorBound := observed_threePointResidual_error_bound
    firstDefect secondDefect thirdDefect
    (affineDefectResponse baseline sensitivity firstDefect)
    (affineDefectResponse baseline sensitivity secondDefect)
    (affineDefectResponse baseline sensitivity thirdDefect)
    observedFirst observedSecond observedThird epsilon
    firstError secondError thirdError
  have trueResidualZero := affine_response_has_zero_threePointResidual
    baseline sensitivity firstDefect secondDefect thirdDefect
  rw [trueResidualZero, sub_zero] at errorBound
  exact (not_lt_of_ge errorBound) rejects

/--
Sharpness witness: changing only the middle observation by `epsilon` produces
residual magnitude exactly `|epsilon| * |thirdDefect-firstDefect|`.  Thus the
test threshold cannot ignore the geometry of the design points.
-/
theorem middle_perturbation_residual_exact
    (baseline sensitivity firstDefect secondDefect thirdDefect epsilon : ℚ) :
    |threePointAffineResidual firstDefect secondDefect thirdDefect
        (affineDefectResponse baseline sensitivity firstDefect)
        (affineDefectResponse baseline sensitivity secondDefect + epsilon)
        (affineDefectResponse baseline sensitivity thirdDefect)| =
      |epsilon| * |thirdDefect - firstDefect| := by
  have residualIdentity :
      threePointAffineResidual firstDefect secondDefect thirdDefect
          (affineDefectResponse baseline sensitivity firstDefect)
          (affineDefectResponse baseline sensitivity secondDefect + epsilon)
          (affineDefectResponse baseline sensitivity thirdDefect) =
        epsilon * (thirdDefect - firstDefect) := by
    unfold threePointAffineResidual affineDefectResponse
    ring
  rw [residualIdentity, abs_mul]

end OCKIndividuationMSpaceComposition
