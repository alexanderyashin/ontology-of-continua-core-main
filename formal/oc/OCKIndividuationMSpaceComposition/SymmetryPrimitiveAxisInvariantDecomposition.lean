import OCKIndividuationMSpaceComposition.SymmetryPrimitiveAxisAutomorphism
import Mathlib.Tactic.Abel

namespace OCKIndividuationMSpaceComposition

universe uCarrier uValue

namespace PrimitiveDistinction

/-!
# Invariant and odd layers on a primitive axis

The local swap derived from a separated pair gives a genuine order-two
symmetry.  This file applies that symmetry to an arbitrary observable with
values in an additive commutative group.  The symmetric layer is the orbit
sum `f + f ∘ reverse`; the odd layer is the contrast `f - f ∘ reverse`.

The construction is intentionally honest about characteristic and
normalisation.  The two layers always reconstruct `2 • f`, but recovering
`f` itself from half-sums requires an additional premise making two
invertible.  No such premise is smuggled into the primitive distinction.
-/

/-- An observable is invariant when it is unchanged by the derived local swap. -/
noncomputable def AxisInvariant
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (observable : distinction.Axis → Value)
    [Zero Value] : Prop :=
  ∀ point, observable (distinction.axisSwap point) = observable point

/-- An observable is anti-invariant (odd) when reversal negates its value. -/
noncomputable def AxisAntiInvariant
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    (observable : distinction.Axis → Value)
    [Neg Value] : Prop :=
  ∀ point, observable (distinction.axisSwap point) = - observable point

/-- The invariant/orbit-sum layer of an additive observable. -/
noncomputable def invariantPart
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [Add Value] (observable : distinction.Axis → Value) :
    distinction.Axis → Value :=
  fun point => observable point + observable (distinction.axisSwap point)

/-- The odd/contrast layer of an additive observable. -/
noncomputable def antiInvariantPart
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [Sub Value] (observable : distinction.Axis → Value) :
    distinction.Axis → Value :=
  fun point => observable point - observable (distinction.axisSwap point)

/-- Invariance on the two-point axis is equivalent to equality of the two
endpoint values. -/
theorem axisInvariant_iff_endpoint_equal
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [Zero Value]
    (observable : distinction.Axis → Value) :
    AxisInvariant distinction observable ↔
      observable distinction.axisFirst = observable distinction.axisSecond := by
  constructor
  · intro invariant
    have endpoint := invariant distinction.axisFirst
    simpa [distinction.axisSwap_first] using endpoint.symm
  · intro endpointEqual point
    rcases distinction.axis_cases point with pointFirst | pointSecond
    · subst point
      simpa [distinction.axisSwap_first] using endpointEqual.symm
    · subst point
      simpa [distinction.axisSwap_second] using endpointEqual

/-- Every invariant observable on the generated axis is constant, and its
constant value is its value at the displayed first endpoint. -/
theorem axisInvariant_eq_constant
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [Zero Value]
    (observable : distinction.Axis → Value)
    (invariant : AxisInvariant distinction observable) (point : distinction.Axis) :
    observable point = observable distinction.axisFirst := by
  rcases distinction.axis_cases point with pointFirst | pointSecond
  · exact congrArg observable pointFirst
  · subst point
    have endpoint := invariant distinction.axisFirst
    simpa [distinction.axisSwap_first] using endpoint

/-- The orbit-sum layer is invariant under reversal. -/
theorem invariantPart_invariant
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [AddCommMonoid Value]
    (observable : distinction.Axis → Value) :
    AxisInvariant distinction (distinction.invariantPart observable) := by
  intro point
  change observable (distinction.axisSwap point) +
      observable (distinction.axisSwap (distinction.axisSwap point)) =
    observable point + observable (distinction.axisSwap point)
  rw [distinction.axisSwap_involutive]
  exact add_comm _ _

/-- The contrast layer is anti-invariant under reversal. -/
theorem antiInvariantPart_antiInvariant
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [AddCommGroup Value]
    (observable : distinction.Axis → Value) :
    AxisAntiInvariant distinction (distinction.antiInvariantPart observable) := by
  intro point
  change observable (distinction.axisSwap point) -
      observable (distinction.axisSwap (distinction.axisSwap point)) =
    -(observable point - observable (distinction.axisSwap point))
  rw [distinction.axisSwap_involutive]
  abel

/-- The invariant and odd layers reconstruct twice the original observable.
This is the exact statement available without assuming that `2` is invertible
in the value group. -/
theorem invariantPart_add_antiInvariantPart_eq_two_smul
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [AddCommGroup Value]
    (observable : distinction.Axis → Value) (point : distinction.Axis) :
    distinction.invariantPart observable point +
        distinction.antiInvariantPart observable point =
      2 • observable point := by
  change (observable point + observable (distinction.axisSwap point)) +
      (observable point - observable (distinction.axisSwap point)) =
    2 • observable point
  rw [two_nsmul]
  abel

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
