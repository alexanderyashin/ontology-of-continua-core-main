import OCKIndividuationMSpaceComposition.SymmetryTwoPlaneCharacterDecomposition

import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

universe uValue

/-!
# Naturality under exchange of two symmetry planes

The two-plane character decomposition has a built-in covariance that must be
checked rather than assumed.  Exchanging the two Boolean coordinates fixes
the even/even and odd/odd characters and exchanges the two mixed characters.
The statements below are proved by the explicit orbit formulas, so the
relabeling does not introduce a hidden identification of the axes.
-/

section BooleanExchange

/-- Exchange the two coordinates of the four-state Boolean presentation. -/
def boolCoordinateSwap : Bool × Bool → Bool × Bool :=
  fun point => (point.2, point.1)

@[simp] theorem boolCoordinateSwap_involutive (point : Bool × Bool) :
    boolCoordinateSwap (boolCoordinateSwap point) = point := by
  rcases point with ⟨first, second⟩
  rfl

/-- Relabel an observable by exchanging its two coordinates. -/
def boolCoordinateSwapObservable {Value : Type uValue}
    (observable : Bool × Bool → Value) : Bool × Bool → Value :=
  fun point => observable (boolCoordinateSwap point)

theorem boolEvenEvenPart_swap
    {Value : Type uValue} [Field Value] [CharZero Value]
    (observable : Bool × Bool → Value) (point : Bool × Bool) :
    boolEvenEvenPart (boolCoordinateSwapObservable observable) point =
      boolEvenEvenPart observable (boolCoordinateSwap point) := by
  rcases point with ⟨first, second⟩
  cases first <;> cases second <;>
    simp [boolEvenEvenPart, boolCoordinateSwapObservable,
      boolCoordinateSwap, boolFlipFirst, boolFlipSecond] <;> ring

theorem boolOddOddPart_swap
    {Value : Type uValue} [Field Value] [CharZero Value]
    (observable : Bool × Bool → Value) (point : Bool × Bool) :
    boolOddOddPart (boolCoordinateSwapObservable observable) point =
      boolOddOddPart observable (boolCoordinateSwap point) := by
  rcases point with ⟨first, second⟩
  cases first <;> cases second <;>
    simp [boolOddOddPart, boolCoordinateSwapObservable,
      boolCoordinateSwap, boolFlipFirst, boolFlipSecond] <;> ring

theorem boolOddEvenPart_swap
    {Value : Type uValue} [Field Value] [CharZero Value]
    (observable : Bool × Bool → Value) (point : Bool × Bool) :
    boolOddEvenPart (boolCoordinateSwapObservable observable) point =
      boolEvenOddPart observable (boolCoordinateSwap point) := by
  rcases point with ⟨first, second⟩
  cases first <;> cases second <;>
    simp [boolOddEvenPart, boolEvenOddPart, boolCoordinateSwapObservable,
      boolCoordinateSwap, boolFlipFirst, boolFlipSecond] <;> ring

theorem boolEvenOddPart_swap
    {Value : Type uValue} [Field Value] [CharZero Value]
    (observable : Bool × Bool → Value) (point : Bool × Bool) :
    boolEvenOddPart (boolCoordinateSwapObservable observable) point =
      boolOddEvenPart observable (boolCoordinateSwap point) := by
  rcases point with ⟨first, second⟩
  cases first <;> cases second <;>
    simp [boolEvenOddPart, boolOddEvenPart, boolCoordinateSwapObservable,
      boolCoordinateSwap, boolFlipFirst, boolFlipSecond] <;> ring

/-- Exchange covariance for all four characters at once. -/
theorem bool_character_parts_exchange_natural
    {Value : Type uValue} [Field Value] [CharZero Value]
    (observable : Bool × Bool → Value) (point : Bool × Bool) :
    (boolEvenEvenPart (boolCoordinateSwapObservable observable) point =
        boolEvenEvenPart observable (boolCoordinateSwap point)) ∧
    (boolOddEvenPart (boolCoordinateSwapObservable observable) point =
        boolEvenOddPart observable (boolCoordinateSwap point)) ∧
    (boolEvenOddPart (boolCoordinateSwapObservable observable) point =
        boolOddEvenPart observable (boolCoordinateSwap point)) ∧
    (boolOddOddPart (boolCoordinateSwapObservable observable) point =
        boolOddOddPart observable (boolCoordinateSwap point)) := by
  exact ⟨boolEvenEvenPart_swap observable point,
    boolOddEvenPart_swap observable point,
    boolEvenOddPart_swap observable point,
    boolOddOddPart_swap observable point⟩

end BooleanExchange

section PrimitivePlaneExchange

namespace PrimitiveDistinction

/-- Swapping the two factors exchanges the two generated primitive planes. -/
noncomputable def planeCoordinateSwapEquiv
    {Left : Type} {Right : Type}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right) :
    PrimitiveDistinctionPlane left right ≃
      PrimitiveDistinctionPlane right left :=
  Equiv.prodComm _ _

/-- Pull a plane observable back along the factor swap. -/
noncomputable def planeCoordinateSwapObservable
    {Left : Type} {Right : Type} {Value : Type uValue}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right)
    (observable : PrimitiveDistinctionPlane left right → Value) :
    PrimitiveDistinctionPlane right left → Value :=
  fun point => observable
    ((planeCoordinateSwapEquiv left right).symm point)

/-- The explicit Boolean plane coordinates commute with the factor swap. -/
theorem generatedPlaneEquiv_coordinateSwap
    {Left : Type} {Right : Type}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right)
    (point : PrimitiveDistinctionPlane left right) :
      right.generatedPlaneEquivBoolProduct left
        ((planeCoordinateSwapEquiv left right) point) =
      boolCoordinateSwap
        (left.generatedPlaneEquivBoolProduct right point) := by
  rcases point with ⟨leftPoint, rightPoint⟩
  rcases left.axis_cases leftPoint with leftFirst | leftSecond <;>
    rcases right.axis_cases rightPoint with rightFirst | rightSecond <;>
      subst leftPoint <;> subst rightPoint <;>
        simp [planeCoordinateSwapEquiv, generatedPlaneEquivBoolProduct,
          boolCoordinateSwap]

/-- The Boolean observable used by the swapped plane is exactly the
coordinate-swapped source observable. -/
theorem planeObservableToBool_coordinateSwap
    {Left : Type} {Right : Type} {Value : Type uValue}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right)
    (observable : PrimitiveDistinctionPlane left right → Value)
    (coordinate : Bool × Bool) :
    planeObservableToBool right left
        (planeCoordinateSwapObservable left right observable) coordinate =
      boolCoordinateSwapObservable
        (planeObservableToBool left right observable) coordinate := by
  let sourceEquiv := left.generatedPlaneEquivBoolProduct right
  let targetEquiv := right.generatedPlaneEquivBoolProduct left
  let sourcePoint := sourceEquiv.symm (boolCoordinateSwap coordinate)
  have swapPoint :
      planeCoordinateSwapEquiv left right sourcePoint =
        targetEquiv.symm coordinate := by
    apply targetEquiv.injective
    calc
      targetEquiv (planeCoordinateSwapEquiv left right sourcePoint) =
          boolCoordinateSwap (sourceEquiv sourcePoint) := by
            exact generatedPlaneEquiv_coordinateSwap left right sourcePoint
      _ = boolCoordinateSwap (boolCoordinateSwap coordinate) := by
            simp [sourcePoint, sourceEquiv]
      _ = coordinate := boolCoordinateSwap_involutive coordinate
      _ = targetEquiv (targetEquiv.symm coordinate) :=
        (targetEquiv.apply_symm_apply coordinate).symm
  change observable ((planeCoordinateSwapEquiv left right).symm
      (targetEquiv.symm coordinate)) =
    observable (sourceEquiv.symm (boolCoordinateSwap coordinate))
  rw [← swapPoint]
  simp [sourcePoint]

/-- Factor exchange covariance for the four transported character layers. -/
theorem plane_character_parts_exchange_natural
    {Left : Type} {Right : Type} {Value : Type uValue}
    [Field Value] [CharZero Value]
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right)
    (observable : PrimitiveDistinctionPlane left right → Value)
    (point : PrimitiveDistinctionPlane right left) :
    (planeEvenEvenPart right left
          (planeCoordinateSwapObservable left right observable) point =
        planeEvenEvenPart left right observable
          ((planeCoordinateSwapEquiv left right).symm point)) ∧
    (planeOddEvenPart right left
          (planeCoordinateSwapObservable left right observable) point =
        planeEvenOddPart left right observable
          ((planeCoordinateSwapEquiv left right).symm point)) ∧
    (planeEvenOddPart right left
          (planeCoordinateSwapObservable left right observable) point =
        planeOddEvenPart left right observable
          ((planeCoordinateSwapEquiv left right).symm point)) ∧
    (planeOddOddPart right left
          (planeCoordinateSwapObservable left right observable) point =
        planeOddOddPart left right observable
          ((planeCoordinateSwapEquiv left right).symm point)) := by
  let sourceEquiv := left.generatedPlaneEquivBoolProduct right
  let targetEquiv := right.generatedPlaneEquivBoolProduct left
  let sourcePoint := (planeCoordinateSwapEquiv left right).symm point
  have coordinateRelation :
      targetEquiv point =
        boolCoordinateSwap (sourceEquiv sourcePoint) := by
    simpa [sourcePoint, targetEquiv] using
      (generatedPlaneEquiv_coordinateSwap left right sourcePoint)
  have observableRelation :
      planeObservableToBool right left
          (planeCoordinateSwapObservable left right observable) =
        boolCoordinateSwapObservable
          (planeObservableToBool left right observable) := by
    funext coordinate
    exact planeObservableToBool_coordinateSwap left right observable coordinate
  let sourceObservable := planeObservableToBool left right observable
  let targetObservable :=
    planeObservableToBool right left
      (planeCoordinateSwapObservable left right observable)
  have ee := boolEvenEvenPart_swap sourceObservable
    (boolCoordinateSwap (sourceEquiv sourcePoint))
  have oe := boolOddEvenPart_swap sourceObservable
    (boolCoordinateSwap (sourceEquiv sourcePoint))
  have eo := boolEvenOddPart_swap sourceObservable
    (boolCoordinateSwap (sourceEquiv sourcePoint))
  have oo := boolOddOddPart_swap sourceObservable
    (boolCoordinateSwap (sourceEquiv sourcePoint))
  have targetCoord : targetEquiv point =
      boolCoordinateSwap (sourceEquiv sourcePoint) := coordinateRelation
  have targetObs : targetObservable =
      boolCoordinateSwapObservable sourceObservable := by
    simpa [targetObservable, sourceObservable] using observableRelation
  constructor
  · have ee' : boolEvenEvenPart targetObservable (targetEquiv point) =
        boolEvenEvenPart sourceObservable (sourceEquiv sourcePoint) := by
      rw [targetCoord, targetObs]
      simpa using ee
    simpa [planeEvenEvenPart, targetObservable, sourceObservable,
      targetEquiv, sourceEquiv, sourcePoint] using ee'
  · constructor
    · have eo' : boolOddEvenPart targetObservable (targetEquiv point) =
            boolEvenOddPart sourceObservable (sourceEquiv sourcePoint) := by
        rw [targetCoord, targetObs]
        simpa using oe
      simpa [planeOddEvenPart, planeEvenOddPart, targetObservable,
        sourceObservable, targetEquiv, sourceEquiv, sourcePoint] using eo'
    · constructor
      · have oe' : boolEvenOddPart targetObservable (targetEquiv point) =
            boolOddEvenPart sourceObservable (sourceEquiv sourcePoint) := by
          rw [targetCoord, targetObs]
          simpa using eo
        simpa [planeEvenOddPart, planeOddEvenPart, targetObservable,
          sourceObservable, targetEquiv, sourceEquiv, sourcePoint] using oe'
      · have oo' : boolOddOddPart targetObservable (targetEquiv point) =
            boolOddOddPart sourceObservable (sourceEquiv sourcePoint) := by
          rw [targetCoord, targetObs]
          simpa using oo
        simpa [planeOddOddPart, targetObservable, sourceObservable,
          targetEquiv, sourceEquiv, sourcePoint] using oo'

end PrimitiveDistinction

end PrimitivePlaneExchange

end OCKIndividuationMSpaceComposition
