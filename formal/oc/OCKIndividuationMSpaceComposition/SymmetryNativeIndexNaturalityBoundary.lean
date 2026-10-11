import OCKIndividuationMSpaceComposition.SymmetryNativeRankBirthNaturality

namespace OCKIndividuationMSpaceComposition

universe uIndex uNewIndex uCarrier

namespace PrimitiveDistinction

namespace NativeIndexNaturalityBoundary

open DisjointDistinctionFamily

variable {Index : Type uIndex} {NewIndex : Type uNewIndex}
variable {Carrier : Type uCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype NewIndex] [DecidableEq NewIndex]
variable [Fintype Carrier] [DecidableEq Carrier]

/-!
# Naturality under a bijective relabeling of primitive-family indices

Carrier relabeling was handled by `NativeCarrierTransport`.  This slice
handles the other independent presentation choice: a bijection between the
index type naming a finite primitive family and a new index type.  The
reindexed family is built from the old distinctions, while disjointness is
transported through injectivity of the index equivalence.

The generated-membership theorem identifies a reindexed generated reversal
with membership of the corresponding old index in the mapped seed.  The
finite native rank and the logarithmic action rank are consequently invariant
under this explicit index equivalence.  An arbitrary map, a non-injective
quotient, or an unproved correspondence is outside this result.

No causal, constitutive, exchange, intrinsic-dimension, or continuum claim
is introduced beyond the already established finite native rank interface.
-/

def reindexFamily
    (relabel : NewIndex ≃ Index)
    (family : DisjointDistinctionFamily Index Carrier) :
    DisjointDistinctionFamily NewIndex Carrier where
  distinction := fun index => family.distinction (relabel index)
  supportsDisjoint := by
    intro first second different
    apply family.supportsDisjoint
    intro equality
    apply different
    exact relabel.injective equality

def reindexSeed
    (relabel : NewIndex ≃ Index)
    (seed : Finset NewIndex) : Finset Index :=
  seed.map relabel.toEmbedding

theorem reindex_reversalGenerated_iff
    (relabel : NewIndex ≃ Index)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset NewIndex) (index : NewIndex) :
    (reindexFamily relabel family).reversalGenerated seed index ↔
      family.reversalGenerated (reindexSeed relabel seed) (relabel index) := by
  rw [DisjointDistinctionFamily.nativeReversalGenerated_iff_mem,
    DisjointDistinctionFamily.nativeReversalGenerated_iff_mem]
  simp [reindexSeed]

theorem reindex_nativeRank_eq_original_nativeRank_mapped_seed
    (relabel : NewIndex ≃ Index)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset NewIndex) :
    ((reindexFamily relabel family).nativeReversalFinitaryClosure).rank seed =
      (family.nativeReversalFinitaryClosure).rank
        (reindexSeed relabel seed) := by
  rw [DisjointDistinctionFamily.nativeReversalFinitaryClosure_rank_eq_card,
    DisjointDistinctionFamily.nativeReversalFinitaryClosure_rank_eq_card]
  simp [reindexSeed]

theorem reindex_nativeRank_birth_iff_original_mapped_seed
    (relabel : NewIndex ≃ Index)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset NewIndex) (index : NewIndex) :
    ((reindexFamily relabel family).nativeReversalFinitaryClosure).rank
          (insert index seed) =
        ((reindexFamily relabel family).nativeReversalFinitaryClosure).rank
          seed + 1 ↔
      (family.nativeReversalFinitaryClosure).rank
          (insert (relabel index) (reindexSeed relabel seed)) =
        (family.nativeReversalFinitaryClosure).rank
          (reindexSeed relabel seed) + 1 := by
  rw [reindex_nativeRank_eq_original_nativeRank_mapped_seed relabel family
        (insert index seed),
    reindex_nativeRank_eq_original_nativeRank_mapped_seed relabel family seed]
  simp [reindexSeed]

theorem reindex_symmetryAlgebraLogRank_eq
    (relabel : NewIndex ≃ Index)
    (family : DisjointDistinctionFamily Index Carrier) :
    symmetryAlgebraLogRank (reindexFamily relabel family) =
      symmetryAlgebraLogRank family := by
  rw [symmetryAlgebraLogRank_eq_card,
    symmetryAlgebraLogRank_eq_card]
  exact Fintype.card_congr relabel

theorem reindex_nativeRank_birth_iff_not_generated
    (relabel : NewIndex ≃ Index)
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset NewIndex) (index : NewIndex) :
    ((reindexFamily relabel family).nativeReversalFinitaryClosure).rank
          (insert index seed) =
        ((reindexFamily relabel family).nativeReversalFinitaryClosure).rank
          seed + 1 ↔
      ¬ family.reversalGenerated (reindexSeed relabel seed) (relabel index) := by
  rw [reindex_nativeRank_birth_iff_original_mapped_seed relabel family seed index]
  exact (DisjointDistinctionFamily.nativeReversal_rank_birth_iff_not_generated
    family (reindexSeed relabel seed) (relabel index)).symm

end NativeIndexNaturalityBoundary

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
