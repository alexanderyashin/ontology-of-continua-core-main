import OCKIndividuationMSpaceComposition.SymmetryAxisCoaxis

namespace OCKIndividuationMSpaceComposition

universe u

namespace PrimitiveDistinction

/-!
# The local coorientation torsor of a generated axis

`SymmetryAxisCoaxis` defines a coaxis as a side predicate flipped by the
canonical endpoint swap.  This module proves the exact local cardinality of
that choice.  On a fixed generated two-point axis every coaxis is either the
coorientation based at the chosen endpoint or its reversal.  Consequently
`Bool` is an explicit coordinate for the local choice, and reversal is the
free nontrivial `Bool` action.

The result is deliberately local.  It does not orient the whole carrier, does
not extend the involution to uncovered points, and does not turn the local
two-element torsor into a global C2 action on OC.
-/

/-! ## The two endpoint representatives of the local axis -/

def coaxisSeed {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    axis symmetry x :=
  ⟨x, axis_mem_left symmetry x⟩

def coaxisPartner {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    axis symmetry x :=
  ⟨symmetry.action x, axis_mem_right symmetry x⟩

theorem coaxis_axis_cases {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier)
    (y : axis symmetry x) :
    y = coaxisSeed symmetry x ∨ y = coaxisPartner symmetry x := by
  rcases axis_side_dichotomy symmetry x y with positive | negative
  · left
    apply Subtype.ext
    exact positive
  · right
    apply Subtype.ext
    exact negative

theorem coaxisSwap_seed_eq_partner {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    axisSwap symmetry x (coaxisSeed symmetry x) =
      coaxisPartner symmetry x :=
  axisSwap_exchanges_endpoints_left symmetry x

/-! ## Extensionality and exact classification -/

theorem axisCoaxis_ext_positive {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    {left right : AxisCoaxis symmetry x}
    (positive : left.positive = right.positive) :
    left = right := by
  cases left with
  | mk leftPositive leftFlips =>
    cases right with
    | mk rightPositive rightFlips =>
      simp_all

theorem axisCoaxis_partner_positive_iff_not_seed_positive {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (coaxis : AxisCoaxis symmetry x) :
    coaxisPartner symmetry x ∈ coaxis.positive ↔
      coaxisSeed symmetry x ∉ coaxis.positive := by
  rw [← coaxisSwap_seed_eq_partner symmetry x]
  exact coaxis.flips (coaxisSeed symmetry x)

theorem axisCoaxis_eq_base_or_reverse_base {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier)
    (coaxis : AxisCoaxis symmetry x) :
    coaxis = baseAxisCoaxis symmetry x ∨
      coaxis = reverseAxisCoaxis (baseAxisCoaxis symmetry x) := by
  by_cases seedPositive : coaxisSeed symmetry x ∈ coaxis.positive
  · left
    apply axisCoaxis_ext_positive
    ext y
    rcases coaxis_axis_cases symmetry x y with seed | partner
    · subst y
      exact iff_of_true seedPositive
        (baseAxisCoaxis_marks_seed_positive symmetry x)
    · subst y
      have coaxisNotPartner :
          coaxisPartner symmetry x ∉ coaxis.positive := by
        intro partnerPositive
        have seedNotPositive :
            coaxisSeed symmetry x ∉ coaxis.positive := by
          apply (coaxis.flips (coaxisSeed symmetry x)).1
          rw [coaxisSwap_seed_eq_partner symmetry x]
          exact partnerPositive
        exact seedNotPositive seedPositive
      exact iff_of_false coaxisNotPartner
        (baseAxisCoaxis_marks_partner_negative symmetry x)
  · right
    apply axisCoaxis_ext_positive
    ext y
    rcases coaxis_axis_cases symmetry x y with seed | partner
    · subst y
      change coaxisSeed symmetry x ∈ coaxis.positive ↔
        ¬ coaxisSeed symmetry x ∈ (baseAxisCoaxis symmetry x).positive
      exact iff_of_false seedPositive (by
        intro notBase
        exact notBase (baseAxisCoaxis_marks_seed_positive symmetry x))
    · subst y
      have coaxisPartnerPositive :
          coaxisPartner symmetry x ∈ coaxis.positive := by
        apply (coaxis.flips (coaxisSeed symmetry x)).2
        exact seedPositive
      change coaxisPartner symmetry x ∈ coaxis.positive ↔
        ¬ coaxisPartner symmetry x ∈ (baseAxisCoaxis symmetry x).positive
      exact iff_of_true coaxisPartnerPositive
        (baseAxisCoaxis_marks_partner_negative symmetry x)

/-! ## A Boolean coordinate and the reversal action -/

noncomputable def axisCoaxisCode {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (coaxis : AxisCoaxis symmetry x) : Bool :=
  by
    classical
    exact if coaxisSeed symmetry x ∈ coaxis.positive then false else true

def coaxisSwap {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (coaxis : AxisCoaxis symmetry x) : AxisCoaxis symmetry x :=
  reverseAxisCoaxis coaxis

theorem coaxisSwap_twice {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (coaxis : AxisCoaxis symmetry x) :
    coaxisSwap (coaxisSwap coaxis) = coaxis := by
  apply axisCoaxis_ext_positive
  ext y
  exact reverseAxisCoaxis_twice coaxis y

theorem axisCoaxisCode_coaxisSwap {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (coaxis : AxisCoaxis symmetry x) :
    axisCoaxisCode (coaxisSwap coaxis) =
      Bool.not (axisCoaxisCode coaxis) := by
  classical
  by_cases seedPositive : coaxisSeed symmetry x ∈ coaxis.positive
  · simp [axisCoaxisCode, coaxisSwap, reverseAxisCoaxis, seedPositive]
  · simp [axisCoaxisCode, coaxisSwap, reverseAxisCoaxis, seedPositive]

theorem coaxisSwap_ne_self {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (coaxis : AxisCoaxis symmetry x) :
    coaxisSwap coaxis ≠ coaxis := by
  intro equality
  have codeEquality := congrArg axisCoaxisCode equality
  rw [axisCoaxisCode_coaxisSwap] at codeEquality
  cases code : axisCoaxisCode coaxis <;> simp [code] at codeEquality

/-! ## The explicit local C2 action -/

def coaxisC2Action {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (bit : Bool) (coaxis : AxisCoaxis symmetry x) : AxisCoaxis symmetry x :=
  if bit then coaxisSwap coaxis else coaxis

theorem coaxisC2Action_false {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (coaxis : AxisCoaxis symmetry x) :
    coaxisC2Action false coaxis = coaxis := by
  rfl

theorem coaxisC2Action_true {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (coaxis : AxisCoaxis symmetry x) :
    coaxisC2Action true coaxis = coaxisSwap coaxis := by
  rfl

theorem coaxisC2Action_xor {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (first second : Bool) (coaxis : AxisCoaxis symmetry x) :
    coaxisC2Action (first ^^ second) coaxis =
      coaxisC2Action first (coaxisC2Action second coaxis) := by
  cases first <;> cases second <;>
    simp [coaxisC2Action, coaxisSwap_twice]

theorem coaxisC2Action_true_ne {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (coaxis : AxisCoaxis symmetry x) :
    coaxisC2Action true coaxis ≠ coaxis := by
  simpa [coaxisC2Action] using coaxisSwap_ne_self coaxis

theorem axisCoaxisCode_base {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    axisCoaxisCode (baseAxisCoaxis symmetry x) = false := by
  classical
  have seedPositive :
      coaxisSeed symmetry x ∈ (baseAxisCoaxis symmetry x).positive := by
    change x = x
    rfl
  simp [axisCoaxisCode, seedPositive]

theorem axisCoaxisCode_reverse_base {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    axisCoaxisCode (reverseAxisCoaxis (baseAxisCoaxis symmetry x)) = true := by
  classical
  have seedNotPositive :
      coaxisSeed symmetry x ∉
        (reverseAxisCoaxis (baseAxisCoaxis symmetry x)).positive := by
    change ¬ (coaxisSeed symmetry x ∉ (baseAxisCoaxis symmetry x).positive)
    intro notBase
    exact notBase (baseAxisCoaxis_marks_seed_positive symmetry x)
  simp [axisCoaxisCode, seedNotPositive]

noncomputable def axisCoaxisEquivBool {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    AxisCoaxis symmetry x ≃ Bool where
  toFun := axisCoaxisCode
  invFun := fun bit =>
    match bit with
    | false => baseAxisCoaxis symmetry x
    | true => reverseAxisCoaxis (baseAxisCoaxis symmetry x)
  left_inv := by
    intro coaxis
    rcases axisCoaxis_eq_base_or_reverse_base symmetry x coaxis with
      base | reverse
    · subst coaxis
      rw [axisCoaxisCode_base]
    · subst coaxis
      rw [axisCoaxisCode_reverse_base]
  right_inv := by
    intro bit
    cases bit
    · simpa using axisCoaxisCode_base symmetry x
    · simpa using axisCoaxisCode_reverse_base symmetry x

theorem axisCoaxisCode_eq_false_iff_seed_positive {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (coaxis : AxisCoaxis symmetry x) :
    axisCoaxisCode coaxis = false ↔
      coaxisSeed symmetry x ∈ coaxis.positive := by
  simp [axisCoaxisCode]

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
