import OCKIndividuationMSpaceComposition.SymmetryFaithfulFamilyRankBridge
import Mathlib.Data.Fin.Basic
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier

namespace PrimitiveDistinction

/-!
# Canonical finite rank from adjacent primitive distinctions

The previous faithful-family bridge reads a Boolean rank back from an actual
carrier action, but it still takes a faithful commuting family as an input.
This file supplies a concrete finite realization from primitive distinctions
alone: on `Fin (2 * n)`, index `i` distinguishes the adjacent points `2*i` and
`2*i+1`.  Arithmetic proves that the displayed pairs are disjoint; the
permutation and rank results are then inherited from the already-proved
transposition calculus.

The construction is deliberately a realization theorem.  It proves genuine
rank witnesses `0, 1, 2, 3` and a uniform finite `n` theorem, but it does not
claim that every OC carrier contains this pairing or that this realization
alone defines global intrinsic dimension.
-/

namespace DisjointDistinctionFamily

variable {Index : Type uIndex} {Carrier : Type uCarrier}

/-! ## A disjoint family is faithful by theorem -/

/-- Disjoint supports imply both commuting and distinct local reversals, so a
disjoint family can be promoted to the weaker faithful-commuting interface
without adding a new premise. -/
def toFaithful
    (family : DisjointDistinctionFamily Index Carrier) :
    FaithfulCommutingDistinctionFamily Index Carrier where
  distinction := family.distinction
  pairSwapCommute := by
    intro first second different
    exact pairSwap_commute_of_supportsDisjoint
      (family.distinction first) (family.distinction second)
      (family.supportsDisjoint different)
  pairSwapDistinct := by
    intro first second different equal
    have disjoint := family.supportsDisjoint different
    have fixedFirst :
        (family.distinction first).pairSwap
            (family.distinction second).first =
          (family.distinction second).first :=
      (family.distinction first).pairSwap_outside _
        disjoint.1.symm disjoint.2.2.1.symm
    have evaluated := congrArg
      (fun transformation : Carrier → Carrier =>
        transformation (family.distinction second).first) equal
    change (family.distinction first).pairSwap
        (family.distinction second).first =
      (family.distinction second).pairSwap
        (family.distinction second).first at evaluated
    rw [fixedFirst, (family.distinction second).pairSwap_first] at evaluated
    exact (family.distinction second).separated evaluated

theorem toFaithful_distinction
    (family : DisjointDistinctionFamily Index Carrier) :
    (family.toFaithful).distinction = family.distinction :=
  rfl

end DisjointDistinctionFamily

namespace CanonicalFiniteFamily

open FiniteCubeRankRealization
open BooleanCompositionRank

/-! ## The adjacent-pair construction -/

/-- The even endpoint assigned to a finite index. -/
def evenPoint (n : Nat) (index : Fin n) : Fin (2 * n) :=
  ⟨2 * index.val, by omega⟩

/-- The odd endpoint assigned to a finite index. -/
def oddPoint (n : Nat) (index : Fin n) : Fin (2 * n) :=
  ⟨2 * index.val + 1, by omega⟩

theorem evenPoint_ne_evenPoint
    {n : Nat} {first second : Fin n} (different : first ≠ second) :
    evenPoint n first ≠ evenPoint n second := by
  intro equal
  apply different
  apply Fin.ext
  simpa [evenPoint] using congrArg Fin.val equal

theorem oddPoint_ne_oddPoint
    {n : Nat} {first second : Fin n} (different : first ≠ second) :
    oddPoint n first ≠ oddPoint n second := by
  intro equal
  apply different
  apply Fin.ext
  simpa [oddPoint] using congrArg Fin.val equal

theorem evenPoint_ne_oddPoint
    {n : Nat} (first second : Fin n) :
    evenPoint n first ≠ oddPoint n second := by
  intro equal
  have values := congrArg Fin.val equal
  simp [evenPoint, oddPoint] at values
  omega

theorem oddPoint_ne_evenPoint
    {n : Nat} (first second : Fin n) :
    oddPoint n first ≠ evenPoint n second := by
  intro equal
  have values := congrArg Fin.val equal
  simp [evenPoint, oddPoint] at values
  omega

/-- The canonical primitive distinction at one index. -/
def canonicalDistinction (n : Nat) (index : Fin n) :
    PrimitiveDistinction (Fin (2 * n)) where
  first := evenPoint n index
  second := oddPoint n index
  separated := evenPoint_ne_oddPoint index index

/-- Canonical adjacent pairs have pairwise disjoint endpoint supports. -/
def canonicalDisjointFamily (n : Nat) :
    DisjointDistinctionFamily (Fin n) (Fin (2 * n)) where
  distinction := canonicalDistinction n
  supportsDisjoint := by
    intro first second different
    refine ⟨?_, ?_, ?_, ?_⟩
    · exact evenPoint_ne_evenPoint different
    · exact evenPoint_ne_oddPoint first second
    · exact oddPoint_ne_evenPoint first second
    · exact oddPoint_ne_oddPoint different

/-- The concrete family is faithful and commuting, with no assumed
faithfulness field: the conversion is derived from disjoint supports. -/
def canonicalFaithfulFamily (n : Nat) :
    FaithfulCommutingDistinctionFamily (Fin n) (Fin (2 * n)) :=
  (canonicalDisjointFamily n).toFaithful

theorem canonicalFaithfulFamily_distinction
    (n : Nat) :
    (canonicalFaithfulFamily n).distinction = canonicalDistinction n :=
  rfl

/-! ## Actual rank and transformation cardinality -/

theorem canonical_actual_mask_range_card (n : Nat) :
    Set.ncard (Set.range (canonicalDisjointFamily n).maskPermutation) =
      2 ^ n := by
  simpa using (canonicalDisjointFamily n).card_maskPermutation_range

theorem canonical_actual_product_range_card (n : Nat) :
    Set.ncard (Set.range (canonicalDisjointFamily n).maskPermutationProduct) =
      2 ^ n := by
  simpa using (canonicalDisjointFamily n).card_maskPermutationProduct_range

/-- The finite Boolean rank is read back from the actual local reversals and
equals the number of indices. -/
theorem canonical_actual_direction_rank (n : Nat) :
    booleanGeneratedClosure.rank
        (FiniteCubeRankRealization.fullCoordinateFamily (Index := Fin n)) = n := by
  let family := canonicalFaithfulFamily n
  calc
    booleanGeneratedClosure.rank
          (FiniteCubeRankRealization.fullCoordinateFamily (Index := Fin n)) =
        family.localSwapFamily.card :=
      FaithfulCommutingDistinctionFamily.actualPrimitiveDirection_rank family
    _ = Fintype.card (Fin n) :=
      FaithfulCommutingDistinctionFamily.localSwapFamily_card family
    _ = n := by simp

/-! ## Small explicit witnesses -/

theorem canonical_rank_zero :
    booleanGeneratedClosure.rank
        (FiniteCubeRankRealization.fullCoordinateFamily (Index := Fin 0)) = 0 := by
  simpa using canonical_actual_direction_rank 0

theorem canonical_rank_one :
    booleanGeneratedClosure.rank
        (FiniteCubeRankRealization.fullCoordinateFamily (Index := Fin 1)) = 1 := by
  simpa using canonical_actual_direction_rank 1

theorem canonical_rank_two :
    booleanGeneratedClosure.rank
        (FiniteCubeRankRealization.fullCoordinateFamily (Index := Fin 2)) = 2 := by
  simpa using canonical_actual_direction_rank 2

theorem canonical_rank_three :
    booleanGeneratedClosure.rank
        (FiniteCubeRankRealization.fullCoordinateFamily (Index := Fin 3)) = 3 := by
  simpa using canonical_actual_direction_rank 3

end CanonicalFiniteFamily

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
