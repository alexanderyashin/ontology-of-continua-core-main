import OCKIndividuationMSpaceComposition.SymmetryTwoPlaneExchangeNaturality
import Mathlib.Data.Finset.Card
import Mathlib.Data.Fintype.Pi

namespace OCKIndividuationMSpaceComposition

universe uLeft uRight

namespace PrimitiveDistinction

/-!
# The concrete two-plane symmetry algebra

The preceding two-plane files establish two generated Boolean coordinates and
their exchange naturality.  This file closes the corresponding finite algebra
without introducing a bundled group as a new premise: a mask is simply a pair
of Booleans, and its action is the coordinatewise XOR action on `Bool × Bool`.

The algebraic laws are therefore proved from Boolean arithmetic.  The two
primitive plane reversals are identified with the two singleton masks, their
composite with the `(true, true)` mask, and the four resulting transformations
are shown to be distinct.  This is a concrete `C₂ × C₂`/Klein-four
realisation of the already-generated product plane; it is not a claim that an
arbitrary OC carrier has this global symmetry algebra.
-/

abbrev PlaneCoordinate := Bool × Bool

/-- Coordinatewise XOR translation of the two-point Boolean plane. -/
def planeMaskAction (mask point : PlaneCoordinate) : PlaneCoordinate :=
  (Bool.xor mask.1 point.1, Bool.xor mask.2 point.2)

/-- The identity mask. -/
def planeZeroMask : PlaneCoordinate := (false, false)

/-- The singleton mask for the first coordinate. -/
def planeFirstMask : PlaneCoordinate := (true, false)

/-- The singleton mask for the second coordinate. -/
def planeSecondMask : PlaneCoordinate := (false, true)

/-- The simultaneous mask. -/
def planeBothMask : PlaneCoordinate := (true, true)

theorem planeMaskAction_zero (point : PlaneCoordinate) :
    planeMaskAction planeZeroMask point = point := by
  rcases point with ⟨first, second⟩
  simp [planeMaskAction, planeZeroMask]

theorem planeMaskAction_self (mask point : PlaneCoordinate) :
    planeMaskAction mask (planeMaskAction mask point) = point := by
  rcases mask with ⟨maskFirst, maskSecond⟩
  rcases point with ⟨first, second⟩
  cases maskFirst <;> cases maskSecond <;>
    cases first <;> cases second <;> rfl

theorem planeMaskAction_comp
    (first second point : PlaneCoordinate) :
    planeMaskAction first (planeMaskAction second point) =
      planeMaskAction
        (Bool.xor first.1 second.1, Bool.xor first.2 second.2) point := by
  rcases first with ⟨firstFirst, firstSecond⟩
  rcases second with ⟨secondFirst, secondSecond⟩
  rcases point with ⟨pointFirst, pointSecond⟩
  cases firstFirst <;> cases firstSecond <;>
    cases secondFirst <;> cases secondSecond <;>
      cases pointFirst <;> cases pointSecond <;> rfl

theorem planeMaskAction_commute
    (first second point : PlaneCoordinate) :
    planeMaskAction first (planeMaskAction second point) =
      planeMaskAction second (planeMaskAction first point) := by
  rw [planeMaskAction_comp, planeMaskAction_comp]
  rcases first with ⟨firstFirst, firstSecond⟩
  rcases second with ⟨secondFirst, secondSecond⟩
  rcases point with ⟨pointFirst, pointSecond⟩
  cases firstFirst <;> cases firstSecond <;>
    cases secondFirst <;> cases secondSecond <;>
      cases pointFirst <;> cases pointSecond <;> rfl

theorem planeMaskAction_involutive (mask : PlaneCoordinate) :
    Function.Involutive (planeMaskAction mask) := by
  intro point
  exact planeMaskAction_self mask point

theorem planeMaskAction_injective :
    Function.Injective
      (fun mask : PlaneCoordinate => planeMaskAction mask) := by
  intro first second equal
  have atZero := congrArg (fun action => action planeZeroMask) equal
  simpa [planeMaskAction, planeZeroMask] using atZero

theorem planeMaskAction_first_second_comp (point : PlaneCoordinate) :
    planeMaskAction planeFirstMask
        (planeMaskAction planeSecondMask point) =
      planeMaskAction planeBothMask point := by
  simpa [planeFirstMask, planeSecondMask, planeBothMask] using
    (planeMaskAction_comp planeFirstMask planeSecondMask point)

theorem planeMaskAction_second_first_comp (point : PlaneCoordinate) :
    planeMaskAction planeSecondMask
        (planeMaskAction planeFirstMask point) =
      planeMaskAction planeBothMask point := by
  simpa [planeSecondMask, planeFirstMask, planeBothMask] using
    (planeMaskAction_comp planeSecondMask planeFirstMask point)

/-- The complete finite set of Boolean masks for two coordinates.  It is
written explicitly so the result does not depend on a hidden finite-instance
or on an ambient carrier enumeration. -/
def planeMaskSet : Finset PlaneCoordinate :=
  {(false, false), (true, false), (false, true), (true, true)}

/-- The four mask actions form a finite family of four distinct maps. -/
noncomputable def planeMaskActionFamily :
    Finset (PlaneCoordinate → PlaneCoordinate) := by
  classical
  exact planeMaskSet.image planeMaskAction

theorem planeMaskActionFamily_card :
    planeMaskActionFamily.card = 4 := by
  classical
  rw [planeMaskActionFamily]
  rw [Finset.card_image_of_injective
    (s := planeMaskSet)
    (f := fun mask : PlaneCoordinate => planeMaskAction mask)
    planeMaskAction_injective]
  decide

theorem planeMaskAction_four_distinct :
    (planeMaskActionFamily.card = 4) :=
  planeMaskActionFamily_card

/-! ## Readback from two generated OC axes -/

theorem generatedPlane_first_as_mask
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right)
    (point : PrimitiveDistinctionPlane left right) :
    left.generatedPlaneEquivBoolProduct right
        ((left.firstPlaneInvolution right).action point) =
      planeMaskAction planeFirstMask
        (left.generatedPlaneEquivBoolProduct right point) := by
  rw [generatedPlane_first_coordinate_reversal]
  rcases left.generatedPlaneEquivBoolProduct right point with ⟨first, second⟩
  cases first <;> cases second <;> rfl

theorem generatedPlane_second_as_mask
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right)
    (point : PrimitiveDistinctionPlane left right) :
    left.generatedPlaneEquivBoolProduct right
        ((left.secondPlaneInvolution right).action point) =
      planeMaskAction planeSecondMask
        (left.generatedPlaneEquivBoolProduct right point) := by
  rw [generatedPlane_second_coordinate_reversal]
  rcases left.generatedPlaneEquivBoolProduct right point with ⟨first, second⟩
  cases first <;> cases second <;> rfl

theorem generatedPlane_composite_as_both_mask
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right)
    (point : PrimitiveDistinctionPlane left right) :
    left.generatedPlaneEquivBoolProduct right
        ((left.firstPlaneInvolution right).action
          ((left.secondPlaneInvolution right).action point)) =
      planeMaskAction planeBothMask
        (left.generatedPlaneEquivBoolProduct right point) := by
  rw [generatedPlane_first_coordinate_reversal,
    generatedPlane_second_coordinate_reversal]
  rcases left.generatedPlaneEquivBoolProduct right point with ⟨first, second⟩
  cases first <;> cases second <;> rfl

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
