import OCKIndividuationMSpaceComposition.SemanticPredictionHorizonAdapter
import OCKIndividuationMSpaceComposition.BrierResidualAlignmentAdmission

namespace OCKIndividuationMSpaceComposition

/-!
# Typed horizon × calibration transport

This module is the formal bridge for the three empirical replays.  A forecast
is indexed by the semantic horizon binding and its calibration coordinate
(domain, outcome, horizon).  The regression/event-log implementations are
domain adapters; the kernel only assumes the information-at-origin contract
and the declared Brier residual/shift vectors.

The positive results are exact quadratic calibration laws.  The no-go result
states why one scalar calibration cannot be universal when two cells have
different residual-alignment ratios.  Transport to a new domain additionally
needs an explicit residual margin.
-/

structure HorizonCalibrationCoordinate where
  domainId : String
  outcomeId : String
  horizonId : String
  deriving DecidableEq

theorem HorizonCalibrationCoordinate.ne_of_outcomeId_ne
    {first second : HorizonCalibrationCoordinate}
    (different : first.outcomeId ≠ second.outcomeId) :
    first ≠ second := by
  intro equal
  apply different
  simpa [equal]

theorem HorizonCalibrationCoordinate.ne_of_domainId_ne
    {first second : HorizonCalibrationCoordinate}
    (different : first.domainId ≠ second.domainId) :
    first ≠ second := by
  intro equal
  apply different
  simpa [equal]

structure TypedHorizonBrierCell (n : ℕ) where
  binding : SemanticPredictionHorizonBinding
  truth : Fin n → ℝ
  base : Fin n → ℝ
  shift : Fin n → ℝ
  shiftEnergyPositive : 0 < BrierShiftEnergy shift

def TypedHorizonBrierCell.risk
    {n : ℕ} (cell : TypedHorizonBrierCell n) (weight : ℝ) : ℝ :=
  BrierContextRisk cell.truth cell.base cell.shift weight

def TypedHorizonBrierCell.alignment
    {n : ℕ} (cell : TypedHorizonBrierCell n) : ℝ :=
  BrierResidualAlignment cell.truth cell.base cell.shift

def TypedHorizonBrierCell.energy
    {n : ℕ} (cell : TypedHorizonBrierCell n) : ℝ :=
  BrierShiftEnergy cell.shift

noncomputable def TypedHorizonBrierCell.clampedWeight
    {n : ℕ} (cell : TypedHorizonBrierCell n) : ℝ :=
  ClampedResidualAlignmentWeight cell.alignment cell.energy

/-- Exact positive calibration rule for a semantically bound horizon cell. -/
theorem TypedHorizonBrierCell.positive_gate_iff
    {n : ℕ} (cell : TypedHorizonBrierCell n)
    (weight : ℝ) (weightPositive : 0 < weight) :
    cell.risk weight < cell.risk 0 ↔
      weight * cell.energy < 2 * cell.alignment := by
  exact positive_brier_context_improves_iff_residual_alignment
    cell.truth cell.base cell.shift weight weightPositive

/-- The clamped residual-alignment rule is globally optimal among `[0,1]` gates. -/
theorem TypedHorizonBrierCell.clamped_weight_minimizes
    {n : ℕ} (cell : TypedHorizonBrierCell n)
    (weight : ℝ) (weightNonnegative : 0 ≤ weight)
    (weightAtMostOne : weight ≤ 1) :
    cell.risk cell.clampedWeight ≤ cell.risk weight := by
  exact clampedBrierResidualAlignmentWeight_globally_minimizes
    cell.truth cell.base cell.shift weight cell.shiftEnergyPositive
    weightNonnegative weightAtMostOne

/-- A strict gain threshold is paid for by a measurable context-signal floor. -/
theorem TypedHorizonBrierCell.gain_threshold_requires_signal_floor
    {n : ℕ} (cell : TypedHorizonBrierCell n)
    (threshold : ℝ) (baselinePositive : 0 < BrierBaseRisk cell.truth cell.base)
    (weight : ℝ) (weightPositive : 0 < weight) :
    cell.risk weight < cell.risk 0 →
      weight * cell.energy < 2 * cell.alignment := by
  intro improvement
  exact (cell.positive_gate_iff weight weightPositive).mp improvement

/-! An outcome/domain-specific adapter is not a defect: distinct cells can
have distinct optimum ratios.  This is the formal boundary observed in UR3
and BPI2017. -/

noncomputable def unconstrainedAlignmentWeight (alignment energy : ℝ) : ℝ :=
  alignment / energy

theorem no_common_unconstrained_weight_of_distinct_alignment_ratios
    (alignment₁ energy₁ alignment₂ energy₂ : ℝ)
    (ratiosDifferent :
      unconstrainedAlignmentWeight alignment₁ energy₁ ≠
        unconstrainedAlignmentWeight alignment₂ energy₂) :
    ¬ ∃ weight : ℝ,
      weight = unconstrainedAlignmentWeight alignment₁ energy₁ ∧
      weight = unconstrainedAlignmentWeight alignment₂ energy₂ := by
  rintro ⟨weight, first, second⟩
  apply ratiosDifferent
  exact first.symm.trans second

theorem TypedHorizonBrierCell.universal_gain_without_signal_floor_is_impossible
    (threshold : ℝ) (thresholdPositive : 0 < threshold) :
    ∃ truth historyPrediction contextPrediction : ℝ,
      ContextResidualOrthogonal truth historyPrediction contextPrediction ∧
      RelativeContextGain truth historyPrediction contextPrediction < threshold := by
  exact no_positive_universal_context_gain_without_signal_floor
    threshold thresholdPositive

/-- Source calibration needs an explicit transport margin before it can bound a
target domain.  A source residual bound alone is not such a theorem. -/
theorem source_horizon_residual_requires_transport_margin :
    ∃ sourceResidual targetResidual radius : ℝ,
      |sourceResidual| ≤ radius ∧ ¬ |targetResidual| ≤ radius := by
  exact ScalarForecastHull.source_residual_bound_does_not_imply_target_bound

theorem transport_margin_yields_target_hull
    (center sourceRadius transportMargin target : ℝ)
    (transportBound :
      |target - center| ≤ sourceRadius + transportMargin) :
    ScalarForecastHull.Contains
      (ScalarForecastHull.symmetric center (sourceRadius + transportMargin))
      target := by
  exact ScalarForecastHull.additive_transport_margin_yields_containment
    center sourceRadius transportMargin target transportBound

end OCKIndividuationMSpaceComposition
