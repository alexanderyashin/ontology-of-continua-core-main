namespace OCBiology

structure BiologySubclaim where
  exactStatement : Prop
  formalProposition : Prop
  benchmarkEvidence : Prop
  falsifier : Prop
  dependencyClosure : Prop
  verification : Prop

def EmpiricalBiologySubclaimClosed (S : BiologySubclaim) : Prop :=
  S.exactStatement ∧ S.formalProposition ∧ S.benchmarkEvidence ∧
  S.falsifier ∧ S.dependencyClosure ∧ S.verification

theorem empirical_biology_subclaim_requires_benchmark_evidence
    (S : BiologySubclaim)
    (h : EmpiricalBiologySubclaimClosed S) :
    S.benchmarkEvidence := by
  exact h.right.right.left

structure K2Upgrade where
  allSubclaimsTerminal : Prop
  woundBiofilmHomeostasisOpen : Nat
  promotedRowsSound : Prop

def FullK2EmpiricalUpgrade (U : K2Upgrade) : Prop :=
  U.allSubclaimsTerminal ∧ U.woundBiofilmHomeostasisOpen = 0 ∧
  U.promotedRowsSound

theorem full_k2_upgrade_requires_no_comparative_gap
    (U : K2Upgrade)
    (h : FullK2EmpiricalUpgrade U) :
    U.woundBiofilmHomeostasisOpen = 0 := by
  exact h.right.left

structure ProgramQueue where
  remainingInputObligations : Nat
  openFollowupRequirements : Nat
  fullEmpiricalCloseoutAllowed : Prop

def LawfulProgramCloseout (Q : ProgramQueue) : Prop :=
  Q.remainingInputObligations = 0 ∧ Q.openFollowupRequirements = 0 ∧
  Q.fullEmpiricalCloseoutAllowed

theorem program_closeout_requires_no_open_followups
    (Q : ProgramQueue)
    (h : LawfulProgramCloseout Q) :
    Q.openFollowupRequirements = 0 := by
  exact h.right.left

end OCBiology
