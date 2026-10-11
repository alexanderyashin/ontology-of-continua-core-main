import OCKIndividuationMSpaceComposition.StochasticQuotientMinimax
import OCKIndividuationMSpaceComposition.StochasticGradualNoncontractiveQuotientDefect

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

/-!
# General time-inhomogeneous stochastic transport envelope

The exact product law proved by the gradual leak countermodel is a theorem
about that structural family.  It is not implied by a measured same-cell row
defect alone.  This module supplies the general operational statement for an
arbitrary finite, time-inhomogeneous quotient process.

If step `t` has transported row error at most `epsilon t` and the abstract
evolution contracts total variation by at most `rho t`, then the horizon error
obeys the recursively computable envelope

`E 0 = E0`, `E (t+1) = rho t * E t + epsilon t`.

The theorem is directly falsifiable: a premise-admissible observed horizon
error above the registered envelope refutes the conjunction of the row-error
and contraction contracts.  A separate countermodel shows why the exact leak
product curve cannot be inferred from the local defect without structural and
initial-law correspondence.
-/

/-- The exact deterministic recurrence used by the general inhomogeneous
transport certificate. -/
def inhomogeneousRobustErrorEnvelope
    (rho epsilon : Nat → ℚ) (initialError : ℚ) : Nat → ℚ
  | 0 => initialError
  | horizon + 1 =>
      rho horizon *
          inhomogeneousRobustErrorEnvelope rho epsilon initialError horizon +
        epsilon horizon

/-- Arbitrary time-varying row errors and contraction coefficients propagate
through the registered scalar recurrence. -/
theorem transportedEvolveMany_tv_le_inhomogeneousRobustErrorEnvelope
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : Nat → FiniteControlledKernel FineState FineAction)
    (abstract : Nat → FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (actions : Nat → FineAction)
    (fineInitial : FiniteProbabilityMass FineState)
    (abstractInitial : FiniteProbabilityMass AbstractState)
    (epsilon rho : Nat → ℚ)
    (rhoNonnegative : ∀ step, 0 ≤ rho step)
    (uniform : ∀ step,
      TransportedKernelRowTVBound (fine step) (abstract step) stateMap actionMap
        (actions step) (epsilon step))
    (contractions : ∀ step,
      FiniteEvolutionContraction (abstract step)
        (actionMap (actions step)) (rho step)) :
    ∀ horizon,
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveMany fine actions horizon fineInitial))
        (evolveMany abstract (fun step => actionMap (actions step)) horizon
          abstractInitial) ≤
      inhomogeneousRobustErrorEnvelope rho epsilon
        (finiteTotalVariation
          (pushforwardFiniteProbability stateMap fineInitial) abstractInitial)
        horizon := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, inhomogeneousRobustErrorEnvelope]
  | succ prior inductionHypothesis =>
      have oneStep := transportedEvolve_tv_le_contracted_initial_add_rowError
        (fine prior) (abstract prior) stateMap actionMap (actions prior)
        (evolveMany fine actions prior fineInitial)
        (evolveMany abstract (fun step => actionMap (actions step)) prior
          abstractInitial)
        (epsilon prior) (rho prior) (uniform prior) (contractions prior)
      calc
        finiteTotalVariation
            (pushforwardFiniteProbability stateMap
              (evolveMany fine actions (prior + 1) fineInitial))
            (evolveMany abstract (fun step => actionMap (actions step))
              (prior + 1) abstractInitial) ≤
          rho prior * finiteTotalVariation
            (pushforwardFiniteProbability stateMap
              (evolveMany fine actions prior fineInitial))
            (evolveMany abstract (fun step => actionMap (actions step)) prior
              abstractInitial) + epsilon prior := oneStep
        _ ≤ rho prior *
              inhomogeneousRobustErrorEnvelope rho epsilon
                (finiteTotalVariation
                  (pushforwardFiniteProbability stateMap fineInitial)
                  abstractInitial) prior + epsilon prior := by
            exact add_le_add
              (mul_le_mul_of_nonneg_left inductionHypothesis
                (rhoNonnegative prior)) (le_refl _)
        _ = inhomogeneousRobustErrorEnvelope rho epsilon
              (finiteTotalVariation
                (pushforwardFiniteProbability stateMap fineInitial)
                abstractInitial) (prior + 1) := rfl

/-- A premise-admissible envelope violation is a sharp negative verifier for
the joint row-error and contraction contract. -/
theorem observed_violation_refutes_inhomogeneous_transport_contract
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : Nat → FiniteControlledKernel FineState FineAction)
    (abstract : Nat → FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (actions : Nat → FineAction)
    (fineInitial : FiniteProbabilityMass FineState)
    (abstractInitial : FiniteProbabilityMass AbstractState)
    (epsilon rho : Nat → ℚ)
    (rhoNonnegative : ∀ step, 0 ≤ rho step)
    (horizon : Nat)
    (violation :
      inhomogeneousRobustErrorEnvelope rho epsilon
          (finiteTotalVariation
            (pushforwardFiniteProbability stateMap fineInitial)
            abstractInitial) horizon <
        finiteTotalVariation
          (pushforwardFiniteProbability stateMap
            (evolveMany fine actions horizon fineInitial))
          (evolveMany abstract (fun step => actionMap (actions step)) horizon
            abstractInitial)) :
    ¬ ((∀ step,
          TransportedKernelRowTVBound (fine step) (abstract step)
            stateMap actionMap (actions step) (epsilon step)) ∧
        (∀ step,
          FiniteEvolutionContraction (abstract step)
            (actionMap (actions step)) (rho step))) := by
  intro premises
  have certified :=
    transportedEvolveMany_tv_le_inhomogeneousRobustErrorEnvelope
      fine abstract stateMap actionMap actions fineInitial abstractInitial
      epsilon rho rhoNonnegative premises.1 premises.2 horizon
  exact (not_lt_of_ge certified) violation

/-- Cumulative row-error budget at the noncontractive boundary. -/
def cumulativeRowError (epsilon : Nat → ℚ) : Nat → ℚ
  | 0 => 0
  | horizon + 1 => cumulativeRowError epsilon horizon + epsilon horizon

/-- With `rho = 1`, the general recurrence is the initial mismatch plus the
cumulative local row-error budget. -/
theorem inhomogeneousRobustErrorEnvelope_one_eq
    (epsilon : Nat → ℚ) (initialError : ℚ) :
    ∀ horizon,
      inhomogeneousRobustErrorEnvelope (fun _ => 1) epsilon initialError
          horizon =
        initialError + cumulativeRowError epsilon horizon := by
  intro horizon
  induction horizon with
  | zero =>
      simp [inhomogeneousRobustErrorEnvelope, cumulativeRowError]
  | succ prior inductionHypothesis =>
      simp [inhomogeneousRobustErrorEnvelope, cumulativeRowError,
        inductionHypothesis]
      ring

/-- General finite-horizon certificate when the quotient is only
nonexpansive. -/
theorem transportedEvolveMany_tv_le_initial_add_cumulativeRowError
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : Nat → FiniteControlledKernel FineState FineAction)
    (abstract : Nat → FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (actions : Nat → FineAction)
    (fineInitial : FiniteProbabilityMass FineState)
    (abstractInitial : FiniteProbabilityMass AbstractState)
    (epsilon : Nat → ℚ)
    (uniform : ∀ step,
      TransportedKernelRowTVBound (fine step) (abstract step) stateMap actionMap
        (actions step) (epsilon step))
    (nonexpansive : ∀ step,
      FiniteEvolutionContraction (abstract step)
        (actionMap (actions step)) 1)
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveMany fine actions horizon fineInitial))
        (evolveMany abstract (fun step => actionMap (actions step)) horizon
          abstractInitial) ≤
      finiteTotalVariation
          (pushforwardFiniteProbability stateMap fineInitial) abstractInitial +
        cumulativeRowError epsilon horizon := by
  have bound :=
    transportedEvolveMany_tv_le_inhomogeneousRobustErrorEnvelope
      fine abstract stateMap actionMap actions fineInitial abstractInitial
      epsilon (fun _ => 1) (fun _ => by norm_num) uniform nonexpansive horizon
  simpa [inhomogeneousRobustErrorEnvelope_one_eq] using bound

/-- Initial law concentrated on the selected representative of the unresolved
quotient cell. -/
def noncontractiveRepresentativeInitial :
    FiniteProbabilityMass NoncontractiveQuotientFineState :=
  finiteDirac NoncontractiveQuotientFineState.representative

/-- Starting from the selected representative produces zero one-step
transport error, even though the kernel still has the same positive hidden-row
defect elsewhere in the optic fibre. -/
theorem gradual_representative_initial_one_step_tv_zero
    (p : ℚ) (pNonnegative : 0 ≤ p) (pAtMostOne : p ≤ 1) :
    finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany
            (gradualNoncontractiveFineSequence p pNonnegative pAtMostOne)
            noncontractiveActionSequence 1
            noncontractiveRepresentativeInitial))
        (evolveMany
          (gradualNoncontractiveAbstractSequence p pNonnegative pAtMostOne)
          noncontractiveActionSequence 1
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveRepresentativeInitial)) = 0 := by
  apply (finiteTotalVariation_eq_zero_iff_mass_eq _ _).2
  funext target
  cases target <;>
    simp [evolveMany, evolveFiniteProbability,
      pushforwardFiniteProbability, noncontractiveRepresentativeInitial,
      finiteDirac, gradualNoncontractiveFineSequence,
      gradualNoncontractiveAbstractSequence,
      gradualNoncontractiveKernel, gradualRepresentativeKernel_mass_eq_dirac,
      noncontractiveActionSequence, noncontractiveQuotientEncode,
      noncontractiveQuotientFineState_univ]

/-- No-go: the local same-cell row defect does not identify even the one-step
transport error.  The same kernel and optic have defect `p`, but hidden and
representative initial laws yield errors `p` and `0`, respectively. -/
theorem local_row_defect_does_not_identify_one_step_transport_error
    (p : ℚ) (pPositive : 0 < p) (pAtMostOne : p ≤ 1) :
    sameCellRowTV
        (gradualNoncontractiveKernel p pPositive.le pAtMostOne)
        noncontractiveQuotientEncode
        NoncontractiveQuotientFineState.hidden
        NoncontractiveQuotientFineState.representative () = p ∧
    finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany
            (gradualNoncontractiveFineSequence p pPositive.le pAtMostOne)
            noncontractiveActionSequence 1 noncontractiveHiddenInitial))
        (evolveMany
          (gradualNoncontractiveAbstractSequence p pPositive.le pAtMostOne)
          noncontractiveActionSequence 1
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) = p ∧
    finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany
            (gradualNoncontractiveFineSequence p pPositive.le pAtMostOne)
            noncontractiveActionSequence 1
            noncontractiveRepresentativeInitial))
        (evolveMany
          (gradualNoncontractiveAbstractSequence p pPositive.le pAtMostOne)
          noncontractiveActionSequence 1
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveRepresentativeInitial)) = 0 := by
  refine ⟨gradual_same_cell_row_tv_exact p pPositive.le pAtMostOne, ?_,
    gradual_representative_initial_one_step_tv_zero
      p pPositive.le pAtMostOne⟩
  rw [gradual_noncontractive_tv_exact]
  ring

end OCKIndividuationMSpaceComposition
