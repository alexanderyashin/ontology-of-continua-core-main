import OCKIndividuationMSpaceComposition.CausalObservationalBridge
import OCKIndividuationMSpaceComposition.StrongestUniversalization
import OCKIndividuationMSpaceComposition.DerivedMSpace
import OCKIndividuationMSpaceComposition.RecursiveComposition
import OCKIndividuationMSpaceComposition.OperatorTransport

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe
  uMechanism uIntervention uOutcome uPresentation uExperiment
  uExperimentOutcome uInput uProvenance uTime uScale

/-!
# Component-presentation reconstruction (legacy pre-split synthesis)

This preserved module reconstructs a causal component carrier from
presentations.  Its `Token` is a component-realization quotient, not
whole-object temporal identity.  The canonical whole-object identity theory
is `DynamicObjectIdentity`; no theorem here may be used to equate a
realization fibre with an object token.

The component construction does not start from an arbitrary admissible set.
It starts with independently typed causal contrasts and a non-port root;
the carrier is their least generated kernel.  A presentation graph is linked
to that carrier by local root preservation, edge soundness and path lifting,
from which exact global carrier coverage is derived.  Experiments then bound
operational identity between forced evidence and allowed indistinguishability.

An `IdentifiedDynamicObject` is a legacy name for this proof-carrying component
synthesis.  It requires its presentation-equivalence bounds to converge and
exact compatibility
between observational identity and causal realization on reachable
presentations, provenance/persistence/scale qualification, an open dynamics,
and a realization-preserving composition law.  These requirements are the
portable mechanics.  Their domain witnesses remain empirical obligations.
-/

/-- Reachability on the presentation graph, exposed as the evidence relation. -/
def PresentationMutualReachability
    {Presentation : Type uPresentation}
    (edge : Presentation → Presentation → Prop) :
    BinaryRelation Presentation :=
  fun first second =>
    ReachableFrom edge first second ∧ ReachableFrom edge second first

/-- Generic finite reachability is transitive. -/
theorem reachableFrom_trans
    {Presentation : Type uPresentation}
    {edge : Presentation → Presentation → Prop}
    {first middle last : Presentation}
    (firstMiddle : ReachableFrom edge first middle)
    (middleLast : ReachableFrom edge middle last) :
    ReachableFrom edge first last := by
  induction middleLast with
  | root => exact firstMiddle
  | step previous nextEdge inductionHypothesis =>
      exact .step inductionHypothesis nextEdge

/-- Presentation mutual reachability is an equivalence relation. -/
theorem presentationMutualReachability_equivalence
    {Presentation : Type uPresentation}
    (edge : Presentation → Presentation → Prop) :
    Equivalence (PresentationMutualReachability edge) := by
  constructor
  · intro presentation
    exact ⟨.root, .root⟩
  · intro first second related
    exact ⟨related.2, related.1⟩
  · intro first second third firstSecond secondThird
    exact ⟨reachableFrom_trans firstSecond.1 secondThird.1,
      reachableFrom_trans secondThird.2 firstSecond.2⟩

/-- Therefore equivalence closure adds no extra presentation pairs. -/
theorem forcedIdentity_presentationMutualReachability
    {Presentation : Type uPresentation}
    (edge : Presentation → Presentation → Prop) :
    ForcedIdentity (PresentationMutualReachability edge) =
      PresentationMutualReachability edge := by
  apply forcedIdentity_eq_of_equivalence
  · intro presentation
    exact ⟨.root, .root⟩
  · intro first second related
    exact ⟨related.2, related.1⟩
  · intro first second third firstSecond secondThird
    exact ⟨reachableFrom_trans firstSecond.1 secondThird.1,
      reachableFrom_trans secondThird.2 firstSecond.2⟩

/--
The causal realization must coincide exactly with the converged operational
identity on the reachable presentation carrier.  This is stronger than merely
placing a carrier and a token in the same record.
-/
def IdentityRealizationExact
    {Mechanism : Type uMechanism}
    {Presentation : Type uPresentation}
    {causalEdge : Mechanism → Mechanism → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Mechanism}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot)
    (evidence : BinaryRelation Presentation) : Prop :=
  ∀ left right :
      ReachablePresentationCarrier presentationEdge presentationRoot,
    ForcedIdentity evidence left.1 right.1 ↔
      bridge.realize left.1 = bridge.realize right.1

/-- A qualified, identified, dynamical and compositional object witness. -/
structure IdentifiedDynamicObject
    (Mechanism : Type uMechanism)
    (Intervention : Type uIntervention)
    (Outcome : Type uOutcome)
    (Presentation : Type uPresentation)
    (Experiment : Type uExperiment)
    (ExperimentOutcome : Type uExperimentOutcome)
    (Input : Type uInput)
    (Provenance : Type uProvenance)
    (Time : Type uTime)
    (Scale : Type uScale) where
  causalModel : ActiveConstraintModel Mechanism Intervention Outcome
  root : Mechanism
  presentationEdge : Presentation → Presentation → Prop
  presentationRoot : Presentation
  bridge : CausalObservationalBridge
    (InternalDependency causalModel) presentationEdge root presentationRoot
  evidence : BinaryRelation Presentation
  experimentLaw : Presentation → Experiment → ExperimentOutcome
  identityConverges :
    ForcedIdentity evidence = AllowedIdentity experimentLaw
  identityRealizationExact : IdentityRealizationExact bridge evidence
  presentationSeedNontrivial :
    NontrivialForcedClass evidence presentationRoot
  formedBy : Mechanism → Provenance → Prop
  continuesAt : Mechanism → Time → Prop
  robustAtScale : (Mechanism → Prop) → Prop
  provenance : Provenance
  qualification : KernelQualification causalModel Provenance Time
    formedBy continuesAt robustAtScale root provenance
  openStep : Mechanism → Input → Mechanism → Prop
  openStep_preserves_carrier : ∀ ⦃current input next⦄,
    GeneratedKernel causalModel root current →
    openStep current input next →
    GeneratedKernel causalModel root next
  realizesChildren : RealizesChildren Mechanism
  compositionRespectsCarrier : ∀ {children parent},
    realizesChildren children parent →
    GeneratedKernel causalModel root parent →
    ∀ child ∈ children, GeneratedKernel causalModel root child

/-- The object carrier is derived, not an input field. -/
abbrev IdentifiedDynamicObject.Carrier
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {Presentation : Type uPresentation}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {Input : Type uInput}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {Scale : Type uScale}
    (object : IdentifiedDynamicObject Mechanism Intervention Outcome
      Presentation Experiment ExperimentOutcome Input Provenance Time Scale) :=
  {mechanism : Mechanism //
    GeneratedKernel object.causalModel object.root mechanism}

/-- The operational token type is derived from the evidence relation. -/
abbrev IdentifiedDynamicObject.Token
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {Presentation : Type uPresentation}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {Input : Type uInput}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {Scale : Type uScale}
    (object : IdentifiedDynamicObject Mechanism Intervention Outcome
      Presentation Experiment ExperimentOutcome Input Provenance Time Scale) :=
  OperationalToken object.evidence

/-- The realized root is always in the independently generated carrier. -/
theorem IdentifiedDynamicObject.root_in_carrier
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {Presentation : Type uPresentation}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {Input : Type uInput}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {Scale : Type uScale}
    (object : IdentifiedDynamicObject Mechanism Intervention Outcome
      Presentation Experiment ExperimentOutcome Input Provenance Time Scale) :
    GeneratedKernel object.causalModel object.root object.root :=
  .ofRoot

/-- Local bridge laws derive exact global realization of the carrier. -/
theorem IdentifiedDynamicObject.exact_carrier_realization
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {Presentation : Type uPresentation}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {Input : Type uInput}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {Scale : Type uScale}
    (object : IdentifiedDynamicObject Mechanism Intervention Outcome
      Presentation Experiment ExperimentOutcome Input Provenance Time Scale)
    (mechanism : Mechanism) :
    GeneratedKernel object.causalModel object.root mechanism ↔
      ∃ presentation,
        ReachableFrom object.presentationEdge object.presentationRoot
          presentation ∧
        object.bridge.realize presentation = mechanism :=
  object.bridge.exact_generatedKernel_image mechanism

/-- The realization-kernel quotient is in bijection with the causal carrier. -/
theorem IdentifiedDynamicObject.presentationQuotient_bijective_carrier
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {Presentation : Type uPresentation}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {Input : Type uInput}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {Scale : Type uScale}
    (object : IdentifiedDynamicObject Mechanism Intervention Outcome
      Presentation Experiment ExperimentOutcome Input Provenance Time Scale) :
    Function.Bijective object.bridge.quotientToCausalCarrier :=
  object.bridge.quotientToCausalCarrier_bijective

/-- The operational identity relation exists uniquely. -/
theorem IdentifiedDynamicObject.identity_exists_unique
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {Presentation : Type uPresentation}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {Input : Type uInput}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {Scale : Type uScale}
    (object : IdentifiedDynamicObject Mechanism Intervention Outcome
      Presentation Experiment ExperimentOutcome Input Provenance Time Scale) :
    ∃! relation,
      AdmissibleIdentityRelation object.evidence object.experimentLaw relation :=
  converged_identity_bounds_exist_unique
    object.evidence object.experimentLaw object.identityConverges

/-- A derived M-space path starting in the carrier stays inside the carrier. -/
theorem IdentifiedDynamicObject.history_endpoint_in_carrier
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {Presentation : Type uPresentation}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {Input : Type uInput}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {Scale : Type uScale}
    (object : IdentifiedDynamicObject Mechanism Intervention Outcome
      Presentation Experiment ExperimentOutcome Input Provenance Time Scale)
    {endpoint : Mechanism}
    (history : OpenHistory object.openStep object.root endpoint) :
    GeneratedKernel object.causalModel object.root endpoint := by
  exact history.invariant
    (invariant := GeneratedKernel object.causalModel object.root)
    object.root_in_carrier (by
      intro current next input currentInCarrier step
      exact object.openStep_preserves_carrier currentInCarrier step)

/--
All finite open histories form a derived M-space downstream of this object and
its open transition law.
-/
abbrev IdentifiedDynamicObject.MSpace
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {Presentation : Type uPresentation}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {Input : Type uInput}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {Scale : Type uScale}
    (object : IdentifiedDynamicObject Mechanism Intervention Outcome
      Presentation Experiment ExperimentOutcome Input Provenance Time Scale) :=
  DerivedMSpace object.openStep object.root

/-- Every local composition of a carrier parent consists only of carrier children. -/
theorem IdentifiedDynamicObject.local_children_in_carrier
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {Presentation : Type uPresentation}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {Input : Type uInput}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {Scale : Type uScale}
    (object : IdentifiedDynamicObject Mechanism Intervention Outcome
      Presentation Experiment ExperimentOutcome Input Provenance Time Scale)
    {children : List Mechanism}
    {parent : Mechanism}
    (realizes : object.realizesChildren children parent)
    (parentInCarrier :
      GeneratedKernel object.causalModel object.root parent) :
    ∀ child ∈ children,
      GeneratedKernel object.causalModel object.root child :=
  object.compositionRespectsCarrier realizes parentInCarrier

/--
Every terminal occurrence at every finite decomposition depth of a carrier
parent remains in the same generated causal carrier.  The theorem transports
carrier membership only; it deliberately does not identify parent and child
tokens or choose one decomposition among several valid ones.
-/
theorem IdentifiedDynamicObject.multiLevel_children_in_carrier
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {Presentation : Type uPresentation}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {Input : Type uInput}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {Scale : Type uScale}
    (object : IdentifiedDynamicObject Mechanism Intervention Outcome
      Presentation Experiment ExperimentOutcome Input Provenance Time Scale)
    {parent : Mechanism}
    {terminal : List Mechanism}
    (decomposition :
      MultiLevelDecomposition object.realizesChildren [parent] terminal)
    (parentInCarrier :
      GeneratedKernel object.causalModel object.root parent) :
    ∀ child ∈ terminal,
      GeneratedKernel object.causalModel object.root child := by
  exact multiLevelDecomposition_from_parent_preserves
    (realizes := object.realizesChildren)
    (invariant := GeneratedKernel object.causalModel object.root)
    object.compositionRespectsCarrier decomposition parentInCarrier

/--
The synthesis theorem packages the strongest consequences without conflating
their types: causal carrier, presentation quotient, identity, derived history
space, and local composition compatibility are all obtained together.
-/
theorem identifiedDynamicObject_full_synthesis
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {Presentation : Type uPresentation}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {Input : Type uInput}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {Scale : Type uScale}
    (object : IdentifiedDynamicObject Mechanism Intervention Outcome
      Presentation Experiment ExperimentOutcome Input Provenance Time Scale) :
    (∀ mechanism,
      GeneratedKernel object.causalModel object.root mechanism ↔
        ∃ presentation,
          ReachableFrom object.presentationEdge object.presentationRoot
            presentation ∧
          object.bridge.realize presentation = mechanism) ∧
    Function.Bijective object.bridge.quotientToCausalCarrier ∧
    (∃! relation,
      AdmissibleIdentityRelation object.evidence object.experimentLaw relation) ∧
    (∀ {endpoint},
      OpenHistory object.openStep object.root endpoint →
        GeneratedKernel object.causalModel object.root endpoint) ∧
    (∀ {parent terminal},
      MultiLevelDecomposition object.realizesChildren [parent] terminal →
      GeneratedKernel object.causalModel object.root parent →
      ∀ child ∈ terminal,
        GeneratedKernel object.causalModel object.root child) :=
  ⟨object.exact_carrier_realization,
    object.presentationQuotient_bijective_carrier,
    object.identity_exists_unique,
    fun history => object.history_endpoint_in_carrier history,
    fun decomposition parentInCarrier =>
      object.multiLevel_children_in_carrier decomposition parentInCarrier⟩

end OCKIndividuationMSpaceComposition
