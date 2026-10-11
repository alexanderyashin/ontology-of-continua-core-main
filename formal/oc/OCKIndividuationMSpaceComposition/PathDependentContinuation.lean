import OCKIndividuationMSpaceComposition.DynamicObjectIdentity

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame

/-!
# Context-indexed, path-dependent continuation witnesses

The endpoint of a history is deliberately insufficient here.  A continuation
claim retains the ordered `OpenHistory`, per-step evidence, its declared OC
context and the invariant under which the claim is meaningful.  Nothing in
this file identifies continuation with Lean equality or with quotient identity.
-/

/--
The portion of an OC context needed by the continuation calculus.  Task,
projection, boundary, constraints, scope and frame remain typed and explicit;
the transition law and evidence policy determine admissible paths.
-/
structure ContinuationContext
    (State : Type uState)
    (Input : Type uInput)
    (Evidence : Type uEvidence)
    (Task : Type uTask)
    (Projection : Type uProjection)
    (Boundary : Type uBoundary)
    (Constraint : Type uConstraint)
    (Scope : Type uScope)
    (Frame : Type uFrame) where
  task : Task
  projection : Projection
  boundary : Boundary
  activeConstraint : Constraint → Prop
  scope : Scope
  frame : Frame
  transition : State → Input → State → Prop
  edgeAdmissible : State → Input → State → Evidence → Prop
  evidenceSufficient : Evidence → Prop
  invariant : State → Prop
  transitionPreservesInvariant : OpenHistory.PreservesInvariant transition invariant

/-- Per-edge evidence aligned with one exact `OpenHistory`. -/
inductive HistoryEvidence
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    (C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    {initial : State} :
    {endpoint : State} → OpenHistory C.transition initial endpoint → Type _
  | start : HistoryEvidence C (.start)
  | extend {current next : State}
      {previous : OpenHistory C.transition initial current} :
      HistoryEvidence C previous →
      (input : Input) →
      (edge : C.transition current input next) →
      (evidence : Evidence) →
      C.edgeAdmissible current input next evidence →
      C.evidenceSufficient evidence →
      HistoryEvidence C (.extend previous input edge)

namespace HistoryEvidence

/-- Evidence is stored in reverse chronological order, matching `inputTrace`. -/
def evidenceTrace
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial endpoint : State}
    {history : OpenHistory C.transition initial endpoint} :
    HistoryEvidence C history → List Evidence
  | .start => []
  | .extend previous _ _ evidence _ _ => evidence :: previous.evidenceTrace

/-- Concatenate evidence in the same direction as `OpenHistory.append`. -/
def append
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial middle endpoint : State}
    {prefixHistory : OpenHistory C.transition initial middle}
    {continuation : OpenHistory C.transition middle endpoint}
    (prefixEvidence : HistoryEvidence C prefixHistory) :
    HistoryEvidence C continuation → HistoryEvidence C (prefixHistory.append continuation)
  | .start => prefixEvidence
  | .extend previous input edge evidence admissible sufficient =>
      .extend (prefixEvidence.append previous) input edge evidence admissible sufficient

theorem evidenceTrace_append
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial middle endpoint : State}
    {prefixHistory : OpenHistory C.transition initial middle}
    {continuation : OpenHistory C.transition middle endpoint}
    (prefixEvidence : HistoryEvidence C prefixHistory)
    (continuationEvidence : HistoryEvidence C continuation) :
    (prefixEvidence.append continuationEvidence).evidenceTrace =
      continuationEvidence.evidenceTrace ++ prefixEvidence.evidenceTrace := by
  induction continuationEvidence with
  | start => rfl
  | extend previous input edge evidence admissible sufficient inductionHypothesis =>
      simp only [append, evidenceTrace, inductionHypothesis, List.cons_append]

/-- Forget path data only after producing a directed lineage proof. -/
def toLineage
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial endpoint : State}
    {history : OpenHistory C.transition initial endpoint}
    (historyEvidence : HistoryEvidence C history) :
    LineageGenerated
      (fun source target =>
        ∃ input evidence,
          C.transition source input target ∧
          C.edgeAdmissible source input target evidence ∧
          C.evidenceSufficient evidence)
      initial endpoint := by
  induction historyEvidence with
  | start => exact .refl initial
  | extend previous input edge evidence admissible sufficient inductionHypothesis =>
      exact .trans inductionHypothesis (.ofEvidence ⟨input, evidence, edge, admissible, sufficient⟩)

end HistoryEvidence

/-- A path, aligned evidence and the initial context invariant. -/
structure ContinuationWitness
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    (C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (initial endpoint : State) : Type _ where
  history : OpenHistory C.transition initial endpoint
  evidence : HistoryEvidence C history
  initialInvariant : C.invariant initial

/-- Continuation is inhabited proof-carrying path evidence, not equality. -/
def Continues
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    (C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (initial endpoint : State) : Prop :=
  Nonempty (ContinuationWitness C initial endpoint)

/-- Reader-facing name; still intentionally not `initial = endpoint`. -/
abbrev SameObjectClaim := @Continues

namespace ContinuationWitness

def refl
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {state : State}
    (admissibleState : C.invariant state) : ContinuationWitness C state state :=
  ⟨.start, .start, admissibleState⟩

def comp
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial middle endpoint : State}
    (left : ContinuationWitness C initial middle)
    (right : ContinuationWitness C middle endpoint) :
    ContinuationWitness C initial endpoint :=
  ⟨left.history.append right.history,
    left.evidence.append right.evidence,
    left.initialInvariant⟩

theorem endpointInvariant
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial endpoint : State}
    (witness : ContinuationWitness C initial endpoint) : C.invariant endpoint :=
  witness.history.invariant witness.initialInvariant C.transitionPreservesInvariant

theorem toLineage
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial endpoint : State}
    (witness : ContinuationWitness C initial endpoint) :
    LineageGenerated
      (fun source target =>
        ∃ input evidence,
          C.transition source input target ∧
          C.edgeAdmissible source input target evidence ∧
          C.evidenceSufficient evidence)
      initial endpoint :=
  witness.evidence.toLineage

end ContinuationWitness

theorem continues_refl
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {state : State}
    (admissibleState : C.invariant state) : Continues C state state :=
  ⟨.refl admissibleState⟩

theorem continues_trans
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial middle endpoint : State} :
    Continues C initial middle → Continues C middle endpoint → Continues C initial endpoint := by
  rintro ⟨left⟩ ⟨right⟩
  exact ⟨left.comp right⟩

theorem OpenHistory.append_assoc
    {State : Type uState}
    {Input : Type uInput}
    {transition : State → Input → State → Prop}
    {a b c d : State}
    (first : OpenHistory transition a b)
    (second : OpenHistory transition b c)
    (third : OpenHistory transition c d) :
    (first.append second).append third = first.append (second.append third) := by
  induction third with
  | start => rfl
  | extend previous input edge inductionHypothesis =>
      simp only [OpenHistory.append, inductionHypothesis]

theorem ContinuationWitness.comp_history_assoc
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {a b c d : State}
    (first : ContinuationWitness C a b)
    (second : ContinuationWitness C b c)
    (third : ContinuationWitness C c d) :
    ((first.comp second).comp third).history =
      (first.comp (second.comp third)).history :=
  OpenHistory.append_assoc first.history second.history third.history

/-- Explicit contract required before moving a witness between contexts. -/
structure ContextCompatibility
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame) where
  taskCompatible : source.task = target.task
  projectionCompatible : source.projection = target.projection
  boundaryCompatible : source.boundary = target.boundary
  scopeCompatible : source.scope = target.scope
  frameCompatible : source.frame = target.frame
  transport : ∀ initial endpoint,
    ContinuationWitness source initial endpoint →
      ContinuationWitness target initial endpoint

def transport_then_compose
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    (compatibility : ContextCompatibility source target)
    {initial middle endpoint : State}
    (left : ContinuationWitness source initial middle)
    (right : ContinuationWitness target middle endpoint) :
    ContinuationWitness target initial endpoint :=
  (compatibility.transport initial middle left).comp right

theorem no_context_compatibility_of_counterexample
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial endpoint : State}
    (sourceWitness : Continues source initial endpoint)
    (targetObstruction : ¬ Continues target initial endpoint) :
    ContextCompatibility source target → False := by
  intro compatibility
  apply targetObstruction
  exact sourceWitness.map (compatibility.transport initial endpoint)

/-- A genuine two-patch cover carries the witnesses needed for gluing. -/
structure LocalWitnessCover
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    (C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (initial endpoint : State) where
  overlap : State
  left : ContinuationWitness C initial overlap
  right : ContinuationWitness C overlap endpoint

def LocalWitnessCover.glue
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
    {initial endpoint : State}
    (cover : LocalWitnessCover C initial endpoint) :
    ContinuationWitness C initial endpoint :=
  cover.left.comp cover.right

end OCKIndividuationMSpaceComposition
