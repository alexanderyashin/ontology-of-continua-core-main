import OCKIndividuationMSpaceComposition.KMPredictiveModelConstraint
import OCKIndividuationMSpaceComposition.PathDependentContinuation
import Mathlib.Tactic.Linarith

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe
  uLiftCarrier uLiftCandidate uRepairCandidate
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame

/-!
# Context and continuation conditions for K/M predictive coherence

K/M rank selection supplies a tied structural model class.  This module states
the additional, inspectable OC conditions under which that class has one
bounded future.  The essential condition is not equality of context labels:
it is equivalence of evidence-qualified transition behavior and of terminal
admission on a common typed carrier.

The reachability proofs below adapt standard transition-system behavioral
equivalence to OC's typed context, evidence policy, continuation witness and
K/M selection surfaces.  No probability law is inferred from reachability.
-/

/-- A transition is prediction-eligible only when the context transition,
edge policy and evidence-sufficiency policy are jointly witnessed. -/
def EvidenceQualifiedStep
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    (context :
      ContinuationContext State Input Evidence Task Projection Boundary
        Constraint Scope Frame) :
    State → Input → State → Prop :=
  fun source input target =>
    ∃ evidence,
      context.transition source input target ∧
      context.edgeAdmissible source input target evidence ∧
      context.evidenceSufficient evidence

/-- One continuation context, viewed as a predictive transition system after
the remaining four admission layers have been supplied explicitly. -/
def ContextPredictiveSystem
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    (context :
      ContinuationContext State Input Evidence Task Projection Boundary
        Constraint Scope Frame)
    (layers : LayeredAdmissibility State) : PredictiveSystem where
  State := State
  Action := Input
  step := EvidenceQualifiedStep context
  layers := layers

/-- Every evidence-carrying continuation history is an exact finite path in
the evidence-qualified predictive system. -/
theorem historyEvidence_reaches_exactly
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary
        Constraint Scope Frame}
    (layers : LayeredAdmissibility State)
    {initial endpoint : State}
    {history : OpenHistory context.transition initial endpoint}
    (historyEvidence : HistoryEvidence context history) :
    ReachExactly (ContextPredictiveSystem context layers) initial
      history.length endpoint := by
  induction historyEvidence with
  | start => exact .root
  | extend previous input edge evidence admissible sufficient inductionHypothesis =>
      exact .tail inductionHypothesis input
        ⟨evidence, edge, admissible, sufficient⟩

/-- Positive continuation-to-prediction bridge.  A witnessed continuation is
a bounded target future once its exact length fits the horizon and its endpoint
passes the explicitly separate admission layers. -/
theorem ContinuationWitness.targetFuture
    {State : Type uState}
    {Input : Type uInput}
    {Evidence : Type uEvidence}
    {Task : Type uTask}
    {Projection : Type uProjection}
    {Boundary : Type uBoundary}
    {Constraint : Type uConstraint}
    {Scope : Type uScope}
    {Frame : Type uFrame}
    {context :
      ContinuationContext State Input Evidence Task Projection Boundary
        Constraint Scope Frame}
    (layers : LayeredAdmissibility State)
    {initial endpoint : State}
    (witness : ContinuationWitness context initial endpoint)
    (horizon : Nat)
    (withinHorizon : witness.history.length ≤ horizon)
    (admitted : layers.FullyAdmitted endpoint) :
    TargetFuture (ContextPredictiveSystem context layers) initial horizon endpoint := by
  exact ⟨⟨witness.history.length, withinHorizon,
    historyEvidence_reaches_exactly layers witness.evidence⟩, admitted⟩

/-- A common-carrier interpretation assigns an OC continuation context and
admission layers to every tied K/M lift candidate. -/
structure KMContextContinuationInterpretation
    {K : CurrentK}
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K) where
  State : Type uState
  Input : Type uInput
  Evidence : Type uEvidence
  Task : Type uTask
  Projection : Type uProjection
  Boundary : Type uBoundary
  Constraint : Type uConstraint
  Scope : Type uScope
  Frame : Type uFrame
  contextOf : liftSearch.Candidate →
    ContinuationContext State Input Evidence Task Projection Boundary
      Constraint Scope Frame
  layersOf : liftSearch.Candidate → LayeredAdmissibility State
  initial : State
  horizon : Nat

/-- Forget only the context fields, retaining the exact qualified transition
and admission behavior used by the generic K/M predictive model class. -/
def KMContextContinuationInterpretation.predictiveInterpretation
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (interpretation : KMContextContinuationInterpretation liftSearch) :
    KMPredictiveInterpretation liftSearch where
  State := interpretation.State
  Action := interpretation.Input
  stepOf := fun candidate => EvidenceQualifiedStep (interpretation.contextOf candidate)
  layersOf := interpretation.layersOf
  initial := interpretation.initial
  horizon := interpretation.horizon

/-- Agreement of context headers and invariants.  This is auditable metadata,
but deliberately weaker than predictive coherence. -/
structure ContextHeaderAgreement
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (left right : liftSearch.Candidate) : Prop where
  task : (interpretation.contextOf left).task =
    (interpretation.contextOf right).task
  projection : (interpretation.contextOf left).projection =
    (interpretation.contextOf right).projection
  boundary : (interpretation.contextOf left).boundary =
    (interpretation.contextOf right).boundary
  activeConstraint : ∀ constraint,
    (interpretation.contextOf left).activeConstraint constraint ↔
      (interpretation.contextOf right).activeConstraint constraint
  scope : (interpretation.contextOf left).scope =
    (interpretation.contextOf right).scope
  frame : (interpretation.contextOf left).frame =
    (interpretation.contextOf right).frame
  invariant : ∀ state,
    (interpretation.contextOf left).invariant state ↔
      (interpretation.contextOf right).invariant state

/-- Exact OC behavioral contract on the common carrier.  Header agreement is
registered, but finite-future transfer is justified by qualified-step and
terminal-admission equivalence. -/
structure ContextContinuationCoherence
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (left right : liftSearch.Candidate) : Prop where
  header : ContextHeaderAgreement interpretation left right
  qualifiedStep : ∀ source input target,
    EvidenceQualifiedStep (interpretation.contextOf left) source input target ↔
      EvidenceQualifiedStep (interpretation.contextOf right) source input target
  fullyAdmitted : ∀ state,
    (interpretation.layersOf left).FullyAdmitted state ↔
      (interpretation.layersOf right).FullyAdmitted state

/-- Structural recursion transporting one exact qualified path forward. -/
def ContextContinuationCoherence.mapReachExactlyForward
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    {left right : liftSearch.Candidate}
    (coherence : ContextContinuationCoherence interpretation left right)
    {depth : Nat} {target : interpretation.State} :
    ReachExactly
        (interpretation.predictiveInterpretation.systemAt left)
        interpretation.initial depth target →
      ReachExactly
        (interpretation.predictiveInterpretation.systemAt right)
        interpretation.initial depth target
  | .root => .root
  | .tail previous input edge =>
      .tail (coherence.mapReachExactlyForward previous) input
        ((coherence.qualifiedStep _ _ _).mp edge)

/-- Structural recursion transporting one exact qualified path backward. -/
def ContextContinuationCoherence.mapReachExactlyBackward
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    {left right : liftSearch.Candidate}
    (coherence : ContextContinuationCoherence interpretation left right)
    {depth : Nat} {target : interpretation.State} :
    ReachExactly
        (interpretation.predictiveInterpretation.systemAt right)
        interpretation.initial depth target →
      ReachExactly
        (interpretation.predictiveInterpretation.systemAt left)
        interpretation.initial depth target
  | .root => .root
  | .tail previous input edge =>
      .tail (coherence.mapReachExactlyBackward previous) input
        ((coherence.qualifiedStep _ _ _).mpr edge)

/-- Exact qualified-step equivalence transports every exact finite path. -/
theorem context_coherence_reachExactly_iff
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    {left right : liftSearch.Candidate}
    (coherence : ContextContinuationCoherence interpretation left right)
    (depth : Nat) (target : interpretation.State) :
    ReachExactly
        (interpretation.predictiveInterpretation.systemAt left)
        interpretation.initial depth target ↔
      ReachExactly
        (interpretation.predictiveInterpretation.systemAt right)
        interpretation.initial depth target := by
  exact ⟨coherence.mapReachExactlyForward,
    coherence.mapReachExactlyBackward⟩

/-- Therefore all bounded reachable sets coincide. -/
theorem context_coherence_reachWithin_iff
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    {left right : liftSearch.Candidate}
    (coherence : ContextContinuationCoherence interpretation left right)
    (horizon : Nat) (target : interpretation.State) :
    ReachWithin
        (interpretation.predictiveInterpretation.systemAt left)
        interpretation.initial horizon target ↔
      ReachWithin
        (interpretation.predictiveInterpretation.systemAt right)
        interpretation.initial horizon target := by
  constructor
  · rintro ⟨depth, bound, reachable⟩
    exact ⟨depth, bound,
      (context_coherence_reachExactly_iff coherence depth target).mp reachable⟩
  · rintro ⟨depth, bound, reachable⟩
    exact ⟨depth, bound,
      (context_coherence_reachExactly_iff coherence depth target).mpr reachable⟩

/-- Exact path behavior plus exact terminal admission is sufficient for equal
bounded target futures. -/
theorem context_coherence_targetFuture_iff
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {interpretation : KMContextContinuationInterpretation liftSearch}
    {left right : liftSearch.Candidate}
    (coherence : ContextContinuationCoherence interpretation left right)
    (target : interpretation.State) :
    interpretation.predictiveInterpretation.targetFutureAt left target ↔
      interpretation.predictiveInterpretation.targetFutureAt right target := by
  constructor
  · rintro ⟨reachable, admitted⟩
    exact ⟨(context_coherence_reachWithin_iff coherence
      interpretation.horizon target).mp reachable,
      (coherence.fullyAdmitted target).mp admitted⟩
  · rintro ⟨reachable, admitted⟩
    exact ⟨(context_coherence_reachWithin_iff coherence
      interpretation.horizon target).mpr reachable,
      (coherence.fullyAdmitted target).mpr admitted⟩

/-- Every tied K/M candidate is behaviorally coherent with the selected
minimum under an explicit context-and-continuation contract. -/
def KMTiedContextContinuationCoherent
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch) : Prop :=
  ∀ candidate, KMTiedResolvingCandidate resolution candidate →
    ContextContinuationCoherence interpretation candidate
      resolution.selection.minimizer.1

/-- The explicit context contract closes the formerly open premise in the v64
K/M point-identification theorem. -/
theorem km_context_continuation_coherence_implies_point_identified
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (coherent : KMTiedContextContinuationCoherent resolution interpretation) :
    KMPointIdentified resolution
      interpretation.predictiveInterpretation.targetFutureAt := by
  apply km_coherence_implies_point_identified
  intro candidate tied target
  exact context_coherence_targetFuture_iff (coherent candidate tied) target

/-!
## Quantitative residual model-class uncertainty
-/

/-- Every tied candidate lies within `epsilon` of the selected candidate's
forecast.  The radius is a declared context/model-class quantity, not a
sampling error silently manufactured by the theorem. -/
def KMContextualNumericCoherence
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (value : liftSearch.Candidate → ℚ)
    (epsilon : ℚ) : Prop :=
  0 ≤ epsilon ∧
  ∀ candidate, KMTiedResolvingCandidate resolution candidate →
    value resolution.selection.minimizer.1 - epsilon ≤ value candidate ∧
      value candidate ≤ value resolution.selection.minimizer.1 + epsilon

/-- A contextual radius `epsilon` bounds pairwise tied-model disagreement by
`2 * epsilon`. -/
theorem km_contextual_radius_bounds_pairwise_disagreement
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (value : liftSearch.Candidate → ℚ)
    (epsilon : ℚ)
    (bounded : KMContextualNumericCoherence resolution value epsilon)
    (left right : liftSearch.Candidate)
    (leftTied : KMTiedResolvingCandidate resolution left)
    (rightTied : KMTiedResolvingCandidate resolution right) :
    value left - value right ≤ 2 * epsilon ∧
      value right - value left ≤ 2 * epsilon := by
  have leftBounds := bounded.2 left leftTied
  have rightBounds := bounded.2 right rightTied
  constructor <;> linarith

/-- The sharp v64 prediction band can be no wider than twice the contextual
coherence radius. -/
theorem km_contextual_radius_bounds_sharp_band_width
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {value : liftSearch.Candidate → ℚ}
    (band : KMSharpPredictionBand resolution value)
    (epsilon : ℚ)
    (bounded : KMContextualNumericCoherence resolution value epsilon) :
    band.width ≤ 2 * epsilon := by
  obtain ⟨lowerCandidate, lowerTied, lowerAt⟩ := band.lowerAttained
  obtain ⟨upperCandidate, upperTied, upperAt⟩ := band.upperAttained
  have pairBound := km_contextual_radius_bounds_pairwise_disagreement
    resolution value epsilon bounded upperCandidate lowerCandidate
      upperTied lowerTied
  dsimp [KMSharpPredictionBand.width]
  rw [← lowerAt, ← upperAt]
  exact pairBound.1

/-- Observation error and residual model-class radius add.  Thus improving
measurement alone cannot beat the remaining structural radius. -/
theorem km_contextual_and_observation_error_add
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (value : liftSearch.Candidate → ℚ)
    (epsilon delta estimate : ℚ)
    (bounded : KMContextualNumericCoherence resolution value epsilon)
    (estimateBounds :
      value resolution.selection.minimizer.1 - delta ≤ estimate ∧
        estimate ≤ value resolution.selection.minimizer.1 + delta)
    (candidate : liftSearch.Candidate)
    (tied : KMTiedResolvingCandidate resolution candidate) :
    value candidate - (epsilon + delta) ≤ estimate ∧
      estimate ≤ value candidate + (epsilon + delta) := by
  have candidateBounds := bounded.2 candidate tied
  constructor <;> linarith

/-- Zero contextual radius collapses all tied numerical predictions exactly to
the selected model's value. -/
theorem km_zero_contextual_radius_gives_exact_numeric_prediction
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (value : liftSearch.Candidate → ℚ)
    (bounded : KMContextualNumericCoherence resolution value 0) :
    ∀ candidate, KMTiedResolvingCandidate resolution candidate →
      value candidate = value resolution.selection.minimizer.1 := by
  intro candidate tied
  have bounds := bounded.2 candidate tied
  linarith

/-!
## Header-only countermodel
-/

def headerCounterSource :
    ContinuationContext Bool Unit Unit Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := fun source _ target => source = false ∧ target = true
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun _ => True
  transitionPreservesInvariant := by
    intro current next input currentInvariant edge
    trivial

def headerCounterTarget :
    ContinuationContext Bool Unit Unit Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := fun _ _ _ => False
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun _ => True
  transitionPreservesInvariant := by
    intro current next input currentInvariant edge
    contradiction

/-- Equal task, projection, boundary, constraints, scope, frame and invariant
do not imply equal qualified dynamics. -/
theorem equal_context_headers_and_invariant_do_not_determine_future :
    headerCounterSource.task = headerCounterTarget.task ∧
    headerCounterSource.projection = headerCounterTarget.projection ∧
    headerCounterSource.boundary = headerCounterTarget.boundary ∧
    (∀ constraint,
      headerCounterSource.activeConstraint constraint ↔
        headerCounterTarget.activeConstraint constraint) ∧
    headerCounterSource.scope = headerCounterTarget.scope ∧
    headerCounterSource.frame = headerCounterTarget.frame ∧
    (∀ state, headerCounterSource.invariant state ↔
      headerCounterTarget.invariant state) ∧
    EvidenceQualifiedStep headerCounterSource false () true ∧
    ¬ EvidenceQualifiedStep headerCounterTarget false () true := by
  refine ⟨rfl, rfl, rfl, ?_, rfl, rfl, ?_, ?_, ?_⟩
  · intro constraint
    exact Iff.rfl
  · intro state
    exact Iff.rfl
  · exact ⟨(), ⟨rfl, rfl⟩, trivial, trivial⟩
  · rintro ⟨evidence, impossible, admissible, sufficient⟩
    exact impossible

end OCKIndividuationMSpaceComposition
