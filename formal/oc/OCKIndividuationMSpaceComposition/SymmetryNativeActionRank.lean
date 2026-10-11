import OCKIndividuationMSpaceComposition.SymmetryDisjointDistinctionDimension
import OCKIndividuationMSpaceComposition.SymmetryPermutationRankBridge
import OCKIndividuationMSpaceComposition.SymmetryIntrinsicFinitaryRank
import Mathlib.Data.Nat.Log

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier

namespace PrimitiveDistinction

/-!
# Rank of a native finite reversal algebra

The disjoint-family construction already produces actual ambient
permutations, not merely formal coordinate labels.  This file records the
smallest rank statement that can be read directly from that action.

For a finite family of pairwise-disjoint primitive distinctions, the image of
the Boolean mask action has cardinality `2 ^ |Index|`.  We therefore define its
*action logarithmic rank* as `log₂` of that image cardinality and prove that it
is exactly the number of independent local reversals.  The definition is
explicitly a rank of the realised symmetry algebra; it is not silently
declared to be the full intrinsic OC dimension.

The extension theorem then gives a strict growth result: adjoining one new
primitive distinction whose two-point support is disjoint from every existing
support increases this action rank by exactly one.  The only new premise is
the concrete disjointness witness needed to make the corresponding ambient
transposition commute and remain detectable.
-/

namespace DisjointDistinctionFamily

variable {Index : Type uIndex} {Carrier : Type uCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]

/-! ## The realised action rank -/

noncomputable def symmetryAlgebraLogRank
    (family : DisjointDistinctionFamily Index Carrier) : Nat :=
  Nat.log 2 (Set.ncard (Set.range family.maskPermutationProduct))

theorem symmetryAlgebraLogRank_eq_card
    (family : DisjointDistinctionFamily Index Carrier) :
    symmetryAlgebraLogRank family = Fintype.card Index := by
  unfold symmetryAlgebraLogRank
  rw [family.card_maskPermutationProduct_range]
  exact Nat.log_pow (by decide) _

/-! The realised permutation rank and the finite Boolean-closure rank count
the same independent coordinates.  This is a representation bridge only;
it does not identify either presentation with intrinsic OC dimension. -/
theorem symmetryAlgebraLogRank_eq_maskPresentationRank
    (family : DisjointDistinctionFamily Index Carrier) :
    symmetryAlgebraLogRank family =
      DisjointPermutationRankBridge.maskPresentationRank (Index := Index) := by
  rw [symmetryAlgebraLogRank_eq_card,
    DisjointPermutationRankBridge.maskPresentationRank_eq_card_index]

theorem symmetryAlgebraLogRank_fin_zero :
    symmetryAlgebraLogRank
      (Index := Fin 0) (Carrier := Fin 0)
      ({ distinction := fun index => by
          exact Fin.elim0 index
         supportsDisjoint := by
          intro first second different
          exact Fin.elim0 first } :
        DisjointDistinctionFamily (Fin 0) (Fin 0)) = 0 := by
  rw [symmetryAlgebraLogRank_eq_card]
  decide

/-! ## Adjoining one genuinely new disjoint reversal -/

theorem supportsDisjoint_symm
    {left right : PrimitiveDistinction Carrier}
    (disjoint : SupportsDisjoint left right) :
    SupportsDisjoint right left := by
  rcases disjoint with ⟨firstFirst, firstSecond, secondFirst, secondSecond⟩
  exact ⟨firstFirst.symm, secondFirst.symm, firstSecond.symm,
    secondSecond.symm⟩

def adjoinDisjoint
    (family : DisjointDistinctionFamily Index Carrier)
    (newDistinction : PrimitiveDistinction Carrier)
    (newDisjoint : ∀ index,
      SupportsDisjoint (family.distinction index) newDistinction) :
    DisjointDistinctionFamily (Option Index) Carrier where
  distinction := fun index =>
    match index with
    | none => newDistinction
    | some index => family.distinction index
  supportsDisjoint := by
    intro first second different
    cases first with
    | none =>
        cases second with
        | none => exact (different rfl).elim
        | some index => exact supportsDisjoint_symm (newDisjoint index)
    | some index =>
        cases second with
        | none => exact newDisjoint index
        | some other =>
            change SupportsDisjoint
              (family.distinction index) (family.distinction other)
            exact family.supportsDisjoint (by
              intro indexEq
              apply different
              cases indexEq
              rfl)

theorem symmetryAlgebraLogRank_adjoinDisjoint_eq_succ
    (family : DisjointDistinctionFamily Index Carrier)
    (newDistinction : PrimitiveDistinction Carrier)
    (newDisjoint : ∀ index,
      SupportsDisjoint (family.distinction index) newDistinction) :
    symmetryAlgebraLogRank
        (adjoinDisjoint family newDistinction newDisjoint) =
      symmetryAlgebraLogRank family + 1 := by
  rw [symmetryAlgebraLogRank_eq_card,
    symmetryAlgebraLogRank_eq_card]
  simp

/-! ## Interpretation boundary -/

theorem symmetryAlgebraLogRank_strict_growth_boundary
    (family : DisjointDistinctionFamily Index Carrier)
    (newDistinction : PrimitiveDistinction Carrier)
    (newDisjoint : ∀ index,
      SupportsDisjoint (family.distinction index) newDistinction) :
    symmetryAlgebraLogRank family <
      symmetryAlgebraLogRank
        (adjoinDisjoint family newDistinction newDisjoint) := by
  rw [symmetryAlgebraLogRank_adjoinDisjoint_eq_succ]
  exact Nat.lt_succ_self _

end DisjointDistinctionFamily

/-! ## Boundary between realised action rank and intrinsic rank -/

namespace NativeIntrinsicRankBoundary

open IntrinsicFinitaryRank

universe uToken

variable {Token : Type uToken} [DecidableEq Token]
variable {Index : Type uIndex} {Carrier : Type uCarrier}
variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]

/-!
This interface makes the missing semantic identification explicit.  The
intrinsic closure must supply an independent finite seed, and the native
action must be related to that seed by an explicit cardinality correspondence.
No token-to-permutation semantics are smuggled in: without such a stronger
map, the theorem below is only a cardinality bridge, not an intrinsic
dimension theorem.
-/
structure CardinalityRealization where
  closure : FinitaryDistinctionClosure Token
  seed : Finset Token
  family : DisjointDistinctionFamily Index Carrier
  seedIndependent : closure.Independent seed
  seed_card_eq_index_card : seed.card = Fintype.card Index

theorem closure_rank_eq_seed_card
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier)) :
    realization.closure.rank realization.seed = realization.seed.card := by
  classical
  apply Nat.le_antisymm
  · unfold FinitaryDistinctionClosure.rank
    apply Finset.sup_le
    intro candidate candidateMember
    exact Finset.card_le_card
      (Finset.mem_powerset.mp (Finset.mem_filter.mp candidateMember).1)
  · exact FinitaryDistinctionClosure.independent_card_le_rank
      realization.closure (subset_refl _) realization.seedIndependent

/-! The rank agreement is conditional on the explicit realization interface.
The closure's exchange field is retained in the interface, but this theorem
does not claim that exchange follows from the native permutation action. -/
theorem intrinsic_rank_eq_native_action_log_rank
    (realization : CardinalityRealization (Token := Token)
      (Index := Index) (Carrier := Carrier)) :
    realization.closure.rank realization.seed =
      DisjointDistinctionFamily.symmetryAlgebraLogRank realization.family := by
  rw [closure_rank_eq_seed_card realization,
    DisjointDistinctionFamily.symmetryAlgebraLogRank_eq_card realization.family]
  exact realization.seed_card_eq_index_card

end NativeIntrinsicRankBoundary

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
