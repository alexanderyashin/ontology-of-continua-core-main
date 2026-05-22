namespace OCWorldReadiness

inductive BlockerStatus where
  | closedInternal
  | closedSelfAuditLimited
  | blockedOwnerDecision
  | blockedTrueExternal
deriving DecidableEq, Repr

structure WorldGate where
  internalArtifacts : Bool
  selfAudit : Bool
  ownerDecision : Bool
  trueExternalEvidence : Bool
deriving DecidableEq, Repr

def internalWorldReady (g : WorldGate) : Bool :=
  g.internalArtifacts && g.selfAudit

def externalWorldReady (g : WorldGate) : Bool :=
  internalWorldReady g && g.ownerDecision && g.trueExternalEvidence

def publicScienceAllowed (bounded noPrivate noHeavy noLegalClientROI : Bool) : Bool :=
  bounded && noPrivate && noHeavy && noLegalClientROI

theorem external_ready_requires_owner
    (g : WorldGate) (h : externalWorldReady g = true) :
    g.ownerDecision = true := by
  cases g with
  | mk internalArtifacts selfAudit ownerDecision trueExternalEvidence =>
      simp [externalWorldReady, internalWorldReady] at h
      exact h.1.2

theorem external_ready_requires_external_evidence
    (g : WorldGate) (h : externalWorldReady g = true) :
    g.trueExternalEvidence = true := by
  cases g with
  | mk internalArtifacts selfAudit ownerDecision trueExternalEvidence =>
      simp [externalWorldReady, internalWorldReady] at h
      exact h.2

theorem public_science_needs_no_private
    (b p h l : Bool) (hp : publicScienceAllowed b p h l = true) :
    p = true := by
  cases b <;> cases p <;> cases h <;> cases l <;> simp [publicScienceAllowed] at hp ⊢

theorem public_science_needs_no_legal_client_roi
    (b p h l : Bool) (hp : publicScienceAllowed b p h l = true) :
    l = true := by
  cases b <;> cases p <;> cases h <;> cases l <;> simp [publicScienceAllowed] at hp ⊢

end OCWorldReadiness
