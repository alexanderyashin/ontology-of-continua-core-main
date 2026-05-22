namespace OCGoalRequirements

inductive RequirementStatus where
  | satisfied
  | failedNeedsRepair
  | blockedByExternalEvidence
  | notRequired
deriving DecidableEq, Repr

structure RequirementGate where
  exactCriterion : Bool
  sourceBound : Bool
  artifactBound : Bool
  verificationBound : Bool
  wordingBound : Bool
deriving DecidableEq, Repr

def requirementSatisfied (g : RequirementGate) : Bool :=
  g.exactCriterion && g.sourceBound && g.artifactBound && g.verificationBound && g.wordingBound

def statusAllowsPass : RequirementStatus -> Bool
  | RequirementStatus.satisfied => true
  | RequirementStatus.notRequired => true
  | RequirementStatus.failedNeedsRepair => false
  | RequirementStatus.blockedByExternalEvidence => false

def lanePasses (allRequiredSatisfied noRequiredBlocked : Bool) : Bool :=
  allRequiredSatisfied && noRequiredBlocked

def journalSendable (scientific publication reputation : Bool) : Bool :=
  scientific && publication && reputation

def monographReady (scientific monograph reputation : Bool) : Bool :=
  scientific && monograph && reputation

def toolkitReady (instrumental toolkit productQa : Bool) : Bool :=
  instrumental && toolkit && productQa

def eaSecondOpinionReady (questionAtlas dataIntake report replay falsifier clientBoundary : Bool) : Bool :=
  questionAtlas && dataIntake && report && replay && falsifier && clientBoundary

def commerciallyClaimable (business governance externalEvidence counselClient : Bool) : Bool :=
  business && governance && externalEvidence && counselClient

theorem satisfied_has_artifact (g : RequirementGate) (h : requirementSatisfied g = true) :
    g.artifactBound = true := by
  unfold requirementSatisfied at h
  cases g.exactCriterion <;> cases g.sourceBound <;> cases g.artifactBound <;>
    cases g.verificationBound <;> cases g.wordingBound <;> simp at h

theorem journal_needs_publication (s p r : Bool) (h : journalSendable s p r = true) :
    p = true := by
  unfold journalSendable at h
  cases s <;> cases p <;> cases r <;> simp at h

theorem toolkit_needs_toolkit_lane (i t p : Bool) (h : toolkitReady i t p = true) :
    t = true := by
  unfold toolkitReady at h
  cases i <;> cases t <;> cases p <;> simp at h

theorem ea_second_opinion_needs_question_atlas
    (q d r f c : Bool) (h : eaSecondOpinionReady q d r true f c = true) :
    q = true := by
  unfold eaSecondOpinionReady at h
  cases q <;> cases d <;> cases r <;> cases f <;> cases c <;> simp at h

theorem commercial_needs_external_evidence
    (b g e c : Bool) (h : commerciallyClaimable b g e c = true) :
    e = true := by
  unfold commerciallyClaimable at h
  cases b <;> cases g <;> cases e <;> cases c <;> simp at h

end OCGoalRequirements
