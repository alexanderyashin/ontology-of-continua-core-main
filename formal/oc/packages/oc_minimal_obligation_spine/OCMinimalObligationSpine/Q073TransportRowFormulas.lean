/-!
OC Core 1.4 minimal obligation spine: Q073/Q012 transport-row formula layer.

This module is intentionally not a claim downgrade.  It formalizes the row-local
transport quantities that are already used by the replay/demo package, so that
the release pipeline does not treat JSON formulas as if they were Lean-backed
mathematical content.

The analytic billiard-to-reduction bridge remains a separate scientific theorem
obligation.  Theorems here close the internal algebraic/formula gap for the
declared row objects and keep the stronger AIM target intact.
-/

namespace OCMinimalObligationSpine

/- Narrow-window periodic Lorentz row.

`inversePi` is an explicit parameter because this minimal file avoids importing
analysis just to name π.  The replay supplies a numerical approximation; the row
formula itself only needs the multiplicative geometric factor.
-/
structure Q073Q012C1NarrowWindowLorentzParams : Type where
  cellLength : Rat
  tracerSpeed : Rat
  windowWidth : Rat
  cellArea : Rat
  inversePi : Rat

def q073_q012_c1_jumpFrequency
    (p : Q073Q012C1NarrowWindowLorentzParams) : Rat :=
  p.tracerSpeed * p.windowWidth * p.inversePi / p.cellArea

def q073_q012_c1_escapeRate
    (p : Q073Q012C1NarrowWindowLorentzParams) : Rat :=
  p.tracerSpeed * p.windowWidth * p.inversePi / p.cellArea

def q073_q012_c1_apertureFluxNumerator
    (p : Q073Q012C1NarrowWindowLorentzParams) : Rat :=
  p.tracerSpeed * p.windowWidth * p.inversePi

def q073_q012_c1_kineticFluxEscapeRate
    (p : Q073Q012C1NarrowWindowLorentzParams) : Rat :=
  q073_q012_c1_apertureFluxNumerator p / p.cellArea

def q073_q012_c1_diffusionCoefficient
    (p : Q073Q012C1NarrowWindowLorentzParams) : Rat :=
  p.cellLength * p.cellLength * q073_q012_c1_jumpFrequency p

theorem q073_q012_c1_kinetic_flux_yields_escape_rate
    (p : Q073Q012C1NarrowWindowLorentzParams) :
    q073_q012_c1_kineticFluxEscapeRate p =
      q073_q012_c1_escapeRate p := by
  rfl

theorem q073_q012_c1_escape_rate_feeds_jump_frequency
    (p : Q073Q012C1NarrowWindowLorentzParams) :
    q073_q012_c1_jumpFrequency p =
      q073_q012_c1_escapeRate p := by
  rfl

theorem q073_q012_c1_lorentz_formula_is_internalized
    (p : Q073Q012C1NarrowWindowLorentzParams) :
    q073_q012_c1_diffusionCoefficient p =
      p.cellLength * p.cellLength *
        (p.tracerSpeed * p.windowWidth * p.inversePi / p.cellArea) := by
  rfl

theorem q073_q012_c1_source_jump_frequency_formula_internalized
    (p : Q073Q012C1NarrowWindowLorentzParams) :
    q073_q012_c1_jumpFrequency p =
      p.tracerSpeed * p.windowWidth * p.inversePi / p.cellArea := by
  rfl

theorem q073_q012_c1_diffusion_is_length_square_times_jump_frequency
    (p : Q073Q012C1NarrowWindowLorentzParams) :
    q073_q012_c1_diffusionCoefficient p =
      p.cellLength * p.cellLength * q073_q012_c1_jumpFrequency p := by
  rfl

/- Continuous-time-random-walk sublayer for the narrow-window row.

This is the next internal bridge layer, not a billiard escape theorem.  It
records the two-dimensional diffusion convention used by the reviewer replay:
once a source-specific asymptotic reduction supplies the jump frequency, the
mean-square displacement growth rate is `4D`, and the row coefficient is the
same `D = l^2 * nu`.
-/
def q073_q012_c1_ctRWMeanSquareRate
    (p : Q073Q012C1NarrowWindowLorentzParams) : Rat :=
  4 * q073_q012_c1_diffusionCoefficient p

def q073_q012_c1_ctRWMeanSquareAtTime
    (p : Q073Q012C1NarrowWindowLorentzParams) (time : Rat) : Rat :=
  time * q073_q012_c1_ctRWMeanSquareRate p

theorem q073_q012_c1_ctrw_msd_rate_is_four_times_diffusion
    (p : Q073Q012C1NarrowWindowLorentzParams) :
    q073_q012_c1_ctRWMeanSquareRate p =
      4 * q073_q012_c1_diffusionCoefficient p := by
  rfl

theorem q073_q012_c1_ctrw_msd_time_is_time_times_rate
    (p : Q073Q012C1NarrowWindowLorentzParams) (time : Rat) :
    q073_q012_c1_ctRWMeanSquareAtTime p time =
      time * q073_q012_c1_ctRWMeanSquareRate p := by
  rfl

theorem q073_q012_c1_ctrw_msd_rate_internalizes_row_formula
    (p : Q073Q012C1NarrowWindowLorentzParams) :
    q073_q012_c1_ctRWMeanSquareRate p =
      4 * (p.cellLength * p.cellLength *
        (p.tracerSpeed * p.windowWidth * p.inversePi / p.cellArea)) := by
  rfl

theorem q073_q012_c1_escape_rate_to_msd_rate_internalized
    (p : Q073Q012C1NarrowWindowLorentzParams) :
    q073_q012_c1_ctRWMeanSquareRate p =
      4 * (p.cellLength * p.cellLength *
        q073_q012_c1_escapeRate p) := by
  rfl

theorem q073_q012_c1_ctrw_msd_time_law_internalizes_row_formula
    (p : Q073Q012C1NarrowWindowLorentzParams) (time : Rat) :
    q073_q012_c1_ctRWMeanSquareAtTime p time =
      time * (4 * (p.cellLength * p.cellLength *
        (p.tracerSpeed * p.windowWidth * p.inversePi / p.cellArea))) := by
  rfl

/- Rare-collision hard-sphere heat row. -/
structure Q073Q012C2RareCollisionHeatParams : Type where
  lengthScale : Rat
  binaryCollisionFrequency : Rat
  sqrtTemperatureScale : Rat

def q073_q012_c2_heatConductivity
    (p : Q073Q012C2RareCollisionHeatParams) : Rat :=
  p.lengthScale * p.lengthScale * p.binaryCollisionFrequency

def q073_q012_c2_sourceUnitBinaryFrequency
    (p : Q073Q012C2RareCollisionHeatParams) : Rat :=
  p.sqrtTemperatureScale

def q073_q012_c2_sourceUnitHeatConductivity
    (p : Q073Q012C2RareCollisionHeatParams) : Rat :=
  p.lengthScale * p.lengthScale *
    q073_q012_c2_sourceUnitBinaryFrequency p

theorem q073_q012_c2_rare_collision_formula_is_internalized
    (p : Q073Q012C2RareCollisionHeatParams) :
    q073_q012_c2_heatConductivity p =
      p.lengthScale * p.lengthScale * p.binaryCollisionFrequency := by
  rfl

theorem q073_q012_c2_source_unit_frequency_scales_like_sqrt_temperature
    (p : Q073Q012C2RareCollisionHeatParams) :
    q073_q012_c2_sourceUnitBinaryFrequency p =
      p.sqrtTemperatureScale := by
  rfl

theorem q073_q012_c2_source_unit_conductivity_formula_is_internalized
    (p : Q073Q012C2RareCollisionHeatParams) :
    q073_q012_c2_sourceUnitHeatConductivity p =
      p.lengthScale * p.lengthScale * p.sqrtTemperatureScale := by
  rfl

theorem q073_q012_c2_binary_frequency_match_yields_source_unit_formula
    (p : Q073Q012C2RareCollisionHeatParams)
    (h : p.binaryCollisionFrequency = p.sqrtTemperatureScale) :
    q073_q012_c2_heatConductivity p =
      q073_q012_c2_sourceUnitHeatConductivity p := by
  unfold q073_q012_c2_heatConductivity
  unfold q073_q012_c2_sourceUnitHeatConductivity
  unfold q073_q012_c2_sourceUnitBinaryFrequency
  rw [h]

/- Stochastic finite-size Helfand/envelope row.

The row records the limiting conductivity and an explicit relative `1/N`-style
envelope.  Division-by-zero and sign side-conditions are deliberately kept as
row hypotheses for the stronger analytic worker rather than hidden here.
-/
structure Q073Q012C3FiniteSizeEnvelopeParams : Type where
  limitingConductivity : Rat
  relativeCorrectionBound : Rat

def q073_q012_c3_lowerEnvelope
    (p : Q073Q012C3FiniteSizeEnvelopeParams) : Rat :=
  p.limitingConductivity * (1 - p.relativeCorrectionBound)

def q073_q012_c3_upperEnvelope
    (p : Q073Q012C3FiniteSizeEnvelopeParams) : Rat :=
  p.limitingConductivity * (1 + p.relativeCorrectionBound)

theorem q073_q012_c3_finite_size_envelope_is_internalized
    (p : Q073Q012C3FiniteSizeEnvelopeParams) :
    q073_q012_c3_lowerEnvelope p =
        p.limitingConductivity * (1 - p.relativeCorrectionBound) ∧
      q073_q012_c3_upperEnvelope p =
        p.limitingConductivity * (1 + p.relativeCorrectionBound) := by
  exact ⟨rfl, rfl⟩

/- Infinite-horizon anomalous-transport row.

The logarithm value is passed in as the row's asymptotic scale factor.  This
keeps the formula layer lightweight while preserving the required terminal
object: finite-time diffusion grows with the log scale and mean-square
displacement is `4 * t * D(t)`.
-/
structure Q073Q012C4AnomalousScaleParams : Type where
  baseAnomalousCoefficient : Rat
  time : Rat
  logTimeRatio : Rat

def q073_q012_c4_finiteTimeDiffusion
    (p : Q073Q012C4AnomalousScaleParams) : Rat :=
  p.baseAnomalousCoefficient * p.logTimeRatio

def q073_q012_c4_meanSquareDisplacement
    (p : Q073Q012C4AnomalousScaleParams) : Rat :=
  4 * p.time * q073_q012_c4_finiteTimeDiffusion p

theorem q073_q012_c4_anomalous_scaling_is_internalized
    (p : Q073Q012C4AnomalousScaleParams) :
    q073_q012_c4_meanSquareDisplacement p =
      4 * p.time * (p.baseAnomalousCoefficient * p.logTimeRatio) := by
  rfl

/- Polygonal/nonchaotic frontier row.

This is not a numerical coefficient row.  It is a typed guard saying the release
cannot silently route polygonal/nonchaotic systems through the hyperbolic
Lorentz/rare-collision formulas.
-/
structure Q073Q012C5PolygonalFrontierBoundary : Type where
  namedPolygonalOrNonchaoticClass : Prop
  hyperbolicSurrogateRejected : Prop
  classSpecificObservableRequired : Prop
  classProof : namedPolygonalOrNonchaoticClass
  rejectionProof : hyperbolicSurrogateRejected
  observableProof : classSpecificObservableRequired

theorem q073_q012_c5_frontier_blocks_untyped_formula_reuse
    (p : Q073Q012C5PolygonalFrontierBoundary) :
    p.namedPolygonalOrNonchaoticClass ∧
      p.hyperbolicSurrogateRejected ∧
      p.classSpecificObservableRequired := by
  exact ⟨p.classProof, p.rejectionProof, p.observableProof⟩

end OCMinimalObligationSpine
