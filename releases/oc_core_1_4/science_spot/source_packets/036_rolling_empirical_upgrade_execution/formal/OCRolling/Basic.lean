namespace OCRolling

structure Subclaim where
  exactStatement : Prop
  formalProposition : Prop
  evidenceMatch : Prop
  falsifier : Prop
  dependencyClosure : Prop
  verification : Prop

def EmpiricalSubclaimClosed (S : Subclaim) : Prop :=
  S.exactStatement ∧ S.formalProposition ∧ S.evidenceMatch ∧
  S.falsifier ∧ S.dependencyClosure ∧ S.verification

theorem empirical_subclaim_requires_evidence_match
    (S : Subclaim)
    (h : EmpiricalSubclaimClosed S) :
    S.evidenceMatch := by
  exact h.right.right.left

structure ChapterUpgrade where
  allSubclaimsTerminal : Prop
  openLocalDataRequirements : Nat
  promotedRowsSound : Prop

def FullChapterEmpiricalUpgrade (U : ChapterUpgrade) : Prop :=
  U.allSubclaimsTerminal ∧ U.openLocalDataRequirements = 0 ∧ U.promotedRowsSound

theorem full_upgrade_requires_zero_local_data
    (U : ChapterUpgrade)
    (h : FullChapterEmpiricalUpgrade U) :
    U.openLocalDataRequirements = 0 := by
  exact h.right.left

structure QueueState where
  remainingInputObligations : Nat
  openFollowupRequirements : Nat
  fullEmpiricalCloseoutAllowed : Prop

def LawfulCloseout (Q : QueueState) : Prop :=
  Q.remainingInputObligations = 0 ∧ Q.openFollowupRequirements = 0 ∧
  Q.fullEmpiricalCloseoutAllowed

theorem lawful_closeout_requires_no_followups
    (Q : QueueState)
    (h : LawfulCloseout Q) :
    Q.openFollowupRequirements = 0 := by
  exact h.right.left

end OCRolling
