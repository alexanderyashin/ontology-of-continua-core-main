import OCKIndividuationMSpaceComposition.CausalObservationalBridge
import OCKIndividuationMSpaceComposition.DerivedMSpace
import OCKIndividuationMSpaceComposition.RecursiveComposition

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe
  uMechanism uIntervention uOutcome uProvenance uTime
  uMemberOccurrence uMemberExperiment uMemberOutcome
  uObjectOccurrence uInput uObjectExperiment uObjectOutcome
  uComponentPresentation

/-!
# Dynamic whole-object identity without component/occurrence conflation

This module is an additive correction layer.  Four roles remain separate:

* `Mechanism` is a causal constituent of a static generated carrier;
* `MemberOccurrence` is a witness belonging to the extension of one static
  object cut;
* `ObjectOccurrence` is a temporally located occurrence of the whole object;
* `ComponentPresentation` presents causal constituents for reconstruction.

The accepted `ConstraintGeneratedObject` remains the static object cut.  Its
seed identity class realizes the *whole causal carrier*: it is not the kernel
of equality of one represented constituent.  A `CausalObservationalBridge`
supplies the separate component-presentation quotient whose classes correspond
to individual causal constituents.

`DerivedObjectTheory.IdentifiedDynamicObject` is therefore retained only as a
legacy component-level construction.  In particular, its realization-kernel
quotient must not be read as the token identity of the changing whole object.
This module does not import or promote that legacy synthesis.
-/

/-! ## Static object cut and component presentation -/

/-- A name for the already accepted static object cut, with its member role explicit. -/
abbrev StaticObjectCut
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (Provenance : Type uProvenance)
    (Time : Type uTime)
    (formedBy : Mechanism → Provenance → Prop)
    (continuesAt : Mechanism → Time → Prop)
    (robustAtScale : (Mechanism → Prop) → Prop)
    (MemberOccurrence : Type uMemberOccurrence)
    (MemberExperiment : Type uMemberExperiment)
    (MemberOutcome : Type uMemberOutcome)
    (memberEvidence : BinaryRelation MemberOccurrence)
    (memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome) :=
  ConstraintGeneratedObject model Provenance Time
    formedBy continuesAt robustAtScale memberEvidence memberLaw

/--
A static object cut equipped with a separate presentation of its causal
constituents.  Presentation equivalence is component reconstruction, while the
static cut's seed class is whole-carrier membership.
-/
structure PresentedStaticObjectCut
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (Provenance : Type uProvenance)
    (Time : Type uTime)
    (formedBy : Mechanism → Provenance → Prop)
    (continuesAt : Mechanism → Time → Prop)
    (robustAtScale : (Mechanism → Prop) → Prop)
    (MemberOccurrence : Type uMemberOccurrence)
    (MemberExperiment : Type uMemberExperiment)
    (MemberOutcome : Type uMemberOutcome)
    (memberEvidence : BinaryRelation MemberOccurrence)
    (memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome)
    (ComponentPresentation : Type uComponentPresentation) where
  cut : StaticObjectCut model Provenance Time formedBy continuesAt
    robustAtScale MemberOccurrence MemberExperiment MemberOutcome
    memberEvidence memberLaw
  componentEdge : ComponentPresentation → ComponentPresentation → Prop
  componentRoot : ComponentPresentation
  componentBridge : CausalObservationalBridge
    (InternalDependency model) componentEdge cut.occurrence.root componentRoot

/--
The two exact static results are deliberately separate conjuncts:

1. component presentations modulo equal realization correspond bijectively to
   individual causal constituents;
2. the static object's seed extension realizes the entire causal carrier.

No equality between those two relations is asserted.
-/
theorem PresentedStaticObjectCut.componentQuotient_and_staticExtension
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {MemberOccurrence : Type uMemberOccurrence}
    {MemberExperiment : Type uMemberExperiment}
    {MemberOutcome : Type uMemberOutcome}
    {memberEvidence : BinaryRelation MemberOccurrence}
    {memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome}
    {ComponentPresentation : Type uComponentPresentation}
    (presented : PresentedStaticObjectCut model Provenance Time formedBy
      continuesAt robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ComponentPresentation) :
    Function.Bijective presented.componentBridge.quotientToCausalCarrier ∧
      (∀ mechanism,
        GeneratedKernel model presented.cut.occurrence.root mechanism ↔
          ∃ memberOccurrence,
            ForcedIdentity memberEvidence presented.cut.individual.seed
              memberOccurrence ∧
            presented.cut.represents memberOccurrence = mechanism) :=
  ⟨presented.componentBridge.quotientToCausalCarrier_bijective,
    presented.cut.class_exactly_realizes_kernel⟩

/-! ## Whole-object dynamics and identity -/

/--
A changing qualified object.  Every `ObjectOccurrence` supplies a qualified
static cut, while continuation evidence, open dynamics, and object-level
experiments live on the separate whole-object occurrence type.
-/
structure DynamicQualifiedObject
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    (model : ActiveConstraintModel Mechanism Intervention Outcome)
    (Provenance : Type uProvenance)
    (Time : Type uTime)
    (formedBy : Mechanism → Provenance → Prop)
    (continuesAt : Mechanism → Time → Prop)
    (robustAtScale : (Mechanism → Prop) → Prop)
    (MemberOccurrence : Type uMemberOccurrence)
    (MemberExperiment : Type uMemberExperiment)
    (MemberOutcome : Type uMemberOutcome)
    (memberEvidence : BinaryRelation MemberOccurrence)
    (memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome)
    (ObjectOccurrence : Type uObjectOccurrence)
    (Input : Type uInput)
    (ObjectExperiment : Type uObjectExperiment)
    (ObjectOutcome : Type uObjectOutcome) where
  seed : ObjectOccurrence
  snapshot : ObjectOccurrence →
    StaticObjectCut model Provenance Time formedBy continuesAt robustAtScale
      MemberOccurrence MemberExperiment MemberOutcome memberEvidence memberLaw
  openStep : ObjectOccurrence → Input → ObjectOccurrence → Prop
  continuationEvidence : BinaryRelation ObjectOccurrence
  continuation_grounded : ∀ ⦃source target⦄,
    continuationEvidence source target →
      ∃ input, openStep source input target
  /--
  Tests admitted here are constitutive, token-invariant identity tests.  They
  are not arbitrary instantaneous state measurements: changing occurrences of
  one token may have different state projections, which belong in an explicit
  representation such as a `CurrentK` bridge.
  -/
  experimentLaw : ObjectOccurrence → ObjectExperiment → ObjectOutcome
  identityConverges :
    ForcedIdentity continuationEvidence = AllowedIdentity experimentLaw

namespace DynamicQualifiedObject

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
  {MemberOccurrence : Type uMemberOccurrence}
  {MemberExperiment : Type uMemberExperiment}
  {MemberOutcome : Type uMemberOutcome}
  {memberEvidence : BinaryRelation MemberOccurrence}
  {memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome}
  {ObjectOccurrence : Type uObjectOccurrence}
  {Input : Type uInput}
  {ObjectExperiment : Type uObjectExperiment}
  {ObjectOutcome : Type uObjectOutcome}

/-- Whole-object token identity, generated only from whole-object evidence. -/
abbrev SameToken
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome) : BinaryRelation ObjectOccurrence :=
  ForcedIdentity object.continuationEvidence

/-- Directed one-step lineage generated by the open whole-object dynamics. -/
def LineageEdge
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome) : BinaryRelation ObjectOccurrence :=
  fun source target => ∃ input, object.openStep source input target

/-- Reflexive-transitive whole-object lineage; unlike token identity it may branch. -/
abbrev Lineage
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome) : BinaryRelation ObjectOccurrence :=
  LineageGenerated object.LineageEdge

/-- A whole-object step certified to stay inside one operational token. -/
def ExactStep
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome) : ObjectOccurrence → Input → ObjectOccurrence → Prop :=
  fun source input target =>
    object.openStep source input target ∧ object.SameToken source target

/-- Operational token quotient of whole-object occurrences. -/
abbrev Token
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome) :=
  OperationalToken object.continuationEvidence

/-- All finite whole-object lineage histories from the declared seed. -/
abbrev LineageMSpace
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome) :=
  DerivedMSpace object.openStep object.seed

/-- Finite histories restricted to exact same-token transitions. -/
abbrev ExactMSpace
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome) :=
  DerivedMSpace object.ExactStep object.seed

/-- Each temporally located whole-object occurrence carries a qualified static cut. -/
theorem snapshot_qualified
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome)
    (occurrence : ObjectOccurrence) :
    KernelQualification model Provenance Time formedBy continuesAt robustAtScale
      (object.snapshot occurrence).occurrence.root
      (object.snapshot occurrence).occurrence.provenance :=
  (object.snapshot occurrence).occurrence.qualification

/-- Converged whole-object bounds determine exactly one admissible identity relation. -/
theorem identity_exists_unique
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome) :
    ∃! relation,
      AdmissibleIdentityRelation object.continuationEvidence
        object.experimentLaw relation :=
  converged_identity_bounds_exist_unique object.continuationEvidence
    object.experimentLaw object.identityConverges

/--
Whole-object identity agrees under every *declared identity test*.  The scope
of `ObjectExperiment` is load-bearing: this theorem does not say that two
temporally distinct occurrences have equal instantaneous state projections.
-/
theorem sameToken_implies_identityTestAgreement
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome)
    {first second : ObjectOccurrence}
    (sameToken : object.SameToken first second)
    (experiment : ObjectExperiment) :
    object.experimentLaw first experiment =
      object.experimentLaw second experiment := by
  have allowed : AllowedIdentity object.experimentLaw first second := by
    rw [← object.identityConverges]
    exact sameToken
  exact allowed experiment

/-- Every exact-history endpoint belongs to the seed's whole-object token. -/
theorem exactHistory_endpoint_sameToken
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome)
    {endpoint : ObjectOccurrence}
    (history : OpenHistory object.ExactStep object.seed endpoint) :
    object.SameToken object.seed endpoint := by
  exact history.invariant
    (invariant := fun occurrence => object.SameToken object.seed occurrence)
    (.refl object.seed) (by
      intro current next input seedCurrent step
      exact .trans seedCurrent step.2)

/-- Every open-history endpoint is a descendant of the seed, without identity collapse. -/
theorem lineageHistory_endpoint_lineage
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome)
    {endpoint : ObjectOccurrence}
    (history : OpenHistory object.openStep object.seed endpoint) :
    object.Lineage object.seed endpoint := by
  exact history.invariant
    (invariant := fun occurrence => object.Lineage object.seed occurrence)
    (.refl object.seed) (by
      intro current next input seedCurrent step
      exact .trans seedCurrent (.ofEvidence ⟨input, step⟩))

/-- Object-level continuation evidence maps to equality of operational tokens. -/
theorem token_preserves_continuationEvidence
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome) :
    ContinuationPreserving object.continuationEvidence
      (operationalTokenOf object.continuationEvidence) := by
  intro source target evidence
  exact Quotient.sound (.ofEvidence evidence)

/-- Reuse of the accepted branching boundary at the whole-object token layer. -/
theorem branching_separated_tokens_no_go
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome)
    {parent leftChild rightChild : ObjectOccurrence}
    (leftBranch : object.continuationEvidence parent leftChild)
    (rightBranch : object.continuationEvidence parent rightChild)
    (childrenSeparated :
      operationalTokenOf object.continuationEvidence leftChild ≠
        operationalTokenOf object.continuationEvidence rightChild) : False :=
  OCMaturityCompletionCycle.branching_with_required_separation_no_go
    object.token_preserves_continuationEvidence leftBranch rightBranch
    childrenSeparated

/-- Reuse of the dual fusion boundary at the whole-object token layer. -/
theorem fusion_separated_tokens_no_go
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome)
    {leftParent rightParent child : ObjectOccurrence}
    (leftFusion : object.continuationEvidence leftParent child)
    (rightFusion : object.continuationEvidence rightParent child)
    (parentsSeparated :
      operationalTokenOf object.continuationEvidence leftParent ≠
        operationalTokenOf object.continuationEvidence rightParent) : False :=
  OCMaturityCompletionCycle.fusion_with_required_separation_no_go
    object.token_preserves_continuationEvidence leftFusion rightFusion
    parentsSeparated

end DynamicQualifiedObject

/-! ## Same token with a changed, separately qualified snapshot -/

/-- The same toy carrier with the two internal member witnesses exchanged. -/
def toySwappedRepresents : ToyOccurrence → ToyMechanism
  | (false, false) => .right
  | (false, true) => .left
  | (true, _) => .environment

def toySwappedIdentitySeed : ToyOccurrence := (false, true)

theorem toy_swapped_identity_class_is_nontrivial :
    NontrivialForcedClass toyIdentityEvidence toySwappedIdentitySeed := by
  constructor
  · refine ⟨(false, false), by decide, ?_⟩
    rw [toy_forced_identity_eq_evidence]
    rfl
  · refine ⟨(true, false), ?_⟩
    rw [toy_forced_identity_eq_evidence]
    simp [toyIdentityEvidence, toySwappedIdentitySeed]

def toySwappedOperationalIndividual :
    UniquelyConstrainedOperationalIndividual
      toyIdentityEvidence toyIdentityLaw where
  seed := toySwappedIdentitySeed
  convergence := toy_identity_bounds_converge
  nontrivial := toy_swapped_identity_class_is_nontrivial

def toySwappedConstraintGeneratedObject :
    ConstraintGeneratedObject toyConstraintModel Unit Bool
      toyFormedBy toyContinuesAt toyRobustAtScale
      toyIdentityEvidence toyIdentityLaw where
  occurrence := toyDerivedObjectOccurrence
  individual := toySwappedOperationalIndividual
  represents := toySwappedRepresents
  seed_represents_root := rfl
  class_exactly_realizes_kernel := by
    intro mechanism
    cases mechanism with
    | left =>
        constructor
        · intro _
          refine ⟨(false, true), ?_, rfl⟩
          rw [toy_forced_identity_eq_evidence]
          rfl
        · intro _
          exact .ofRoot
    | right =>
        constructor
        · intro _
          refine ⟨(false, false), ?_, rfl⟩
          rw [toy_forced_identity_eq_evidence]
          rfl
        · intro _
          exact toy_right_is_in_generated_kernel
    | environment =>
        constructor
        · intro generated
          exact False.elim ((generatedKernel_contains_no_ports
            (model := toyConstraintModel)
            (root := ToyMechanism.left)
            (mechanism := ToyMechanism.environment)
            (by simp [toyConstraintModel]) generated)
            (by simp [toyConstraintModel]))
        · rintro ⟨internalOccurrence, sameClass, represented⟩
          rw [toy_forced_identity_eq_evidence] at sameClass
          change false = internalOccurrence.1 at sameClass
          rcases internalOccurrence with ⟨first, second⟩
          cases first <;> cases second <;>
            simp [toySwappedRepresents] at sameClass represented

theorem toy_static_snapshots_are_distinct :
    toyConstraintGeneratedObject ≠ toySwappedConstraintGeneratedObject := by
  intro equalCuts
  have equalSeeds := congrArg
    (fun cut => cut.individual.seed) equalCuts
  change (false, false) = (false, true) at equalSeeds
  have unequalSeeds : (false, false) ≠ (false, true) := by decide
  exact unequalSeeds equalSeeds

def boolWholeObjectEvidence : BinaryRelation Bool := fun _ _ => True

def boolWholeObjectLaw : Bool → Unit → Unit := fun _ _ => ()

theorem bool_whole_object_identity_converges :
    ForcedIdentity boolWholeObjectEvidence =
      AllowedIdentity boolWholeObjectLaw := by
  have forced :
      ForcedIdentity boolWholeObjectEvidence = boolWholeObjectEvidence := by
    apply forcedIdentity_eq_of_equivalence
    · intro occurrence
      trivial
    · intro first second related
      trivial
    · intro first second third firstSecond secondThird
      trivial
  have allowed :
      AllowedIdentity boolWholeObjectLaw = boolWholeObjectEvidence := by
    funext first second
    apply propext
    constructor
    · intro _
      trivial
    · intro _ experiment
      cases experiment
      rfl
  exact forced.trans allowed.symm

def boolDynamicQualifiedObject :
    DynamicQualifiedObject toyConstraintModel Unit Bool toyFormedBy
      toyContinuesAt toyRobustAtScale ToyOccurrence Unit Bool
      toyIdentityEvidence toyIdentityLaw Bool Unit Unit Unit where
  seed := false
  snapshot := fun occurrence =>
    if occurrence then toySwappedConstraintGeneratedObject
    else toyConstraintGeneratedObject
  openStep := fun _ _ _ => True
  continuationEvidence := boolWholeObjectEvidence
  continuation_grounded := by
    intro source target evidence
    exact ⟨(), trivial⟩
  experimentLaw := boolWholeObjectLaw
  identityConverges := bool_whole_object_identity_converges

/--
Whole-object identity permits state change and distinct qualified static
snapshots.  Token identity is therefore neither state equality nor snapshot
record equality.
-/
theorem sameToken_allows_changed_state_and_snapshot :
    boolDynamicQualifiedObject.SameToken false true ∧
      false ≠ true ∧
      boolDynamicQualifiedObject.snapshot false ≠
        boolDynamicQualifiedObject.snapshot true ∧
      KernelQualification toyConstraintModel Unit Bool toyFormedBy
        toyContinuesAt toyRobustAtScale
        (boolDynamicQualifiedObject.snapshot false).occurrence.root
        (boolDynamicQualifiedObject.snapshot false).occurrence.provenance ∧
      KernelQualification toyConstraintModel Unit Bool toyFormedBy
        toyContinuesAt toyRobustAtScale
        (boolDynamicQualifiedObject.snapshot true).occurrence.root
        (boolDynamicQualifiedObject.snapshot true).occurrence.provenance := by
  refine ⟨.ofEvidence trivial, by decide, ?_,
    boolDynamicQualifiedObject.snapshot_qualified false,
    boolDynamicQualifiedObject.snapshot_qualified true⟩
  simpa [boolDynamicQualifiedObject] using toy_static_snapshots_are_distinct

/-! ## Recursive composition preserves every locally inherited qualification -/

/-- Every member of a list satisfies a predicate. -/
def EveryObject
    {Object : Type*}
    (predicate : Object → Prop)
    (objects : List Object) : Prop :=
  ∀ object, object ∈ objects → predicate object

/-- A local child-for-parent rewrite preserves any locally inherited predicate. -/
theorem decompositionStep_preserves_everyObject
    {Object : Type*}
    {realizes : RealizesChildren Object}
    {predicate : Object → Prop}
    (locallyInherited : ∀ {children parent},
      realizes children parent → predicate parent →
        EveryObject predicate children)
    {first second : List Object}
    (step : DecompositionStep realizes first second)
    (firstQualified : EveryObject predicate first) :
    EveryObject predicate second := by
  cases step with
  | replace before children after parent witness =>
      have beforeQualified : EveryObject predicate before := by
        intro object member
        exact firstQualified object (by simp [member])
      have parentQualified : predicate parent :=
        firstQualified parent (by simp)
      have childrenQualified : EveryObject predicate children :=
        locallyInherited witness parentQualified
      have afterQualified : EveryObject predicate after := by
        intro object member
        exact firstQualified object (by simp [member])
      intro object member
      rw [List.mem_append] at member
      rcases member with prefixMember | afterMember
      · rw [List.mem_append] at prefixMember
        rcases prefixMember with beforeMember | childMember
        · exact beforeQualified object beforeMember
        · exact childrenQualified object childMember
      · exact afterQualified object afterMember

/-- The reflexive-transitive recursive decomposition inherits the local law. -/
theorem multiLevelDecomposition_preserves_everyObject
    {Object : Type*}
    {realizes : RealizesChildren Object}
    {predicate : Object → Prop}
    (locallyInherited : ∀ {children parent},
      realizes children parent → predicate parent →
        EveryObject predicate children)
    {first terminal : List Object}
    (decomposition : MultiLevelDecomposition realizes first terminal)
    (firstQualified : EveryObject predicate first) :
    EveryObject predicate terminal := by
  induction decomposition with
  | root => exact firstQualified
  | tail previous step inductionHypothesis =>
      exact decompositionStep_preserves_everyObject
        locallyInherited step inductionHypothesis

/--
Specialization: recursive composition of whole-object occurrences stays inside
the qualified occurrence type.  The theorem assumes no unique decomposition.
-/
theorem DynamicQualifiedObject.multiLevelComposition_snapshots_qualified
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {MemberOccurrence : Type uMemberOccurrence}
    {MemberExperiment : Type uMemberExperiment}
    {MemberOutcome : Type uMemberOutcome}
    {memberEvidence : BinaryRelation MemberOccurrence}
    {memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome}
    {ObjectOccurrence : Type uObjectOccurrence}
    {Input : Type uInput}
    {ObjectExperiment : Type uObjectExperiment}
    {ObjectOutcome : Type uObjectOutcome}
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome)
    {realizes : RealizesChildren ObjectOccurrence}
    {first terminal : List ObjectOccurrence}
    (decomposition : MultiLevelDecomposition realizes first terminal) :
    EveryObject
      (fun occurrence =>
        KernelQualification model Provenance Time formedBy continuesAt
          robustAtScale (object.snapshot occurrence).occurrence.root
          (object.snapshot occurrence).occurrence.provenance)
      terminal := by
  apply multiLevelDecomposition_preserves_everyObject
    (realizes := realizes)
    (predicate := fun occurrence =>
      KernelQualification model Provenance Time formedBy continuesAt
        robustAtScale (object.snapshot occurrence).occurrence.root
        (object.snapshot occurrence).occurrence.provenance)
    (decomposition := decomposition)
  · intro children parent realization parentQualified child member
    exact object.snapshot_qualified child
  · intro occurrence member
    exact object.snapshot_qualified occurrence

end OCKIndividuationMSpaceComposition
