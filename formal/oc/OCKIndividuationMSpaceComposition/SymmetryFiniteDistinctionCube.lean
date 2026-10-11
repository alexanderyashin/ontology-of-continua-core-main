import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinction
import Mathlib.Data.Fintype.Basic

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier

/-!
# A finite Cartesian realization of primitive distinction axes

This module makes one deliberately bounded construction. Given a finite
indexed family of primitive distinctions, it takes the dependent product of
their two-point generated axes and lets a Boolean mask flip the selected
coordinates. The resulting action is a concrete product realization: the
product carrier and coordinate independence are inputs to the construction.

Nothing here claims that an arbitrary family of distinctions jointly
generates this carrier, that arbitrary actions commute, or that the number of
coordinates is an intrinsic OC dimension. Those are separate scientific
premises and theorem layers. The finite product is therefore a realization
boundary, not a definition of OC dimension.
-/

/-- A family of primitive distinctions, one on each local carrier. -/
abbrev PrimitiveDistinctionFamily (Index : Type uIndex)
    (Carrier : Index → Type uCarrier) :=
  ∀ index : Index, PrimitiveDistinction (Carrier index)

/-- The dependent Cartesian product of the local two-point axes. -/
abbrev FiniteDistinctionCube (Index : Type uIndex) [Fintype Index]
    (Carrier : Index → Type uCarrier)
    (axis : PrimitiveDistinctionFamily Index Carrier) :=
  ∀ index : Index, (axis index).Axis

/-- Boolean masks select which local axis coordinates are exchanged. -/
abbrev DistinctionMask (Index : Type uIndex) := Index → Bool

variable {Index : Type uIndex} [Fintype Index]
variable {Carrier : Index → Type uCarrier}

/-- Pointwise Boolean composition of coordinate masks. -/
def maskXor (first second : DistinctionMask Index) : DistinctionMask Index :=
  fun index => Bool.xor (first index) (second index)

/-- The base point chooses the displayed first endpoint in every coordinate.
This is a coordinate basepoint for the product realization, not an intrinsic
origin of the underlying OC carrier. -/
def cubeBase (axis : PrimitiveDistinctionFamily Index Carrier) :
    FiniteDistinctionCube Index Carrier axis :=
  fun index => (axis index).axisFirst

/-- Flip exactly the coordinates selected by a Boolean mask. -/
noncomputable def maskAction (axis : PrimitiveDistinctionFamily Index Carrier)
    (mask : DistinctionMask Index) :
    FiniteDistinctionCube Index Carrier axis →
      FiniteDistinctionCube Index Carrier axis :=
  fun point index =>
    if mask index then (axis index).axisSwap (point index) else point index

/-- The all-false mask is the identity action. -/
theorem maskAction_identity (axis : PrimitiveDistinctionFamily Index Carrier)
    (point : FiniteDistinctionCube Index Carrier axis) :
    maskAction axis (fun _ => false) point = point := by
  funext index
  simp [maskAction]

/-- Applying two masks is exactly pointwise Boolean XOR of those masks. -/
theorem maskAction_comp (axis : PrimitiveDistinctionFamily Index Carrier)
    (first second : DistinctionMask Index)
    (point : FiniteDistinctionCube Index Carrier axis) :
    maskAction axis first (maskAction axis second point) =
      maskAction axis (maskXor first second) point := by
  funext index
  by_cases firstValue : first index <;>
    by_cases secondValue : second index <;>
      simp [maskAction, maskXor, firstValue, secondValue,
        PrimitiveDistinction.axisSwap_involutive]

/-- Reapplying one mask is the identity. -/
theorem maskAction_involutive (axis : PrimitiveDistinctionFamily Index Carrier)
    (mask : DistinctionMask Index)
    (point : FiniteDistinctionCube Index Carrier axis) :
    maskAction axis mask (maskAction axis mask point) = point := by
  funext index
  by_cases maskValue : mask index <;>
    simp [maskAction, maskValue, PrimitiveDistinction.axisSwap_involutive]

/-- Every mask action is an equivalence, with itself as inverse. -/
noncomputable def maskActionEquiv
    (axis : PrimitiveDistinctionFamily Index Carrier)
    (mask : DistinctionMask Index) :
    FiniteDistinctionCube Index Carrier axis ≃
      FiniteDistinctionCube Index Carrier axis where
  toFun := maskAction axis mask
  invFun := maskAction axis mask
  left_inv := maskAction_involutive axis mask
  right_inv := maskAction_involutive axis mask

/-- The product cube is coordinatized by one Boolean per primitive axis. -/
noncomputable def cubeEquivBool
    (axis : PrimitiveDistinctionFamily Index Carrier) :
    FiniteDistinctionCube Index Carrier axis ≃ DistinctionMask Index where
  toFun := fun point index => (axis index).generatedAxisEquivBool (point index)
  invFun := fun mask index =>
    (axis index).generatedAxisEquivBool.symm (mask index)
  left_inv := by
    intro point
    funext index
    simp
  right_inv := by
    intro mask
    funext index
    simp

/-- The chosen product basepoint is the all-false Boolean coordinate. -/
theorem cubeEquivBool_base (axis : PrimitiveDistinctionFamily Index Carrier) :
    cubeEquivBool axis (cubeBase axis) = fun _ => false := by
  funext index
  simp [cubeEquivBool, cubeBase,
    PrimitiveDistinction.generatedAxisEquivBool]

/-- A mask action changes the Boolean coordinate by XOR with the mask. -/
theorem cubeEquivBool_maskAction
    (axis : PrimitiveDistinctionFamily Index Carrier)
    (mask : DistinctionMask Index)
    (point : FiniteDistinctionCube Index Carrier axis) :
    cubeEquivBool axis (maskAction axis mask point) =
      fun index => Bool.xor (mask index) ((cubeEquivBool axis point) index) := by
  funext index
  by_cases maskValue : mask index
  · have firstCoordinate :
        (axis index).generatedAxisEquivBool (axis index).axisFirst = false := by
      simp [PrimitiveDistinction.generatedAxisEquivBool]
    have secondCoordinate :
        (axis index).generatedAxisEquivBool (axis index).axisSecond = true := by
      change (axis index).generatedPolarity (axis index).axisSecond = true
      exact (axis index).generatedPolarity_second
    rcases (axis index).axis_cases (point index) with pointFirst | pointSecond
    · simp [cubeEquivBool, maskAction, maskValue, pointFirst, firstCoordinate,
        secondCoordinate]
    · simp [cubeEquivBool, maskAction, maskValue, pointSecond, firstCoordinate,
        secondCoordinate]
  · simp [cubeEquivBool, maskAction, maskValue]

/-- Distinct masks produce distinct transformations on the product cube.
The proof probes the basepoint and uses only the endpoint separation already
contained in each primitive distinction. -/
theorem maskAction_injective (axis : PrimitiveDistinctionFamily Index Carrier) :
    Function.Injective
      (fun mask : DistinctionMask Index => maskAction axis mask) := by
  intro first second equalActions
  funext index
  have atBase :
      maskAction axis first (cubeBase axis) index =
        maskAction axis second (cubeBase axis) index := by
    exact congrArg
      (fun action :
          FiniteDistinctionCube Index Carrier axis →
            FiniteDistinctionCube Index Carrier axis =>
        action (cubeBase axis) index) equalActions
  by_cases firstValue : first index
  · by_cases secondValue : second index
    · simp [firstValue, secondValue]
    · have endpoints : (axis index).axisSecond = (axis index).axisFirst := by
        simpa [maskAction, cubeBase, firstValue, secondValue] using atBase
      exact False.elim ((axis index).axisFirst_ne_axisSecond endpoints.symm)
  · by_cases secondValue : second index
    · have endpoints : (axis index).axisFirst = (axis index).axisSecond := by
        simpa [maskAction, cubeBase, firstValue, secondValue] using atBase
      exact False.elim ((axis index).axisFirst_ne_axisSecond endpoints)
    · simp [firstValue, secondValue]

end OCKIndividuationMSpaceComposition
