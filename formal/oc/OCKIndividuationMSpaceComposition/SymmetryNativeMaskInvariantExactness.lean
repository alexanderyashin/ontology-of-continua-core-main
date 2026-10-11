import OCKIndividuationMSpaceComposition.SymmetryNativeMaskInvariantBoundary

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier uScalar

namespace PrimitiveDistinction

namespace NativeMaskInvariantExactness

open DisjointDistinctionFamily
open NativeMaskInvariantBoundary

variable {Index : Type uIndex} {Carrier : Type uCarrier} {Scalar : Type uScalar}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]

/-!
# Exactness of finite mask invariance

The preceding boundary theorem proves that invariance under every primitive
generator propagates to every finite Boolean mask product.  In the native
finite family, the converse is also available: a singleton mask selects one
factor, and the product presentation reduces to that pair swap.  We therefore
obtain an exact iff, but only for this explicit finite disjoint realization.

This is not a global OC theorem.  The finite index type, the disjoint family,
and the derived mask-product presentation remain explicit premises.  No
intrinsic dimension, coordinate realization outside this family, or global
C2/torsor extension is inferred.
 -/

def singletonMask (index : Index) : Index → Bool :=
  fun current => decide (current = index)

theorem selectedIndices_singletonMask
    (index : Index) :
    selectedIndices (singletonMask index) = {index} := by
  ext current
  simp [singletonMask, selectedIndices]

theorem maskPermutationProduct_singletonMask
    (family : DisjointDistinctionFamily Index Carrier)
    (index : Index) :
    family.maskPermutationProduct (singletonMask index) =
      pairSwapEquiv (family.distinction index) := by
  rw [family.maskPermutationProduct_eq_maskPermutation]
  unfold maskPermutation
  rw [selectedIndices_singletonMask index]
  simp

theorem localMaskInvariant_of_maskInvariant
    (family : DisjointDistinctionFamily Index Carrier)
    (observable : Carrier → Scalar)
    (global : MaskInvariant family observable) :
    LocalMaskInvariant family observable := by
  intro index point
  have singleton := global (singletonMask index) point
  rw [maskPermutationProduct_singletonMask] at singleton
  exact singleton

theorem maskInvariant_iff_localMaskInvariant
    (family : DisjointDistinctionFamily Index Carrier)
    (observable : Carrier → Scalar) :
    MaskInvariant family observable ↔
      LocalMaskInvariant family observable := by
  constructor
  · exact localMaskInvariant_of_maskInvariant family observable
  · exact maskInvariant_of_localMaskInvariant family observable

end NativeMaskInvariantExactness

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
