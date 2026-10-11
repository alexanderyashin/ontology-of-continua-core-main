import OCKIndividuationMSpaceComposition.SymmetryIntrinsicDimensionBoundary
import OCKIndividuationMSpaceComposition.SymmetryIntrinsicDimensionInterface
import Mathlib.Tactic.FinCases

namespace OCKIndividuationMSpaceComposition

namespace IntrinsicDimensionBasisBoundary

open IntrinsicDimensionBoundary
open IntrinsicDimensionInterface
open IntrinsicFinitaryRank

/-!
# The exact boundary of the finite basis interface

`IntrinsicDimensionBoundary.fanClosure` is an explicit finite closure that is
extensive, monotone and idempotent, yet has maximal independent families of
different sizes.  The original countermodel already proves the closure-law
failure.  This companion adds the missing interface fact: the same model
fails the finite augmentation property used by the conditional rank theorem.

The counterexample is deliberately stated for an ordinary closure, rather
than coerced into `FinitaryDistinctionClosure`: the latter structure contains
exchange by design.  Thus the result does not smuggle exchange into the
countermodel, and it does not claim that `BasisAugmentation` is necessary in
every possible dimension theory.
-/

/-! Augmentation for an ordinary closure, before exchange is assumed. -/
def PlainBasisAugmentation
    (closure : Finset Token → Finset Token)
    (seed : Finset Token) : Prop :=
  ∀ ⦃first second : Finset Token⦄,
    ClosureIndependent closure first →
    first ⊆ seed →
    ClosureIndependent closure second →
    second ⊆ seed →
    first.card < second.card →
    ∃ token ∈ second, token ∉ first ∧
      ClosureIndependent closure (insert token first)

/-! The fan closure has two maximal independent families but cannot augment
the smaller one toward the larger one. -/
theorem fanClosure_fails_plainBasisAugmentation :
    ¬ PlainBasisAugmentation fanClosure (Finset.univ : Finset Token) := by
  intro augmentation
  have firstIndependent : ClosureIndependent fanClosure ({0} : Finset Token) :=
    fanClosure_singleton_zero_maximal.1
  have secondIndependent : ClosureIndependent fanClosure ({1, 2} : Finset Token) :=
    fanClosure_pair_one_two_maximal.1
  rcases augmentation firstIndependent (by simp) secondIndependent (by simp)
      (by decide) with ⟨token, tokenInSecond, tokenNotFirst, tokenIndependent⟩
  fin_cases token
  · simp at tokenInSecond
  · have generated := tokenIndependent 1 (by simp)
    exact generated (by simp [fanClosure])
  · have generated := tokenIndependent 2 (by simp)
    exact generated (by simp [fanClosure])

/-!
An explicit boundary package: all three ordinary closure laws and the two
maximal-independent witnesses hold, while the finite augmentation interface
fails.  This is the requested non-derivability witness for dimension as a
well-defined maximal-independent cardinality from closure laws alone.
-/
theorem closure_laws_and_maximality_without_augmentation_are_insufficient :
    ClosureExtensive fanClosure ∧
      ClosureMonotone fanClosure ∧
      ClosureIdempotent fanClosure ∧
      ∃ first second : Finset Token,
        ClosureMaximalIndependent fanClosure first ∧
        ClosureMaximalIndependent fanClosure second ∧
        first.card ≠ second.card ∧
        ¬ PlainBasisAugmentation fanClosure (Finset.univ : Finset Token) := by
  exact ⟨fanClosure_extensive, fanClosure_monotone, fanClosure_idempotent,
    {0}, {1, 2}, fanClosure_singleton_zero_maximal,
    fanClosure_pair_one_two_maximal,
    fanClosure_maximal_cardinalities_differ,
    fanClosure_fails_plainBasisAugmentation⟩

/-!
`BasisAugmentation` is sufficient for the existing finite rank interface.
This packages the already-proved conditional rank theorem and the resulting
uniqueness statement; no converse is asserted. -/
theorem basisAugmentation_suffices_for_wellDefined_finite_dimension
    {Carrier : Type} [DecidableEq Carrier]
    (closure : FinitaryDistinctionClosure Carrier)
    (seed family : Finset Carrier)
    (maximal : MaximalIndependent closure seed family)
    (augmentation : BasisAugmentation closure seed) :
    closure.rank seed = family.card ∧
      ∀ other, MaximalIndependent closure seed other →
        other.card = family.card := by
  constructor
  · exact rank_is_wellDefined_maximalIndependent_dimension
      closure seed family maximal augmentation
  · intro other otherMaximal
    exact (maximalIndependent_card_unique_of_augmentation
      closure seed family other maximal otherMaximal augmentation).symm

end IntrinsicDimensionBasisBoundary

end OCKIndividuationMSpaceComposition
