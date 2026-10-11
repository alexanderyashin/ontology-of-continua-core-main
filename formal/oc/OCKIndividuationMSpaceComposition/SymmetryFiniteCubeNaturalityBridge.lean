import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionFamilyNaturality
import OCKIndividuationMSpaceComposition.SymmetryPermutationRankBridge

namespace OCKIndividuationMSpaceComposition

universe uIndex uFinalIndex uSourceCarrier uTargetCarrier

namespace FiniteCubeNaturalityBridge

open PrimitiveDistinction
open PrimitiveDistinctionFamilyNaturality
open FiniteCubeRankRealization
open DisjointPermutationRankBridge

/-!
# From local naturality to the finite Boolean presentation

`EndpointPreservingFamilyMap` already gives the exact local naturality
interface: one ambient map per reindexed primitive distinction, preserving the
two displayed endpoints.  This module assembles those maps at the polarity
level and transports the existing finite Boolean mask action.

The target cube is a dependent product of axes.  An arbitrary family map does
not identify `targetAxis (indexEquiv i)` with an independently chosen target
axis at another index, so this bridge deliberately does **not** manufacture a
dependent point-level cube map by hidden casts.  Its native output is the
reindexed polarity mask, for which the component maps are exactly typed.  The
finite mask rank is then read back through the existing finite realization
theorem.  It remains a finite presentation invariant, not an intrinsic OC
dimension theorem.
-/

variable {Index : Type uIndex} {FinalIndex : Type uFinalIndex}
variable {SourceCarrier : Index → Type uSourceCarrier}
variable {TargetCarrier : FinalIndex → Type uTargetCarrier}
variable [Fintype Index] [Fintype FinalIndex]

variable {sourceAxis : PrimitiveDistinctionFamily Index SourceCarrier}
variable {targetAxis : PrimitiveDistinctionFamily FinalIndex TargetCarrier}

/-! ## The induced family relabeling -/

/-- The explicit equivalence that reindexes finite Boolean masks. -/
noncomputable def reindexMaskEquiv
    (indexEquiv : Index ≃ FinalIndex) :
    DistinctionMask Index ≃ DistinctionMask FinalIndex where
  toFun := PrimitiveDistinctionFamilyNaturality.reindexMask indexEquiv
  invFun := PrimitiveDistinctionFamilyNaturality.reindexMask indexEquiv.symm
  left_inv := by
    intro mask
    funext index
    simp [PrimitiveDistinctionFamilyNaturality.reindexMask]
  right_inv := by
    intro mask
    funext index
    simp [PrimitiveDistinctionFamilyNaturality.reindexMask]

/-- The component naturality maps induce a well-typed target polarity mask.
This is intentionally polarity-level: no equality between unrelated
dependent target-axis subtypes is assumed. -/
noncomputable def inducedFamilyPolarity
    (indexEquiv : Index ≃ FinalIndex)
    (map : EndpointPreservingFamilyMap indexEquiv sourceAxis targetAxis)
    (point : FiniteDistinctionCube Index SourceCarrier sourceAxis) :
    DistinctionMask FinalIndex :=
  fun finalIndex =>
    (targetAxis (indexEquiv (indexEquiv.symm finalIndex))).generatedPolarity
      ((map.component (indexEquiv.symm finalIndex)).axisMap
        (point (indexEquiv.symm finalIndex)))

/-- Component naturality is exactly reindexing of the source polarity mask. -/
theorem inducedFamilyPolarity_eq_reindexed
    (indexEquiv : Index ≃ FinalIndex)
    (map : EndpointPreservingFamilyMap indexEquiv sourceAxis targetAxis)
    (point : FiniteDistinctionCube Index SourceCarrier sourceAxis) :
    inducedFamilyPolarity indexEquiv map point =
      PrimitiveDistinctionFamilyNaturality.reindexMask indexEquiv
        (familyPolarity sourceAxis point) := by
  funext finalIndex
  simpa [inducedFamilyPolarity,
    PrimitiveDistinctionFamilyNaturality.reindexMask, familyPolarity] using
    (PrimitiveDistinctionFamilyNaturality.component_polarity_transport
      indexEquiv map point (indexEquiv.symm finalIndex))

/-! ## Mask equivariance -/

/-- The induced polarity mask commutes with every finite Boolean mask flip.
The mask is reindexed by the same explicit index equivalence; no ambient
global action is smuggled into this statement. -/
theorem inducedFamilyPolarity_maskAction
    (indexEquiv : Index ≃ FinalIndex)
    (map : EndpointPreservingFamilyMap indexEquiv sourceAxis targetAxis)
    (mask : DistinctionMask Index)
    (point : FiniteDistinctionCube Index SourceCarrier sourceAxis) :
    inducedFamilyPolarity indexEquiv map (maskAction sourceAxis mask point) =
      maskXor
        (PrimitiveDistinctionFamilyNaturality.reindexMask indexEquiv mask)
        (inducedFamilyPolarity indexEquiv map point) := by
  funext finalIndex
  have masked :=
    PrimitiveDistinctionFamilyNaturality.component_polarity_maskAction_transport
      indexEquiv map mask point (indexEquiv.symm finalIndex)
  have unmasked :=
    PrimitiveDistinctionFamilyNaturality.component_polarity_transport
      indexEquiv map point (indexEquiv.symm finalIndex)
  calc
    inducedFamilyPolarity indexEquiv map (maskAction sourceAxis mask point)
        finalIndex =
      Bool.xor (mask (indexEquiv.symm finalIndex))
        ((sourceAxis (indexEquiv.symm finalIndex)).generatedPolarity
          (point (indexEquiv.symm finalIndex))) := by
            simpa [inducedFamilyPolarity] using masked
    _ = Bool.xor (mask (indexEquiv.symm finalIndex))
        ((targetAxis (indexEquiv (indexEquiv.symm finalIndex))).generatedPolarity
          ((map.component (indexEquiv.symm finalIndex)).axisMap
            (point (indexEquiv.symm finalIndex)))) := by
          rw [unmasked]
    _ = (maskXor
        (PrimitiveDistinctionFamilyNaturality.reindexMask indexEquiv mask)
        (inducedFamilyPolarity indexEquiv map point)) finalIndex := by
          rfl

/-! ## Finite rank readback -/

/-- Reindexing the finite mask presentation preserves its existing closure
rank.  This reuses the canonical finite-rank realization theorem; it does not
claim that the rank is an intrinsic dimension of OC. -/
theorem finiteCubeRank_indexEquiv_invariant
    (indexEquiv : Index ≃ FinalIndex) :
    maskPresentationRank (Index := Index) =
      maskPresentationRank (Index := FinalIndex) := by
  classical
  rw [DisjointPermutationRankBridge.maskPresentationRank_eq_card_index,
    DisjointPermutationRankBridge.maskPresentationRank_eq_card_index]
  exact Fintype.card_congr indexEquiv

/-- A family relabeling therefore transports the cube and leaves the finite
mask rank unchanged.  The family map appears only to state the common
naturality context; rank is a property of the finite Boolean presentation. -/
theorem inducedFamilyRelabeling_rank_invariant
    (indexEquiv : Index ≃ FinalIndex)
    (_map : EndpointPreservingFamilyMap indexEquiv sourceAxis targetAxis) :
    maskPresentationRank (Index := Index) =
      maskPresentationRank (Index := FinalIndex) := by
  exact finiteCubeRank_indexEquiv_invariant indexEquiv

end FiniteCubeNaturalityBridge

end OCKIndividuationMSpaceComposition
