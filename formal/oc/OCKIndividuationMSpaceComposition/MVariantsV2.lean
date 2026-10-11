import OCKIndividuationMSpaceComposition.DynamicObjectIdentity
import OCMinimalObligationSpine.MSpace
import OCMaturityCompletionCycle.ContextualOpenDynamics

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine
open OCMaturityCompletionCycle

universe uState uInput uBoundary uLiftCarrier uLiftCandidate
universe uContext uAction
universe uPoint uPoint' uState' uInput' uObservation uObservation'

/-!
# Distinct M-variants and explicit translations

The name `M` has denoted several non-equivalent constructions.  This module
keeps the constructions in different Lean types and supplies only directed
forgetful maps or proof-carrying adapters.  No coercion identifies a lift
search fiber, a finite generated history, a viable history, a boundary-labeled
history, an infinite history, or a stochastic path law.
-/

namespace OpenHistory

/-- Map a history along an inclusion of transition laws on the same carriers. -/
def weaken
    {State : Type uState}
    {Input : Type uInput}
    {transition transition' : State -> Input -> State -> Prop}
    (includes : forall {source input target},
      transition source input target -> transition' source input target)
    {initial endpoint : State} :
    OpenHistory transition initial endpoint ->
      OpenHistory transition' initial endpoint
  | .start => .start
  | .extend previous input edge =>
      .extend (previous.weaken includes) input (includes edge)

/-- Weakening a transition predicate preserves the exact input trace. -/
theorem inputTrace_weaken
    {State : Type uState}
    {Input : Type uInput}
    {transition transition' : State -> Input -> State -> Prop}
    (includes : forall {source input target},
      transition source input target -> transition' source input target)
    {initial endpoint : State}
    (history : OpenHistory transition initial endpoint) :
    (history.weaken includes).inputTrace = history.inputTrace := by
  induction history with
  | start => rfl
  | extend previous input edge inductionHypothesis =>
      simp [weaken, inputTrace, inductionHypothesis]

/-- Every state visited by a finite history satisfies a supplied viability law. -/
def AllStates
    {State : Type uState}
    {Input : Type uInput}
    {transition : State -> Input -> State -> Prop}
    {initial endpoint : State}
    (viable : State -> Prop) :
    OpenHistory transition initial endpoint -> Prop
  | .start => viable initial
  | .extend previous _ _ => AllStates viable previous /\ viable endpoint

/-- Viability implies endpoint viability. -/
theorem AllStates.endpoint
    {State : Type uState}
    {Input : Type uInput}
    {transition : State -> Input -> State -> Prop}
    {initial endpoint : State}
    {viable : State -> Prop}
    {history : OpenHistory transition initial endpoint}
    (allStates : history.AllStates viable) :
    viable endpoint := by
  cases history with
  | start => exact allStates
  | extend previous input edge => exact allStates.2

end OpenHistory

/-- Directed translation of a generated M-space along a step inclusion. -/
def DerivedMSpace.weaken
    {State : Type uState}
    {Input : Type uInput}
    {transition transition' : State -> Input -> State -> Prop}
    (includes : forall {source input target},
      transition source input target -> transition' source input target)
    {initial : State} :
    DerivedMSpace transition initial -> DerivedMSpace transition' initial :=
  fun point => ⟨point.1, point.2.weaken includes⟩

/-- The directed M-space translation preserves endpoints exactly. -/
theorem DerivedMSpace.weaken_endpoint
    {State : Type uState}
    {Input : Type uInput}
    {transition transition' : State -> Input -> State -> Prop}
    (includes : forall {source input target},
      transition source input target -> transition' source input target)
    {initial : State}
    (point : DerivedMSpace transition initial) :
    (point.weaken includes).1 = point.1 :=
  rfl

/-- A finite derived history together with all-state viability evidence. -/
structure ViableMSpace
    {State : Type uState}
    {Input : Type uInput}
    (transition : State -> Input -> State -> Prop)
    (initial : State)
    (viable : State -> Prop) where
  point : DerivedMSpace transition initial
  allStates : point.2.AllStates viable

/-- Forget viability evidence while preserving the complete finite history. -/
def ViableMSpace.forget
    {State : Type uState}
    {Input : Type uInput}
    {transition : State -> Input -> State -> Prop}
    {initial : State}
    {viable : State -> Prop} :
    ViableMSpace transition initial viable -> DerivedMSpace transition initial :=
  fun point => point.point

/-- The viability-forgetting map is faithful to proof-carrying points. -/
theorem ViableMSpace.forget_injective
    {State : Type uState}
    {Input : Type uInput}
    {transition : State -> Input -> State -> Prop}
    {initial : State}
    {viable : State -> Prop} :
    Function.Injective
      (@ViableMSpace.forget State Input transition initial viable) := by
  intro first second samePoint
  cases first
  cases second
  cases samePoint
  rfl

/-- A boundary label admitted by a predicate over the complete input trace. -/
structure BoundaryHistoryMSpace
    {State : Type uState}
    {Input : Type uInput}
    (transition : State -> Input -> State -> Prop)
    (initial : State)
    (Boundary : Type uBoundary)
    (compatible : List Input -> Boundary -> Prop) where
  point : DerivedMSpace transition initial
  boundary : Boundary
  compatible_with_history : compatible point.2.inputTrace boundary

/-- Forget the boundary label but retain the generated finite history. -/
def BoundaryHistoryMSpace.forget
    {State : Type uState}
    {Input : Type uInput}
    {transition : State -> Input -> State -> Prop}
    {initial : State}
    {Boundary : Type uBoundary}
    {compatible : List Input -> Boundary -> Prop} :
    BoundaryHistoryMSpace transition initial Boundary compatible ->
      DerivedMSpace transition initial :=
  fun point => point.point

/-- A genuinely infinite input-labelled open history. -/
structure OmegaOpenHistory
    {State : Type uState}
    {Input : Type uInput}
    (transition : State -> Input -> State -> Prop)
    (initial : State) where
  state : Nat -> State
  input : Nat -> Input
  starts : state 0 = initial
  productive : forall depth,
    transition (state depth) (input depth) (state (depth + 1))

namespace OmegaOpenHistory

/-- Every finite stage of an omega history is propositionally reachable. -/
theorem finiteStageReachable
    {State : Type uState}
    {Input : Type uInput}
    {transition : State -> Input -> State -> Prop}
    {initial : State}
    (history : OmegaOpenHistory transition initial) :
    forall depth,
      OpenReachable transition initial (history.state depth) := by
  intro depth
  induction depth with
  | zero => simpa [history.starts] using
      (OpenReachable.initial : OpenReachable transition initial initial)
  | succ depth inductionHypothesis =>
      exact OpenReachable.step inductionHypothesis (history.input depth)
        (by simpa [Nat.succ_eq_add_one] using history.productive depth)

end OmegaOpenHistory

/-- A finite stochastic path remains a separate weighted-path point. -/
structure FiniteStochasticMPoint
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    [Fintype State]
    (experiment : FinitePathExperiment State Context Boundary Action) where
  path : FiniteStatePath State experiment.horizon

/-- Its weight is derived from the experiment, never an arbitrary annotation. -/
def FiniteStochasticMPoint.weight
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    [Fintype State]
    {experiment : FinitePathExperiment State Context Boundary Action}
    (point : FiniteStochasticMPoint experiment) : ℚ :=
  inducedFinitePathWeight experiment point.path

/-!
## Evidence-bearing semantic translations
-/

/--
A presentation of the semantic coordinates that an M-space translation may
claim to preserve.  Keeping the point carrier separate permits finite
histories, lift fibers, boundary histories, and path laws to instantiate the
same contract without identifying their types.
-/
structure MSpaceSemanticPresentation
    (Point : Type uPoint)
    (State : Type uState)
    (Input : Type uInput)
    (Observation : Type uObservation) where
  transition : State -> Input -> State -> Prop
  initial : State
  endpoint : Point -> State
  inputTrace : Point -> List Input
  observation : Point -> Observation

/-- The five preservation obligations for declared carrier maps. -/
def MSpaceTranslationConditions
    {SourcePoint : Type uPoint}
    {SourceState : Type uState}
    {SourceInput : Type uInput}
    {SourceObservation : Type uObservation}
    {TargetPoint : Type uPoint'}
    {TargetState : Type uState'}
    {TargetInput : Type uInput'}
    {TargetObservation : Type uObservation'}
    (source : MSpaceSemanticPresentation SourcePoint SourceState
      SourceInput SourceObservation)
    (target : MSpaceSemanticPresentation TargetPoint TargetState
      TargetInput TargetObservation)
    (pointMap : SourcePoint -> TargetPoint)
    (stateMap : SourceState -> TargetState)
    (inputMap : SourceInput -> TargetInput)
    (observationMap : SourceObservation -> TargetObservation) : Prop :=
  (forall sourceState sourceInput targetState,
      source.transition sourceState sourceInput targetState ->
        target.transition (stateMap sourceState) (inputMap sourceInput)
          (stateMap targetState)) /\
  stateMap source.initial = target.initial /\
  (forall point,
      target.endpoint (pointMap point) = stateMap (source.endpoint point)) /\
  (forall point,
      target.inputTrace (pointMap point) =
        (source.inputTrace point).map inputMap) /\
  (forall point,
      target.observation (pointMap point) =
        observationMap (source.observation point))

/--
A semantic M translation carries maps plus evidence for transition, initial
state, endpoint, complete input trace, and observation preservation.
-/
structure MSpaceSemanticTranslation
    {SourcePoint : Type uPoint}
    {SourceState : Type uState}
    {SourceInput : Type uInput}
    {SourceObservation : Type uObservation}
    {TargetPoint : Type uPoint'}
    {TargetState : Type uState'}
    {TargetInput : Type uInput'}
    {TargetObservation : Type uObservation'}
    (source : MSpaceSemanticPresentation SourcePoint SourceState
      SourceInput SourceObservation)
    (target : MSpaceSemanticPresentation TargetPoint TargetState
      TargetInput TargetObservation) where
  pointMap : SourcePoint -> TargetPoint
  stateMap : SourceState -> TargetState
  inputMap : SourceInput -> TargetInput
  observationMap : SourceObservation -> TargetObservation
  transition_preserves : forall sourceState sourceInput targetState,
    source.transition sourceState sourceInput targetState ->
      target.transition (stateMap sourceState) (inputMap sourceInput)
        (stateMap targetState)
  initial_preserves : stateMap source.initial = target.initial
  endpoint_preserves : forall point,
    target.endpoint (pointMap point) = stateMap (source.endpoint point)
  inputTrace_preserves : forall point,
    target.inputTrace (pointMap point) =
      (source.inputTrace point).map inputMap
  observation_preserves : forall point,
    target.observation (pointMap point) =
      observationMap (source.observation point)

/--
Exact existence criterion: a semantic translation exists if and only if four
carrier maps jointly satisfy all five preservation obligations.  This prevents
a bare function between point carriers from being reported as a semantic M
translation.
-/
theorem mSpaceSemanticTranslation_exists_iff_preserving_maps
    {SourcePoint : Type uPoint}
    {SourceState : Type uState}
    {SourceInput : Type uInput}
    {SourceObservation : Type uObservation}
    {TargetPoint : Type uPoint'}
    {TargetState : Type uState'}
    {TargetInput : Type uInput'}
    {TargetObservation : Type uObservation'}
    (source : MSpaceSemanticPresentation SourcePoint SourceState
      SourceInput SourceObservation)
    (target : MSpaceSemanticPresentation TargetPoint TargetState
      TargetInput TargetObservation) :
    Nonempty (MSpaceSemanticTranslation source target) <->
      exists pointMap stateMap inputMap observationMap,
        MSpaceTranslationConditions source target pointMap stateMap
          inputMap observationMap := by
  constructor
  · rintro ⟨translation⟩
    exact ⟨translation.pointMap, translation.stateMap,
      translation.inputMap, translation.observationMap,
      translation.transition_preserves, translation.initial_preserves,
      translation.endpoint_preserves, translation.inputTrace_preserves,
      translation.observation_preserves⟩
  · rintro ⟨pointMap, stateMap, inputMap, observationMap,
      transitionPreserves, initialPreserves, endpointPreserves,
      inputTracePreserves, observationPreserves⟩
    exact ⟨{
      pointMap := pointMap
      stateMap := stateMap
      inputMap := inputMap
      observationMap := observationMap
      transition_preserves := transitionPreserves
      initial_preserves := initialPreserves
      endpoint_preserves := endpointPreserves
      inputTrace_preserves := inputTracePreserves
      observation_preserves := observationPreserves
    }⟩

/-- The semantic presentation carried by finite generated histories. -/
def derivedMSpaceSemanticPresentation
    {State : Type uState}
    {Input : Type uInput}
    {Observation : Type uObservation}
    (transition : State -> Input -> State -> Prop)
    (initial : State)
    (observe : State -> Observation) :
    MSpaceSemanticPresentation
      (DerivedMSpace transition initial) State Input Observation where
  transition := transition
  initial := initial
  endpoint := fun point => point.1
  inputTrace := fun point => point.2.inputTrace
  observation := fun point => observe point.1

/--
Step inclusion is a genuine semantic-translation existence theorem for finite
generated histories, not merely a point-carrier map.
-/
def DerivedMSpace.weakenSemanticTranslation
    {State : Type uState}
    {Input : Type uInput}
    {Observation : Type uObservation}
    {transition transition' : State -> Input -> State -> Prop}
    (includes : forall {source input target},
      transition source input target -> transition' source input target)
    {initial : State}
    (observe : State -> Observation) :
    MSpaceSemanticTranslation
      (derivedMSpaceSemanticPresentation transition initial observe)
      (derivedMSpaceSemanticPresentation transition' initial observe) where
  pointMap := fun point => point.weaken includes
  stateMap := id
  inputMap := id
  observationMap := id
  transition_preserves := by
    intro source input target edge
    exact includes edge
  initial_preserves := rfl
  endpoint_preserves := by intro point; rfl
  inputTrace_preserves := by
    intro point
    simpa [derivedMSpaceSemanticPresentation] using
      (OpenHistory.inputTrace_weaken includes point.2)
  observation_preserves := by intro point; rfl

/-- Transition inclusion is a constructive existence criterion for this bridge. -/
theorem DerivedMSpace.semanticTranslation_exists_of_step_inclusion
    {State : Type uState}
    {Input : Type uInput}
    {Observation : Type uObservation}
    {transition transition' : State -> Input -> State -> Prop}
    (includes : forall {source input target},
      transition source input target -> transition' source input target)
    {initial : State}
    (observe : State -> Observation) :
    Nonempty (MSpaceSemanticTranslation
      (derivedMSpaceSemanticPresentation transition initial observe)
      (derivedMSpaceSemanticPresentation transition' initial observe)) :=
  ⟨DerivedMSpace.weakenSemanticTranslation includes observe⟩

/-- A one-point presentation with an admitted transition. -/
def permissiveUnitMSpacePresentation :
    MSpaceSemanticPresentation Unit Unit Unit Unit where
  transition := fun _ _ _ => True
  initial := ()
  endpoint := fun _ => ()
  inputTrace := fun _ => []
  observation := fun _ => ()

/-- The same carriers with every transition forbidden. -/
def blockedUnitMSpacePresentation :
    MSpaceSemanticPresentation Unit Unit Unit Unit where
  transition := fun _ _ _ => False
  initial := ()
  endpoint := fun _ => ()
  inputTrace := fun _ => []
  observation := fun _ => ()

/--
An underlying point map can exist while no evidence-bearing semantic
translation exists: the admitted source edge cannot map to the blocked target.
-/
theorem bare_point_map_does_not_imply_semantic_translation :
    Nonempty (Unit -> Unit) /\
      IsEmpty (MSpaceSemanticTranslation
        permissiveUnitMSpacePresentation blockedUnitMSpacePresentation) := by
  constructor
  · exact ⟨id⟩
  · constructor
    intro translation
    exact translation.transition_preserves () () () trivial

/-!
## Carrier-level adapters to the current `MSpaceFiber`

The older adapters below remain useful as raw directed carrier maps.  They are
not semantic translations unless the lift fiber and history are each equipped
with an `MSpaceSemanticPresentation` and the map is lifted to an
`MSpaceSemanticTranslation` satisfying the five evidence fields above.
-/

/--
A directed adapter from representational lift candidates to generated
histories.  `admissibleHistory` is supplied because lift resolution alone says
nothing about a transition law, initial condition, or history semantics.
-/
structure MSpaceFiberToHistoryAdapter
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (distinction : TrajectoryDistinction K)
    {State : Type uState}
    {Input : Type uInput}
    (transition : State -> Input -> State -> Prop)
    (initial : State)
    (admissibleHistory : DerivedMSpace transition initial -> Prop) where
  toHistory : MSpaceFiber search distinction -> DerivedMSpace transition initial
  preserves_admissibility : forall member,
    admissibleHistory (toHistory member)

/-- The reverse direction is a different contract and is not inferred. -/
structure HistoryToMSpaceFiberAdapter
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (distinction : TrajectoryDistinction K)
    {State : Type uState}
    {Input : Type uInput}
    (transition : State -> Input -> State -> Prop)
    (initial : State)
    (admissibleHistory : DerivedMSpace transition initial -> Prop) where
  toLift : (point : DerivedMSpace transition initial) ->
    admissibleHistory point -> MSpaceFiber search distinction

/-- Two-sided equivalence is additional data, not a consequence of shared naming. -/
structure MSpaceFiberHistoryEquivalence
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (distinction : TrajectoryDistinction K)
    {State : Type uState}
    {Input : Type uInput}
    (transition : State -> Input -> State -> Prop)
    (initial : State) where
  toHistory : MSpaceFiber search distinction -> DerivedMSpace transition initial
  toLift : DerivedMSpace transition initial -> MSpaceFiber search distinction
  left_inverse : forall member, toLift (toHistory member) = member
  right_inverse : forall point, toHistory (toLift point) = point

/-- A two-sided bridge is exactly an equivalence of the two declared types. -/
def MSpaceFiberHistoryEquivalence.toEquiv
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {distinction : TrajectoryDistinction K}
    {State : Type uState}
    {Input : Type uInput}
    {transition : State -> Input -> State -> Prop}
    {initial : State}
    (bridge : MSpaceFiberHistoryEquivalence search distinction transition initial) :
    MSpaceFiber search distinction ≃ DerivedMSpace transition initial where
  toFun := bridge.toHistory
  invFun := bridge.toLift
  left_inv := bridge.left_inverse
  right_inv := bridge.right_inverse

/-!
## Countermodels to semantic collapse
-/

def zeroUnitHistory :
    OpenHistory (fun (_ : Unit) (_ : Unit) (_ : Unit) => False) () () :=
  .start

def zeroUnitDerivedPoint :
    DerivedMSpace (fun (_ : Unit) (_ : Unit) (_ : Unit) => False) () :=
  ⟨(), zeroUnitHistory⟩

/-- Finite M is inhabited even when no infinite productive history exists. -/
theorem finiteDerivedMSpace_does_not_imply_omegaHistory :
    Nonempty
        (DerivedMSpace
          (fun (_ : Unit) (_ : Unit) (_ : Unit) => False) ()) /\
      IsEmpty
        (OmegaOpenHistory
          (fun (_ : Unit) (_ : Unit) (_ : Unit) => False) ()) := by
  constructor
  · exact ⟨zeroUnitDerivedPoint⟩
  · constructor
    intro history
    exact history.productive 0

def allBoolBoundaries (_ : List Unit) (_ : Bool) : Prop := True

def falseBoundaryPoint :
    BoundaryHistoryMSpace
      (fun (_ : Unit) (_ : Unit) (_ : Unit) => False)
      () Bool allBoolBoundaries where
  point := zeroUnitDerivedPoint
  boundary := false
  compatible_with_history := trivial

def trueBoundaryPoint :
    BoundaryHistoryMSpace
      (fun (_ : Unit) (_ : Unit) (_ : Unit) => False)
      () Bool allBoolBoundaries where
  point := zeroUnitDerivedPoint
  boundary := true
  compatible_with_history := trivial

/-- Forgetting boundary-history data is non-injective. -/
theorem boundaryHistory_forgetting_not_injective :
    Not (Function.Injective
      (@BoundaryHistoryMSpace.forget
        Unit Unit
        (fun (_ : Unit) (_ : Unit) (_ : Unit) => False)
        () Bool allBoolBoundaries)) := by
  intro injective
  have equalPoints : falseBoundaryPoint = trueBoundaryPoint :=
    injective rfl
  have equalBoundaries := congrArg BoundaryHistoryMSpace.boundary equalPoints
  exact Bool.false_ne_true equalBoundaries

/-- Viability can remove a reachable finite endpoint; forgetting need not be onto. -/
theorem nonviable_endpoint_has_no_viable_preimage
    {State : Type uState}
    {Input : Type uInput}
    {transition : State -> Input -> State -> Prop}
    {initial : State}
    {viable : State -> Prop}
    (point : DerivedMSpace transition initial)
    (notViable : Not (viable point.1)) :
    Not (exists viablePoint : ViableMSpace transition initial viable,
      viablePoint.forget = point) := by
  rintro ⟨viablePoint, samePoint⟩
  have endpointViable := viablePoint.allStates.endpoint
  change viablePoint.point = point at samePoint
  rw [samePoint] at endpointViable
  exact notViable endpointViable

/-!
Consequently:

* `MSpaceFiber` is a scoped lift-search fiber;
* `DerivedMSpace` is a finite generated history space;
* viability and boundary dependence are strict typed enrichments;
* omega histories are not implied by finite histories;
* finite stochastic paths retain exact weights from a specified experiment;
* ExactMSpace and LineageMSpace remain the separate identity-specialized
  aliases defined in `DynamicObjectIdentity`; and
* raw carrier adapters are not semantic translations; a semantic bridge must
  satisfy transition, initial, endpoint, input-trace, and observation laws;
* step inclusion constructs one such evidence-bearing bridge for finite
  generated histories, while a bare point map can fail to extend; and
* historical M has no Lean carrier here and remains a hypothesis until a
  source supplies a presentation plus an evidence-bearing translation.
-/

end OCKIndividuationMSpaceComposition
