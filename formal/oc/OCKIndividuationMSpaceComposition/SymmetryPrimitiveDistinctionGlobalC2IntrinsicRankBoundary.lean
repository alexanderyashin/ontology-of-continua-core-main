import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionGlobalC2TorsorBoundary
import OCKIndividuationMSpaceComposition.SymmetryNativeActionRank
import OCKIndividuationMSpaceComposition.SymmetryNativeIntrinsicDimensionBridge
import OCKIndividuationMSpaceComposition.SymmetryRankZeroBoundary
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# Global C₂ and the first intrinsic-rank boundary

The covered-carrier theorem supplies a global free two-point torsor, while the
native finite-rank interface counts independent distinction generators.  These
are related only after an explicit realization is supplied.  This file gives
the smallest positive realization for one primitive pair and a concrete
negative model showing that the torsor fields alone do not determine a rank.

The positive result is not a definition of dimension: the one-element native
family, its subgroup closure, its independent seed, and the pointwise action
identification are all explicit.  The negative result uses the same covered
two-point carrier and its global torsor with an empty native family.  Hence a
global C₂ witness, without a generator/action correspondence or a closure
interface, cannot by itself imply positive intrinsic rank.
-/

open NativeIntrinsicRankBoundary

/-! ## Explicit one-generator realization on the ambient carrier -/

/-- The displayed primitive pair is the sole generator of a one-coordinate
native family.  Its support-disjointness obligation is vacuous for `Fin 1`. -/
noncomputable def globalPairNativeFamily
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    DisjointDistinctionFamily (Fin 1) Carrier where
  distinction := fun _ => distinction
  supportsDisjoint := by
    intro first second different
    exact (different (Subsingleton.elim _ _)).elim

/-- The explicit rank realization includes the independent seed and the
cardinality comparison needed by the intrinsic-rank bridge. -/
noncomputable def globalPairNativeRealization
    {Carrier : Type uCarrier} [Fintype Carrier] [DecidableEq Carrier]
    (distinction : PrimitiveDistinction Carrier) :
    CardinalityRealization (Token := Fin 1) (Index := Fin 1)
      (Carrier := Carrier) where
  closure := (globalPairNativeFamily distinction).nativeReversalFinitaryClosure
  seed := ({0} : Finset (Fin 1))
  family := globalPairNativeFamily distinction
  seedIndependent :=
    (globalPairNativeFamily distinction).nativeReversalFinitaryClosure_independent
      ({0} : Finset (Fin 1))
  seed_card_eq_index_card := by decide

theorem globalPairNativeRealization_seed_independent
    {Carrier : Type uCarrier} [Fintype Carrier] [DecidableEq Carrier]
    (distinction : PrimitiveDistinction Carrier) :
    (globalPairNativeRealization distinction).closure.Independent
      (globalPairNativeRealization distinction).seed := by
  exact (globalPairNativeRealization distinction).seedIndependent

theorem globalPairNativeRealization_rank_one
    {Carrier : Type uCarrier} [Fintype Carrier] [DecidableEq Carrier]
    (distinction : PrimitiveDistinction Carrier) :
    (globalPairNativeRealization distinction).closure.rank
        (globalPairNativeRealization distinction).seed = 1 := by
  rw [NativeIntrinsicRankBoundary.closure_rank_eq_seed_card]
  simp [globalPairNativeRealization]

theorem globalPairNativeRealization_action_rank_one
    {Carrier : Type uCarrier} [Fintype Carrier] [DecidableEq Carrier]
    (distinction : PrimitiveDistinction Carrier) :
    DisjointDistinctionFamily.symmetryAlgebraLogRank
        (globalPairNativeRealization distinction).family = 1 := by
  rw [DisjointDistinctionFamily.symmetryAlgebraLogRank_eq_card]
  decide

theorem globalPairNativeRealization_rank_eq_action_rank
    {Carrier : Type uCarrier} [Fintype Carrier] [DecidableEq Carrier]
    (distinction : PrimitiveDistinction Carrier) :
    (globalPairNativeRealization distinction).closure.rank
        (globalPairNativeRealization distinction).seed =
      DisjointDistinctionFamily.symmetryAlgebraLogRank
        (globalPairNativeRealization distinction).family := by
  exact NativeIntrinsicRankBoundary.intrinsic_rank_eq_native_action_log_rank
    (globalPairNativeRealization distinction)

/-- The native generator is exactly the canonical pair-swap, hence exactly the
reversal of the covered-carrier global torsor.  This is the explicit semantic
identification missing from the bare torsor interface. -/
theorem globalPairNativeFamily_pairSwap_matches_global_torsor
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) (point : Carrier) :
    pairSwapEquiv
        ((globalPairNativeFamily distinction).distinction (0 : Fin 1)) point =
      (pairSwapGlobalTorsor distinction covers).reverse point := by
  rfl

/-- Positive bounded spine: coverage gives the global torsor, and the explicit
one-generator native realization gives exactly one independent native rank. -/
theorem covered_global_c2_native_rank_one_spine
    {Carrier : Type uCarrier} [Fintype Carrier] [DecidableEq Carrier]
    (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) :
    (∃ torsor : R3C2OrientationTorsorInterface Carrier Unit Unit,
      torsor.reverse = distinction.pairSwap) ∧
      (globalPairNativeRealization distinction).closure.Independent
        (globalPairNativeRealization distinction).seed ∧
      (globalPairNativeRealization distinction).closure.rank
        (globalPairNativeRealization distinction).seed = 1 ∧
      DisjointDistinctionFamily.symmetryAlgebraLogRank
        (globalPairNativeRealization distinction).family = 1 ∧
      (globalPairNativeRealization distinction).closure.rank
        (globalPairNativeRealization distinction).seed =
        DisjointDistinctionFamily.symmetryAlgebraLogRank
          (globalPairNativeRealization distinction).family ∧
      (∀ point : Carrier,
        pairSwapEquiv
            ((globalPairNativeFamily distinction).distinction (0 : Fin 1)) point =
          (pairSwapGlobalTorsor distinction covers).reverse point) := by
  refine ⟨⟨pairSwapGlobalTorsor distinction covers, rfl⟩, ?_, ?_, ?_, ?_, ?_⟩
  · exact globalPairNativeRealization_seed_independent distinction
  · exact globalPairNativeRealization_rank_one distinction
  · exact globalPairNativeRealization_action_rank_one distinction
  · exact globalPairNativeRealization_rank_eq_action_rank distinction
  · intro point
    exact globalPairNativeFamily_pairSwap_matches_global_torsor distinction
      covers point

/-! ## A concrete no-go: torsor fields do not choose a native closure -/

/-- The canonical covered pair on `Fin 2`. -/
def twoPointDistinction : PrimitiveDistinction (Fin 2) where
  first := 0
  second := 1
  separated := by decide

theorem twoPointDistinction_covers :
    twoPointDistinction.CoversCarrier := by
  intro point
  fin_cases point <;> simp [twoPointDistinction]

noncomputable def twoPointGlobalTorsor :
    R3C2OrientationTorsorInterface (Fin 2) Unit Unit :=
  pairSwapGlobalTorsor twoPointDistinction twoPointDistinction_covers

/-- An empty native family on the same two-point carrier.  It is a genuine
native closure, but it contains no generator to correspond to the torsor. -/
def emptyNativeFamily : DisjointDistinctionFamily (Fin 0) (Fin 2) where
  distinction := fun index => Fin.elim0 index
  supportsDisjoint := by
    intro first second different
    exact Fin.elim0 first

theorem emptyNativeFamily_rank_zero :
    (emptyNativeFamily.nativeReversalFinitaryClosure).rank
        (∅ : Finset (Fin 0)) = 0 := by
  rw [DisjointDistinctionFamily.nativeReversalFinitaryClosure_rank_eq_card]
  simp

/-- A global C₂ torsor can coexist with a zero-generator native realization;
the missing premise is a nonempty/action-corresponding generator family. -/
theorem global_c2_does_not_force_positive_native_rank :
    (∃ torsor : R3C2OrientationTorsorInterface (Fin 2) Unit Unit,
      torsor.reverse = twoPointDistinction.pairSwap) ∧
      (emptyNativeFamily.nativeReversalFinitaryClosure).rank
          (∅ : Finset (Fin 0)) = 0 := by
  exact ⟨⟨twoPointGlobalTorsor, rfl⟩, emptyNativeFamily_rank_zero⟩

/-! The preceding witness is not a claim that the empty family represents the
pair.  It is precisely the boundary model: the same torsor data admits no
rank conclusion until the native family and its correspondence are supplied. -/

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
