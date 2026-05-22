namespace OCCognition

structure CognitionSubclaim where
  exactStatement : Prop
  formalProposition : Prop
  localDataset : Prop
  replayScript : Prop
  acceptanceThresholds : Prop
  falsifier : Prop
  dependencyClosure : Prop
  verification : Prop

def EmpiricalCognitionSubclaimClosed (S : CognitionSubclaim) : Prop :=
  S.exactStatement ∧ S.formalProposition ∧ S.localDataset ∧
  S.replayScript ∧ S.acceptanceThresholds ∧ S.falsifier ∧
  S.dependencyClosure ∧ S.verification

theorem empirical_cognition_requires_local_dataset
    (S : CognitionSubclaim)
    (h : EmpiricalCognitionSubclaimClosed S) :
    S.localDataset := by
  exact h.right.right.left

theorem empirical_cognition_requires_replay_script
    (S : CognitionSubclaim)
    (h : EmpiricalCognitionSubclaimClosed S) :
    S.replayScript := by
  exact h.right.right.right.left

structure K3Upgrade where
  allSubclaimsTerminal : Prop
  ambiguousSentenceOpen : Nat
  roadsidePerceptionOpen : Nat
  promotedRowsSound : Prop

def FullK3EmpiricalUpgrade (U : K3Upgrade) : Prop :=
  U.allSubclaimsTerminal ∧ U.ambiguousSentenceOpen = 0 ∧
  U.roadsidePerceptionOpen = 0 ∧ U.promotedRowsSound

theorem full_k3_upgrade_requires_no_ambiguity_gap
    (U : K3Upgrade)
    (h : FullK3EmpiricalUpgrade U) :
    U.ambiguousSentenceOpen = 0 := by
  exact h.right.left

theorem full_k3_upgrade_requires_no_roadside_gap
    (U : K3Upgrade)
    (h : FullK3EmpiricalUpgrade U) :
    U.roadsidePerceptionOpen = 0 := by
  exact h.right.right.left

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

end OCCognition
