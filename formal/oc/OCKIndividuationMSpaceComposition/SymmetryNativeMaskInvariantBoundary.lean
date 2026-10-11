import OCKIndividuationMSpaceComposition.SymmetryNativeMaskProductNaturalityBoundary

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier uScalar

namespace PrimitiveDistinction

namespace NativeMaskInvariantBoundary

open DisjointDistinctionFamily

variable {Index : Type uIndex} {Carrier : Type uCarrier} {Scalar : Type uScalar}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]

/-!
# Local generators force invariance of every finite mask product

`DisjointDistinctionFamily` supplies a finite family of pairwise-disjoint
primitive reversals.  The preceding native-action layer constructs their
Boolean mask product.  Here an observable is invariant under every local
generator, and we prove the genuinely stronger finite-product consequence:
it is invariant under every mask product.

The induction uses the actual unordered noncommutative product and the
family's derived pairwise-commutation proof.  Thus the result is not a
definition of invariance and does not assume a global action, a coordinate
realization, or an intrinsic-dimension identification.  The converse (that
invariance under all products recovers each generator) is intentionally not
claimed here; it needs a separate singleton-mask recovery theorem.
-/

def LocalMaskInvariant
    (family : DisjointDistinctionFamily Index Carrier)
    (observable : Carrier → Scalar) : Prop :=
  ∀ index point,
    observable (pairSwapEquiv (family.distinction index) point) =
      observable point

def MaskInvariant
    (family : DisjointDistinctionFamily Index Carrier)
    (observable : Carrier → Scalar) : Prop :=
  ∀ mask point,
    observable (family.maskPermutationProduct mask point) =
      observable point

theorem maskInvariant_of_localMaskInvariant
    (family : DisjointDistinctionFamily Index Carrier)
    (observable : Carrier → Scalar)
    (localInvariant : LocalMaskInvariant family observable) :
    MaskInvariant family observable := by
  intro mask point
  let invariant : Equiv.Perm Carrier → Prop := fun permutation =>
    ∀ point, observable (permutation point) = observable point
  have factors : invariant (family.maskPermutationProduct mask) := by
    unfold DisjointDistinctionFamily.maskPermutationProduct
    apply Finset.noncommProd_induction
      (s := (Finset.univ : Finset Index))
      (f := family.maskFactor mask)
      (family.maskFactor_pairwise_commute mask)
      invariant
    · intro first second firstInvariant secondInvariant point
      change observable ((first * second) point) = observable point
      rw [Equiv.Perm.mul_apply]
      exact (firstInvariant (second point)).trans (secondInvariant point)
    · intro point
      simp
    · intro index indexMember point
      by_cases selected : mask index = true
      · simp only [maskFactor, selected, if_pos]
        exact localInvariant index point
      · simp [maskFactor, selected]
  exact factors point

end NativeMaskInvariantBoundary

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
