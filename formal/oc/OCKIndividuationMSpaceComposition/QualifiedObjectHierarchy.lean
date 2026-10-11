import OCKIndividuationMSpaceComposition.ConstraintGeneratedObject
import OCKIndividuationMSpaceComposition.DerivedMSpace

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe
  uMechanism uIntervention uOutcome uProvenance uTime uAccess
  uOccurrence uExperiment uExperimentOutcome
  uObjectOccurrence uInput uObjectExperiment uObjectOutcome

/-!
# Context-relative atomic and composite qualified objects

`KernelQualification` is intentionally a qualification of a nontrivially
integrated composite carrier: it requires two distinct internally dependent
mechanisms.  It must therefore not be used as a universal definition of every
object.  This additive module keeps that accepted composite surface unchanged
and adds the missing context-relative atomic base case.

Atomicity here is not an absolute material predicate.  It means that the
generated kernel is irreducible in the declared intervention/dependency
context.  A typed access relation must also exhibit at least one admitted way
to access the root.  This permits an isolated universe to use a declared
external observational/access interface without inventing a boundary
mechanism, while preventing a vacuous bare `Prop` from certifying access.
-/

/-! ## Common, atomic, and composite qualification -/

/-- Qualification evidence shared by atomic and composite object cuts. -/
structure CommonKernelQualification
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (Provenance : Type uProvenance)
    (Time : Type uTime)
    (formedBy : Mechanism → Provenance → Prop)
    (continuesAt : Mechanism → Time → Prop)
    (robustAtScale : (Mechanism → Prop) → Prop)
    (root : Mechanism)
    (provenance : Provenance) : Prop where
  root_not_port : ¬ model.port root
  provenance_grounded : formedBy root provenance
  persists_at_distinct_times :
    ∃ start finish, start ≠ finish ∧
      continuesAt root start ∧ continuesAt root finish
  scale_robust : robustAtScale (GeneratedKernel model root)

/-- A typed context supplies possible access acts and their target relation. -/
structure AtomicAccessContext
    (Mechanism : Type uMechanism)
    (Access : Type uAccess) where
  accesses : Access → Mechanism → Prop

/--
An atomic object qualification relative to one declared intervention and
access context.  `kernel_irreducible` says that this context discovers no
distinct internal constituent; it does not say that the root is metaphysically
simple in every finer context.
-/
structure AtomicKernelQualification
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (Provenance : Type uProvenance)
    (Time : Type uTime)
    (formedBy : Mechanism → Provenance → Prop)
    (continuesAt : Mechanism → Time → Prop)
    (robustAtScale : (Mechanism → Prop) → Prop)
    (Access : Type uAccess)
    (accessContext : AtomicAccessContext Mechanism Access)
    (root : Mechanism)
    (provenance : Provenance) : Prop where
  common : CommonKernelQualification model Provenance Time formedBy
    continuesAt robustAtScale root provenance
  kernel_irreducible :
    ∀ ⦃mechanism⦄, GeneratedKernel model root mechanism → mechanism = root
  externally_accessible : ∃ access, accessContext.accesses access root

/-- The accepted nontrivially integrated qualification, explicitly named as
the composite grade. -/
abbrev CompositeKernelQualification
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (Provenance : Type uProvenance)
    (Time : Type uTime)
    (formedBy : Mechanism → Provenance → Prop)
    (continuesAt : Mechanism → Time → Prop)
    (robustAtScale : (Mechanism → Prop) → Prop)
    (root : Mechanism)
    (provenance : Provenance) :=
  KernelQualification model Provenance Time formedBy continuesAt
    robustAtScale root provenance

/-- Every accepted composite qualification contains the common evidence. -/
def KernelQualification.toCommon
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {root : Mechanism}
    {provenance : Provenance}
    (qualification : KernelQualification model Provenance Time formedBy
      continuesAt robustAtScale root provenance) :
    CommonKernelQualification model Provenance Time formedBy continuesAt
      robustAtScale root provenance where
  root_not_port := qualification.root_not_port
  provenance_grounded := qualification.provenance_grounded
  persists_at_distinct_times := qualification.persists_at_distinct_times
  scale_robust := qualification.scale_robust

/-- Exactly the two structural grades admitted by this generalized layer. -/
inductive ObjectQualificationGrade
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (Provenance : Type uProvenance)
    (Time : Type uTime)
    (formedBy : Mechanism → Provenance → Prop)
    (continuesAt : Mechanism → Time → Prop)
    (robustAtScale : (Mechanism → Prop) → Prop)
    (Access : Type uAccess)
    (accessContext : AtomicAccessContext Mechanism Access)
    (root : Mechanism)
    (provenance : Provenance) : Type (max uMechanism uIntervention uOutcome
      uProvenance uTime uAccess) where
  | atomic : AtomicKernelQualification model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext root provenance →
      ObjectQualificationGrade model Provenance Time formedBy continuesAt
        robustAtScale Access accessContext root provenance
  | composite : CompositeKernelQualification model Provenance Time formedBy
      continuesAt robustAtScale root provenance →
      ObjectQualificationGrade model Provenance Time formedBy continuesAt
        robustAtScale Access accessContext root provenance

namespace ObjectQualificationGrade

/-- Both grades expose the same boundary, provenance, persistence, and scale
contract. -/
def common
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {Access : Type uAccess}
    {accessContext : AtomicAccessContext Mechanism Access}
    {root : Mechanism}
    {provenance : Provenance}
    (grade : ObjectQualificationGrade model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext root provenance) :
    CommonKernelQualification model Provenance Time formedBy continuesAt
      robustAtScale root provenance := by
  cases grade with
  | atomic qualification => exact qualification.common
  | composite qualification => exact qualification.toCommon

/-- Atomic and composite evidence cannot both hold for the same generated
kernel in one fixed context. -/
theorem atomic_composite_disjoint
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {Access : Type uAccess}
    {accessContext : AtomicAccessContext Mechanism Access}
    {root : Mechanism}
    {provenance : Provenance}
    (atomic : AtomicKernelQualification model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext root provenance)
    (composite : CompositeKernelQualification model Provenance Time formedBy
      continuesAt robustAtScale root provenance) : False := by
  rcases composite.internally_integrated with
    ⟨first, second, firstGenerated, secondGenerated, different, dependency⟩
  have firstRoot := atomic.kernel_irreducible firstGenerated
  have secondRoot := atomic.kernel_irreducible secondGenerated
  exact different (firstRoot.trans secondRoot.symm)

end ObjectQualificationGrade

/-! ## Generalized static cuts and the composite adapter -/

/-- Operational identity without the old nontrivial-class requirement.  This
is the required base for a genuine singleton atomic witness. -/
structure ConvergedOperationalIndividual
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    (evidence : BinaryRelation Occurrence)
    (law : Occurrence → Experiment → ExperimentOutcome) where
  seed : Occurrence
  convergence : ForcedIdentity evidence = AllowedIdentity law

def ConvergedOperationalIndividual.token
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {evidence : BinaryRelation Occurrence}
    {law : Occurrence → Experiment → ExperimentOutcome}
    (individual : ConvergedOperationalIndividual evidence law) :
    OperationalToken evidence :=
  operationalTokenOf evidence individual.seed

/-- A static exact carrier-realization cut admitting either structural grade. -/
structure GeneralizedStaticObjectCut
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (Provenance : Type uProvenance)
    (Time : Type uTime)
    (formedBy : Mechanism → Provenance → Prop)
    (continuesAt : Mechanism → Time → Prop)
    (robustAtScale : (Mechanism → Prop) → Prop)
    (Access : Type uAccess)
    (accessContext : AtomicAccessContext Mechanism Access)
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    (evidence : BinaryRelation Occurrence)
    (law : Occurrence → Experiment → ExperimentOutcome) where
  root : Mechanism
  provenance : Provenance
  grade : ObjectQualificationGrade model Provenance Time formedBy continuesAt
    robustAtScale Access accessContext root provenance
  individual : ConvergedOperationalIndividual evidence law
  represents : Occurrence → Mechanism
  seed_represents_root : represents individual.seed = root
  class_exactly_realizes_kernel : ∀ mechanism,
    GeneratedKernel model root mechanism ↔
      ∃ memberOccurrence,
        ForcedIdentity evidence individual.seed memberOccurrence ∧
          represents memberOccurrence = mechanism

namespace GeneralizedStaticObjectCut

/-- Every pre-existing constraint-generated object embeds without changing its
carrier, member identity, or exact realization theorem. -/
def ofConstraintGeneratedObject
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {Access : Type uAccess}
    (accessContext : AtomicAccessContext Mechanism Access)
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {evidence : BinaryRelation Occurrence}
    {law : Occurrence → Experiment → ExperimentOutcome}
    (object : ConstraintGeneratedObject model Provenance Time formedBy
      continuesAt robustAtScale evidence law) :
    GeneralizedStaticObjectCut model Provenance Time formedBy continuesAt
      robustAtScale Access accessContext evidence law where
  root := object.occurrence.root
  provenance := object.occurrence.provenance
  grade := .composite object.occurrence.qualification
  individual :=
    { seed := object.individual.seed
      convergence := object.individual.convergence }
  represents := object.represents
  seed_represents_root := object.seed_represents_root
  class_exactly_realizes_kernel := object.class_exactly_realizes_kernel

theorem adapted_object_is_composite
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {Access : Type uAccess}
    (accessContext : AtomicAccessContext Mechanism Access)
    {Occurrence : Type uOccurrence}
    {Experiment : Type uExperiment}
    {ExperimentOutcome : Type uExperimentOutcome}
    {evidence : BinaryRelation Occurrence}
    {law : Occurrence → Experiment → ExperimentOutcome}
    (object : ConstraintGeneratedObject model Provenance Time formedBy
      continuesAt robustAtScale evidence law) :
    ∃ qualification,
      (ofConstraintGeneratedObject accessContext object).grade =
        ObjectQualificationGrade.composite qualification := by
  exact ⟨object.occurrence.qualification, rfl⟩

end GeneralizedStaticObjectCut

/-! ## Generalized changing objects -/

/-- Whole-object dynamics whose snapshots may independently be atomic or
composite in the same declared context.  Identity tests are constitutive,
token-invariant tests, not arbitrary instantaneous state measurements. -/
structure GeneralizedDynamicQualifiedObject
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (Provenance : Type uProvenance)
    (Time : Type uTime)
    (formedBy : Mechanism → Provenance → Prop)
    (continuesAt : Mechanism → Time → Prop)
    (robustAtScale : (Mechanism → Prop) → Prop)
    (Access : Type uAccess)
    (accessContext : AtomicAccessContext Mechanism Access)
    (MemberOccurrence : Type uOccurrence)
    (MemberExperiment : Type uExperiment)
    (MemberOutcome : Type uExperimentOutcome)
    (memberEvidence : BinaryRelation MemberOccurrence)
    (memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome)
    (ObjectOccurrence : Type uObjectOccurrence)
    (Input : Type uInput)
    (ObjectExperiment : Type uObjectExperiment)
    (ObjectOutcome : Type uObjectOutcome) where
  seed : ObjectOccurrence
  snapshot : ObjectOccurrence →
    GeneralizedStaticObjectCut model Provenance Time formedBy continuesAt
      robustAtScale Access accessContext memberEvidence memberLaw
  openStep : ObjectOccurrence → Input → ObjectOccurrence → Prop
  continuationEvidence : BinaryRelation ObjectOccurrence
  continuation_grounded : ∀ ⦃source target⦄,
    continuationEvidence source target → ∃ input, openStep source input target
  identityExperimentLaw : ObjectOccurrence → ObjectExperiment → ObjectOutcome
  identityConverges :
    ForcedIdentity continuationEvidence = AllowedIdentity identityExperimentLaw

namespace GeneralizedDynamicQualifiedObject

variable
  {Mechanism : Type uMechanism}
  {Intervention : Type uIntervention}
  {Outcome : Type uOutcome}
  {model : ActiveConstraintModel Mechanism Intervention Outcome}
  {Provenance : Type uProvenance}
  {Time : Type uTime}
  {formedBy : Mechanism → Provenance → Prop}
  {continuesAt : Mechanism → Time → Prop}
  {robustAtScale : (Mechanism → Prop) → Prop}
  {Access : Type uAccess}
  {accessContext : AtomicAccessContext Mechanism Access}
  {MemberOccurrence : Type uOccurrence}
  {MemberExperiment : Type uExperiment}
  {MemberOutcome : Type uExperimentOutcome}
  {memberEvidence : BinaryRelation MemberOccurrence}
  {memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome}
  {ObjectOccurrence : Type uObjectOccurrence}
  {Input : Type uInput}
  {ObjectExperiment : Type uObjectExperiment}
  {ObjectOutcome : Type uObjectOutcome}

abbrev SameToken
    (object : GeneralizedDynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext MemberOccurrence
      MemberExperiment MemberOutcome memberEvidence memberLaw ObjectOccurrence
      Input ObjectExperiment ObjectOutcome) : BinaryRelation ObjectOccurrence :=
  ForcedIdentity object.continuationEvidence

def LineageEdge
    (object : GeneralizedDynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext MemberOccurrence
      MemberExperiment MemberOutcome memberEvidence memberLaw ObjectOccurrence
      Input ObjectExperiment ObjectOutcome) : BinaryRelation ObjectOccurrence :=
  fun source target => ∃ input, object.openStep source input target

abbrev Lineage
    (object : GeneralizedDynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext MemberOccurrence
      MemberExperiment MemberOutcome memberEvidence memberLaw ObjectOccurrence
      Input ObjectExperiment ObjectOutcome) : BinaryRelation ObjectOccurrence :=
  LineageGenerated object.LineageEdge

def ExactStep
    (object : GeneralizedDynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext MemberOccurrence
      MemberExperiment MemberOutcome memberEvidence memberLaw ObjectOccurrence
      Input ObjectExperiment ObjectOutcome) :
    ObjectOccurrence → Input → ObjectOccurrence → Prop :=
  fun source input target =>
    object.openStep source input target ∧ object.SameToken source target

abbrev LineageMSpace
    (object : GeneralizedDynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext MemberOccurrence
      MemberExperiment MemberOutcome memberEvidence memberLaw ObjectOccurrence
      Input ObjectExperiment ObjectOutcome) :=
  DerivedMSpace object.openStep object.seed

abbrev ExactMSpace
    (object : GeneralizedDynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext MemberOccurrence
      MemberExperiment MemberOutcome memberEvidence memberLaw ObjectOccurrence
      Input ObjectExperiment ObjectOutcome) :=
  DerivedMSpace object.ExactStep object.seed

theorem sameToken_implies_identityTestAgreement
    (object : GeneralizedDynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext MemberOccurrence
      MemberExperiment MemberOutcome memberEvidence memberLaw ObjectOccurrence
      Input ObjectExperiment ObjectOutcome)
    {first second : ObjectOccurrence}
    (sameToken : object.SameToken first second)
    (experiment : ObjectExperiment) :
    object.identityExperimentLaw first experiment =
      object.identityExperimentLaw second experiment := by
  have allowed : AllowedIdentity object.identityExperimentLaw first second := by
    rw [← object.identityConverges]
    exact sameToken
  exact allowed experiment

theorem exactHistory_endpoint_sameToken
    (object : GeneralizedDynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext MemberOccurrence
      MemberExperiment MemberOutcome memberEvidence memberLaw ObjectOccurrence
      Input ObjectExperiment ObjectOutcome)
    {endpoint : ObjectOccurrence}
    (history : OpenHistory object.ExactStep object.seed endpoint) :
    object.SameToken object.seed endpoint := by
  exact history.invariant
    (invariant := fun occurrence => object.SameToken object.seed occurrence)
    (.refl object.seed) (by
      intro current next input seedCurrent step
      exact .trans seedCurrent step.2)

theorem lineageHistory_endpoint_lineage
    (object : GeneralizedDynamicQualifiedObject model Provenance Time formedBy
      continuesAt robustAtScale Access accessContext MemberOccurrence
      MemberExperiment MemberOutcome memberEvidence memberLaw ObjectOccurrence
      Input ObjectExperiment ObjectOutcome)
    {endpoint : ObjectOccurrence}
    (history : OpenHistory object.openStep object.seed endpoint) :
    object.Lineage object.seed endpoint := by
  exact history.invariant
    (invariant := fun occurrence => object.Lineage object.seed occurrence)
    (.refl object.seed) (by
      intro current next input seedCurrent step
      exact .trans seedCurrent (.ofEvidence ⟨input, step⟩))

end GeneralizedDynamicQualifiedObject

/-! ## A genuine singleton atomic witness -/

def singletonAtomicModel : ActiveConstraintModel Unit Unit Unit where
  response := fun _ _ => ()
  responseWithout := fun _ _ _ => ()
  port := fun _ => False

def singletonFormedBy (_ : Unit) (_ : Unit) : Prop := True
def singletonContinuesAt (_ : Unit) (_ : Bool) : Prop := True
def singletonRobustAtScale (_ : Unit → Prop) : Prop := True

def singletonAccessContext : AtomicAccessContext Unit Unit where
  accesses := fun _ _ => True

def singletonCommonQualification :
    CommonKernelQualification singletonAtomicModel Unit Bool singletonFormedBy
      singletonContinuesAt singletonRobustAtScale () () where
  root_not_port := by simp [singletonAtomicModel]
  provenance_grounded := trivial
  persists_at_distinct_times := ⟨false, true, by decide, trivial, trivial⟩
  scale_robust := trivial

theorem singletonGeneratedKernel_irreducible
    {mechanism : Unit}
    (generated : GeneratedKernel singletonAtomicModel () mechanism) :
    mechanism = () := by
  cases mechanism
  rfl

def singletonAtomicQualification :
    AtomicKernelQualification singletonAtomicModel Unit Bool singletonFormedBy
      singletonContinuesAt singletonRobustAtScale Unit singletonAccessContext
      () () where
  common := singletonCommonQualification
  kernel_irreducible := by
    intro mechanism generated
    exact singletonGeneratedKernel_irreducible generated
  externally_accessible := ⟨(), trivial⟩

def singletonMemberEvidence : BinaryRelation Unit := fun _ _ => True
def singletonMemberLaw : Unit → Unit → Unit := fun _ _ => ()

theorem singleton_member_identity_converges :
    ForcedIdentity singletonMemberEvidence = AllowedIdentity singletonMemberLaw := by
  have forced : ForcedIdentity singletonMemberEvidence = singletonMemberEvidence := by
    apply forcedIdentity_eq_of_equivalence
    · intro occurrence; trivial
    · intro first second related; trivial
    · intro first second third firstSecond secondThird; trivial
  have allowed : AllowedIdentity singletonMemberLaw = singletonMemberEvidence := by
    funext first second
    apply propext
    constructor <;> intro related
    · trivial
    · intro experiment
      cases first
      cases second
      cases experiment
      rfl
  exact forced.trans allowed.symm

def singletonConvergedIndividual :
    ConvergedOperationalIndividual singletonMemberEvidence singletonMemberLaw where
  seed := ()
  convergence := singleton_member_identity_converges

def singletonGeneralizedStaticObjectCut :
    GeneralizedStaticObjectCut singletonAtomicModel Unit Bool singletonFormedBy
      singletonContinuesAt singletonRobustAtScale Unit singletonAccessContext
      singletonMemberEvidence singletonMemberLaw where
  root := ()
  provenance := ()
  grade := .atomic singletonAtomicQualification
  individual := singletonConvergedIndividual
  represents := fun _ => ()
  seed_represents_root := rfl
  class_exactly_realizes_kernel := by
    intro mechanism
    cases mechanism
    constructor
    · intro generated
      exact ⟨(), EquivalenceGenerated.ofEvidence trivial, rfl⟩
    · intro witness
      exact .ofRoot

theorem atomic_singleton_object_is_inhabited :
    Nonempty
      (GeneralizedStaticObjectCut singletonAtomicModel Unit Bool
        singletonFormedBy singletonContinuesAt singletonRobustAtScale Unit
        singletonAccessContext singletonMemberEvidence singletonMemberLaw) :=
  ⟨singletonGeneralizedStaticObjectCut⟩

theorem singleton_atomic_grade_has_no_composite_qualification :
    ¬ CompositeKernelQualification singletonAtomicModel Unit Bool
      singletonFormedBy singletonContinuesAt singletonRobustAtScale () () := by
  intro composite
  exact ObjectQualificationGrade.atomic_composite_disjoint
    singletonAtomicQualification composite

/-! ## Atomicity changes under a refined dependency context -/

/-- A coarse intervention model on the same `ToyMechanism` carrier detects no
internal dependency.  The environmental port convention is unchanged. -/
def coarseToyConstraintModel : ActiveConstraintModel ToyMechanism Unit Bool where
  response := fun _ _ => true
  responseWithout := fun _ _ _ => true
  port := fun mechanism => mechanism = .environment

/-- Coarse-scale robustness is specific to the singleton generated kernel. -/
def coarseToyRobustAtScale (carrier : ToyMechanism → Prop) : Prop :=
  carrier .left ∧ ¬ carrier .right ∧ ¬ carrier .environment

def coarseToyAccessContext : AtomicAccessContext ToyMechanism Unit where
  accesses := fun _ mechanism => mechanism = .left

theorem coarseToy_has_no_essential_dependency
    (target support : ToyMechanism) :
    ¬ EssentialDependency coarseToyConstraintModel target support := by
  rintro ⟨witness⟩
  exact witness.changes (by simp [coarseToyConstraintModel])

theorem coarseToy_has_no_internal_dependency
    (current next : ToyMechanism) :
    ¬ InternalDependency coarseToyConstraintModel current next := by
  intro internal
  rcases internal.2 with dependency | dependency
  · exact coarseToy_has_no_essential_dependency current next dependency
  · exact coarseToy_has_no_essential_dependency next current dependency

theorem coarseToy_generatedKernel_irreducible
    {mechanism : ToyMechanism}
    (generated : GeneratedKernel coarseToyConstraintModel .left mechanism) :
    mechanism = .left := by
  cases generated with
  | ofRoot => rfl
  | ofInternalDependency previous dependency =>
      exact False.elim
        (coarseToy_has_no_internal_dependency _ _ dependency)

def coarseToyCommonQualification :
    CommonKernelQualification coarseToyConstraintModel Unit Bool toyFormedBy
      toyContinuesAt coarseToyRobustAtScale .left () where
  root_not_port := by simp [coarseToyConstraintModel]
  provenance_grounded := rfl
  persists_at_distinct_times := ⟨false, true, by decide, rfl, rfl⟩
  scale_robust := by
    refine ⟨.ofRoot, ?_, ?_⟩
    · intro rightGenerated
      have equal := coarseToy_generatedKernel_irreducible rightGenerated
      cases equal
    · intro environmentGenerated
      have equal := coarseToy_generatedKernel_irreducible environmentGenerated
      cases equal

def coarseToyAtomicQualification :
    AtomicKernelQualification coarseToyConstraintModel Unit Bool toyFormedBy
      toyContinuesAt coarseToyRobustAtScale Unit coarseToyAccessContext
      .left () where
  common := coarseToyCommonQualification
  kernel_irreducible := by
    intro mechanism generated
    exact coarseToy_generatedKernel_irreducible generated
  externally_accessible := ⟨(), rfl⟩

/--
The same underlying `ToyMechanism.left` root is atomic in the coarse context
and composite in the refined intervention context.  Thus structural grade is
context-relative and cannot be promoted to an absolute material predicate.
-/
theorem same_toy_root_is_atomic_coarse_and_composite_refined :
    AtomicKernelQualification coarseToyConstraintModel Unit Bool toyFormedBy
        toyContinuesAt coarseToyRobustAtScale Unit coarseToyAccessContext
        .left () ∧
      CompositeKernelQualification toyConstraintModel Unit Bool toyFormedBy
        toyContinuesAt toyRobustAtScale .left () :=
  ⟨coarseToyAtomicQualification, toyKernelQualification⟩

end OCKIndividuationMSpaceComposition
