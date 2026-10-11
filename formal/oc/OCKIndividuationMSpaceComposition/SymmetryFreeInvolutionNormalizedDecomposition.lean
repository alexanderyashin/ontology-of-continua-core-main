import OCKIndividuationMSpaceComposition.SymmetryFiniteFreeInvolutionOrbitRank
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

universe uCarrier uValue

/-!
# Normalized even/odd decomposition for a free involution

The orbit quotient and the two-point fibre theorem are independent of any
choice of coordinates.  This file applies the same symmetry to an arbitrary
value-valued observable over a characteristic-zero field.  The half-sum is
the invariant projection and the half-difference is the orientation-sensitive
projection.  They reconstruct the observable exactly, and the decomposition
is unique among all invariant/anti-invariant decompositions.

The quotient boundary is exact: the invariant half always factors through the
orbit quotient, while the anti-invariant half factors through it exactly when
it vanishes.  Thus the only information removed by quotienting is the odd
orientation-sensitive component.  No global C₂ action is constructed here;
the free involution is an explicit input.
-/

namespace FixedPointFreeInvolution

variable {Carrier : Type uCarrier} {Value : Type uValue}

/-- An additive observable transforming by the sign character of the
    involution. -/
def AntiInvariantObservable
    (symmetry : FixedPointFreeInvolution Carrier)
    (observable : Carrier → Value) [Neg Value] : Prop :=
  ∀ point, observable (symmetry.action point) = - observable point

/-- The normalized invariant projection (half-sum). -/
noncomputable def invariantHalf
    (symmetry : FixedPointFreeInvolution Carrier)
    [Field Value] [CharZero Value]
    (observable : Carrier → Value) : Carrier → Value :=
  fun point =>
    (observable point + observable (symmetry.action point)) / 2

/-- The normalized anti-invariant projection (half-difference). -/
noncomputable def antiInvariantHalf
    (symmetry : FixedPointFreeInvolution Carrier)
    [Field Value] [CharZero Value]
    (observable : Carrier → Value) : Carrier → Value :=
  fun point =>
    (observable point - observable (symmetry.action point)) / 2

theorem invariantHalf_invariant
    (symmetry : FixedPointFreeInvolution Carrier)
    [Field Value] [CharZero Value]
    (observable : Carrier → Value) :
    InvariantObservable symmetry (invariantHalf symmetry observable) := by
  intro point
  simp only [invariantHalf, symmetry.involutive point]
  ring

theorem antiInvariantHalf_antiInvariant
    (symmetry : FixedPointFreeInvolution Carrier)
    [Field Value] [CharZero Value]
    (observable : Carrier → Value) :
    AntiInvariantObservable symmetry (antiInvariantHalf symmetry observable) := by
  intro point
  simp only [antiInvariantHalf, symmetry.involutive point]
  ring

theorem invariantHalf_add_antiInvariantHalf_eq_observable
    (symmetry : FixedPointFreeInvolution Carrier)
    [Field Value] [CharZero Value]
    (observable : Carrier → Value) (point : Carrier) :
    invariantHalf symmetry observable point +
        antiInvariantHalf symmetry observable point =
      observable point := by
  simp only [invariantHalf, antiInvariantHalf]
  ring

/-- Any invariant/anti-invariant decomposition is the canonical normalized
    half-sum/half-difference decomposition. -/
theorem even_odd_decomposition_unique
    (symmetry : FixedPointFreeInvolution Carrier)
    [Field Value] [CharZero Value]
    (observable evenPart oddPart : Carrier → Value)
    (even : InvariantObservable symmetry evenPart)
    (odd : AntiInvariantObservable symmetry oddPart)
    (reconstruct : ∀ point, evenPart point + oddPart point = observable point) :
    (∀ point,
      evenPart point = invariantHalf symmetry observable point) ∧
    (∀ point,
      oddPart point = antiInvariantHalf symmetry observable point) := by
  constructor
  · intro point
    have atAction := reconstruct (symmetry.action point)
    rw [even point, odd point] at atAction
    have atAction' : evenPart point - oddPart point =
        observable (symmetry.action point) := by
      simpa [sub_eq_add_neg] using atAction
    have atPoint := reconstruct point
    change evenPart point =
      (observable point + observable (symmetry.action point)) / 2
    apply (eq_div_iff (by norm_num : (2 : Value) ≠ 0)).2
    calc
      evenPart point * 2 =
          (evenPart point + oddPart point) +
            (evenPart point - oddPart point) := by ring
      _ = observable point + observable (symmetry.action point) := by
        rw [atPoint, atAction']
  · intro point
    have atAction := reconstruct (symmetry.action point)
    rw [even point, odd point] at atAction
    have atAction' : evenPart point - oddPart point =
        observable (symmetry.action point) := by
      simpa [sub_eq_add_neg] using atAction
    have atPoint := reconstruct point
    change oddPart point =
      (observable point - observable (symmetry.action point)) / 2
    apply (eq_div_iff (by norm_num : (2 : Value) ≠ 0)).2
    calc
      oddPart point * 2 =
          (evenPart point + oddPart point) -
            (evenPart point - oddPart point) := by ring
      _ = observable point - observable (symmetry.action point) := by
        rw [atPoint, atAction']

/-! ## Exact quotient separation -/

theorem invariantHalf_factors_through_axis_quotient
    (symmetry : FixedPointFreeInvolution Carrier)
    [Field Value] [CharZero Value]
    (observable : Carrier → Value) :
    ∃ factor : AxisQuotient symmetry → Value,
      ∀ point,
        factor (axisClass symmetry point) =
          invariantHalf symmetry observable point :=
  invariant_observable_factors_through_axis_quotient symmetry
    (invariantHalf symmetry observable)
    (invariantHalf_invariant symmetry observable)

theorem antiInvariantHalf_factor_through_axis_quotient_iff_zero
    (symmetry : FixedPointFreeInvolution Carrier)
    [Field Value] [CharZero Value]
    (observable : Carrier → Value) :
    (∃ factor : AxisQuotient symmetry → Value,
      ∀ point,
        factor (axisClass symmetry point) =
          antiInvariantHalf symmetry observable point) ↔
      ∀ point, antiInvariantHalf symmetry observable point = 0 := by
  constructor
  · rintro ⟨factor, specification⟩ point
    have eqNeg : antiInvariantHalf symmetry observable point =
        - antiInvariantHalf symmetry observable point := by
      calc
        antiInvariantHalf symmetry observable point =
            factor (axisClass symmetry point) :=
          (specification point).symm
        _ = factor (axisClass symmetry (symmetry.action point)) := by
          rw [action_preserves_axis_class]
        _ = antiInvariantHalf symmetry observable (symmetry.action point) :=
          specification (symmetry.action point)
        _ = - antiInvariantHalf symmetry observable point :=
          antiInvariantHalf_antiInvariant symmetry observable point
    have doubled :
        (2 : Value) * antiInvariantHalf symmetry observable point = 0 := by
      calc
        (2 : Value) * antiInvariantHalf symmetry observable point =
            antiInvariantHalf symmetry observable point +
              antiInvariantHalf symmetry observable point := by ring
        _ = antiInvariantHalf symmetry observable point +
              (- antiInvariantHalf symmetry observable point) := by
          exact congrArg
            (fun value : Value =>
              antiInvariantHalf symmetry observable point + value) eqNeg
        _ = 0 := add_neg_cancel _
    exact (mul_eq_zero.mp doubled).resolve_left (by norm_num)
  · intro zero
    refine ⟨fun _ => 0, ?_⟩
    intro point
    rw [zero point]

theorem antiInvariantHalf_eq_zero_iff_invariant
    (symmetry : FixedPointFreeInvolution Carrier)
    [Field Value] [CharZero Value]
    (observable : Carrier → Value) :
    (∀ point, antiInvariantHalf symmetry observable point = 0) ↔
      InvariantObservable symmetry observable := by
  constructor
  · intro zero point
    have halfZero : antiInvariantHalf symmetry observable point = 0 := zero point
    have differenceZero :
        observable point - observable (symmetry.action point) = 0 := by
      simpa using
        (div_eq_iff (by norm_num : (2 : Value) ≠ 0)).mp halfZero
    exact (sub_eq_zero.mp differenceZero).symm
  · intro invariant point
    change (observable point - observable (symmetry.action point)) / 2 = 0
    rw [sub_eq_zero.mpr (invariant point).symm, zero_div]

end FixedPointFreeInvolution

end OCKIndividuationMSpaceComposition
