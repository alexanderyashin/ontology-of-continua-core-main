import OCMaturityCompletionCycle.CrossStateAbstractionBounds
import OCMaturityCompletionCycle.StochasticOpen
import Mathlib.Tactic.Linarith

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe uState uAction uQuotient uFineState uAbstractState uFineAction uAbstractAction

/-!
# Stochastic quotient defects and finite-horizon transport

This module is the finite-probability refinement of the deterministic
observation-quotient boundary.  The exact quotient theorem already lives in
`StochasticOpen`; here the operational defect is made numeric: a same-cell
pair has a defect equal to the total variation distance of its pushed-forward
one-step laws.  The finite sum is zero exactly when the controlled lumpability
condition holds.  The cross-state horizon theorem is then exposed through the
existing finite-TV transport calculus, with an exact zero-defect corollary.

The result is intentionally an adapter, not a claim that arbitrary OC
contexts are Markovian.  A domain may use it only after registering a finite
state map, action map, normalized kernels, and the row-TV contract.
-/

/-- The pushed-forward one-step law of one finite controlled kernel row. -/
def pushedKernelRowProbability
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (state : State)
    (action : Action) : FiniteProbabilityMass Quotient :=
  pushforwardFiniteProbability encode
    (kernelRowProbability kernel state action)

/-- The mass of the pushed row is exactly the existing `pushedMass` formula. -/
theorem pushedKernelRowProbability_mass
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (state : State)
    (action : Action)
    (target : Quotient) :
    (pushedKernelRowProbability kernel encode state action).mass target =
      pushedMass kernel encode state action target :=
  rfl

/-- TV separation of two fine states for one fixed action. -/
def sameCellRowTV
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (left right : State)
    (action : Action) : ℚ :=
  finiteTotalVariation
    (pushedKernelRowProbability kernel encode left action)
    (pushedKernelRowProbability kernel encode right action)

/-- A finite scalar defect for one controlled action and one encoder. -/
def pairwiseLumpabilityDefect
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (action : Action) : ℚ :=
  ∑ pair : State × State,
    if encode pair.1 = encode pair.2 then
      sameCellRowTV kernel encode pair.1 pair.2 action
    else 0

theorem sameCellRowTV_nonnegative
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (left right : State)
    (action : Action) :
    0 ≤ sameCellRowTV kernel encode left right action :=
  finiteTotalVariation_nonnegative _ _

/-- The finite scalar defect is zero iff every same-cell pair has equal rows. -/
theorem pairwiseLumpabilityDefect_eq_zero_iff
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (action : Action) :
    pairwiseLumpabilityDefect kernel encode action = 0 ↔
      ∀ ⦃left right : State⦄,
        encode left = encode right →
          sameCellRowTV kernel encode left right action = 0 := by
  constructor
  · intro defectZero left right sameCell
    have everyTermZero :
        (fun pair : State × State =>
          if encode pair.1 = encode pair.2 then
            sameCellRowTV kernel encode pair.1 pair.2 action
          else 0) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg (fun pair => by
        by_cases same : encode pair.1 = encode pair.2
        · simp [same, sameCellRowTV_nonnegative]
        · simp [same])).mp defectZero
    have selected := congrFun everyTermZero (left, right)
    simpa [sameCell] using selected
  · intro allZero
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun pair => by
      by_cases same : encode pair.1 = encode pair.2
      · simp [same, sameCellRowTV_nonnegative]
      · simp [same])).mpr
    funext pair
    by_cases same : encode pair.1 = encode pair.2
    · simpa [same] using (allZero same)
    · simp [same]

/--
Exact controlled lumpability is equivalent to vanishing numeric defect for
every action.  This is the finite-TV operational form of the exact quotient
criterion.
-/
theorem controlledLumpability_iff_pairwiseTV_defect_zero
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient) :
    ControlledLumpability kernel encode ↔
      ∀ action, pairwiseLumpabilityDefect kernel encode action = 0 := by
  constructor
  · intro lumpable action
    apply (pairwiseLumpabilityDefect_eq_zero_iff kernel encode action).2
    intro left right sameCell
    apply (finiteTotalVariation_eq_zero_iff_mass_eq _ _).2
    funext target
    exact lumpable sameCell action target
  · intro defects left right sameCell action target
    have tvZero :=
      (pairwiseLumpabilityDefect_eq_zero_iff kernel encode action).1
        (defects action) sameCell
    have massEqual := (finiteTotalVariation_eq_zero_iff_mass_eq _ _).1 tvZero
    exact congrFun massEqual target

/-- A positive measured same-cell defect rules out every exact memoryless factor. -/
theorem positive_pairwiseTV_defect_no_exact_quotient
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [Fintype Quotient]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (action : Action)
    (positive : 0 < pairwiseLumpabilityDefect kernel encode action) :
    IsEmpty (QuotientControlledKernel kernel encode) := by
  apply nonlumpable_no_exact_memoryless_quotient kernel encode
  intro lumpable
  have allZero :=
    (controlledLumpability_iff_pairwiseTV_defect_zero kernel encode).1 lumpable
  linarith [allZero action]

/-! ## Cross-state transport and the zero-defect exactness boundary -/

/-!
The following theorem is a thin OC naming adapter around the finite-state
transport calculus.  It is the quantitative prediction rule used by a domain
adapter: initial representation mismatch plus the sum of declared row-TV
defects, clipped by the probability diameter.
-/
theorem oc14_transported_kernel_horizon_bound
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
    (rowError : Nat → ℚ)
    (uniform : ∀ step,
      TransportedKernelRowTVBound (fine step) (abstract step) stateMap actionMap
        (actions step) (rowError step))
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveMany fine actions horizon fineInitial))
        (evolveMany abstract (fun step => actionMap (actions step)) horizon
          abstractInitial) ≤
      min 1 (finiteTotalVariation
          (pushforwardFiniteProbability stateMap fineInitial) abstractInitial +
        ∑ step ∈ Finset.range horizon, rowError step) :=
  transportedEvolveMany_tv_le_min_one_initial_add_sum_rowError fine abstract
    stateMap actionMap actions fineInitial abstractInitial rowError uniform horizon

/-- If the initial law and every registered transported row are exact, every
finite-horizon transported law is exact as well. -/
theorem zero_transport_defect_preserves_exact_horizon
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
    (initialExact :
      pushforwardFiniteProbability stateMap fineInitial = abstractInitial)
    (uniformExact : ∀ step,
      TransportedKernelRowTVBound (fine step) (abstract step) stateMap actionMap
        (actions step) 0)
    (horizon : Nat) :
    pushforwardFiniteProbability stateMap
        (evolveMany fine actions horizon fineInitial) =
      evolveMany abstract (fun step => actionMap (actions step)) horizon
        abstractInitial := by
  have bound := transportedEvolveMany_tv_le_min_one_initial_add_horizon_mul
    fine abstract stateMap actionMap actions fineInitial abstractInitial 0
    uniformExact horizon
  have tvZero :
      finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveMany fine actions horizon fineInitial))
        (evolveMany abstract (fun step => actionMap (actions step)) horizon
          abstractInitial) = 0 := by
    have bound' := bound
    rw [initialExact] at bound'
    apply le_antisymm
    · simpa [finiteTotalVariation] using bound'
    · exact finiteTotalVariation_nonnegative _ _
  have massEqual := (finiteTotalVariation_eq_zero_iff_mass_eq _ _).1 tvZero
  cases leftLaw : pushforwardFiniteProbability stateMap
      (evolveMany fine actions horizon fineInitial) with
  | mk leftMass leftNonnegative leftNormalized =>
    cases rightLaw : evolveMany abstract
        (fun step => actionMap (actions step)) horizon abstractInitial with
    | mk rightMass rightNonnegative rightNormalized =>
      simp only [leftLaw, rightLaw] at massEqual ⊢
      cases massEqual
      rfl

end OCKIndividuationMSpaceComposition
