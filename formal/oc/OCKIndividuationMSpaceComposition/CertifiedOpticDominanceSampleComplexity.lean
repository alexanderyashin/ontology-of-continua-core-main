import OCKIndividuationMSpaceComposition.CertifiedOpticRiskIntervals
import OCKIndividuationMSpaceComposition.StochasticForecastSampleComplexity

namespace OCKIndividuationMSpaceComposition

/-!
# Sample complexity for resolving an optic comparison

For two point estimates separated by a positive centre gap, strict interval
dominance appears when the sum of their confidence radii is below that gap.
With inverse-square-root radii, this yields an explicit independent-equivalent
count threshold.  The theorem is a planning law conditional on the registered
centres and radius coefficients; centre drift remains a prospective falsifier.
-/

/-- Symmetric inverse-square-root confidence radius. -/
noncomputable def inverseSqrtRiskRadius
    (coefficient observations : ℝ) : ℝ :=
  coefficient / Real.sqrt observations

/-- Independent-equivalent count at which two inverse-square-root radii can
fit inside a positive centre gap. -/
noncomputable def dominanceRequiredIndependentCount
    (leftCoefficient rightCoefficient centreGap : ℝ) : ℝ :=
  ((leftCoefficient + rightCoefficient) / centreGap) ^ 2

/-- The explicit count threshold makes the sum of both radii strictly smaller
than the registered positive centre gap. -/
theorem dominance_sample_threshold_makes_pair_radii_smaller_than_gap
    (leftCoefficient rightCoefficient centreGap observations : ℝ)
    (leftNonnegative : 0 ≤ leftCoefficient)
    (rightNonnegative : 0 ≤ rightCoefficient)
    (gapPositive : 0 < centreGap)
    (observationsPositive : 0 < observations)
    (enough :
      dominanceRequiredIndependentCount
          leftCoefficient rightCoefficient centreGap < observations) :
    inverseSqrtRiskRadius leftCoefficient observations +
        inverseSqrtRiskRadius rightCoefficient observations < centreGap := by
  let total := leftCoefficient + rightCoefficient
  let normalized := total / centreGap
  have totalNonnegative : 0 ≤ total := add_nonneg leftNonnegative rightNonnegative
  have normalizedNonnegative : 0 ≤ normalized :=
    div_nonneg totalNonnegative gapPositive.le
  have sqrtPositive : 0 < Real.sqrt observations := Real.sqrt_pos.2 observationsPositive
  have sqrtSquare : (Real.sqrt observations) ^ 2 = observations :=
    Real.sq_sqrt observationsPositive.le
  have normalizedSquare : normalized ^ 2 < observations := by
    simpa [dominanceRequiredIndependentCount, normalized, total] using enough
  have normalizedBelowSqrt : normalized < Real.sqrt observations := by
    nlinarith
  have totalIdentity : normalized * centreGap = total := by
    dsimp [normalized]
    field_simp
  have totalBelow : total < Real.sqrt observations * centreGap := by
    nlinarith
  unfold inverseSqrtRiskRadius
  rw [← add_div]
  dsimp [total] at totalBelow ⊢
  exact (div_lt_iff₀ sqrtPositive).2 (by simpa [mul_comm] using totalBelow)

/-- End-to-end interval separation: after the threshold, the left symmetric
upper endpoint lies below the right symmetric lower endpoint. -/
theorem dominance_sample_threshold_certifies_interval_separation
    (leftCentre rightCentre leftCoefficient rightCoefficient observations : ℝ)
    (leftNonnegative : 0 ≤ leftCoefficient)
    (rightNonnegative : 0 ≤ rightCoefficient)
    (centreGapPositive : 0 < rightCentre - leftCentre)
    (observationsPositive : 0 < observations)
    (enough :
      dominanceRequiredIndependentCount leftCoefficient rightCoefficient
          (rightCentre - leftCentre) < observations) :
    leftCentre + inverseSqrtRiskRadius leftCoefficient observations <
      rightCentre - inverseSqrtRiskRadius rightCoefficient observations := by
  have radiiBelow := dominance_sample_threshold_makes_pair_radii_smaller_than_gap
    leftCoefficient rightCoefficient (rightCentre - leftCentre) observations
    leftNonnegative rightNonnegative centreGapPositive observationsPositive enough
  linarith

/-- A bounded design effect converts the independent-equivalent dominance
threshold into a raw trace threshold. -/
theorem designEffect_raw_threshold_certifies_interval_separation
    (leftCentre rightCentre leftCoefficient rightCoefficient raw designEffect : ℝ)
    (leftNonnegative : 0 ≤ leftCoefficient)
    (rightNonnegative : 0 ≤ rightCoefficient)
    (centreGapPositive : 0 < rightCentre - leftCentre)
    (designEffectPositive : 0 < designEffect)
    (enoughRaw :
      designEffect * dominanceRequiredIndependentCount
          leftCoefficient rightCoefficient (rightCentre - leftCentre) < raw) :
    leftCentre + inverseSqrtRiskRadius leftCoefficient
        (designEffectEffectiveObservations raw designEffect) <
      rightCentre - inverseSqrtRiskRadius rightCoefficient
        (designEffectEffectiveObservations raw designEffect) := by
  have requiredNonnegative : 0 ≤ dominanceRequiredIndependentCount
      leftCoefficient rightCoefficient (rightCentre - leftCentre) := by
    exact sq_nonneg _
  have rawPositive : 0 < raw := by
    have productNonnegative :
        0 ≤ designEffect * dominanceRequiredIndependentCount
          leftCoefficient rightCoefficient (rightCentre - leftCentre) :=
      mul_nonneg designEffectPositive.le requiredNonnegative
    linarith
  apply dominance_sample_threshold_certifies_interval_separation
    leftCentre rightCentre leftCoefficient rightCoefficient
    (designEffectEffectiveObservations raw designEffect)
    leftNonnegative rightNonnegative centreGapPositive
  · exact div_pos rawPositive designEffectPositive
  · rw [designEffectEffectiveObservations]
    exact (lt_div_iff₀ designEffectPositive).2
      (by simpa [mul_comm] using enoughRaw)

/-- No-go at zero or reversed centre gap: nonnegative symmetric radii cannot
certify the left interval strictly below the right interval. -/
theorem nonpositive_centre_gap_blocks_left_dominance
    (leftCentre rightCentre leftRadius rightRadius : ℝ)
    (gapNonpositive : rightCentre - leftCentre ≤ 0)
    (leftRadiusNonnegative : 0 ≤ leftRadius)
    (rightRadiusNonnegative : 0 ≤ rightRadius) :
    ¬ leftCentre + leftRadius < rightCentre - rightRadius := by
  intro claimed
  linarith

/-- Exact fourfold law: reducing an inverse-square-root radius by one half
requires multiplying the independent-equivalent count by four. -/
theorem inverseSqrtRiskRadius_fourfold_count_halves
    (coefficient observations : ℝ) :
    inverseSqrtRiskRadius coefficient (4 * observations) =
      inverseSqrtRiskRadius coefficient observations / 2 := by
  unfold inverseSqrtRiskRadius
  rw [Real.sqrt_mul (by norm_num : 0 ≤ (4 : ℝ)) observations]
  have sqrtFour : Real.sqrt (4 : ℝ) = 2 := by
    calc
      Real.sqrt (4 : ℝ) = Real.sqrt ((2 : ℝ) ^ 2) := by norm_num
      _ = 2 := Real.sqrt_sq (by norm_num)
  rw [sqrtFour]
  ring

end OCKIndividuationMSpaceComposition
