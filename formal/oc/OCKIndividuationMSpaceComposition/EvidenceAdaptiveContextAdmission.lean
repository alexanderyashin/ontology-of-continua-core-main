import OCKIndividuationMSpaceComposition.ContextTypingRefinement
import OCKIndividuationMSpaceComposition.ContextRiskDecomposition

namespace OCKIndividuationMSpaceComposition

/-!
# Evidence-adaptive admission of a typed context refinement

Proper-score decomposition, hierarchical shrinkage and model-selection oracle
inequalities are mature prior art.  The OC-specific bridge is an explicit
certificate separating population information gain, finite-sample estimation
penalty and transport penalty.  A child context is admitted only when a valid
lower confidence bound for gain exceeds an upper bound for the total penalty.

The theorem is deliberately estimator-agnostic: Hoeffding, empirical-Bernstein,
e-process, cross-validation or a domain-specific transport audit may supply the
bounds, but none is silently assumed by the continuation semantics.
-/

section

variable {Model : Type*}

/-- A quantitative certificate for admitting a fitted refinement.  `radius`
accounts for uncertainty in the estimated information gain; `penaltyUpper`
must cover both finite-sample estimation and transport error. -/
structure EvidenceAdaptiveAdmissionCertificate
    {risk : Model → ℝ} {baseClass refinedClass : Set Model}
    (localOptimal : OptimalRiskWitness risk baseClass)
    (jointOptimal : OptimalRiskWitness risk refinedClass)
    (fitted : Model) where
  estimatedGain : ℝ
  radius : ℝ
  penaltyUpper : ℝ
  radius_nonnegative : 0 ≤ radius
  gain_lower_valid :
    estimatedGain - radius ≤
      PredictiveInformationGain localOptimal jointOptimal
  penalty_upper_valid :
    PredictiveEstimationPenalty jointOptimal fitted ≤ penaltyUpper
  admission_margin_positive : penaltyUpper < estimatedGain - radius

/-- Positive theorem: a valid evidence-adaptive admission certificate implies
strict improvement over the old optimum. -/
theorem fitted_refinement_beats_local_of_admission_certificate
    (risk : Model → ℝ) (baseClass refinedClass : Set Model)
    (localOptimal : OptimalRiskWitness risk baseClass)
    (jointOptimal : OptimalRiskWitness risk refinedClass)
    (fitted : Model)
    (certificate : EvidenceAdaptiveAdmissionCertificate
      localOptimal jointOptimal fitted) :
    risk fitted < localOptimal.value := by
  rw [fitted_refinement_beats_local_iff_penalty_lt_gain
    risk baseClass refinedClass localOptimal jointOptimal fitted]
  exact lt_of_le_of_lt certificate.penalty_upper_valid
    (lt_of_lt_of_le certificate.admission_margin_positive
      certificate.gain_lower_valid)

/-- The certified margin is a numerical lower bound on the actual
information-gain-minus-penalty advantage. -/
theorem admission_margin_lower_bounds_true_advantage
    (risk : Model → ℝ) (baseClass refinedClass : Set Model)
    (localOptimal : OptimalRiskWitness risk baseClass)
    (jointOptimal : OptimalRiskWitness risk refinedClass)
    (fitted : Model)
    (certificate : EvidenceAdaptiveAdmissionCertificate
      localOptimal jointOptimal fitted) :
    certificate.estimatedGain - certificate.radius - certificate.penaltyUpper ≤
      PredictiveInformationGain localOptimal jointOptimal -
        PredictiveEstimationPenalty jointOptimal fitted := by
  linarith [certificate.gain_lower_valid, certificate.penalty_upper_valid]

/-- A count-dependent penalty clears a positive gain floor exactly under an
explicit sample-size inequality.  This is a parameter-setting rule, not a
claim that count alone establishes the gain floor. -/
theorem inverse_sample_penalty_lt_gain_floor
    (complexity gainFloor sampleSize : ℝ)
    (sampleSizePositive : 0 < sampleSize)
    (sampleSizeSufficient : complexity < gainFloor * sampleSize) :
    complexity / sampleSize < gainFloor := by
  exact (div_lt_iff₀ sampleSizePositive).2 (by
    simpa [mul_comm] using sampleSizeSufficient)

/-- Natural-number form of the operational sample-size rule. -/
theorem inverse_nat_sample_penalty_lt_gain_floor
    (complexity gainFloor : ℝ) (sampleSize : ℕ)
    (sampleSizePositive : 0 < sampleSize)
    (sampleSizeSufficient : complexity < gainFloor * sampleSize) :
    complexity / sampleSize < gainFloor := by
  apply inverse_sample_penalty_lt_gain_floor complexity gainFloor sampleSize
  · exact_mod_cast sampleSizePositive
  · exact sampleSizeSufficient

/-- No-go theorem motivated by the Sepsis replay: for every proposed support
threshold there is a refinement with support meeting that threshold whose
chosen fitted member is nevertheless strictly worse.  Support can control an
estimation bound, but cannot by itself prove positive context information. -/
theorem count_threshold_alone_cannot_guarantee_nonworsening
    (threshold : ℕ) :
    ∃ (support : ℕ), threshold ≤ support ∧
      ∃ (risk : Bool → ℝ) (baseClass refinedClass : Set Bool),
        baseClass ⊆ refinedClass ∧
        ∃ (localOptimal : OptimalRiskWitness risk baseClass)
          (jointOptimal : OptimalRiskWitness risk refinedClass) (fitted : Bool),
          jointOptimal.value = localOptimal.value ∧
          fitted ∈ refinedClass ∧
          localOptimal.value < risk fitted := by
  obtain ⟨risk, baseClass, refinedClass, subset, localOptimal, jointOptimal,
    fitted, equalOptima, fittedAdmissible, reversal⟩ :=
      exists_finite_estimator_reversal_under_refinement
  exact ⟨threshold, le_rfl, risk, baseClass, refinedClass, subset,
    localOptimal, jointOptimal, fitted, equalOptima, fittedAdmissible, reversal⟩

/-- A selector which falls back to the base predictor when certification
fails is never worse than the base whenever every admitted branch carries a
valid non-worsening proof. -/
def evidenceAdaptivePredictor
    (admit : Bool) (base fitted : Model) : Model :=
  if admit then fitted else base

theorem evidenceAdaptivePredictor_nonworse
    (risk : Model → ℝ) (admit : Bool) (base fitted : Model)
    (admittedSafe : admit = true → risk fitted ≤ risk base) :
    risk (evidenceAdaptivePredictor admit base fitted) ≤ risk base := by
  cases admit <;> simp [evidenceAdaptivePredictor, admittedSafe]

end

end OCKIndividuationMSpaceComposition
