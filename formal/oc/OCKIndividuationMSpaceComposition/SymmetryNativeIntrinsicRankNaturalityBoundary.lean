import OCKIndividuationMSpaceComposition.SymmetryNativeFamilyNaturalityBoundary

namespace OCKIndividuationMSpaceComposition

universe uToken uIndex uNewIndex uCarrier uTargetCarrier

namespace PrimitiveDistinction

namespace NativeIntrinsicRankNaturalityBoundary

open DisjointDistinctionFamily
open IntrinsicFinitaryRank
open NativeFamilyNaturalityBoundary
open NativeIntrinsicRankBoundary

variable {Token : Type uToken} [DecidableEq Token]
variable {Index : Type uIndex} {NewIndex : Type uNewIndex}
variable {Carrier : Type uCarrier} {TargetCarrier : Type uTargetCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype NewIndex] [DecidableEq NewIndex]
variable [Fintype Carrier] [DecidableEq Carrier]
variable [Fintype TargetCarrier] [DecidableEq TargetCarrier]

/-!
# Naturality of an explicit intrinsic/native rank realization

`CardinalityRealization` is the deliberately conditional interface joining a
finite intrinsic closure to a concrete native reversal family.  The previous
family-naturality result transports the native family under independent index
and carrier equivalences, but does not yet state that the whole realization
interface survives that transport.  This file supplies that commuting
triangle.

The closure and its observed seed are kept unchanged.  The family is changed
only by the two explicit equivalences, and the seed-cardinality field is
transported through `Fintype.card_congr`.  Thus the intrinsic/native equality
continues to hold for the transported presentation, and its native action
rank agrees with the original presentation.

The result is a representation theorem for a supplied finite realization.  It
does not derive a closure/action correspondence from primitive distinction,
does not select a canonical equivalence, and does not identify finite native
rank with generic OC dimension.
 -/

def reindexedRealization
    (indexRelabel : NewIndex ≃ Index)
    (carrierRelabel : Carrier ≃ TargetCarrier)
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier)) :
    CardinalityRealization (Token := Token)
      (Index := NewIndex) (Carrier := TargetCarrier) where
  closure := realization.closure
  seed := realization.seed
  family := combinedFamily indexRelabel carrierRelabel realization.family
  seedIndependent := realization.seedIndependent
  seed_card_eq_index_card := by
    calc
      realization.seed.card = Fintype.card Index :=
        realization.seed_card_eq_index_card
      _ = Fintype.card NewIndex := (Fintype.card_congr indexRelabel).symm

theorem reindexedRealization_closure_rank_eq_original
    (indexRelabel : NewIndex ≃ Index)
    (carrierRelabel : Carrier ≃ TargetCarrier)
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier)) :
    (reindexedRealization indexRelabel carrierRelabel realization).closure.rank
        (reindexedRealization indexRelabel carrierRelabel realization).seed =
      realization.closure.rank realization.seed := by
  rfl

theorem reindexedRealization_intrinsic_rank_eq_combined_action
    (indexRelabel : NewIndex ≃ Index)
    (carrierRelabel : Carrier ≃ TargetCarrier)
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier)) :
    (reindexedRealization indexRelabel carrierRelabel realization).closure.rank
        (reindexedRealization indexRelabel carrierRelabel realization).seed =
      symmetryAlgebraLogRank
        (combinedFamily indexRelabel carrierRelabel realization.family) := by
  exact intrinsic_rank_eq_native_action_log_rank
    (reindexedRealization indexRelabel carrierRelabel realization)

/-- The transported realization forms a commuting rank triangle with the
original native family.  Both index and carrier correspondence remain
explicit inputs. -/
theorem reindexedRealization_intrinsic_rank_eq_original_action
    (indexRelabel : NewIndex ≃ Index)
    (carrierRelabel : Carrier ≃ TargetCarrier)
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier)) :
    (reindexedRealization indexRelabel carrierRelabel realization).closure.rank
        (reindexedRealization indexRelabel carrierRelabel realization).seed =
      symmetryAlgebraLogRank realization.family := by
  calc
    (reindexedRealization indexRelabel carrierRelabel realization).closure.rank
        (reindexedRealization indexRelabel carrierRelabel realization).seed =
        symmetryAlgebraLogRank
          (combinedFamily indexRelabel carrierRelabel realization.family) :=
      reindexedRealization_intrinsic_rank_eq_combined_action
        indexRelabel carrierRelabel realization
    _ = symmetryAlgebraLogRank realization.family :=
      combined_symmetryAlgebraLogRank_eq_original
        indexRelabel carrierRelabel realization.family

/-! This negative boundary exposes why the cardinality field is not cosmetic:
if a proposed closure/seed pair has a rank different from the finite index
cardinality, the native action rank cannot equal that intrinsic rank. -/
theorem rank_bridge_boundary_of_mismatched_cardinality
    (closure : FinitaryDistinctionClosure Token)
    (seed : Finset Token)
    (family : DisjointDistinctionFamily Index Carrier)
    (rank_mismatch : closure.rank seed ≠ Fintype.card Index) :
    closure.rank seed ≠ symmetryAlgebraLogRank family := by
  rw [symmetryAlgebraLogRank_eq_card]
  exact rank_mismatch

end NativeIntrinsicRankNaturalityBoundary

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
