import OCKIndividuationMSpaceComposition.SymmetryNativeActionRank
import OCKIndividuationMSpaceComposition.SymmetryFiniteCubeRankRealization
import OCKIndividuationMSpaceComposition.SymmetryJointCompositionBoundary

namespace OCKIndividuationMSpaceComposition

universe uLeft uRight uCarrier

namespace PrimitiveDistinction

/-!
# Additive composition of already-realised Boolean symmetry families

The native action rank of a pairwise-disjoint finite family is additive under
disjoint union of the index families.  This is a conditional realization
theorem: the cross-support disjointness premise is what makes the two native
products commute and remain faithful.  The corresponding finite Boolean
closure is the existing exchange-bearing `booleanGeneratedClosure`; this file
only aligns its rank with the native product and does not call either rank an
intrinsic OC dimension.

Two negative boundaries are retained.  Overlapping primitive supports can fail
to commute, so they cannot be inserted into this disjoint product interface.
Separately, a joint-generation closure without exchange can have unequal
maximal-independent cardinalities, so no unique additive rank is justified
there.  These are obstruction witnesses, not claims that every overlap fails
or that disjointness is the only possible independence mechanism.
-/

namespace DisjointDistinctionFamily

variable {IndexLeft : Type uLeft} {IndexRight : Type uRight}
  {Carrier : Type uCarrier}

/-! ## Cross-family independence and disjoint-union realization -/

/-- Support disjointness is symmetric.  This elementary fact is kept local so
    the disjoint-union constructor does not inherit the finite-carrier
    parameters of the larger native-action namespace. -/
theorem supportsDisjoint_swap
    {left right : PrimitiveDistinction Carrier}
    (disjoint : SupportsDisjoint left right) :
    SupportsDisjoint right left := by
  rcases disjoint with ⟨firstFirst, firstSecond,
    secondFirst, secondSecond⟩
  exact ⟨firstFirst.symm, secondFirst.symm,
    firstSecond.symm, secondSecond.symm⟩

/-- Every distinction in one family has support disjoint from every
distinction in the other.  This is an explicit cross-family premise; it is not
inferred from the two internal family witnesses. -/
structure CrossSupportsDisjoint
    (left : DisjointDistinctionFamily IndexLeft Carrier)
    (right : DisjointDistinctionFamily IndexRight Carrier) : Prop where
  disjoint : ∀ (first : IndexLeft) (second : IndexRight),
    SupportsDisjoint (left.distinction first) (right.distinction second)

/-- The disjoint union of two native distinction families. -/
def sumFamily
    (left : DisjointDistinctionFamily IndexLeft Carrier)
    (right : DisjointDistinctionFamily IndexRight Carrier)
    (cross : CrossSupportsDisjoint left right) :
    DisjointDistinctionFamily (Sum IndexLeft IndexRight) Carrier where
  distinction := Sum.elim left.distinction right.distinction
  supportsDisjoint := by
    intro first second different
    cases first with
    | inl first =>
        cases second with
        | inl second =>
            apply left.supportsDisjoint
            intro equality
            apply different
            cases equality
            rfl
        | inr second =>
            exact cross.disjoint first second
    | inr first =>
        cases second with
        | inl second =>
            exact supportsDisjoint_swap (cross.disjoint second first)
        | inr second =>
            apply right.supportsDisjoint
            intro equality
            apply different
            cases equality
            rfl

/-/ The native logarithmic rank counts the two finite index families additively
    after the cross-disjoint union. -/
theorem sumFamily_symmetryAlgebraLogRank_additive
    [Fintype IndexLeft] [DecidableEq IndexLeft]
    [Fintype IndexRight] [DecidableEq IndexRight]
    [Fintype Carrier] [DecidableEq Carrier]
    (left : DisjointDistinctionFamily IndexLeft Carrier)
    (right : DisjointDistinctionFamily IndexRight Carrier)
    (cross : CrossSupportsDisjoint left right) :
    symmetryAlgebraLogRank (sumFamily left right cross) =
      symmetryAlgebraLogRank left + symmetryAlgebraLogRank right := by
  rw [symmetryAlgebraLogRank_eq_card,
    symmetryAlgebraLogRank_eq_card,
    symmetryAlgebraLogRank_eq_card]
  simp only [Fintype.card_sum]

/-/ The same additive count is obtained by the existing finite Boolean closure,
    whose `FinitaryDistinctionClosure` explicitly carries exchange. -/
theorem sumFamily_native_rank_eq_boolean_exchange_rank
    [Fintype IndexLeft] [DecidableEq IndexLeft]
    [Fintype IndexRight] [DecidableEq IndexRight]
    [Fintype Carrier] [DecidableEq Carrier]
    (left : DisjointDistinctionFamily IndexLeft Carrier)
    (right : DisjointDistinctionFamily IndexRight Carrier)
    (cross : CrossSupportsDisjoint left right) :
    symmetryAlgebraLogRank (sumFamily left right cross) =
      BooleanCompositionRank.booleanGeneratedClosure.rank
        (FiniteCubeRankRealization.fullCoordinateFamily
          (Index := Sum IndexLeft IndexRight)) := by
  rw [symmetryAlgebraLogRank_eq_card,
    FiniteCubeRankRealization.booleanGeneratedClosure_fullCoordinateFamily_rank]

/-! ## Overlap obstruction -/

def fin3OverlapLeft : PrimitiveDistinction (Fin 3) :=
  ⟨0, 1, by decide⟩

def fin3OverlapRight : PrimitiveDistinction (Fin 3) :=
  ⟨1, 2, by decide⟩

theorem fin3_overlap_not_supportsDisjoint :
    ¬ SupportsDisjoint fin3OverlapLeft fin3OverlapRight := by
  intro disjoint
  exact disjoint.2.2.1 rfl

theorem fin3_overlap_not_commuting :
    ¬ Function.Commute fin3OverlapLeft.pairSwap
      fin3OverlapRight.pairSwap := by
  simpa [fin3OverlapLeft, fin3OverlapRight] using
    fin3_overlap_pairSwaps_noncommute

/-- A concrete overlap simultaneously violates the cross-disjoint premise and
the commuting-transposition requirement. -/
theorem fin3_overlap_product_boundary :
    ¬ SupportsDisjoint fin3OverlapLeft fin3OverlapRight ∧
      ¬ Function.Commute fin3OverlapLeft.pairSwap
        fin3OverlapRight.pairSwap := by
  constructor
  · exact fin3_overlap_not_supportsDisjoint
  · exact fin3_overlap_not_commuting

/-! ## No-exchange obstruction to intrinsic rank composition -/

open JointCompositionBoundary

/-- The existing two-root closure supplies joint generation and the ordinary
closure laws, but without exchange it has two unequal maximal-independent
cardinalities.  Thus an intrinsic additive rank cannot be read off from this
interface without an explicit exchange/rank principle. -/
theorem twoRoot_no_exchange_rank_boundary :
    (∀ seed : Finset TwoRootToken, seed ⊆ twoRootClosure seed) ∧
    (∀ {first second : Finset TwoRootToken}, first ⊆ second →
      twoRootClosure first ⊆ twoRootClosure second) ∧
    (∀ seed : Finset TwoRootToken,
      twoRootClosure (twoRootClosure seed) = twoRootClosure seed) ∧
    twoRootJointPremise.jointGenerated ({0, 1} : Finset TwoRootToken) 2 ∧
    ¬ ExchangeLaw twoRootClosure ∧
    OrdinaryMaximalIndependent twoRootClosure ({0, 2} : Finset TwoRootToken) ∧
    OrdinaryMaximalIndependent twoRootClosure ({1, 2, 3} : Finset TwoRootToken) ∧
    ({0, 2} : Finset TwoRootToken).card ≠
      ({1, 2, 3} : Finset TwoRootToken).card := by
  exact ⟨twoRootClosure_extensive,
    twoRootClosure_monotone,
    twoRootClosure_idempotent,
    twoRoot_target_is_joint,
    twoRootClosure_fails_exchange,
    twoRoot_maximal_independent_first,
    twoRoot_maximal_independent_second,
    twoRoot_maximal_independent_cardinals_differ⟩

end DisjointDistinctionFamily

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
