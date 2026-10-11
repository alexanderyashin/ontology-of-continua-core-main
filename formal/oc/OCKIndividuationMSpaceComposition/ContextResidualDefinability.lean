import OCKIndividuationMSpaceComposition.TypedCausalContinuationTransport
import OCKIndividuationMSpaceComposition.StrongestUniversalization
import OCKIndividuationMSpaceComposition.UnknownSupportInformationBounds

namespace OCKIndividuationMSpaceComposition

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame
  uObserved uCausalContext uVisible uHidden

/-!
# Constructive definability of the context-compatibility residual

The outer predictive correspondence leaves `ContextCompatibility` as a
residual.  This module does not encode that residual as a supplied Boolean.
Instead it gives the strongest constructive decomposition currently justified:

1. an observation channel must exactly recover the task-relative context
   signature;
2. a provenance/reachability adapter must transport every admitted evidenced
   edge;
3. a robust-envelope adapter must transport the initial invariant;
4. the mature causal transport contract remains a separate component.

The positive result recursively constructs transport of the complete ordered
history.  The negative results identify two independent obstructions:
observational aliasing of a context coordinate, and failure of stepwise path
transport even when all five context labels agree.
-/

/-- The task-relative label surface explicitly required by
`ContextCompatibility`.  Constraint predicates and transition semantics are
not silently identified with these labels; they are handled by path transport. -/
structure ContextLabelSignature
    (Task : Type uTask)
    (Projection : Type uProjection)
    (Boundary : Type uBoundary)
    (Scope : Type uScope)
    (Frame : Type uFrame) where
  task : Task
  projection : Projection
  boundary : Boundary
  scope : Scope
  frame : Frame

/-- Extract exactly the five equality fields of `ContextCompatibility`. -/
def contextLabelSignature
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (context :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame) :
    ContextLabelSignature Task Projection Boundary Scope Frame where
  task := context.task
  projection := context.projection
  boundary := context.boundary
  scope := context.scope
  frame := context.frame

/-- A declared observation channel with an exact left inverse.  Exactness is
an auditable premise, not a conclusion inferred from the name of an ID. -/
structure ExactObservationChannel (Latent : Type*) (Observed : Type*) where
  observe : Latent → Observed
  recover : Observed → Latent
  recovers : Function.LeftInverse recover observe

/-- Equal exact readbacks identify the latent value. -/
theorem ExactObservationChannel.eq_of_observation_eq
    {Latent Observed : Type*}
    (channel : ExactObservationChannel Latent Observed)
    {left right : Latent}
    (same : channel.observe left = channel.observe right) :
    left = right := by
  rw [← channel.recovers left, ← channel.recovers right, same]

/-- Exact recovery is possible only through an injective observation map. -/
theorem ExactObservationChannel.observe_injective
    {Latent Observed : Type*}
    (channel : ExactObservationChannel Latent Observed) :
    Function.Injective channel.observe := by
  intro left right same
  exact channel.eq_of_observation_eq same

/-- PROV-style lineage and reachability evidence must be strong enough to map
each admitted source edge, with its evidence, to an admitted target edge. -/
structure ProvenanceReachabilityAdapter
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame) where
  transportStep : ∀ {current next : State} (input : Input) (evidence : Evidence),
    source.transition current input next →
    source.edgeAdmissible current input next evidence →
    source.evidenceSufficient evidence →
      target.transition current input next ∧
      target.edgeAdmissible current input next evidence ∧
      target.evidenceSufficient evidence

/-- Robust-control/invariance component, kept separate from provenance. -/
structure RobustInvariantAdapter
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame) where
  transportInvariant : ∀ state, source.invariant state → target.invariant state

namespace ProvenanceReachabilityAdapter

/-- Stepwise evidence transport recursively constructs a target history and
aligned evidence.  This is the constructive reachability theorem missing from
an endpoint-only or supplied-flag formulation. -/
noncomputable def transportHistoryEvidence
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    (adapter : ProvenanceReachabilityAdapter source target)
    {initial endpoint : State}
    {history : OpenHistory source.transition initial endpoint}
    (historyEvidence : HistoryEvidence source history) :
    Σ targetHistory : OpenHistory target.transition initial endpoint,
      HistoryEvidence target targetHistory := by
  induction historyEvidence with
  | start => exact ⟨.start, .start⟩
  | @extend current next previous previousEvidence input edge evidence
      admissible sufficient inductionHypothesis =>
      rcases inductionHypothesis with ⟨targetPrevious, targetPreviousEvidence⟩
      rcases adapter.transportStep input evidence edge admissible sufficient with
        ⟨targetEdge, targetAdmissible, targetSufficient⟩
      exact ⟨.extend targetPrevious input targetEdge,
        .extend targetPreviousEvidence input targetEdge evidence
          targetAdmissible targetSufficient⟩

end ProvenanceReachabilityAdapter

/-- Local mature components construct transport of a complete continuation
witness; no global compatibility witness is assumed. -/
noncomputable def constructContinuationWitnessTransport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    (provenance : ProvenanceReachabilityAdapter source target)
    (robust : RobustInvariantAdapter source target)
    {initial endpoint : State}
    (witness : ContinuationWitness source initial endpoint) :
    ContinuationWitness target initial endpoint := by
  rcases provenance.transportHistoryEvidence witness.evidence with
    ⟨targetHistory, targetEvidence⟩
  exact ⟨targetHistory, targetEvidence,
    robust.transportInvariant initial witness.initialInvariant⟩

/-- Strongest constructive mature composite used by the v93 boundary test.
The fields expose observations, local path transport, invariance and causal
transport independently; none is a precomputed `ContextCompatibility` flag. -/
structure ConstructiveMatureContextComposite
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (Observed : Type uObserved)
    (CausalContext : Type uCausalContext) [Fintype CausalContext] where
  labels : ExactObservationChannel
    (ContextLabelSignature Task Projection Boundary Scope Frame) Observed
  sameLabelObservation :
    labels.observe (contextLabelSignature source) =
      labels.observe (contextLabelSignature target)
  provenance : ProvenanceReachabilityAdapter source target
  robust : RobustInvariantAdapter source target
  causal : StaticEffectTransportContract CausalContext

/-- Positive reconstruction: a separating observation channel plus local
path/invariant adapters derives the full OC context compatibility contract. -/
noncomputable def ConstructiveMatureContextComposite.toContextCompatibility
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {Observed : Type uObserved}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    (composite : ConstructiveMatureContextComposite source target Observed CausalContext) :
    ContextCompatibility source target := by
  have signatureEquality :
      contextLabelSignature source = contextLabelSignature target :=
    composite.labels.eq_of_observation_eq composite.sameLabelObservation
  exact {
    taskCompatible := congrArg ContextLabelSignature.task signatureEquality
    projectionCompatible := congrArg ContextLabelSignature.projection signatureEquality
    boundaryCompatible := congrArg ContextLabelSignature.boundary signatureEquality
    scopeCompatible := congrArg ContextLabelSignature.scope signatureEquality
    frameCompatible := congrArg ContextLabelSignature.frame signatureEquality
    transport := fun _initial _endpoint witness =>
      constructContinuationWitnessTransport composite.provenance composite.robust witness
  }

/-- The constructive mature composite and a standard causal contract derive
the typed exact OC transport certificate. -/
noncomputable def ConstructiveMatureContextComposite.toTypedExactCausalTransport
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {Observed : Type uObserved}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    (composite : ConstructiveMatureContextComposite source target Observed CausalContext) :
    TypedExactCausalContinuationTransport source target CausalContext where
  continuation := composite.toContextCompatibility
  causal := composite.causal

/-- Operational consequence: every source continuation and transported causal
effect is valid in the target when the constructive composite is inhabited. -/
theorem constructive_composite_certifies_target_continuation_and_effect
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {Observed : Type uObserved}
    {CausalContext : Type uCausalContext} [Fintype CausalContext]
    (composite : ConstructiveMatureContextComposite source target Observed CausalContext)
    {initial endpoint : State}
    (sourceWitness : ContinuationWitness source initial endpoint) :
    Continues target initial endpoint ∧
      reweightedSourceEffect composite.causal.sourceWeight
          composite.causal.targetWeight composite.causal.sourceEffect =
        domainAverageEffect composite.causal.targetWeight
          composite.causal.targetEffect :=
  typed_exact_transport_certifies_continuation_and_effect
    composite.toTypedExactCausalTransport sourceWitness

/-! ## Sharp residual obstructions -/

/-- Omitting any nontrivial context coordinate produces a collision under the
canonical product projection and therefore forbids exact recovery.  `Hidden`
may instantiate task, projection, boundary, scope, frame, or an additional
semantic coordinate required by an adapter. -/
theorem omitted_context_coordinate_blocks_exact_recovery
    {Visible : Type uVisible} {Hidden : Type uHidden}
    (visible : Visible) {first second : Hidden}
    (different : first ≠ second) :
    ¬ ∃ recover : Visible → Visible × Hidden,
      Function.LeftInverse recover Prod.fst := by
  have pairDifferent : (visible, first) ≠ (visible, second) := by
    intro samePair
    exact different (congrArg Prod.snd samePair)
  exact projection_collision_no_leftInverse pairDifferent
    (show (visible, first).1 = (visible, second).1 from rfl)

/-- A collision in any proposed composite observation rules out an exact
context-signature decoder. -/
theorem context_observation_collision_blocks_exact_recovery
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Scope : Type uScope} {Frame : Type uFrame}
    {Observed : Type uObserved}
    (observe : ContextLabelSignature Task Projection Boundary Scope Frame → Observed)
    {left right : ContextLabelSignature Task Projection Boundary Scope Frame}
    (different : left ≠ right)
    (collision : observe left = observe right) :
    ¬ ∃ recover : Observed →
        ContextLabelSignature Task Projection Boundary Scope Frame,
      Function.LeftInverse recover observe :=
  projection_collision_no_leftInverse different collision

/-- Even perfect recovery of all five labels is insufficient when an admitted
source path cannot be transported to the target.  The remaining premise is
therefore genuinely step-semantic, not another identifier. -/
theorem equal_labels_without_path_adapter_do_not_imply_compatibility
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    (_equalLabels : contextLabelSignature source = contextLabelSignature target)
    {initial endpoint : State}
    (sourceWitness : Continues source initial endpoint)
    (targetObstruction : ¬ Continues target initial endpoint) :
    ¬ Nonempty (ContextCompatibility source target) := by
  intro compatibility
  rcases compatibility with ⟨compatibility⟩
  exact no_context_compatibility_of_counterexample sourceWitness targetObstruction
    compatibility

/-! ## Quantitative residual-information requirement -/

/-- If one observation fiber contains `residualSignatures` viable context
signatures and a registered observation contributes at most `capacity` nats,
Fano's bound gives the required observation count for error `error`. -/
theorem context_residual_fano_observation_lower_bound
    {residualSignatures observations : ℕ}
    (certificate : FanoChannelCertificate residualSignatures observations)
    (positiveCapacity : 0 < certificate.perObservationCapacity) :
    fanoRequiredInformation residualSignatures certificate.error /
        certificate.perObservationCapacity ≤ observations :=
  fano_observations_lower_bound certificate positiveCapacity

/-- Below the residual Fano floor, no total-information assignment can satisfy
both the discrimination requirement and the channel-capacity contract. -/
theorem below_context_residual_information_floor_no_go
    {residualSignatures observations : ℕ}
    (error capacity : ℝ)
    (positiveCapacity : 0 < capacity)
    (tooFew : (observations : ℝ) <
      fanoRequiredInformation residualSignatures error / capacity) :
    ¬ ∃ totalInformation : ℝ,
        fanoRequiredInformation residualSignatures error ≤ totalInformation ∧
        totalInformation ≤ (observations : ℝ) * capacity :=
  below_fano_capacity_floor_no_go error capacity positiveCapacity tooFew

end OCKIndividuationMSpaceComposition
