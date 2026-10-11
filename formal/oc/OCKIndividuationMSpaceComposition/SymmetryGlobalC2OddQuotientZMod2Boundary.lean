import OCKIndividuationMSpaceComposition.SymmetryGlobalC2OddQuotientExactness
import Mathlib.Data.ZMod.Basic

namespace OCKIndividuationMSpaceComposition

namespace PrimitiveDistinction

/-!
# Tightness witness for the odd quotient criterion

The exactness theorem is intentionally stated with a 2-torsion conclusion.
This file supplies a concrete finite countermodel showing that the
no-two-torsion hypothesis cannot be omitted: over `ZMod 2`, sign reversal is
the identity, so a nonzero anti-invariant observable can still factor through
the orientation-forgetting quotient.
-/

def boolDistinction : PrimitiveDistinction Bool where
  first := false
  second := true
  separated := by decide

theorem boolDistinction_covers : boolDistinction.CoversCarrier := by
  intro point
  cases point <;> simp [boolDistinction]

def boolZModTwoObservable : Bool → ZMod 2 := fun _ => 1

theorem boolZModTwoObservable_antiInvariant :
    CarrierAntiInvariant boolDistinction boolZModTwoObservable := by
  intro point
  cases point <;> norm_num [boolDistinction, boolZModTwoObservable,
    PrimitiveDistinction.pairSwap]

theorem boolZModTwoObservable_nonzero :
    boolZModTwoObservable false ≠ 0 := by
  norm_num [boolZModTwoObservable]

theorem boolZModTwoObservable_twoTorsion :
    ∀ point, 2 • boolZModTwoObservable point = 0 := by
  intro point
  cases point <;>
    change (1 : ZMod 2) + 1 = 0 <;>
    decide

theorem boolZModTwoObservable_factors_through_globalPairQuotient :
    ∃ factor : AxisQuotient
        (boolDistinction.pairSwapGlobalInvolution boolDistinction_covers) → ZMod 2,
      ∀ point,
        factor (axisClass
          (boolDistinction.pairSwapGlobalInvolution boolDistinction_covers) point) =
          boolZModTwoObservable point :=
  (boolDistinction.carrierAntiInvariant_factor_through_globalPairQuotient_iff_two_torsion
    boolDistinction_covers boolZModTwoObservable
    boolZModTwoObservable_antiInvariant).mpr
    boolZModTwoObservable_twoTorsion

theorem boolZModTwoObservable_nonzero_odd_factorization_boundary :
    boolZModTwoObservable false ≠ 0 ∧
      (∃ factor : AxisQuotient
          (boolDistinction.pairSwapGlobalInvolution boolDistinction_covers) → ZMod 2,
        ∀ point,
          factor (axisClass
            (boolDistinction.pairSwapGlobalInvolution boolDistinction_covers) point) =
            boolZModTwoObservable point) := by
  exact ⟨boolZModTwoObservable_nonzero,
    boolZModTwoObservable_factors_through_globalPairQuotient⟩

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
