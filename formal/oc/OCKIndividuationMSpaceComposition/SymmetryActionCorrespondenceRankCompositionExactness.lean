import OCKIndividuationMSpaceComposition.SymmetryActionCorrespondenceRankComposition
import OCKIndividuationMSpaceComposition.SymmetryFinitaryRankCompositionExactness

namespace OCKIndividuationMSpaceComposition

universe uToken uIndex uCarrier

namespace PrimitiveDistinction

namespace NativeIntrinsicRankBoundary

open IntrinsicFinitaryRank

variable {Token : Type uToken} [DecidableEq Token]
variable {Index : Type uIndex} {Carrier : Type uCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]

/-!
# Exact rank composition through an action correspondence

M48 supplied the forward composition theorem for explicitly given disjoint
rank-attaining witnesses.  This slice closes the adjacent exactness seam.
For any explicit `ActionCorrespondence` whose realized seed is `first ∪
second`, the correspondence action rank is always bounded above by the sum of
the two closure ranks.  Equality holds exactly when the existing finitary
closure admits disjoint rank-attaining witnesses from the two sides whose
union is independent.

The correspondence, seed equality, and exchange-based closure interface stay
explicit premises.  Nothing here derives an action from cardinality, turns a
finite realization into generic OC dimension, or proves disjointness from a
bare pair of families.
-/

theorem correspondence_action_rank_subadditive_of_seed_union
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction)
    (first second : Finset Token)
    (seed_eq : realization.seed = first ∪ second) :
    correspondenceActionLogRank realization tokenAction correspondence ≤
      realization.closure.rank first + realization.closure.rank second := by
  rw [correspondenceActionLogRank_eq_intrinsic_rank
    realization tokenAction correspondence, seed_eq]
  exact realization.closure.rank_union_subadditive first second

/--
The correspondence-aware equality criterion.  The right-hand side is the
precise finite witness condition supplied by the existing exchange closure;
it is not a definition of equality and does not assert a generic OC
dimension theorem.
-/
theorem correspondence_action_rank_eq_add_iff_disjoint_rank_witnesses
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction)
    (first second : Finset Token)
    (seed_eq : realization.seed = first ∪ second) :
    correspondenceActionLogRank realization tokenAction correspondence =
        realization.closure.rank first + realization.closure.rank second ↔
      ∃ left right : Finset Token,
        left ⊆ first ∧
        right ⊆ second ∧
        Disjoint left right ∧
        realization.closure.Independent (left ∪ right) ∧
        left.card = realization.closure.rank first ∧
        right.card = realization.closure.rank second := by
  rw [correspondenceActionLogRank_eq_intrinsic_rank
    realization tokenAction correspondence, seed_eq]
  exact rank_union_eq_add_iff_exists_disjoint_rank_witnesses
    realization.closure first second

end NativeIntrinsicRankBoundary

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
