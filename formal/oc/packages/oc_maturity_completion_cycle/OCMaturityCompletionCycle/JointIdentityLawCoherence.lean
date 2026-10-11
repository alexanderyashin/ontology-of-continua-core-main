import OCMaturityCompletionCycle.JointPathTransport

/-!
# Identity/process and joint-law coherence gates

Persistent identity is linked to a witnessed positive-mass joint process trace;
it is not inferred from a stable string identifier.  Candidate state/output
path laws are separately required to equal the law induced by the primitive
joint kernel and policy.
-/

namespace OCMaturityCompletionCycle

universe uOccurrence uState uContext uBoundaryIn uAction uBoundaryOut
  uAbstractState uAbstractContext uAbstractBoundaryIn uAbstractAction
  uAbstractBoundaryOut

/-- Exact realization of a candidate normalized joint path law. -/
def JointLawRealization
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (experiment :
      FiniteJointOpenExperiment State Context BoundaryIn Action BoundaryOut)
    (candidate : FiniteProbabilityMass
      (FiniteStateOutputPath State BoundaryOut experiment.horizon)) : Prop :=
  candidate.mass = (inducedFiniteStateOutputPathLaw experiment).mass

/-- Raw occurrence-to-trace presentation before compatibility is checked. -/
structure IdentityProcessCandidate
    {Occurrence : Type uOccurrence}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (identity : IdentityPresentation Occurrence State)
    (experiment :
      FiniteJointOpenExperiment State Context BoundaryIn Action BoundaryOut) where
  witnessedPath : FiniteStateOutputPath State BoundaryOut experiment.horizon
  occurrenceTime : Occurrence → Nat
  occurrenceOutput : Occurrence → Option BoundaryOut
  occurrenceHistory : Occurrence → List State

/-- Undirected continuation connectivity, permitting branching and fusion. -/
def ContinuationZigzag
    {Occurrence : Type uOccurrence}
    {State : Type uState}
    (identity : IdentityPresentation Occurrence State) :
    Occurrence → Occurrence → Prop :=
  Relation.ReflTransGen fun left right =>
    identity.continuationEvidence left right ∨
      identity.continuationEvidence right left

/--
Compatibility requires a positive-mass trace, exact state/output/history
positions, monotone continuation, and lineage support for every assembly edge.
-/
def IdentityProcessCompatibility
    {Occurrence : Type uOccurrence}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    {identity : IdentityPresentation Occurrence State}
    {experiment :
      FiniteJointOpenExperiment State Context BoundaryIn Action BoundaryOut}
    (candidate : IdentityProcessCandidate identity experiment) : Prop :=
  0 < (inducedFiniteStateOutputPathLaw experiment).mass candidate.witnessedPath ∧
  (∀ occurrence,
    (finiteStateOutputPathStates experiment.horizon candidate.witnessedPath
        )[candidate.occurrenceTime occurrence]? =
      some (identity.stateOf occurrence)) ∧
  (∀ occurrence,
    candidate.occurrenceOutput occurrence =
      if candidate.occurrenceTime occurrence = 0 then none
      else
        (finiteStateOutputPathOutputs experiment.horizon candidate.witnessedPath
          )[candidate.occurrenceTime occurrence - 1]?) ∧
  (∀ occurrence,
    candidate.occurrenceHistory occurrence =
      (finiteStateOutputPathStates experiment.horizon candidate.witnessedPath).take
        (candidate.occurrenceTime occurrence + 1)) ∧
  (∀ ⦃left right⦄,
    identity.continuationEvidence left right →
      candidate.occurrenceTime left ≤ candidate.occurrenceTime right) ∧
  (∀ ⦃left right⦄,
    identity.assembledTogether left right →
      ContinuationZigzag identity left right)

/--
A checked single-trace relation bridge from identity assertions to one induced
joint process path.  It proves neither a functional Occurrence-to-Object map nor
quotient uniqueness.  Branching/fusion require a separate path-family bridge.
-/
structure IdentityProcessBridge
    {Occurrence : Type uOccurrence}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (identity : IdentityPresentation Occurrence State)
    (experiment :
      FiniteJointOpenExperiment State Context BoundaryIn Action BoundaryOut) where
  candidate : IdentityProcessCandidate identity experiment
  compatible : IdentityProcessCompatibility candidate

/-- The bridge currently proves relation compatibility on one process trace only. -/
inductive IdentityProcessBridgeScope where
  | singleTraceRelationCompatibility
  deriving DecidableEq, Repr

/-- Exact scientific scope; no quotient/object functionality is inferred. -/
def IdentityProcessBridge.scope
    {Occurrence : Type uOccurrence}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    {identity : IdentityPresentation Occurrence State}
    {experiment :
      FiniteJointOpenExperiment State Context BoundaryIn Action BoundaryOut}
    (_ : IdentityProcessBridge identity experiment) : IdentityProcessBridgeScope :=
  .singleTraceRelationCompatibility

/--
The process-realized identity relation must also be respected by the abstraction
state used by the predictive law.  This is the missing typed bridge between
identity/process evidence and abstraction semantics.
-/
def JointIdentityAbstractionCompatibility
    {Occurrence : Type uOccurrence}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    {identity : IdentityPresentation Occurrence State}
    {data : AlignedJointOpenExperiments abstraction}
    (bridge : IdentityProcessBridge identity data.fineExperiment) : Prop :=
  ∀ ⦃left right⦄,
    identity.assembledTogether left right →
      abstraction.stateMap (identity.stateOf left) =
        abstraction.stateMap (identity.stateOf right)

/--
All gates required before calling one joint abstraction coherent.  The fields
are actual process/identity/law predicates, not arbitrary Boolean labels.
-/
structure CoherentJointOpenExactness
    {Occurrence : Type uOccurrence}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (identity : IdentityPresentation Occurrence State)
    (data : AlignedJointOpenExperiments abstraction)
    (candidate : FiniteProbabilityMass
      (FiniteStateOutputPath AbstractState AbstractBoundaryOut data.horizon)) where
  transportAlignment : JointExperimentTransportAlignment data
  kernelCommutes : JointOpenKernelCommutes abstraction
  identityBridge : IdentityProcessBridge identity data.fineExperiment
  identityAbstractionCompatible :
    JointIdentityAbstractionCompatibility identityBridge
  lawRealization : JointLawRealization data.abstractExperiment candidate

/-- Coherence yields both exact candidate transport and a checked identity bridge. -/
theorem coherentJointOpenExactness_yields_pathLaw_and_identityCompatibility
    {Occurrence : Type uOccurrence}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (identity : IdentityPresentation Occurrence State)
    (data : AlignedJointOpenExperiments abstraction)
    (candidate : FiniteProbabilityMass
      (FiniteStateOutputPath AbstractState AbstractBoundaryOut data.horizon))
    (coherence : CoherentJointOpenExactness identity data candidate) :
    (transportedFineJointPathLaw data).mass = candidate.mass ∧
      IdentityProcessCompatibility coherence.identityBridge.candidate ∧
      JointIdentityAbstractionCompatibility coherence.identityBridge := by
  constructor
  · have pathExact :=
      jointOpenKernelCommutes_and_alignment_imply_pathLawExact data
        coherence.transportAlignment coherence.kernelCommutes
    exact pathExact.trans coherence.lawRealization.symm
  · exact ⟨coherence.identityBridge.compatible,
      coherence.identityAbstractionCompatible⟩

/-- Exact structural unpacking of the five typed coherence prerequisites. -/
theorem coherentJointOpenExactness_iff_all_typed_gates
    {Occurrence : Type uOccurrence}
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundaryIn : Type uAbstractBoundaryIn}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (identity : IdentityPresentation Occurrence State)
    (data : AlignedJointOpenExperiments abstraction)
    (candidate : FiniteProbabilityMass
      (FiniteStateOutputPath AbstractState AbstractBoundaryOut data.horizon)) :
    Nonempty (CoherentJointOpenExactness identity data candidate) ↔
      ∃ alignment : JointExperimentTransportAlignment data,
      ∃ bridge : IdentityProcessBridge identity data.fineExperiment,
        JointOpenKernelCommutes abstraction ∧
        JointIdentityAbstractionCompatibility bridge ∧
        JointLawRealization data.abstractExperiment candidate := by
  constructor
  · rintro ⟨coherence⟩
    exact ⟨coherence.transportAlignment, coherence.identityBridge,
      coherence.kernelCommutes, coherence.identityAbstractionCompatible,
      coherence.lawRealization⟩
  · rintro ⟨alignment, bridge, kernelCommutes, identityCompatible,
      lawRealization⟩
    exact ⟨{
      transportAlignment := alignment
      kernelCommutes := kernelCommutes
      identityBridge := bridge
      identityAbstractionCompatible := identityCompatible
      lawRealization := lawRealization
    }⟩

end OCMaturityCompletionCycle
