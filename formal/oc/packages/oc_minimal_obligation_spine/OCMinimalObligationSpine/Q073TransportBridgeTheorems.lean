import OCMinimalObligationSpine.Q073BilliardsStatisticalGates
import OCMinimalObligationSpine.Q073LogarithmicDiffusionDivergence
import OCMinimalObligationSpine.Q073PortmanteauMomentBridge
import OCMinimalObligationSpine.Q073TransportRowFormulas

/-!
OC Core 1.4 minimal obligation spine: Q073/Q012 transport bridge layer.

The previous row-formula layer internalizes the algebraic quantities used by
the replay/demo package.  This file adds the next scientific layer: explicit
bridge packages.  A bridge package is the object a later analytic worker must
fill with billiard-specific hypotheses, reduction validity, boundary proofs,
and replay/uncertainty evidence.  Once such a package is supplied, Lean derives
the row-local coefficient/scaling conclusion without renaming the AIM target.

This is the typed route from "we have a source-bound row and replay" to
"we have an OC-internal theorem payload for this row".  The bottom layer keeps
row-local bridge obligations visible; the package layer below closes the
declared source-bound plural release answer without silently promoting that
answer into an unbounded external settlement of every possible billiard class.
-/

namespace OCMinimalObligationSpine

open scoped BoundedContinuousFunction

structure Q073Q012C1NarrowWindowLorentzBridge : Type where
  params : Q073Q012C1NarrowWindowLorentzParams
  narrowWindowRegime : Prop
  localEquilibriumBetweenJumps : Prop
  continuousTimeRandomWalkReduction : Prop
  boundaryExcludesPluralTargetCollapse : Prop
  numericReplayEvidence : Q073NumericReplayEvidence
  analyticAsset : Q073SourceBoundAnalyticAsset
  regimeProof : narrowWindowRegime
  equilibriumProof : localEquilibriumBetweenJumps
  reductionProof : continuousTimeRandomWalkReduction
  boundaryProof : boundaryExcludesPluralTargetCollapse

def Q073Q012C1NarrowWindowLorentzBridge.formulaPayload
    (bridge : Q073Q012C1NarrowWindowLorentzBridge) :
    Q073Q012TransportCoefficientPayload where
  billiardTaxonomy := bridge.narrowWindowRegime
  coefficientDefinitions :=
    q073_q012_c1_diffusionCoefficient bridge.params =
      bridge.params.cellLength * bridge.params.cellLength *
        (bridge.params.tracerSpeed * bridge.params.windowWidth *
          bridge.params.inversePi / bridge.params.cellArea)
  coefficientFormulaOrAlgorithm := bridge.continuousTimeRandomWalkReduction
  analyticAssets := bridge.analyticAsset
  numericEvidence := bridge.numericReplayEvidence
  boundary := {
    coveredClassesSpecified := bridge.narrowWindowRegime
    excludedClassesSpecified := bridge.boundaryExcludesPluralTargetCollapse
    noOneSystemAsFullTarget := bridge.boundaryExcludesPluralTargetCollapse
    coveredProof := bridge.regimeProof
    excludedProof := bridge.boundaryProof
    noOneSystemProof := bridge.boundaryProof
  }
  taxonomyProof := bridge.regimeProof
  definitionProof := q073_q012_c1_lorentz_formula_is_internalized bridge.params
  formulaOrAlgorithmProof := bridge.reductionProof

theorem q073_q012_c1_bridge_yields_internal_formula_payload
    (bridge : Q073Q012C1NarrowWindowLorentzBridge) :
    ∃ payload : Q073Q012TransportCoefficientPayload,
      payload.coefficientDefinitions ∧
        payload.coefficientFormulaOrAlgorithm ∧
        payload.boundary.noOneSystemAsFullTarget := by
  refine ⟨bridge.formulaPayload, ?_⟩
  exact ⟨bridge.formulaPayload.definitionProof,
    bridge.formulaPayload.formulaOrAlgorithmProof,
    bridge.formulaPayload.boundary.noOneSystemProof⟩

structure Q073Q012C1KineticFluxLayer : Type where
  bridge : Q073Q012C1NarrowWindowLorentzBridge
  uniformBoundaryPhaseDensity : Prop
  apertureFluxNormalization : Prop
  areaNormalization : Prop
  densityProof : uniformBoundaryPhaseDensity
  apertureProof : apertureFluxNormalization
  areaProof : areaNormalization

theorem q073_q012_c1_kinetic_flux_layer_yields_escape_rate
    (layer : Q073Q012C1KineticFluxLayer) :
    layer.uniformBoundaryPhaseDensity ∧
      layer.apertureFluxNormalization ∧
      layer.areaNormalization ∧
      q073_q012_c1_kineticFluxEscapeRate layer.bridge.params =
        q073_q012_c1_escapeRate layer.bridge.params := by
  exact ⟨layer.densityProof,
    layer.apertureProof,
    layer.areaProof,
    q073_q012_c1_kinetic_flux_yields_escape_rate layer.bridge.params⟩

structure Q073Q012C1EscapeRateLayer : Type where
  bridge : Q073Q012C1NarrowWindowLorentzBridge
  narrowWindowEscapeRateAdmitted : Prop
  escapeRateIsTheJumpClock : Prop
  escapeRateProof : narrowWindowEscapeRateAdmitted
  jumpClockProof : escapeRateIsTheJumpClock

theorem q073_q012_c1_escape_rate_layer_yields_jump_frequency
    (layer : Q073Q012C1EscapeRateLayer) :
    layer.narrowWindowEscapeRateAdmitted ∧
      layer.escapeRateIsTheJumpClock ∧
      q073_q012_c1_jumpFrequency layer.bridge.params =
        q073_q012_c1_escapeRate layer.bridge.params := by
  exact ⟨layer.escapeRateProof,
    layer.jumpClockProof,
    q073_q012_c1_escape_rate_feeds_jump_frequency layer.bridge.params⟩

structure Q073Q012C1CTRWReductionLayer : Type where
  bridge : Q073Q012C1NarrowWindowLorentzBridge
  twoDimensionalMSDConvention : Prop
  jumpFrequencyFeedsRowFormula : Prop
  conventionProof : twoDimensionalMSDConvention
  jumpFrequencyProof : jumpFrequencyFeedsRowFormula

theorem q073_q012_c1_ctrw_reduction_layer_yields_msd_rate_formula
    (layer : Q073Q012C1CTRWReductionLayer) :
    layer.twoDimensionalMSDConvention ∧
      layer.jumpFrequencyFeedsRowFormula ∧
      q073_q012_c1_ctRWMeanSquareRate layer.bridge.params =
        4 * (layer.bridge.params.cellLength * layer.bridge.params.cellLength *
          (layer.bridge.params.tracerSpeed *
            layer.bridge.params.windowWidth *
            layer.bridge.params.inversePi / layer.bridge.params.cellArea)) := by
  exact ⟨layer.conventionProof,
    layer.jumpFrequencyProof,
    q073_q012_c1_ctrw_msd_rate_internalizes_row_formula layer.bridge.params⟩

structure Q073Q012C1EscapeCTRWReductionLayer : Type where
  bridge : Q073Q012C1NarrowWindowLorentzBridge
  narrowWindowEscapeRateAdmitted : Prop
  escapeRateIsTheJumpClock : Prop
  twoDimensionalMSDConvention : Prop
  escapeRateProof : narrowWindowEscapeRateAdmitted
  jumpClockProof : escapeRateIsTheJumpClock
  conventionProof : twoDimensionalMSDConvention

theorem q073_q012_c1_escape_and_ctrw_layers_yield_msd_rate
    (layer : Q073Q012C1EscapeCTRWReductionLayer) :
    layer.narrowWindowEscapeRateAdmitted ∧
      layer.escapeRateIsTheJumpClock ∧
      layer.twoDimensionalMSDConvention ∧
      q073_q012_c1_ctRWMeanSquareRate layer.bridge.params =
        4 * (layer.bridge.params.cellLength * layer.bridge.params.cellLength *
          q073_q012_c1_escapeRate layer.bridge.params) := by
  exact ⟨layer.escapeRateProof,
    layer.jumpClockProof,
    layer.conventionProof,
    q073_q012_c1_escape_rate_to_msd_rate_internalized layer.bridge.params⟩

structure Q073Q012C1KineticFluxToDiffusionChain : Type where
  bridge : Q073Q012C1NarrowWindowLorentzBridge
  uniformBoundaryPhaseDensity : Prop
  apertureFluxNormalization : Prop
  areaNormalization : Prop
  escapeRateIsTheJumpClock : Prop
  twoDimensionalMSDConvention : Prop
  densityProof : uniformBoundaryPhaseDensity
  apertureProof : apertureFluxNormalization
  areaProof : areaNormalization
  jumpClockProof : escapeRateIsTheJumpClock
  conventionProof : twoDimensionalMSDConvention

theorem q073_q012_c1_kinetic_flux_chain_yields_diffusion_formula
    (chain : Q073Q012C1KineticFluxToDiffusionChain) :
    chain.uniformBoundaryPhaseDensity ∧
      chain.apertureFluxNormalization ∧
      chain.areaNormalization ∧
      chain.escapeRateIsTheJumpClock ∧
      chain.twoDimensionalMSDConvention ∧
      q073_q012_c1_diffusionCoefficient chain.bridge.params =
        chain.bridge.params.cellLength * chain.bridge.params.cellLength *
          q073_q012_c1_kineticFluxEscapeRate chain.bridge.params := by
  exact ⟨chain.densityProof,
    chain.apertureProof,
    chain.areaProof,
    chain.jumpClockProof,
    chain.conventionProof,
    rfl⟩

structure Q073Q012C1SourceA1FormulaExtractionChain : Type where
  bridge : Q073Q012C1NarrowWindowLorentzBridge
  sourceLineBoundFormulaReviewed : Prop
  narrowWindowSourceScopeMatched : Prop
  sourceReviewProof : sourceLineBoundFormulaReviewed
  scopeProof : narrowWindowSourceScopeMatched

theorem q073_q012_c1_source_a1_chain_yields_source_equations
    (chain : Q073Q012C1SourceA1FormulaExtractionChain) (time : Rat) :
    chain.sourceLineBoundFormulaReviewed ∧
      chain.narrowWindowSourceScopeMatched ∧
      q073_q012_c1_jumpFrequency chain.bridge.params =
        chain.bridge.params.tracerSpeed *
          chain.bridge.params.windowWidth *
          chain.bridge.params.inversePi /
          chain.bridge.params.cellArea ∧
      q073_q012_c1_diffusionCoefficient chain.bridge.params =
        chain.bridge.params.cellLength *
          chain.bridge.params.cellLength *
          q073_q012_c1_jumpFrequency chain.bridge.params ∧
      q073_q012_c1_ctRWMeanSquareRate chain.bridge.params =
        4 * q073_q012_c1_diffusionCoefficient chain.bridge.params ∧
      q073_q012_c1_ctRWMeanSquareAtTime chain.bridge.params time =
        time * (4 * q073_q012_c1_diffusionCoefficient chain.bridge.params) := by
  exact ⟨chain.sourceReviewProof,
    chain.scopeProof,
    q073_q012_c1_source_jump_frequency_formula_internalized chain.bridge.params,
    q073_q012_c1_diffusion_is_length_square_times_jump_frequency chain.bridge.params,
    q073_q012_c1_ctrw_msd_rate_is_four_times_diffusion chain.bridge.params,
    by
      calc
        q073_q012_c1_ctRWMeanSquareAtTime chain.bridge.params time =
            time * q073_q012_c1_ctRWMeanSquareRate chain.bridge.params := by
          rfl
        _ = time * (4 * q073_q012_c1_diffusionCoefficient chain.bridge.params) := by
          rw [q073_q012_c1_ctrw_msd_rate_is_four_times_diffusion chain.bridge.params]⟩

structure Q073Q012C1QuantitativeMixingWitness
    (bridge : Q073Q012C1NarrowWindowLorentzBridge) : Type where
  correlationDecayBound : Rat
  admittedLocalEquilibriumTolerance : Rat
  jumpClockAfterMixingWindow : Prop
  boundWithinTolerance :
    correlationDecayBound ≤ admittedLocalEquilibriumTolerance
  windowProof : jumpClockAfterMixingWindow
  mixingBoundImpliesLocalEquilibrium :
    correlationDecayBound ≤ admittedLocalEquilibriumTolerance →
      jumpClockAfterMixingWindow →
      bridge.localEquilibriumBetweenJumps

theorem q073_q012_c1_quantitative_mixing_witness_yields_local_equilibrium
    {bridge : Q073Q012C1NarrowWindowLorentzBridge}
    (witness : Q073Q012C1QuantitativeMixingWitness bridge) :
    bridge.localEquilibriumBetweenJumps := by
  exact witness.mixingBoundImpliesLocalEquilibrium
    witness.boundWithinTolerance witness.windowProof

def q073_q012_c1_replayWindowRatio : Rat := 1 / 25

def q073_q012_c1_replayCorrelationDecayBound : Rat := 1 / 625

def q073_q012_c1_replayLocalEquilibriumTolerance : Rat := 1 / 100

def q073_q012_c1_replayNarrowWindowGate : Rat := 1 / 10

theorem q073_q012_c1_replay_window_ratio_is_narrow :
    q073_q012_c1_replayWindowRatio ≤
      q073_q012_c1_replayNarrowWindowGate := by
  decide +kernel

theorem q073_q012_c1_replay_mixing_bound_within_tolerance :
    q073_q012_c1_replayCorrelationDecayBound ≤
      q073_q012_c1_replayLocalEquilibriumTolerance := by
  decide +kernel

structure Q073Q012C1SourceLocalEquilibriumTheoremPort
    (bridge : Q073Q012C1NarrowWindowLorentzBridge) : Type where
  sourceId : String
  statementId : String
  assetId : String
  sourceLocator : String
  canonicalSourceId :
    sourceId = "GG_2011_TWO_STAGE_RELAXATION"
  canonicalStatementId :
    statementId = "Q012_STMT_A1_DIFFUSION_COEFFICIENT"
  canonicalAssetId :
    assetId = "Q012_A1_DIFFUSION_COEFFICIENT"
  canonicalLocator :
    sourceLocator = "PDF lines 246-286; equations (8)-(11)"
  sourceHypothesesCoverNarrowWindowPeriodicLorentz : Prop
  sourceHypothesesCoverLocalEquilibriumClosure : Prop
  sourceConclusionMatchesLocalEquilibrium : Prop
  sourceTwoStageRelaxationTheorem : Prop
  narrowWindowHypothesisProof :
    sourceHypothesesCoverNarrowWindowPeriodicLorentz
  localEquilibriumClosureHypothesisProof :
    sourceHypothesesCoverLocalEquilibriumClosure
  conclusionMatchProof :
    sourceConclusionMatchesLocalEquilibrium
  sourceTheoremProof : sourceTwoStageRelaxationTheorem
  sourceTheoremMapsSeparationToLocalEquilibrium :
    sourceTwoStageRelaxationTheorem →
      sourceHypothesesCoverNarrowWindowPeriodicLorentz →
      sourceHypothesesCoverLocalEquilibriumClosure →
      sourceConclusionMatchesLocalEquilibrium →
      (inCellRelaxationTime directionalJumpTime admittedRelaxationToJumpRatio : Rat) →
      inCellRelaxationTime ≤ directionalJumpTime * admittedRelaxationToJumpRatio →
      bridge.localEquilibriumBetweenJumps

theorem q073_q012_c1_source_local_equilibrium_port_is_canonical
    {bridge : Q073Q012C1NarrowWindowLorentzBridge}
    (port : Q073Q012C1SourceLocalEquilibriumTheoremPort bridge) :
    port.sourceId = "GG_2011_TWO_STAGE_RELAXATION" ∧
      port.statementId = "Q012_STMT_A1_DIFFUSION_COEFFICIENT" ∧
      port.assetId = "Q012_A1_DIFFUSION_COEFFICIENT" ∧
      port.sourceLocator = "PDF lines 246-286; equations (8)-(11)" ∧
      port.sourceHypothesesCoverNarrowWindowPeriodicLorentz ∧
      port.sourceHypothesesCoverLocalEquilibriumClosure ∧
      port.sourceConclusionMatchesLocalEquilibrium ∧
      port.sourceTwoStageRelaxationTheorem := by
  exact ⟨port.canonicalSourceId,
    port.canonicalStatementId,
    port.canonicalAssetId,
    port.canonicalLocator,
    port.narrowWindowHypothesisProof,
    port.localEquilibriumClosureHypothesisProof,
    port.conclusionMatchProof,
    port.sourceTheoremProof⟩

structure Q073Q012C1SourceBoundLocalEquilibriumTheoremInstance
    (bridge : Q073Q012C1NarrowWindowLorentzBridge) : Type where
  sourcePort : Q073Q012C1SourceLocalEquilibriumTheoremPort bridge
  inCellRelaxationTime : Rat
  directionalJumpTime : Rat
  admittedRelaxationToJumpRatio : Rat
  sourceReadbackSupportsTwoStageRelaxation : Prop
  sourceReadbackSupportsControlledLocalEquilibration : Prop
  sourceReadbackSupportsMemoryLoss : Prop
  sourceReadbackSupportsCTRWReduction : Prop
  sourceReadbackSupportsDimensionalDiffusionCoefficient : Prop
  relaxationBeforeJump :
    inCellRelaxationTime ≤ directionalJumpTime * admittedRelaxationToJumpRatio
  twoStageRelaxationProof : sourceReadbackSupportsTwoStageRelaxation
  controlledLocalEquilibrationProof :
    sourceReadbackSupportsControlledLocalEquilibration
  memoryLossProof : sourceReadbackSupportsMemoryLoss
  ctrwReductionProof : sourceReadbackSupportsCTRWReduction
  dimensionalCoefficientProof :
    sourceReadbackSupportsDimensionalDiffusionCoefficient

theorem q073_q012_c1_source_bound_instance_yields_local_equilibrium
    {bridge : Q073Q012C1NarrowWindowLorentzBridge}
    (inst :
      Q073Q012C1SourceBoundLocalEquilibriumTheoremInstance bridge) :
    bridge.localEquilibriumBetweenJumps := by
  exact inst.sourcePort.sourceTheoremMapsSeparationToLocalEquilibrium
    inst.sourcePort.sourceTheoremProof
    inst.sourcePort.narrowWindowHypothesisProof
    inst.sourcePort.localEquilibriumClosureHypothesisProof
    inst.sourcePort.conclusionMatchProof
    inst.inCellRelaxationTime
    inst.directionalJumpTime
    inst.admittedRelaxationToJumpRatio
    inst.relaxationBeforeJump

structure Q073Q012C1TimeScaleSeparationWitness
    (bridge : Q073Q012C1NarrowWindowLorentzBridge) : Type where
  inCellRelaxationTime : Rat
  directionalJumpTime : Rat
  admittedRelaxationToJumpRatio : Rat
  sourceTheoremPort : Q073Q012C1SourceLocalEquilibriumTheoremPort bridge
  relaxationBeforeJump :
    inCellRelaxationTime ≤
      directionalJumpTime * admittedRelaxationToJumpRatio

theorem q073_q012_c1_time_scale_separation_yields_local_equilibrium
    {bridge : Q073Q012C1NarrowWindowLorentzBridge}
    (witness : Q073Q012C1TimeScaleSeparationWitness bridge) :
    bridge.localEquilibriumBetweenJumps := by
  exact witness.sourceTheoremPort.sourceTheoremMapsSeparationToLocalEquilibrium
    witness.sourceTheoremPort.sourceTheoremProof
    witness.sourceTheoremPort.narrowWindowHypothesisProof
    witness.sourceTheoremPort.localEquilibriumClosureHypothesisProof
    witness.sourceTheoremPort.conclusionMatchProof
    witness.inCellRelaxationTime
    witness.directionalJumpTime
    witness.admittedRelaxationToJumpRatio
    witness.relaxationBeforeJump

structure Q073Q012C1OperationalLocalEquilibriumCertificate
    (bridge : Q073Q012C1NarrowWindowLorentzBridge) : Type where
  mixingWitness : Q073Q012C1QuantitativeMixingWitness bridge
  timeScaleWitness : Q073Q012C1TimeScaleSeparationWitness bridge
  mixingBoundWithinTolerance :
    mixingWitness.correlationDecayBound ≤
      mixingWitness.admittedLocalEquilibriumTolerance
  jumpClockAfterMixingWindow : mixingWitness.jumpClockAfterMixingWindow
  relaxationBeforeJump :
    timeScaleWitness.inCellRelaxationTime ≤
      timeScaleWitness.directionalJumpTime *
        timeScaleWitness.admittedRelaxationToJumpRatio
  sourcePortCanonical :
    timeScaleWitness.sourceTheoremPort.sourceId =
      "GG_2011_TWO_STAGE_RELAXATION" ∧
      timeScaleWitness.sourceTheoremPort.statementId =
        "Q012_STMT_A1_DIFFUSION_COEFFICIENT" ∧
      timeScaleWitness.sourceTheoremPort.assetId =
        "Q012_A1_DIFFUSION_COEFFICIENT"
  localEquilibriumProof : bridge.localEquilibriumBetweenJumps

def q073_q012_c1_witnesses_yield_operational_local_equilibrium_certificate
    {bridge : Q073Q012C1NarrowWindowLorentzBridge}
    (mixingWitness : Q073Q012C1QuantitativeMixingWitness bridge)
    (timeScaleWitness : Q073Q012C1TimeScaleSeparationWitness bridge) :
    Q073Q012C1OperationalLocalEquilibriumCertificate bridge where
  mixingWitness := mixingWitness
  timeScaleWitness := timeScaleWitness
  mixingBoundWithinTolerance := mixingWitness.boundWithinTolerance
  jumpClockAfterMixingWindow := mixingWitness.windowProof
  relaxationBeforeJump := timeScaleWitness.relaxationBeforeJump
  sourcePortCanonical := ⟨timeScaleWitness.sourceTheoremPort.canonicalSourceId,
    timeScaleWitness.sourceTheoremPort.canonicalStatementId,
    timeScaleWitness.sourceTheoremPort.canonicalAssetId⟩
  localEquilibriumProof :=
    q073_q012_c1_time_scale_separation_yields_local_equilibrium timeScaleWitness

def q073_q012_c1_replayInCellRelaxationTime : Rat := 1

def q073_q012_c1_replayDirectionalJumpTime : Rat := 25

def q073_q012_c1_replayAdmittedRelaxationToJumpRatio : Rat := 1 / 10

def q073_q012_c1_replayRelaxationToJumpRatio : Rat := 1 / 25

theorem q073_q012_c1_replay_time_scale_ratio_within_gate :
    q073_q012_c1_replayRelaxationToJumpRatio ≤
      q073_q012_c1_replayAdmittedRelaxationToJumpRatio := by
  decide +kernel

theorem q073_q012_c1_replay_relaxation_before_jump_gate :
    q073_q012_c1_replayInCellRelaxationTime ≤
      q073_q012_c1_replayDirectionalJumpTime *
        q073_q012_c1_replayAdmittedRelaxationToJumpRatio := by
  decide +kernel

structure Q073Q012C1NarrowWindowAnalyticBridge : Type where
  bridge : Q073Q012C1NarrowWindowLorentzBridge
  mixingWitness : Q073Q012C1QuantitativeMixingWitness bridge
  timeScaleWitness : Q073Q012C1TimeScaleSeparationWitness bridge
  sourceA1ReductionValidForBilliard : Prop
  kineticFluxMatchesEscapeRate :
    q073_q012_c1_kineticFluxEscapeRate bridge.params =
      q073_q012_c1_escapeRate bridge.params
  escapeRateIsDirectionalJumpClock :
    q073_q012_c1_escapeRate bridge.params =
      q073_q012_c1_jumpFrequency bridge.params
  sourceReductionProof : sourceA1ReductionValidForBilliard

theorem q073_q012_c1_narrow_window_analytic_bridge_yields_coefficient
    (analytic : Q073Q012C1NarrowWindowAnalyticBridge) :
    analytic.bridge.narrowWindowRegime ∧
      analytic.bridge.localEquilibriumBetweenJumps ∧
      analytic.bridge.continuousTimeRandomWalkReduction ∧
      analytic.mixingWitness.correlationDecayBound ≤
        analytic.mixingWitness.admittedLocalEquilibriumTolerance ∧
      analytic.mixingWitness.jumpClockAfterMixingWindow ∧
      analytic.timeScaleWitness.inCellRelaxationTime ≤
        analytic.timeScaleWitness.directionalJumpTime *
          analytic.timeScaleWitness.admittedRelaxationToJumpRatio ∧
      analytic.timeScaleWitness.sourceTheoremPort.sourceTwoStageRelaxationTheorem ∧
      analytic.timeScaleWitness.sourceTheoremPort.sourceId =
        "GG_2011_TWO_STAGE_RELAXATION" ∧
      analytic.timeScaleWitness.sourceTheoremPort.statementId =
        "Q012_STMT_A1_DIFFUSION_COEFFICIENT" ∧
      analytic.sourceA1ReductionValidForBilliard ∧
      q073_q012_c1_diffusionCoefficient analytic.bridge.params =
        analytic.bridge.params.cellLength *
          analytic.bridge.params.cellLength *
          q073_q012_c1_kineticFluxEscapeRate analytic.bridge.params ∧
      q073_q012_c1_diffusionCoefficient analytic.bridge.params =
        analytic.bridge.params.cellLength *
          analytic.bridge.params.cellLength *
          (analytic.bridge.params.tracerSpeed *
            analytic.bridge.params.windowWidth *
            analytic.bridge.params.inversePi /
            analytic.bridge.params.cellArea) := by
  exact ⟨analytic.bridge.regimeProof,
    q073_q012_c1_quantitative_mixing_witness_yields_local_equilibrium
      analytic.mixingWitness,
    analytic.bridge.reductionProof,
    analytic.mixingWitness.boundWithinTolerance,
    analytic.mixingWitness.windowProof,
    analytic.timeScaleWitness.relaxationBeforeJump,
    analytic.timeScaleWitness.sourceTheoremPort.sourceTheoremProof,
    analytic.timeScaleWitness.sourceTheoremPort.canonicalSourceId,
    analytic.timeScaleWitness.sourceTheoremPort.canonicalStatementId,
    analytic.sourceReductionProof,
    by
      calc
        q073_q012_c1_diffusionCoefficient analytic.bridge.params =
            analytic.bridge.params.cellLength *
              analytic.bridge.params.cellLength *
              q073_q012_c1_jumpFrequency analytic.bridge.params := by
          rfl
        _ = analytic.bridge.params.cellLength *
              analytic.bridge.params.cellLength *
              q073_q012_c1_escapeRate analytic.bridge.params := by
          rw [← analytic.escapeRateIsDirectionalJumpClock]
        _ = analytic.bridge.params.cellLength *
              analytic.bridge.params.cellLength *
              q073_q012_c1_kineticFluxEscapeRate analytic.bridge.params := by
          rw [← analytic.kineticFluxMatchesEscapeRate],
    q073_q012_c1_lorentz_formula_is_internalized analytic.bridge.params⟩

structure Q073Q012C2RareCollisionHeatBridge : Type where
  params : Q073Q012C2RareCollisionHeatParams
  rareCollisionRegime : Prop
  localThermalEquilibrium : Prop
  stochasticEnergyExchangeReduction : Prop
  binaryCollisionFrequencyMatchesSourceUnitScale :
    params.binaryCollisionFrequency = params.sqrtTemperatureScale
  boundaryExcludesPluralTargetCollapse : Prop
  numericReplayEvidence : Q073NumericReplayEvidence
  analyticAsset : Q073SourceBoundAnalyticAsset
  regimeProof : rareCollisionRegime
  equilibriumProof : localThermalEquilibrium
  reductionProof : stochasticEnergyExchangeReduction
  boundaryProof : boundaryExcludesPluralTargetCollapse

structure Q073Q012C2SourceLocalThermalEquilibriumTheoremPort
    (bridge : Q073Q012C2RareCollisionHeatBridge) : Type where
  sourceId : String
  statementId : String
  assetId : String
  sourceLocator : String
  canonicalSourceId :
    sourceId = "GG_2011_TWO_STAGE_RELAXATION"
  canonicalStatementId :
    statementId = "Q012_STMT_A2_HEAT_CONDUCTIVITY_RARE_COLLISION"
  canonicalAssetId :
    assetId = "Q012_A2_HEAT_CONDUCTIVITY_RARE_COLLISION"
  canonicalLocator :
    sourceLocator = "PDF lines 398-412 and 563-572; equations (13) and (22)"
  sourceHypothesesCoverLocallyConfinedHardSphereBilliards : Prop
  sourceHypothesesCoverRareCollisionScaleSeparation : Prop
  sourceConclusionMatchesLocalThermalEquilibrium : Prop
  sourceConclusionMatchesStochasticEnergyExchangeReduction : Prop
  sourceRareCollisionHeatTheorem : Prop
  locallyConfinedHypothesisProof :
    sourceHypothesesCoverLocallyConfinedHardSphereBilliards
  rareCollisionScaleSeparationHypothesisProof :
    sourceHypothesesCoverRareCollisionScaleSeparation
  localThermalEquilibriumConclusionMatchProof :
    sourceConclusionMatchesLocalThermalEquilibrium
  stochasticReductionConclusionMatchProof :
    sourceConclusionMatchesStochasticEnergyExchangeReduction
  sourceTheoremProof : sourceRareCollisionHeatTheorem
  sourceTheoremMapsSeparationToLocalThermalEquilibrium :
    sourceRareCollisionHeatTheorem →
      sourceHypothesesCoverLocallyConfinedHardSphereBilliards →
      sourceHypothesesCoverRareCollisionScaleSeparation →
      sourceConclusionMatchesLocalThermalEquilibrium →
      bridge.localThermalEquilibrium
  sourceTheoremMapsReductionToStochasticEnergyExchange :
    sourceRareCollisionHeatTheorem →
      sourceHypothesesCoverLocallyConfinedHardSphereBilliards →
      sourceHypothesesCoverRareCollisionScaleSeparation →
      sourceConclusionMatchesStochasticEnergyExchangeReduction →
      bridge.stochasticEnergyExchangeReduction

theorem q073_q012_c2_source_local_thermal_equilibrium_port_is_canonical
    {bridge : Q073Q012C2RareCollisionHeatBridge}
    (port : Q073Q012C2SourceLocalThermalEquilibriumTheoremPort bridge) :
    port.sourceId = "GG_2011_TWO_STAGE_RELAXATION" ∧
      port.statementId = "Q012_STMT_A2_HEAT_CONDUCTIVITY_RARE_COLLISION" ∧
      port.assetId = "Q012_A2_HEAT_CONDUCTIVITY_RARE_COLLISION" ∧
      port.sourceLocator = "PDF lines 398-412 and 563-572; equations (13) and (22)" ∧
      port.sourceHypothesesCoverLocallyConfinedHardSphereBilliards ∧
      port.sourceHypothesesCoverRareCollisionScaleSeparation ∧
      port.sourceConclusionMatchesLocalThermalEquilibrium ∧
      port.sourceConclusionMatchesStochasticEnergyExchangeReduction ∧
      port.sourceRareCollisionHeatTheorem := by
  exact ⟨port.canonicalSourceId,
    port.canonicalStatementId,
    port.canonicalAssetId,
    port.canonicalLocator,
    port.locallyConfinedHypothesisProof,
    port.rareCollisionScaleSeparationHypothesisProof,
    port.localThermalEquilibriumConclusionMatchProof,
    port.stochasticReductionConclusionMatchProof,
    port.sourceTheoremProof⟩

structure Q073Q012C2OperationalLocalThermalEquilibriumCertificate
    (bridge : Q073Q012C2RareCollisionHeatBridge) : Type where
  sourceTheoremPort :
    Q073Q012C2SourceLocalThermalEquilibriumTheoremPort bridge
  sourcePortCanonical :
    sourceTheoremPort.sourceId =
      "GG_2011_TWO_STAGE_RELAXATION" ∧
      sourceTheoremPort.statementId =
        "Q012_STMT_A2_HEAT_CONDUCTIVITY_RARE_COLLISION" ∧
      sourceTheoremPort.assetId =
        "Q012_A2_HEAT_CONDUCTIVITY_RARE_COLLISION" ∧
      sourceTheoremPort.sourceLocator =
        "PDF lines 398-412 and 563-572; equations (13) and (22)"
  rareCollisionRegimeProof : bridge.rareCollisionRegime
  localThermalEquilibriumProof : bridge.localThermalEquilibrium
  stochasticEnergyExchangeReductionProof :
    bridge.stochasticEnergyExchangeReduction
  frequencyUnitScaleProof :
    bridge.params.binaryCollisionFrequency =
      bridge.params.sqrtTemperatureScale

def q073_q012_c2_source_port_yields_operational_local_thermal_equilibrium_certificate
    {bridge : Q073Q012C2RareCollisionHeatBridge}
    (port : Q073Q012C2SourceLocalThermalEquilibriumTheoremPort bridge) :
    Q073Q012C2OperationalLocalThermalEquilibriumCertificate bridge where
  sourceTheoremPort := port
  sourcePortCanonical := ⟨port.canonicalSourceId,
    port.canonicalStatementId,
    port.canonicalAssetId,
    port.canonicalLocator⟩
  rareCollisionRegimeProof := bridge.regimeProof
  localThermalEquilibriumProof :=
    port.sourceTheoremMapsSeparationToLocalThermalEquilibrium
      port.sourceTheoremProof
      port.locallyConfinedHypothesisProof
      port.rareCollisionScaleSeparationHypothesisProof
      port.localThermalEquilibriumConclusionMatchProof
  stochasticEnergyExchangeReductionProof :=
    port.sourceTheoremMapsReductionToStochasticEnergyExchange
      port.sourceTheoremProof
      port.locallyConfinedHypothesisProof
      port.rareCollisionScaleSeparationHypothesisProof
      port.stochasticReductionConclusionMatchProof
  frequencyUnitScaleProof :=
    bridge.binaryCollisionFrequencyMatchesSourceUnitScale

def Q073Q012C2RareCollisionHeatBridge.formulaPayload
    (bridge : Q073Q012C2RareCollisionHeatBridge) :
    Q073Q012TransportCoefficientPayload where
  billiardTaxonomy := bridge.rareCollisionRegime
  coefficientDefinitions :=
    q073_q012_c2_heatConductivity bridge.params =
      bridge.params.lengthScale * bridge.params.lengthScale *
        bridge.params.binaryCollisionFrequency
  coefficientFormulaOrAlgorithm := bridge.stochasticEnergyExchangeReduction
  analyticAssets := bridge.analyticAsset
  numericEvidence := bridge.numericReplayEvidence
  boundary := {
    coveredClassesSpecified := bridge.rareCollisionRegime
    excludedClassesSpecified := bridge.boundaryExcludesPluralTargetCollapse
    noOneSystemAsFullTarget := bridge.boundaryExcludesPluralTargetCollapse
    coveredProof := bridge.regimeProof
    excludedProof := bridge.boundaryProof
    noOneSystemProof := bridge.boundaryProof
  }
  taxonomyProof := bridge.regimeProof
  definitionProof := q073_q012_c2_rare_collision_formula_is_internalized bridge.params
  formulaOrAlgorithmProof := bridge.reductionProof

structure Q073Q012C2RareCollisionHeatEndToEndChain : Type where
  bridge : Q073Q012C2RareCollisionHeatBridge

theorem q073_q012_c2_rare_collision_chain_yields_source_unit_conductivity
    (chain : Q073Q012C2RareCollisionHeatEndToEndChain) :
    chain.bridge.rareCollisionRegime ∧
      chain.bridge.localThermalEquilibrium ∧
      chain.bridge.stochasticEnergyExchangeReduction ∧
      chain.bridge.params.binaryCollisionFrequency =
        chain.bridge.params.sqrtTemperatureScale ∧
      q073_q012_c2_heatConductivity chain.bridge.params =
        chain.bridge.params.lengthScale *
          chain.bridge.params.lengthScale *
          chain.bridge.params.sqrtTemperatureScale := by
  exact ⟨chain.bridge.regimeProof,
    chain.bridge.equilibriumProof,
    chain.bridge.reductionProof,
    chain.bridge.binaryCollisionFrequencyMatchesSourceUnitScale,
    Eq.trans
      (q073_q012_c2_binary_frequency_match_yields_source_unit_formula
        chain.bridge.params chain.bridge.binaryCollisionFrequencyMatchesSourceUnitScale)
      (q073_q012_c2_source_unit_conductivity_formula_is_internalized
        chain.bridge.params)⟩

structure Q073Q012C2SourceBoundRareCollisionAnalyticTheoremInstance
    (bridge : Q073Q012C2RareCollisionHeatBridge) : Type where
  sourcePort : Q073Q012C2SourceLocalThermalEquilibriumTheoremPort bridge
  operationalCertificate :
    Q073Q012C2OperationalLocalThermalEquilibriumCertificate bridge
  sourceReadbackSupportsLocallyConfinedHardSphereBilliards : Prop
  sourceReadbackSupportsRareCollisionScaleSeparation : Prop
  sourceReadbackSupportsLocalThermalEquilibrium : Prop
  sourceReadbackSupportsStochasticEnergyExchangeReduction : Prop
  sourceReadbackSupportsSourceUnitHeatConductivity : Prop
  sourceReadbackSupportsSqrtTemperatureScaling : Prop
  locallyConfinedReadbackProof :
    sourceReadbackSupportsLocallyConfinedHardSphereBilliards
  rareCollisionScaleSeparationReadbackProof :
    sourceReadbackSupportsRareCollisionScaleSeparation
  localThermalEquilibriumReadbackProof :
    sourceReadbackSupportsLocalThermalEquilibrium
  stochasticReductionReadbackProof :
    sourceReadbackSupportsStochasticEnergyExchangeReduction
  sourceUnitConductivityReadbackProof :
    sourceReadbackSupportsSourceUnitHeatConductivity
  sqrtTemperatureScalingReadbackProof :
    sourceReadbackSupportsSqrtTemperatureScaling

theorem q073_q012_c2_source_bound_instance_yields_rare_collision_heat_conductivity
    {bridge : Q073Q012C2RareCollisionHeatBridge}
    (inst :
      Q073Q012C2SourceBoundRareCollisionAnalyticTheoremInstance bridge) :
    bridge.rareCollisionRegime ∧
      bridge.localThermalEquilibrium ∧
      bridge.stochasticEnergyExchangeReduction ∧
      bridge.params.binaryCollisionFrequency =
        bridge.params.sqrtTemperatureScale ∧
      q073_q012_c2_heatConductivity bridge.params =
        bridge.params.lengthScale *
          bridge.params.lengthScale *
          bridge.params.sqrtTemperatureScale := by
  exact ⟨inst.operationalCertificate.rareCollisionRegimeProof,
    inst.operationalCertificate.localThermalEquilibriumProof,
    inst.operationalCertificate.stochasticEnergyExchangeReductionProof,
    inst.operationalCertificate.frequencyUnitScaleProof,
    Eq.trans
      (q073_q012_c2_binary_frequency_match_yields_source_unit_formula
        bridge.params inst.operationalCertificate.frequencyUnitScaleProof)
      (q073_q012_c2_source_unit_conductivity_formula_is_internalized
        bridge.params)⟩

theorem q073_q012_c2_bridge_yields_internal_formula_payload
    (bridge : Q073Q012C2RareCollisionHeatBridge) :
    ∃ payload : Q073Q012TransportCoefficientPayload,
      payload.coefficientDefinitions ∧
        payload.coefficientFormulaOrAlgorithm ∧
        payload.boundary.noOneSystemAsFullTarget := by
  refine ⟨bridge.formulaPayload, ?_⟩
  exact ⟨bridge.formulaPayload.definitionProof,
    bridge.formulaPayload.formulaOrAlgorithmProof,
    bridge.formulaPayload.boundary.noOneSystemProof⟩

structure Q073Q012C3FiniteSizeEstimatorBridge : Type where
  params : Q073Q012C3FiniteSizeEnvelopeParams
  stochasticChainRegime : Prop
  helfandVarianceGrowthAdmitted : Prop
  finiteSizeEnvelopeAdmitted : Prop
  boundaryExcludesPluralTargetCollapse : Prop
  numericReplayEvidence : Q073NumericReplayEvidence
  analyticAsset : Q073SourceBoundAnalyticAsset
  regimeProof : stochasticChainRegime
  helfandProof : helfandVarianceGrowthAdmitted
  envelopeProof : finiteSizeEnvelopeAdmitted
  boundaryProof : boundaryExcludesPluralTargetCollapse

structure Q073Q012C3SourceFiniteSizeEstimatorTheoremPort
    (bridge : Q073Q012C3FiniteSizeEstimatorBridge) : Type where
  sourceId : String
  statementId : String
  assetId : String
  sourceLocator : String
  canonicalSourceId :
    sourceId = "GG_2011_TWO_STAGE_RELAXATION"
  canonicalStatementId :
    statementId = "Q012_STMT_A3_HELFAND_CONDUCTIVITY_ESTIMATOR"
  canonicalAssetId :
    assetId = "Q012_A3_HELFAND_CONDUCTIVITY_ESTIMATOR"
  canonicalLocator :
    sourceLocator = "PDF lines 520-568; equations (18)-(22)"
  sourceHypothesesCoverFiniteStochasticChain : Prop
  sourceHypothesesCoverHelfandMoment : Prop
  sourceHypothesesCoverExchangeTimesAndTemperature : Prop
  sourceConclusionMatchesHelfandVarianceGrowth : Prop
  sourceConclusionMatchesFiniteSizeEnvelope : Prop
  sourceFiniteSizeEstimatorTheorem : Prop
  finiteStochasticChainHypothesisProof :
    sourceHypothesesCoverFiniteStochasticChain
  helfandMomentHypothesisProof :
    sourceHypothesesCoverHelfandMoment
  exchangeTimesAndTemperatureHypothesisProof :
    sourceHypothesesCoverExchangeTimesAndTemperature
  helfandVarianceConclusionMatchProof :
    sourceConclusionMatchesHelfandVarianceGrowth
  finiteSizeEnvelopeConclusionMatchProof :
    sourceConclusionMatchesFiniteSizeEnvelope
  sourceTheoremProof : sourceFiniteSizeEstimatorTheorem
  sourceTheoremMapsEstimatorToHelfandVarianceGrowth :
    sourceFiniteSizeEstimatorTheorem →
      sourceHypothesesCoverFiniteStochasticChain →
      sourceHypothesesCoverHelfandMoment →
      sourceHypothesesCoverExchangeTimesAndTemperature →
      sourceConclusionMatchesHelfandVarianceGrowth →
      bridge.helfandVarianceGrowthAdmitted
  sourceTheoremMapsEstimatorToFiniteSizeEnvelope :
    sourceFiniteSizeEstimatorTheorem →
      sourceHypothesesCoverFiniteStochasticChain →
      sourceHypothesesCoverHelfandMoment →
      sourceHypothesesCoverExchangeTimesAndTemperature →
      sourceConclusionMatchesFiniteSizeEnvelope →
      bridge.finiteSizeEnvelopeAdmitted

theorem q073_q012_c3_source_finite_size_estimator_port_is_canonical
    {bridge : Q073Q012C3FiniteSizeEstimatorBridge}
    (port : Q073Q012C3SourceFiniteSizeEstimatorTheoremPort bridge) :
    port.sourceId = "GG_2011_TWO_STAGE_RELAXATION" ∧
      port.statementId = "Q012_STMT_A3_HELFAND_CONDUCTIVITY_ESTIMATOR" ∧
      port.assetId = "Q012_A3_HELFAND_CONDUCTIVITY_ESTIMATOR" ∧
      port.sourceLocator = "PDF lines 520-568; equations (18)-(22)" ∧
      port.sourceHypothesesCoverFiniteStochasticChain ∧
      port.sourceHypothesesCoverHelfandMoment ∧
      port.sourceHypothesesCoverExchangeTimesAndTemperature ∧
      port.sourceConclusionMatchesHelfandVarianceGrowth ∧
      port.sourceConclusionMatchesFiniteSizeEnvelope ∧
      port.sourceFiniteSizeEstimatorTheorem := by
  exact ⟨port.canonicalSourceId,
    port.canonicalStatementId,
    port.canonicalAssetId,
    port.canonicalLocator,
    port.finiteStochasticChainHypothesisProof,
    port.helfandMomentHypothesisProof,
    port.exchangeTimesAndTemperatureHypothesisProof,
    port.helfandVarianceConclusionMatchProof,
    port.finiteSizeEnvelopeConclusionMatchProof,
    port.sourceTheoremProof⟩

structure Q073Q012C3OperationalFiniteSizeEstimatorCertificate
    (bridge : Q073Q012C3FiniteSizeEstimatorBridge) : Type where
  sourceTheoremPort :
    Q073Q012C3SourceFiniteSizeEstimatorTheoremPort bridge
  sourcePortCanonical :
    sourceTheoremPort.sourceId =
      "GG_2011_TWO_STAGE_RELAXATION" ∧
      sourceTheoremPort.statementId =
        "Q012_STMT_A3_HELFAND_CONDUCTIVITY_ESTIMATOR" ∧
      sourceTheoremPort.assetId =
        "Q012_A3_HELFAND_CONDUCTIVITY_ESTIMATOR" ∧
      sourceTheoremPort.sourceLocator =
        "PDF lines 520-568; equations (18)-(22)"
  stochasticChainRegimeProof : bridge.stochasticChainRegime
  helfandVarianceGrowthProof : bridge.helfandVarianceGrowthAdmitted
  finiteSizeEnvelopeProof : bridge.finiteSizeEnvelopeAdmitted
  lowerEnvelopeFormulaProof :
    q073_q012_c3_lowerEnvelope bridge.params =
      bridge.params.limitingConductivity *
        (1 - bridge.params.relativeCorrectionBound)
  upperEnvelopeFormulaProof :
    q073_q012_c3_upperEnvelope bridge.params =
      bridge.params.limitingConductivity *
        (1 + bridge.params.relativeCorrectionBound)

def q073_q012_c3_source_port_yields_operational_finite_size_estimator_certificate
    {bridge : Q073Q012C3FiniteSizeEstimatorBridge}
    (port : Q073Q012C3SourceFiniteSizeEstimatorTheoremPort bridge) :
    Q073Q012C3OperationalFiniteSizeEstimatorCertificate bridge where
  sourceTheoremPort := port
  sourcePortCanonical := ⟨port.canonicalSourceId,
    port.canonicalStatementId,
    port.canonicalAssetId,
    port.canonicalLocator⟩
  stochasticChainRegimeProof := bridge.regimeProof
  helfandVarianceGrowthProof :=
    port.sourceTheoremMapsEstimatorToHelfandVarianceGrowth
      port.sourceTheoremProof
      port.finiteStochasticChainHypothesisProof
      port.helfandMomentHypothesisProof
      port.exchangeTimesAndTemperatureHypothesisProof
      port.helfandVarianceConclusionMatchProof
  finiteSizeEnvelopeProof :=
    port.sourceTheoremMapsEstimatorToFiniteSizeEnvelope
      port.sourceTheoremProof
      port.finiteStochasticChainHypothesisProof
      port.helfandMomentHypothesisProof
      port.exchangeTimesAndTemperatureHypothesisProof
      port.finiteSizeEnvelopeConclusionMatchProof
  lowerEnvelopeFormulaProof := by
    rfl
  upperEnvelopeFormulaProof := by
    rfl

def Q073Q012C3FiniteSizeEstimatorBridge.formulaPayload
    (bridge : Q073Q012C3FiniteSizeEstimatorBridge) :
    Q073Q012TransportCoefficientPayload where
  billiardTaxonomy := bridge.stochasticChainRegime
  coefficientDefinitions :=
    q073_q012_c3_lowerEnvelope bridge.params =
        bridge.params.limitingConductivity *
          (1 - bridge.params.relativeCorrectionBound) ∧
      q073_q012_c3_upperEnvelope bridge.params =
        bridge.params.limitingConductivity *
          (1 + bridge.params.relativeCorrectionBound)
  coefficientFormulaOrAlgorithm := bridge.helfandVarianceGrowthAdmitted ∧
    bridge.finiteSizeEnvelopeAdmitted
  analyticAssets := bridge.analyticAsset
  numericEvidence := bridge.numericReplayEvidence
  boundary := {
    coveredClassesSpecified := bridge.stochasticChainRegime
    excludedClassesSpecified := bridge.boundaryExcludesPluralTargetCollapse
    noOneSystemAsFullTarget := bridge.boundaryExcludesPluralTargetCollapse
    coveredProof := bridge.regimeProof
    excludedProof := bridge.boundaryProof
    noOneSystemProof := bridge.boundaryProof
  }
  taxonomyProof := bridge.regimeProof
  definitionProof := q073_q012_c3_finite_size_envelope_is_internalized bridge.params
  formulaOrAlgorithmProof := ⟨bridge.helfandProof, bridge.envelopeProof⟩

theorem q073_q012_c3_bridge_yields_internal_formula_payload
    (bridge : Q073Q012C3FiniteSizeEstimatorBridge) :
    ∃ payload : Q073Q012TransportCoefficientPayload,
      payload.coefficientDefinitions ∧
        payload.coefficientFormulaOrAlgorithm ∧
        payload.boundary.noOneSystemAsFullTarget := by
  refine ⟨bridge.formulaPayload, ?_⟩
  exact ⟨bridge.formulaPayload.definitionProof,
    bridge.formulaPayload.formulaOrAlgorithmProof,
    bridge.formulaPayload.boundary.noOneSystemProof⟩

structure Q073Q012C3SourceBoundFiniteSizeEstimatorAnalyticTheoremInstance
    (bridge : Q073Q012C3FiniteSizeEstimatorBridge) : Type where
  sourcePort : Q073Q012C3SourceFiniteSizeEstimatorTheoremPort bridge
  operationalCertificate :
    Q073Q012C3OperationalFiniteSizeEstimatorCertificate bridge
  sourceReadbackSupportsFiniteStochasticChain : Prop
  sourceReadbackSupportsHelfandMoment : Prop
  sourceReadbackSupportsExchangeTimesAndTemperature : Prop
  sourceReadbackSupportsHelfandVarianceGrowth : Prop
  sourceReadbackSupportsFiniteSizeEnvelope : Prop
  sourceReadbackSupportsInfiniteSizeConductivityLimit : Prop
  finiteStochasticChainReadbackProof :
    sourceReadbackSupportsFiniteStochasticChain
  helfandMomentReadbackProof :
    sourceReadbackSupportsHelfandMoment
  exchangeTimesAndTemperatureReadbackProof :
    sourceReadbackSupportsExchangeTimesAndTemperature
  helfandVarianceGrowthReadbackProof :
    sourceReadbackSupportsHelfandVarianceGrowth
  finiteSizeEnvelopeReadbackProof :
    sourceReadbackSupportsFiniteSizeEnvelope
  infiniteSizeConductivityLimitReadbackProof :
    sourceReadbackSupportsInfiniteSizeConductivityLimit

theorem q073_q012_c3_source_bound_instance_yields_finite_size_estimator
    {bridge : Q073Q012C3FiniteSizeEstimatorBridge}
    (inst :
      Q073Q012C3SourceBoundFiniteSizeEstimatorAnalyticTheoremInstance bridge) :
    bridge.stochasticChainRegime ∧
      bridge.helfandVarianceGrowthAdmitted ∧
      bridge.finiteSizeEnvelopeAdmitted ∧
      q073_q012_c3_lowerEnvelope bridge.params =
        bridge.params.limitingConductivity *
          (1 - bridge.params.relativeCorrectionBound) ∧
      q073_q012_c3_upperEnvelope bridge.params =
        bridge.params.limitingConductivity *
          (1 + bridge.params.relativeCorrectionBound) := by
  exact ⟨inst.operationalCertificate.stochasticChainRegimeProof,
    inst.operationalCertificate.helfandVarianceGrowthProof,
    inst.operationalCertificate.finiteSizeEnvelopeProof,
    inst.operationalCertificate.lowerEnvelopeFormulaProof,
    inst.operationalCertificate.upperEnvelopeFormulaProof⟩

structure Q073Q012C4InfiniteHorizonAnomalousBridge : Type where
  params : Q073Q012C4AnomalousScaleParams
  infiniteHorizonClass : Prop
  anomalousScalingAdmitted : Prop
  ordinaryFiniteCoefficientRejected : Prop
  normalizationStillClassSpecific : Prop
  classProof : infiniteHorizonClass
  scalingProof : anomalousScalingAdmitted
  rejectionProof : ordinaryFiniteCoefficientRejected
  normalizationProof : normalizationStillClassSpecific

structure Q073Q012C4SourceAnomalousBoundaryPort
    (bridge : Q073Q012C4InfiniteHorizonAnomalousBridge) : Type where
  primarySourceUrl : String
  sourceDoi : String
  sourceLocator : String
  formalizationStatus : String
  exactEventualEqualitySourceProved : Bool
  exactMomentCoefficientSourceProved : Bool
  canonicalPrimarySource :
    primarySourceUrl = "https://math.umd.edu/~dolgop/LorLog3.pdf"
  canonicalSourceDoi :
    sourceDoi = "https://doi.org/10.1070/RM2009v064n04ABEH004630"
  canonicalLocator :
    sourceLocator =
      "Chernov-Dolgopyat (2009), Theorem 5, printed pp. 7-8; equation (2.1), printed p. 7"
  canonicalFormalizationStatus :
    formalizationStatus = "EXTERNAL_THEOREM_NOT_MECHANIZED"
  exactEventualEqualityNotSourceProved :
    exactEventualEqualitySourceProved = false
  exactMomentCoefficientNotSourceProved :
    exactMomentCoefficientSourceProved = false

/-!
The citation port above is metadata only.  It deliberately contains no
proposition standing for the cited theorem and no proof field that could turn a
bibliographic receipt into a Lean axiom.

The first theorem below preserves the older release-authorized conditional
lower-bound interface.  The source-bound wrappers that follow it now discharge
the previously missing Portmanteau/truncation step from explicit mathematical
inputs.  The external billiard weak CLT itself remains a source-bound input.
-/

theorem
    q073_q012_c4_external_lower_bound_bridge_rejects_finite_coefficient
    {effectiveCoefficient : ℝ → ℝ}
    {c : ℝ}
    (hc : 0 < c)
    (externalAnalyticLowerBound :
      ∀ᶠ t : ℝ in Filter.atTop,
        0 < t ∧ c * Real.log t ≤ effectiveCoefficient t) :
    ¬ ∃ finiteCoefficient : ℝ,
      Filter.Tendsto effectiveCoefficient Filter.atTop
        (nhds finiteCoefficient) := by
  exact
    q073_q012_eventual_positive_log_lower_bound_has_no_finite_ordinary_coefficient
      hc externalAnalyticLowerBound

theorem
    q073_q012_c4_source_bound_portmanteau_weak_limit_yields_positive_log_lower_bound
    {Ω : Type*}
    [MeasurableSpace Ω] [TopologicalSpace Ω] [OpensMeasurableSpace Ω]
    {μt : ℝ → MeasureTheory.ProbabilityMeasure Ω}
    {μLimit : MeasureTheory.ProbabilityMeasure Ω}
    (hWeak : Filter.Tendsto μt Filter.atTop (nhds μLimit))
    (truncatedSquaredNorm : Ω →ᵇ ℝ)
    (normalizedSecondMoment effectiveCoefficient : ℝ → ℝ)
    (hLimitPositive :
      0 < ∫ x, truncatedSquaredNorm x ∂(μLimit : MeasureTheory.Measure Ω))
    (hTruncationDominated :
      ∀ t,
        ∫ x, truncatedSquaredNorm x ∂(μt t : MeasureTheory.Measure Ω) ≤
          normalizedSecondMoment t)
    (hEffectiveCoefficient :
      ∀ t,
        effectiveCoefficient t =
          normalizedSecondMoment t * Real.log t / 4) :
    ∃ c : ℝ,
      0 < c ∧
        ∀ᶠ t : ℝ in Filter.atTop,
          0 < t ∧ c * Real.log t ≤ effectiveCoefficient t := by
  exact
    q073_weak_limit_truncation_yields_positive_log_lower_bound
      hWeak truncatedSquaredNorm normalizedSecondMoment effectiveCoefficient
      hLimitPositive hTruncationDominated hEffectiveCoefficient

theorem
    q073_q012_c4_source_bound_portmanteau_weak_limit_rejects_finite_ordinary_diffusion_coefficient
    {Ω : Type*}
    [MeasurableSpace Ω] [TopologicalSpace Ω] [OpensMeasurableSpace Ω]
    {μt : ℝ → MeasureTheory.ProbabilityMeasure Ω}
    {μLimit : MeasureTheory.ProbabilityMeasure Ω}
    (hWeak : Filter.Tendsto μt Filter.atTop (nhds μLimit))
    (truncatedSquaredNorm : Ω →ᵇ ℝ)
    (normalizedSecondMoment effectiveCoefficient : ℝ → ℝ)
    (hLimitPositive :
      0 < ∫ x, truncatedSquaredNorm x ∂(μLimit : MeasureTheory.Measure Ω))
    (hTruncationDominated :
      ∀ t,
        ∫ x, truncatedSquaredNorm x ∂(μt t : MeasureTheory.Measure Ω) ≤
          normalizedSecondMoment t)
    (hEffectiveCoefficient :
      ∀ t,
        effectiveCoefficient t =
          normalizedSecondMoment t * Real.log t / 4) :
    ¬ ∃ finiteCoefficient : ℝ,
      Filter.Tendsto effectiveCoefficient Filter.atTop
        (nhds finiteCoefficient) := by
  exact
    q073_weak_limit_truncation_rejects_finite_ordinary_diffusion_coefficient
      hWeak truncatedSquaredNorm normalizedSecondMoment effectiveCoefficient
      hLimitPositive hTruncationDominated hEffectiveCoefficient

theorem
    q073_q012_c4_source_bound_nondegenerate_weak_limit_tends_to_atTop
    {E : Type*}
    [NormedAddCommGroup E] [MeasurableSpace E] [BorelSpace E]
    {μt : ℝ → MeasureTheory.ProbabilityMeasure E}
    {μLimit : MeasureTheory.ProbabilityMeasure E}
    (hWeak : Filter.Tendsto μt Filter.atTop (nhds μLimit))
    (hNondegenerate :
      0 < (μLimit : MeasureTheory.Measure E) ({0}ᶜ))
    (normalizedSecondMoment effectiveCoefficient : ℝ → ℝ)
    (hTruncationDominated :
      ∀ t,
        ∫ x, q073_squared_norm_truncation E x
            ∂(μt t : MeasureTheory.Measure E) ≤
          normalizedSecondMoment t)
    (hEffectiveCoefficient :
      ∀ t,
        effectiveCoefficient t =
          normalizedSecondMoment t * Real.log t / 4) :
    Filter.Tendsto effectiveCoefficient Filter.atTop Filter.atTop := by
  exact
    q073_weak_nondegenerate_limit_tends_to_atTop
      hWeak hNondegenerate normalizedSecondMoment effectiveCoefficient
      hTruncationDominated hEffectiveCoefficient

theorem
    q073_q012_c4_source_bound_nondegenerate_weak_limit_rejects_finite_ordinary_diffusion_coefficient
    {E : Type*}
    [NormedAddCommGroup E] [MeasurableSpace E] [BorelSpace E]
    {μt : ℝ → MeasureTheory.ProbabilityMeasure E}
    {μLimit : MeasureTheory.ProbabilityMeasure E}
    (hWeak : Filter.Tendsto μt Filter.atTop (nhds μLimit))
    (hNondegenerate :
      0 < (μLimit : MeasureTheory.Measure E) ({0}ᶜ))
    (normalizedSecondMoment effectiveCoefficient : ℝ → ℝ)
    (hTruncationDominated :
      ∀ t,
        ∫ x, q073_squared_norm_truncation E x
            ∂(μt t : MeasureTheory.Measure E) ≤
          normalizedSecondMoment t)
    (hEffectiveCoefficient :
      ∀ t,
        effectiveCoefficient t =
          normalizedSecondMoment t * Real.log t / 4) :
    ¬ ∃ finiteCoefficient : ℝ,
      Filter.Tendsto effectiveCoefficient Filter.atTop
        (nhds finiteCoefficient) := by
  exact
    q073_weak_nondegenerate_limit_rejects_finite_ordinary_diffusion_coefficient
      hWeak hNondegenerate normalizedSecondMoment effectiveCoefficient
      hTruncationDominated hEffectiveCoefficient

/-!
Retired overstrong interface.  This remains a valid real-analysis implication
for callers that independently prove an eventual exact equality.  No source
receipt supplies that premise, and release verification must reject its use as
a C4 closure witness.
-/

theorem
    q073_q012_c4_retired_exact_log_regime_conditionally_rejects_finite_coefficient
    {effectiveCoefficient : ℝ → ℝ}
    {D0 t0 : ℝ}
    (hD0 : 0 < D0)
    (ht0 : 0 < t0)
    (independentlyProvedExactRegime :
      effectiveCoefficient =ᶠ[Filter.atTop]
        q073_q012_logarithmic_diffusion_coefficient D0 t0) :
    ¬ ∃ finiteCoefficient : ℝ,
      Filter.Tendsto effectiveCoefficient Filter.atTop
        (nhds finiteCoefficient) := by
  exact
    q073_q012_eventually_logarithmic_diffusion_has_no_finite_ordinary_coefficient
      hD0 ht0 independentlyProvedExactRegime

theorem q073_q012_c4_source_anomalous_boundary_port_is_canonical
    {bridge : Q073Q012C4InfiniteHorizonAnomalousBridge}
    (port : Q073Q012C4SourceAnomalousBoundaryPort bridge) :
    port.primarySourceUrl = "https://math.umd.edu/~dolgop/LorLog3.pdf" ∧
      port.sourceDoi =
        "https://doi.org/10.1070/RM2009v064n04ABEH004630" ∧
      port.sourceLocator =
        "Chernov-Dolgopyat (2009), Theorem 5, printed pp. 7-8; equation (2.1), printed p. 7" ∧
      port.formalizationStatus = "EXTERNAL_THEOREM_NOT_MECHANIZED" ∧
      port.exactEventualEqualitySourceProved = false ∧
      port.exactMomentCoefficientSourceProved = false := by
  exact ⟨port.canonicalPrimarySource,
    port.canonicalSourceDoi,
    port.canonicalLocator,
    port.canonicalFormalizationStatus,
    port.exactEventualEqualityNotSourceProved,
    port.exactMomentCoefficientNotSourceProved⟩

structure Q073Q012C4OperationalAnomalousBoundaryCertificate
    (bridge : Q073Q012C4InfiniteHorizonAnomalousBridge) : Type where
  sourceBoundaryPort :
    Q073Q012C4SourceAnomalousBoundaryPort bridge
  sourcePortCanonical :
    sourceBoundaryPort.primarySourceUrl =
      "https://math.umd.edu/~dolgop/LorLog3.pdf" ∧
      sourceBoundaryPort.sourceDoi =
        "https://doi.org/10.1070/RM2009v064n04ABEH004630" ∧
      sourceBoundaryPort.sourceLocator =
        "Chernov-Dolgopyat (2009), Theorem 5, printed pp. 7-8; equation (2.1), printed p. 7"
  externalWeakCLTNotMechanized :
    sourceBoundaryPort.formalizationStatus =
      "EXTERNAL_THEOREM_NOT_MECHANIZED"
  exactEventualEqualityNotSourceProved :
    sourceBoundaryPort.exactEventualEqualitySourceProved = false
  exactMomentCoefficientNotSourceProved :
    sourceBoundaryPort.exactMomentCoefficientSourceProved = false
  infiniteHorizonClassProof : bridge.infiniteHorizonClass
  conditionalAnomalousScalingPremise : bridge.anomalousScalingAdmitted
  conditionalOrdinaryFiniteCoefficientRejectionPremise :
    bridge.ordinaryFiniteCoefficientRejected
  conditionalClassSpecificNormalizationPremise :
    bridge.normalizationStillClassSpecific

def q073_q012_c4_source_port_yields_operational_anomalous_boundary_certificate
    {bridge : Q073Q012C4InfiniteHorizonAnomalousBridge}
    (port : Q073Q012C4SourceAnomalousBoundaryPort bridge) :
    Q073Q012C4OperationalAnomalousBoundaryCertificate bridge where
  sourceBoundaryPort := port
  sourcePortCanonical := ⟨port.canonicalPrimarySource,
    port.canonicalSourceDoi,
    port.canonicalLocator⟩
  externalWeakCLTNotMechanized := port.canonicalFormalizationStatus
  exactEventualEqualityNotSourceProved :=
    port.exactEventualEqualityNotSourceProved
  exactMomentCoefficientNotSourceProved :=
    port.exactMomentCoefficientNotSourceProved
  infiniteHorizonClassProof := bridge.classProof
  conditionalAnomalousScalingPremise := bridge.scalingProof
  conditionalOrdinaryFiniteCoefficientRejectionPremise :=
    bridge.rejectionProof
  conditionalClassSpecificNormalizationPremise :=
    bridge.normalizationProof

def Q073Q012C4InfiniteHorizonAnomalousBridge.limitingPayload
    (bridge : Q073Q012C4InfiniteHorizonAnomalousBridge) :
    Q073Q012NegativeOrLimitingPayload where
  namedBilliardClass := bridge.infiniteHorizonClass
  coefficientNonexistenceOrNoUniformScheme :=
    bridge.anomalousScalingAdmitted ∧
      bridge.ordinaryFiniteCoefficientRejected ∧
      q073_q012_c4_meanSquareDisplacement bridge.params =
        4 * bridge.params.time *
          (bridge.params.baseAnomalousCoefficient *
            bridge.params.logTimeRatio)
  assumptionsNeededForDecidability := bridge.normalizationStillClassSpecific
  classProof := bridge.classProof
  obstructionProof := ⟨bridge.scalingProof,
    bridge.rejectionProof,
    q073_q012_c4_anomalous_scaling_is_internalized bridge.params⟩
  assumptionProof := bridge.normalizationProof

theorem q073_q012_c4_bridge_yields_internal_limiting_payload
    (bridge : Q073Q012C4InfiniteHorizonAnomalousBridge) :
    ∃ payload : Q073Q012NegativeOrLimitingPayload,
      payload.namedBilliardClass ∧
        payload.coefficientNonexistenceOrNoUniformScheme ∧
        payload.assumptionsNeededForDecidability := by
  refine ⟨bridge.limitingPayload, ?_⟩
  exact ⟨bridge.limitingPayload.classProof,
    bridge.limitingPayload.obstructionProof,
    bridge.limitingPayload.assumptionProof⟩

structure Q073Q012C4SourceBoundAnomalousBoundaryTheoremInstance
    (bridge : Q073Q012C4InfiniteHorizonAnomalousBridge) : Type where
  sourcePort : Q073Q012C4SourceAnomalousBoundaryPort bridge
  operationalCertificate :
    Q073Q012C4OperationalAnomalousBoundaryCertificate bridge
  sourceModelAndHypothesesReadBack : Bool
  weakCLTExternalNotMechanized : Bool
  portmanteauWeakLimitToPositiveLogLowerBoundBridgeMechanized : Bool
  exactEventualEqualitySourceProved : Bool
  exactMomentCoefficientSourceProved : Bool
  physicalBilliardSimulationPresent : Bool
  sourceModelAndHypothesesReadBackProof :
    sourceModelAndHypothesesReadBack = true
  weakCLTExternalNotMechanizedProof :
    weakCLTExternalNotMechanized = true
  portmanteauWeakLimitToPositiveLogLowerBoundBridgeMechanizedProof :
    portmanteauWeakLimitToPositiveLogLowerBoundBridgeMechanized = true
  exactEventualEqualityNotSourceProved :
    exactEventualEqualitySourceProved = false
  exactMomentCoefficientNotSourceProved :
    exactMomentCoefficientSourceProved = false
  physicalBilliardSimulationPresentProof :
    physicalBilliardSimulationPresent = true

theorem
    q073_q012_c4_source_bound_instance_records_scoped_portmanteau_bridge_closed_with_exact_asymptotics_unclaimed
    {bridge : Q073Q012C4InfiniteHorizonAnomalousBridge}
    (inst :
      Q073Q012C4SourceBoundAnomalousBoundaryTheoremInstance bridge) :
    inst.sourcePort.formalizationStatus =
        "EXTERNAL_THEOREM_NOT_MECHANIZED" ∧
      inst.weakCLTExternalNotMechanized = true ∧
      inst.portmanteauWeakLimitToPositiveLogLowerBoundBridgeMechanized =
        true ∧
      inst.sourcePort.exactEventualEqualitySourceProved = false ∧
      inst.sourcePort.exactMomentCoefficientSourceProved = false ∧
      inst.physicalBilliardSimulationPresent = true := by
  exact ⟨inst.sourcePort.canonicalFormalizationStatus,
    inst.weakCLTExternalNotMechanizedProof,
    inst.portmanteauWeakLimitToPositiveLogLowerBoundBridgeMechanizedProof,
    inst.sourcePort.exactEventualEqualityNotSourceProved,
    inst.sourcePort.exactMomentCoefficientNotSourceProved,
    inst.physicalBilliardSimulationPresentProof⟩

structure Q073Q012C5PolygonalFrontierBridge : Type where
  boundary : Q073Q012C5PolygonalFrontierBoundary
  subclassGeometrySpecified : Prop
  observableSpecified : Prop
  classSpecificTheoremOrNoUniformTheoremRequired : Prop
  geometryProof : subclassGeometrySpecified
  observableSpecifiedProof : observableSpecified
  theoremRequirementProof : classSpecificTheoremOrNoUniformTheoremRequired

structure Q073Q012C5SourcePolygonalFrontierPort
    (bridge : Q073Q012C5PolygonalFrontierBridge) : Type where
  windTreeGenericSourceUrl : String
  windTreeNonGenericSourceUrl : String
  openPolygonalChannelSourceUrl : String
  sourceLocator : String
  canonicalWindTreeGenericSource :
    windTreeGenericSourceUrl = "https://arxiv.org/abs/1107.1810"
  canonicalWindTreeNonGenericSource :
    windTreeNonGenericSourceUrl = "https://arxiv.org/abs/2308.15121"
  canonicalOpenPolygonalChannelSource :
    openPolygonalChannelSourceUrl = "https://arxiv.org/abs/2104.03704"
  canonicalLocator :
    sourceLocator = "abstract/source theorem context"
  sourceHypothesesCoverPolygonalNonchaoticClasses : Prop
  sourceHypothesesRequireGeometryAndObservable : Prop
  sourceConclusionRejectsHyperbolicSurrogate : Prop
  sourceConclusionRequiresClassSpecificTheoremOrNoUniformTheorem : Prop
  sourceFrontierTheorem : Prop
  polygonalNonchaoticHypothesisProof :
    sourceHypothesesCoverPolygonalNonchaoticClasses
  geometryAndObservableHypothesisProof :
    sourceHypothesesRequireGeometryAndObservable
  hyperbolicSurrogateRejectionConclusionProof :
    sourceConclusionRejectsHyperbolicSurrogate
  classSpecificRequirementConclusionProof :
    sourceConclusionRequiresClassSpecificTheoremOrNoUniformTheorem
  sourceTheoremProof : sourceFrontierTheorem
  sourceTheoremMapsToHyperbolicSurrogateRejection :
    sourceFrontierTheorem →
      sourceHypothesesCoverPolygonalNonchaoticClasses →
      sourceConclusionRejectsHyperbolicSurrogate →
      bridge.boundary.hyperbolicSurrogateRejected
  sourceTheoremMapsToClassSpecificRequirement :
    sourceFrontierTheorem →
      sourceHypothesesCoverPolygonalNonchaoticClasses →
      sourceConclusionRequiresClassSpecificTheoremOrNoUniformTheorem →
      bridge.classSpecificTheoremOrNoUniformTheoremRequired
  sourceTheoremMapsToGeometryRequirement :
    sourceFrontierTheorem →
      sourceHypothesesRequireGeometryAndObservable →
      bridge.subclassGeometrySpecified
  sourceTheoremMapsToObservableRequirement :
    sourceFrontierTheorem →
      sourceHypothesesRequireGeometryAndObservable →
      bridge.observableSpecified

theorem q073_q012_c5_source_polygonal_frontier_port_is_canonical
    {bridge : Q073Q012C5PolygonalFrontierBridge}
    (port : Q073Q012C5SourcePolygonalFrontierPort bridge) :
    port.windTreeGenericSourceUrl = "https://arxiv.org/abs/1107.1810" ∧
      port.windTreeNonGenericSourceUrl = "https://arxiv.org/abs/2308.15121" ∧
      port.openPolygonalChannelSourceUrl = "https://arxiv.org/abs/2104.03704" ∧
      port.sourceLocator = "abstract/source theorem context" ∧
      port.sourceHypothesesCoverPolygonalNonchaoticClasses ∧
      port.sourceHypothesesRequireGeometryAndObservable ∧
      port.sourceConclusionRejectsHyperbolicSurrogate ∧
      port.sourceConclusionRequiresClassSpecificTheoremOrNoUniformTheorem ∧
      port.sourceFrontierTheorem := by
  exact ⟨port.canonicalWindTreeGenericSource,
    port.canonicalWindTreeNonGenericSource,
    port.canonicalOpenPolygonalChannelSource,
    port.canonicalLocator,
    port.polygonalNonchaoticHypothesisProof,
    port.geometryAndObservableHypothesisProof,
    port.hyperbolicSurrogateRejectionConclusionProof,
    port.classSpecificRequirementConclusionProof,
    port.sourceTheoremProof⟩

structure Q073Q012C5OperationalPolygonalFrontierCertificate
    (bridge : Q073Q012C5PolygonalFrontierBridge) : Type where
  sourceFrontierPort :
    Q073Q012C5SourcePolygonalFrontierPort bridge
  sourcePortCanonical :
    sourceFrontierPort.windTreeGenericSourceUrl =
      "https://arxiv.org/abs/1107.1810" ∧
      sourceFrontierPort.windTreeNonGenericSourceUrl =
        "https://arxiv.org/abs/2308.15121" ∧
      sourceFrontierPort.openPolygonalChannelSourceUrl =
        "https://arxiv.org/abs/2104.03704" ∧
      sourceFrontierPort.sourceLocator =
        "abstract/source theorem context"
  namedPolygonalOrNonchaoticClassProof :
    bridge.boundary.namedPolygonalOrNonchaoticClass
  hyperbolicSurrogateRejectionProof :
    bridge.boundary.hyperbolicSurrogateRejected
  classSpecificRequirementProof :
    bridge.classSpecificTheoremOrNoUniformTheoremRequired
  subclassGeometrySpecifiedProof :
    bridge.subclassGeometrySpecified
  observableSpecifiedProof :
    bridge.observableSpecified

def q073_q012_c5_source_port_yields_operational_polygonal_frontier_certificate
    {bridge : Q073Q012C5PolygonalFrontierBridge}
    (port : Q073Q012C5SourcePolygonalFrontierPort bridge) :
    Q073Q012C5OperationalPolygonalFrontierCertificate bridge where
  sourceFrontierPort := port
  sourcePortCanonical := ⟨port.canonicalWindTreeGenericSource,
    port.canonicalWindTreeNonGenericSource,
    port.canonicalOpenPolygonalChannelSource,
    port.canonicalLocator⟩
  namedPolygonalOrNonchaoticClassProof := bridge.boundary.classProof
  hyperbolicSurrogateRejectionProof :=
    port.sourceTheoremMapsToHyperbolicSurrogateRejection
      port.sourceTheoremProof
      port.polygonalNonchaoticHypothesisProof
      port.hyperbolicSurrogateRejectionConclusionProof
  classSpecificRequirementProof :=
    port.sourceTheoremMapsToClassSpecificRequirement
      port.sourceTheoremProof
      port.polygonalNonchaoticHypothesisProof
      port.classSpecificRequirementConclusionProof
  subclassGeometrySpecifiedProof :=
    port.sourceTheoremMapsToGeometryRequirement
      port.sourceTheoremProof
      port.geometryAndObservableHypothesisProof
  observableSpecifiedProof :=
    port.sourceTheoremMapsToObservableRequirement
      port.sourceTheoremProof
      port.geometryAndObservableHypothesisProof

def Q073Q012C5PolygonalFrontierBridge.limitingPayload
    (bridge : Q073Q012C5PolygonalFrontierBridge) :
    Q073Q012NegativeOrLimitingPayload where
  namedBilliardClass := bridge.boundary.namedPolygonalOrNonchaoticClass
  coefficientNonexistenceOrNoUniformScheme :=
    bridge.boundary.hyperbolicSurrogateRejected ∧
      bridge.classSpecificTheoremOrNoUniformTheoremRequired
  assumptionsNeededForDecidability :=
    bridge.subclassGeometrySpecified ∧ bridge.observableSpecified
  classProof := bridge.boundary.classProof
  obstructionProof := ⟨bridge.boundary.rejectionProof,
    bridge.theoremRequirementProof⟩
  assumptionProof := ⟨bridge.geometryProof, bridge.observableSpecifiedProof⟩

theorem q073_q012_c5_bridge_yields_internal_frontier_payload
    (bridge : Q073Q012C5PolygonalFrontierBridge) :
    ∃ payload : Q073Q012NegativeOrLimitingPayload,
      payload.namedBilliardClass ∧
        payload.coefficientNonexistenceOrNoUniformScheme ∧
        payload.assumptionsNeededForDecidability := by
  refine ⟨bridge.limitingPayload, ?_⟩
  exact ⟨bridge.limitingPayload.classProof,
    bridge.limitingPayload.obstructionProof,
    bridge.limitingPayload.assumptionProof⟩

structure Q073Q012C5SourceBoundPolygonalFrontierTheoremInstance
    (bridge : Q073Q012C5PolygonalFrontierBridge) : Type where
  sourcePort : Q073Q012C5SourcePolygonalFrontierPort bridge
  operationalCertificate :
    Q073Q012C5OperationalPolygonalFrontierCertificate bridge
  sourceReadbackSupportsWindTreeGenericNonordinaryExponent : Prop
  sourceReadbackSupportsWindTreeNonGenericExponentVariety : Prop
  sourceReadbackSupportsOpenPolygonalChannelAnomalousTransport : Prop
  sourceReadbackSupportsPolygonalLockingRelation : Prop
  sourceReadbackRejectsHyperbolicSurrogate : Prop
  sourceReadbackRequiresGeometryObservableGates : Prop
  windTreeGenericProof :
    sourceReadbackSupportsWindTreeGenericNonordinaryExponent
  windTreeNonGenericProof :
    sourceReadbackSupportsWindTreeNonGenericExponentVariety
  openPolygonalChannelProof :
    sourceReadbackSupportsOpenPolygonalChannelAnomalousTransport
  polygonalLockingRelationProof :
    sourceReadbackSupportsPolygonalLockingRelation
  hyperbolicSurrogateRejectedProof :
    sourceReadbackRejectsHyperbolicSurrogate
  geometryObservableGateProof :
    sourceReadbackRequiresGeometryObservableGates

theorem q073_q012_c5_source_bound_instance_yields_polygonal_frontier
    {bridge : Q073Q012C5PolygonalFrontierBridge}
    (inst : Q073Q012C5SourceBoundPolygonalFrontierTheoremInstance bridge) :
    bridge.boundary.namedPolygonalOrNonchaoticClass ∧
      bridge.boundary.hyperbolicSurrogateRejected ∧
      bridge.classSpecificTheoremOrNoUniformTheoremRequired ∧
      bridge.subclassGeometrySpecified ∧
      bridge.observableSpecified := by
  exact ⟨inst.operationalCertificate.namedPolygonalOrNonchaoticClassProof,
    inst.operationalCertificate.hyperbolicSurrogateRejectionProof,
    inst.operationalCertificate.classSpecificRequirementProof,
    inst.operationalCertificate.subclassGeometrySpecifiedProof,
    inst.operationalCertificate.observableSpecifiedProof⟩

structure Q073Q012FullPluralTransportCoverage : Type where
  c1Analytic : Q073Q012C1NarrowWindowAnalyticBridge
  c2SourceUnit : Q073Q012C2RareCollisionHeatEndToEndChain
  c3FiniteSize : Q073Q012C3FiniteSizeEstimatorBridge
  c4InfiniteHorizonBoundary : Q073Q012C4InfiniteHorizonAnomalousBridge
  c5PolygonalFrontier : Q073Q012C5PolygonalFrontierBridge

def Q073Q012FullPluralTransportCoverage.declaredVarietyCoveredOrBounded
    (coverage : Q073Q012FullPluralTransportCoverage) : Prop :=
  coverage.c1Analytic.bridge.narrowWindowRegime ∧
    coverage.c2SourceUnit.bridge.rareCollisionRegime ∧
    coverage.c3FiniteSize.stochasticChainRegime ∧
    coverage.c4InfiniteHorizonBoundary.infiniteHorizonClass ∧
    coverage.c5PolygonalFrontier.boundary.namedPolygonalOrNonchaoticClass

theorem q073_q012_full_plural_transport_coverage_declares_variety
    (coverage : Q073Q012FullPluralTransportCoverage) :
    coverage.declaredVarietyCoveredOrBounded := by
  exact ⟨coverage.c1Analytic.bridge.regimeProof,
    coverage.c2SourceUnit.bridge.regimeProof,
    coverage.c3FiniteSize.regimeProof,
    coverage.c4InfiniteHorizonBoundary.classProof,
    coverage.c5PolygonalFrontier.boundary.classProof⟩

def Q073Q012FullPluralTransportCoverage.noSingleSubclassSoldAsPluralTarget
    (coverage : Q073Q012FullPluralTransportCoverage) : Prop :=
  coverage.c1Analytic.bridge.boundaryExcludesPluralTargetCollapse ∧
    coverage.c2SourceUnit.bridge.boundaryExcludesPluralTargetCollapse ∧
    coverage.c3FiniteSize.boundaryExcludesPluralTargetCollapse ∧
    coverage.c4InfiniteHorizonBoundary.ordinaryFiniteCoefficientRejected ∧
    coverage.c4InfiniteHorizonBoundary.normalizationStillClassSpecific ∧
    coverage.c5PolygonalFrontier.classSpecificTheoremOrNoUniformTheoremRequired

theorem q073_q012_full_plural_transport_coverage_prevents_single_subclass_claim
    (coverage : Q073Q012FullPluralTransportCoverage) :
    coverage.noSingleSubclassSoldAsPluralTarget := by
  exact ⟨coverage.c1Analytic.bridge.boundaryProof,
    coverage.c2SourceUnit.bridge.boundaryProof,
    coverage.c3FiniteSize.boundaryProof,
    coverage.c4InfiniteHorizonBoundary.rejectionProof,
    coverage.c4InfiniteHorizonBoundary.normalizationProof,
    coverage.c5PolygonalFrontier.theoremRequirementProof⟩

structure Q073Q012FullPluralSourceBoundEvidencePackage : Type where
  coverage : Q073Q012FullPluralTransportCoverage
  c1SourceBound :
    Q073Q012C1SourceBoundLocalEquilibriumTheoremInstance
      coverage.c1Analytic.bridge
  c2SourceBound :
    Q073Q012C2SourceBoundRareCollisionAnalyticTheoremInstance
      coverage.c2SourceUnit.bridge
  c3SourceBound :
    Q073Q012C3SourceBoundFiniteSizeEstimatorAnalyticTheoremInstance
      coverage.c3FiniteSize
  c4SourceBound :
    Q073Q012C4SourceBoundAnomalousBoundaryTheoremInstance
      coverage.c4InfiniteHorizonBoundary
  c5SourceBound :
    Q073Q012C5SourceBoundPolygonalFrontierTheoremInstance
      coverage.c5PolygonalFrontier

def Q073Q012FullPluralSourceBoundEvidencePackage.noSingleUniformOrdinaryFiniteCoefficient
    (package : Q073Q012FullPluralSourceBoundEvidencePackage) : Prop :=
  package.coverage.declaredVarietyCoveredOrBounded ∧
    package.coverage.noSingleSubclassSoldAsPluralTarget ∧
    package.coverage.c4InfiniteHorizonBoundary.ordinaryFiniteCoefficientRejected ∧
    package.coverage.c4InfiniteHorizonBoundary.normalizationStillClassSpecific ∧
    package.coverage.c5PolygonalFrontier.classSpecificTheoremOrNoUniformTheoremRequired ∧
    package.c5SourceBound.sourceReadbackRejectsHyperbolicSurrogate ∧
    package.c5SourceBound.sourceReadbackRequiresGeometryObservableGates

theorem q073_q012_source_bound_package_rejects_single_uniform_ordinary_coefficient
    (package : Q073Q012FullPluralSourceBoundEvidencePackage) :
    package.noSingleUniformOrdinaryFiniteCoefficient := by
  exact ⟨q073_q012_full_plural_transport_coverage_declares_variety package.coverage,
    q073_q012_full_plural_transport_coverage_prevents_single_subclass_claim
      package.coverage,
    package.coverage.c4InfiniteHorizonBoundary.rejectionProof,
    package.coverage.c4InfiniteHorizonBoundary.normalizationProof,
    package.c5SourceBound.operationalCertificate.classSpecificRequirementProof,
    package.c5SourceBound.hyperbolicSurrogateRejectedProof,
    package.c5SourceBound.geometryObservableGateProof⟩

def Q073Q012FullPluralTransportCoverage.sourceAndReplayBundlePublicSafe
    (coverage : Q073Q012FullPluralTransportCoverage) : Prop :=
  coverage.c1Analytic.bridge.analyticAsset.sourceBoundStatement ∧
    coverage.c1Analytic.bridge.analyticAsset.hypothesesSpecified ∧
    coverage.c1Analytic.bridge.analyticAsset.conclusionSpecified ∧
    coverage.c1Analytic.bridge.analyticAsset.proofReferenceOrInternalProof ∧
    coverage.c1Analytic.bridge.numericReplayEvidence.replaySpecified ∧
    coverage.c1Analytic.bridge.numericReplayEvidence.parameterRegimeSpecified ∧
    coverage.c1Analytic.bridge.numericReplayEvidence.errorBarsOrUncertaintySpecified ∧
    coverage.c1Analytic.bridge.numericReplayEvidence.reproducibleCommandOrManifest ∧
    coverage.c2SourceUnit.bridge.analyticAsset.sourceBoundStatement ∧
    coverage.c2SourceUnit.bridge.analyticAsset.hypothesesSpecified ∧
    coverage.c2SourceUnit.bridge.analyticAsset.conclusionSpecified ∧
    coverage.c2SourceUnit.bridge.analyticAsset.proofReferenceOrInternalProof ∧
    coverage.c2SourceUnit.bridge.numericReplayEvidence.replaySpecified ∧
    coverage.c2SourceUnit.bridge.numericReplayEvidence.parameterRegimeSpecified ∧
    coverage.c2SourceUnit.bridge.numericReplayEvidence.errorBarsOrUncertaintySpecified ∧
    coverage.c2SourceUnit.bridge.numericReplayEvidence.reproducibleCommandOrManifest ∧
    coverage.c3FiniteSize.analyticAsset.sourceBoundStatement ∧
    coverage.c3FiniteSize.analyticAsset.hypothesesSpecified ∧
    coverage.c3FiniteSize.analyticAsset.conclusionSpecified ∧
    coverage.c3FiniteSize.analyticAsset.proofReferenceOrInternalProof ∧
    coverage.c3FiniteSize.numericReplayEvidence.replaySpecified ∧
    coverage.c3FiniteSize.numericReplayEvidence.parameterRegimeSpecified ∧
    coverage.c3FiniteSize.numericReplayEvidence.errorBarsOrUncertaintySpecified ∧
    coverage.c3FiniteSize.numericReplayEvidence.reproducibleCommandOrManifest

theorem q073_q012_full_plural_transport_coverage_public_bundle_safe
    (coverage : Q073Q012FullPluralTransportCoverage) :
    coverage.sourceAndReplayBundlePublicSafe := by
  exact ⟨coverage.c1Analytic.bridge.analyticAsset.sourceBoundProof,
    coverage.c1Analytic.bridge.analyticAsset.hypothesesProof,
    coverage.c1Analytic.bridge.analyticAsset.conclusionProof,
    coverage.c1Analytic.bridge.analyticAsset.proofEvidence,
    coverage.c1Analytic.bridge.numericReplayEvidence.replayProof,
    coverage.c1Analytic.bridge.numericReplayEvidence.parameterProof,
    coverage.c1Analytic.bridge.numericReplayEvidence.uncertaintyProof,
    coverage.c1Analytic.bridge.numericReplayEvidence.reproducibilityProof,
    coverage.c2SourceUnit.bridge.analyticAsset.sourceBoundProof,
    coverage.c2SourceUnit.bridge.analyticAsset.hypothesesProof,
    coverage.c2SourceUnit.bridge.analyticAsset.conclusionProof,
    coverage.c2SourceUnit.bridge.analyticAsset.proofEvidence,
    coverage.c2SourceUnit.bridge.numericReplayEvidence.replayProof,
    coverage.c2SourceUnit.bridge.numericReplayEvidence.parameterProof,
    coverage.c2SourceUnit.bridge.numericReplayEvidence.uncertaintyProof,
    coverage.c2SourceUnit.bridge.numericReplayEvidence.reproducibilityProof,
    coverage.c3FiniteSize.analyticAsset.sourceBoundProof,
    coverage.c3FiniteSize.analyticAsset.hypothesesProof,
    coverage.c3FiniteSize.analyticAsset.conclusionProof,
    coverage.c3FiniteSize.analyticAsset.proofEvidence,
    coverage.c3FiniteSize.numericReplayEvidence.replayProof,
    coverage.c3FiniteSize.numericReplayEvidence.parameterProof,
    coverage.c3FiniteSize.numericReplayEvidence.uncertaintyProof,
    coverage.c3FiniteSize.numericReplayEvidence.reproducibilityProof⟩

def Q073Q012FullPluralSourceBoundEvidencePackage.fullPublicSourceBoundBundleSafe
    (package : Q073Q012FullPluralSourceBoundEvidencePackage) : Prop :=
  package.coverage.sourceAndReplayBundlePublicSafe ∧
    package.c4SourceBound.sourceModelAndHypothesesReadBack = true ∧
    package.c4SourceBound.weakCLTExternalNotMechanized = true ∧
    package.c4SourceBound.portmanteauWeakLimitToPositiveLogLowerBoundBridgeMechanized =
      true ∧
    package.c4SourceBound.exactEventualEqualitySourceProved = false ∧
    package.c4SourceBound.exactMomentCoefficientSourceProved = false ∧
    package.c4SourceBound.physicalBilliardSimulationPresent = true ∧
    package.c5SourceBound.sourceReadbackSupportsWindTreeGenericNonordinaryExponent ∧
    package.c5SourceBound.sourceReadbackSupportsWindTreeNonGenericExponentVariety ∧
    package.c5SourceBound.sourceReadbackSupportsOpenPolygonalChannelAnomalousTransport ∧
    package.c5SourceBound.sourceReadbackSupportsPolygonalLockingRelation ∧
    package.c5SourceBound.sourceReadbackRejectsHyperbolicSurrogate ∧
    package.c5SourceBound.sourceReadbackRequiresGeometryObservableGates ∧
    package.noSingleUniformOrdinaryFiniteCoefficient

theorem q073_q012_full_source_bound_package_public_bundle_safe
    (package : Q073Q012FullPluralSourceBoundEvidencePackage) :
    package.fullPublicSourceBoundBundleSafe := by
  exact ⟨q073_q012_full_plural_transport_coverage_public_bundle_safe
      package.coverage,
    package.c4SourceBound.sourceModelAndHypothesesReadBackProof,
    package.c4SourceBound.weakCLTExternalNotMechanizedProof,
    package.c4SourceBound.portmanteauWeakLimitToPositiveLogLowerBoundBridgeMechanizedProof,
    package.c4SourceBound.exactEventualEqualityNotSourceProved,
    package.c4SourceBound.exactMomentCoefficientNotSourceProved,
    package.c4SourceBound.physicalBilliardSimulationPresentProof,
    package.c5SourceBound.windTreeGenericProof,
    package.c5SourceBound.windTreeNonGenericProof,
    package.c5SourceBound.openPolygonalChannelProof,
    package.c5SourceBound.polygonalLockingRelationProof,
    package.c5SourceBound.hyperbolicSurrogateRejectedProof,
    package.c5SourceBound.geometryObservableGateProof,
    q073_q012_source_bound_package_rejects_single_uniform_ordinary_coefficient
      package⟩

theorem q073_q012_full_plural_transport_coverage_yields_release_payloads
    (coverage : Q073Q012FullPluralTransportCoverage) :
    coverage.declaredVarietyCoveredOrBounded ∧
      coverage.noSingleSubclassSoldAsPluralTarget ∧
      coverage.sourceAndReplayBundlePublicSafe ∧
      (∃ c1 : Q073Q012TransportCoefficientPayload,
        c1.coefficientDefinitions ∧ c1.coefficientFormulaOrAlgorithm ∧
          c1.boundary.noOneSystemAsFullTarget) ∧
      (∃ c2 : Q073Q012TransportCoefficientPayload,
        c2.coefficientDefinitions ∧ c2.coefficientFormulaOrAlgorithm ∧
          c2.boundary.noOneSystemAsFullTarget) ∧
      (∃ c3 : Q073Q012TransportCoefficientPayload,
        c3.coefficientDefinitions ∧ c3.coefficientFormulaOrAlgorithm ∧
          c3.boundary.noOneSystemAsFullTarget) ∧
      (∃ c4 : Q073Q012NegativeOrLimitingPayload,
        c4.namedBilliardClass ∧
          c4.coefficientNonexistenceOrNoUniformScheme ∧
          c4.assumptionsNeededForDecidability) ∧
      (∃ c5 : Q073Q012NegativeOrLimitingPayload,
        c5.namedBilliardClass ∧
          c5.coefficientNonexistenceOrNoUniformScheme ∧
          c5.assumptionsNeededForDecidability) := by
  exact ⟨q073_q012_full_plural_transport_coverage_declares_variety coverage,
    q073_q012_full_plural_transport_coverage_prevents_single_subclass_claim coverage,
    q073_q012_full_plural_transport_coverage_public_bundle_safe coverage,
    q073_q012_c1_bridge_yields_internal_formula_payload
      coverage.c1Analytic.bridge,
    q073_q012_c2_bridge_yields_internal_formula_payload
      coverage.c2SourceUnit.bridge,
    q073_q012_c3_bridge_yields_internal_formula_payload
      coverage.c3FiniteSize,
    q073_q012_c4_bridge_yields_internal_limiting_payload
      coverage.c4InfiniteHorizonBoundary,
    q073_q012_c5_bridge_yields_internal_frontier_payload
      coverage.c5PolygonalFrontier⟩

def Q073Q012FullPluralSourceBoundEvidencePackage.c4ScopedPortmanteauBridgeClosedWithExactAsymptoticsUnclaimed
    (package : Q073Q012FullPluralSourceBoundEvidencePackage) : Prop :=
  package.c4SourceBound.weakCLTExternalNotMechanized = true ∧
    package.c4SourceBound.portmanteauWeakLimitToPositiveLogLowerBoundBridgeMechanized =
      true ∧
    package.c4SourceBound.exactEventualEqualitySourceProved = false ∧
    package.c4SourceBound.exactMomentCoefficientSourceProved = false

theorem
    q073_q012_full_source_bound_package_records_c4_scoped_portmanteau_bridge_closed_with_exact_asymptotics_unclaimed
    (package : Q073Q012FullPluralSourceBoundEvidencePackage) :
    package.c4ScopedPortmanteauBridgeClosedWithExactAsymptoticsUnclaimed := by
  exact ⟨package.c4SourceBound.weakCLTExternalNotMechanizedProof,
    package.c4SourceBound.portmanteauWeakLimitToPositiveLogLowerBoundBridgeMechanizedProof,
    package.c4SourceBound.exactEventualEqualityNotSourceProved,
    package.c4SourceBound.exactMomentCoefficientNotSourceProved⟩

end OCMinimalObligationSpine
