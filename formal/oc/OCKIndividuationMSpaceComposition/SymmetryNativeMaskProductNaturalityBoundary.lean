import OCKIndividuationMSpaceComposition.SymmetryNativeReversalClosure

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier uTargetCarrier

namespace PrimitiveDistinction

namespace NativeMaskProductNaturalityBoundary

open DisjointDistinctionFamily
open NativeCarrierTransport

variable {Index : Type uIndex}
variable {Carrier : Type uCarrier} {TargetCarrier : Type uTargetCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]
variable [Fintype TargetCarrier] [DecidableEq TargetCarrier]

/-!
# Carrier naturality of the native Boolean mask action

`NativeCarrierTransport` already conjugates one primitive transposition and
preserves the finite reversal closure.  The remaining action-level statement
is that the whole Boolean mask product is conjugated to the product of the
transported family.  We expose the conjugation as a monoid hom and then apply
the finite noncommutative-product map theorem.

This is a concrete native-action result.  The carrier equivalence is an
explicit correspondence premise; no arbitrary map, new generator, global OC
action, or intrinsic-dimension identification is obtained from it.
 -/

noncomputable def transportPermutationMonoidHom
    (relabel : Carrier ≃ TargetCarrier) :
    Equiv.Perm Carrier →* Equiv.Perm TargetCarrier where
  toFun := transportPermutation relabel
  map_one' := by
    ext point
    simp [transportPermutation]
  map_mul' := by
    intro first second
    ext point
    simp [transportPermutation, Equiv.Perm.mul_apply]

@[simp] theorem transportPermutationMonoidHom_apply
    (relabel : Carrier ≃ TargetCarrier)
    (permutation : Equiv.Perm Carrier) :
    transportPermutationMonoidHom relabel permutation =
      transportPermutation relabel permutation :=
  rfl

theorem transport_maskFactor
    (relabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index → Bool) (index : Index) :
    transportPermutation relabel
        (maskFactor family mask index) =
      maskFactor (transportFamily relabel family) mask index := by
  by_cases selected : mask index = true
  · simp only [maskFactor, selected, if_pos]
    change transportPermutation relabel
        (pairSwapEquiv (family.distinction index)) =
      pairSwapEquiv (transportDistinction relabel (family.distinction index))
    exact transport_pairSwap relabel (family.distinction index)
  · simp only [maskFactor, selected, if_neg]
    change transportPermutation relabel (1 : Equiv.Perm Carrier) =
      (1 : Equiv.Perm TargetCarrier)
    ext point
    simp [transportPermutation]

/-- Conjugation preserves the complete finite mask product, not only its
    cardinality or generated membership. -/
theorem transport_maskPermutationProduct
    (relabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index → Bool) :
    transportPermutation relabel
        (family.maskPermutationProduct mask) =
      (transportFamily relabel family).maskPermutationProduct mask := by
  unfold maskPermutationProduct
  change transportPermutationMonoidHom relabel
      ((Finset.univ : Finset Index).noncommProd
        (maskFactor family mask)
        (family.maskFactor_pairwise_commute mask)) =
    (Finset.univ : Finset Index).noncommProd
      (maskFactor (transportFamily relabel family) mask)
      ((transportFamily relabel family).maskFactor_pairwise_commute mask)
  rw [Finset.map_noncommProd]
  apply Finset.noncommProd_congr rfl
  intro index indexMember
  simpa only [transportPermutationMonoidHom_apply] using
    transport_maskFactor relabel family mask index

theorem transport_maskPermutationProduct_apply
    (relabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index → Bool) (point : TargetCarrier) :
    transportPermutation relabel
        (family.maskPermutationProduct mask) point =
      (transportFamily relabel family).maskPermutationProduct mask point := by
  rw [transport_maskPermutationProduct]

end NativeMaskProductNaturalityBoundary

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
