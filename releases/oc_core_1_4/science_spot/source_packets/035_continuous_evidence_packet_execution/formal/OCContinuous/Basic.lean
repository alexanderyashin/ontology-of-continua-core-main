namespace OCContinuous

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

structure ChapterProjection where
  packetComplete : Prop
  empiricalClaim : Prop
  chapterLevelEmpiricalEvidence : Prop
  sourceDeniesEmpiricalPromotion : Prop

def FormalNonEmpiricalProjection (C : ChapterProjection) : Prop :=
  C.packetComplete ∧ ¬ C.empiricalClaim ∧ C.sourceDeniesEmpiricalPromotion

def EmpiricalProjection (C : ChapterProjection) : Prop :=
  C.packetComplete ∧ C.empiricalClaim ∧ C.chapterLevelEmpiricalEvidence

theorem formal_projection_blocks_empirical_wording
    (C : ChapterProjection)
    (h : FormalNonEmpiricalProjection C) :
    ¬ C.empiricalClaim := by
  exact h.right.left

theorem empirical_projection_requires_local_evidence
    (C : ChapterProjection)
    (h : EmpiricalProjection C) :
    C.chapterLevelEmpiricalEvidence := by
  exact h.right.right

structure CrownStoneCandidate where
  namedStatement : Prop
  theoremChain : Prop
  noRefutedDependency : Prop
  falsifier : Prop
  evidenceIfEmpirical : Prop

def CrownStoneProved (C : CrownStoneCandidate) : Prop :=
  C.namedStatement ∧ C.theoremChain ∧ C.noRefutedDependency ∧
  C.falsifier ∧ C.evidenceIfEmpirical

theorem crown_stone_requires_theorem_chain
    (C : CrownStoneCandidate)
    (h : CrownStoneProved C) :
    C.theoremChain := by
  exact h.right.left

structure ContinuousCloseoutState where
  packetOpenRows : Nat
  empiricalUpgradeOpenRows : Nat
  promotedRowsSound : Prop

def FullEmpiricalCloseoutAllowed (S : ContinuousCloseoutState) : Prop :=
  S.packetOpenRows = 0 ∧ S.empiricalUpgradeOpenRows = 0 ∧ S.promotedRowsSound

theorem closeout_requires_zero_empirical_upgrades
    (S : ContinuousCloseoutState)
    (h : FullEmpiricalCloseoutAllowed S) :
    S.empiricalUpgradeOpenRows = 0 := by
  exact h.right.left

end OCContinuous
