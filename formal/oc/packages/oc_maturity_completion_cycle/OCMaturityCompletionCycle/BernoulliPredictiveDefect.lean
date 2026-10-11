import Mathlib.Algebra.Order.Ring.Abs
import OCMaturityCompletionCycle.EmpiricalCouplingPredictionR2
import OCMaturityCompletionCycle.FiniteProbabilityTV

/-!
# Exact Bernoulli predictive-defect bridge

This file contains only population identities over exact rational
probabilities.  It makes no claim that a fitted probability is consistent for
the population parameter.
-/

namespace OCMaturityCompletionCycle

/-- Exact finite Bernoulli law on `Bool`, with `true` probability `p`. -/
def finiteBernoulliProbabilityR2
    (p : ℚ)
    (probability : IsProbabilityR2 p) : FiniteProbabilityMass Bool where
  mass
    | false => 1 - p
    | true => p
  nonnegative
    | false => sub_nonneg.mpr probability.2
    | true => probability.1
  normalized := by simp

/-- Every normalized finite Boolean law has a valid `true` parameter. -/
theorem finiteBoolTrueMass_isProbabilityR2
    (law : FiniteProbabilityMass Bool) : IsProbabilityR2 (law.mass true) := by
  constructor
  · exact law.nonnegative true
  · calc
      law.mass true ≤ law.mass false + law.mass true := by
        exact le_add_of_nonneg_left (law.nonnegative false)
      _ = 1 := by simpa [Fintype.sum_bool, add_comm] using law.normalized

/-- Every finite Boolean probability is exactly its Bernoulli parameterization. -/
theorem finiteBoolProbability_mass_eq_bernoulliR2
    (law : FiniteProbabilityMass Bool) :
    law.mass =
      (finiteBernoulliProbabilityR2 (law.mass true)
        (finiteBoolTrueMass_isProbabilityR2 law)).mass := by
  funext outcome
  cases outcome
  · change law.mass false = 1 - law.mass true
    calc
      law.mass false =
          (law.mass false + law.mass true) - law.mass true := by ring
      _ = 1 - law.mass true := by
        rw [show law.mass false + law.mass true = 1 by
          simpa [Fintype.sum_bool, add_comm] using law.normalized]
  · rfl

/-- Total variation of exact finite Bernoulli laws is parameter distance. -/
theorem finiteBernoulliTotalVariationR2_eq_abs_sub
    (p q : ℚ)
    (pProbability : IsProbabilityR2 p)
    (qProbability : IsProbabilityR2 q) :
    finiteTotalVariation
        (finiteBernoulliProbabilityR2 p pProbability)
        (finiteBernoulliProbabilityR2 q qProbability) = |p - q| := by
  simp only [finiteTotalVariation, Fintype.sum_bool,
    finiteBernoulliProbabilityR2]
  have complementDifference : 1 - p - (1 - q) = -(p - q) := by ring
  rw [complementDifference, abs_neg]
  ring

/-- TV of arbitrary normalized Boolean laws is their `true`-mass distance. -/
theorem finiteBoolTotalVariation_eq_abs_trueMass
    (left right : FiniteProbabilityMass Bool) :
    finiteTotalVariation left right = |left.mass true - right.mass true| := by
  simp only [finiteTotalVariation]
  conv_lhs =>
    rw [finiteBoolProbability_mass_eq_bernoulliR2 left,
      finiteBoolProbability_mass_eq_bernoulliR2 right]
  simpa only [finiteTotalVariation] using
    (finiteBernoulliTotalVariationR2_eq_abs_sub
      (left.mass true) (right.mass true)
      (finiteBoolTrueMass_isProbabilityR2 left)
      (finiteBoolTrueMass_isProbabilityR2 right))

/-- Bayes Brier excess of report `q` under truth `p` is `(p-q)^2`. -/
theorem bernoulliBayesBrierExcessR2_eq_sq_sub
    (p q : ℚ) :
    BernoulliBrierRiskR2 p q - BernoulliBrierRiskR2 p p = (p - q) ^ 2 := by
  rw [bernoulliBrierRiskR2_decomposition]
  ring

/--
Exact bridge used by the empirical adapter: population Bayes Brier excess is
the square of the finite Bernoulli predictive TV defect.
-/
theorem bernoulliBayesBrierExcessR2_eq_totalVariation_sq
    (p q : ℚ)
    (pProbability : IsProbabilityR2 p)
    (qProbability : IsProbabilityR2 q) :
    BernoulliBrierRiskR2 p q - BernoulliBrierRiskR2 p p =
      (finiteTotalVariation
        (finiteBernoulliProbabilityR2 p pProbability)
        (finiteBernoulliProbabilityR2 q qProbability)) ^ 2 := by
  rw [bernoulliBayesBrierExcessR2_eq_sq_sub,
    finiteBernoulliTotalVariationR2_eq_abs_sub, sq_abs (p - q)]

/-- A finite family of Bernoulli population truths and reports. -/
structure FiniteBernoulliPredictionFamily
    (Stratum : Type*)
    [Fintype Stratum] where
  weight : FiniteProbabilityMass Stratum
  truth : Stratum → ℚ
  report : Stratum → ℚ
  truth_probability : ∀ stratum, IsProbabilityR2 (truth stratum)
  report_probability : ∀ stratum, IsProbabilityR2 (report stratum)

/-- Weighted population Brier excess over an arbitrary finite stratum set. -/
def finiteStratifiedBrierExcessR2
    {Stratum : Type*}
    [Fintype Stratum]
    (family : FiniteBernoulliPredictionFamily Stratum) : ℚ :=
  ∑ stratum,
    family.weight.mass stratum *
      (BernoulliBrierRiskR2 (family.truth stratum) (family.report stratum) -
        BernoulliBrierRiskR2 (family.truth stratum) (family.truth stratum))

/-- Weighted squared-TV population defect over the same finite strata. -/
def finiteStratifiedBernoulliTVSquaredR2
    {Stratum : Type*}
    [Fintype Stratum]
    (family : FiniteBernoulliPredictionFamily Stratum) : ℚ :=
  ∑ stratum,
    family.weight.mass stratum *
      (finiteTotalVariation
        (finiteBernoulliProbabilityR2 (family.truth stratum)
          (family.truth_probability stratum))
        (finiteBernoulliProbabilityR2 (family.report stratum)
          (family.report_probability stratum))) ^ 2

/-- Multi-stratum Brier decomposition into the weighted squared TV defect. -/
theorem finiteStratifiedBrierExcessR2_eq_weighted_tvSquared
    {Stratum : Type*}
    [Fintype Stratum]
    (family : FiniteBernoulliPredictionFamily Stratum) :
    finiteStratifiedBrierExcessR2 family =
      finiteStratifiedBernoulliTVSquaredR2 family := by
  apply Finset.sum_congr rfl
  intro stratum _
  rw [bernoulliBayesBrierExcessR2_eq_totalVariation_sq]

/--
Training-only finite plug-in contract for the shared cross-domain prediction
defect.  `HistoryIndex` denotes a causal pre-event history row or a frozen
history stratum.  The record stores fitted probabilities, not population truth.
-/
structure TrainingOnlyBernoulliPredictivePlugin
    (Group : Type*)
    (HistoryIndex : Type*)
    [Fintype Group]
    [Fintype HistoryIndex] where
  eligible : Group → HistoryIndex → Bool
  historyWeight : Group → FiniteProbabilityMass HistoryIndex
  fineProbability : Group → HistoryIndex → ℚ
  abstractProbability : Group → HistoryIndex → ℚ
  fine_is_probability : ∀ group history,
    IsProbabilityR2 (fineProbability group history)
  abstract_is_probability : ∀ group history,
    IsProbabilityR2 (abstractProbability group history)
  eligible_weight_normalized : ∀ group,
    (∑ history,
      if eligible group history then (historyWeight group).mass history else 0) = 1
  trainingCutDigest : String
  fineEstimatorId : String
  abstractEstimatorId : String

/--
Fitted row disagreement `|hat p_fine - hat p_abs|`.  Cross-fitting and split
integrity are external preregistration evidence, not inferred from this record.
-/
def trainingBernoulliRowPredictionDefect
    {Group HistoryIndex : Type*}
    [Fintype Group]
    [Fintype HistoryIndex]
    (estimate : TrainingOnlyBernoulliPredictivePlugin Group HistoryIndex)
    (group : Group)
    (history : HistoryIndex) : ℚ :=
  |estimate.fineProbability group history -
    estimate.abstractProbability group history|

/--
Weighted mean absolute fitted-law disagreement.  This is an optional TV-scale
diagnostic, not the squared Brier-scale proxy frozen by the cross-domain v2
preregistration.
-/
def trainingBernoulliGroupPredictionDefect
    {Group HistoryIndex : Type*}
    [Fintype Group]
    [Fintype HistoryIndex]
    (estimate : TrainingOnlyBernoulliPredictivePlugin Group HistoryIndex)
    (group : Group) : ℚ :=
  ∑ history,
    if estimate.eligible group history then
      (estimate.historyWeight group).mass history *
        trainingBernoulliRowPredictionDefect estimate group history
    else 0

/--
Frozen group proxy on the Brier scale: the eligible-row weighted mean of
`(hat p_fine - hat p_abstract)^2`.
-/
def trainingBernoulliGroupSquaredPredictionDefect
    {Group HistoryIndex : Type*}
    [Fintype Group]
    [Fintype HistoryIndex]
    (estimate : TrainingOnlyBernoulliPredictivePlugin Group HistoryIndex)
    (group : Group) : ℚ :=
  ∑ history,
    if estimate.eligible group history then
      (estimate.historyWeight group).mass history *
        (trainingBernoulliRowPredictionDefect estimate group history) ^ 2
    else 0

/--
Model-relative Brier contrast that treats `hat p_fine` as the reference law.
It is not empirical risk under the unknown outcome law and is not a population
Bayes excess unless a separate identification result establishes
`hat p_fine = p_H`.
-/
def trainingBernoulliGroupPluginReferenceBrierExcess
    {Group HistoryIndex : Type*}
    [Fintype Group]
    [Fintype HistoryIndex]
    (estimate : TrainingOnlyBernoulliPredictivePlugin Group HistoryIndex)
    (group : Group) : ℚ :=
  ∑ history,
    if estimate.eligible group history then
      (estimate.historyWeight group).mass history *
        (BernoulliBrierRiskR2 (estimate.fineProbability group history)
            (estimate.abstractProbability group history) -
          BernoulliBrierRiskR2 (estimate.fineProbability group history)
            (estimate.fineProbability group history))
    else 0

/-- The row plug-in value is exactly TV between the two fitted Bernoulli laws. -/
theorem trainingBernoulliRowPredictionDefect_eq_fitted_tv
    {Group HistoryIndex : Type*}
    [Fintype Group]
    [Fintype HistoryIndex]
    (estimate : TrainingOnlyBernoulliPredictivePlugin Group HistoryIndex)
    (group : Group)
    (history : HistoryIndex) :
    trainingBernoulliRowPredictionDefect estimate group history =
      finiteTotalVariation
        (finiteBernoulliProbabilityR2
          (estimate.fineProbability group history)
          (estimate.fine_is_probability group history))
        (finiteBernoulliProbabilityR2
          (estimate.abstractProbability group history)
          (estimate.abstract_is_probability group history)) := by
  rw [finiteBernoulliTotalVariationR2_eq_abs_sub]
  rfl

/-- Squared fitted disagreement equals the plug-in-reference Brier contrast. -/
theorem trainingBernoulliRowPredictionDefect_sq_eq_pluginReferenceBrierExcess
    {Group HistoryIndex : Type*}
    [Fintype Group]
    [Fintype HistoryIndex]
    (estimate : TrainingOnlyBernoulliPredictivePlugin Group HistoryIndex)
    (group : Group)
    (history : HistoryIndex) :
    (trainingBernoulliRowPredictionDefect estimate group history) ^ 2 =
      BernoulliBrierRiskR2 (estimate.fineProbability group history)
          (estimate.abstractProbability group history) -
        BernoulliBrierRiskR2 (estimate.fineProbability group history)
          (estimate.fineProbability group history) := by
  rw [trainingBernoulliRowPredictionDefect_eq_fitted_tv]
  exact (bernoulliBayesBrierExcessR2_eq_totalVariation_sq
    (estimate.fineProbability group history)
    (estimate.abstractProbability group history)
    (estimate.fine_is_probability group history)
    (estimate.abstract_is_probability group history)).symm

/--
Exact group-level algebra used by the frozen v2 proxy.  The name deliberately
says `pluginReference`: no statistical identification is hidden in the theorem.
-/
theorem pluginReferenceBrierExcess_eq_squaredDisagreement
    {Group HistoryIndex : Type*}
    [Fintype Group]
    [Fintype HistoryIndex]
    (estimate : TrainingOnlyBernoulliPredictivePlugin Group HistoryIndex)
    (group : Group) :
    trainingBernoulliGroupPluginReferenceBrierExcess estimate group =
      trainingBernoulliGroupSquaredPredictionDefect estimate group := by
  simp only [trainingBernoulliGroupPluginReferenceBrierExcess,
    trainingBernoulliGroupSquaredPredictionDefect]
  apply Finset.sum_congr rfl
  intro history _
  by_cases eligible : estimate.eligible group history
  · simp only [eligible, if_true]
    rw [trainingBernoulliRowPredictionDefect_sq_eq_pluginReferenceBrierExcess]
  · simp [eligible]

/-- No population-consistency statement follows from the plug-in constructor. -/
def StrongPairwiseTrainingBernoulliDefectRanksHeldOutBrier
    {Group HistoryIndex : Type*}
    [Fintype Group]
    [Fintype HistoryIndex]
    (estimate : TrainingOnlyBernoulliPredictivePlugin Group HistoryIndex)
    (heldOutBrierExcess : Group → ℚ) : Prop :=
  ∀ left right,
    trainingBernoulliGroupSquaredPredictionDefect estimate left <
        trainingBernoulliGroupSquaredPredictionDefect estimate right →
      heldOutBrierExcess left ≤ heldOutBrierExcess right

end OCMaturityCompletionCycle
