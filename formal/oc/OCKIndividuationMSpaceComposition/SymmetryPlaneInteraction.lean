import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinction

namespace OCKIndividuationMSpaceComposition

universe uCarrier uLeft uRight

/-!
# Interaction between two symmetry planes

Two fixed-point-free involutions on one carrier do not automatically form
independent symmetry planes.  Their composite is itself involutive exactly
when the two actions commute.  This gives a sharp compatibility test rather
than silently treating several symmetries as Cartesian axes.

The second part supplies one positive construction.  Two primitive
distinctions generate two local axes independently; on their product the two
derived swaps act on separate coordinates, commute exactly, and give four
distinct parity states.  No action, commutation law or four-state orbit is
present in either primitive distinction.
-/

/-- Pointwise commutation of two involutive symmetry actions. -/
def InvolutionsCommute {Carrier : Type uCarrier}
    (first second : FixedPointFreeInvolution Carrier) : Prop :=
  ∀ point,
    first.action (second.action point) =
      second.action (first.action point)

/-- Exact interaction criterion: the composite of two fixed-point-free
involutions is an involution precisely when the two symmetry planes commute. -/
theorem involutionComposition_involutive_iff_commute
    {Carrier : Type uCarrier}
    (first second : FixedPointFreeInvolution Carrier) :
    (∀ point,
        first.action (second.action
          (first.action (second.action point))) = point) ↔
      InvolutionsCommute first second := by
  constructor
  · intro compositeInvolutive point
    have afterFirst := congrArg first.action (compositeInvolutive point)
    have cancelFirst :
        second.action (first.action (second.action point)) =
          first.action point := by
      calc
        second.action (first.action (second.action point)) =
            first.action (first.action
              (second.action (first.action (second.action point)))) :=
          (first.involutive _).symm
        _ = first.action point := afterFirst
    have afterSecond := congrArg second.action cancelFirst
    calc
      first.action (second.action point) =
          second.action (second.action
            (first.action (second.action point))) :=
        (second.involutive _).symm
      _ = second.action (first.action point) := afterSecond
  · intro commute point
    calc
      first.action (second.action
          (first.action (second.action point))) =
          first.action (first.action
            (second.action (second.action point))) :=
        congrArg first.action (commute (second.action point)).symm
      _ = second.action (second.action point) :=
        first.involutive _
      _ = point := second.involutive point

/-- The carrier of two independently generated local distinction axes. -/
abbrev PrimitiveDistinctionPlane
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right) :=
  left.Axis × right.Axis

namespace PrimitiveDistinction

/-- Swap only the first generated axis. -/
noncomputable def firstPlaneInvolution
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right) :
    FixedPointFreeInvolution (PrimitiveDistinctionPlane left right) where
  action :=
    { toFun := fun point => (left.axisSwap point.1, point.2)
      invFun := fun point => (left.axisSwap point.1, point.2)
      left_inv := by
        intro point
        apply Prod.ext
        · exact left.axisSwap_involutive point.1
        · rfl
      right_inv := by
        intro point
        apply Prod.ext
        · exact left.axisSwap_involutive point.1
        · rfl }
  involutive := by
    intro point
    apply Prod.ext
    · exact left.axisSwap_involutive point.1
    · rfl
  fixedPointFree := by
    intro point fixed
    exact left.axisSwap_fixedPointFree point.1
      (congrArg Prod.fst fixed)

/-- Swap only the second generated axis. -/
noncomputable def secondPlaneInvolution
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right) :
    FixedPointFreeInvolution (PrimitiveDistinctionPlane left right) where
  action :=
    { toFun := fun point => (point.1, right.axisSwap point.2)
      invFun := fun point => (point.1, right.axisSwap point.2)
      left_inv := by
        intro point
        apply Prod.ext
        · rfl
        · exact right.axisSwap_involutive point.2
      right_inv := by
        intro point
        apply Prod.ext
        · rfl
        · exact right.axisSwap_involutive point.2 }
  involutive := by
    intro point
    apply Prod.ext
    · rfl
    · exact right.axisSwap_involutive point.2
  fixedPointFree := by
    intro point fixed
    exact right.axisSwap_fixedPointFree point.2
      (congrArg Prod.snd fixed)

/-- Independently generated product planes commute exactly. -/
theorem generatedPlanes_commute
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right) :
    InvolutionsCommute
      (left.firstPlaneInvolution right)
      (left.secondPlaneInvolution right) := by
  intro point
  rfl

/-- The two coordinate actions are genuinely different.  Commutation alone
does not collapse the two planes into one transformation. -/
theorem generatedPlanes_distinct
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right) :
    (left.firstPlaneInvolution right).action ≠
      (left.secondPlaneInvolution right).action := by
  intro equalActions
  have atBase := congrArg
    (fun action :
        PrimitiveDistinctionPlane left right ≃
          PrimitiveDistinctionPlane left right =>
      action (left.axisFirst, right.axisFirst)) equalActions
  have firstCoordinates := congrArg Prod.fst atBase
  have endpoints : left.axisSecond = left.axisFirst := by
    simpa [firstPlaneInvolution, secondPlaneInvolution] using firstCoordinates
  exact left.axisFirst_ne_axisSecond endpoints.symm

/-- Therefore the simultaneous two-plane reversal is involutive.  This is a
derived consequence of commutation, not a field of the product construction. -/
theorem generatedPlanes_composition_involutive
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right) :
    ∀ point,
      (left.firstPlaneInvolution right).action
        ((left.secondPlaneInvolution right).action
          ((left.firstPlaneInvolution right).action
            ((left.secondPlaneInvolution right).action point))) = point :=
  (involutionComposition_involutive_iff_commute
    (left.firstPlaneInvolution right)
    (left.secondPlaneInvolution right)).2
      (left.generatedPlanes_commute right)

/-- Simultaneously reversing both planes is nontrivial.  The product therefore
contains identity, each coordinate reversal, and their distinct composite. -/
theorem generatedPlanes_composite_ne_identity
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right) :
    (fun point =>
      (left.firstPlaneInvolution right).action
        ((left.secondPlaneInvolution right).action point)) ≠
      (id : PrimitiveDistinctionPlane left right →
        PrimitiveDistinctionPlane left right) := by
  intro equalFunctions
  have atBase := congrFun equalFunctions (left.axisFirst, right.axisFirst)
  have firstCoordinates := congrArg Prod.fst atBase
  have endpoints : left.axisSecond = left.axisFirst := by
    simpa [firstPlaneInvolution, secondPlaneInvolution] using firstCoordinates
  exact left.axisFirst_ne_axisSecond endpoints.symm

/-- In the explicit product construction, simultaneous reversal is also free.
This does not follow for arbitrary commuting free involutions, whose composite
may have fixed points when the two actions coincide. -/
theorem generatedPlanes_composition_fixedPointFree
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right)
    (point : PrimitiveDistinctionPlane left right) :
    (left.firstPlaneInvolution right).action
        ((left.secondPlaneInvolution right).action point) ≠ point := by
  intro fixed
  exact left.axisSwap_fixedPointFree point.1
    (congrArg Prod.fst fixed)

/-- The product of the two generated axes has a base-relative four-state
coordinate.  Each Bool coordinate comes from one primitive distinction. -/
noncomputable def generatedPlaneEquivBoolProduct
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right) :
    PrimitiveDistinctionPlane left right ≃ Bool × Bool where
  toFun := fun point =>
    (left.generatedAxisEquivBool point.1,
      right.generatedAxisEquivBool point.2)
  invFun := fun coordinate =>
    (left.generatedAxisEquivBool.symm coordinate.1,
      right.generatedAxisEquivBool.symm coordinate.2)
  left_inv := by
    intro point
    apply Prod.ext <;> simp
  right_inv := by
    intro coordinate
    apply Prod.ext <;> simp

/-- First-plane reversal negates exactly the first parity coordinate. -/
theorem generatedPlane_first_coordinate_reversal
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right)
    (point : PrimitiveDistinctionPlane left right) :
    left.generatedPlaneEquivBoolProduct right
        ((left.firstPlaneInvolution right).action point) =
      (Bool.not ((left.generatedPlaneEquivBoolProduct right point).1),
        (left.generatedPlaneEquivBoolProduct right point).2) := by
  have leftFirst :
      left.generatedAxisEquivBool left.axisFirst = false := by
    simpa [generatedAxisEquivBool, generatedPolarity] using
      left.generatedPolarity_first
  have leftSecond :
      left.generatedAxisEquivBool left.axisSecond = true := by
    simpa [generatedAxisEquivBool, generatedPolarity] using
      left.generatedPolarity_second
  rcases point with ⟨leftPoint, rightPoint⟩
  rcases left.axis_cases leftPoint with rfl | rfl <;>
  rcases right.axis_cases rightPoint with rfl | rfl <;>
  simp [generatedPlaneEquivBoolProduct, firstPlaneInvolution,
    leftFirst, leftSecond]

/-- Second-plane reversal negates exactly the second parity coordinate. -/
theorem generatedPlane_second_coordinate_reversal
    {Left : Type uLeft} {Right : Type uRight}
    (left : PrimitiveDistinction Left)
    (right : PrimitiveDistinction Right)
    (point : PrimitiveDistinctionPlane left right) :
    left.generatedPlaneEquivBoolProduct right
        ((left.secondPlaneInvolution right).action point) =
      ((left.generatedPlaneEquivBoolProduct right point).1,
        Bool.not ((left.generatedPlaneEquivBoolProduct right point).2)) := by
  have rightFirst :
      right.generatedAxisEquivBool right.axisFirst = false := by
    simpa [generatedAxisEquivBool, generatedPolarity] using
      right.generatedPolarity_first
  have rightSecond :
      right.generatedAxisEquivBool right.axisSecond = true := by
    simpa [generatedAxisEquivBool, generatedPolarity] using
      right.generatedPolarity_second
  rcases point with ⟨leftPoint, rightPoint⟩
  rcases left.axis_cases leftPoint with rfl | rfl <;>
  rcases right.axis_cases rightPoint with rfl | rfl <;>
  simp [generatedPlaneEquivBoolProduct, secondPlaneInvolution,
    rightFirst, rightSecond]

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
