import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionExtension
import OCKIndividuationMSpaceComposition.SymmetryFiniteCubeRankRealization
import Mathlib.Data.Fin.Basic
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Fintype.Card
import Mathlib.Data.Fintype.Pi
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uCarrier uIndex

/-!
# The local C₂ and the global coverage boundary

`PrimitiveDistinction` contains only two unequal carrier points.  The
generated `Axis` is nevertheless exactly a two-point carrier, its canonical
swap is a free involution, and the already proved admissible-transformation
algebra is the two-element Boolean algebra.  These are local consequences of
the pair and its two-point subtype.

The ambient boundary is separate.  The canonical pair transposition is free
on the whole carrier exactly when the pair covers that carrier.  A larger
carrier can acquire a global free involution only with explicit free pairing
data on its complement.  The three-point witness below shows why the local
C₂ cannot silently be promoted to a global one.

The finite cube cardinality theorem is only a Cartesian realization result.
It does not identify the number of coordinates with intrinsic OC dimension.
-/

namespace PrimitiveDistinction

/-! ## Local two-point cardinality and C₂ algebra -/

/-- The generated axis inherits a finite structure from its already proved
Bool equivalence.  This instance is local to the mathematical construction:
it does not assert that the ambient carrier is finite. -/
noncomputable instance axisFintype {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) : Fintype distinction.Axis :=
  Fintype.ofEquiv Bool distinction.generatedAxisEquivBool.symm

/-- The generated axis has exactly two elements.  The finite structure is
transported from the already constructed Bool equivalence; it is not an
additional premise on the ambient carrier. -/
theorem axis_card_eq_two {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    Fintype.card distinction.Axis = 2 := by
    calc
    Fintype.card distinction.Axis = Fintype.card Bool :=
      Fintype.card_congr distinction.generatedAxisEquivBool
    _ = 2 := by decide

/-/ The canonical swap is Boolean negation in the base-relative coordinate. -/
theorem generatedAxisEquivBool_swap {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) :
    distinction.generatedAxisEquivBool (distinction.axisSwap point) =
      Bool.not (distinction.generatedAxisEquivBool point) := by
  change distinction.generatedPolarity (distinction.axisSwap point) =
    Bool.not (distinction.generatedPolarity point)
  rcases distinction.axis_cases point with rfl | rfl <;> simp

/-- The primitive pair yields the local C₂ spine and its already classified
admissible automorphism algebra.  No global carrier coverage is used here. -/
theorem local_c2_spine {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    Fintype.card distinction.Axis = 2 ∧
      (∀ point : distinction.Axis,
        distinction.axisSwap (distinction.axisSwap point) = point) ∧
      (∀ point : distinction.Axis,
        distinction.axisSwap point ≠ point) ∧
      (∀ point : distinction.Axis,
        distinction.generatedAxisEquivBool (distinction.axisSwap point) =
          Bool.not (distinction.generatedAxisEquivBool point)) ∧
      Nonempty
        (R3AdmissibleEndomorphism distinction.toR3Torsor ≃ Bool) := by
  refine ⟨distinction.axis_card_eq_two, distinction.axisSwap_involutive,
    distinction.axisSwap_fixedPointFree,
    distinction.generatedAxisEquivBool_swap, ?_⟩
  exact ⟨distinction.generatedAdmissibleAutomorphismsEquivBool⟩

/-! ## Global free-swap boundary -/

/-- Under exact carrier coverage, the canonical pair transposition packages as
a global fixed-point-free involution. -/
noncomputable def pairSwapGlobalInvolution
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) :
    FixedPointFreeInvolution Carrier where
  action :=
    { toFun := distinction.pairSwap
      invFun := distinction.pairSwap
      left_inv := distinction.pairSwap_involutive
      right_inv := distinction.pairSwap_involutive }
  involutive := distinction.pairSwap_involutive
  fixedPointFree :=
    (distinction.pairSwap_fixedPointFree_iff_coversCarrier).mpr covers

theorem pairSwapGlobalInvolution_exchanges_pair
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) :
    (distinction.pairSwapGlobalInvolution covers).action distinction.first =
      distinction.second := by
  change distinction.pairSwap distinction.first = distinction.second
  exact distinction.pairSwap_first

/-- The two global boundaries already proved for the primitive pair are
re-stated together: canonical global freeness is coverage, while arbitrary
global extension requires an explicit free complement action. -/
theorem global_c2_boundary_spine {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    ((∀ point : Carrier, distinction.pairSwap point ≠ point) ↔
        distinction.CoversCarrier) ∧
      ((∃ symmetry : FixedPointFreeInvolution Carrier,
          symmetry.action distinction.first = distinction.second) ↔
        Nonempty (FixedPointFreeInvolution distinction.Outside)) := by
  exact ⟨distinction.pairSwap_fixedPointFree_iff_coversCarrier,
    distinction.globalFreeExtension_exists_iff_outsidePairing⟩

/-! ## Sharp extra-point countermodel -/

def threePointDistinction : PrimitiveDistinction (Fin 3) where
  first := 0
  second := 1
  separated := by decide

def threePointExtra : threePointDistinction.Outside :=
  ⟨2, by decide, by decide⟩

theorem threePoint_not_covered :
    ¬ threePointDistinction.CoversCarrier := by
  intro covers
  have impossible := covers (2 : Fin 3)
  simpa [threePointDistinction, CoversCarrier] using impossible

theorem threePoint_extra_is_fixed :
    threePointDistinction.pairSwap (2 : Fin 3) = 2 := by
  exact threePointDistinction.pairSwap_outside 2 (by decide) (by decide)

/-- The complement of the two-point pair in `Fin 3` is a singleton, so it
cannot carry a fixed-point-free involution. -/
theorem threePoint_outside_unique (point : threePointDistinction.Outside) :
    point = threePointExtra := by
  apply Subtype.ext
  rcases point with ⟨point, notFirst, notSecond⟩
  fin_cases point
  · exact (notFirst rfl).elim
  · exact (notSecond rfl).elim
  · rfl

theorem threePoint_outside_has_no_free_involution :
    ¬ Nonempty (FixedPointFreeInvolution threePointDistinction.Outside) := by
  rintro ⟨symmetry⟩
  have fixed : symmetry.action threePointExtra = threePointExtra :=
    threePoint_outside_unique (symmetry.action threePointExtra)
  exact symmetry.fixedPointFree threePointExtra fixed

theorem threePoint_no_global_free_extension :
    ¬ ∃ symmetry : FixedPointFreeInvolution (Fin 3),
      symmetry.action threePointDistinction.first =
        threePointDistinction.second := by
  intro extension
  have outsidePairing :=
    (threePointDistinction.globalFreeExtension_exists_iff_outsidePairing).mp
      extension
  exact threePoint_outside_has_no_free_involution outsidePairing

end PrimitiveDistinction

/-! ## Finite product realization boundary -/

namespace FiniteCubeC2Boundary

/-- The finite product inherits a finite structure from its Boolean-mask
equivalence.  This is a realization instance, not an intrinsic dimension
assignment to the underlying ontology. -/
noncomputable instance finiteDistinctionCubeFintype
    {Index : Type uIndex} [Fintype Index]
    {Carrier : Index → Type uCarrier}
    (axis : PrimitiveDistinctionFamily Index Carrier) :
    Fintype (FiniteDistinctionCube Index Carrier axis) :=
  by
    classical
    exact Fintype.ofEquiv (DistinctionMask Index) (cubeEquivBool axis).symm

/-- A finite Cartesian product of local two-point axes has `2^|Index|`
elements.  This is a product-realization cardinality bridge, not an
intrinsic OC-dimension theorem and not a joint-generation theorem. -/
theorem finiteDistinctionCube_card_eq_two_power
    {Index : Type uIndex} [Fintype Index]
    {Carrier : Index → Type uCarrier}
    (axis : PrimitiveDistinctionFamily Index Carrier) :
    Fintype.card (FiniteDistinctionCube Index Carrier axis) =
      2 ^ Fintype.card Index := by
  classical
  calc
    Fintype.card (FiniteDistinctionCube Index Carrier axis) =
        Fintype.card (DistinctionMask Index) :=
      Fintype.card_congr (cubeEquivBool axis)
    _ = 2 ^ Fintype.card Index := by
      change Fintype.card (Index → Bool) = 2 ^ Fintype.card Index
      rw [Fintype.card_pi]
      simp

end FiniteCubeC2Boundary

end OCKIndividuationMSpaceComposition
