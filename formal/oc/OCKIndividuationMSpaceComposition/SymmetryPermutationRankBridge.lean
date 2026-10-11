import OCKIndividuationMSpaceComposition.SymmetryDisjointDistinctionDimension
import OCKIndividuationMSpaceComposition.SymmetryFiniteCubeRankRealization

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier

namespace DisjointPermutationRankBridge

open PrimitiveDistinction
open FiniteCubeRankRealization

variable {Index : Type uIndex} {Carrier : Type uCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]

/-!
# Faithful permutation symmetry and finite closure rank

The disjoint-support construction gives a faithful Boolean homomorphism from
the masks of a finite family into ambient permutations.  The existing finite
closure-rank realization computes the rank of the same singleton-support
masks.  This file makes the bridge explicit: the image contains exactly
`2 ^ rank` transformations.

The theorem is a representation result.  It does not identify the displayed
coordinate rank with intrinsic OC dimension; that identification still
requires an OC-native closure and a realization-independence theorem.
-/

/- The rank belongs to the Boolean mask presentation; the family enters when
  the presentation is represented by ambient permutations. -/
noncomputable def maskPresentationRank : Nat :=
  BooleanCompositionRank.booleanGeneratedClosure.rank
    (fullCoordinateFamily (Index := Index))

theorem maskPresentationRank_eq_card_index :
    maskPresentationRank (Index := Index) = Fintype.card Index := by
  exact FiniteCubeRankRealization.booleanGeneratedClosure_fullCoordinateFamily_rank

/-! Reindexing cannot change the rank of this finite presentation.  The proof
  uses only cardinal invariance of equivalent finite index types; it does not
  identify the presentation with an intrinsic OC dimension. -/
theorem maskPresentationRank_index_equiv
    {FinalIndex : Type uIndex} [Fintype FinalIndex] [DecidableEq FinalIndex]
    (indexEquiv : Index ≃ FinalIndex) :
    maskPresentationRank (Index := Index) =
      maskPresentationRank (Index := FinalIndex) := by
  rw [maskPresentationRank_eq_card_index,
    maskPresentationRank_eq_card_index]
  exact Fintype.card_congr indexEquiv

/-! ## Exact image cardinality -/

theorem permutationProduct_range_card_eq_two_pow_maskPresentationRank
    (family : DisjointDistinctionFamily Index Carrier) :
    Set.ncard (Set.range family.maskPermutationProduct) =
      2 ^ maskPresentationRank (Index := Index) := by
  rw [family.card_maskPermutationProduct_range]
  rw [maskPresentationRank_eq_card_index]

theorem permutationProductHom_range_card_eq_two_pow_maskPresentationRank
    (family : DisjointDistinctionFamily Index Carrier) :
    Set.ncard (Set.range family.maskPermutationProductHom) =
      2 ^ maskPresentationRank (Index := Index) := by
  classical
  rw [Set.ncard_range_of_injective family.maskPermutationProductHom_injective]
  rw [maskPresentationRank_eq_card_index]
  simp [Nat.card_eq_fintype_card]

/-! The faithful map therefore carries the same finite Boolean algebra as the
  mask closure; no extra transformations appear in the image. -/
theorem permutationProductHom_range_card_eq_permutationProduct_range_card
    (family : DisjointDistinctionFamily Index Carrier) :
    Set.ncard (Set.range family.maskPermutationProductHom) =
      Set.ncard (Set.range family.maskPermutationProduct) := by
  rw [permutationProductHom_range_card_eq_two_pow_maskPresentationRank,
    permutationProduct_range_card_eq_two_pow_maskPresentationRank]

end DisjointPermutationRankBridge

end OCKIndividuationMSpaceComposition
