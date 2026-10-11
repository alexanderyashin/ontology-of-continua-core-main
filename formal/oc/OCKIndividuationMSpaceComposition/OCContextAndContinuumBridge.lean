import OCKIndividuationMSpaceComposition.PathDependentContinuation

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame

/-!
# OC context derivation and Continuum boundary

An open transition law supplies the M-space of possible finite histories.  It
does not, by itself, select a task, frame, projection, evidence policy or
identity invariant.  Those additional choices are exposed as an adapter.  The
negative fixtures below show why a context cannot be uniquely reconstructed
from bare reachability.
-/

/-- Explicit non-mystical adapter from an OC open-dynamics surface to the
continuation context.  The transition law is reused, not copied or hidden. -/
structure OCContinuationAdapter
    (State : Type uState)
    (Input : Type uInput)
    (Evidence : Type uEvidence)
    (Task : Type uTask)
    (Projection : Type uProjection)
    (Boundary : Type uBoundary)
    (Constraint : Type uConstraint)
    (Scope : Type uScope)
    (Frame : Type uFrame)
    (openStep : State → Input → State → Prop) where
  task : Task
  projection : Projection
  boundary : Boundary
  activeConstraint : Constraint → Prop
  scope : Scope
  frame : Frame
  edgeAdmissible : State → Input → State → Evidence → Prop
  evidenceSufficient : Evidence → Prop
  invariant : State → Prop
  openStepPreservesInvariant :
    OpenHistory.PreservesInvariant openStep invariant

def OCContinuationAdapter.toContext
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {openStep : State → Input → State → Prop}
    (adapter : OCContinuationAdapter State Input Evidence Task Projection
      Boundary Constraint Scope Frame openStep) :
    ContinuationContext State Input Evidence Task Projection Boundary
      Constraint Scope Frame where
  task := adapter.task
  projection := adapter.projection
  boundary := adapter.boundary
  activeConstraint := adapter.activeConstraint
  scope := adapter.scope
  frame := adapter.frame
  transition := openStep
  edgeAdmissible := adapter.edgeAdmissible
  evidenceSufficient := adapter.evidenceSufficient
  invariant := adapter.invariant
  transitionPreservesInvariant := adapter.openStepPreservesInvariant

theorem OCContinuationAdapter.toContext_reuses_openStep
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {openStep : State → Input → State → Prop}
    (adapter : OCContinuationAdapter State Input Evidence Task Projection
      Boundary Constraint Scope Frame openStep) :
    adapter.toContext.transition = openStep := rfl

/-- Every continuation witness is literally an element of the derived M-space
after evidence and context are forgotten. -/
def ContinuationWitness.toDerivedMSpace
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary
      Constraint Scope Frame}
    {initial endpoint : State}
    (witness : ContinuationWitness C initial endpoint) :
    DerivedMSpace C.transition initial :=
  ⟨endpoint, witness.history⟩

inductive BridgeState
  | initial
  | terminal
  deriving DecidableEq, Repr

inductive BridgeInput
  | advance
  deriving DecidableEq, Repr

def bridgeTransition : BridgeState → BridgeInput → BridgeState → Prop
  | .initial, .advance, .terminal => True
  | _, _, _ => False

/-- Same open dynamics, but independently supplied frame and evidence policy. -/
def bridgeContext (frame evidencePolicy : Bool) :
    ContinuationContext BridgeState BridgeInput Bool Unit Unit Unit Unit Unit Bool where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := frame
  transition := bridgeTransition
  edgeAdmissible := fun _ _ _ evidence => evidence = true
  evidenceSufficient := fun evidence => evidencePolicy = true ∧ evidence = true
  invariant := fun _ => True
  transitionPreservesInvariant := by
    intro current next input currentInvariant edge
    trivial

/-- Bare M-space reachability cannot uniquely determine the active frame. -/
theorem same_open_dynamics_does_not_determine_context_frame :
    ∃ first second :
        ContinuationContext BridgeState BridgeInput Bool Unit Unit Unit Unit Unit Bool,
      first.transition = second.transition ∧ first.frame ≠ second.frame := by
  refine ⟨bridgeContext false true, bridgeContext true true, rfl, ?_⟩
  simp [bridgeContext]

/-- The raw lineage contains the edge even when the evidence policy rejects
every possible witness.  Thus Continuum/lineage reachability is a lossy
projection of contextual continuation, not its full semantics. -/
theorem raw_lineage_does_not_determine_contextual_continuation :
    LineageGenerated
        (fun source target => ∃ input, bridgeTransition source input target)
        .initial .terminal ∧
      ¬ Continues (bridgeContext false false) .initial .terminal := by
  constructor
  · exact .ofEvidence ⟨.advance, trivial⟩
  · rintro ⟨witness⟩
    have lineage := witness.toLineage
    have relationRefinesEquality :
        RelationRefines
          (fun source target =>
            ∃ input evidence,
              (bridgeContext false false).transition source input target ∧
              (bridgeContext false false).edgeAdmissible source input target evidence ∧
              (bridgeContext false false).evidenceSufficient evidence)
          (fun source target : BridgeState => source = target) := by
      intro source target edge
      rcases edge with ⟨input, evidence, transition, admissible, sufficient⟩
      simp [bridgeContext] at sufficient
    have equal : BridgeState.initial = BridgeState.terminal :=
      LineageGenerated.minimal relationRefinesEquality
        (fun state => rfl) (fun _ _ _ first second => first.trans second) lineage
    cases equal

/-- Context derivation is therefore conditional: an explicit adapter is
sufficient, while the bare transition relation is not. -/
theorem context_derivation_exact_boundary :
    (∀ adapter : OCContinuationAdapter BridgeState BridgeInput Bool Unit Unit
        Unit Unit Unit Bool bridgeTransition,
      adapter.toContext.transition = bridgeTransition) ∧
    (∃ first second :
        ContinuationContext BridgeState BridgeInput Bool Unit Unit Unit Unit Unit Bool,
      first.transition = second.transition ∧ first.frame ≠ second.frame) := by
  constructor
  · intro adapter
    exact adapter.toContext_reuses_openStep
  · exact same_open_dynamics_does_not_determine_context_frame

end OCKIndividuationMSpaceComposition
