namespace OCSequential

structure EvidencePacket where
  exactStatement : Prop
  proposition : Prop
  observables : Prop
  constraints : Prop
  operatorMap : Prop
  invariants : Prop
  falsifier : Prop
  replayOrReplicationSurface : Prop
  evidenceRefs : Prop
  dependencyClosure : Prop
  verification : Prop

def PacketComplete (P : EvidencePacket) : Prop :=
  P.exactStatement ∧ P.proposition ∧ P.observables ∧ P.constraints ∧
  P.operatorMap ∧ P.invariants ∧ P.falsifier ∧
  P.replayOrReplicationSurface ∧ P.evidenceRefs ∧
  P.dependencyClosure ∧ P.verification

theorem packet_requires_falsifier
    (P : EvidencePacket)
    (h : PacketComplete P) :
    P.falsifier := by
  exact h.right.right.right.right.right.right.left

theorem packet_requires_dependency_closure
    (P : EvidencePacket)
    (h : PacketComplete P) :
    P.dependencyClosure := by
  exact h.right.right.right.right.right.right.right.right.right.left

structure ProjectionStatus where
  packetComplete : Prop
  empiricalClaim : Prop
  chapterLevelEmpiricalEvidence : Prop

def NonEmpiricalProjectionClosed (S : ProjectionStatus) : Prop :=
  S.packetComplete ∧ ¬ S.empiricalClaim

def EmpiricalProjectionClosed (S : ProjectionStatus) : Prop :=
  S.packetComplete ∧ S.empiricalClaim ∧ S.chapterLevelEmpiricalEvidence

theorem empirical_projection_requires_chapter_evidence
    (S : ProjectionStatus)
    (h : EmpiricalProjectionClosed S) :
    S.chapterLevelEmpiricalEvidence := by
  exact h.right.right

theorem non_empirical_projection_blocks_empirical_wording
    (S : ProjectionStatus)
    (h : NonEmpiricalProjectionClosed S) :
    ¬ S.empiricalClaim := by
  exact h.right

structure CloseoutState where
  remainingOpenRows : Nat
  promotedRowsSound : Prop

def FullCloseoutAllowed (S : CloseoutState) : Prop :=
  S.remainingOpenRows = 0 ∧ S.promotedRowsSound

theorem closeout_requires_zero_remaining
    (S : CloseoutState)
    (h : FullCloseoutAllowed S) :
    S.remainingOpenRows = 0 := by
  exact h.left

end OCSequential
