import OCKIndividuationMSpaceComposition.SymmetryInvariantQuotient
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Fintype.Card
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uCarrier

/-!
# Finite orbit cardinality for a free primitive symmetry

The quotient `AxisQuotient symmetry` records the two-point orbits of a
fixed-point-free involution.  The preceding quotient modules establish its
universal property for invariant observables, but do not yet quantify the
finite size of the quotient.  This file supplies that missing arithmetic
bridge without choosing representatives or adding a quotient axiom.

For a finite carrier, every quotient fibre is proved equivalent to the
explicit two-point axis of any representative.  The canonical sigma-fibre
equivalence then gives

    card Carrier = 2 * card (AxisQuotient symmetry).

Thus a free involution forces even ambient cardinality, and an invariant
finite-valued observable has exactly one carrier value per orbit.  These are
cardinality consequences of the already supplied action; they do not claim
that an arbitrary OC carrier admits such an action.
-/

namespace FixedPointFreeInvolution

variable {Carrier : Type uCarrier}

/-! The local axis itself has an explicit Boolean coordinate. -/

noncomputable def axisEquivBool
    (symmetry : FixedPointFreeInvolution Carrier) (representative : Carrier) :
    axis symmetry representative ≃ Bool where
  toFun := by
    classical
    exact fun point => if point.1 = representative then false else true
  invFun := fun bit =>
    if bit then
      (⟨symmetry.action representative, axis_mem_right symmetry representative⟩ :
        axis symmetry representative)
    else
      ⟨representative, axis_mem_left symmetry representative⟩
  left_inv := by
    classical
    intro point
    apply Subtype.ext
    by_cases same : point.1 = representative
    · simp [same]
    · have actionCase : point.1 = symmetry.action representative := by
        have pointCase : point.1 = representative ∨
            point.1 = symmetry.action representative := point.2
        exact pointCase.resolve_left same
      simp [actionCase, symmetry.fixedPointFree representative]
  right_inv := by
    classical
    intro bit
    cases bit
    · change (if representative = representative then false else true) = false
      simp
    · change (if symmetry.action representative = representative then false else true) = true
      simp [symmetry.fixedPointFree representative]

noncomputable instance axisFintype
    (symmetry : FixedPointFreeInvolution Carrier) (representative : Carrier) :
    Fintype (axis symmetry representative) :=
  Fintype.ofEquiv Bool (axisEquivBool symmetry representative).symm

theorem axis_card_eq_two
    (symmetry : FixedPointFreeInvolution Carrier) (representative : Carrier) :
    Fintype.card (axis symmetry representative) = 2 := by
  rw [Fintype.card_congr (axisEquivBool symmetry representative)]
  decide

/-! ## Fibres of the orbit quotient -/

def AxisFiber (symmetry : FixedPointFreeInvolution Carrier)
    (quotientPoint : AxisQuotient symmetry) : Type uCarrier :=
  {point : Carrier // axisClass symmetry point = quotientPoint}

noncomputable instance axisQuotientFinite
    (symmetry : FixedPointFreeInvolution Carrier) [Fintype Carrier] :
    Finite (AxisQuotient symmetry) := by
  apply Finite.of_surjective (axisClass symmetry)
  intro quotientPoint
  refine Quotient.inductionOn quotientPoint ?_
  intro representative
  exact ⟨representative, rfl⟩

noncomputable instance axisFiberFinite
    (symmetry : FixedPointFreeInvolution Carrier) [Fintype Carrier]
    (quotientPoint : AxisQuotient symmetry) :
    Finite (AxisFiber symmetry quotientPoint) := by
  apply Finite.of_injective Subtype.val Subtype.coe_injective

noncomputable instance axisQuotientFintype
    (symmetry : FixedPointFreeInvolution Carrier) [Fintype Carrier] :
    Fintype (AxisQuotient symmetry) :=
  Fintype.ofFinite _

noncomputable instance axisFiberFintype
    (symmetry : FixedPointFreeInvolution Carrier) [Fintype Carrier]
    (quotientPoint : AxisQuotient symmetry) :
    Fintype (AxisFiber symmetry quotientPoint) :=
  Fintype.ofFinite _

/-- A quotient fibre over a represented class is exactly its two-point axis.
    No representative is chosen globally; this equivalence is local to the
    displayed representative. -/
noncomputable def axisFiberEquivAxis
    (symmetry : FixedPointFreeInvolution Carrier) (representative : Carrier) :
    AxisFiber symmetry (axisClass symmetry representative) ≃
      axis symmetry representative where
  toFun := fun point =>
    ⟨point.1, by
      exact sameAxis_symm symmetry
        ((axisClass_eq_iff_sameAxis symmetry point.1 representative).1 point.2)⟩
  invFun := fun point =>
    ⟨point.1, (axisClass_eq_iff_sameAxis symmetry point.1 representative).2
      (sameAxis_symm symmetry (by
        exact point.2))⟩
  left_inv := by
    intro point
    rfl
  right_inv := by
    intro point
    rfl

theorem axisFiber_card_eq_two
    (symmetry : FixedPointFreeInvolution Carrier)
    (representative : Carrier) [Fintype Carrier] :
    Fintype.card (AxisFiber symmetry (axisClass symmetry representative)) = 2 := by
  rw [Fintype.card_congr (axisFiberEquivAxis symmetry representative)]
  exact axis_card_eq_two symmetry representative

/-! ## Every finite free involution has an even carrier -/

theorem carrier_card_eq_two_mul_quotient_card
    (symmetry : FixedPointFreeInvolution Carrier)
    [Fintype Carrier] [DecidableEq Carrier] :
    Fintype.card Carrier =
      2 * Fintype.card (AxisQuotient symmetry) := by
  classical
  let fibreEquiv := Equiv.sigmaFiberEquiv (axisClass symmetry)
  have fibreCard : ∀ quotientPoint : AxisQuotient symmetry,
      Fintype.card (AxisFiber symmetry quotientPoint) = 2 := by
    intro quotientPoint
    refine Quotient.inductionOn quotientPoint ?_
    intro representative
    exact axisFiber_card_eq_two symmetry representative
  calc
    Fintype.card Carrier =
        Fintype.card (Σ quotientPoint : AxisQuotient symmetry,
          AxisFiber symmetry quotientPoint) :=
      Fintype.card_congr fibreEquiv.symm
    _ = ∑ quotientPoint : AxisQuotient symmetry,
        Fintype.card (AxisFiber symmetry quotientPoint) :=
      Fintype.card_sigma
    _ = ∑ _quotientPoint : AxisQuotient symmetry, 2 := by
      apply Finset.sum_congr rfl
      intro quotientPoint quotientPointMem
      rw [fibreCard quotientPoint]
    _ = 2 * Fintype.card (AxisQuotient symmetry) := by
      rw [Finset.sum_const, Finset.card_univ]
      exact Nat.mul_comm _ _

theorem even_carrier_card
    (symmetry : FixedPointFreeInvolution Carrier)
    [Fintype Carrier] [DecidableEq Carrier] :
    Even (Fintype.card Carrier) := by
  rw [carrier_card_eq_two_mul_quotient_card symmetry]
  refine ⟨Fintype.card (AxisQuotient symmetry), ?_⟩
  omega

/-! ## Invariant finite observables have one degree of freedom per orbit -/

def FiniteInvariantObservable
    (symmetry : FixedPointFreeInvolution Carrier) (Value : Type*)
    (observable : Carrier → Value) : Prop :=
  InvariantObservable symmetry observable

noncomputable def invariantObservableEquivQuotientFunction
    (symmetry : FixedPointFreeInvolution Carrier) {Value : Type*}
    (observable : Carrier → Value)
    (invariant : FiniteInvariantObservable symmetry Value observable) :
    (AxisQuotient symmetry → Value) :=
  invariantObservableFactor symmetry observable invariant

theorem invariantObservableEquivQuotientFunction_spec
    (symmetry : FixedPointFreeInvolution Carrier) {Value : Type*}
    (observable : Carrier → Value)
    (invariant : FiniteInvariantObservable symmetry Value observable)
    (point : Carrier) :
    invariantObservableEquivQuotientFunction symmetry observable invariant
      (axisClass symmetry point) = observable point :=
  invariantObservableFactor_spec symmetry observable invariant point

end FixedPointFreeInvolution

end OCKIndividuationMSpaceComposition
