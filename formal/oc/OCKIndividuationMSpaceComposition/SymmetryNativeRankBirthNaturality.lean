import OCKIndividuationMSpaceComposition.SymmetryNativeRankBirthEquivalence

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier

namespace PrimitiveDistinction

/-!
# Naturality of native rank birth under carrier relabeling

`NativeCarrierTransport` already conjugates each pair-swap to a relabeled
carrier.  This file closes the corresponding dimension-facing statement:
membership in the native reversal closure, rank growth, and the exact
"new-direction" criterion are invariant under that admissible equivalence.
The carrier bijection is an explicit premise; arbitrary maps are not silently
declared OC symmetries.
-/

namespace NativeCarrierTransport

variable {Index : Type uIndex} {Carrier : Type uCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]
variable {TargetCarrier : Type*}
variable [Fintype TargetCarrier] [DecidableEq TargetCarrier]

theorem transport_reversalGenerated_iff
    (relabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset Index) (index : Index) :
    (transportFamily relabel family).reversalGenerated seed index ↔
      family.reversalGenerated seed index := by
  rw [DisjointDistinctionFamily.nativeReversalGenerated_iff_mem,
    DisjointDistinctionFamily.nativeReversalGenerated_iff_mem]

theorem transport_rank_birth_iff_original_rank_birth
    (relabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset Index) (index : Index) :
    ((transportFamily relabel family).nativeReversalFinitaryClosure).rank
          (insert index seed) =
        ((transportFamily relabel family).nativeReversalFinitaryClosure).rank
          seed + 1 ↔
      (family.nativeReversalFinitaryClosure).rank (insert index seed) =
        (family.nativeReversalFinitaryClosure).rank seed + 1 := by
  rw [transport_nativeReversalFinitaryClosure_rank relabel family
        (insert index seed),
    transport_nativeReversalFinitaryClosure_rank relabel family seed]

/-! The criterion can be read either before or after relabeling. -/
theorem transport_rank_birth_iff_not_generated
    (relabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset Index) (index : Index) :
    ((transportFamily relabel family).nativeReversalFinitaryClosure).rank
          (insert index seed) =
        ((transportFamily relabel family).nativeReversalFinitaryClosure).rank
          seed + 1 ↔
      ¬ family.reversalGenerated seed index := by
  rw [transport_rank_birth_iff_original_rank_birth relabel family seed index]
  exact (DisjointDistinctionFamily.nativeReversal_rank_birth_iff_not_generated
    family seed index).symm

theorem transport_rank_birth_iff_not_in_original_subgroup
    (relabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset Index) (index : Index) :
    ((transportFamily relabel family).nativeReversalFinitaryClosure).rank
          (insert index seed) =
        ((transportFamily relabel family).nativeReversalFinitaryClosure).rank
          seed + 1 ↔
      (pairSwapEquiv (family.distinction index) : Equiv.Perm Carrier) ∉
        family.reversalSubgroup seed := by
  rw [transport_rank_birth_iff_original_rank_birth relabel family seed index]
  exact (DisjointDistinctionFamily.nativeReversal_rank_birth_iff_not_in_subgroup
    family seed index).symm

end NativeCarrierTransport

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
