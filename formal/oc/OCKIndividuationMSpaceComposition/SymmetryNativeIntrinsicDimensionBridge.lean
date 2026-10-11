import OCKIndividuationMSpaceComposition.SymmetryNativeReversalClosure
import OCKIndividuationMSpaceComposition.SymmetryIntrinsicDimensionInterface

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier

namespace PrimitiveDistinction

namespace DisjointDistinctionFamily

open IntrinsicFinitaryRank
open IntrinsicDimensionInterface

variable {Index : Type uIndex} {Carrier : Type uCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]

/-!
# Native primitive distinctions and a finite intrinsic-dimension witness

`SymmetryNativeReversalClosure` constructs a closure from actual carrier
permutations and proves that, for pairwise-disjoint primitive supports, the
subgroup-generated index closure is exactly the supplied seed.  This file
adds the missing dimension-facing consequences without changing the closure
definition or importing vectors, coordinates, or `finrank`.

The positive result is deliberately conditional.  A finite family of
pairwise-disjoint primitive distinctions supplies one faithful reversible
direction per index; in that realised native model every seed is independent,
the only maximal independent family in the full index universe is the full
universe, and adjoining an unseen index raises rank by one.  Thus the
cardinality is a genuine finite basis cardinality for this selected native
realisation.

This does not claim that one primitive distinction by itself determines a
global OC dimension.  The finite index family, finite carrier, disjoint
support premise, and native reversal composition remain explicit.  The
ordinary-closure and singleton-generation countermodels in the preceding
dimension modules remain the boundary for a general OC composition law.
-/

/-! Since the native subgroup closure is proved equal to its seed, every
finite seed is independent in the induced intrinsic closure. -/
theorem nativeReversalFinitaryClosure_independent
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset Index) :
    (family.nativeReversalFinitaryClosure).Independent seed := by
  intro index indexMember generated
  change index ∈ family.nativeReversalClosure (seed.erase index) at generated
  rw [family.nativeReversalClosure_eq_seed (seed.erase index)] at generated
  simpa using generated

/-! The generic exchange-rank insertion theorem becomes a concrete statement
for the native reversal closure: non-membership in the actual seed is exactly
non-generation in the native subgroup closure. -/
theorem nativeReversalFinitaryClosure_rank_insert_eq_add_one_of_not_mem
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset Index) (index : Index)
    (indexNotMember : index ∉ seed) :
    (family.nativeReversalFinitaryClosure).rank (insert index seed) =
      (family.nativeReversalFinitaryClosure).rank seed + 1 := by
  apply FinitaryDistinctionClosure.rank_insert_eq_add_one_of_not_generated
  change index ∉ family.nativeReversalClosure seed
  rw [family.nativeReversalClosure_eq_seed seed]
  exact indexNotMember

/-! A maximal independent family in the full finite index universe cannot omit
an index: the native closure makes every finite seed independent, so an omitted
index could always be inserted. -/
theorem nativeReversal_maximalIndependent_eq_univ
    (family : DisjointDistinctionFamily Index Carrier)
    (basis : Finset Index)
    (maximal : MaximalIndependent
      family.nativeReversalFinitaryClosure (Finset.univ : Finset Index) basis) :
    basis = (Finset.univ : Finset Index) := by
  apply Finset.Subset.antisymm
  · exact Finset.subset_univ _
  · intro index indexMember
    by_contra indexNotMember
    have extendedIndependent :
        (family.nativeReversalFinitaryClosure).Independent
          (insert index basis) :=
      family.nativeReversalFinitaryClosure_independent (insert index basis)
    exact (maximal.2.2 index (Finset.mem_univ _) indexNotMember
      extendedIndependent).elim

/-! The native reversal model therefore has a well-defined finite basis
cardinality, with no separate augmentation premise needed: maximality is
resolved directly from the native closure theorem. -/
theorem nativeReversal_maximalIndependent_card_eq_index_card
    (family : DisjointDistinctionFamily Index Carrier)
    (basis : Finset Index)
    (maximal : MaximalIndependent
      family.nativeReversalFinitaryClosure (Finset.univ : Finset Index) basis) :
    basis.card = Fintype.card Index := by
  rw [family.nativeReversal_maximalIndependent_eq_univ basis maximal]
  simp

/-! The basis cardinality agrees with both finite intrinsic rank and the
logarithmic cardinality of the realised native action. -/
theorem nativeReversal_maximalIndependent_card_eq_rank_eq_action_log_rank
    (family : DisjointDistinctionFamily Index Carrier)
    (basis : Finset Index)
    (maximal : MaximalIndependent
      family.nativeReversalFinitaryClosure (Finset.univ : Finset Index) basis) :
    basis.card =
      (family.nativeReversalFinitaryClosure).rank Finset.univ ∧
      (family.nativeReversalFinitaryClosure).rank Finset.univ =
        symmetryAlgebraLogRank family := by
  constructor
  · rw [family.nativeReversal_maximalIndependent_card_eq_index_card basis maximal,
      family.nativeReversalFinitaryClosure_rank_eq_card]
    exact (Finset.card_univ).symm
  · exact family.nativeReversalFinitaryClosure_rank_univ_eq_action_log_rank

/-! A compact finite emergence statement: when a new primitive index is not
in the observed native seed, its addition contributes exactly one new
independent direction in the selected native model. -/
theorem nativeReversal_new_primitive_index_adds_one_rank
    (family : DisjointDistinctionFamily Index Carrier)
    (seed : Finset Index) (index : Index)
    (indexNotMember : index ∉ seed) :
    (family.nativeReversalFinitaryClosure).rank (insert index seed) =
      (family.nativeReversalFinitaryClosure).rank seed + 1 :=
  family.nativeReversalFinitaryClosure_rank_insert_eq_add_one_of_not_mem
    seed index indexNotMember

end DisjointDistinctionFamily

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
