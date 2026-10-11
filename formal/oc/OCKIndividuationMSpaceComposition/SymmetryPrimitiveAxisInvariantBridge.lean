import OCKIndividuationMSpaceComposition.SymmetryPrimitiveAxisInvariantDecomposition
import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionDecomposition
import Mathlib.Algebra.Algebra.Defs
import Mathlib.Tactic
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

universe uCarrier uScalar

namespace PrimitiveDistinction

/-!
# Bridge between unnormalised and normalised axis decompositions

The primitive-axis invariant module deliberately works in an arbitrary
additive commutative group: the orbit sum and contrast always reconstruct
`2 • f`.  The older decomposition module works over a characteristic-zero
field and divides those same layers by two.  This file proves that the two
presentations are the same decomposition at different normalisation levels.

The bridge is semantic rather than terminological.  It exposes exactly where
the field assumption enters and prevents a normalised even/odd statement from
being mistaken for a consequence of bare two-point distinction.
-/

theorem evenObservable_iff_axisInvariant
    {Carrier : Type uCarrier} {Scalar : Type uScalar}
    (distinction : PrimitiveDistinction Carrier)
    [Zero Scalar]
    (observable : distinction.Axis → Scalar) :
    EvenObservable distinction observable ↔
      AxisInvariant distinction observable := by
  rfl

theorem oddObservable_iff_axisAntiInvariant
    {Carrier : Type uCarrier} {Scalar : Type uScalar}
    [Neg Scalar]
    (distinction : PrimitiveDistinction Carrier)
    (observable : distinction.Axis → Scalar) :
    OddObservable distinction observable ↔
      AxisAntiInvariant distinction observable := by
  rfl

theorem generatedEvenPart_eq_inv_two_smul_invariantPart
    {Carrier : Type uCarrier} {Scalar : Type uScalar}
    [Field Scalar] [CharZero Scalar]
    (distinction : PrimitiveDistinction Carrier)
    (observable : distinction.Axis → Scalar) (point : distinction.Axis) :
    distinction.generatedEvenPart observable point =
      (2 : Scalar)⁻¹ • distinction.invariantPart observable point := by
  simp only [generatedEvenPart, invariantPart, smul_eq_mul, div_eq_mul_inv]
  ring

theorem generatedOddPart_eq_inv_two_smul_antiInvariantPart
    {Carrier : Type uCarrier} {Scalar : Type uScalar}
    [Field Scalar] [CharZero Scalar]
    (distinction : PrimitiveDistinction Carrier)
    (observable : distinction.Axis → Scalar) (point : distinction.Axis) :
    distinction.generatedOddPart observable point =
      (2 : Scalar)⁻¹ • distinction.antiInvariantPart observable point := by
  simp only [generatedOddPart, antiInvariantPart, smul_eq_mul, div_eq_mul_inv]
  ring

theorem invariantPart_eq_two_smul_generatedEvenPart
    {Carrier : Type uCarrier} {Scalar : Type uScalar}
    [Field Scalar] [CharZero Scalar]
    (distinction : PrimitiveDistinction Carrier)
    (observable : distinction.Axis → Scalar) (point : distinction.Axis) :
    distinction.invariantPart observable point =
      2 • distinction.generatedEvenPart observable point := by
  rw [distinction.generatedEvenPart_eq_inv_two_smul_invariantPart]
  have two_ne : (2 : Scalar) ≠ 0 := by norm_num
  simp only [two_nsmul, smul_eq_mul]
  rw [← two_mul, ← mul_assoc, mul_inv_cancel₀ two_ne, one_mul]

theorem antiInvariantPart_eq_two_smul_generatedOddPart
    {Carrier : Type uCarrier} {Scalar : Type uScalar}
    [Field Scalar] [CharZero Scalar]
    (distinction : PrimitiveDistinction Carrier)
    (observable : distinction.Axis → Scalar) (point : distinction.Axis) :
    distinction.antiInvariantPart observable point =
      2 • distinction.generatedOddPart observable point := by
  rw [distinction.generatedOddPart_eq_inv_two_smul_antiInvariantPart]
  have two_ne : (2 : Scalar) ≠ 0 := by norm_num
  simp only [two_nsmul, smul_eq_mul]
  rw [← two_mul, ← mul_assoc, mul_inv_cancel₀ two_ne, one_mul]

theorem normalised_reconstruction_is_unscaled_reconstruction
    {Carrier : Type uCarrier} {Scalar : Type uScalar}
    [Field Scalar] [CharZero Scalar]
    (distinction : PrimitiveDistinction Carrier)
    (observable : distinction.Axis → Scalar) (point : distinction.Axis) :
    distinction.generatedEvenPart observable point +
        distinction.generatedOddPart observable point = observable point := by
  exact distinction.generated_even_odd_reconstruction observable point

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
