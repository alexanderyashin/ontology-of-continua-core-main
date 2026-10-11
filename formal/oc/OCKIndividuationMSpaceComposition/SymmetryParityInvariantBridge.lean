import OCKIndividuationMSpaceComposition.SymmetryInvariantQuotient
import OCKIndividuationMSpaceComposition.SymmetryDistinctionDimensionBoundary

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# Invariant and orientation-dependent layers of a generated axis

The generated two-point axis has two observables with different symmetry
status.  Its Boolean polarity records the chosen orientation and therefore
cannot descend to the quotient by reversal.  A simultaneous endpoint-pair
magnitude is invariant and does descend.  This is the smallest concrete
instance of the invariant/odd split required by the symmetry programme.
-/

/-! The magnitude of a point against its reversed partner. -/
noncomputable def diagonalDiscreteMagnitude
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) : Nat :=
  distinction.axisDiscreteMagnitude point (distinction.axisSwap point)

theorem diagonalDiscreteMagnitude_eq_one
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) :
    distinction.diagonalDiscreteMagnitude point = 1 := by
  rcases distinction.axis_cases point with pointFirst | pointSecond
  · subst point
    simp [diagonalDiscreteMagnitude, axisDiscreteMagnitude,
      distinction.axisFirst_ne_axisSecond]
  · subst point
    simp [diagonalDiscreteMagnitude, axisDiscreteMagnitude,
      Ne.symm distinction.axisFirst_ne_axisSecond]

/-! The pair magnitude is constant, hence invariant under local reversal. -/
theorem diagonalDiscreteMagnitude_invariant
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    InvariantObservable distinction.toFixedPointFreeInvolution
      distinction.diagonalDiscreteMagnitude := by
  intro point
  rw [distinction.diagonalDiscreteMagnitude_eq_one,
    distinction.diagonalDiscreteMagnitude_eq_one]

theorem diagonalDiscreteMagnitude_factors_through_axis_quotient
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    ∃ factor : AxisQuotient distinction.toFixedPointFreeInvolution → Nat,
      ∀ point,
        factor (axisClass distinction.toFixedPointFreeInvolution point) =
          distinction.diagonalDiscreteMagnitude point :=
  invariant_observable_factors_through_axis_quotient
    distinction.toFixedPointFreeInvolution distinction.diagonalDiscreteMagnitude
    distinction.diagonalDiscreteMagnitude_invariant

/-! Polarity is the complementary, orientation-sensitive observable. -/
theorem generatedPolarity_breaks_local_symmetry
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    SymmetryBreakingWitness distinction.toFixedPointFreeInvolution
      distinction.generatedPolarity distinction.axisFirst := by
  change distinction.generatedPolarity
      (distinction.axisSwap distinction.axisFirst) ≠
    distinction.generatedPolarity distinction.axisFirst
  simp

theorem generatedPolarity_does_not_factor_through_axis_quotient
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    ¬ ∃ factor : AxisQuotient distinction.toFixedPointFreeInvolution → Bool,
      ∀ point,
        factor (axisClass distinction.toFixedPointFreeInvolution point) =
          distinction.generatedPolarity point :=
  symmetry_breaking_forbids_axis_quotient_factor
    distinction.toFixedPointFreeInvolution distinction.generatedPolarity
    distinction.axisFirst distinction.generatedPolarity_breaks_local_symmetry

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
