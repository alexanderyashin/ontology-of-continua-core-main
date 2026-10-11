import OCKIndividuationMSpaceComposition.SemanticPredictionContract

namespace OCKIndividuationMSpaceComposition

/-!
# Composition of set-valued mechanism uncertainty and residual uncertainty

The mechanism layer supplies a hull containing the conditional centre selected
by the realized successor.  The calibration layer supplies an absolute residual
bound around that centre.  Their operational composition is interval inflation.

This is standard interval/Minkowski arithmetic (`REUSE`).  The OC-specific role
is the typed bridge: destination continuation, response-hull containment and
residual calibration remain separate premises and may fail separately.
-/

namespace ScalarForecastHull

/-- Positive bridge theorem: containment of the realized conditional centre in
the successor-response hull plus a residual certificate around that centre is
sufficient for containment of the physical target in the inflated hull. -/
theorem contained_center_and_residual_bound_yield_inflated_target
    (hull : ScalarForecastHull) (center target radius : ℝ)
    (centerContained : Contains hull center)
    (residualBound : |target - center| ≤ radius) :
    Contains (inflate hull radius) target := by
  have residualSides := abs_le.mp residualBound
  constructor
  · dsimp [Contains, inflate] at centerContained ⊢
    linarith [centerContained.1, residualSides.1]
  · dsimp [Contains, inflate] at centerContained ⊢
    linarith [centerContained.2, residualSides.2]

/-- No-go countermodel: a hull may contain the conditional mechanism centre
exactly while failing to contain the realized physical target.  Destination or
oracle-response containment therefore cannot replace a residual premise. -/
theorem mechanism_center_containment_alone_does_not_imply_target_containment :
    ∃ (hull : ScalarForecastHull) (center target : ℝ),
      Contains hull center ∧ ¬ Contains hull target := by
  refine ⟨{ lower := 0, upper := 0 }, 0, 1, ?_, ?_⟩
  · norm_num [Contains]
  · norm_num [Contains]

/-- Minimality of the composed envelope: any candidate hull required to cover
the lower and upper extreme residual worlds must contain the explicitly
inflated mechanism hull. -/
theorem inflated_hull_is_minimal_for_extreme_residual_worlds
    (mechanism candidate : ScalarForecastHull) (radius : ℝ)
    (coversLower : Contains candidate (mechanism.lower - radius))
    (coversUpper : Contains candidate (mechanism.upper + radius)) :
    Refines (inflate mechanism radius) candidate := by
  exact ⟨coversLower.1, coversUpper.2⟩

/-- Width accounting for the composed forecast is exact, not heuristic: the
mechanism diameter is retained and the residual layer costs exactly `2r`. -/
theorem composed_width_exact
    (mechanism : ScalarForecastHull) (radius : ℝ) :
    (inflate mechanism radius).upper - (inflate mechanism radius).lower =
      (mechanism.upper - mechanism.lower) + 2 * radius :=
  inflate_width mechanism radius

end ScalarForecastHull

end OCKIndividuationMSpaceComposition
