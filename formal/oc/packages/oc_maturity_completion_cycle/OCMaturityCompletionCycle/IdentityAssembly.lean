import OCProjectionCausalityIdentity.SeparatedTypes

/-!
# Continuation evidence and generated identity assemblies

Continuation evidence is a directed relation on occurrences. It does not use
or presuppose a `same object` predicate. A closure policy is an independent
scientific choice: equivalence closure generates quotient identity, directed
closure generates lineage, and a membership relation represents overlap.
-/

namespace OCMaturityCompletionCycle

universe uOccurrence uIdentity

abbrev BinaryRelation (Occurrence : Type uOccurrence) :=
  Occurrence → Occurrence → Prop

/-- Directed continuation evidence, before any persistence policy is chosen. -/
structure ContinuationEvidence (Occurrence : Type uOccurrence) where
  relates : BinaryRelation Occurrence

/-- Inclusion order on binary relations. -/
def RelationRefines
    {Occurrence : Type uOccurrence}
    (left right : BinaryRelation Occurrence) : Prop :=
  ∀ ⦃source target⦄, left source target → right source target

/-- The policy used to turn evidence into a persistence-shaped object. -/
inductive RelationClosurePolicy
  | equivalenceIdentity
  | directedLineage
  | overlapMembership
  deriving DecidableEq, Repr

/-- Reflexive, symmetric, transitive closure of directed evidence. -/
inductive EquivalenceGenerated
    {Occurrence : Type uOccurrence}
    (evidence : BinaryRelation Occurrence) : BinaryRelation Occurrence
  | ofEvidence {source target} :
      evidence source target → EquivalenceGenerated evidence source target
  | refl (occurrence) : EquivalenceGenerated evidence occurrence occurrence
  | symm {source target} :
      EquivalenceGenerated evidence source target →
        EquivalenceGenerated evidence target source
  | trans {source middle target} :
      EquivalenceGenerated evidence source middle →
      EquivalenceGenerated evidence middle target →
        EquivalenceGenerated evidence source target

namespace EquivalenceGenerated

theorem isReflexive
    {Occurrence : Type uOccurrence}
    {evidence : BinaryRelation Occurrence} :
    Reflexive (EquivalenceGenerated evidence) := by
  intro occurrence
  exact .refl occurrence

theorem isSymmetric
    {Occurrence : Type uOccurrence}
    {evidence : BinaryRelation Occurrence} :
    Symmetric (EquivalenceGenerated evidence) := by
  intro source target related
  exact .symm related

theorem isTransitive
    {Occurrence : Type uOccurrence}
    {evidence : BinaryRelation Occurrence} :
    Transitive (EquivalenceGenerated evidence) := by
  intro source middle target first second
  exact .trans first second

/--
Equivalence closure is the least equivalence relation containing the evidence.
-/
theorem minimal
    {Occurrence : Type uOccurrence}
    {evidence target : BinaryRelation Occurrence}
    (containsEvidence : RelationRefines evidence target)
    (targetReflexive : Reflexive target)
    (targetSymmetric : Symmetric target)
    (targetTransitive : Transitive target) :
    RelationRefines (EquivalenceGenerated evidence) target := by
  intro source destination generated
  induction generated with
  | ofEvidence edge => exact containsEvidence edge
  | refl occurrence => exact targetReflexive occurrence
  | symm _ inductionHypothesis => exact targetSymmetric inductionHypothesis
  | trans _ _ firstHypothesis secondHypothesis =>
      exact targetTransitive firstHypothesis secondHypothesis

end EquivalenceGenerated

/-- Reflexive, transitive directed closure of continuation evidence. -/
inductive LineageGenerated
    {Occurrence : Type uOccurrence}
    (evidence : BinaryRelation Occurrence) : BinaryRelation Occurrence
  | ofEvidence {source target} :
      evidence source target → LineageGenerated evidence source target
  | refl (occurrence) : LineageGenerated evidence occurrence occurrence
  | trans {source middle target} :
      LineageGenerated evidence source middle →
      LineageGenerated evidence middle target →
        LineageGenerated evidence source target

namespace LineageGenerated

theorem isReflexive
    {Occurrence : Type uOccurrence}
    {evidence : BinaryRelation Occurrence} :
    Reflexive (LineageGenerated evidence) := by
  intro occurrence
  exact .refl occurrence

theorem isTransitive
    {Occurrence : Type uOccurrence}
    {evidence : BinaryRelation Occurrence} :
    Transitive (LineageGenerated evidence) := by
  intro source middle target first second
  exact .trans first second

/-- Lineage closure is the least preorder relation containing the evidence. -/
theorem minimal
    {Occurrence : Type uOccurrence}
    {evidence target : BinaryRelation Occurrence}
    (containsEvidence : RelationRefines evidence target)
    (targetReflexive : Reflexive target)
    (targetTransitive : Transitive target) :
    RelationRefines (LineageGenerated evidence) target := by
  intro source destination generated
  induction generated with
  | ofEvidence edge => exact containsEvidence edge
  | refl occurrence => exact targetReflexive occurrence
  | trans _ _ firstHypothesis secondHypothesis =>
      exact targetTransitive firstHypothesis secondHypothesis

end LineageGenerated

/-- Quotient-style identity: an explicitly certified equivalence relation. -/
structure EquivalenceIdentityAssembly (Occurrence : Type uOccurrence) where
  same : BinaryRelation Occurrence
  reflexive : Reflexive same
  symmetric : Symmetric same
  transitive : Transitive same

/-- Persistence lineage: an explicitly certified preorder, not a quotient. -/
structure LineageAssembly (Occurrence : Type uOccurrence) where
  precedes : BinaryRelation Occurrence
  reflexive : Reflexive precedes
  transitive : Transitive precedes

/-- Many-to-many identity membership, suitable for overlap and fusion. -/
structure OverlapAssembly
    (Occurrence : Type uOccurrence)
    (Identity : Type uIdentity) where
  member : Occurrence → Identity → Prop
  covered : ∀ occurrence, ∃ identity, member occurrence identity

/-- A function realizes every and only the declared membership assertions. -/
def RealizesMembership
    {Occurrence : Type uOccurrence}
    {Identity : Type uIdentity}
    (assembly : OverlapAssembly Occurrence Identity)
    (objectOf : Occurrence → Identity) : Prop :=
  ∀ occurrence identity,
    assembly.member occurrence identity ↔ objectOf occurrence = identity

/-- Each occurrence has exactly one declared assembly member. -/
def HasUniqueMember
    {Occurrence : Type uOccurrence}
    {Identity : Type uIdentity}
    (assembly : OverlapAssembly Occurrence Identity) : Prop :=
  ∀ occurrence, ∃! identity, assembly.member occurrence identity

/-- Exact boundary: relational membership is functional iff membership is unique. -/
theorem realizesMembership_iff_hasUniqueMember
    {Occurrence : Type uOccurrence}
    {Identity : Type uIdentity}
    (assembly : OverlapAssembly Occurrence Identity) :
    (∃ objectOf, RealizesMembership assembly objectOf) ↔
      HasUniqueMember assembly := by
  constructor
  · rintro ⟨objectOf, realizes⟩ occurrence
    refine ⟨objectOf occurrence, (realizes occurrence _).2 rfl, ?_⟩
    intro identity membership
    exact ((realizes occurrence identity).1 membership).symm
  · intro uniqueMember
    classical
    let objectOf : Occurrence → Identity := fun occurrence =>
      Classical.choose (uniqueMember occurrence)
    refine ⟨objectOf, ?_⟩
    intro occurrence identity
    have chosen := Classical.choose_spec (uniqueMember occurrence)
    constructor
    · intro membership
      exact (chosen.2 identity membership).symm
    · intro equality
      rw [← equality]
      exact chosen.1

/-- A single overlap at one occurrence forbids exact functional realization. -/
theorem overlap_precludes_functional_membership
    {Occurrence : Type uOccurrence}
    {Identity : Type uIdentity}
    (assembly : OverlapAssembly Occurrence Identity)
    {occurrence : Occurrence}
    {left right : Identity}
    (leftMember : assembly.member occurrence left)
    (rightMember : assembly.member occurrence right)
    (distinct : left ≠ right) :
    ¬ ∃ objectOf, RealizesMembership assembly objectOf := by
  rintro ⟨objectOf, realizes⟩
  have leftEquality := (realizes occurrence left).1 leftMember
  have rightEquality := (realizes occurrence right).1 rightMember
  exact distinct (leftEquality.symm.trans rightEquality)

/-- A functional identity map preserves continuation by collapsing each edge. -/
def ContinuationPreserving
    {Occurrence : Type uOccurrence}
    {Identity : Type uIdentity}
    (evidence : BinaryRelation Occurrence)
    (objectOf : Occurrence → Identity) : Prop :=
  ∀ ⦃source target⦄, evidence source target → objectOf source = objectOf target

/--
Branching alone is not inconsistent. It becomes a no-go for a functional
identity only when the two children are independently required to be distinct.
-/
theorem branching_with_required_separation_no_go
    {Occurrence : Type uOccurrence}
    {Identity : Type uIdentity}
    {evidence : BinaryRelation Occurrence}
    {objectOf : Occurrence → Identity}
    {parent leftChild rightChild : Occurrence}
    (preserves : ContinuationPreserving evidence objectOf)
    (leftBranch : evidence parent leftChild)
    (rightBranch : evidence parent rightChild)
    (childrenDistinct : objectOf leftChild ≠ objectOf rightChild) : False := by
  apply childrenDistinct
  exact (preserves leftBranch).symm.trans (preserves rightBranch)

/-- Fusion plus independently required parent separation has the dual no-go. -/
theorem fusion_with_required_separation_no_go
    {Occurrence : Type uOccurrence}
    {Identity : Type uIdentity}
    {evidence : BinaryRelation Occurrence}
    {objectOf : Occurrence → Identity}
    {leftParent rightParent child : Occurrence}
    (preserves : ContinuationPreserving evidence objectOf)
    (leftFusion : evidence leftParent child)
    (rightFusion : evidence rightParent child)
    (parentsDistinct : objectOf leftParent ≠ objectOf rightParent) : False := by
  apply parentsDistinct
  exact (preserves leftFusion).trans (preserves rightFusion).symm

/-- Intersection of every relation admitted by a family predicate. -/
def FamilyIntersection
    {Occurrence : Type uOccurrence}
    (family : BinaryRelation Occurrence → Prop) : BinaryRelation Occurrence :=
  fun source target =>
    ∀ relation, family relation → relation source target

/-- Universal property of the least relation in the inclusion order. -/
structure AssemblyUniversalProperty
    {Occurrence : Type uOccurrence}
    (family : BinaryRelation Occurrence → Prop)
    (generated : BinaryRelation Occurrence) : Prop where
  admitted : family generated
  least : ∀ relation, family relation → RelationRefines generated relation

/-- Admission depends only on the pointwise content of a relation. -/
def RelationExtensionalFamily
    {Occurrence : Type uOccurrence}
    (family : BinaryRelation Occurrence → Prop) : Prop :=
  ∀ ⦃left right⦄,
    (∀ source target, left source target ↔ right source target) →
      family left → family right

/-- Existence and equality-level uniqueness of a least admitted relation. -/
def HasUniqueLeastRelation
    {Occurrence : Type uOccurrence}
    (family : BinaryRelation Occurrence → Prop) : Prop :=
  ∃! generated, AssemblyUniversalProperty family generated

theorem familyIntersection_isLeast
    {Occurrence : Type uOccurrence}
    {family : BinaryRelation Occurrence → Prop}
    (intersectionAdmitted : family (FamilyIntersection family)) :
    AssemblyUniversalProperty family (FamilyIntersection family) := by
  refine ⟨intersectionAdmitted, ?_⟩
  intro relation relationAdmitted source target inIntersection
  exact inIntersection relation relationAdmitted

theorem leastRelation_pointwise_eq_familyIntersection
    {Occurrence : Type uOccurrence}
    {family : BinaryRelation Occurrence → Prop}
    {generated : BinaryRelation Occurrence}
    (universal : AssemblyUniversalProperty family generated) :
    ∀ source target,
      generated source target ↔ FamilyIntersection family source target := by
  intro source target
  constructor
  · intro inGenerated relation relationAdmitted
    exact universal.least relation relationAdmitted inGenerated
  · intro inIntersection
    exact inIntersection generated universal.admitted

theorem leastRelation_unique
    {Occurrence : Type uOccurrence}
    {family : BinaryRelation Occurrence → Prop}
    {left right : BinaryRelation Occurrence}
    (leftUniversal : AssemblyUniversalProperty family left)
    (rightUniversal : AssemblyUniversalProperty family right) :
    left = right := by
  funext source target
  apply propext
  exact ⟨fun inLeft =>
      leftUniversal.least right rightUniversal.admitted inLeft,
    fun inRight =>
      rightUniversal.least left leftUniversal.admitted inRight⟩

/--
Exact characterization. It concerns a least admissible relation, not a merely
unique minimal element and not uniqueness of every admissible assembly.
-/
theorem uniqueLeastRelation_iff_intersectionAdmitted
    {Occurrence : Type uOccurrence}
    {family : BinaryRelation Occurrence → Prop}
    (extensional : RelationExtensionalFamily family) :
    HasUniqueLeastRelation family ↔
      family (FamilyIntersection family) := by
  constructor
  · rintro ⟨generated, universal, _⟩
    apply extensional (leastRelation_pointwise_eq_familyIntersection universal)
    exact universal.admitted
  · intro intersectionAdmitted
    have universal := familyIntersection_isLeast intersectionAdmitted
    refine ⟨FamilyIntersection family, universal, ?_⟩
    intro candidate candidateUniversal
    exact leastRelation_unique candidateUniversal universal

/-- Closure under intersections indexed by an arbitrary type. -/
def ClosedUnderIndexedIntersections
    {Occurrence : Type uOccurrence}
    (family : BinaryRelation Occurrence → Prop) : Prop :=
  ∀ {Index : Type uOccurrence} (relations : Index → BinaryRelation Occurrence),
    (∀ index, family (relations index)) →
      family (fun source target => ∀ index, relations index source target)

/-- A genuine nonempty Moore family is sufficient for a unique least relation. -/
theorem mooreFamily_hasUniqueLeastRelation
    {Occurrence : Type uOccurrence}
    {family : BinaryRelation Occurrence → Prop}
    (extensional : RelationExtensionalFamily family)
    (_nonempty : ∃ relation, family relation)
    (closed : ClosedUnderIndexedIntersections family) :
    HasUniqueLeastRelation family := by
  apply (uniqueLeastRelation_iff_intersectionAdmitted extensional).2
  let Admitted := { relation : BinaryRelation Occurrence // family relation }
  let indexedIntersection : BinaryRelation Occurrence :=
    fun source target => ∀ relation : Admitted, relation.1 source target
  have indexedAdmitted : family indexedIntersection := by
    exact closed (Index := Admitted) (fun relation : Admitted => relation.1)
      (fun relation : Admitted => relation.2)
  apply extensional (left := indexedIntersection)
    (right := FamilyIntersection family) _ indexedAdmitted
  intro source target
  constructor
  · intro inIndexed relation relationAdmitted
    exact inIndexed ⟨relation, relationAdmitted⟩
  · intro inFamily relation
    exact inFamily relation.1 relation.2

/-- Kernel inclusion between two concrete assembly maps. -/
def MapKernelRefines
    {Occurrence : Type uOccurrence}
    {LeftIdentity RightIdentity : Type uIdentity}
    (left : Occurrence → LeftIdentity)
    (right : Occurrence → RightIdentity) : Prop :=
  ∀ ⦃first second⦄, left first = left second → right first = right second

/-! ## Finite policy and crossing-context countermodels -/

inductive ForkOccurrence
  | root
  | left
  | right
  deriving DecidableEq, Repr

def forkEvidence : BinaryRelation ForkOccurrence
  | .root, .left => True
  | .root, .right => True
  | _, _ => False

def forkOverlap : OverlapAssembly ForkOccurrence Bool where
  member
    | .root, _ => True
    | .left, false => True
    | .right, true => True
    | _, _ => False
  covered
    | .root => ⟨false, trivial⟩
    | .left => ⟨false, trivial⟩
    | .right => ⟨true, trivial⟩

theorem fork_equivalence_relates_left_to_root :
    EquivalenceGenerated forkEvidence .left .root := by
  exact .symm (.ofEvidence trivial)

def forkRank : ForkOccurrence → Nat
  | .root => 0
  | .left => 1
  | .right => 1

theorem forkEvidence_rank_monotone :
    RelationRefines forkEvidence (fun source target => forkRank source ≤ forkRank target) := by
  intro source target edge
  cases source <;> cases target <;> simp_all [forkEvidence, forkRank]

theorem fork_lineage_does_not_run_left_to_root :
    ¬ LineageGenerated forkEvidence .left .root := by
  intro lineage
  have rankOrder : forkRank ForkOccurrence.left ≤ forkRank ForkOccurrence.root :=
    LineageGenerated.minimal forkEvidence_rank_monotone
      (fun occurrence => Nat.le_refl (forkRank occurrence))
      (fun _ _ _ => Nat.le_trans) lineage
  simp [forkRank] at rankOrder

theorem fork_overlap_is_not_functional :
    ¬ ∃ objectOf, RealizesMembership forkOverlap objectOf := by
  exact overlap_precludes_functional_membership forkOverlap
    (occurrence := .root) (left := false) (right := true)
    trivial trivial Bool.false_ne_true

/--
The equivalence and lineage readings come from the same fork evidence. The
overlap failure uses a separately declared membership assembly; this theorem
does not claim that `forkOverlap` is generated by `forkEvidence`.
-/
theorem fork_relations_and_independent_overlap_are_not_interchangeable :
    EquivalenceGenerated forkEvidence .left .root ∧
      ¬ LineageGenerated forkEvidence .left .root ∧
      ¬ ∃ objectOf, RealizesMembership forkOverlap objectOf := by
  exact ⟨fork_equivalence_relates_left_to_root,
    fork_lineage_does_not_run_left_to_root,
    fork_overlap_is_not_functional⟩

inductive CrossingOccurrence
  | northWest
  | northEast
  | southWest
  | southEast
  deriving DecidableEq, Repr

def rowAssembly : CrossingOccurrence → Bool
  | .northWest | .northEast => false
  | .southWest | .southEast => true

def columnAssembly : CrossingOccurrence → Bool
  | .northWest | .southWest => false
  | .northEast | .southEast => true

theorem crossing_context_partitions_are_incomparable :
    ¬ MapKernelRefines rowAssembly columnAssembly ∧
      ¬ MapKernelRefines columnAssembly rowAssembly := by
  constructor
  · intro refinement
    have impossible := refinement
      (first := CrossingOccurrence.northWest)
      (second := CrossingOccurrence.northEast) rfl
    exact Bool.false_ne_true impossible
  · intro refinement
    have impossible := refinement
      (first := CrossingOccurrence.northWest)
      (second := CrossingOccurrence.southWest) rfl
    exact Bool.false_ne_true impossible

end OCMaturityCompletionCycle
