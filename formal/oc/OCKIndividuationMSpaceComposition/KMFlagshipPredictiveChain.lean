import OCKIndividuationMSpaceComposition.CompositePredictiveKernelCorrespondence
import OCKIndividuationMSpaceComposition.KMContextContinuationCoherence
import OCKIndividuationMSpaceComposition.SemanticPredictionContract

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe
  uLiftCarrier uLiftCandidate uRepairCandidate
  uObservation uOutcome uExecution uCausalContext

/-!
# K/M-generated flagship predictive chain

This module closes the domain-generic composition gap between OC's K/M
selection, forecast-origin information, typed continuation semantics and the
continuation-aware predictive kernel.  Mature set-valued prediction and
partial-identification results are reused; the new surface is the minimum OC
adapter that makes the admitted model class structural rather than arbitrary.

The adapter remains conditional on an inspectable domain observation filter,
endpoint projection and execution envelope.  Those are parameters to be
registered and tested by a domain adapter, not universal facts manufactured by
the metamodel.
-/

/-- A K/M candidate remains prediction-admissible only if it is tied at the
selected resolving rank and survives the information available at the
forecast origin. -/
def ObservedKMTiedCandidate
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (observationAdmits : liftSearch.Candidate → Prop)
    (candidate : liftSearch.Candidate) : Prop :=
  KMTiedResolvingCandidate resolution candidate ∧
    observationAdmits candidate

/-- The observation available at the forecast origin indexes the admissible
model class.  This prevents a later outcome or an untyped Boolean filter from
silently changing the information set. -/
structure PreOutcomeModelFilter (Model : Type uLiftCandidate) where
  ObservationState : Type uObservation
  originObservation : ObservationState
  admitsAt : ObservationState → Model → Prop

def PreOutcomeModelFilter.originAdmits
    {Model : Type uLiftCandidate}
    (filter : PreOutcomeModelFilter Model)
    (model : Model) : Prop :=
  filter.admitsAt filter.originObservation model

/-- Minimum domain contract turning an origin-qualified K/M model class into
a continuation-backed outcome map.  `forecastEndpointFuture` prevents an
adapter from assigning an outcome to a candidate with no admitted future in
its own typed context. -/
structure KMFlagshipPredictionAdapter
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch) where
  Outcome : Type uOutcome
  Execution : Type uExecution
  CausalContext : Type uCausalContext
  causalContextFintype : Fintype CausalContext
  forecastContract : OperationalSemanticForecastContract
  observationFilter : PreOutcomeModelFilter liftSearch.Candidate
  selectedObservationAdmitted :
    observationFilter.originAdmits resolution.selection.minimizer.1
  forecastEndpoint : liftSearch.Candidate → interpretation.State
  forecastEndpointFuture : ∀ candidate,
    ObservedKMTiedCandidate resolution observationFilter.originAdmits candidate →
      interpretation.predictiveInterpretation.targetFutureAt candidate
        (forecastEndpoint candidate)
  outcomeOfState : interpretation.State → Outcome
  targetContext :
    ContinuationContext interpretation.State interpretation.Input
      interpretation.Evidence interpretation.Task interpretation.Projection
      interpretation.Boundary interpretation.Constraint interpretation.Scope
      interpretation.Frame
  admissibleExecution : Execution → Prop
  executionOutcome : Execution → Outcome

/-- The adapter's deterministic candidate outcome is explicitly a projection
of a continuation-admitted endpoint. -/
def KMFlagshipPredictionAdapter.predictedOutcome
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation)
    (candidate : liftSearch.Candidate) : adapter.Outcome :=
  adapter.outcomeOfState (adapter.forecastEndpoint candidate)

/-- Canonical OC-generated flagship kernel. -/
def KMFlagshipPredictionAdapter.toKernel
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation) :
    ContinuationAwarePredictiveAdmissibilityKernel where
  State := interpretation.State
  Input := interpretation.Input
  Evidence := interpretation.Evidence
  Task := interpretation.Task
  Projection := interpretation.Projection
  Boundary := interpretation.Boundary
  Constraint := interpretation.Constraint
  Scope := interpretation.Scope
  Frame := interpretation.Frame
  Model := liftSearch.Candidate
  Outcome := adapter.Outcome
  Execution := adapter.Execution
  CausalContext := adapter.CausalContext
  causalContextFintype := adapter.causalContextFintype
  sourceContext := interpretation.contextOf resolution.selection.minimizer.1
  targetContext := adapter.targetContext
  admissibleModel :=
    ObservedKMTiedCandidate resolution adapter.observationFilter.originAdmits
  predictedOutcome := adapter.predictedOutcome
  modelExists := ⟨resolution.selection.minimizer.1,
    selected_is_km_tied_resolving resolution,
    adapter.selectedObservationAdmitted⟩
  admissibleExecution := adapter.admissibleExecution
  executionOutcome := adapter.executionOutcome

/-- The public kernel's model class is exactly the image of the typed
pre-outcome observation state intersected with the K/M-tied resolving class. -/
theorem km_flagship_admission_is_origin_observation_map
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation)
    (candidate : liftSearch.Candidate) :
    adapter.toKernel.admissibleModel candidate ↔
      KMTiedResolvingCandidate resolution candidate ∧
      adapter.observationFilter.admitsAt
        adapter.observationFilter.originObservation candidate := by
  rfl

/-- Exact positive bridge from K/M selection plus origin observation to the
kernel possible-future surface. -/
theorem km_flagship_possible_future_iff
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation)
    (outcome : adapter.Outcome) :
    KernelPossibleFuture adapter.toKernel outcome ↔
      ∃ candidate,
        ObservedKMTiedCandidate resolution adapter.observationFilter.originAdmits candidate ∧
        adapter.predictedOutcome candidate = outcome := by
  rfl

/-- Exact intersection semantics for necessary futures. -/
theorem km_flagship_necessary_future_iff
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation)
    (outcome : adapter.Outcome) :
    KernelNecessaryFuture adapter.toKernel outcome ↔
      ∀ candidate,
        ObservedKMTiedCandidate resolution adapter.observationFilter.originAdmits candidate →
        adapter.predictedOutcome candidate = outcome := by
  rfl

/-- Every admitted model's reported endpoint is a genuine bounded future in
that candidate's typed continuation context. -/
theorem km_flagship_endpoint_is_continuation_future
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation)
    (candidate : liftSearch.Candidate)
    (admitted : ObservedKMTiedCandidate resolution
      adapter.observationFilter.originAdmits candidate) :
    interpretation.predictiveInterpretation.targetFutureAt candidate
      (adapter.forecastEndpoint candidate) :=
  adapter.forecastEndpointFuture candidate admitted

/-- Operational origin discipline is inherited by every declared input. -/
theorem km_flagship_input_available_at_origin
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation)
    (item : ForecastInformationItem)
    (member : item ∈ adapter.forecastContract.inputs) :
    item.availableAt ≤ adapter.forecastContract.origin :=
  operational_contract_input_available adapter.forecastContract item member

/-- Ambiguity is exactly disagreement between two origin-admitted K/M
candidates. -/
theorem km_flagship_abstains_iff_tied_outcome_disagreement
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation) :
    KernelAbstains adapter.toKernel ↔
      ∃ first second,
        ObservedKMTiedCandidate resolution adapter.observationFilter.originAdmits first ∧
        ObservedKMTiedCandidate resolution adapter.observationFilter.originAdmits second ∧
        adapter.predictedOutcome first ≠ adapter.predictedOutcome second := by
  constructor
  · rintro ⟨firstOutcome, secondOutcome, firstPossible, secondPossible, distinct⟩
    rcases firstPossible with ⟨first, firstAdmitted, firstPredicted⟩
    rcases secondPossible with ⟨second, secondAdmitted, secondPredicted⟩
    refine ⟨first, second, firstAdmitted, secondAdmitted, ?_⟩
    intro same
    apply distinct
    exact firstPredicted.symm.trans (same.trans secondPredicted)
  · rintro ⟨first, second, firstAdmitted, secondAdmitted, distinct⟩
    exact ⟨adapter.predictedOutcome first, adapter.predictedOutcome second,
      admissible_model_outcome_is_possible adapter.toKernel first firstAdmitted,
      admissible_model_outcome_is_possible adapter.toKernel second secondAdmitted,
      distinct⟩

/-- Same-information sharpness: excluding any OC-generated possible outcome
makes a predictor unsound unless a new class-refining premise or observation
is supplied. -/
theorem no_same_information_predictor_can_exclude_km_flagship_future
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation)
    (predictor : adapter.Outcome → Prop) (outcome : adapter.Outcome)
    (possible : KernelPossibleFuture adapter.toKernel outcome)
    (excluded : ¬ predictor outcome) :
    ¬ KernelSoundPredictor adapter.toKernel predictor :=
  excluding_possible_future_is_unsound adapter.toKernel predictor outcome
    possible excluded

/-- Typed transport remains a separate conjunction: K/M admission and a
continuation endpoint do not silently manufacture cross-context transport. -/
theorem km_flagship_transport_iff_context_and_causal_components
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation) :
    KernelTransportAllowed adapter.toKernel ↔
      Nonempty (ContextCompatibility adapter.toKernel.sourceContext
        adapter.toKernel.targetContext) ∧
      KernelCausalTransportAvailable adapter.toKernel :=
  kernel_transport_allowed_iff_components adapter.toKernel

/-! ## Quantitative pre-outcome parameter contract -/

/-- Four separately auditable uncertainty contributions.  A domain adapter
must bind them before the realized outcome is inspected.  The intermediate
maps expose which term is responsible for a wide forecast rather than hiding
all error in one fitted scalar. -/
structure KMFlagshipQuantitativeParameterContract
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation)
    [PseudoMetricSpace adapter.Outcome] where
  referenceCandidate : liftSearch.Candidate
  referenceAdmitted : adapter.toKernel.admissibleModel referenceCandidate
  observationAdjusted : liftSearch.Candidate → adapter.Outcome
  transportedOutcome : liftSearch.Candidate → adapter.Outcome
  structuralRadius : ℝ
  observationRadius : ℝ
  transportRadius : ℝ
  executionRadius : ℝ
  structuralRadius_nonnegative : 0 ≤ structuralRadius
  observationRadius_nonnegative : 0 ≤ observationRadius
  transportRadius_nonnegative : 0 ≤ transportRadius
  executionRadius_nonnegative : 0 ≤ executionRadius
  structuralBound : ∀ candidate,
    adapter.toKernel.admissibleModel candidate →
      dist (adapter.predictedOutcome referenceCandidate)
        (adapter.predictedOutcome candidate) ≤ structuralRadius
  observationBound : ∀ candidate,
    adapter.toKernel.admissibleModel candidate →
      dist (adapter.predictedOutcome candidate)
        (observationAdjusted candidate) ≤ observationRadius
  transportBound : ∀ candidate,
    adapter.toKernel.admissibleModel candidate →
      dist (observationAdjusted candidate)
        (transportedOutcome candidate) ≤ transportRadius
  executionBound : ∀ candidate execution,
    adapter.toKernel.admissibleModel candidate →
    adapter.admissibleExecution execution →
      dist (transportedOutcome candidate)
        (adapter.executionOutcome execution) ≤ executionRadius

def KMFlagshipQuantitativeParameterContract.totalRadius
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    {adapter : KMFlagshipPredictionAdapter resolution interpretation}
    [PseudoMetricSpace adapter.Outcome]
    (contract : KMFlagshipQuantitativeParameterContract adapter) : ℝ :=
  contract.structuralRadius + contract.observationRadius +
    contract.transportRadius + contract.executionRadius

/-- Operational numerical prediction: every admitted execution lies in the
closed ball around the registered reference prediction with radius
`rho_KM + rho_obs + rho_transport + rho_execution`. -/
theorem km_flagship_total_radius_bound
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    {adapter : KMFlagshipPredictionAdapter resolution interpretation}
    [PseudoMetricSpace adapter.Outcome]
    (contract : KMFlagshipQuantitativeParameterContract adapter)
    (candidate : liftSearch.Candidate)
    (candidateAdmitted : adapter.toKernel.admissibleModel candidate)
    (execution : adapter.Execution)
    (executionAdmitted : adapter.admissibleExecution execution) :
    dist (adapter.predictedOutcome contract.referenceCandidate)
      (adapter.executionOutcome execution) ≤ contract.totalRadius := by
  have firstTriangle := dist_triangle
    (adapter.predictedOutcome contract.referenceCandidate)
    (adapter.predictedOutcome candidate)
    (adapter.executionOutcome execution)
  have secondTriangle := dist_triangle
    (adapter.predictedOutcome candidate)
    (contract.observationAdjusted candidate)
    (adapter.executionOutcome execution)
  have thirdTriangle := dist_triangle
    (contract.observationAdjusted candidate)
    (contract.transportedOutcome candidate)
    (adapter.executionOutcome execution)
  have structural := contract.structuralBound candidate candidateAdmitted
  have observation := contract.observationBound candidate candidateAdmitted
  have transport := contract.transportBound candidate candidateAdmitted
  have executionBound := contract.executionBound candidate execution
    candidateAdmitted executionAdmitted
  dsimp [KMFlagshipQuantitativeParameterContract.totalRadius]
  linarith

/-! ## Sharp removed-premise boundaries -/

def ObservationIndexedPossibleFuture
    {Observation Model Outcome : Type*}
    (admitsAt : Observation → Model → Prop)
    (predictedOutcome : Model → Outcome)
    (observation : Observation) (outcome : Outcome) : Prop :=
  ∃ model, admitsAt observation model ∧ predictedOutcome model = outcome

def binaryObservationAdmits (observation model : Bool) : Prop :=
  observation = false ∨ model = false

def binaryObservationOutcome (model : Bool) : Fin 2 :=
  if model then 1 else 0

/-- Removing the discriminating observation strictly enlarges the possible
set: outcome `1` becomes possible although the observed class excludes it. -/
theorem removing_observation_filter_strictly_enlarges_possible_set :
    ObservationIndexedPossibleFuture binaryObservationAdmits
      binaryObservationOutcome false 1 ∧
    ¬ ObservationIndexedPossibleFuture binaryObservationAdmits
      binaryObservationOutcome true 1 := by
  constructor
  · exact ⟨true, by simp [binaryObservationAdmits], by simp [binaryObservationOutcome]⟩
  · rintro ⟨model, admitted, predicted⟩
    cases model <;>
      simp [binaryObservationAdmits, binaryObservationOutcome] at admitted predicted

/-- Endpoint equality without a continuation witness accepts a false future
in the canonical axe model. -/
theorem removing_continuation_premise_admits_false_endpoint :
    axePhysicalProjection .a2 = axePhysicalProjection .b ∧
    Continues axeHistoricalContext .a0 .a2 ∧
    ¬ Continues axeHistoricalContext .a0 .b :=
  terminal_projection_does_not_determine_continuation

/-- A mature causal component alone does not authorize application after a
frame change. -/
theorem km_flagship_causal_component_alone_does_not_allow_transport
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation)
    (causalAvailable : KernelCausalTransportAvailable adapter.toKernel)
    (frameMismatch : adapter.toKernel.sourceContext.frame ≠
      adapter.toKernel.targetContext.frame) :
    KernelCausalTransportAvailable adapter.toKernel ∧
      ¬ KernelTransportAllowed adapter.toKernel :=
  causal_transport_without_frame_continuity_is_not_kernel_transport
    adapter.toKernel causalAvailable frameMismatch

/-! ## Mature-composite disposition -/

/-- At the common outer information contract the flagship is a conservative
adapter: possible, necessary, sound and robust statements coincide exactly. -/
theorem km_flagship_mature_composite_correspondence
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation) :
    (∀ outcome, CompositePossibleFuture adapter.toKernel.toMatureComposite outcome ↔
      KernelPossibleFuture adapter.toKernel outcome) ∧
    (∀ outcome, CompositeNecessaryFuture adapter.toKernel.toMatureComposite outcome ↔
      KernelNecessaryFuture adapter.toKernel outcome) ∧
    (∀ predictor, CompositeSoundPredictor adapter.toKernel.toMatureComposite predictor ↔
      KernelSoundPredictor adapter.toKernel predictor) ∧
    (∀ outcome, CompositeRobustOutcome adapter.toKernel.toMatureComposite outcome ↔
      KernelRobustOutcome adapter.toKernel outcome) ∧
    (adapter.toKernel.toMatureComposite.transportAllowed ↔
      Nonempty (ContextCompatibility adapter.toKernel.sourceContext
        adapter.toKernel.targetContext) ∧
      KernelCausalTransportAvailable adapter.toKernel) :=
  continuation_aware_kernel_mature_composite_correspondence adapter.toKernel

/-- No strict outer predictive gain can be claimed against the exact mature
composite; strict gain requires a demonstrably different admission or outcome
contract. -/
theorem km_flagship_has_no_strict_gain_over_exact_mature_composite
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    (adapter : KMFlagshipPredictionAdapter resolution interpretation) :
    ¬ ∃ outcome, KernelPossibleFuture adapter.toKernel outcome ∧
      ¬ CompositePossibleFuture adapter.toKernel.toMatureComposite outcome :=
  no_strict_possible_future_gain_over_exact_mature_composite adapter.toKernel

/-! ## Concrete finite nonvacuity witness -/

def finiteFlagshipContext :
    ContinuationContext Unit Unit Unit Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := fun source _ target => source = target
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun _ => True
  transitionPreservesInvariant := by
    intro current next input currentInvariant edge
    trivial

/-- Two admissible finite models produce two of three possible outcome values.
The resulting forecast is informative but must abstain from a point. -/
abbrev finiteNontrivialFlagshipKernel :
    ContinuationAwarePredictiveAdmissibilityKernel where
  State := Unit
  Input := Unit
  Evidence := Unit
  Task := Unit
  Projection := Unit
  Boundary := Unit
  Constraint := Unit
  Scope := Unit
  Frame := Unit
  Model := Bool
  Outcome := Fin 3
  Execution := Bool
  CausalContext := Unit
  causalContextFintype := inferInstance
  sourceContext := finiteFlagshipContext
  targetContext := finiteFlagshipContext
  admissibleModel := fun _ => True
  predictedOutcome := fun model => if model then 1 else 0
  modelExists := ⟨false, trivial⟩
  admissibleExecution := fun _ => True
  executionOutcome := fun model => if model then 1 else 0

theorem finite_flagship_zero_possible :
    KernelPossibleFuture finiteNontrivialFlagshipKernel 0 := by
  exact ⟨false, trivial, by decide⟩

theorem finite_flagship_one_possible :
    KernelPossibleFuture finiteNontrivialFlagshipKernel 1 := by
  exact ⟨true, trivial, by decide⟩

theorem finite_flagship_two_impossible :
    ¬ KernelPossibleFuture finiteNontrivialFlagshipKernel 2 := by
  rintro ⟨model, admitted, predicted⟩
  cases model <;> contradiction

theorem finite_flagship_is_informative_and_abstains :
    KernelPossibleFuture finiteNontrivialFlagshipKernel 0 ∧
    KernelPossibleFuture finiteNontrivialFlagshipKernel 1 ∧
    ¬ KernelPossibleFuture finiteNontrivialFlagshipKernel 2 ∧
    KernelAbstains finiteNontrivialFlagshipKernel := by
  refine ⟨finite_flagship_zero_possible, finite_flagship_one_possible,
    finite_flagship_two_impossible, ?_⟩
  exact ⟨0, 1, finite_flagship_zero_possible, finite_flagship_one_possible,
    by decide⟩

end OCKIndividuationMSpaceComposition
