import OCKIndividuationMSpaceComposition.SymmetryActionCorrespondence
import OCKIndividuationMSpaceComposition.SymmetryFinitaryRankComposition

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
# Additive rank through an explicit action correspondence

The generic finite rank theorem and the generator-to-native-action theorem
already exist separately.  This module composes them at one precise seam.
Two disjoint rank-attaining finite witnesses are required to form the realized
seed, their union must remain independent, and an explicit
`ActionCorrespondence` must identify every seed generator with its native
pair-swap.  Under exactly those premises, the additive closure rank equals the
correspondence action rank, which equals the native symmetry-algebra rank.

The result is a conditional finite realization theorem.  It does not derive
disjointness, exchange, an action correspondence, or a generic intrinsic OC
dimension from a bare distinction.  The existing cardinality-only
countermodel remains the boundary when the correspondence is absent.
-/

theorem correspondence_rank_composition_of_disjoint_rank_witnesses
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier))
    (tokenAction : SeedGenerator realization → Equiv.Perm Carrier)
    (correspondence : ActionCorrespondence realization tokenAction)
    (left right : Finset Token)
    (seed_eq : realization.seed = left ∪ right)
    (piecesDisjoint : Disjoint left right)
    (piecesIndependent : realization.closure.Independent (left ∪ right))
    (leftRank : left.card = realization.closure.rank left)
    (rightRank : right.card = realization.closure.rank right) :
    realization.closure.rank left + realization.closure.rank right =
        correspondenceActionLogRank realization tokenAction correspondence ∧
      correspondenceActionLogRank realization tokenAction correspondence =
        DisjointDistinctionFamily.symmetryAlgebraLogRank realization.family := by
  constructor
  · calc
      realization.closure.rank left + realization.closure.rank right =
          realization.closure.rank (left ∪ right) := by
        exact (realization.closure.rank_union_eq_add_of_independent_rank_witnesses
          left right left right
          (by intro token tokenMember; exact tokenMember)
          (by intro token tokenMember; exact tokenMember)
          piecesDisjoint piecesIndependent leftRank rightRank).symm
      _ = realization.closure.rank realization.seed := by rw [seed_eq]
      _ = correspondenceActionLogRank realization tokenAction correspondence :=
        intrinsic_rank_eq_correspondence_action_log_rank
          realization tokenAction correspondence
  · exact correspondenceActionLogRank_eq_native
      realization tokenAction correspondence

end NativeIntrinsicRankBoundary

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
