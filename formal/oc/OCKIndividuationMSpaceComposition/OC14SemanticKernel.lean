import Mathlib.Probability.ProbabilityMassFunction.Constructions
import OCKIndividuationMSpaceComposition.PathDependentContinuation
import OCKIndividuationMSpaceComposition.TaskOpticModelClassBridge
import OCKIndividuationMSpaceComposition.SemanticPredictionContract

namespace OCKIndividuationMSpaceComposition

universe uSystem uEnvironment uInput uObservation uWorld uModel

/-!
# OC 1.4 canonical semantic kernel

This module adds only the semantic primitives missing from the existing typed
continuation, optic, identity and prediction kernels.  A world configuration
separates the system from its environment.  An event is a witnessed world
transition, not an observation record.  A stochastic observation channel maps
worlds to probability mass functions; deterministic optics embed as degenerate
channels.  Physical and epistemic continuation spaces remain different typed
sets and respond to different revision operations.

Existing canonical surfaces are reused rather than duplicated:

* `ContinuationContext`, `ContinuationWitness`, `Continues` and
  `SameObjectClaim` carry continuation and contextual identity;
* `TaskConditionedOptic` and `TaskContract` carry optic/task semantics;
* `OperationalSemanticForecastContract` carries prediction meaning and
  origin-time information availability;
* `CausalAdmissionPremises` remains the independent causal-evidence gate.
-/

/-- The ontic configuration keeps the system and its environment as separate
coordinates. -/
structure WorldConfiguration
    (System : Type uSystem) (Environment : Type uEnvironment) where
  system : System
  environment : Environment
  deriving DecidableEq

/-- An event is a transition witness between two world configurations under a
declared input.  Observation is deliberately absent from this structure. -/
structure WorldEvent
    {World : Type uWorld} {Input : Type uInput}
    (transition : World → Input → World → Prop) where
  source : World
  input : Input
  target : World
  valid : transition source input target

/-- Discrete stochastic observation channel. -/
structure StochasticObservationChannel
    (World : Type uWorld) (Observation : Type uObservation) where
  observe : World → PMF Observation

/-- Every deterministic observation map embeds as a degenerate stochastic
channel. -/
noncomputable def deterministicObservationChannel
    {World : Type uWorld} {Observation : Type uObservation}
    (observe : World → Observation) :
    StochasticObservationChannel World Observation where
  observe := fun world => PMF.pure (observe world)

/-- Equality of observable laws under one channel. -/
def ObservationallyAliased
    {World : Type uWorld} {Observation : Type uObservation}
    (channel : StochasticObservationChannel World Observation)
    (left right : World) : Prop :=
  channel.observe left = channel.observe right

/-! ## System reality is not observation -/

private abbrev HiddenWorld := WorldConfiguration Bool Unit

private def hiddenBefore : HiddenWorld := ⟨false, ()⟩
private def hiddenAfter : HiddenWorld := ⟨true, ()⟩
private def hiddenTransition (_source : HiddenWorld) (_input : Unit)
    (_target : HiddenWorld) : Prop := True
private def hiddenObservation (_world : HiddenWorld) : Unit := ()

/-- Exact hidden-event witness: a valid event changes the world while the
declared observation remains unchanged. -/
theorem world_event_can_be_observationally_silent :
    ∃ event : WorldEvent hiddenTransition,
      event.source ≠ event.target ∧
        hiddenObservation event.source = hiddenObservation event.target := by
  let event : WorldEvent hiddenTransition :=
    { source := hiddenBefore
      input := ()
      target := hiddenAfter
      valid := trivial }
  refine ⟨event, ?_, rfl⟩
  intro equalWorlds
  have equalSystems := congrArg WorldConfiguration.system equalWorlds
  exact Bool.noConfusion equalSystems

/-- Equal observation laws under one channel do not imply equal world states.
The constant deterministic channel aliases two distinct Boolean worlds. -/
theorem observational_alias_does_not_imply_world_equality :
    ∃ channel : StochasticObservationChannel Bool Unit,
      ObservationallyAliased channel false true ∧ false ≠ true := by
  refine ⟨deterministicObservationChannel (fun _ : Bool => ()), ?_, by decide⟩
  rfl

/-- A deterministic task optic has a canonical stochastic-channel view; no
new observation semantics are invented by this adapter. -/
noncomputable def TaskConditionedOptic.toStochasticObservationChannel
    {World : Type uWorld} (optic : TaskConditionedOptic World) :
    StochasticObservationChannel World optic.Observation :=
  deterministicObservationChannel optic.observe

/-! ## Canonical physical and epistemic continuation spaces -/

/-- One-step physical continuations admitted by the declared world transition
law.  Longer paths remain represented by `DerivedMSpace` and
`ContinuationWitness`. -/
def PhysicalContinuationSet
    {World : Type uWorld} {Input : Type uInput}
    (transition : World → Input → World → Prop) (current : World) : Set World :=
  {next | ∃ input, transition current input next}

/-- Worlds realized by prior-admitted models whose predictions are compatible
with the actual observation under the declared optic. -/
def EpistemicContinuationSet
    {World : Type uWorld} {Model : Type uModel}
    (optic : TaskConditionedOptic World)
    (modelWorld : Model → World)
    (priorAdmits : Model → Prop)
    (actual : World) : Set World :=
  {world | ∃ model,
    OpticPosteriorAdmits optic modelWorld priorAdmits actual model ∧
      modelWorld model = world}

/-- Optic revision and model-class revision have opposite monotonic directions
in the canonical epistemic M-space.  Refining the optic contracts the space. -/
theorem optic_refinement_contracts_epistemic_continuation_set
    {World : Type uWorld} {Model : Type uModel}
    {coarse fine : TaskConditionedOptic World}
    (refinement : OpticRefinement coarse fine)
    (modelWorld : Model → World)
    (priorAdmits : Model → Prop)
    (actual : World) :
    EpistemicContinuationSet fine modelWorld priorAdmits actual ⊆
      EpistemicContinuationSet coarse modelWorld priorAdmits actual := by
  rintro world ⟨model, fineAdmitted, realizes⟩
  exact ⟨model,
    optic_refinement_contracts_admitted_model_class refinement
      modelWorld priorAdmits actual model fineAdmitted,
    realizes⟩

/-- At a fixed optic and observation, extending the prior model class expands
the epistemic continuation set. -/
theorem model_class_extension_expands_epistemic_continuation_set
    {World : Type uWorld} {Model : Type uModel}
    (optic : TaskConditionedOptic World)
    (modelWorld : Model → World)
    (small large : Model → Prop)
    (classExtends : ∀ model, small model → large model)
    (actual : World) :
    EpistemicContinuationSet optic modelWorld small actual ⊆
      EpistemicContinuationSet optic modelWorld large actual := by
  rintro world ⟨model, smallAdmitted, realizes⟩
  exact ⟨model, ⟨classExtends model smallAdmitted.1, smallAdmitted.2⟩, realizes⟩

end OCKIndividuationMSpaceComposition
