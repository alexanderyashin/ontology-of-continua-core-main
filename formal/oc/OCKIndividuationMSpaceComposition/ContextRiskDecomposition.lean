import Mathlib.Analysis.InnerProductSpace.Basic

namespace OCKIndividuationMSpaceComposition

/-!
# Exact predictive value of an added context

For squared loss, an orthogonal refinement of a history-only prediction has
an exact Pythagorean risk decomposition.  The context contribution is the
squared norm of the prediction shift.  This both supplies the positive law
used by the empirical bridge and rules out a domain-independent positive
percentage without an explicit context-signal floor.
-/

section

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- Pointwise squared prediction loss in a real Hilbert outcome space. -/
def SquaredPredictionRisk (truth prediction : E) : ℝ :=
  ‖truth - prediction‖ ^ 2

/-- Energy added to the prediction when the declared context is admitted. -/
def ContextSignalEnergy (historyPrediction contextPrediction : E) : ℝ :=
  ‖contextPrediction - historyPrediction‖ ^ 2

/-- The refined residual is orthogonal to the prediction change.  Conditional
expectation and nested least-squares projection instantiate this contract. -/
def ContextResidualOrthogonal
    (truth historyPrediction contextPrediction : E) : Prop :=
  inner ℝ (truth - contextPrediction) (contextPrediction - historyPrediction) = 0

/-- Dimensionless risk reduction relative to the history-only prediction. -/
noncomputable def RelativeContextGain
    (truth historyPrediction contextPrediction : E) : ℝ :=
  (SquaredPredictionRisk truth historyPrediction -
    SquaredPredictionRisk truth contextPrediction) /
      SquaredPredictionRisk truth historyPrediction

/-- Unconditional algebraic law.  Without the projection contract the observed
risk change also contains residual alignment, so predictive gain may not be
attributed to context-signal energy alone. -/
theorem context_squared_risk_general_decomposition
    (truth historyPrediction contextPrediction : E) :
    SquaredPredictionRisk truth historyPrediction =
      SquaredPredictionRisk truth contextPrediction +
        ContextSignalEnergy historyPrediction contextPrediction +
          2 * inner ℝ (truth - contextPrediction)
            (contextPrediction - historyPrediction) := by
  have decomposition :
      truth - historyPrediction =
        (truth - contextPrediction) +
          (contextPrediction - historyPrediction) := by
    abel
  calc
    SquaredPredictionRisk truth historyPrediction =
        ‖(truth - contextPrediction) +
          (contextPrediction - historyPrediction)‖ ^ 2 := by
      rw [SquaredPredictionRisk, decomposition]
    _ = ‖truth - contextPrediction‖ ^ 2 +
        2 * inner ℝ (truth - contextPrediction)
          (contextPrediction - historyPrediction) +
        ‖contextPrediction - historyPrediction‖ ^ 2 := by
      exact norm_add_sq_real _ _
    _ = SquaredPredictionRisk truth contextPrediction +
        ContextSignalEnergy historyPrediction contextPrediction +
          2 * inner ℝ (truth - contextPrediction)
            (contextPrediction - historyPrediction) := by
      simp only [SquaredPredictionRisk, ContextSignalEnergy]
      ring

/-- Operational improvement criterion without assuming orthogonality.  A
context refinement helps exactly when its prediction-shift energy plus twice
its residual alignment is positive. -/
theorem context_refinement_improves_iff_positive_net_signal
    (truth historyPrediction contextPrediction : E) :
    SquaredPredictionRisk truth contextPrediction <
        SquaredPredictionRisk truth historyPrediction ↔
      0 < ContextSignalEnergy historyPrediction contextPrediction +
        2 * inner ℝ (truth - contextPrediction)
          (contextPrediction - historyPrediction) := by
  rw [context_squared_risk_general_decomposition truth historyPrediction
    contextPrediction]
  constructor <;> intro hypothesis <;> linarith

/-- Exact failure boundary: a context refinement increases risk precisely when
the residual alignment is more negative than half the shift energy. -/
theorem context_refinement_worsens_iff_alignment_below_boundary
    (truth historyPrediction contextPrediction : E) :
    SquaredPredictionRisk truth historyPrediction <
        SquaredPredictionRisk truth contextPrediction ↔
      inner ℝ (truth - contextPrediction)
          (contextPrediction - historyPrediction) <
        -(ContextSignalEnergy historyPrediction contextPrediction / 2) := by
  rw [context_squared_risk_general_decomposition truth historyPrediction
    contextPrediction]
  constructor <;> intro hypothesis <;> linarith

/-- Exact neutral boundary separating helpful from harmful refinement. -/
theorem context_refinement_neutral_iff_alignment_on_boundary
    (truth historyPrediction contextPrediction : E) :
    SquaredPredictionRisk truth historyPrediction =
        SquaredPredictionRisk truth contextPrediction ↔
      inner ℝ (truth - contextPrediction)
          (contextPrediction - historyPrediction) =
        -(ContextSignalEnergy historyPrediction contextPrediction / 2) := by
  rw [context_squared_risk_general_decomposition truth historyPrediction
    contextPrediction]
  constructor <;> intro hypothesis <;> linarith

/-- Positive law: squared history risk is refined risk plus exactly the energy
of the context-induced prediction change. -/
theorem context_squared_risk_decomposition
    (truth historyPrediction contextPrediction : E)
    (orthogonal :
      ContextResidualOrthogonal truth historyPrediction contextPrediction) :
    SquaredPredictionRisk truth historyPrediction =
      SquaredPredictionRisk truth contextPrediction +
        ContextSignalEnergy historyPrediction contextPrediction := by
  have decomposition :
      truth - historyPrediction =
        (truth - contextPrediction) +
          (contextPrediction - historyPrediction) := by
    abel
  calc
    SquaredPredictionRisk truth historyPrediction =
        ‖(truth - contextPrediction) +
          (contextPrediction - historyPrediction)‖ ^ 2 := by
      rw [SquaredPredictionRisk, decomposition]
    _ = ‖truth - contextPrediction‖ ^ 2 +
        ‖contextPrediction - historyPrediction‖ ^ 2 := by
      have pythagoras :=
        norm_add_sq_eq_norm_sq_add_norm_sq_real
          (by simpa [ContextResidualOrthogonal] using orthogonal)
      calc
        ‖(truth - contextPrediction) +
            (contextPrediction - historyPrediction)‖ ^ 2 =
            ‖(truth - contextPrediction) +
              (contextPrediction - historyPrediction)‖ *
              ‖(truth - contextPrediction) +
                (contextPrediction - historyPrediction)‖ := by ring
        _ = ‖truth - contextPrediction‖ * ‖truth - contextPrediction‖ +
            ‖contextPrediction - historyPrediction‖ *
              ‖contextPrediction - historyPrediction‖ := pythagoras
        _ = ‖truth - contextPrediction‖ ^ 2 +
            ‖contextPrediction - historyPrediction‖ ^ 2 := by ring
    _ = SquaredPredictionRisk truth contextPrediction +
        ContextSignalEnergy historyPrediction contextPrediction := by
      rfl

/-- An orthogonal context refinement cannot increase squared risk. -/
theorem context_squared_risk_monotone
    (truth historyPrediction contextPrediction : E)
    (orthogonal :
      ContextResidualOrthogonal truth historyPrediction contextPrediction) :
    SquaredPredictionRisk truth contextPrediction ≤
      SquaredPredictionRisk truth historyPrediction := by
  rw [context_squared_risk_decomposition truth historyPrediction
    contextPrediction orthogonal]
  exact le_add_of_nonneg_right (sq_nonneg _)

/-- Under the projection contract, strict improvement occurs exactly when the
admitted context changes the prediction. -/
theorem context_strictly_improves_iff_prediction_changes
    (truth historyPrediction contextPrediction : E)
    (orthogonal :
      ContextResidualOrthogonal truth historyPrediction contextPrediction) :
    SquaredPredictionRisk truth contextPrediction <
        SquaredPredictionRisk truth historyPrediction ↔
      contextPrediction ≠ historyPrediction := by
  constructor
  · intro strict same
    subst contextPrediction
    simpa using strict
  · intro changed
    rw [context_squared_risk_decomposition truth historyPrediction
      contextPrediction orthogonal]
    have shiftNonzero : contextPrediction - historyPrediction ≠ 0 :=
      sub_ne_zero.mpr changed
    have shiftPositive :
        0 < ContextSignalEnergy historyPrediction contextPrediction := by
      exact sq_pos_of_pos (norm_pos_iff.mpr shiftNonzero)
    exact lt_add_of_pos_right _ shiftPositive

/-- Exact operational formula: relative gain is context-signal energy divided
by the pre-context risk. -/
theorem relative_context_gain_eq_signal_ratio
    (truth historyPrediction contextPrediction : E)
    (orthogonal :
      ContextResidualOrthogonal truth historyPrediction contextPrediction) :
    RelativeContextGain truth historyPrediction contextPrediction =
      ContextSignalEnergy historyPrediction contextPrediction /
        SquaredPredictionRisk truth historyPrediction := by
  rw [RelativeContextGain,
    context_squared_risk_decomposition truth historyPrediction
      contextPrediction orthogonal]
  ring

/-- Parameter rule: for positive baseline risk, a requested fractional gain is
met exactly when the context-signal energy clears the corresponding risk-scaled
floor. -/
theorem relative_context_gain_threshold_iff_signal_floor
    (truth historyPrediction contextPrediction : E) (threshold : ℝ)
    (orthogonal :
      ContextResidualOrthogonal truth historyPrediction contextPrediction)
    (baselinePositive : 0 < SquaredPredictionRisk truth historyPrediction) :
    threshold ≤ RelativeContextGain truth historyPrediction contextPrediction ↔
      threshold * SquaredPredictionRisk truth historyPrediction ≤
        ContextSignalEnergy historyPrediction contextPrediction := by
  rw [relative_context_gain_eq_signal_ratio truth historyPrediction
    contextPrediction orthogonal]
  exact le_div_iff₀ baselinePositive

/-- No-go: without a positive context-signal assumption, every proposed
strictly positive universal fractional gain is falsified by a valid zero-shift
context. -/
theorem no_positive_universal_context_gain_without_signal_floor
    (threshold : ℝ) (thresholdPositive : 0 < threshold) :
    ∃ truth historyPrediction contextPrediction : ℝ,
      ContextResidualOrthogonal truth historyPrediction contextPrediction ∧
      RelativeContextGain truth historyPrediction contextPrediction < threshold := by
  refine ⟨1, 0, 0, ?_, ?_⟩
  · simp [ContextResidualOrthogonal]
  · simpa [RelativeContextGain, SquaredPredictionRisk] using thresholdPositive

/-- Zero context signal forces zero relative gain whenever baseline risk is
nonzero. -/
theorem zero_context_signal_forces_zero_gain
    (truth historyPrediction contextPrediction : E)
    (orthogonal :
      ContextResidualOrthogonal truth historyPrediction contextPrediction)
    (signalZero : ContextSignalEnergy historyPrediction contextPrediction = 0) :
    RelativeContextGain truth historyPrediction contextPrediction = 0 := by
  rw [relative_context_gain_eq_signal_ratio truth historyPrediction
    contextPrediction orthogonal, signalZero, zero_div]

end

end OCKIndividuationMSpaceComposition
