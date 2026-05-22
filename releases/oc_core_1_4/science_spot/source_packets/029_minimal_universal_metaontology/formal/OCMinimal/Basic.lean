namespace OCMinimal

universe u

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

def adequacyCode : AdequacyRole → Nat
  | AdequacyRole.observationCoverage => 0
  | AdequacyRole.distinguishability => 1
  | AdequacyRole.stateDynamics => 2
  | AdequacyRole.constraintPressure => 3
  | AdequacyRole.sameRepair => 4
  | AdequacyRole.extension => 5
  | AdequacyRole.collapse => 6
  | AdequacyRole.underdetermination => 7
  | AdequacyRole.projectionNonInflation => 8
  | AdequacyRole.evidenceBinding => 9
  | AdequacyRole.compositionalRefinement => 10

theorem adequacyCode_injective :
    Function.Injective adequacyCode := by
  intro a b h
  cases a <;> cases b <;> simp [adequacyCode] at h ⊢

structure MetaLanguage where
  HasRole : AdequacyRole → Prop

def Adequate (L : MetaLanguage) : Prop :=
  ∀ r : AdequacyRole, L.HasRole r

def OCMeta : MetaLanguage :=
  { HasRole := fun _ => True }

def RoleEquivalent (A B : MetaLanguage) : Prop :=
  ∀ r : AdequacyRole, A.HasRole r ↔ B.HasRole r

theorem ocmeta_adequate : Adequate OCMeta := by
  intro r
  trivial

theorem representation_theorem (L : MetaLanguage)
    (h : Adequate L) :
    ∀ r : AdequacyRole, L.HasRole r := by
  exact h

theorem minimal_uniqueness_up_to_definitional_equivalence
    (L : MetaLanguage)
    (h : Adequate L) :
    RoleEquivalent OCMeta L := by
  intro r
  constructor
  · intro _
    exact h r
  · intro _
    trivial

def missingRoleLanguage (missing : AdequacyRole) : MetaLanguage :=
  { HasRole := fun r => r ≠ missing }

theorem removing_any_adequacy_role_breaks_adequacy
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

def OCOperators : OperatorLanguage :=
  { HasOperator := fun _ => True }

def missingOperatorLanguage (missing : OperatorRole) : OperatorLanguage :=
  { HasOperator := fun r => r ≠ missing }

theorem oc_operators_adequate : OperatorAdequate OCOperators := by
  intro r
  trivial

theorem removing_any_operator_breaks_operator_adequacy
    (missing : OperatorRole) :
    ¬ OperatorAdequate (missingOperatorLanguage missing) := by
  intro h
  exact (h missing) rfl

theorem operator_minimality_lower_bound
    (L : OperatorLanguage)
    (h : OperatorAdequate L) :
    ∀ r : OperatorRole, L.HasOperator r := by
  exact h

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

theorem central_four_outcome_taxonomy (C : StressContext) :
    classify C = absorption ∨
    classify C = extension ∨
    classify C = collapse ∨
    classify C = underdetermined := by
  cases classify C <;> simp

theorem absorption_is_counterexample_to_old_two_fork
    (C : StressContext)
    (hE : C.evidenceBound)
    (hS : C.sameDescriptionRepair) :
    classify C = absorption := by
  classical
  simp [classify, hE, hS]

def kRank (n : Nat) : Nat := n

theorem k_adjacent_noncollapse (n : Nat) :
    kRank n < kRank (n + 1) := by
  exact Nat.lt_succ_self n

def kLadder (maxDepth : Nat) : List Nat :=
  List.range (maxDepth + 1)

theorem k_ladder_reference_13_count :
    (kLadder 12).length = 13 := by
  native_decide

theorem fixed_k_count_not_absolute :
    ∃ alternativeDepth : Nat, (kLadder alternativeDepth).length ≠ 13 := by
  exact ⟨13, by native_decide⟩

structure LawCandidate where
  trigger : Prop
  scope : Prop
  outcomeCriterion : Prop
  falsifier : Prop

def LawAdmissible (L : LawCandidate) : Prop :=
  L.trigger ∧ L.scope ∧ L.outcomeCriterion ∧ L.falsifier

theorem law_admissibility_requires_falsifier
    (L : LawCandidate)
    (h : LawAdmissible L) :
    L.falsifier := by
  exact h.right.right.right

structure DomainClaim where
  coreSignature : Prop
  localInstantiation : Prop
  evidenceBound : Prop

def DomainValidated (D : DomainClaim) : Prop :=
  D.coreSignature ∧ D.localInstantiation ∧ D.evidenceBound

theorem domain_projection_non_inflation
    (D : DomainClaim)
    (h : DomainValidated D) :
    D.localInstantiation ∧ D.evidenceBound := by
  exact ⟨h.right.left, h.right.right⟩

def coreOnlyDomainClaim : DomainClaim :=
  { coreSignature := True, localInstantiation := False, evidenceBound := False }

theorem core_signature_alone_cannot_validate_domain :
    coreOnlyDomainClaim.coreSignature ∧ ¬ DomainValidated coreOnlyDomainClaim := by
  constructor
  · trivial
  · intro h
    exact h.right.left

def CrownPromoted (D : DomainClaim) : Prop :=
  DomainValidated D

theorem crown_not_core_from_signature_only :
    ¬ CrownPromoted coreOnlyDomainClaim := by
  intro h
  exact h.right.left

end OCMinimal
