import OCKIndividuationMSpaceComposition.SymmetryAutomorphismParity

namespace OCKIndividuationMSpaceComposition

universe uCarrier

/-!
# Symmetry derived from a primitive distinction

This module starts below the former R3 interface.  A primitive distinction is
only two points together with evidence that they differ.  In particular it
contains no reversal, involution, freeness, transitivity, group action, axis or
orientation choice.

The two-point axis cut out by those points nevertheless has a canonical,
label-independent transposition.  On that axis the transposition is
involutive, fixed-point-free and transitive, hence produces the R3 C₂ torsor
and its already proved admissible-automorphism algebra.

The ambient carrier has a sharp boundary: the same canonical transposition
fixes every point outside the distinguished pair.  It is fixed-point-free on
the whole carrier exactly when the pair exhausts the carrier.  Thus a bare
distinction derives C₂ on its own generated axis, but does not justify a
global C₂ action without an exact two-side coverage premise (or some other
explicit action on the complement).
-/

/-- Two unequal carrier points, with no symmetry operation built in. -/
structure PrimitiveDistinction (Carrier : Type uCarrier) where
  first : Carrier
  second : Carrier
  separated : first ≠ second

/-- A relation-level primitive distinction.  Irreflexivity and one witnessed
edge imply endpoint inequality, but contain no map or action. -/
structure IrreflexiveDistinctionWitness (Carrier : Type uCarrier) where
  relation : Carrier → Carrier → Prop
  irreflexive : ∀ point : Carrier, ¬ relation point point
  first : Carrier
  second : Carrier
  witnessed : relation first second

namespace IrreflexiveDistinctionWitness

/-- A witnessed irreflexive relation separates its endpoints ontically. -/
theorem endpoints_ne {Carrier : Type uCarrier}
    (witness : IrreflexiveDistinctionWitness Carrier) :
    witness.first ≠ witness.second := by
  intro equality
  have diagonal := witness.witnessed
  rw [← equality] at diagonal
  exact witness.irreflexive witness.first diagonal

/-- Forget the relation after extracting its actual primitive distinction. -/
def toPrimitiveDistinction {Carrier : Type uCarrier}
    (witness : IrreflexiveDistinctionWitness Carrier) :
    PrimitiveDistinction Carrier where
  first := witness.first
  second := witness.second
  separated := witness.endpoints_ne

/-- Symmetry of the evidence relation is an explicit order-neutrality premise,
not an inferred pole-exchange map. -/
theorem reverse_witness_of_symmetric {Carrier : Type uCarrier}
    (witness : IrreflexiveDistinctionWitness Carrier)
    (symmetric : Symmetric witness.relation) :
    witness.relation witness.second witness.first :=
  symmetric witness.witnessed

end IrreflexiveDistinctionWitness

namespace PrimitiveDistinction

/-- Reverse the presentation labels.  This changes no underlying unordered
distinction. -/
def reverseLabels {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) : PrimitiveDistinction Carrier where
  first := distinction.second
  second := distinction.first
  separated := Ne.symm distinction.separated

/-- The generated axis is exactly the subtype consisting of the two
distinguished points. -/
def Axis {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :=
  { point : Carrier // point = distinction.first ∨ point = distinction.second }

/-- First displayed endpoint of the generated axis. -/
def axisFirst {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) : distinction.Axis :=
  ⟨distinction.first, Or.inl rfl⟩

/-- Second displayed endpoint of the generated axis. -/
def axisSecond {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) : distinction.Axis :=
  ⟨distinction.second, Or.inr rfl⟩

/-- The generated endpoints remain distinct. -/
theorem axisFirst_ne_axisSecond {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.axisFirst ≠ distinction.axisSecond := by
  intro equality
  exact distinction.separated (congrArg Subtype.val equality)

/-- Every point of the generated axis is one of its two endpoints.  This is a
theorem from subtype membership, not an interface hypothesis. -/
theorem axis_cases {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) (point : distinction.Axis) :
    point = distinction.axisFirst ∨ point = distinction.axisSecond := by
  rcases point.property with first | second
  · left
    exact Subtype.ext first
  · right
    exact Subtype.ext second

/-- Canonical exchange on the generated two-point axis. -/
noncomputable def axisSwap {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.Axis → distinction.Axis := by
  classical
  intro point
  exact if point = distinction.axisFirst then
    distinction.axisSecond else distinction.axisFirst

@[simp] theorem axisSwap_first {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.axisSwap distinction.axisFirst = distinction.axisSecond := by
  simp [axisSwap]

@[simp] theorem axisSwap_second {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.axisSwap distinction.axisSecond = distinction.axisFirst := by
  simp [axisSwap, Ne.symm distinction.axisFirst_ne_axisSecond]

/-- The derived swap is involutive. -/
theorem axisSwap_involutive {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) (point : distinction.Axis) :
    distinction.axisSwap (distinction.axisSwap point) = point := by
  rcases distinction.axis_cases point with rfl | rfl <;> simp

/-- The derived swap is free. -/
theorem axisSwap_fixedPointFree {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) (point : distinction.Axis) :
    distinction.axisSwap point ≠ point := by
  rcases distinction.axis_cases point with rfl | rfl
  · rw [axisSwap_first]
    exact distinction.axisFirst_ne_axisSecond.symm
  · rw [axisSwap_second]
    exact distinction.axisFirst_ne_axisSecond

/-- Package the derived swap as an equivalence. -/
noncomputable def axisSwapEquiv {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.Axis ≃ distinction.Axis where
  toFun := distinction.axisSwap
  invFun := distinction.axisSwap
  left_inv := distinction.axisSwap_involutive
  right_inv := distinction.axisSwap_involutive

/-- The primitive distinction therefore generates a free involution on its
axis, without assuming one. -/
noncomputable def toFixedPointFreeInvolution {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    FixedPointFreeInvolution distinction.Axis where
  action := distinction.axisSwapEquiv
  involutive := distinction.axisSwap_involutive
  fixedPointFree := distinction.axisSwap_fixedPointFree

/-- The generated two-side action is transitive; this follows from the exact
two-point axis theorem. -/
theorem axis_pairTransitive {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (first second : distinction.Axis) :
    second = first ∨ second = distinction.axisSwap first := by
  rcases distinction.axis_cases first with rfl | rfl <;>
    rcases distinction.axis_cases second with rfl | rfl <;> simp

/-- The induced R3 torsor uses `Unit` only for the still-uninterpreted typed
axis and identity observations.  It makes no claim that those semantic layers
are derived from a bare pair. -/
noncomputable def toR3Torsor {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    R3C2OrientationTorsorInterface distinction.Axis Unit Unit where
  reverse := distinction.axisSwap
  reverseInvolutive := distinction.axisSwap_involutive
  reverseFree := distinction.axisSwap_fixedPointFree
  pairTransitive := distinction.axis_pairTransitive
  axisOf := fun _ => ()
  identityOf := fun _ => ()

/-- The admissible endomorphisms of the generated axis are exactly C₂. -/
noncomputable def generatedAdmissibleAutomorphismsEquivBool
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier) :
    R3AdmissibleEndomorphism distinction.toR3Torsor ≃ Bool :=
  r3AdmissibleEndomorphismEquivBool distinction.toR3Torsor distinction.axisFirst

/-- Choosing the displayed first endpoint as base identifies the generated
axis itself with the regular two-element C₂ carrier.  The equivalence is
base-relative; the action and unordered axis are not. -/
noncomputable def generatedAxisEquivBool
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier) :
    distinction.Axis ≃ Bool :=
  r3OrientationEquivBool distinction.toR3Torsor distinction.axisFirst

/-- No endpoint of the generated axis is fixed by every admissible
transformation.  Thus primitive distinction derives absence of a canonically
privileged pole rather than assuming it. -/
theorem generatedAxis_no_admissiblyCanonicalPole
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier) :
    ¬ ∃ point : distinction.Axis,
        ∀ transform : distinction.Axis → distinction.Axis,
          R3AdmissibleTransformation distinction.toR3Torsor transform →
            transform point = point :=
  r3_no_orientation_fixed_by_all_admissible_transformations
    distinction.toR3Torsor

/-- The polarity coordinate obtained by choosing the first endpoint as
negative.  The coordinate is derived only after this explicit base choice. -/
noncomputable def generatedPolarity {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) : distinction.Axis → Bool :=
  r3OrientationEquivBool distinction.toR3Torsor distinction.axisFirst

@[simp] theorem generatedPolarity_first {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.generatedPolarity distinction.axisFirst = false :=
  r3OrientationEquivBool_base distinction.toR3Torsor distinction.axisFirst

@[simp] theorem generatedPolarity_second {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.generatedPolarity distinction.axisSecond = true := by
  rw [← distinction.axisSwap_first]
  simpa [generatedPolarity, toR3Torsor] using
    r3OrientationEquivBool_partner distinction.toR3Torsor distinction.axisFirst

/-- Choosing the opposite endpoint negates the polarity everywhere.  Thus the
axis and exchange are canonical, while sign is canonical only up to reversal. -/
theorem generatedPolarity_change_base {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) (point : distinction.Axis) :
    r3OrientationEquivBool distinction.toR3Torsor distinction.axisSecond point =
      Bool.not (distinction.generatedPolarity point) := by
  rw [← distinction.axisSwap_first]
  simpa [generatedPolarity, toR3Torsor] using
    r3OrientationEquivBool_change_base distinction.toR3Torsor
      distinction.axisFirst point

/-! ## Exact ambient-carrier boundary -/

/-- The canonical ambient transposition exchanges the distinguished pair and
fixes everything else. -/
noncomputable def pairSwap {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) (point : Carrier) : Carrier := by
  classical
  exact if point = distinction.first then distinction.second
    else if point = distinction.second then distinction.first else point

@[simp] theorem pairSwap_first {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.pairSwap distinction.first = distinction.second := by
  simp [pairSwap]

@[simp] theorem pairSwap_second {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.pairSwap distinction.second = distinction.first := by
  simp [pairSwap, Ne.symm distinction.separated]

theorem pairSwap_outside {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) (point : Carrier)
    (notFirst : point ≠ distinction.first)
    (notSecond : point ≠ distinction.second) :
    distinction.pairSwap point = point := by
  simp [pairSwap, notFirst, notSecond]

/-- The ambient transposition is always involutive, even when the carrier has
additional points. -/
theorem pairSwap_involutive {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) (point : Carrier) :
    distinction.pairSwap (distinction.pairSwap point) = point := by
  classical
  by_cases first : point = distinction.first
  · subst point
    simp
  · by_cases second : point = distinction.second
    · subst point
      simp
    · simp [pairSwap, first, second]

/-- Reordering the displayed endpoints leaves the canonical transposition
unchanged.  Hence no pole is privileged by the derived operation. -/
theorem pairSwap_reverseLabels {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.reverseLabels.pairSwap = distinction.pairSwap := by
  funext point
  classical
  by_cases first : point = distinction.first
  · subst point
    simp [pairSwap, reverseLabels, distinction.separated]
  · by_cases second : point = distinction.second
    · subst point
      simp [pairSwap, reverseLabels, Ne.symm distinction.separated]
    · simp [pairSwap, reverseLabels, first, second]

/-- The missing premise for a global free swap is exact coverage of the
ambient carrier by the distinguished pair. -/
def CoversCarrier {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) : Prop :=
  ∀ point : Carrier, point = distinction.first ∨ point = distinction.second

/-- Sharp boundary theorem: the canonical transposition is fixed-point-free on
the entire ambient carrier iff no third point exists. -/
theorem pairSwap_fixedPointFree_iff_coversCarrier
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier) :
    (∀ point : Carrier, distinction.pairSwap point ≠ point) ↔
      distinction.CoversCarrier := by
  constructor
  · intro free point
    by_contra outside
    have notFirst : point ≠ distinction.first := by
      intro equal
      exact outside (Or.inl equal)
    have notSecond : point ≠ distinction.second := by
      intro equal
      exact outside (Or.inr equal)
    exact free point (distinction.pairSwap_outside point notFirst notSecond)
  · intro covers point
    rcases covers point with first | second
    · subst point
      rw [pairSwap_first]
      exact Ne.symm distinction.separated
    · subst point
      rw [pairSwap_second]
      exact distinction.separated

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
