namespace OCFullEmpirical

structure EmpiricalEvidence where
  observables : Prop
  constraints : Prop
  operators : Prop
  invariants : Prop
  falsifier : Prop
  evidenceRefs : Prop
  replayOrReplication : Prop
  claimCeiling : Prop
  noBlockers : Prop

def EmpiricallyProved (E : EmpiricalEvidence) : Prop :=
  E.observables ∧ E.constraints ∧ E.operators ∧ E.invariants ∧
  E.falsifier ∧ E.evidenceRefs ∧ E.replayOrReplication ∧
  E.claimCeiling ∧ E.noBlockers

theorem empirical_proof_requires_replay
    (E : EmpiricalEvidence)
    (h : EmpiricallyProved E) :
    E.replayOrReplication := by
  exact h.right.right.right.right.right.right.left

theorem empirical_proof_requires_claim_ceiling
    (E : EmpiricalEvidence)
    (h : EmpiricallyProved E) :
    E.claimCeiling := by
  exact h.right.right.right.right.right.right.right.left

structure CrownStoneChain where
  exactStatement : Prop
  coreDependencyChain : Prop
  noRefutedDependency : Prop
  theoremOrCounterproof : Prop
  falsifier : Prop
  localEvidenceIfEmpirical : Prop

def CrownStoneProved (C : CrownStoneChain) : Prop :=
  C.exactStatement ∧ C.coreDependencyChain ∧ C.noRefutedDependency ∧
  C.theoremOrCounterproof ∧ C.falsifier ∧ C.localEvidenceIfEmpirical

theorem crown_stone_requires_dependency_chain
    (C : CrownStoneChain)
    (h : CrownStoneProved C) :
    C.coreDependencyChain := by
  exact h.right.left

theorem crown_stone_requires_no_refuted_dependency
    (C : CrownStoneChain)
    (h : CrownStoneProved C) :
    C.noRefutedDependency := by
  exact h.right.right.left

structure CloseoutState where
  hasOpenLocalDataRows : Prop
  promotedRowsSound : Prop

def FullEmpiricalCloseoutAllowed (S : CloseoutState) : Prop :=
  ¬ S.hasOpenLocalDataRows ∧ S.promotedRowsSound

theorem closeout_requires_no_open_local_data
    (S : CloseoutState)
    (h : FullEmpiricalCloseoutAllowed S) :
    ¬ S.hasOpenLocalDataRows := by
  exact h.left

structure ArticleClaim where
  saysFullEmpiricalTheory : Prop
  fullCloseoutAllowed : Prop

def ArticleFullEmpiricalSafe (A : ArticleClaim) : Prop :=
  A.saysFullEmpiricalTheory → A.fullCloseoutAllowed

theorem full_empirical_wording_requires_closeout
    (A : ArticleClaim)
    (h : ArticleFullEmpiricalSafe A)
    (hsay : A.saysFullEmpiricalTheory) :
    A.fullCloseoutAllowed := by
  exact h hsay

end OCFullEmpirical
