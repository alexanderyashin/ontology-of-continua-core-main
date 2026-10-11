import OCKIndividuationMSpaceComposition.SymmetryFiniteDistinctionCube
import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionNaturality

namespace OCKIndividuationMSpaceComposition

universe uIndex uFinalIndex uSourceCarrier uTargetCarrier

namespace PrimitiveDistinctionFamilyNaturality

/-!
# Naturality of a finite family of generated axes

The finite cube is a Cartesian realization, while `OrderPreservingMap` is the
local naturality interface for one generated axis.  This module supplies the
missing bridge between those two levels.  An index equivalence and a family of
endpoint-preserving component maps transport the Boolean polarity coordinate
componentwise.  We state the result at the indexed level, where dependent
carrier families require no hidden casts or definitional equalities.

No global action on an ambient carrier is introduced.  The only data are the
explicit index equivalence and the endpoint equations of each component map.
Product structure remains a stated realization premise, so the result does
not promote Cartesian rank to intrinsic OC dimension.
-/

variable {Index : Type uIndex} {FinalIndex : Type uFinalIndex}
variable {SourceCarrier : Index → Type uSourceCarrier}
variable {TargetCarrier : FinalIndex → Type uTargetCarrier}
variable [Fintype Index] [Fintype FinalIndex]

variable {sourceAxis : PrimitiveDistinctionFamily Index SourceCarrier}
variable {targetAxis : PrimitiveDistinctionFamily FinalIndex TargetCarrier}

/- An endpoint-preserving component map for every reindexed coordinate. -/
structure EndpointPreservingFamilyMap
    (indexEquiv : Index ≃ FinalIndex)
    (sourceAxis : PrimitiveDistinctionFamily Index SourceCarrier)
    (targetAxis : PrimitiveDistinctionFamily FinalIndex TargetCarrier) where
  component : ∀ index : Index,
    PrimitiveDistinction.OrderPreservingMap
      (sourceAxis index) (targetAxis (indexEquiv index))

/- Boolean masks transported along the index equivalence. -/
def reindexMask (indexEquiv : Index ≃ FinalIndex)
    (mask : DistinctionMask Index) : DistinctionMask FinalIndex :=
  fun index => mask (indexEquiv.symm index)

@[simp] theorem reindexMask_apply
    (indexEquiv : Index ≃ FinalIndex) (mask : DistinctionMask Index)
    (index : FinalIndex) :
    reindexMask indexEquiv mask index = mask (indexEquiv.symm index) := rfl

theorem reindexMask_injective (indexEquiv : Index ≃ FinalIndex) :
    Function.Injective (reindexMask indexEquiv) := by
  intro first second equal
  funext index
  have := congrFun equal (indexEquiv index)
  simpa using this

theorem reindexMask_xor
    (indexEquiv : Index ≃ FinalIndex)
    (first second : DistinctionMask Index) :
    reindexMask indexEquiv (maskXor first second) =
      maskXor (reindexMask indexEquiv first) (reindexMask indexEquiv second) := by
  funext index
  rfl

/- A Boolean polarity coordinate for a finite family of generated axes. -/
noncomputable def familyPolarity
    (axis : PrimitiveDistinctionFamily Index SourceCarrier)
    (point : FiniteDistinctionCube Index SourceCarrier axis) :
    DistinctionMask Index :=
  fun index => (axis index).generatedPolarity (point index)

/- Naturality transports the polarity at each reindexed component. -/
theorem component_polarity_transport
    (indexEquiv : Index ≃ FinalIndex)
    (map : EndpointPreservingFamilyMap indexEquiv sourceAxis targetAxis)
    (point : FiniteDistinctionCube Index SourceCarrier sourceAxis)
    (index : Index) :
    (targetAxis (indexEquiv index)).generatedPolarity
        ((map.component index).axisMap (point index)) =
      (sourceAxis index).generatedPolarity (point index) := by
  exact PrimitiveDistinction.OrderPreservingMap.generatedPolarity_natural
    (map.component index) (point index)

/- The same transport remains valid after a local Boolean flip.  Thus the
family-level Boolean action is not an unrelated Cartesian construction: each
coordinate is the image of the corresponding primitive axis action. -/
theorem component_polarity_maskAction_transport
    (indexEquiv : Index ≃ FinalIndex)
    (map : EndpointPreservingFamilyMap indexEquiv sourceAxis targetAxis)
    (mask : DistinctionMask Index)
    (point : FiniteDistinctionCube Index SourceCarrier sourceAxis)
    (index : Index) :
    (targetAxis (indexEquiv index)).generatedPolarity
        ((map.component index).axisMap
          ((maskAction sourceAxis mask point) index)) =
      Bool.xor (mask index) ((sourceAxis index).generatedPolarity (point index)) := by
  rcases (sourceAxis index).axis_cases (point index) with pointFirst | pointSecond
  · by_cases selected : mask index <;>
      simp [maskAction, selected, pointFirst]
  · by_cases selected : mask index <;>
      simp [maskAction, selected, pointSecond]

end PrimitiveDistinctionFamilyNaturality

end OCKIndividuationMSpaceComposition
