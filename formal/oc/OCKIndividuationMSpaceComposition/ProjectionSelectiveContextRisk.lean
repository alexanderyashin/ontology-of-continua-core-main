import OCKIndividuationMSpaceComposition.ContextRiskDecomposition

namespace OCKIndividuationMSpaceComposition

/-!
# Projection-selective predictive value

The same continuation context need not have the same predictive value for
different declared projections.  This module lifts the exact context-risk law
to a projection-indexed surface and exposes the net-signal admission rule.
-/

section

variable {E F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F]

/-- Squared risk after applying the declared task projection. -/
def ProjectedSquaredPredictionRisk
    (projection : E → F) (truth prediction : E) : ℝ :=
  SquaredPredictionRisk (projection truth) (projection prediction)

/-- Prediction-shift energy visible through the declared projection. -/
def ProjectedContextSignalEnergy
    (projection : E → F) (historyPrediction contextPrediction : E) : ℝ :=
  ContextSignalEnergy (projection historyPrediction) (projection contextPrediction)

/-- Residual alignment visible through the declared projection. -/
def ProjectedContextResidualAlignment
    (projection : E → F) (truth historyPrediction contextPrediction : E) : ℝ :=
  inner ℝ (projection truth - projection contextPrediction)
    (projection contextPrediction - projection historyPrediction)

/-- Relative context gain for one declared task projection. -/
noncomputable def ProjectedRelativeContextGain
    (projection : E → F) (truth historyPrediction contextPrediction : E) : ℝ :=
  RelativeContextGain (projection truth) (projection historyPrediction)
    (projection contextPrediction)

/-- Exact projection-indexed operational law. -/
theorem projected_relative_context_gain_eq_net_signal_ratio
    (projection : E → F) (truth historyPrediction contextPrediction : E) :
    ProjectedRelativeContextGain projection truth historyPrediction contextPrediction =
      (ProjectedContextSignalEnergy projection historyPrediction contextPrediction +
        2 * ProjectedContextResidualAlignment projection truth historyPrediction
          contextPrediction) /
        ProjectedSquaredPredictionRisk projection truth historyPrediction := by
  simp only [ProjectedRelativeContextGain, ProjectedContextSignalEnergy,
    ProjectedContextResidualAlignment, ProjectedSquaredPredictionRisk,
    RelativeContextGain]
  rw [context_squared_risk_general_decomposition
    (projection truth) (projection historyPrediction) (projection contextPrediction)]
  ring

/-- A projected context refinement helps exactly when its projected net signal
is positive. -/
theorem projected_context_refinement_improves_iff_positive_net_signal
    (projection : E → F) (truth historyPrediction contextPrediction : E) :
    ProjectedSquaredPredictionRisk projection truth contextPrediction <
        ProjectedSquaredPredictionRisk projection truth historyPrediction ↔
      0 < ProjectedContextSignalEnergy projection historyPrediction contextPrediction +
        2 * ProjectedContextResidualAlignment projection truth historyPrediction
          contextPrediction := by
  exact context_refinement_improves_iff_positive_net_signal
    (projection truth) (projection historyPrediction) (projection contextPrediction)

/-- Positive inherited law under a projected orthogonality contract. -/
theorem projected_context_squared_risk_decomposition
    (projection : E → F) (truth historyPrediction contextPrediction : E)
    (orthogonal :
      ContextResidualOrthogonal (projection truth) (projection historyPrediction)
        (projection contextPrediction)) :
    ProjectedSquaredPredictionRisk projection truth historyPrediction =
      ProjectedSquaredPredictionRisk projection truth contextPrediction +
        ProjectedContextSignalEnergy projection historyPrediction contextPrediction := by
  exact context_squared_risk_decomposition
    (projection truth) (projection historyPrediction) (projection contextPrediction)
      orthogonal

/-- Projection selectivity is possible even with the same truth and candidate
predictions: one projection can expose strict value while another exposes no
change at all. -/
theorem exists_projection_selective_context_value :
    ∃ truth historyPrediction contextPrediction : ℝ,
      ∃ valuableProjection neutralProjection : ℝ → ℝ,
        ProjectedSquaredPredictionRisk valuableProjection truth contextPrediction <
          ProjectedSquaredPredictionRisk valuableProjection truth historyPrediction ∧
        ProjectedSquaredPredictionRisk neutralProjection truth contextPrediction =
          ProjectedSquaredPredictionRisk neutralProjection truth historyPrediction := by
  refine ⟨1, 0, 1, id, (fun _ => 0), ?_, ?_⟩
  · norm_num [ProjectedSquaredPredictionRisk, SquaredPredictionRisk]
  · norm_num [ProjectedSquaredPredictionRisk, SquaredPredictionRisk]

end

end OCKIndividuationMSpaceComposition
