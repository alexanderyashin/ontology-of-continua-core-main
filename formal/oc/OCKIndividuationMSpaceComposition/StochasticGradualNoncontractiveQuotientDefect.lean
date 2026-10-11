import OCKIndividuationMSpaceComposition.StochasticNoncontractiveQuotientDefect
import OCKIndividuationMSpaceComposition.GovernanceBarrierHazard
import Mathlib.Algebra.Order.Archimedean.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

/-!
# Exact gradual loss at the noncontractive quotient boundary

The sharp one-step countermodel is generalized to every rational structural
defect `p` in `[0,1]`.  The hidden fine state leaks to an absorbing visible
state with probability `p` at every step, whereas the selected representative
remains in the original optic cell.  The representative quotient is therefore
the identity kernel and is only nonexpansive (`rho = 1`).

The actual transported prediction error at horizon `h` is proved exactly:

`TV_h = 1 - (1 - p)^h`.

Thus even an arbitrarily small positive local quotient defect accumulates
according to a geometric law.  A proposed finite-horizon threshold is
falsified exactly when the displayed rational expression exceeds it.  No
asymptotic or floating-point argument is used.
-/

/-- A three-state Markov kernel with a gradual hidden-to-visible leak. -/
def gradualNoncontractiveKernel
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1) :
    FiniteControlledKernel NoncontractiveQuotientFineState Unit where
  mass state _ target :=
    match state, target with
    | NoncontractiveQuotientFineState.representative,
        NoncontractiveQuotientFineState.representative => 1
    | NoncontractiveQuotientFineState.hidden,
        NoncontractiveQuotientFineState.hidden => 1 - p
    | NoncontractiveQuotientFineState.hidden,
        NoncontractiveQuotientFineState.absorbed => p
    | NoncontractiveQuotientFineState.absorbed,
        NoncontractiveQuotientFineState.absorbed => 1
    | _, _ => 0
  nonnegative state action target := by
    cases state <;> cases target <;> simp_all
  normalized state action := by
    cases state <;>
      simp [noncontractiveQuotientFineState_univ]

def gradualNoncontractiveFineSequence
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1) :
    Nat → FiniteControlledKernel NoncontractiveQuotientFineState Unit :=
  fun _ => gradualNoncontractiveKernel p pNonnegative pAtMostOne

def gradualNoncontractiveRepresentativeKernel
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1) :
    FiniteControlledKernel Bool Unit :=
  representativeQuotientKernel
    (gradualNoncontractiveKernel p pNonnegative pAtMostOne)
    noncontractiveQuotientEncode noncontractiveQuotientRepresentative

def gradualNoncontractiveAbstractSequence
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1) :
    Nat → FiniteControlledKernel Bool Unit :=
  fun _ => gradualNoncontractiveRepresentativeKernel
    p pNonnegative pAtMostOne

/-- The selected representative quotient is the identity transition. -/
theorem gradualRepresentativeKernel_mass_eq_dirac
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1)
    (source target : Bool) :
    (gradualNoncontractiveRepresentativeKernel
      p pNonnegative pAtMostOne).mass source () target =
      if target = source then 1 else 0 := by
  cases source <;> cases target <;>
    simp [gradualNoncontractiveRepresentativeKernel,
      representativeQuotientKernel, pushedKernelRowProbability,
      pushforwardFiniteProbability, kernelRowProbability,
      gradualNoncontractiveKernel, noncontractiveQuotientEncode,
      noncontractiveQuotientRepresentative,
      noncontractiveQuotientFineState_univ]

/-- Exact survival mass of the unresolved hidden fine state. -/
theorem gradual_hidden_mass_exact
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1) :
    ∀ horizon,
      (evolveMany
        (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
        noncontractiveActionSequence horizon noncontractiveHiddenInitial).mass
          NoncontractiveQuotientFineState.hidden = (1 - p) ^ horizon := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, noncontractiveHiddenInitial, finiteDirac]
  | succ horizon inductionHypothesis =>
      simp [evolveMany, evolveFiniteProbability,
        gradualNoncontractiveFineSequence, gradualNoncontractiveKernel,
        noncontractiveQuotientFineState_univ, inductionHypothesis,
        pow_succ]

/-- The representative state is unreachable from the hidden initial law. -/
theorem gradual_representative_mass_zero
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1) :
    ∀ horizon,
      (evolveMany
        (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
        noncontractiveActionSequence horizon noncontractiveHiddenInitial).mass
          NoncontractiveQuotientFineState.representative = 0 := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, noncontractiveHiddenInitial, finiteDirac]
  | succ horizon inductionHypothesis =>
      simp [evolveMany, evolveFiniteProbability,
        gradualNoncontractiveFineSequence, gradualNoncontractiveKernel,
        noncontractiveQuotientFineState_univ, inductionHypothesis]

/-- Exact cumulative mass that has escaped to the visible absorbing cell. -/
theorem gradual_absorbed_mass_exact
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1) :
    ∀ horizon,
      (evolveMany
        (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
        noncontractiveActionSequence horizon noncontractiveHiddenInitial).mass
          NoncontractiveQuotientFineState.absorbed =
        1 - (1 - p) ^ horizon := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, noncontractiveHiddenInitial, finiteDirac]
  | succ horizon inductionHypothesis =>
      simp [evolveMany, evolveFiniteProbability,
        gradualNoncontractiveFineSequence, gradualNoncontractiveKernel,
        noncontractiveQuotientFineState_univ,
        gradual_hidden_mass_exact p pNonnegative pAtMostOne horizon,
        inductionHypothesis, pow_succ]
      ring

/-- The abstract representative process remains concentrated in `false`. -/
theorem gradual_abstract_false_mass_one
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1) :
    ∀ horizon,
      (evolveMany
        (gradualNoncontractiveAbstractSequence p pNonnegative pAtMostOne)
        noncontractiveActionSequence horizon
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          noncontractiveHiddenInitial)).mass false = 1 := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, pushforwardFiniteProbability,
        noncontractiveHiddenInitial, finiteDirac,
        noncontractiveQuotientEncode,
        noncontractiveQuotientFineState_univ]
  | succ horizon inductionHypothesis =>
      simp [evolveMany, evolveFiniteProbability,
        gradualNoncontractiveAbstractSequence,
        noncontractiveActionSequence,
        gradualRepresentativeKernel_mass_eq_dirac,
        inductionHypothesis]

/-- The abstract representative process assigns zero mass to `true`. -/
theorem gradual_abstract_true_mass_zero
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1) :
    ∀ horizon,
      (evolveMany
        (gradualNoncontractiveAbstractSequence p pNonnegative pAtMostOne)
        noncontractiveActionSequence horizon
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          noncontractiveHiddenInitial)).mass true = 0 := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, pushforwardFiniteProbability,
        noncontractiveHiddenInitial, finiteDirac,
        noncontractiveQuotientEncode,
        noncontractiveQuotientFineState_univ]
  | succ horizon inductionHypothesis =>
      simp [evolveMany, evolveFiniteProbability,
        gradualNoncontractiveAbstractSequence,
        noncontractiveActionSequence,
        gradualRepresentativeKernel_mass_eq_dirac,
        inductionHypothesis]

/-- The local same-cell row defect is exactly the leak probability `p`. -/
theorem gradual_same_cell_row_tv_exact
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1) :
    sameCellRowTV
      (gradualNoncontractiveKernel p pNonnegative pAtMostOne)
      noncontractiveQuotientEncode
      NoncontractiveQuotientFineState.hidden
      NoncontractiveQuotientFineState.representative () = p := by
  simp [sameCellRowTV, finiteTotalVariation,
    pushedKernelRowProbability, pushforwardFiniteProbability,
    kernelRowProbability, gradualNoncontractiveKernel,
    noncontractiveQuotientEncode,
    noncontractiveQuotientFineState_univ,
    abs_of_nonneg pNonnegative]

/-- Exact actual transported-law error at every finite horizon. -/
theorem gradual_noncontractive_tv_exact
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1)
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany
            (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
            noncontractiveActionSequence horizon
            noncontractiveHiddenInitial))
        (evolveMany
          (gradualNoncontractiveAbstractSequence p pNonnegative pAtMostOne)
          noncontractiveActionSequence horizon
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) =
      1 - (1 - p) ^ horizon := by
  have survivalAtMostOne : (1 - p) ^ horizon ≤ 1 := by
    have factorNonnegative : 0 ≤ 1 - p := sub_nonneg.mpr pAtMostOne
    have factorAtMostOne : 1 - p ≤ 1 := by linarith
    exact pow_le_one₀ factorNonnegative factorAtMostOne
  have actualFalse :
      (pushforwardFiniteProbability noncontractiveQuotientEncode
        (evolveMany
          (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
          noncontractiveActionSequence horizon
          noncontractiveHiddenInitial)).mass false = (1 - p) ^ horizon := by
    simp [pushforwardFiniteProbability,
      noncontractiveQuotientFineState_univ,
      noncontractiveQuotientEncode,
      gradual_hidden_mass_exact p pNonnegative pAtMostOne horizon,
      gradual_representative_mass_zero p pNonnegative pAtMostOne horizon,
      gradual_absorbed_mass_exact p pNonnegative pAtMostOne horizon]
  have actualTrue :
      (pushforwardFiniteProbability noncontractiveQuotientEncode
        (evolveMany
          (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
          noncontractiveActionSequence horizon
          noncontractiveHiddenInitial)).mass true =
        1 - (1 - p) ^ horizon := by
    simp [pushforwardFiniteProbability,
      noncontractiveQuotientFineState_univ,
      noncontractiveQuotientEncode,
      gradual_hidden_mass_exact p pNonnegative pAtMostOne horizon,
      gradual_representative_mass_zero p pNonnegative pAtMostOne horizon,
      gradual_absorbed_mass_exact p pNonnegative pAtMostOne horizon]
  have abstractFalse :=
    gradual_abstract_false_mass_one p pNonnegative pAtMostOne horizon
  have abstractTrue :=
    gradual_abstract_true_mass_zero p pNonnegative pAtMostOne horizon
  simp [finiteTotalVariation, actualFalse, actualTrue,
    abstractFalse, abstractTrue,
    abs_of_nonpos (sub_nonpos.mpr survivalAtMostOne),
    abs_of_nonneg (sub_nonneg.mpr survivalAtMostOne)]

/-- The exact quotient error is the CDF of a constant structural-defect hazard. -/
theorem gradual_noncontractive_tv_eq_constant_hazard_cdf
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1)
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany
            (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
            noncontractiveActionSequence horizon
            noncontractiveHiddenInitial))
        (evolveMany
          (gradualNoncontractiveAbstractSequence p pNonnegative pAtMostOne)
          noncontractiveActionSequence horizon
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) =
      barrierCdf (constantBarrierHazard p) horizon := by
  rw [gradual_noncontractive_tv_exact p pNonnegative pAtMostOne horizon,
    constantBarrierHazard_cdf]

/-- Each additional step increases the actual TV error by exactly the remaining
unresolved mass times the local defect. -/
theorem gradual_noncontractive_tv_increment_exact
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1)
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany
            (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
            noncontractiveActionSequence (horizon + 1)
            noncontractiveHiddenInitial))
        (evolveMany
          (gradualNoncontractiveAbstractSequence p pNonnegative pAtMostOne)
          noncontractiveActionSequence (horizon + 1)
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) -
      finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany
            (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
            noncontractiveActionSequence horizon
            noncontractiveHiddenInitial))
        (evolveMany
          (gradualNoncontractiveAbstractSequence p pNonnegative pAtMostOne)
          noncontractiveActionSequence horizon
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) =
      (1 - p) ^ horizon * p := by
  rw [gradual_noncontractive_tv_exact p pNonnegative pAtMostOne,
    gradual_noncontractive_tv_exact p pNonnegative pAtMostOne, pow_succ]
  ring

/-- Actual quotient error is monotone in the prediction horizon. -/
theorem gradual_noncontractive_tv_mono_succ
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1)
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany
            (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
            noncontractiveActionSequence horizon
            noncontractiveHiddenInitial))
        (evolveMany
          (gradualNoncontractiveAbstractSequence p pNonnegative pAtMostOne)
          noncontractiveActionSequence horizon
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) ≤
      finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany
            (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
            noncontractiveActionSequence (horizon + 1)
            noncontractiveHiddenInitial))
        (evolveMany
          (gradualNoncontractiveAbstractSequence p pNonnegative pAtMostOne)
          noncontractiveActionSequence (horizon + 1)
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) := by
  have remainingNonnegative : 0 ≤ (1 - p) ^ horizon :=
    pow_nonneg (sub_nonneg.mpr pAtMostOne) _
  have incrementNonnegative : 0 ≤ (1 - p) ^ horizon * p :=
    mul_nonneg remainingNonnegative pNonnegative
  linarith [gradual_noncontractive_tv_increment_exact
    p pNonnegative pAtMostOne horizon]

/-- A declared finite-horizon threshold is refuted by an exact rational test. -/
theorem gradual_noncontractive_threshold_falsifier
    (p bound : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1)
    (horizon : Nat)
    (thresholdExceeded : bound < 1 - (1 - p) ^ horizon) :
    ¬ finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany
            (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
            noncontractiveActionSequence horizon
            noncontractiveHiddenInitial))
        (evolveMany
          (gradualNoncontractiveAbstractSequence p pNonnegative pAtMostOne)
          noncontractiveActionSequence horizon
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) ≤ bound := by
  rw [gradual_noncontractive_tv_exact p pNonnegative pAtMostOne horizon]
  exact not_le_of_gt thresholdExceeded

/-- Strong noncontractive no-go: every positive local defect, however small,
eventually refutes every time-uniform TV guarantee strictly below one. -/
theorem gradual_positive_defect_no_uniform_subunit_bound
    (p bound : ℚ) (pPositive : 0 < p) (pAtMostOne : p ≤ 1)
    (boundBelowOne : bound < 1) :
    ¬ ∀ horizon,
      finiteTotalVariation
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            (evolveMany
              (gradualNoncontractiveFineSequence p pPositive.le pAtMostOne)
              noncontractiveActionSequence horizon
              noncontractiveHiddenInitial))
          (evolveMany
            (gradualNoncontractiveAbstractSequence p pPositive.le pAtMostOne)
            noncontractiveActionSequence horizon
            (pushforwardFiniteProbability noncontractiveQuotientEncode
              noncontractiveHiddenInitial)) ≤ bound := by
  intro uniformBound
  obtain ⟨horizon, decayBelowSlack⟩ :=
    exists_pow_lt_of_lt_one
      (show 0 < 1 - bound by linarith)
      (show 1 - p < 1 by linarith)
  exact gradual_noncontractive_threshold_falsifier
    p bound pPositive.le pAtMostOne horizon (by linarith) (uniformBound horizon)

/-- Concrete exact prediction: a 10% local defect produces 65.13215599% TV
error after ten steps at the noncontractive boundary. -/
theorem gradual_ten_percent_ten_step_prediction :
    finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany
            (gradualNoncontractiveFineSequence (1 / 10) (by norm_num) (by norm_num))
            noncontractiveActionSequence 10 noncontractiveHiddenInitial))
        (evolveMany
          (gradualNoncontractiveAbstractSequence (1 / 10) (by norm_num) (by norm_num))
          noncontractiveActionSequence 10
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) = 6513215599 / 10000000000 := by
  rw [gradual_noncontractive_tv_exact]
  norm_num

end OCKIndividuationMSpaceComposition
