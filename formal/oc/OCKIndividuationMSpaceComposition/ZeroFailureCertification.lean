import OCKIndividuationMSpaceComposition.MeasureChannelIdentifiability

namespace OCKIndividuationMSpaceComposition

/-! ## Finite evidence required to certify a rare failure rate

This layer separates a conditional model theorem from the finite empirical
evidence needed to certify that its operational preconditions are met often
enough.  Within each endpoint, the formula assumes independent Bernoulli
opportunities with a common failure rate.  Across endpoints it uses only a
union bound, not independence.
-/

/-- Bonferroni/union-bound probability of seeing zero failures in every one of
`endpoints` tests when the boundary failure rate is `failureRate`. -/
noncomputable def zeroFailureFamilywiseBound
    (endpoints : ℕ) (failureRate : ℝ) (trialsPerEndpoint : ℕ) : ℝ :=
  (endpoints : ℝ) * (1 - failureRate) ^ trialsPerEndpoint

/-- A finite zero-failure design certifies a boundary rate when its familywise
false-certification bound is below the declared error budget. -/
def ZeroFailureCertifies
    (endpoints : ℕ) (failureRate familywiseAlpha : ℝ)
    (trialsPerEndpoint : ℕ) : Prop :=
  zeroFailureFamilywiseBound endpoints failureRate trialsPerEndpoint ≤
    familywiseAlpha

/-- Additional trials multiply the false-certification bound by the remaining
zero-failure probability over the added block. -/
theorem zeroFailureFamilywiseBound_add_trials
    (endpoints trials additional : ℕ) (failureRate : ℝ) :
    zeroFailureFamilywiseBound endpoints failureRate (trials + additional) =
      zeroFailureFamilywiseBound endpoints failureRate trials *
        (1 - failureRate) ^ additional := by
  simp [zeroFailureFamilywiseBound, pow_add]
  ring

/-- More independent trials cannot worsen the certification bound for a valid
failure probability. -/
theorem zeroFailureFamilywiseBound_antitone_trials
    (endpoints firstTrials secondTrials : ℕ) (failureRate : ℝ)
    (failureRateNonnegative : 0 ≤ failureRate)
    (failureRateAtMostOne : failureRate ≤ 1)
    (moreTrials : firstTrials ≤ secondTrials) :
    zeroFailureFamilywiseBound endpoints failureRate secondTrials ≤
      zeroFailureFamilywiseBound endpoints failureRate firstTrials := by
  unfold zeroFailureFamilywiseBound
  apply mul_le_mul_of_nonneg_left
  · exact pow_le_pow_of_le_one
      (sub_nonneg.mpr failureRateAtMostOne)
      (sub_le_self 1 failureRateNonnegative) moreTrials
  · positivity

/-- Once a zero-failure design certifies a rate, collecting more independent
trials preserves the certificate. -/
theorem zeroFailureCertification_preserved_by_more_trials
    (endpoints firstTrials secondTrials : ℕ)
    (failureRate familywiseAlpha : ℝ)
    (failureRateNonnegative : 0 ≤ failureRate)
    (failureRateAtMostOne : failureRate ≤ 1)
    (moreTrials : firstTrials ≤ secondTrials)
    (certified : ZeroFailureCertifies endpoints failureRate familywiseAlpha firstTrials) :
    ZeroFailureCertifies endpoints failureRate familywiseAlpha secondTrials := by
  exact (zeroFailureFamilywiseBound_antitone_trials endpoints firstTrials secondTrials
    failureRate failureRateNonnegative failureRateAtMostOne moreTrials).trans certified

/-- At a strictly positive boundary failure rate below one, every finite
zero-failure experiment retains strictly positive false-certification risk. -/
theorem finite_zero_failure_evidence_never_eliminates_risk
    (endpoints trials : ℕ) (failureRate : ℝ)
    (positiveEndpoints : 0 < endpoints)
    (failureRateBelowOne : failureRate < 1) :
    0 < zeroFailureFamilywiseBound endpoints failureRate trials := by
  unfold zeroFailureFamilywiseBound
  exact mul_pos (by exact_mod_cast positiveEndpoints)
    (pow_pos (sub_pos.mpr failureRateBelowOne) _)

/-- No-go: if the boundary failure rate is zero, more zero-failure observations
carry no evidence against that boundary; the bound remains the endpoint count. -/
theorem zero_boundary_rate_is_not_learned_from_zero_failures
    (endpoints trials : ℕ) :
    zeroFailureFamilywiseBound endpoints 0 trials = endpoints := by
  simp [zeroFailureFamilywiseBound]

/-- Therefore a nontrivial familywise budget below the endpoint count cannot
certify a zero boundary failure rate from any finite all-success sample. -/
theorem zero_boundary_rate_cannot_be_certified
    (endpoints trials : ℕ) (familywiseAlpha : ℝ)
    (budgetBelowEndpoints : familywiseAlpha < endpoints) :
    ¬ ZeroFailureCertifies endpoints 0 familywiseAlpha trials := by
  intro certified
  unfold ZeroFailureCertifies at certified
  rw [zero_boundary_rate_is_not_learned_from_zero_failures] at certified
  exact (not_le_of_gt budgetBelowEndpoints) certified

end OCKIndividuationMSpaceComposition
