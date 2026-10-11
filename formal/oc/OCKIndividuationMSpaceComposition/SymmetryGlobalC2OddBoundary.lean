import OCKIndividuationMSpaceComposition.SymmetryGlobalC2InvariantDecomposition

namespace OCKIndividuationMSpaceComposition

universe uCarrier uValue

namespace PrimitiveDistinction

/-!
# Boundary for odd observables outside a primitive pair

The canonical ambient pair swap fixes every point outside the distinguished
pair.  An anti-invariant observable must therefore equal its own negation at
such a point.  The exact consequence is `2 • value = 0`; vanishing itself
requires a separate no-two-torsion premise on the value type.

This makes the complement obstruction explicit in the observable layer.  It
does not silently extend the local C₂ action to the rest of the carrier.
-/

theorem carrierAntiInvariant_at_outside_two_nsmul_eq_zero
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [AddCommGroup Value]
    (observable : Carrier → Value)
    (antiInvariant : CarrierAntiInvariant distinction observable)
    (point : Carrier)
    (notFirst : point ≠ distinction.first)
    (notSecond : point ≠ distinction.second) :
    2 • observable point = 0 := by
  have fixedValue : observable point = - observable point := by
    simpa [distinction.pairSwap_outside point notFirst notSecond] using
      antiInvariant point
  calc
    2 • observable point = observable point + observable point := by
      rw [two_nsmul]
    _ = observable point + - observable point :=
      congrArg (fun value => observable point + value) fixedValue
    _ = 0 := add_neg_cancel _

theorem carrierAntiInvariantPart_at_outside_two_nsmul_eq_zero
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [AddCommGroup Value]
    (observable : Carrier → Value)
    (point : Carrier)
    (notFirst : point ≠ distinction.first)
    (notSecond : point ≠ distinction.second) :
    2 • distinction.carrierAntiInvariantPart observable point = 0 :=
  carrierAntiInvariant_at_outside_two_nsmul_eq_zero distinction
    (distinction.carrierAntiInvariantPart observable)
    (distinction.carrierAntiInvariantPart_antiInvariant observable)
    point notFirst notSecond

theorem carrierAntiInvariant_vanishes_at_outside_of_no_two_torsion
    {Carrier : Type uCarrier} {Value : Type uValue}
    (distinction : PrimitiveDistinction Carrier)
    [AddCommGroup Value]
    (observable : Carrier → Value)
    (antiInvariant : CarrierAntiInvariant distinction observable)
    (noTwoTorsion : ∀ value : Value, 2 • value = 0 → value = 0)
    (point : Carrier)
    (notFirst : point ≠ distinction.first)
    (notSecond : point ≠ distinction.second) :
    observable point = 0 :=
  noTwoTorsion (observable point)
    (carrierAntiInvariant_at_outside_two_nsmul_eq_zero distinction
      observable antiInvariant point notFirst notSecond)

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
