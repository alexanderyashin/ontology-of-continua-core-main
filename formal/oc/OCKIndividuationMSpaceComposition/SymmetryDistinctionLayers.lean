import OCKIndividuationMSpaceComposition.SymmetryLayerSynthesis
import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinction

namespace OCKIndividuationMSpaceComposition

universe uCarrier

/-!
# Primitive distinction integrated with the existing R1/R2/R3 layers

This module does not introduce another symmetry interpretation.  It applies
the already proved R1/R2/R3 layer-synthesis theorems to the R3 torsor derived
from a primitive distinction.  Hence the invariant boundary, relative
separator and odd polarity become consequences of the primitive pair.
-/

namespace PrimitiveDistinction

/-- The existing R1 canonical-separator layer instantiated on the generated
axis. -/
noncomputable def generatedCanonicalSeparator {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :=
  r3CanonicalSeparator distinction.toR3Torsor distinction.axisFirst

/-- The existing R2 odd-sign layer instantiated on the same derived torsor. -/
noncomputable def generatedAxisSignPairing {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :=
  r3AxisSignPairing distinction.toR3Torsor distinction.axisFirst

/-- The relative R1 separator is exactly the negative fiber of the derived
polarity coordinate. -/
theorem generatedSeparator_iff_polarity_false
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) :
    (distinction.generatedCanonicalSeparator).separator point ↔
      distinction.generatedPolarity point = false := by
  simpa [generatedCanonicalSeparator, generatedPolarity] using
    r3_separator_iff_sign_false distinction.toR3Torsor
      distinction.axisFirst point

/-- The R1 quotient boundary is constant across the two generated poles. -/
theorem generatedBoundary_projection_constant
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) :
    (distinction.generatedCanonicalSeparator).projection point =
      (distinction.generatedCanonicalSeparator).boundary := by
  simpa [generatedCanonicalSeparator] using
    r3_boundary_projection_constant distinction.toR3Torsor
      distinction.axisFirst point

/-- The primitive swap preserves the invariant R1 boundary while negating
the R2/R3 polarity. -/
theorem generatedSwap_preserves_boundary_and_negates_polarity
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) :
    (distinction.generatedCanonicalSeparator).projection
        (distinction.axisSwap point) =
        (distinction.generatedCanonicalSeparator).projection point ∧
      distinction.generatedPolarity (distinction.axisSwap point) =
        Bool.not (distinction.generatedPolarity point) := by
  simpa [generatedCanonicalSeparator, generatedPolarity, toR3Torsor] using
    r3_reversal_preserves_boundary_and_negates_sign distinction.toR3Torsor
      distinction.axisFirst point

/-- Complete R1/R2/R3 compatibility specialized to a primitive distinction:
constant invariant boundary, separator/sign agreement and odd reversal. -/
theorem generated_r1_r2_r3_layer_synthesis
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (point : distinction.Axis) :
    (distinction.generatedCanonicalSeparator).projection point =
        (distinction.generatedCanonicalSeparator).boundary ∧
      ((distinction.generatedCanonicalSeparator).separator point ↔
        (distinction.generatedAxisSignPairing).sign
          (r3AxisPoint distinction.toR3Torsor distinction.axisFirst point) =
            false) ∧
      (distinction.generatedAxisSignPairing).sign
          (r3AxisPoint distinction.toR3Torsor distinction.axisFirst
            (distinction.axisSwap point)) =
        Bool.not ((distinction.generatedAxisSignPairing).sign
          (r3AxisPoint distinction.toR3Torsor distinction.axisFirst point)) := by
  simpa [generatedCanonicalSeparator, generatedAxisSignPairing,
    toR3Torsor] using
    r3_r1_r2_r3_layer_synthesis distinction.toR3Torsor
      distinction.axisFirst point

/-- The odd side coordinate cannot be recovered from the invariant boundary;
the distinction erased by quotienting is mathematically real. -/
theorem generatedSign_does_not_factor_through_boundary
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier) :
    ¬ ∃ factor :
        AxisQuotient
          (axisSwapInvolution
            (r3FixedPointFreeInvolution distinction.toR3Torsor)
            distinction.axisFirst) → Bool,
      ∀ point,
        factor (axisClass
          (axisSwapInvolution
            (r3FixedPointFreeInvolution distinction.toR3Torsor)
            distinction.axisFirst) point) =
          (distinction.generatedAxisSignPairing).sign point := by
  simpa [generatedAxisSignPairing] using
    r3_sign_does_not_factor_through_boundary distinction.toR3Torsor
      distinction.axisFirst

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
