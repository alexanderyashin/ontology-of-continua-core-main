import OCKIndividuationMSpaceComposition.FiniteObservationOracle
import Mathlib.Analysis.SpecialFunctions.Log.Basic

namespace OCKIndividuationMSpaceComposition

/-!
## From finite observation oracles to population-aware learning contracts

The finite cell oracle is a same-block optimum.  This module states the two
additional mathematical facts needed before it can guide a prospective model:

* a sufficient, explicit sample budget for uniform concentration;
* a no-free-lunch result at every genuinely unseen world when the outcome-law
  class is unrestricted.

Together they prevent singleton memorisation from being reported as predictive
power while retaining a constructive route when repeatable cells and a valid
sampling law are supplied.
-/

/-- Closed-form sufficient condition for the finite-hypothesis concentration
certificate used by the empirical design.  The registered hypothesis count
may include every state/class coordinate and every simultaneous model under
the declared family-wise error budget. -/
theorem uniformConcentrationCertificate_of_log_budget
    (sampleSize hypothesisCount : ℕ) (epsilon delta : ℝ)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (hypothesisCountPositive : 0 < hypothesisCount)
    (logBudget :
      Real.log (2 * (hypothesisCount : ℝ) / delta) ≤
        2 * (sampleSize : ℝ) * epsilon ^ 2) :
    UniformConcentrationCertificate
      sampleSize hypothesisCount epsilon delta := by
  refine ⟨epsilonPositive, deltaPositive, ?_⟩
  have countPositive : 0 < (hypothesisCount : ℝ) := by
    exact_mod_cast hypothesisCountPositive
  have scalePositive : 0 < 2 * (hypothesisCount : ℝ) :=
    mul_pos (by norm_num) countPositive
  have ratioPositive :
      0 < 2 * (hypothesisCount : ℝ) / delta :=
    div_pos scalePositive deltaPositive
  have exponentOrder :
      -2 * (sampleSize : ℝ) * epsilon ^ 2 ≤
        -Real.log (2 * (hypothesisCount : ℝ) / delta) := by
    linarith
  have expOrder := Real.exp_le_exp.mpr exponentOrder
  have expNegativeLog :
      Real.exp (-Real.log (2 * (hypothesisCount : ℝ) / delta)) =
        1 / (2 * (hypothesisCount : ℝ) / delta) := by
    rw [Real.exp_neg, Real.exp_log ratioPositive]
    simp [one_div]
  calc
    2 * (hypothesisCount : ℝ) *
        Real.exp (-2 * (sampleSize : ℝ) * epsilon ^ 2) ≤
      2 * (hypothesisCount : ℝ) *
        Real.exp (-Real.log (2 * (hypothesisCount : ℝ) / delta)) := by
          exact mul_le_mul_of_nonneg_left expOrder scalePositive.le
    _ = 2 * (hypothesisCount : ℝ) *
        (1 / (2 * (hypothesisCount : ℝ) / delta)) := by
          rw [expNegativeLog]
    _ = delta := by
      field_simp

/-- If the true best-vs-competitor margin exceeds twice the uniform estimation
error, the empirical ordering is guaranteed to be correct. -/
theorem argmax_pair_stable_of_uniform_error
    {Hypothesis : Type*}
    (trueScore estimatedScore : Hypothesis → ℝ)
    (best competitor : Hypothesis) (epsilon : ℝ)
    (bestError : |estimatedScore best - trueScore best| ≤ epsilon)
    (competitorError :
      |estimatedScore competitor - trueScore competitor| ≤ epsilon)
    (margin : trueScore competitor + 2 * epsilon < trueScore best) :
    estimatedScore competitor < estimatedScore best := by
  have bestLower := (abs_le.mp bestError).1
  have competitorUpper := (abs_le.mp competitorError).2
  linarith

/-- No-free-lunch at an unseen world.  For any learner trained on the frozen
labels, two outcome laws agree on every sampled world and disagree at the
unseen world; the learner must be wrong for at least one of them there. -/
theorem unseen_world_no_learner_guarantees_both_outcome_laws
    {World : Type*} [DecidableEq World] {sampleSize : ℕ}
    (sample : Fin sampleSize → World) (hidden : World)
    (unseen : ∀ index, sample index ≠ hidden)
    (learner : (Fin sampleSize → Bool) → World → Bool) :
    let firstLaw : World → Bool := fun _ => false
    let secondLaw : World → Bool := hiddenFlip hidden
    let observedLabels : Fin sampleSize → Bool :=
      fun index => firstLaw (sample index)
    (∀ index, firstLaw (sample index) = secondLaw (sample index)) ∧
      firstLaw hidden ≠ secondLaw hidden ∧
      (learner observedLabels hidden ≠ firstLaw hidden ∨
        learner observedLabels hidden ≠ secondLaw hidden) := by
  dsimp only
  have indistinguishable :=
    unseen_world_supports_indistinguishable_outcome_laws sample hidden unseen
  refine ⟨indistinguishable.1, indistinguishable.2, ?_⟩
  by_cases predictsFalse : learner (fun _ => false) hidden = false
  · right
    simpa [hiddenFlip, predictsFalse]
  · left
    exact predictsFalse

/-- Positive counterpart to the no-free-lunch result.  Once the observation
is sufficient and the finite design covers every observation fiber, the
covered-sample predictor is exact.  This wrapper exposes the exact pair of
domain obligations that singleton-heavy enterprise data currently fails. -/
theorem sufficient_and_covered_observation_is_exactly_learnable
    {World Observation Outcome : Type*} [Inhabited Outcome]
    {sampleSize : ℕ}
    (observe : World → Observation) (outcome : World → Outcome)
    (sample : Fin sampleSize → World)
    (sufficient : ∀ left right,
      observe left = observe right → outcome left = outcome right)
    (covers : ObservationDesignCovers observe sample) :
    ∀ world,
      coveredSamplePredictor observe outcome sample (observe world) =
        outcome world :=
  covered_sufficient_sample_predictor_is_exact
    observe outcome sample covers sufficient

end OCKIndividuationMSpaceComposition
