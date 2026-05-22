namespace OCOperational

structure EvidenceBinding where
  formalProof : Prop
  executableWitness : Prop
  sourceBinding : Prop
  falsifier : Prop
  dependencyClosure : Prop

def ProvedWithEvidence (E : EvidenceBinding) : Prop :=
  E.formalProof ∧ E.executableWitness ∧ E.sourceBinding ∧
  E.falsifier ∧ E.dependencyClosure

theorem proved_with_evidence_requires_formal_proof
    (E : EvidenceBinding)
    (h : ProvedWithEvidence E) :
    E.formalProof := by
  exact h.left

theorem proved_with_evidence_requires_executable_witness
    (E : EvidenceBinding)
    (h : ProvedWithEvidence E) :
    E.executableWitness := by
  exact h.right.left

theorem proved_with_evidence_requires_source_binding
    (E : EvidenceBinding)
    (h : ProvedWithEvidence E) :
    E.sourceBinding := by
  exact h.right.right.left

theorem proved_with_evidence_requires_falsifier
    (E : EvidenceBinding)
    (h : ProvedWithEvidence E) :
    E.falsifier := by
  exact h.right.right.right.left

theorem proved_with_evidence_requires_dependency_closure
    (E : EvidenceBinding)
    (h : ProvedWithEvidence E) :
    E.dependencyClosure := by
  exact h.right.right.right.right

structure DomainEvidence where
  replayPass : Prop
  validationPass : Prop
  completionPass : Prop
  noBlockers : Prop
  hasAcceptanceCriterion : Prop
  hasFalsifier : Prop
  hasEvidenceRefs : Prop
  hasClaimCeiling : Prop

def DomainProvedWithEvidence (D : DomainEvidence) : Prop :=
  D.replayPass ∧ D.validationPass ∧ D.completionPass ∧ D.noBlockers ∧
  D.hasAcceptanceCriterion ∧ D.hasFalsifier ∧ D.hasEvidenceRefs ∧
  D.hasClaimCeiling

theorem domain_evidence_requires_claim_ceiling
    (D : DomainEvidence)
    (h : DomainProvedWithEvidence D) :
    D.hasClaimCeiling := by
  exact h.right.right.right.right.right.right.right

theorem domain_evidence_requires_no_blockers
    (D : DomainEvidence)
    (h : DomainProvedWithEvidence D) :
    D.noBlockers := by
  exact h.right.right.right.left

structure ArticlePromotion where
  provedWithEvidence : Prop
  withinClaimCeiling : Prop
  noGuardOverclaim : Prop

def ArticlePromotable (A : ArticlePromotion) : Prop :=
  A.provedWithEvidence ∧ A.withinClaimCeiling ∧ A.noGuardOverclaim

theorem article_promotion_requires_claim_ceiling
    (A : ArticlePromotion)
    (h : ArticlePromotable A) :
    A.withinClaimCeiling := by
  exact h.right.left

theorem article_promotion_requires_no_guard_overclaim
    (A : ArticlePromotion)
    (h : ArticlePromotable A) :
    A.noGuardOverclaim := by
  exact h.right.right

end OCOperational
