import OCKIndividuationMSpaceComposition.GeneralizedLeastSquaresNoGo
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-- Information that Fano's inequality requires to identify one of `m`
hypotheses with error at most `error`.  The probabilistic Fano theorem enters
the OC layer through the explicit certificate below; the resource consequences
are proved here without hiding likelihood assumptions. -/
noncomputable def fanoRequiredInformation (m : ℕ) (error : ℝ) : ℝ :=
  (1 - error) * Real.log m - Real.log 2

/-- A likelihood-specific channel certificate separates the Fano premise from
the per-observation information capacity. -/
structure FanoChannelCertificate (hypotheses observations : ℕ) where
  error : ℝ
  totalInformation : ℝ
  perObservationCapacity : ℝ
  fano : fanoRequiredInformation hypotheses error ≤ totalInformation
  capacity : totalInformation ≤ (observations : ℝ) * perObservationCapacity

/-- Positive bridge: a valid Fano/channel certificate yields a total capacity
requirement. -/
theorem fano_requiredInformation_le_observationCapacity
    {hypotheses observations : ℕ}
    (certificate : FanoChannelCertificate hypotheses observations) :
    fanoRequiredInformation hypotheses certificate.error ≤
      (observations : ℝ) * certificate.perObservationCapacity :=
  certificate.fano.trans certificate.capacity

/-- Exact observation lower bound when every observation carries at most a
positive amount of information. -/
theorem fano_observations_lower_bound
    {hypotheses observations : ℕ}
    (certificate : FanoChannelCertificate hypotheses observations)
    (positiveCapacity : 0 < certificate.perObservationCapacity) :
    fanoRequiredInformation hypotheses certificate.error /
        certificate.perObservationCapacity ≤ observations := by
  apply (div_le_iff₀ positiveCapacity).2
  simpa [mul_comm] using
    fano_requiredInformation_le_observationCapacity certificate

/-- No-go form: below the Fano/capacity floor no total-information value can
satisfy both contracts. -/
theorem below_fano_capacity_floor_no_go
    {hypotheses observations : ℕ} (error capacity : ℝ)
    (positiveCapacity : 0 < capacity)
    (tooFew : (observations : ℝ) <
      fanoRequiredInformation hypotheses error / capacity) :
    ¬ ∃ totalInformation : ℝ,
        fanoRequiredInformation hypotheses error ≤ totalInformation ∧
        totalInformation ≤ (observations : ℝ) * capacity := by
  rintro ⟨totalInformation, fano, channel⟩
  have requiredLeCapacity :
      fanoRequiredInformation hypotheses error ≤
        (observations : ℝ) * capacity := fano.trans channel
  have lower : fanoRequiredInformation hypotheses error / capacity ≤ observations := by
    apply (div_le_iff₀ positiveCapacity).2
    simpa [mul_comm] using requiredLeCapacity
  exact (not_le_of_gt tooFew) lower

/-- Pathwise adaptive transcript law.  Even when the next experiment depends
on the realized history, bounded conditional information increments add to at
most `N * capacity`. -/
theorem adaptive_information_accumulation_bound
    {observations : ℕ} {History : Type*}
    (conditionalInformation : Fin observations → History → ℝ)
    (history : Fin observations → History)
    (capacity : ℝ)
    (incrementBound : ∀ i, conditionalInformation i (history i) ≤ capacity) :
    (∑ i, conditionalInformation i (history i)) ≤
      (observations : ℝ) * capacity := by
  calc
    (∑ i, conditionalInformation i (history i)) ≤
        ∑ _i : Fin observations, capacity :=
      Finset.sum_le_sum fun i _ => incrementBound i
    _ = (observations : ℝ) * capacity := by simp

/-- Adaptive Fano lower bound: feedback can redistribute information across
trials but cannot beat a uniform conditional-information ceiling. -/
theorem adaptive_fano_observations_lower_bound
    {hypotheses observations : ℕ} {History : Type*}
    (conditionalInformation : Fin observations → History → ℝ)
    (history : Fin observations → History)
    (error capacity transcriptInformation : ℝ)
    (positiveCapacity : 0 < capacity)
    (fano : fanoRequiredInformation hypotheses error ≤ transcriptInformation)
    (chainRuleBound : transcriptInformation ≤
      ∑ i, conditionalInformation i (history i))
    (incrementBound : ∀ i, conditionalInformation i (history i) ≤ capacity) :
    fanoRequiredInformation hypotheses error / capacity ≤ observations := by
  have totalBound := adaptive_information_accumulation_bound
    conditionalInformation history capacity incrementBound
  have requiredLeCapacity :
      fanoRequiredInformation hypotheses error ≤
        (observations : ℝ) * capacity := fano.trans (chainRuleBound.trans totalBound)
  apply (div_le_iff₀ positiveCapacity).2
  simpa [mul_comm] using requiredLeCapacity

/-- Data processing cannot improve the budget: if a decision is computed from
the transcript, its information requirement is still bounded by transcript
capacity. -/
theorem processed_decision_fano_lower_bound
    {hypotheses observations : ℕ}
    (error capacity decisionInformation transcriptInformation : ℝ)
    (positiveCapacity : 0 < capacity)
    (fano : fanoRequiredInformation hypotheses error ≤ decisionInformation)
    (dataProcessing : decisionInformation ≤ transcriptInformation)
    (transcriptCapacity : transcriptInformation ≤
      (observations : ℝ) * capacity) :
    fanoRequiredInformation hypotheses error / capacity ≤ observations := by
  apply (div_le_iff₀ positiveCapacity).2
  simpa [mul_comm] using fano.trans (dataProcessing.trans transcriptCapacity)

/-- Unknown support among all `s`-subsets produces `choose d s` hypotheses. -/
theorem unknownSupport_fano_lower_bound
    {dimensions supportSize observations : ℕ}
    (certificate :
      FanoChannelCertificate (Nat.choose dimensions supportSize) observations)
    (positiveCapacity : 0 < certificate.perObservationCapacity) :
    fanoRequiredInformation (Nat.choose dimensions supportSize) certificate.error /
        certificate.perObservationCapacity ≤ observations :=
  fano_observations_lower_bound certificate positiveCapacity

end OCKIndividuationMSpaceComposition
