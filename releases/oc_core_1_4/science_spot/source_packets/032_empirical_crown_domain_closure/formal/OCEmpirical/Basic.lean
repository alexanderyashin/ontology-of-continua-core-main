namespace OCEmpirical

structure LocalEvidence where
  observables : Prop
  constraints : Prop
  operators : Prop
  invariants : Prop
  falsifiers : Prop
  evidenceBindings : Prop
  replayOrReplication : Prop
  claimCeiling : Prop
  noBlockers : Prop

def LocalEvidenceComplete (E : LocalEvidence) : Prop :=
  E.observables ∧ E.constraints ∧ E.operators ∧ E.invariants ∧
  E.falsifiers ∧ E.evidenceBindings ∧ E.replayOrReplication ∧
  E.claimCeiling ∧ E.noBlockers

theorem empirical_domain_requires_falsifier
    (E : LocalEvidence)
    (h : LocalEvidenceComplete E) :
    E.falsifiers := by
  exact h.right.right.right.right.left

theorem empirical_domain_requires_claim_ceiling
    (E : LocalEvidence)
    (h : LocalEvidenceComplete E) :
    E.claimCeiling := by
  exact h.right.right.right.right.right.right.right.left

theorem empirical_domain_requires_no_blockers
    (E : LocalEvidence)
    (h : LocalEvidenceComplete E) :
    E.noBlockers := by
  exact h.right.right.right.right.right.right.right.right

structure CrownChain where
  sourceBinding : Prop
  coreTheoremChain : Prop
  localEvidenceOrExplicitCondition : Prop
  noRefutedDependency : Prop
  falsifier : Prop
  dependencyClosure : Prop

def ConditionalCrownCorollary (C : CrownChain) : Prop :=
  C.sourceBinding ∧ C.coreTheoremChain ∧
  C.localEvidenceOrExplicitCondition ∧ C.noRefutedDependency ∧
  C.falsifier ∧ C.dependencyClosure

theorem crown_corollary_requires_dependency_closure
    (C : CrownChain)
    (h : ConditionalCrownCorollary C) :
    C.dependencyClosure := by
  exact h.right.right.right.right.right

theorem crown_corollary_requires_no_refuted_dependency
    (C : CrownChain)
    (h : ConditionalCrownCorollary C) :
    C.noRefutedDependency := by
  exact h.right.right.right.left

structure CoreOnlyCrownClaim where
  coreVocabulary : Prop
  localEvidence : Prop

def CrownPromotable (C : CoreOnlyCrownClaim) : Prop :=
  C.coreVocabulary ∧ C.localEvidence

theorem core_vocabulary_alone_not_crown_promotion
    (C : CoreOnlyCrownClaim)
    (_hcore : C.coreVocabulary)
    (hmissing : ¬ C.localEvidence) :
    ¬ CrownPromotable C := by
  intro hp
  exact hmissing hp.right

structure ArticleClaim where
  positiveEmpiricalWording : Prop
  empiricalEvidence : Prop
  withinCeiling : Prop
  noForbiddenCrownOverclaim : Prop

def ArticleSafe (A : ArticleClaim) : Prop :=
  (A.positiveEmpiricalWording → A.empiricalEvidence) ∧
  A.withinCeiling ∧ A.noForbiddenCrownOverclaim

theorem positive_empirical_wording_requires_evidence
    (A : ArticleClaim)
    (h : ArticleSafe A)
    (hp : A.positiveEmpiricalWording) :
    A.empiricalEvidence := by
  exact h.left hp

end OCEmpirical
