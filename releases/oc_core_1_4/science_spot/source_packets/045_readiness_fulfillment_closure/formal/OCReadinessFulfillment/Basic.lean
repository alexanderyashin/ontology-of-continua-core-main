namespace OCReadinessFulfillment

inductive GateStatus where
  | satisfied
  | repaired
  | blockedExternal
  | notRequired
deriving DecidableEq, Repr

structure ReleaseGate where
  artifactBound : Bool
  verificationBound : Bool
  wordingBound : Bool
  externalEvidence : Bool
deriving DecidableEq, Repr

def internalPacketComplete (g : ReleaseGate) : Bool :=
  g.artifactBound && g.verificationBound && g.wordingBound

def externalReleaseAllowed (g : ReleaseGate) : Bool :=
  internalPacketComplete g && g.externalEvidence

def publicPayloadAllowed (scienceBound noPrivate noHeavy noOverclaim : Bool) : Bool :=
  scienceBound && noPrivate && noHeavy && noOverclaim

theorem external_release_needs_external_evidence
    (g : ReleaseGate) (h : externalReleaseAllowed g = true) :
    g.externalEvidence = true := by
  unfold externalReleaseAllowed at h
  unfold internalPacketComplete at h
  cases g.artifactBound <;> cases g.verificationBound <;> cases g.wordingBound <;>
    cases g.externalEvidence <;> simp at h

theorem internal_packet_needs_artifact
    (g : ReleaseGate) (h : internalPacketComplete g = true) :
    g.artifactBound = true := by
  unfold internalPacketComplete at h
  cases g.artifactBound <;> cases g.verificationBound <;> cases g.wordingBound <;>
    cases g.externalEvidence <;> simp at h

theorem public_payload_needs_no_private
    (s p h o : Bool) (hp : publicPayloadAllowed s p h o = true) :
    p = true := by
  unfold publicPayloadAllowed at hp
  cases s <;> cases p <;> cases h <;> cases o <;> simp at hp

end OCReadinessFulfillment
