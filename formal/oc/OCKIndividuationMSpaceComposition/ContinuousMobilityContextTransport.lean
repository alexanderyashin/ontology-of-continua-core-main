import OCKIndividuationMSpaceComposition.ContextRiskDecomposition

namespace OCKIndividuationMSpaceComposition

/-!
# Continuous mobility transport and the admission boundary for context gates

The physical adapter estimates a local squared-displacement rate from a past
window and transports it to the future observation duration.  This module
states the unit-covariance laws of that construction and the exact squared-risk
boundary at which an additional categorical context gate helps or harms.
-/

/-- Transport a past mean squared displacement through the ratio of future to
past observation duration. -/
noncomputable def MobilityTransport
    (presentJumpEnergy presentDuration futureDuration : ℝ) : ℝ :=
  presentJumpEnergy / presentDuration * futureDuration

/-- Changing the time unit by the same nonzero factor in both durations leaves
the transported squared displacement unchanged. -/
theorem mobilityTransport_time_unit_invariant
    (presentJumpEnergy presentDuration futureDuration scale : ℝ)
    (presentDurationNonzero : presentDuration ≠ 0)
    (scaleNonzero : scale ≠ 0) :
    MobilityTransport presentJumpEnergy (scale * presentDuration)
        (scale * futureDuration) =
      MobilityTransport presentJumpEnergy presentDuration futureDuration := by
  unfold MobilityTransport
  field_simp

/-- Multiplying coordinates by a factor multiplies squared displacement and
its transported prediction by the square of that factor. -/
theorem mobilityTransport_coordinate_scale_covariant
    (presentJumpEnergy presentDuration futureDuration coordinateScale : ℝ) :
    MobilityTransport (coordinateScale ^ 2 * presentJumpEnergy)
        presentDuration futureDuration =
      coordinateScale ^ 2 *
        MobilityTransport presentJumpEnergy presentDuration futureDuration := by
  unfold MobilityTransport
  ring

/-- Under constant local mobility, the transport formula exactly predicts the
future mean squared displacement. -/
theorem mobilityTransport_exact_under_constant_mobility
    (mobility presentDuration futureDuration : ℝ)
    (presentDurationNonzero : presentDuration ≠ 0) :
    MobilityTransport (mobility * presentDuration)
        presentDuration futureDuration = mobility * futureDuration := by
  unfold MobilityTransport
  field_simp

/-- Exact operational boundary for adding a scalar context gate to an existing
continuous-transport prediction.  The gate helps precisely when twice its
alignment with the old residual exceeds its own squared magnitude. -/
theorem added_context_gate_improves_iff_alignment_exceeds_half_energy
    (truth continuousPrediction gate : ℝ) :
    SquaredPredictionRisk truth (continuousPrediction + gate) <
        SquaredPredictionRisk truth continuousPrediction ↔
      gate ^ 2 < 2 * (truth - continuousPrediction) * gate := by
  simp only [SquaredPredictionRisk, Real.norm_eq_abs, sq_abs]
  constructor <;> intro hypothesis <;> nlinarith

/-- Dual no-go boundary: an added context gate worsens prediction precisely
when its squared magnitude exceeds twice its residual alignment. -/
theorem added_context_gate_worsens_iff_alignment_below_half_energy
    (truth continuousPrediction gate : ℝ) :
    SquaredPredictionRisk truth continuousPrediction <
        SquaredPredictionRisk truth (continuousPrediction + gate) ↔
      2 * (truth - continuousPrediction) * gate < gate ^ 2 := by
  simp only [SquaredPredictionRisk, Real.norm_eq_abs, sq_abs]
  constructor <;> intro hypothesis <;> nlinarith

/-- A nonzero categorical gate which has zero alignment with the residual of
the continuous transport predictor strictly increases squared risk. -/
theorem unaligned_nonzero_context_gate_strictly_worsens
    (truth continuousPrediction gate : ℝ)
    (zeroAlignment : (truth - continuousPrediction) * gate = 0)
    (gateNonzero : gate ≠ 0) :
    SquaredPredictionRisk truth continuousPrediction <
      SquaredPredictionRisk truth (continuousPrediction + gate) := by
  rw [added_context_gate_worsens_iff_alignment_below_half_energy]
  have gateEnergyPositive : 0 < gate ^ 2 := sq_pos_of_ne_zero gateNonzero
  nlinarith

/-- A categorical context whose fitted shift is zero is predictively neutral;
context labels alone cannot create information. -/
theorem zero_context_gate_is_predictively_neutral
    (truth continuousPrediction : ℝ) :
    SquaredPredictionRisk truth (continuousPrediction + 0) =
      SquaredPredictionRisk truth continuousPrediction := by
  simp

end OCKIndividuationMSpaceComposition
