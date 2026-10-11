import OCKIndividuationMSpaceComposition.StochasticQuotientMinimax
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

/-!
# Sharp noncontractive boundary for an actual stochastic quotient

The scalar robust envelope can grow without bound when `rho >= 1`, but total
variation between probability laws is always at most one.  Consequently that
scalar fact alone is not a sharp probabilistic no-go.  This finite OC fixture
closes the gap: two fine states share one optic cell, their pushed rows are at
TV distance one, the representative quotient is nonexpansive with coefficient
one, and an initially hidden representative mismatch reaches actual TV error
one after one step.

Therefore no theorem using only a structural row-defect bound and a
noncontractive (`rho = 1`) quotient can promise a time-uniform error bound
strictly below the probability diameter.  The `min 1` clip in the general
horizon theorem is mathematically necessary, not cosmetic scalar bookkeeping.
-/

inductive NoncontractiveQuotientFineState
  | representative
  | hidden
  | absorbed
  deriving DecidableEq, Fintype, Repr

theorem noncontractiveQuotientFineState_univ :
    (Finset.univ : Finset NoncontractiveQuotientFineState) =
      {NoncontractiveQuotientFineState.representative,
        NoncontractiveQuotientFineState.hidden,
        NoncontractiveQuotientFineState.absorbed} := by
  decide

def noncontractiveQuotientSuccessor :
    NoncontractiveQuotientFineState → NoncontractiveQuotientFineState
  | NoncontractiveQuotientFineState.representative =>
      NoncontractiveQuotientFineState.representative
  | NoncontractiveQuotientFineState.hidden =>
      NoncontractiveQuotientFineState.absorbed
  | NoncontractiveQuotientFineState.absorbed =>
      NoncontractiveQuotientFineState.absorbed

def noncontractiveQuotientKernel :
    FiniteControlledKernel NoncontractiveQuotientFineState Unit where
  mass state _ target :=
    if target = noncontractiveQuotientSuccessor state then 1 else 0
  nonnegative state action target := by
    split <;> norm_num
  normalized state action := by
    simpa using
      (Finset.sum_ite_eq'
        (noncontractiveQuotientSuccessor state)
        (fun _ : NoncontractiveQuotientFineState => (1 : ℚ)))

def noncontractiveQuotientEncode :
    NoncontractiveQuotientFineState → Bool
  | NoncontractiveQuotientFineState.representative
  | NoncontractiveQuotientFineState.hidden => false
  | NoncontractiveQuotientFineState.absorbed => true

def noncontractiveQuotientRepresentative :
    Bool → NoncontractiveQuotientFineState
  | false => NoncontractiveQuotientFineState.representative
  | true => NoncontractiveQuotientFineState.absorbed

theorem noncontractiveQuotientRepresentative_rightInverse :
    Function.RightInverse noncontractiveQuotientRepresentative
      noncontractiveQuotientEncode := by
  intro quotient
  cases quotient <;> rfl

/-- The hidden and selected fine representatives occupy the same optic cell. -/
theorem hidden_and_representative_same_quotient_cell :
    noncontractiveQuotientEncode
        NoncontractiveQuotientFineState.hidden =
      noncontractiveQuotientEncode
        NoncontractiveQuotientFineState.representative := rfl

/-- Their pushed one-step rows attain the full probability diameter. -/
theorem hidden_representative_same_cell_tv_eq_one :
    sameCellRowTV noncontractiveQuotientKernel
      noncontractiveQuotientEncode
      NoncontractiveQuotientFineState.hidden
      NoncontractiveQuotientFineState.representative () = 1 := by
  simp [sameCellRowTV, finiteTotalVariation,
    pushedKernelRowProbability, pushforwardFiniteProbability,
    kernelRowProbability, noncontractiveQuotientKernel,
    noncontractiveQuotientSuccessor, noncontractiveQuotientEncode,
    noncontractiveQuotientFineState_univ]

/-- The operational fibre diameter `1` is valid, and is attained by the
hidden/representative pair rather than introduced as a loose bound. -/
theorem noncontractiveQuotient_pairwiseDiameter_one :
    PairwiseLumpabilityDiameterBound noncontractiveQuotientKernel
      noncontractiveQuotientEncode () 1 := by
  intro left right sameCell
  exact finiteTotalVariation_le_one _ _

def noncontractiveRepresentativeKernel :
    FiniteControlledKernel Bool Unit :=
  representativeQuotientKernel noncontractiveQuotientKernel
    noncontractiveQuotientEncode noncontractiveQuotientRepresentative

/-- Like every finite Markov kernel, the representative quotient is
nonexpansive in TV.  Here the available coefficient is exactly the
noncontractive boundary `rho = 1`. -/
theorem noncontractiveRepresentativeKernel_contraction_one :
    FiniteEvolutionContraction noncontractiveRepresentativeKernel () 1 := by
  intro left right
  simpa using
    evolveFiniteProbability_nonexpansive
      noncontractiveRepresentativeKernel () left right

def noncontractiveHiddenInitial :
    FiniteProbabilityMass NoncontractiveQuotientFineState :=
  finiteDirac NoncontractiveQuotientFineState.hidden

def noncontractiveFineSequence :
    Nat → FiniteControlledKernel NoncontractiveQuotientFineState Unit :=
  fun _ => noncontractiveQuotientKernel

def noncontractiveAbstractSequence :
    Nat → FiniteControlledKernel Bool Unit :=
  fun _ => noncontractiveRepresentativeKernel

def noncontractiveActionSequence : Nat → Unit := fun _ => ()

/-- The actual transported probability error, not merely its scalar envelope,
equals one after one step.  This simultaneously witnesses sharpness of the
row-defect bound and of the probability-diameter clip. -/
theorem noncontractiveQuotient_one_step_tv_eq_one :
    finiteTotalVariation
        (pushforwardFiniteProbability noncontractiveQuotientEncode
          (evolveMany noncontractiveFineSequence noncontractiveActionSequence
            1 noncontractiveHiddenInitial))
        (evolveMany noncontractiveAbstractSequence noncontractiveActionSequence
          1
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            noncontractiveHiddenInitial)) = 1 := by
  simp [finiteTotalVariation, pushforwardFiniteProbability, evolveMany,
    evolveFiniteProbability, noncontractiveFineSequence,
    noncontractiveAbstractSequence, noncontractiveActionSequence,
    noncontractiveHiddenInitial, finiteDirac,
    noncontractiveRepresentativeKernel, representativeQuotientKernel,
    pushedKernelRowProbability, kernelRowProbability,
    noncontractiveQuotientKernel, noncontractiveQuotientSuccessor,
    noncontractiveQuotientEncode, noncontractiveQuotientRepresentative,
    noncontractiveQuotientFineState_univ]

/-- Sharp probabilistic no-go: at `rho = 1`, structural quotient defect alone
cannot justify any uniform TV guarantee strictly below one. -/
theorem noncontractive_structural_defect_no_uniform_subunit_bound
    (bound : ℚ)
    (boundBelowOne : bound < 1) :
    ¬ ∀ horizon,
      finiteTotalVariation
          (pushforwardFiniteProbability noncontractiveQuotientEncode
            (evolveMany noncontractiveFineSequence
              noncontractiveActionSequence horizon
              noncontractiveHiddenInitial))
          (evolveMany noncontractiveAbstractSequence
            noncontractiveActionSequence horizon
            (pushforwardFiniteProbability noncontractiveQuotientEncode
              noncontractiveHiddenInitial)) ≤ bound := by
  intro uniform
  have atOne := uniform 1
  rw [noncontractiveQuotient_one_step_tv_eq_one] at atOne
  linarith

/-- The representative construction satisfies its general row-radius theorem
at the same attained diameter used by the no-go fixture. -/
theorem noncontractiveRepresentativeKernel_rowBound_one :
    ApproximateQuotientRowBound noncontractiveQuotientKernel
      noncontractiveRepresentativeKernel noncontractiveQuotientEncode () 1 := by
  exact representativeQuotientKernel_rowBound_of_pairwiseDiameter
    noncontractiveQuotientKernel noncontractiveQuotientEncode
    noncontractiveQuotientRepresentative
    noncontractiveQuotientRepresentative_rightInverse () 1
    noncontractiveQuotient_pairwiseDiameter_one

end OCKIndividuationMSpaceComposition
