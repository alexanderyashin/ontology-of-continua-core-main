import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionC2Boundary
import OCKIndividuationMSpaceComposition.SymmetryFiniteCubeRankRealization
import Mathlib.Data.Fin.Basic
import Mathlib.Data.Finset.Basic
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uIndex

namespace IntrinsicRankFiniteWitnesses

/-!
# Finite rank witnesses and the exact emergence boundary

The preceding closure modules establish two different facts that must not be
merged.  A native causal kernel is singleton-generated, so it cannot supply a
joint direction.  A Boolean reversible composition supplies an exchange
closure, and therefore a finite relative rank.  This file records concrete
rank `0`, `1`, `2`, and `3` witnesses for that latter realization and exposes
the strict-growth theorem as a consequence of non-generation.

The rank in this file is the relative rank of the supplied Boolean-composition
realization.  It is not silently promoted to an intrinsic OC dimension: the
composition law, finite universe, and coordinate family remain explicit
realization data.  Thus the file advances the dimension programme while
preserving the exact boundary between a proved realization and the still-open
question of which OC-native law should be selected.
-/

/-! ## A concrete local source for the finite coordinate family -/

/-- The canonical two-point primitive used by the finite realization. -/
def binaryPrimitiveDistinction : PrimitiveDistinction (Fin 2) where
  first := 0
  second := 1
  separated := by decide

/-- Every finite coordinate is supplied by the same local two-point axis.
This is a realization witness, not an assumption in the intrinsic theory. -/
def binaryAxisFamily (Index : Type uIndex) :
    PrimitiveDistinctionFamily Index (fun _ => Fin 2) :=
  fun _ => binaryPrimitiveDistinction

/-! ## Rank in the Boolean-composition realization -/

variable {Index : Type uIndex} [Fintype Index]

/-- The relative rank of the full singleton-support family. -/
noncomputable def standardCoordinateRank : Nat :=
  BooleanCompositionRank.booleanGeneratedClosure.rank
    (FiniteCubeRankRealization.fullCoordinateFamily (Index := Index))

/-- The finite Boolean realization has one independent reversible direction per
coordinate. -/
theorem standardCoordinateRank_eq_card :
    standardCoordinateRank (Index := Index) = Fintype.card Index := by
  exact FiniteCubeRankRealization.booleanGeneratedClosure_fullCoordinateFamily_rank

theorem standardCoordinateRank_fin_zero :
    standardCoordinateRank (Index := Fin 0) = 0 := by
  simpa using (standardCoordinateRank_eq_card (Index := Fin 0))

theorem standardCoordinateRank_fin_one :
    standardCoordinateRank (Index := Fin 1) = 1 := by
  simpa using (standardCoordinateRank_eq_card (Index := Fin 1))

theorem standardCoordinateRank_fin_two :
    standardCoordinateRank (Index := Fin 2) = 2 := by
  simpa using (standardCoordinateRank_eq_card (Index := Fin 2))

theorem standardCoordinateRank_fin_three :
    standardCoordinateRank (Index := Fin 3) = 3 := by
  simpa using (standardCoordinateRank_eq_card (Index := Fin 3))

/-! ## The non-generation event is exactly a strict rank increase here -/

theorem standard_nonGenerated_strict_rank_growth
    (seed : Finset (FiniteCubeRankRealization.BooleanMask Index))
    (token : FiniteCubeRankRealization.BooleanMask Index)
    (notGenerated : token ∉
      BooleanCompositionRank.generatedClose seed) :
    BooleanCompositionRank.booleanGeneratedClosure.rank (insert token seed) >
      BooleanCompositionRank.booleanGeneratedClosure.rank seed := by
  rw [BooleanCompositionRank.rank_insert_eq_add_one_of_not_generated
    seed token notGenerated]
  omega

/-! ## Faithfulness ties the realization back to primitive distinctions -/

theorem binary_mask_action_faithful (Index : Type uIndex) [Fintype Index] :
    Function.Injective
      (fun token : FiniteCubeRankRealization.BooleanMask Index =>
        maskAction (binaryAxisFamily Index) (Multiplicative.toAdd token)) := by
  exact FiniteCubeRankRealization.maskAction_faithful
    (binaryAxisFamily Index)

/-!
The four finite values above are therefore explicit realization witnesses.
They do not close the intrinsic-selection problem: a future OC theorem must
still identify which native composition feeds the Boolean closure, or prove a
different rank calculus and its boundary.
-/

end IntrinsicRankFiniteWitnesses

end OCKIndividuationMSpaceComposition
