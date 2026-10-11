import OCKIndividuationMSpaceComposition.SymmetryIntrinsicFinitaryRank
import OCKIndividuationMSpaceComposition.SymmetryFiniteCubeRankRealization

namespace OCKIndividuationMSpaceComposition

namespace IntrinsicFinitaryRank

/-!
# Generic finite rank composition laws

This module develops the finite-family laws of the existing
`FinitaryDistinctionClosure` without importing a native permutation product.
Rank monotonicity and subadditivity use only the hereditary independence
already proved from the closure interface.  Exchange is not needed for these
inequalities; it is needed by the separate rank-growth and basis results.

The subadditivity statement is deliberately for arbitrary overlapping finite
seeds.  Equality is therefore not asserted: overlap can make the inequality
strict.  A concrete one-coordinate Boolean realization witnesses that boundary.
The native disjoint-family additivity theorem remains a separate conditional
realization result and is not redefined here.
-/

universe uToken

variable {Token : Type uToken} [DecidableEq Token]

/-! ## Monotonicity -/

/-- Enlarging the observed finite seed cannot lower its closure rank. -/
theorem FinitaryDistinctionClosure.rank_mono
    (closure : FinitaryDistinctionClosure Token)
    {first second : Finset Token}
    (subset : first ⊆ second) :
    closure.rank first ≤ closure.rank second := by
  rcases closure.exists_independent_rank_witness first with
    ⟨family, familySubset, independent, familyCard⟩
  rw [← familyCard]
  exact closure.independent_card_le_rank
    (familySubset.trans subset) independent

/-! ## Subadditivity for arbitrary overlap -/

/-- The two parts of an independent family cut by `first` remain independent,
    and their cardinalities bound the two corresponding ranks. -/
theorem FinitaryDistinctionClosure.independent_inter_sdiff_rank_bounds
    (closure : FinitaryDistinctionClosure Token)
    {family first second : Finset Token}
    (familySubset : family ⊆ first ∪ second)
    (independent : closure.Independent family) :
    (family ∩ first).card ≤ closure.rank first ∧
      (family \ first).card ≤ closure.rank second := by
  have leftIndependent : closure.Independent (family ∩ first) :=
    independent.mono Finset.inter_subset_left
  have leftBound : (family ∩ first).card ≤ closure.rank first :=
    closure.independent_card_le_rank Finset.inter_subset_right leftIndependent
  have rightIndependent : closure.Independent (family \ first) :=
    independent.mono Finset.sdiff_subset
  have rightSubset : family \ first ⊆ second := by
    intro token tokenMember
    have tokenInUnion : token ∈ first ∪ second :=
      familySubset (Finset.mem_sdiff.mp tokenMember).1
    rcases Finset.mem_union.mp tokenInUnion with tokenInFirst | tokenInSecond
    · exact (Finset.mem_sdiff.mp tokenMember).2 tokenInFirst |>.elim
    · exact tokenInSecond
  have rightBound : (family \ first).card ≤ closure.rank second :=
    closure.independent_card_le_rank rightSubset rightIndependent
  exact ⟨leftBound, rightBound⟩

/-- Rank is subadditive on the union of any two finite observed seeds.  The
    proof partitions a maximal independent witness into its intersection with
    `first` and its difference from `first`; no disjointness or exchange
    premise is smuggled into the statement. -/
theorem FinitaryDistinctionClosure.rank_union_subadditive
    (closure : FinitaryDistinctionClosure Token)
    (first second : Finset Token) :
    closure.rank (first ∪ second) ≤
      closure.rank first + closure.rank second := by
  rcases closure.exists_independent_rank_witness (first ∪ second) with
    ⟨family, familySubset, independent, familyCard⟩
  have bounds := closure.independent_inter_sdiff_rank_bounds
    (familySubset := familySubset) independent
  have partition := Finset.card_inter_add_card_sdiff family first
  rw [← familyCard]
  rw [← partition]
  exact Nat.add_le_add bounds.1 bounds.2

/-- Equality is recovered only when explicit rank-attaining witnesses from the
    two sides are disjoint and their union is independent in the same closure.
    These hypotheses are a realization criterion, not a consequence of seed
    overlap or of the native disjoint-family theorem. -/
theorem FinitaryDistinctionClosure.rank_union_eq_add_of_independent_rank_witnesses
    (closure : FinitaryDistinctionClosure Token)
    (first second left right : Finset Token)
    (leftSubset : left ⊆ first)
    (rightSubset : right ⊆ second)
    (disjoint : Disjoint left right)
    (unionIndependent : closure.Independent (left ∪ right))
    (leftRank : left.card = closure.rank first)
    (rightRank : right.card = closure.rank second) :
    closure.rank (first ∪ second) =
      closure.rank first + closure.rank second := by
  have lower : closure.rank first + closure.rank second ≤
      closure.rank (first ∪ second) := by
    rw [← leftRank, ← rightRank,
      ← Finset.card_union_of_disjoint disjoint]
    exact closure.independent_card_le_rank
      (Finset.union_subset_union leftSubset rightSubset) unionIndependent
  exact Nat.le_antisymm
    (closure.rank_union_subadditive first second) lower

/-! ## Overlap boundary: equality need not hold -/

/-- In the one-coordinate Boolean realization, the same singleton family on
    both sides overlaps completely, so union rank is one while the sum of
    ranks is two. -/
theorem boolean_one_coordinate_overlap_strict :
    let family :=
      FiniteCubeRankRealization.fullCoordinateFamily (Index := Fin 1)
    BooleanCompositionRank.booleanGeneratedClosure.rank (family ∪ family) <
      BooleanCompositionRank.booleanGeneratedClosure.rank family +
        BooleanCompositionRank.booleanGeneratedClosure.rank family := by
  dsimp
  rw [Finset.union_self]
  have familyRank :
      BooleanCompositionRank.booleanGeneratedClosure.rank
          (FiniteCubeRankRealization.fullCoordinateFamily (Index := Fin 1)) =
        (FiniteCubeRankRealization.fullCoordinateFamily (Index := Fin 1)).card :=
    FiniteCubeRankRealization.rank_eq_card_of_independent _
      FiniteCubeRankRealization.fullCoordinateFamily_independent
  rw [familyRank]
  rw [FiniteCubeRankRealization.fullCoordinateFamily_card]
  decide

end IntrinsicFinitaryRank

end OCKIndividuationMSpaceComposition
