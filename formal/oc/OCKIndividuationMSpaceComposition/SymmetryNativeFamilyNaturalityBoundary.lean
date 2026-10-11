import OCKIndividuationMSpaceComposition.SymmetryNativeIndexNaturalityBoundary

namespace OCKIndividuationMSpaceComposition

universe uIndex uNewIndex uCarrier uTargetCarrier

namespace PrimitiveDistinction

namespace NativeFamilyNaturalityBoundary

open DisjointDistinctionFamily
open NativeCarrierTransport
open NativeIndexNaturalityBoundary

variable {Index : Type uIndex} {NewIndex : Type uNewIndex}
variable {Carrier : Type uCarrier} {TargetCarrier : Type uTargetCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype NewIndex] [DecidableEq NewIndex]
variable [Fintype Carrier] [DecidableEq Carrier]
variable [Fintype TargetCarrier] [DecidableEq TargetCarrier]

/-!
# Joint naturality of a finite native distinction family

Carrier relabeling and index relabeling are separate naturality results.  This
slice gives their direct composition for one finite native family: an index
equivalence changes the names of primitive directions, while a carrier
equivalence conjugates their actual endpoint swaps.  The two transports
therefore preserve generated-membership and finite native rank together.

The mapped seed records the index correspondence explicitly.  The carrier
equivalence changes the ambient carrier but not the finite closure rank.  Both
equivalences are required data; pairwise disjointness alone does not produce a
canonical family equivalence.

No generic OC symmetry, constitutive law, causal law, exchange derivation,
intrinsic dimension, or continuum conclusion is introduced.
-/

def combinedFamily
    (indexRelabel : NewIndex ≃ Index)
    (carrierRelabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier) :
    DisjointDistinctionFamily NewIndex TargetCarrier :=
  transportFamily carrierRelabel
    (reindexFamily indexRelabel family)

theorem combined_reversalGenerated_iff
    (indexRelabel : NewIndex ≃ Index)
    (carrierRelabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset NewIndex) (index : NewIndex) :
    (combinedFamily indexRelabel carrierRelabel family).reversalGenerated
        seed index ↔
      family.reversalGenerated (reindexSeed indexRelabel seed)
        (indexRelabel index) := by
  change (transportFamily carrierRelabel
      (reindexFamily indexRelabel family)).reversalGenerated seed index ↔
    family.reversalGenerated (reindexSeed indexRelabel seed)
      (indexRelabel index)
  rw [transport_reversalGenerated_iff carrierRelabel
      (reindexFamily indexRelabel family) seed index]
  exact reindex_reversalGenerated_iff indexRelabel family seed index

theorem combined_nativeRank_eq_original_mapped_seed
    (indexRelabel : NewIndex ≃ Index)
    (carrierRelabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset NewIndex) :
    ((combinedFamily indexRelabel carrierRelabel family).nativeReversalFinitaryClosure).rank seed =
      (family.nativeReversalFinitaryClosure).rank
        (reindexSeed indexRelabel seed) := by
  calc
    ((combinedFamily indexRelabel carrierRelabel family).nativeReversalFinitaryClosure).rank seed =
        ((reindexFamily indexRelabel family).nativeReversalFinitaryClosure).rank seed := by
      exact transport_nativeReversalFinitaryClosure_rank carrierRelabel
        (reindexFamily indexRelabel family) seed
    _ = (family.nativeReversalFinitaryClosure).rank
        (reindexSeed indexRelabel seed) :=
      reindex_nativeRank_eq_original_nativeRank_mapped_seed
        indexRelabel family seed

theorem combined_nativeRank_birth_iff_original_mapped_seed
    (indexRelabel : NewIndex ≃ Index)
    (carrierRelabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset NewIndex) (index : NewIndex) :
    ((combinedFamily indexRelabel carrierRelabel family).nativeReversalFinitaryClosure).rank (insert index seed) =
        ((combinedFamily indexRelabel carrierRelabel family).nativeReversalFinitaryClosure).rank seed + 1 ↔
      (family.nativeReversalFinitaryClosure).rank
          (insert (indexRelabel index)
            (reindexSeed indexRelabel seed)) =
        (family.nativeReversalFinitaryClosure).rank
          (reindexSeed indexRelabel seed) + 1 := by
  rw [combined_nativeRank_eq_original_mapped_seed indexRelabel
      carrierRelabel family (insert index seed),
    combined_nativeRank_eq_original_mapped_seed indexRelabel
      carrierRelabel family seed]
  simp [reindexSeed]

theorem combined_nativeRank_birth_iff_not_generated
    (indexRelabel : NewIndex ≃ Index)
    (carrierRelabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset NewIndex) (index : NewIndex) :
    ((combinedFamily indexRelabel carrierRelabel family).nativeReversalFinitaryClosure).rank (insert index seed) =
        ((combinedFamily indexRelabel carrierRelabel family).nativeReversalFinitaryClosure).rank seed + 1 ↔
      ¬ family.reversalGenerated (reindexSeed indexRelabel seed)
        (indexRelabel index) := by
  rw [combined_nativeRank_birth_iff_original_mapped_seed indexRelabel
      carrierRelabel family seed index]
  exact (nativeReversal_rank_birth_iff_not_generated
    family (reindexSeed indexRelabel seed) (indexRelabel index)).symm

theorem combined_symmetryAlgebraLogRank_eq_original
    (indexRelabel : NewIndex ≃ Index)
    (carrierRelabel : Carrier ≃ TargetCarrier)
    (family : DisjointDistinctionFamily Index Carrier) :
    symmetryAlgebraLogRank (combinedFamily indexRelabel carrierRelabel family) =
      symmetryAlgebraLogRank family := by
  rw [symmetryAlgebraLogRank_eq_card,
    symmetryAlgebraLogRank_eq_card]
  exact Fintype.card_congr indexRelabel

end NativeFamilyNaturalityBoundary

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
