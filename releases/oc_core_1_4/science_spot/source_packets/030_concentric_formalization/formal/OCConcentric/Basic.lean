namespace OCConcentric

inductive Contour where
  | center
  | adequacy
  | operators
  | kLadder
  | theoremSchemas
  | laws
  | crown
  | domains
  deriving DecidableEq, Repr

def contourRank : Contour → Nat
  | Contour.center => 0
  | Contour.adequacy => 1
  | Contour.operators => 2
  | Contour.kLadder => 3
  | Contour.theoremSchemas => 4
  | Contour.laws => 5
  | Contour.crown => 6
  | Contour.domains => 7

theorem contourRank_injective :
    Function.Injective contourRank := by
  intro a b h
  cases a <;> cases b <;> simp [contourRank] at h ⊢

inductive StressResponse where
  | absorption
  | extension
  | collapse
  | underdetermined
  deriving DecidableEq, Repr

structure StressContext where
  evidenceBound : Prop
  sameDescriptionRepair : Prop
  extensionRepair : Prop
  invariantFailure : Prop

open StressResponse

noncomputable def classify (C : StressContext) : StressResponse := by
  classical
  exact
    if hE : C.evidenceBound then
      if hS : C.sameDescriptionRepair then
        absorption
      else if hX : C.extensionRepair then
        extension
      else if hC : C.invariantFailure then
        collapse
      else
        underdetermined
    else
      underdetermined

theorem center_four_outcome_total (C : StressContext) :
    classify C = absorption ∨
    classify C = extension ∨
    classify C = collapse ∨
    classify C = underdetermined := by
  cases classify C <;> simp

theorem center_absorption_repairs_old_fork
    (C : StressContext)
    (hE : C.evidenceBound)
    (hS : C.sameDescriptionRepair) :
    classify C = absorption := by
  classical
  simp [classify, hE, hS]

inductive AdequacyRole where
  | observationCoverage
  | distinguishability
  | stateDynamics
  | constraintPressure
  | sameRepair
  | extension
  | collapse
  | underdetermination
  | projectionNonInflation
  | evidenceBinding
  | compositionalRefinement
  deriving DecidableEq, Repr

structure MetaLanguage where
  HasRole : AdequacyRole → Prop

def Adequate (L : MetaLanguage) : Prop :=
  ∀ r : AdequacyRole, L.HasRole r

def missingRoleLanguage (missing : AdequacyRole) : MetaLanguage :=
  { HasRole := fun r => r ≠ missing }

theorem adequacy_no_role_eliminable
    (missing : AdequacyRole) :
    ¬ Adequate (missingRoleLanguage missing) := by
  intro h
  exact (h missing) rfl

inductive OperatorRole where
  | introduce
  | differentiate
  | stabilize
  | project
  | invalidate
  | repair
  deriving DecidableEq, Repr

def operatorCode : OperatorRole → Nat
  | OperatorRole.introduce => 0
  | OperatorRole.differentiate => 1
  | OperatorRole.stabilize => 2
  | OperatorRole.project => 3
  | OperatorRole.invalidate => 4
  | OperatorRole.repair => 5

theorem operatorCode_injective :
    Function.Injective operatorCode := by
  intro a b h
  cases a <;> cases b <;> simp [operatorCode] at h ⊢

structure OperatorLanguage where
  HasOperator : OperatorRole → Prop

def OperatorAdequate (L : OperatorLanguage) : Prop :=
  ∀ r : OperatorRole, L.HasOperator r

def missingOperatorLanguage (missing : OperatorRole) : OperatorLanguage :=
  { HasOperator := fun r => r ≠ missing }

theorem operators_no_role_eliminable
    (missing : OperatorRole) :
    ¬ OperatorAdequate (missingOperatorLanguage missing) := by
  intro h
  exact (h missing) rfl

def kRank (n : Nat) : Nat := n

theorem k_adjacent_noncollapse (n : Nat) :
    kRank n < kRank (n + 1) := by
  exact Nat.lt_succ_self n

def kLadder (maxDepth : Nat) : List Nat :=
  List.range (maxDepth + 1)

theorem k_reference_depth_12_count :
    (kLadder 12).length = 13 := by
  native_decide

theorem k_absolute_count_guard :
    ∃ alternativeDepth : Nat, (kLadder alternativeDepth).length ≠ 13 := by
  exact ⟨13, by native_decide⟩

structure TheoremSchema where
  dependenciesClosed : Prop
  proofArtifact : Prop
  falsifier : Prop

def SchemaAdmissible (S : TheoremSchema) : Prop :=
  S.dependenciesClosed ∧ S.proofArtifact ∧ S.falsifier

theorem theorem_schema_requires_closed_dependencies
    (S : TheoremSchema)
    (h : SchemaAdmissible S) :
    S.dependenciesClosed := by
  exact h.left

structure LawCandidate where
  trigger : Prop
  scope : Prop
  outcomeCriterion : Prop
  falsifier : Prop

def LawAdmissible (L : LawCandidate) : Prop :=
  L.trigger ∧ L.scope ∧ L.outcomeCriterion ∧ L.falsifier

theorem law_requires_falsifier
    (L : LawCandidate)
    (h : LawAdmissible L) :
    L.falsifier := by
  exact h.right.right.right

structure LocalEvidence where
  observables : Prop
  constraints : Prop
  operators : Prop
  invariants : Prop
  falsifiers : Prop
  evidenceBindings : Prop

def LocalEvidenceComplete (E : LocalEvidence) : Prop :=
  E.observables ∧ E.constraints ∧ E.operators ∧
  E.invariants ∧ E.falsifiers ∧ E.evidenceBindings

structure DomainProjection where
  coreSignature : Prop
  localEvidence : LocalEvidence

def DomainProjectionValidated (D : DomainProjection) : Prop :=
  D.coreSignature ∧ LocalEvidenceComplete D.localEvidence

def emptyEvidence : LocalEvidence :=
  { observables := False, constraints := False, operators := False,
    invariants := False, falsifiers := False, evidenceBindings := False }

def coreOnlyDomainProjection : DomainProjection :=
  { coreSignature := True, localEvidence := emptyEvidence }

theorem domain_projection_requires_local_evidence
    (D : DomainProjection)
    (h : DomainProjectionValidated D) :
    LocalEvidenceComplete D.localEvidence := by
  exact h.right

theorem core_signature_alone_not_domain_proof :
    coreOnlyDomainProjection.coreSignature ∧
    ¬ DomainProjectionValidated coreOnlyDomainProjection := by
  constructor
  · trivial
  · intro h
    exact h.right.left

def CrownPromoted (D : DomainProjection) : Prop :=
  DomainProjectionValidated D

theorem crown_not_core_without_local_evidence :
    ¬ CrownPromoted coreOnlyDomainProjection := by
  intro h
  exact h.right.left

end OCConcentric
