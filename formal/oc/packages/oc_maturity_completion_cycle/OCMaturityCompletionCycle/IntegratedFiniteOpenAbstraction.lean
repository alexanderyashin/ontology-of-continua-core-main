import OCMaturityCompletionCycle.JointOpenHistoryDefect

/-!
# Integrated finite open abstraction certificate

This module deliberately stays at the finite rational, frozen-history-support
scope.  It combines the evidence/identity gate, the operational history encoder,
the primitive joint process, context transport, and induced path law in one typed
certificate.  It is an N1-style characterization, not a novelty claim.
-/

namespace OCMaturityCompletionCycle

universe uOccurrence uHistory uObservation uState uContext uBoundaryIn uAction
  uBoundaryOut uAbstractState uAbstractContext uAbstractBoundaryIn
  uAbstractAction uAbstractBoundaryOut

/--
Exact evidence binding between the selected identity trace and the frozen
history family.  Every occurrence is assigned to a declared history whose
realized state trace is exactly that occurrence's witnessed prefix.  The
selected state/output trace is also the exact history-realization trace, so a
different positive branch of the same experiment cannot satisfy this gate.
-/
structure IdentityHistoryEvidenceBinding
    {Occurrence : Type uOccurrence}
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
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
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut)
    (identity : IdentityPresentation Occurrence State)
    (index : HistoryIndex)
    (bridge : IdentityProcessBridge identity
      (study.pathExperiment index).fineExperiment) where
  occurrenceIndex : Occurrence → HistoryIndex
  selected_state_trace_exact :
    finiteStateOutputPathStates
        (study.pathExperiment index).fineExperiment.horizon
        bridge.candidate.witnessedPath =
      finiteStateOutputPathStates
        (study.historyRealization.experiment index).horizon
        (study.historyRealization.witnessedPath index)
  selected_output_trace_exact :
    finiteStateOutputPathOutputs
        (study.pathExperiment index).fineExperiment.horizon
        bridge.candidate.witnessedPath =
      finiteStateOutputPathOutputs
        (study.historyRealization.experiment index).horizon
        (study.historyRealization.witnessedPath index)
  occurrence_state_trace_exact : ∀ occurrence,
    finiteStateOutputPathStates
        (study.historyRealization.experiment (occurrenceIndex occurrence)).horizon
        (study.historyRealization.witnessedPath (occurrenceIndex occurrence)) =
      bridge.candidate.occurrenceHistory occurrence
  occurrence_observations_exact : ∀ occurrence,
    study.historyProcess.support.observations (occurrenceIndex occurrence) =
      List.map study.historyAbstraction.observeState
        (bridge.candidate.occurrenceHistory occurrence)
  occurrence_controls_exact : ∀ occurrence,
    study.historyProcess.support.controls (occurrenceIndex occurrence) =
      (study.historyProcess.support.controls index).take
        (bridge.candidate.occurrenceTime occurrence)

/--
Every bound process-realized occurrence must be represented by the same
abstract state whether it is reached through the identity presentation or
through qχ on its exact frozen observation/control history.
-/
def IdentityHistoryEncoderCompatibility
    {Occurrence : Type uOccurrence}
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
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
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut)
    (identity : IdentityPresentation Occurrence State)
    (index : HistoryIndex)
    (bridge : IdentityProcessBridge identity
      (study.pathExperiment index).fineExperiment)
    (binding : IdentityHistoryEvidenceBinding study identity index bridge) : Prop :=
  ∀ occurrence,
    operationalHistoryAbstractState study.historyAbstraction study.historyProcess
        (binding.occurrenceIndex occurrence) =
      study.abstraction.stateMap (identity.stateOf occurrence)

/--
One finite certificate in which all defect coordinates, identity/process
compatibility, history encoding, and candidate-law realization refer to the same
plant, abstraction, frozen history family, and selected experiment.
-/
structure IntegratedFiniteOpenAbstractionCertificate
    {Occurrence : Type uOccurrence}
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
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
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractBoundaryOut]
    [DecidableEq AbstractContext]
    [DecidableEq AbstractBoundaryIn]
    [DecidableEq AbstractAction]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut)
    (identity : IdentityPresentation Occurrence State)
    (index : HistoryIndex)
    (candidate : FiniteProbabilityMass
      (FiniteStateOutputPath AbstractState AbstractBoundaryOut
        (study.pathExperiment index).horizon)) where
  zeroDefects : (jointOpenHistoryDefect study).ZeroScientificComponents
  coherence : CoherentJointOpenExactness identity (study.pathExperiment index)
    candidate
  identityHistoryBinding :
    IdentityHistoryEvidenceBinding study identity index coherence.identityBridge
  identityHistoryCompatible :
    IdentityHistoryEncoderCompatibility study identity index coherence.identityBridge
      identityHistoryBinding

/-- Exact finite consequences of the integrated certificate, with no independence claim. -/
theorem integratedFiniteOpenAbstractionCertificate_yields_exact_scope
    {Occurrence : Type uOccurrence}
    {HistoryIndex : Type uHistory}
    {Observation : Type uObservation}
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
    [Fintype HistoryIndex]
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractBoundaryOut]
    [DecidableEq AbstractContext]
    [DecidableEq AbstractBoundaryIn]
    [DecidableEq AbstractAction]
    (study : JointOpenHistoryStudy HistoryIndex Observation State Context
      BoundaryIn Action BoundaryOut AbstractState AbstractContext
      AbstractBoundaryIn AbstractAction AbstractBoundaryOut)
    (identity : IdentityPresentation Occurrence State)
    (index : HistoryIndex)
    (candidate : FiniteProbabilityMass
      (FiniteStateOutputPath AbstractState AbstractBoundaryOut
        (study.pathExperiment index).horizon))
    (certificate : IntegratedFiniteOpenAbstractionCertificate study identity index
      candidate) :
    FiniteLawFamilyExact
        (transportedFineHistoryStateLaw study.abstraction study.historyProcess)
        (abstractHistoryStateLaw study.abstraction study.historyAbstraction
          study.historyProcess) ∧
      HistoryEncoderKernelConsistent study.historyAbstraction study.historyProcess ∧
      FiniteLawFamilyExact
        (transportedFineHistoryBoundaryLaw study.abstraction study.historyProcess)
        (abstractHistoryBoundaryLaw study.abstraction study.historyAbstraction
          study.historyProcess) ∧
      HistoryContextNatural study ∧
      (∀ historyIndex,
        (transportedFineJointPathLaw (study.pathExperiment historyIndex)).mass =
          (inducedFiniteStateOutputPathLaw
            (study.pathExperiment historyIndex).abstractExperiment).mass) ∧
      (transportedFineJointPathLaw (study.pathExperiment index)).mass =
        candidate.mass ∧
      IdentityProcessCompatibility certificate.coherence.identityBridge.candidate ∧
      JointIdentityAbstractionCompatibility certificate.coherence.identityBridge ∧
      IdentityHistoryEncoderCompatibility study identity index
        certificate.coherence.identityBridge
        certificate.identityHistoryBinding := by
  rcases (jointOpenHistoryDefect_zero_iff_all_exact study).1
      certificate.zeroDefects with
    ⟨predictionExact, lumpabilityExact, boundaryExact, contextExact,
      stitchingExact⟩
  rcases coherentJointOpenExactness_yields_pathLaw_and_identityCompatibility
      identity (study.pathExperiment index) candidate certificate.coherence with
    ⟨candidateExact, processCompatible, identityAbstractCompatible⟩
  exact ⟨predictionExact, lumpabilityExact, boundaryExact, contextExact,
    stitchingExact, candidateExact, processCompatible, identityAbstractCompatible,
    certificate.identityHistoryCompatible⟩

end OCMaturityCompletionCycle
