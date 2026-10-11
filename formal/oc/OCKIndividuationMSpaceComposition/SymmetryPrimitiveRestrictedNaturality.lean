import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionCommutation
import Mathlib.Logic.Equiv.Basic

namespace OCKIndividuationMSpaceComposition

universe uCarrier

/-!
# Restricted naturality for a primitive pair swap

M43 shows that full invariance under every carrier relabeling is impossible
once a third point exists.  The missing premise can be made explicit without
choosing a complement pairing: allow only relabelings that preserve the
unordered support of the primitive distinction.  Such relabelings may still
reverse the displayed orientation and may permute the complement arbitrarily.

This file proves that the canonical transposition commutes with exactly this
support-preserving class.  The result is a naturality theorem for a specified
admissible transformation class, not a hidden assertion that all relabelings
are admissible and not a global C₂ construction.
-/

namespace PrimitiveDistinction

variable {Carrier : Type uCarrier}

/-- A carrier relabeling preserves the unordered support of a primitive pair.
Both orientations are admitted; no pole is privileged by this predicate. -/
def PreservesPairSupport
    (distinction : PrimitiveDistinction Carrier)
    (relabel : Carrier ≃ Carrier) : Prop :=
  (relabel distinction.first = distinction.first ∧
      relabel distinction.second = distinction.second) ∨
    (relabel distinction.first = distinction.second ∧
      relabel distinction.second = distinction.first)

/-- The canonical pair transposition commutes with every relabeling that
preserves the pair support.  Complement points are not required to be fixed;
injectivity forces their images to remain in the complement. -/
theorem pairSwap_commutes_of_preservesPairSupport
    (distinction : PrimitiveDistinction Carrier)
    (relabel : Carrier ≃ Carrier)
    (preserves : PreservesPairSupport distinction relabel) :
    Function.Commute distinction.pairSwap relabel := by
  intro point
  by_cases pointFirst : point = distinction.first
  · subst point
    rcases preserves with preserve | reverse
    · rw [preserve.1, distinction.pairSwap_first, preserve.2]
    · rw [reverse.1, distinction.pairSwap_second, distinction.pairSwap_first,
        reverse.2]
  · by_cases pointSecond : point = distinction.second
    · subst point
      rcases preserves with preserve | reverse
      · rw [preserve.2, distinction.pairSwap_second, preserve.1]
      · rw [reverse.2, distinction.pairSwap_first, distinction.pairSwap_second,
          reverse.1]
    · have relabelOutsideFirst : relabel point ≠ distinction.first := by
        intro equality
        rcases preserves with preserve | reverse
        · apply pointFirst
          apply relabel.injective
          exact equality.trans preserve.1.symm
        · apply pointSecond
          apply relabel.injective
          exact equality.trans reverse.2.symm
      have relabelOutsideSecond : relabel point ≠ distinction.second := by
        intro equality
        rcases preserves with preserve | reverse
        · apply pointSecond
          apply relabel.injective
          exact equality.trans preserve.2.symm
        · apply pointFirst
          apply relabel.injective
          exact equality.trans reverse.1.symm
      rw [distinction.pairSwap_outside point pointFirst pointSecond]
      exact distinction.pairSwap_outside (relabel point) relabelOutsideFirst
        relabelOutsideSecond

/-- Support-preserving relabelings fix the conjugation class of the canonical
pair swap.  This is the exact restricted-naturality form left available on a
larger carrier after the M43 full-relabeling obstruction. -/
theorem pairSwapEquiv_conjugationInvariant_of_preservesPairSupport
    (distinction : PrimitiveDistinction Carrier)
    (relabel : Carrier ≃ Carrier)
    (preserves : PreservesPairSupport distinction relabel) :
    relabel.trans ((pairSwapEquiv distinction).trans relabel.symm) =
      pairSwapEquiv distinction := by
  apply Equiv.ext
  intro point
  have commute :=
    distinction.pairSwap_commutes_of_preservesPairSupport relabel preserves
  have commuteAt := commute point
  have conjugated := congrArg relabel.symm commuteAt
  simp only [Equiv.trans_apply, pairSwapEquiv]
  simpa using conjugated

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
