import OCKIndividuationMSpaceComposition.QualifiedObjectHierarchy

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe
  uSourceMechanism uSourceIntervention uSourceOutcome
  uTargetMechanism uTargetIntervention uTargetOutcome
  uProvenance uTime uAccess

/-!
# Qualification under explicit base change

Object qualification is not invariant under an arbitrary change of model or
resolution.  The contracts in this file expose the exact maps needed to
transport a causal carrier: mechanism, intervention and outcome maps;
commutation with actual and removal responses; outcome injectivity; and exact
port reflection.  Qualification additionally transports provenance, time,
robustness and typed access.

Atomic transport needs target-kernel reflection, because a refined model may
reveal new constituents.  Composite transport needs injectivity of the
mechanism map to preserve a distinct internal-dependency witness.  The two
iff theorems below are necessary-and-sufficient only relative to the complete
declared transport contract; they are not context-free invariance claims.
-/

/-! ## Causal-model base change -/

/-- A response-faithful typed map between active constraint models. -/
structure ActiveConstraintBaseChange
    {SourceMechanism : Type uSourceMechanism}
    {SourceIntervention : Type uSourceIntervention}
    {SourceOutcome : Type uSourceOutcome}
    {TargetMechanism : Type uTargetMechanism}
    {TargetIntervention : Type uTargetIntervention}
    {TargetOutcome : Type uTargetOutcome}
    (source : ActiveConstraintModel SourceMechanism SourceIntervention
      SourceOutcome)
    (target : ActiveConstraintModel TargetMechanism TargetIntervention
      TargetOutcome) where
  mechanismMap : SourceMechanism → TargetMechanism
  interventionMap : SourceIntervention → TargetIntervention
  outcomeMap : SourceOutcome → TargetOutcome
  outcomeMap_injective : Function.Injective outcomeMap
  response_commutes : ∀ mechanism intervention,
    outcomeMap (source.response mechanism intervention) =
      target.response (mechanismMap mechanism)
        (interventionMap intervention)
  responseWithout_commutes : ∀ affected support intervention,
    outcomeMap (source.responseWithout affected support intervention) =
      target.responseWithout (mechanismMap affected) (mechanismMap support)
        (interventionMap intervention)
  port_iff : ∀ mechanism,
    target.port (mechanismMap mechanism) ↔ source.port mechanism

namespace ActiveConstraintBaseChange

variable
  {SourceMechanism : Type uSourceMechanism}
  {SourceIntervention : Type uSourceIntervention}
  {SourceOutcome : Type uSourceOutcome}
  {TargetMechanism : Type uTargetMechanism}
  {TargetIntervention : Type uTargetIntervention}
  {TargetOutcome : Type uTargetOutcome}
  {source : ActiveConstraintModel SourceMechanism SourceIntervention
    SourceOutcome}
  {target : ActiveConstraintModel TargetMechanism TargetIntervention
    TargetOutcome}

/-- Exact response commutation and injective outcome comparison transport a
disable/removal difference witness. -/
def mapDifferenceWitness
    (change : ActiveConstraintBaseChange source target)
    {affected support : SourceMechanism}
    (witness : DifferenceWitness source affected support) :
    DifferenceWitness target (change.mechanismMap affected)
      (change.mechanismMap support) where
  intervention := change.interventionMap witness.intervention
  changes := by
    intro targetEqual
    apply witness.changes
    apply change.outcomeMap_injective
    calc
      change.outcomeMap
          (source.response affected witness.intervention) =
          target.response (change.mechanismMap affected)
            (change.interventionMap witness.intervention) :=
        change.response_commutes affected witness.intervention
      _ = target.responseWithout (change.mechanismMap affected)
            (change.mechanismMap support)
            (change.interventionMap witness.intervention) := targetEqual
      _ = change.outcomeMap
          (source.responseWithout affected support witness.intervention) :=
        (change.responseWithout_commutes affected support
          witness.intervention).symm

theorem mapEssentialDependency
    (change : ActiveConstraintBaseChange source target)
    {affected support : SourceMechanism}
    (dependency : EssentialDependency source affected support) :
    EssentialDependency target (change.mechanismMap affected)
      (change.mechanismMap support) := by
  rcases dependency with ⟨witness⟩
  exact ⟨change.mapDifferenceWitness witness⟩

/-- Port reflection is load-bearing: a mapped internal target cannot silently
become a boundary port. -/
theorem mapInternalDependency
    (change : ActiveConstraintBaseChange source target)
    {current next : SourceMechanism}
    (dependency : InternalDependency source current next) :
    InternalDependency target (change.mechanismMap current)
      (change.mechanismMap next) := by
  constructor
  · intro targetPort
    exact dependency.1 ((change.port_iff next).1 targetPort)
  · rcases dependency.2 with forward | backward
    · exact Or.inl (change.mapEssentialDependency forward)
    · exact Or.inr (change.mapEssentialDependency backward)

/-- Every member of the source generated kernel maps into the target generated
kernel.  Surjectivity onto the target kernel is a separate reflection premise. -/
theorem mapGeneratedKernel
    (change : ActiveConstraintBaseChange source target)
    (root : SourceMechanism)
    {mechanism : SourceMechanism}
    (generated : GeneratedKernel source root mechanism) :
    GeneratedKernel target (change.mechanismMap root)
      (change.mechanismMap mechanism) := by
  induction generated with
  | ofRoot => exact .ofRoot
  | ofInternalDependency previous dependency inductionHypothesis =>
      exact .ofInternalDependency inductionHypothesis
        (change.mapInternalDependency dependency)

end ActiveConstraintBaseChange

/-! ## Qualification doctrine and its transport contract -/

/-- The context-sensitive qualification predicates surrounding one causal
model.  Keeping these fields together prevents a carrier map from silently
changing provenance, time, robustness or access semantics. -/
structure QualificationDoctrine
    {Mechanism : Type uSourceMechanism}
    {Intervention : Type uSourceIntervention}
    {Outcome : Type uSourceOutcome}
    (model : ActiveConstraintModel Mechanism Intervention Outcome) where
  Provenance : Type uProvenance
  Time : Type uTime
  Access : Type uAccess
  formedBy : Mechanism → Provenance → Prop
  continuesAt : Mechanism → Time → Prop
  robustAtScale : (Mechanism → Prop) → Prop
  accessContext : AtomicAccessContext Mechanism Access

abbrev CommonQualificationAt
    {Mechanism : Type uSourceMechanism}
    {Intervention : Type uSourceIntervention}
    {Outcome : Type uSourceOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    (doctrine : QualificationDoctrine model)
    (root : Mechanism)
    (provenance : doctrine.Provenance) :=
  CommonKernelQualification model doctrine.Provenance doctrine.Time
    doctrine.formedBy doctrine.continuesAt doctrine.robustAtScale root
    provenance

abbrev AtomicQualificationAt
    {Mechanism : Type uSourceMechanism}
    {Intervention : Type uSourceIntervention}
    {Outcome : Type uSourceOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    (doctrine : QualificationDoctrine model)
    (root : Mechanism)
    (provenance : doctrine.Provenance) :=
  AtomicKernelQualification model doctrine.Provenance doctrine.Time
    doctrine.formedBy doctrine.continuesAt doctrine.robustAtScale
    doctrine.Access doctrine.accessContext root provenance

abbrev CompositeQualificationAt
    {Mechanism : Type uSourceMechanism}
    {Intervention : Type uSourceIntervention}
    {Outcome : Type uSourceOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    (doctrine : QualificationDoctrine model)
    (root : Mechanism)
    (provenance : doctrine.Provenance) :=
  CompositeKernelQualification model doctrine.Provenance doctrine.Time
    doctrine.formedBy doctrine.continuesAt doctrine.robustAtScale root
    provenance

/-- Full context transport surrounding a response-faithful causal-model map. -/
structure QualificationBaseChange
    {SourceMechanism : Type uSourceMechanism}
    {SourceIntervention : Type uSourceIntervention}
    {SourceOutcome : Type uSourceOutcome}
    {TargetMechanism : Type uTargetMechanism}
    {TargetIntervention : Type uTargetIntervention}
    {TargetOutcome : Type uTargetOutcome}
    {sourceModel : ActiveConstraintModel SourceMechanism SourceIntervention
      SourceOutcome}
    {targetModel : ActiveConstraintModel TargetMechanism TargetIntervention
      TargetOutcome}
    (source : QualificationDoctrine sourceModel)
    (target : QualificationDoctrine targetModel) where
  constraints : ActiveConstraintBaseChange sourceModel targetModel
  provenanceMap : source.Provenance → target.Provenance
  timeMap : source.Time → target.Time
  timeMap_injective : Function.Injective timeMap
  accessMap : source.Access → target.Access
  formedBy_preserves : ∀ ⦃mechanism provenance⦄,
    source.formedBy mechanism provenance →
      target.formedBy (constraints.mechanismMap mechanism)
        (provenanceMap provenance)
  continuesAt_preserves : ∀ ⦃mechanism time⦄,
    source.continuesAt mechanism time →
      target.continuesAt (constraints.mechanismMap mechanism) (timeMap time)
  robustness_preserves : ∀ root,
    source.robustAtScale (GeneratedKernel sourceModel root) →
      target.robustAtScale
        (GeneratedKernel targetModel (constraints.mechanismMap root))
  access_preserves : ∀ ⦃access mechanism⦄,
    source.accessContext.accesses access mechanism →
      target.accessContext.accesses (accessMap access)
        (constraints.mechanismMap mechanism)

namespace QualificationBaseChange

variable
  {SourceMechanism : Type uSourceMechanism}
  {SourceIntervention : Type uSourceIntervention}
  {SourceOutcome : Type uSourceOutcome}
  {TargetMechanism : Type uTargetMechanism}
  {TargetIntervention : Type uTargetIntervention}
  {TargetOutcome : Type uTargetOutcome}
  {sourceModel : ActiveConstraintModel SourceMechanism SourceIntervention
    SourceOutcome}
  {targetModel : ActiveConstraintModel TargetMechanism TargetIntervention
    TargetOutcome}
  {source : QualificationDoctrine sourceModel}
  {target : QualificationDoctrine targetModel}

variable (change : QualificationBaseChange source target)

/-- Common qualification transports under the explicit context contract. -/
def transportCommon
    {root : SourceMechanism}
    {provenance : source.Provenance}
    (qualification : CommonQualificationAt source root provenance) :
    CommonQualificationAt target (change.constraints.mechanismMap root)
      (change.provenanceMap provenance) where
  root_not_port := by
    intro targetPort
    exact qualification.root_not_port
      ((change.constraints.port_iff root).1 targetPort)
  provenance_grounded :=
    change.formedBy_preserves qualification.provenance_grounded
  persists_at_distinct_times := by
    rcases qualification.persists_at_distinct_times with
      ⟨start, finish, different, starts, finishes⟩
    refine ⟨change.timeMap start, change.timeMap finish, ?_,
      change.continuesAt_preserves starts,
      change.continuesAt_preserves finishes⟩
    intro mappedEqual
    exact different (change.timeMap_injective mappedEqual)
  scale_robust :=
    change.robustness_preserves root qualification.scale_robust

/-- Target-kernel reflection is the exact extra premise used by the atomic
transport theorem.  It is not inferred from forward causal preservation. -/
def GeneratedKernelReflects : Prop :=
  ∀ root targetMechanism,
    GeneratedKernel targetModel (change.constraints.mechanismMap root)
      targetMechanism →
    ∃ sourceMechanism,
      GeneratedKernel sourceModel root sourceMechanism ∧
        change.constraints.mechanismMap sourceMechanism = targetMechanism

theorem targetKernel_irreducible_of_reflection
    (reflects : change.GeneratedKernelReflects)
    {root : SourceMechanism}
    {provenance : source.Provenance}
    (atomic : AtomicQualificationAt source root provenance) :
    ∀ ⦃targetMechanism⦄,
      GeneratedKernel targetModel (change.constraints.mechanismMap root)
        targetMechanism →
      targetMechanism = change.constraints.mechanismMap root := by
  intro targetMechanism generated
  rcases reflects root targetMechanism generated with
    ⟨sourceMechanism, sourceGenerated, mapsToTarget⟩
  have sourceIsRoot := atomic.kernel_irreducible sourceGenerated
  calc
    targetMechanism = change.constraints.mechanismMap sourceMechanism :=
      mapsToTarget.symm
    _ = change.constraints.mechanismMap root :=
      congrArg change.constraints.mechanismMap sourceIsRoot

/-- Relative necessary-and-sufficient atomic criterion.  Common qualification
and access are already transported by `change`; the only remaining target
condition is irreducibility of its generated kernel. -/
theorem targetAtomicQualification_iff_kernelIrreducible
    {root : SourceMechanism}
    {provenance : source.Provenance}
    (atomic : AtomicQualificationAt source root provenance) :
    AtomicQualificationAt target (change.constraints.mechanismMap root)
        (change.provenanceMap provenance) ↔
      ∀ ⦃targetMechanism⦄,
        GeneratedKernel targetModel (change.constraints.mechanismMap root)
          targetMechanism →
        targetMechanism = change.constraints.mechanismMap root := by
  constructor
  · intro targetAtomic
    exact targetAtomic.kernel_irreducible
  · intro irreducible
    exact
      { common := change.transportCommon atomic.common
        kernel_irreducible := irreducible
        externally_accessible := by
          rcases atomic.externally_accessible with ⟨access, accesses⟩
          exact ⟨change.accessMap access,
            change.access_preserves accesses⟩ }

/-- Atomicity transports only after target-kernel reflection is supplied. -/
def transportAtomic
    (reflects : change.GeneratedKernelReflects)
    {root : SourceMechanism}
    {provenance : source.Provenance}
    (atomic : AtomicQualificationAt source root provenance) :
    AtomicQualificationAt target (change.constraints.mechanismMap root)
      (change.provenanceMap provenance) :=
  (change.targetAtomicQualification_iff_kernelIrreducible atomic).2
    (change.targetKernel_irreducible_of_reflection reflects atomic)

/-- Composite qualification transports when distinct mechanisms remain
distinct.  Forward kernel and dependency preservation are already consequences
of the causal-model base-change contract. -/
def transportComposite
    (mechanismMap_injective :
      Function.Injective change.constraints.mechanismMap)
    {root : SourceMechanism}
    {provenance : source.Provenance}
    (composite : CompositeQualificationAt source root provenance) :
    CompositeQualificationAt target (change.constraints.mechanismMap root)
      (change.provenanceMap provenance) where
  root_not_port :=
    (change.transportCommon composite.toCommon).root_not_port
  provenance_grounded :=
    (change.transportCommon composite.toCommon).provenance_grounded
  persists_at_distinct_times :=
    (change.transportCommon composite.toCommon).persists_at_distinct_times
  scale_robust :=
    (change.transportCommon composite.toCommon).scale_robust
  internally_integrated := by
    rcases composite.internally_integrated with
      ⟨first, second, firstGenerated, secondGenerated, different, dependency⟩
    refine ⟨change.constraints.mechanismMap first,
      change.constraints.mechanismMap second,
      change.constraints.mapGeneratedKernel root firstGenerated,
      change.constraints.mapGeneratedKernel root secondGenerated, ?_,
      change.constraints.mapInternalDependency dependency⟩
    intro mappedEqual
    exact different (mechanismMap_injective mappedEqual)

/-- Relative necessary-and-sufficient composite criterion.  Once common
qualification has been transported, target composite qualification is exactly
the existence of its declared nontrivial internal witness. -/
theorem targetCompositeQualification_iff_internalWitness
    {root : SourceMechanism}
    {provenance : source.Provenance}
    (common : CommonQualificationAt source root provenance) :
    CompositeQualificationAt target (change.constraints.mechanismMap root)
        (change.provenanceMap provenance) ↔
      ∃ first second,
        GeneratedKernel targetModel (change.constraints.mechanismMap root)
          first ∧
        GeneratedKernel targetModel (change.constraints.mechanismMap root)
          second ∧
        first ≠ second ∧ InternalDependency targetModel first second := by
  constructor
  · intro targetComposite
    exact targetComposite.internally_integrated
  · intro integrated
    let transported := change.transportCommon common
    exact
      { root_not_port := transported.root_not_port
        provenance_grounded := transported.provenance_grounded
        internally_integrated := integrated
        persists_at_distinct_times := transported.persists_at_distinct_times
        scale_robust := transported.scale_robust }

end QualificationBaseChange

/-! ## Bidirectional base isomorphism and exact grade preservation -/

/-- A genuine qualification-base isomorphism consists of admitted base changes
in both directions whose carrier and contextual maps are mutual inverses.
Unlike `GeneratedKernelReflects` or mechanism injectivity, this is not a
one-way sufficient transport premise. -/
structure QualificationBaseIsomorphism
    {SourceMechanism : Type uSourceMechanism}
    {SourceIntervention : Type uSourceIntervention}
    {SourceOutcome : Type uSourceOutcome}
    {TargetMechanism : Type uTargetMechanism}
    {TargetIntervention : Type uTargetIntervention}
    {TargetOutcome : Type uTargetOutcome}
    {sourceModel : ActiveConstraintModel SourceMechanism SourceIntervention
      SourceOutcome}
    {targetModel : ActiveConstraintModel TargetMechanism TargetIntervention
      TargetOutcome}
    (source : QualificationDoctrine sourceModel)
    (target : QualificationDoctrine targetModel) where
  forward : QualificationBaseChange source target
  backward : QualificationBaseChange target source
  mechanism_forward_backward : ∀ mechanism,
    backward.constraints.mechanismMap
        (forward.constraints.mechanismMap mechanism) = mechanism
  mechanism_backward_forward : ∀ mechanism,
    forward.constraints.mechanismMap
        (backward.constraints.mechanismMap mechanism) = mechanism
  intervention_forward_backward : ∀ intervention,
    backward.constraints.interventionMap
        (forward.constraints.interventionMap intervention) = intervention
  intervention_backward_forward : ∀ intervention,
    forward.constraints.interventionMap
        (backward.constraints.interventionMap intervention) = intervention
  outcome_forward_backward : ∀ outcome,
    backward.constraints.outcomeMap
        (forward.constraints.outcomeMap outcome) = outcome
  outcome_backward_forward : ∀ outcome,
    forward.constraints.outcomeMap
        (backward.constraints.outcomeMap outcome) = outcome
  provenance_forward_backward : ∀ provenance,
    backward.provenanceMap (forward.provenanceMap provenance) = provenance
  provenance_backward_forward : ∀ provenance,
    forward.provenanceMap (backward.provenanceMap provenance) = provenance
  time_forward_backward : ∀ time,
    backward.timeMap (forward.timeMap time) = time
  time_backward_forward : ∀ time,
    forward.timeMap (backward.timeMap time) = time
  access_forward_backward : ∀ access,
    backward.accessMap (forward.accessMap access) = access
  access_backward_forward : ∀ access,
    forward.accessMap (backward.accessMap access) = access

namespace QualificationBaseIsomorphism

variable
  {SourceMechanism : Type uSourceMechanism}
  {SourceIntervention : Type uSourceIntervention}
  {SourceOutcome : Type uSourceOutcome}
  {TargetMechanism : Type uTargetMechanism}
  {TargetIntervention : Type uTargetIntervention}
  {TargetOutcome : Type uTargetOutcome}
  {sourceModel : ActiveConstraintModel SourceMechanism SourceIntervention
    SourceOutcome}
  {targetModel : ActiveConstraintModel TargetMechanism TargetIntervention
    TargetOutcome}
  {source : QualificationDoctrine sourceModel}
  {target : QualificationDoctrine targetModel}

variable (iso : QualificationBaseIsomorphism source target)

theorem forward_mechanismMap_injective :
    Function.Injective iso.forward.constraints.mechanismMap := by
  intro first second sameImage
  calc
    first = iso.backward.constraints.mechanismMap
        (iso.forward.constraints.mechanismMap first) :=
      (iso.mechanism_forward_backward first).symm
    _ = iso.backward.constraints.mechanismMap
        (iso.forward.constraints.mechanismMap second) :=
      congrArg iso.backward.constraints.mechanismMap sameImage
    _ = second := iso.mechanism_forward_backward second

theorem backward_mechanismMap_injective :
    Function.Injective iso.backward.constraints.mechanismMap := by
  intro first second sameImage
  calc
    first = iso.forward.constraints.mechanismMap
        (iso.backward.constraints.mechanismMap first) :=
      (iso.mechanism_backward_forward first).symm
    _ = iso.forward.constraints.mechanismMap
        (iso.backward.constraints.mechanismMap second) :=
      congrArg iso.forward.constraints.mechanismMap sameImage
    _ = second := iso.mechanism_backward_forward second

/-- Bidirectionality derives the forward target-kernel reflection premise that
was merely sufficient data in the one-way transport theorem. -/
def forwardGeneratedKernelReflects :
    iso.forward.GeneratedKernelReflects := by
  intro root targetMechanism generated
  have mappedBack := iso.backward.constraints.mapGeneratedKernel
    (iso.forward.constraints.mechanismMap root) generated
  refine ⟨iso.backward.constraints.mechanismMap targetMechanism, ?_, ?_⟩
  · simpa only [iso.mechanism_forward_backward root] using mappedBack
  · exact iso.mechanism_backward_forward targetMechanism

def backwardGeneratedKernelReflects :
    iso.backward.GeneratedKernelReflects := by
  intro root sourceMechanism generated
  have mappedForward := iso.forward.constraints.mapGeneratedKernel
    (iso.backward.constraints.mechanismMap root) generated
  refine ⟨iso.forward.constraints.mechanismMap sourceMechanism, ?_, ?_⟩
  · simpa only [iso.mechanism_backward_forward root] using mappedForward
  · exact iso.mechanism_forward_backward sourceMechanism

/-- Atomic qualification is preserved and reflected by a genuine base
isomorphism.  This is the N-and-S result; one-way kernel reflection remains
only a sufficient premise for `transportAtomic`. -/
theorem atomicQualification_iff
    {root : SourceMechanism}
    {provenance : source.Provenance} :
    AtomicQualificationAt source root provenance ↔
      AtomicQualificationAt target
        (iso.forward.constraints.mechanismMap root)
        (iso.forward.provenanceMap provenance) := by
  constructor
  · intro atomic
    exact iso.forward.transportAtomic iso.forwardGeneratedKernelReflects atomic
  · intro atomic
    have transportedBack := iso.backward.transportAtomic
      iso.backwardGeneratedKernelReflects atomic
    simpa only [iso.mechanism_forward_backward root,
      iso.provenance_forward_backward provenance] using transportedBack

/-- Composite qualification is preserved and reflected by a genuine base
isomorphism.  One-way mechanism injectivity remains only a sufficient premise
for `transportComposite`. -/
theorem compositeQualification_iff
    {root : SourceMechanism}
    {provenance : source.Provenance} :
    CompositeQualificationAt source root provenance ↔
      CompositeQualificationAt target
        (iso.forward.constraints.mechanismMap root)
        (iso.forward.provenanceMap provenance) := by
  constructor
  · intro composite
    exact iso.forward.transportComposite
      iso.forward_mechanismMap_injective composite
  · intro composite
    have transportedBack := iso.backward.transportComposite
      iso.backward_mechanismMap_injective composite
    simpa only [iso.mechanism_forward_backward root,
      iso.provenance_forward_backward provenance] using transportedBack

end QualificationBaseIsomorphism

/-- The two structural grade names, separated from their proof objects. -/
inductive QualificationGradeTag
  | atomic
  | composite
  deriving DecidableEq, Repr

/-- Predicate that one root has one declared grade in one doctrine. -/
def HasQualificationGrade
    {Mechanism : Type uSourceMechanism}
    {Intervention : Type uSourceIntervention}
    {Outcome : Type uSourceOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    (doctrine : QualificationDoctrine model)
    (root : Mechanism)
    (provenance : doctrine.Provenance) : QualificationGradeTag → Prop
  | .atomic => AtomicQualificationAt doctrine root provenance
  | .composite => CompositeQualificationAt doctrine root provenance

/-- Exact grade preservation and reflection, relative to the complete
bidirectional base-isomorphism contract. -/
theorem QualificationBaseIsomorphism.qualificationGrade_iff
    {SourceMechanism : Type uSourceMechanism}
    {SourceIntervention : Type uSourceIntervention}
    {SourceOutcome : Type uSourceOutcome}
    {TargetMechanism : Type uTargetMechanism}
    {TargetIntervention : Type uTargetIntervention}
    {TargetOutcome : Type uTargetOutcome}
    {sourceModel : ActiveConstraintModel SourceMechanism SourceIntervention
      SourceOutcome}
    {targetModel : ActiveConstraintModel TargetMechanism TargetIntervention
      TargetOutcome}
    {source : QualificationDoctrine sourceModel}
    {target : QualificationDoctrine targetModel}
    (iso : QualificationBaseIsomorphism source target)
    (grade : QualificationGradeTag)
    (root : SourceMechanism)
    (provenance : source.Provenance) :
    HasQualificationGrade source root provenance grade ↔
      HasQualificationGrade target
        (iso.forward.constraints.mechanismMap root)
        (iso.forward.provenanceMap provenance) grade := by
  cases grade with
  | atomic => exact iso.atomicQualification_iff
  | composite => exact iso.compositeQualification_iff

/-! ## The existing coarse/refined countermodel is the non-invariance witness -/

/-- Without an admitted base-change contract, the same carrier/root may change
grade.  This is not a contradiction: the intervention/dependency evidence has
changed. -/
theorem qualificationGrade_is_not_contextInvariant_without_contract :
    AtomicKernelQualification coarseToyConstraintModel Unit Bool toyFormedBy
        toyContinuesAt coarseToyRobustAtScale Unit coarseToyAccessContext
        .left () ∧
      CompositeKernelQualification toyConstraintModel Unit Bool toyFormedBy
        toyContinuesAt toyRobustAtScale .left () :=
  same_toy_root_is_atomic_coarse_and_composite_refined

end OCKIndividuationMSpaceComposition
