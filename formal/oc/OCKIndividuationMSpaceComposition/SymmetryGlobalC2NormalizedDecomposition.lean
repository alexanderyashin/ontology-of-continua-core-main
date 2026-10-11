import OCKIndividuationMSpaceComposition.SymmetryGlobalC2InvariantDecomposition
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

universe uCarrier uValue

namespace PrimitiveDistinction

/-!
# Normalized global even/odd decomposition

The ambient invariant/anti-invariant layers are defined for arbitrary
additive groups and therefore reconstruct only `2 • f`.  Over a
characteristic-zero field, division by two is legitimate.  This module
proves the missing global statement: every observable splits canonically into
an invariant half-sum and an anti-invariant half-difference, and that split is
unique among all invariant/anti-invariant decompositions.

Coverage is not required for the algebraic splitting; it is needed only when
the resulting invariant layer is interpreted through the global pair
quotient.  No extra action or dimension premise is introduced.
-/

/-- The normalized global invariant (even) projection. -/
noncomputable def carrierInvariantHalf
    {Carrier : Type uCarrier} {Value : Type uValue}
    [Field Value] [CharZero Value]
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value) : Carrier → Value :=
  fun point =>
    (observable point + observable (distinction.pairSwap point)) / 2

/-- The normalized global anti-invariant (odd) projection. -/
noncomputable def carrierAntiInvariantHalf
    {Carrier : Type uCarrier} {Value : Type uValue}
    [Field Value] [CharZero Value]
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value) : Carrier → Value :=
  fun point =>
    (observable point - observable (distinction.pairSwap point)) / 2

theorem carrierInvariantHalf_invariant
    {Carrier : Type uCarrier} {Value : Type uValue}
    [Field Value] [CharZero Value]
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value) :
    CarrierInvariant distinction (distinction.carrierInvariantHalf observable) := by
  intro point
  simp only [carrierInvariantHalf, distinction.pairSwap_involutive point]
  ring

theorem carrierAntiInvariantHalf_antiInvariant
    {Carrier : Type uCarrier} {Value : Type uValue}
    [Field Value] [CharZero Value]
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value) :
    CarrierAntiInvariant distinction
      (distinction.carrierAntiInvariantHalf observable) := by
  intro point
  simp only [carrierAntiInvariantHalf, distinction.pairSwap_involutive point]
  ring

theorem carrierInvariantHalf_add_carrierAntiInvariantHalf_eq_observable
    {Carrier : Type uCarrier} {Value : Type uValue}
    [Field Value] [CharZero Value]
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value) (point : Carrier) :
    distinction.carrierInvariantHalf observable point +
        distinction.carrierAntiInvariantHalf observable point =
      observable point := by
  simp only [carrierInvariantHalf, carrierAntiInvariantHalf]
  ring

/-- Any invariant/anti-invariant decomposition of an observable is the
canonical half-sum/half-difference decomposition. -/
theorem carrier_even_odd_decomposition_unique
    {Carrier : Type uCarrier} {Value : Type uValue}
    [Field Value] [CharZero Value]
    (distinction : PrimitiveDistinction Carrier)
    (observable evenPart oddPart : Carrier → Value)
    (even : CarrierInvariant distinction evenPart)
    (odd : CarrierAntiInvariant distinction oddPart)
    (reconstruct : ∀ point, evenPart point + oddPart point = observable point) :
    (∀ point,
      evenPart point = distinction.carrierInvariantHalf observable point) ∧
    (∀ point,
      oddPart point = distinction.carrierAntiInvariantHalf observable point) := by
  constructor
  · intro point
    have atSwap := reconstruct (distinction.pairSwap point)
    rw [even point, odd point] at atSwap
    have atSwap' : evenPart point - oddPart point =
        observable (distinction.pairSwap point) := by
      simpa [sub_eq_add_neg] using atSwap
    have atPoint := reconstruct point
    change evenPart point =
      (observable point + observable (distinction.pairSwap point)) / 2
    apply (eq_div_iff (by norm_num : (2 : Value) ≠ 0)).2
    calc
      evenPart point * 2 =
          (evenPart point + oddPart point) +
            (evenPart point - oddPart point) := by ring
      _ = observable point + observable (distinction.pairSwap point) := by
        rw [atPoint, atSwap']
  · intro point
    have atSwap := reconstruct (distinction.pairSwap point)
    rw [even point, odd point] at atSwap
    have atSwap' : evenPart point - oddPart point =
        observable (distinction.pairSwap point) := by
      simpa [sub_eq_add_neg] using atSwap
    have atPoint := reconstruct point
    change oddPart point =
      (observable point - observable (distinction.pairSwap point)) / 2
    apply (eq_div_iff (by norm_num : (2 : Value) ≠ 0)).2
    calc
      oddPart point * 2 =
          (evenPart point + oddPart point) -
            (evenPart point - oddPart point) := by ring
      _ = observable point - observable (distinction.pairSwap point) := by
        rw [atPoint, atSwap']

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
