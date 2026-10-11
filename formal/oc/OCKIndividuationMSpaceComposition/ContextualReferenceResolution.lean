import OCKIndividuationMSpaceComposition.PathDependentContinuation

namespace OCKIndividuationMSpaceComposition

universe
  uSignal uCandidate uTask uFrame uProjection uConstraint
  uInput uEvidence uBoundary uScope

/-!
# Task-relative reference resolution

Signal lineage, referent continuation and a binding decision are independent
proof obligations.  Candidate resolution may retain several candidates when
they are equivalent for the declared task; singleton identity is not assumed.
-/

structure ReferenceQuery
    (Signal : Type uSignal)
    (Candidate : Type uCandidate)
    (Task : Type uTask)
    (Frame : Type uFrame)
    (Projection : Type uProjection)
    (Constraint : Type uConstraint) where
  signal : Signal
  task : Task
  frame : Frame
  projection : Projection
  activeConstraint : Constraint → Prop
  satisfiesConstraint : Candidate → Constraint → Prop

def CandidateSatisfies
    {Signal : Type uSignal}
    {Candidate : Type uCandidate}
    {Task : Type uTask}
    {Frame : Type uFrame}
    {Projection : Type uProjection}
    {Constraint : Type uConstraint}
    (query : ReferenceQuery Signal Candidate Task Frame Projection Constraint)
    (candidate : Candidate) : Prop :=
  ∀ constraint, query.activeConstraint constraint →
    query.satisfiesConstraint candidate constraint

/-- Refinement is meaningful only when task, frame and projection are stable. -/
structure StableReferenceRefinement
    {Signal : Type uSignal}
    {Candidate : Type uCandidate}
    {Task : Type uTask}
    {Frame : Type uFrame}
    {Projection : Type uProjection}
    {Constraint : Type uConstraint}
    (base refined : ReferenceQuery Signal Candidate Task Frame Projection Constraint) : Prop where
  signalStable : base.signal = refined.signal
  taskStable : base.task = refined.task
  frameStable : base.frame = refined.frame
  projectionStable : base.projection = refined.projection
  constraintStrengthening :
    ∀ constraint, base.activeConstraint constraint → refined.activeConstraint constraint
  constraintMeaningStable :
    ∀ candidate constraint,
      refined.satisfiesConstraint candidate constraint →
        base.satisfiesConstraint candidate constraint

theorem stable_refinement_prunes_candidates
    {Signal : Type uSignal}
    {Candidate : Type uCandidate}
    {Task : Type uTask}
    {Frame : Type uFrame}
    {Projection : Type uProjection}
    {Constraint : Type uConstraint}
    {base refined : ReferenceQuery Signal Candidate Task Frame Projection Constraint}
    (refinement : StableReferenceRefinement base refined) :
    ∀ candidate, CandidateSatisfies refined candidate → CandidateSatisfies base candidate := by
  intro candidate refinedCandidate constraint active
  exact refinement.constraintMeaningStable candidate constraint
    (refinedCandidate constraint (refinement.constraintStrengthening constraint active))

/-- Resolution permits several task-equivalent candidates. -/
def Resolves
    {Signal : Type uSignal}
    {Candidate : Type uCandidate}
    {Task : Type uTask}
    {Frame : Type uFrame}
    {Projection : Type uProjection}
    {Constraint : Type uConstraint}
    (query : ReferenceQuery Signal Candidate Task Frame Projection Constraint)
    (taskEquivalent : Candidate → Candidate → Prop) : Prop :=
  (∃ candidate, CandidateSatisfies query candidate) ∧
  ∀ left right,
    CandidateSatisfies query left →
    CandidateSatisfies query right →
    taskEquivalent left right

/--
A reference binding keeps signal lineage, referent continuation and current
candidate validity separate.  It therefore cannot launder an ID or pointer
into an object-continuation proof.
-/
structure BindingWitness
    {Signal : Type uSignal}
    {Candidate : Type uCandidate}
    {Task : Type uTask}
    {Frame : Type uFrame}
    {Projection : Type uProjection}
    {Constraint : Type uConstraint}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Boundary : Type uBoundary}
    {Scope : Type uScope}
    (context :
      ContinuationContext Candidate Input Evidence Task Projection Boundary Constraint Scope Frame)
    (signalLineage : Signal → Signal → Prop)
    (sourceSignal targetSignal : Signal)
    (query : ReferenceQuery Signal Candidate Task Frame Projection Constraint)
    (sourceReferent targetReferent : Candidate) : Prop where
  signalContinues : signalLineage sourceSignal targetSignal
  referentContinues : Continues context sourceReferent targetReferent
  targetCandidate : CandidateSatisfies query targetReferent

def finiteCandidateSet
    {Signal : Type uSignal}
    {Candidate : Type uCandidate}
    {Task : Type uTask}
    {Frame : Type uFrame}
    {Projection : Type uProjection}
    {Constraint : Type uConstraint}
    (query : ReferenceQuery Signal Candidate Task Frame Projection Constraint)
    [DecidablePred (CandidateSatisfies query)]
    (candidateUniverse : List Candidate) : List Candidate :=
  candidateUniverse.filter (CandidateSatisfies query)

def candidateCount
    {Signal : Type uSignal}
    {Candidate : Type uCandidate}
    {Task : Type uTask}
    {Frame : Type uFrame}
    {Projection : Type uProjection}
    {Constraint : Type uConstraint}
    (query : ReferenceQuery Signal Candidate Task Frame Projection Constraint)
    [DecidablePred (CandidateSatisfies query)]
    (candidateUniverse : List Candidate) : Nat :=
  (finiteCandidateSet query candidateUniverse).length

/-- Number of unordered candidate pairs still requiring disambiguation. -/
def ambiguityPairCount (candidateTotal : Nat) : Nat :=
  candidateTotal * (candidateTotal - 1) / 2

/-- Token saving of a witness representation, truncated at zero. -/
def referenceCompressionGain (rawDescriptionTokens witnessTokens : Nat) : Nat :=
  rawDescriptionTokens - witnessTokens

theorem finiteCandidateSet_sound
    {Signal : Type uSignal}
    {Candidate : Type uCandidate}
    {Task : Type uTask}
    {Frame : Type uFrame}
    {Projection : Type uProjection}
    {Constraint : Type uConstraint}
    (query : ReferenceQuery Signal Candidate Task Frame Projection Constraint)
    [DecidablePred (CandidateSatisfies query)]
    (candidateUniverse : List Candidate)
    {candidate : Candidate} :
    candidate ∈ finiteCandidateSet query candidateUniverse → CandidateSatisfies query candidate := by
  intro member
  exact of_decide_eq_true (List.mem_filter.mp member).2

theorem finiteCandidateSet_complete_on_universe
    {Signal : Type uSignal}
    {Candidate : Type uCandidate}
    {Task : Type uTask}
    {Frame : Type uFrame}
    {Projection : Type uProjection}
    {Constraint : Type uConstraint}
    (query : ReferenceQuery Signal Candidate Task Frame Projection Constraint)
    [DecidablePred (CandidateSatisfies query)]
    (candidateUniverse : List Candidate)
    {candidate : Candidate} :
    candidate ∈ candidateUniverse → CandidateSatisfies query candidate →
      candidate ∈ finiteCandidateSet query candidateUniverse := by
  intro inUniverse satisfies
  exact List.mem_filter.mpr ⟨inUniverse, decide_eq_true satisfies⟩

end OCKIndividuationMSpaceComposition
