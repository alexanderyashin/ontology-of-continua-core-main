import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinction

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# Uniqueness of the swap derived from a primitive distinction

The generated axis has exactly two points.  Consequently, once a candidate
operation is required to exchange the two endpoints, its value is forced at
every point.  More strongly, fixed-point-freeness alone already forces that
exchange; no involution, transitivity, group law, or C₂ interface is needed as
an additional premise.  The existing derived `axisSwap` is therefore the
unique fixed-point-free self-map of the generated axis.

This is a uniqueness result, not a hidden redefinition of freeness: the
candidate map is arbitrary and the only premise supplied to the stronger
theorem is the stated pointwise non-fixed-point condition.
-/

/-- Any map that exchanges both displayed endpoints is the canonical swap. -/
theorem axisSwap_unique_of_endpoint_exchange
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (candidate : distinction.Axis → distinction.Axis)
    (first_maps : candidate distinction.axisFirst = distinction.axisSecond)
    (second_maps : candidate distinction.axisSecond = distinction.axisFirst) :
    candidate = distinction.axisSwap := by
  funext point
  rcases distinction.axis_cases point with pointFirst | pointSecond
  · subst point
    rw [first_maps, axisSwap_first]
  · subst point
    rw [second_maps, axisSwap_second]

/-- On a two-point generated axis, fixed-point-freeness alone forces endpoint
exchange and hence identifies the candidate with the derived swap. -/
theorem axisSwap_unique_of_fixedPointFree
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (candidate : distinction.Axis → distinction.Axis)
    (fixedPointFree : ∀ point, candidate point ≠ point) :
    candidate = distinction.axisSwap := by
  apply axisSwap_unique_of_endpoint_exchange distinction candidate
  · rcases distinction.axis_cases (candidate distinction.axisFirst) with
      candidateFirst | candidateSecond
    · exact (fixedPointFree distinction.axisFirst candidateFirst).elim
    · exact candidateSecond
  · rcases distinction.axis_cases (candidate distinction.axisSecond) with
      candidateFirst | candidateSecond
    · exact candidateFirst
    · exact (fixedPointFree distinction.axisSecond candidateSecond).elim

/-- Existence and uniqueness of the fixed-point-free map on the generated
axis.  Its involutivity is supplied separately by `axisSwap_involutive`. -/
theorem existsUnique_fixedPointFree_axisMap
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    ∃! candidate : distinction.Axis → distinction.Axis,
      ∀ point, candidate point ≠ point := by
  refine ⟨distinction.axisSwap, distinction.axisSwap_fixedPointFree, ?_⟩
  intro candidate candidateFree
  exact axisSwap_unique_of_fixedPointFree distinction candidate candidateFree

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
