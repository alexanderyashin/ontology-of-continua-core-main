import OCKIndividuationMSpaceComposition.SymmetryFinitaryRankComposition
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uToken

namespace IntrinsicFinitaryRank

/-!
# Exact finite criterion for additive composition

`rank_union_eq_add_of_independent_rank_witnesses` gives a sufficient
composition condition.  The converse is also available for the finite
exchange closure already present in the OC rank interface: if the union rank
is additive, a maximal independent witness for the union splits into a
rank-attaining witness on each side, and those two pieces remain independent
together.  Thus the equality is not a convention about disjointness; it is
equivalent to the existence of a genuine independent decomposition.
-/

variable {Token : Type uToken} [DecidableEq Token]

theorem rank_union_eq_add_iff_exists_disjoint_rank_witnesses
    (closure : FinitaryDistinctionClosure Token)
    (first second : Finset Token) :
    closure.rank (first ∪ second) =
        closure.rank first + closure.rank second ↔
      ∃ left right : Finset Token,
        left ⊆ first ∧
        right ⊆ second ∧
        Disjoint left right ∧
        closure.Independent (left ∪ right) ∧
        left.card = closure.rank first ∧
        right.card = closure.rank second := by
  constructor
  · intro additive
    rcases closure.exists_independent_rank_witness (first ∪ second) with
      ⟨family, familySubset, familyIndependent, familyCard⟩
    let left := family ∩ first
    let right := family \ first
    have leftSubset : left ⊆ first := by
      intro token tokenMember
      exact (Finset.mem_inter.mp tokenMember).2
    have rightSubset : right ⊆ second := by
      intro token tokenMember
      have tokenInUnion : token ∈ first ∪ second :=
        familySubset (Finset.mem_sdiff.mp tokenMember).1
      rcases Finset.mem_union.mp tokenInUnion with tokenInFirst | tokenInSecond
      · exact ((Finset.mem_sdiff.mp tokenMember).2 tokenInFirst).elim
      · exact tokenInSecond
    have piecesDisjoint : Disjoint left right := by
      apply Finset.disjoint_left.mpr
      intro token tokenInLeft tokenInRight
      exact (Finset.mem_sdiff.mp tokenInRight).2
        (Finset.mem_inter.mp tokenInLeft).2
    have piecesIndependent : closure.Independent (left ∪ right) := by
      have piecesUnion : left ∪ right = family := by
        ext token
        constructor
        · intro member
          rcases Finset.mem_union.mp member with member | member
          · exact (Finset.mem_inter.mp member).1
          · exact (Finset.mem_sdiff.mp member).1
        · intro member
          by_cases inFirst : token ∈ first
          · exact Finset.mem_union.mpr
              (Or.inl (Finset.mem_inter.mpr ⟨member, inFirst⟩))
          · exact Finset.mem_union.mpr
              (Or.inr (Finset.mem_sdiff.mpr ⟨member, inFirst⟩))
      rw [piecesUnion]
      exact familyIndependent
    have bounds := closure.independent_inter_sdiff_rank_bounds
      (familySubset := familySubset) familyIndependent
    have leftBound : left.card ≤ closure.rank first := by
      simpa [left] using bounds.1
    have rightBound : right.card ≤ closure.rank second := by
      simpa [right] using bounds.2
    have partition : left.card + right.card = family.card := by
      simpa [left, right] using
        (Finset.card_inter_add_card_sdiff family first).symm
    have piecesSum : left.card + right.card =
        closure.rank first + closure.rank second := by
      rw [partition, familyCard, additive]
    have leftCard : left.card = closure.rank first := by
      omega
    have rightCard : right.card = closure.rank second := by
      omega
    exact ⟨left, right, leftSubset, rightSubset, piecesDisjoint,
      piecesIndependent, leftCard, rightCard⟩
  · rintro ⟨left, right, leftSubset, rightSubset, piecesDisjoint,
      piecesIndependent, leftCard, rightCard⟩
    exact closure.rank_union_eq_add_of_independent_rank_witnesses
      first second left right leftSubset rightSubset piecesDisjoint
      piecesIndependent leftCard rightCard

end IntrinsicFinitaryRank

end OCKIndividuationMSpaceComposition
