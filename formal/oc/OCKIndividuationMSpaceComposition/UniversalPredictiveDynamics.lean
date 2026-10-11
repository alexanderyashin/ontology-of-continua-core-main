import OCKIndividuationMSpaceComposition.EnterpriseDynamicsBridge
import OCKIndividuationMSpaceComposition.OperatorTransport

namespace OCKIndividuationMSpaceComposition

/-!
# Universal predictive dynamics

This module is a conservative predictive layer over the existing OC transition,
observation, continuation, and operator corpus.  It does not identify an ontic
state with an observation or encoding, and it does not manufacture a
probability law from a possibility relation.

The central object is a typed transition system with inspectable admissibility
layers.  A domain projection is a forward simulation.  Exact transfer requires
the additional lifting contract stated below; a lossy projection cannot support
exact prediction when one fiber contains behaviorally different states.
-/

universe uState uAction uDomainState uDomainAction uFeature

/-- The admissibility relations are deliberately separated. -/
structure LayeredAdmissibility (State : Type uState) where
  semantic : State → Prop
  epistemic : State → Prop
  observable : State → Prop
  operational : State → Prop
  governance : State → Prop

/-- A state is fully admitted only when every declared layer admits it. -/
def LayeredAdmissibility.FullyAdmitted
    {State : Type uState} (layers : LayeredAdmissibility State) (state : State) : Prop :=
  layers.semantic state ∧
  layers.epistemic state ∧
  layers.observable state ∧
  layers.operational state ∧
  layers.governance state

/-- Universal carrier for bounded predictive questions. -/
structure PredictiveSystem where
  State : Type uState
  Action : Type uAction
  step : State → Action → State → Prop
  layers : LayeredAdmissibility State

/-- Exact finite path length.  This keeps the action witness at every step. -/
inductive ReachExactly (system : PredictiveSystem) (initial : system.State) :
    Nat → system.State → Prop
  | root : ReachExactly system initial 0 initial
  | tail {depth : Nat} {current next : system.State} :
      ReachExactly system initial depth current →
      (action : system.Action) →
      system.step current action next →
      ReachExactly system initial (depth + 1) next

/-- Reachability by some witnessed path no longer than the declared horizon. -/
def ReachWithin (system : PredictiveSystem) (initial : system.State)
    (horizon : Nat) (target : system.State) : Prop :=
  ∃ depth, depth ≤ horizon ∧ ReachExactly system initial depth target

/-- Ontically reachable and admitted by all five declared layers. -/
def TargetFuture (system : PredictiveSystem) (initial : system.State)
    (horizon : Nat) (target : system.State) : Prop :=
  ReachWithin system initial horizon target ∧
  system.layers.FullyAdmitted target

/-- A generator is sound when it never accepts a target outside the bounded
target future. -/
def GeneratorSound (system : PredictiveSystem) (initial : system.State)
    (horizon : Nat) (generated : system.State → Prop) : Prop :=
  ∀ target, generated target → TargetFuture system initial horizon target

/-- Completeness is always relative to one system, initial state, horizon, and
operator family. -/
def GeneratorComplete (system : PredictiveSystem) (initial : system.State)
    (horizon : Nat) (generated : system.State → Prop) : Prop :=
  ∀ target, TargetFuture system initial horizon target → generated target

theorem generated_necessary_feature_sound
    (system : PredictiveSystem) (initial : system.State) (horizon : Nat)
    (generated feature : system.State → Prop)
    (complete : GeneratorComplete system initial horizon generated)
    (allGenerated : ∀ target, generated target → feature target) :
    ∀ target, TargetFuture system initial horizon target → feature target := by
  intro target targetFuture
  exact allGenerated target (complete target targetFuture)

theorem generated_exclusion_sound
    (system : PredictiveSystem) (initial : system.State) (horizon : Nat)
    (generated : system.State → Prop)
    (complete : GeneratorComplete system initial horizon generated) :
    ∀ target, ¬ generated target → ¬ TargetFuture system initial horizon target := by
  intro target notGenerated targetFuture
  exact notGenerated (complete target targetFuture)

theorem sound_complete_generator_exact
    (system : PredictiveSystem) (initial : system.State) (horizon : Nat)
    (generated : system.State → Prop)
    (sound : GeneratorSound system initial horizon generated)
    (complete : GeneratorComplete system initial horizon generated) :
    generated = TargetFuture system initial horizon := by
  funext target
  apply propext
  exact ⟨sound target, complete target⟩

/-- A domain projection is a forward simulation plus preservation of the five
admissibility layers.  This is the minimum contract for sound transfer. -/
structure DomainProjection (source target : PredictiveSystem) where
  mapState : source.State → target.State
  mapAction : source.Action → target.Action
  step_sound : ∀ {left right action},
    source.step left action right →
    target.step (mapState left) (mapAction action) (mapState right)
  admitted_sound : ∀ {state},
    source.layers.FullyAdmitted state →
    target.layers.FullyAdmitted (mapState state)

def DomainProjection.identity (system : PredictiveSystem) :
    DomainProjection system system where
  mapState := id
  mapAction := id
  step_sound := by intro left right action step; exact step
  admitted_sound := by intro state admitted; exact admitted

def DomainProjection.comp
    {first middle last : PredictiveSystem}
    (left : DomainProjection first middle)
    (right : DomainProjection middle last) :
    DomainProjection first last where
  mapState := right.mapState ∘ left.mapState
  mapAction := right.mapAction ∘ left.mapAction
  step_sound := by
    intro source target action step
    exact right.step_sound (left.step_sound step)
  admitted_sound := by
    intro state admitted
    exact right.admitted_sound (left.admitted_sound admitted)

theorem DomainProjection.map_reachExactly
    {source target : PredictiveSystem}
    (projection : DomainProjection source target)
    {initial endpoint : source.State} {depth : Nat}
    (reachable : ReachExactly source initial depth endpoint) :
    ReachExactly target (projection.mapState initial) depth
      (projection.mapState endpoint) := by
  induction reachable with
  | root => exact ReachExactly.root
  | tail reachable action step inductionHypothesis =>
      exact ReachExactly.tail inductionHypothesis
        (projection.mapAction action) (projection.step_sound step)

theorem DomainProjection.map_reachWithin
    {source target : PredictiveSystem}
    (projection : DomainProjection source target)
    {initial endpoint : source.State} {horizon : Nat}
    (reachable : ReachWithin source initial horizon endpoint) :
    ReachWithin target (projection.mapState initial) horizon
      (projection.mapState endpoint) := by
  rcases reachable with ⟨depth, bounded, path⟩
  exact ⟨depth, bounded, projection.map_reachExactly path⟩

theorem DomainProjection.map_targetFuture
    {source target : PredictiveSystem}
    (projection : DomainProjection source target)
    {initial endpoint : source.State} {horizon : Nat}
    (future : TargetFuture source initial horizon endpoint) :
    TargetFuture target (projection.mapState initial) horizon
      (projection.mapState endpoint) :=
  ⟨projection.map_reachWithin future.1, projection.admitted_sound future.2⟩

/-- Exact domain transfer adds a target-future lifting law.  Mere simulation is
not enough for necessity or completeness claims in the reverse direction. -/
structure ExactDomainProjection (source target : PredictiveSystem)
    extends DomainProjection source target where
  lift_target : ∀ {initial : source.State} {horizon : Nat} {domainTarget : target.State},
    TargetFuture target (mapState initial) horizon domainTarget →
    ∃ sourceTarget,
      TargetFuture source initial horizon sourceTarget ∧
      mapState sourceTarget = domainTarget

theorem domain_necessary_feature_pulls_back
    {source target : PredictiveSystem}
    (projection : DomainProjection source target)
    (domainFeature : target.State → Prop)
    {initial : source.State} {horizon : Nat}
    (necessary : ∀ domainTarget,
      TargetFuture target (projection.mapState initial) horizon domainTarget →
      domainFeature domainTarget) :
    ∀ sourceTarget, TargetFuture source initial horizon sourceTarget →
      domainFeature (projection.mapState sourceTarget) := by
  intro sourceTarget sourceFuture
  exact necessary (projection.mapState sourceTarget)
    (projection.map_targetFuture sourceFuture)

theorem source_necessary_feature_descends_of_exact
    {source target : PredictiveSystem}
    (projection : ExactDomainProjection source target)
    (sourceFeature : source.State → Prop) (domainFeature : target.State → Prop)
    (fiberInvariant : ∀ sourceState,
      domainFeature (projection.mapState sourceState) ↔ sourceFeature sourceState)
    {initial : source.State} {horizon : Nat}
    (necessary : ∀ sourceTarget,
      TargetFuture source initial horizon sourceTarget → sourceFeature sourceTarget) :
    ∀ domainTarget,
      TargetFuture target (projection.mapState initial) horizon domainTarget →
      domainFeature domainTarget := by
  intro domainTarget domainFuture
  rcases projection.lift_target domainFuture with
    ⟨sourceTarget, sourceFuture, mapsToDomain⟩
  rw [← mapsToDomain]
  exact (fiberInvariant sourceTarget).2 (necessary sourceTarget sourceFuture)

/-- A conservative frame extension embeds the old transition system without
changing old transitions or old admissibility judgements. -/
structure ConservativeFrameExtension (oldFrame newFrame : PredictiveSystem) where
  embedState : oldFrame.State → newFrame.State
  embedAction : oldFrame.Action → newFrame.Action
  step_iff : ∀ {left right action},
    newFrame.step (embedState left) (embedAction action) (embedState right) ↔
    oldFrame.step left action right
  admitted_iff : ∀ {state},
    newFrame.layers.FullyAdmitted (embedState state) ↔
    oldFrame.layers.FullyAdmitted state

def ConservativeFrameExtension.toDomainProjection
    {oldFrame newFrame : PredictiveSystem}
    (extension : ConservativeFrameExtension oldFrame newFrame) :
    DomainProjection oldFrame newFrame where
  mapState := extension.embedState
  mapAction := extension.embedAction
  step_sound := by intro left right action step; exact extension.step_iff.mpr step
  admitted_sound := by intro state admitted; exact extension.admitted_iff.mpr admitted

inductive ContinuationAlternative (sameState extendedState : Type) where
  | sameFrame : sameState → ContinuationAlternative sameState extendedState
  | extendedFrame : extendedState → ContinuationAlternative sameState extendedState

def AlternativeAdmissible
    (sameFrame extendedFrame : PredictiveSystem)
    (sameInitial : sameFrame.State) (extendedInitial : extendedFrame.State)
    (horizon : Nat) :
    ContinuationAlternative sameFrame.State extendedFrame.State → Prop
  | .sameFrame state => TargetFuture sameFrame sameInitial horizon state
  | .extendedFrame state => TargetFuture extendedFrame extendedInitial horizon state

/-- The sound content of “same-frame exhaustion forces extension”.  It says
only that an admitted continuation in the declared two-class universe is in
the extension class; it does not conjure an extension or prove search
completeness. -/
theorem same_frame_exhaustion_forces_extension
    (sameFrame extendedFrame : PredictiveSystem)
    (sameInitial : sameFrame.State) (extendedInitial : extendedFrame.State)
    (horizon : Nat)
    (sameExhausted : ∀ state,
      ¬ TargetFuture sameFrame sameInitial horizon state)
    (alternative : ContinuationAlternative sameFrame.State extendedFrame.State)
    (admitted : AlternativeAdmissible sameFrame extendedFrame
      sameInitial extendedInitial horizon alternative) :
    ∃ extendedState, alternative = .extendedFrame extendedState := by
  cases alternative with
  | sameFrame state => exact False.elim (sameExhausted state admitted)
  | extendedFrame state => exact ⟨state, rfl⟩

/-- Observation aliasing is the universal obstruction already exposed by the
enterprise bridge. -/
theorem observation_collision_no_exact_predictor
    {World Observation Outcome : Type}
    (observe : World → Observation) (outcome : World → Outcome)
    (left right : World)
    (sameObservation : observe left = observe right)
    (differentOutcome : outcome left ≠ outcome right) :
    ¬ ∃ predictor : Observation → Outcome,
      ∀ world, predictor (observe world) = outcome world :=
  collapsed_observation_no_exact_predictor
    observe outcome left right sameObservation differentOutcome

/-- Quantitative two-world bound: on an equally weighted aliased pair, every
point predictor has accuracy at most one half. -/
theorem observation_collision_pair_correct_count_le_one
    {World Observation Outcome : Type} [DecidableEq Outcome]
    (observe : World → Observation) (outcome : World → Outcome)
    (predictor : Observation → Outcome) (left right : World)
    (sameObservation : observe left = observe right)
    (differentOutcome : outcome left ≠ outcome right) :
    ZeroOneCorrect (predictor (observe left)) (outcome left) +
        ZeroOneCorrect (predictor (observe right)) (outcome right) ≤ 1 :=
  omitted_intervention_pair_correct_count_le_one
    observe outcome predictor left right sameObservation differentOutcome

/-- Possibility support alone cannot determine quantitative transition
weights, hence cannot justify probabilities. -/
theorem possibility_support_does_not_determine_weights :
    ¬ Function.Injective (@weightedSupport Unit Bool) :=
  weightedSupport_not_injective

/-- The action-conditioned enterprise result is an instance of the universal
system: the action declares a candidate next outcome and the step relation
requires conformance. -/
def ActionConditionedPredictiveSystem (Outcome : Type) : PredictiveSystem where
  State := Outcome
  Action := DeclaredIntervention Outcome
  step := fun _ intervention next => InterventionConformant intervention next
  layers := {
    semantic := fun _ => True
    epistemic := fun _ => True
    observable := fun _ => True
    operational := fun _ => True
    governance := fun _ => True
  }

theorem action_conditioned_system_step_is_exact
    {Outcome : Type} (current next : Outcome)
    (intervention : DeclaredIntervention Outcome)
    (step : (ActionConditionedPredictiveSystem Outcome).step
      current intervention next) :
    ActionConditionedPredictor intervention = next :=
  action_conditioned_prediction_exact_when_conformant intervention next step

end OCKIndividuationMSpaceComposition
