import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionCommutationClassification
import OCKIndividuationMSpaceComposition.SymmetryDisjointDistinctionDimension

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier

namespace PrimitiveDistinction

/-!
# Faithful commuting families and the exact independence boundary

The previous commutation classification gives the missing implication needed
for a faithful finite Boolean direction family.  Pairwise commutation alone is
too weak: two copies of the same transposition commute.  If the local
transformations are also pairwise distinct, the classification theorem forces
their endpoint supports to be disjoint.

This file packages that implication without putting disjointness into the
input structure.  The resulting conversion reuses the existing intrinsic
Boolean product and its `2^n` faithfulness theorem.  The `Fin 2` duplicate
family below is an explicit countermodel showing why the distinctness premise
cannot be dropped.
-/

/-- A family of primitive distinctions whose local reversals commute and are
pairwise distinct as transformations.  No support disjointness is assumed. -/
structure FaithfulCommutingDistinctionFamily
    (Index : Type uIndex) (Carrier : Type uCarrier) where
  distinction : Index → PrimitiveDistinction Carrier
  pairSwapCommute : ∀ {first second : Index}, first ≠ second →
    Function.Commute (distinction first).pairSwap (distinction second).pairSwap
  pairSwapDistinct : ∀ {first second : Index}, first ≠ second →
    (distinction first).pairSwap ≠ (distinction second).pairSwap

namespace FaithfulCommutingDistinctionFamily

variable {Index : Type uIndex} {Carrier : Type uCarrier}

/-- Faithful commutation is enough to recover the disjoint-support family
required by the Boolean product construction. -/
def toDisjoint
    (family : FaithfulCommutingDistinctionFamily Index Carrier) :
    DisjointDistinctionFamily Index Carrier where
  distinction := family.distinction
  supportsDisjoint := by
    intro first second different
    exact commute_and_pairSwap_ne_implies_supportsDisjoint
      (family.distinction first) (family.distinction second)
      (family.pairSwapCommute different)
      (family.pairSwapDistinct different)

/-- The recovered disjointness is a theorem, not an extra field of the
original faithful-commuting family. -/
theorem supportsDisjoint
    (family : FaithfulCommutingDistinctionFamily Index Carrier)
    {first second : Index} (different : first ≠ second) :
    SupportsDisjoint (family.distinction first) (family.distinction second) :=
  family.toDisjoint.supportsDisjoint different

/-! ## Dimension realization after the boundary theorem -/

variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]

/-- Once faithful commutation has been proved, the existing native product
realizes exactly `2^n` distinct ambient transformations.  The cardinality is
therefore a consequence of the recovered supports, not a coordinate premise
of this interface. -/
theorem maskPermutationProduct_range_card
    (family : FaithfulCommutingDistinctionFamily Index Carrier) :
    Set.ncard (Set.range family.toDisjoint.maskPermutationProduct) =
      2 ^ Fintype.card Index := by
  exact family.toDisjoint.card_maskPermutationProduct_range

end FaithfulCommutingDistinctionFamily

/-! ## Countermodel: commutation without a new direction -/

/-- One fixed primitive pair used twice on `Fin 2`. -/
def duplicateFinTwoDistinction : PrimitiveDistinction (Fin 2) :=
  ⟨0, 1, by decide⟩

/-- A two-index family that repeats the same local distinction. -/
def duplicateFinTwoFamily (_ : Fin 2) : PrimitiveDistinction (Fin 2) :=
  duplicateFinTwoDistinction

/-- The repeated local reversals commute, because they are literally the same
transformation. -/
theorem duplicateFinTwoFamily_pairSwap_commute
    {first second : Fin 2} (_different : first ≠ second) :
    Function.Commute
      (duplicateFinTwoFamily first).pairSwap
      (duplicateFinTwoFamily second).pairSwap := by
  intro point
  rfl

/-- The repeated family is not support-disjoint: its two members share both
endpoints. -/
theorem duplicateFinTwoFamily_not_supportsDisjoint :
    ¬ SupportsDisjoint
      (duplicateFinTwoFamily (0 : Fin 2))
      (duplicateFinTwoFamily (1 : Fin 2)) := by
  intro disjoint
  exact disjoint.1 rfl

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
