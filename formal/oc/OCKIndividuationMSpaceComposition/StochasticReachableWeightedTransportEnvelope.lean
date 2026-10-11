import OCKIndividuationMSpaceComposition.StochasticInhomogeneousTransportEnvelope
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

/-!
# Reachable-mass-weighted stochastic transport

A maximum row defect is valid but can be arbitrarily conservative when the
maximally defective rows carry little or no reachable mass. The exact mixture
inequality instead weights each transported row TV by the current fine law.
This module lifts that mature inequality into the typed OC quotient dynamics
and supplies a time-inhomogeneous reachable-mass recurrence.
-/

/-- TV defect of one pushed fine row against its frozen abstract row. -/
def transportedKernelRowTV
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : FiniteControlledKernel FineState FineAction)
    (abstract : FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (action : FineAction) (state : FineState) : ℚ :=
  finiteTotalVariation
    (pushedKernelRowProbability fine stateMap state action)
    (kernelRowProbability abstract (stateMap state) (actionMap action))

/-- Current-law-weighted row defect. Unlike a fibre maximum, rows with zero
reachable mass contribute exactly zero. -/
def reachableWeightedTransportDefect
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : FiniteControlledKernel FineState FineAction)
    (abstract : FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (action : FineAction)
    (fineLaw : FiniteProbabilityMass FineState) : ℚ :=
  ∑ state, fineLaw.mass state *
    transportedKernelRowTV fine abstract stateMap actionMap action state

/-- The weighted defect never exceeds any valid uniform row radius. -/
theorem reachableWeightedTransportDefect_le_uniform
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : FiniteControlledKernel FineState FineAction)
    (abstract : FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (action : FineAction)
    (fineLaw : FiniteProbabilityMass FineState)
    (epsilon : ℚ)
    (uniform : TransportedKernelRowTVBound fine abstract stateMap actionMap
      action epsilon) :
    reachableWeightedTransportDefect fine abstract stateMap actionMap action
        fineLaw ≤ epsilon := by
  calc
    reachableWeightedTransportDefect fine abstract stateMap actionMap action
        fineLaw ≤
      ∑ state, fineLaw.mass state * epsilon := by
        apply Finset.sum_le_sum
        intro state _
        exact mul_le_mul_of_nonneg_left (uniform state)
          (fineLaw.nonnegative state)
    _ = epsilon := by
      rw [← Finset.sum_mul, fineLaw.normalized]
      simp

/-- If a positive-mass row is strictly below the uniform radius, the weighted
certificate is strictly tighter than that radius. -/
theorem reachableWeightedTransportDefect_lt_uniform_of_positive_slack
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : FiniteControlledKernel FineState FineAction)
    (abstract : FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (action : FineAction)
    (fineLaw : FiniteProbabilityMass FineState)
    (epsilon : ℚ)
    (uniform : TransportedKernelRowTVBound fine abstract stateMap actionMap
      action epsilon)
    (witness : FineState)
    (positiveMass : 0 < fineLaw.mass witness)
    (strictRow : transportedKernelRowTV fine abstract stateMap actionMap
      action witness < epsilon) :
    reachableWeightedTransportDefect fine abstract stateMap actionMap action
        fineLaw < epsilon := by
  calc
    reachableWeightedTransportDefect fine abstract stateMap actionMap action
        fineLaw <
      ∑ state, fineLaw.mass state * epsilon := by
        apply Finset.sum_lt_sum
        · intro state _
          exact mul_le_mul_of_nonneg_left (uniform state)
            (fineLaw.nonnegative state)
        · exact ⟨witness, Finset.mem_univ witness,
            mul_lt_mul_of_pos_left strictRow positiveMass⟩
    _ = epsilon := by
      rw [← Finset.sum_mul, fineLaw.normalized]
      simp

/-- One-step typed transport with the exact reachable-law weighted defect. -/
theorem transportedEvolve_tv_le_contracted_initial_add_weightedRowError
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : FiniteControlledKernel FineState FineAction)
    (abstract : FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (action : FineAction)
    (fineInitial : FiniteProbabilityMass FineState)
    (abstractInitial : FiniteProbabilityMass AbstractState)
    (rho : ℚ)
    (contraction : FiniteEvolutionContraction abstract (actionMap action) rho) :
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveFiniteProbability fine action fineInitial))
        (evolveFiniteProbability abstract (actionMap action) abstractInitial) ≤
      rho * finiteTotalVariation
        (pushforwardFiniteProbability stateMap fineInitial) abstractInitial +
      reachableWeightedTransportDefect fine abstract stateMap actionMap action
        fineInitial := by
  let transportedInitial := pushforwardFiniteProbability stateMap fineInitial
  have rowMixture :
      finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveFiniteProbability fine action fineInitial))
        (evolveFiniteProbability abstract (actionMap action)
          transportedInitial) ≤
      reachableWeightedTransportDefect fine abstract stateMap actionMap action
        fineInitial := by
    simp only [finiteTotalVariation]
    rw [pushforward_evolve_mass_eq_transportedRowMixture,
      evolve_pushforward_mass_eq_mappedAbstractRowMixture]
    exact finiteProbabilityMixture_tv_le_weighted_row_tv fineInitial _ _
  calc
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveFiniteProbability fine action fineInitial))
        (evolveFiniteProbability abstract (actionMap action) abstractInitial) ≤
      finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveFiniteProbability fine action fineInitial))
        (evolveFiniteProbability abstract (actionMap action)
          transportedInitial) +
      finiteTotalVariation
        (evolveFiniteProbability abstract (actionMap action) transportedInitial)
        (evolveFiniteProbability abstract (actionMap action) abstractInitial) :=
      finiteTotalVariation_triangle _ _ _
    _ ≤ reachableWeightedTransportDefect fine abstract stateMap actionMap action
          fineInitial +
        rho * finiteTotalVariation transportedInitial abstractInitial :=
      add_le_add rowMixture (contraction transportedInitial abstractInitial)
    _ = rho * finiteTotalVariation
        (pushforwardFiniteProbability stateMap fineInitial) abstractInitial +
      reachableWeightedTransportDefect fine abstract stateMap actionMap action
        fineInitial := by ring

/-- Reachable weighted defect schedule induced by the evolving fine law. -/
def reachableWeightedRowErrorSchedule
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
    (fineInitial : FiniteProbabilityMass FineState) (step : Nat) : ℚ :=
  reachableWeightedTransportDefect (fine step) (abstract step) stateMap
    actionMap (actions step) (evolveMany fine actions step fineInitial)

/-- Time-inhomogeneous reachable-mass recurrence. -/
theorem transportedEvolveMany_tv_le_reachableWeightedEnvelope
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
    (rho : Nat → ℚ)
    (rhoNonnegative : ∀ step, 0 ≤ rho step)
    (contractions : ∀ step,
      FiniteEvolutionContraction (abstract step)
        (actionMap (actions step)) (rho step)) :
    ∀ horizon,
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveMany fine actions horizon fineInitial))
        (evolveMany abstract (fun step => actionMap (actions step)) horizon
          abstractInitial) ≤
      inhomogeneousRobustErrorEnvelope rho
        (reachableWeightedRowErrorSchedule fine abstract stateMap actionMap
          actions fineInitial)
        (finiteTotalVariation
          (pushforwardFiniteProbability stateMap fineInitial) abstractInitial)
        horizon := by
  intro horizon
  induction horizon with
  | zero =>
      simp [evolveMany, inhomogeneousRobustErrorEnvelope]
  | succ prior inductionHypothesis =>
      have oneStep :=
        transportedEvolve_tv_le_contracted_initial_add_weightedRowError
          (fine prior) (abstract prior) stateMap actionMap (actions prior)
          (evolveMany fine actions prior fineInitial)
          (evolveMany abstract (fun step => actionMap (actions step)) prior
            abstractInitial)
          (rho prior) (contractions prior)
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
              abstractInitial) +
          reachableWeightedRowErrorSchedule fine abstract stateMap actionMap
            actions fineInitial prior := oneStep
        _ ≤ rho prior *
              inhomogeneousRobustErrorEnvelope rho
                (reachableWeightedRowErrorSchedule fine abstract stateMap
                  actionMap actions fineInitial)
                (finiteTotalVariation
                  (pushforwardFiniteProbability stateMap fineInitial)
                  abstractInitial) prior +
            reachableWeightedRowErrorSchedule fine abstract stateMap actionMap
              actions fineInitial prior := by
          exact add_le_add
            (mul_le_mul_of_nonneg_left inductionHypothesis
              (rhoNonnegative prior)) (le_refl _)
        _ = inhomogeneousRobustErrorEnvelope rho
              (reachableWeightedRowErrorSchedule fine abstract stateMap
                actionMap actions fineInitial)
              (finiteTotalVariation
                (pushforwardFiniteProbability stateMap fineInitial)
                abstractInitial) (prior + 1) := rfl

end OCKIndividuationMSpaceComposition
