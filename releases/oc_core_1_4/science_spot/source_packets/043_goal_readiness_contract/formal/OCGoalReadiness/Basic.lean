namespace OCGoalReadiness

structure LaneGate where
  artifacts : Bool
  verification : Bool
  allowedWording : Bool
  forbiddenWording : Bool
deriving DecidableEq, Repr

def lanePasses (g : LaneGate) : Bool :=
  g.artifacts && g.verification && g.allowedWording && g.forbiddenWording

theorem passed_has_artifacts (g : LaneGate) (h : lanePasses g = true) :
    g.artifacts = true := by
  unfold lanePasses at h
  cases g.artifacts <;> simp at h

theorem passed_has_verification (g : LaneGate) (h : lanePasses g = true) :
    g.verification = true := by
  unfold lanePasses at h
  cases g.artifacts <;> cases g.verification <;> simp at h

def journalSendable (scientific publication reputation : Bool) : Bool :=
  scientific && publication && reputation

def practicallyUsable (instrumental product : Bool) : Bool :=
  instrumental && product

def commerciallyClaimable (business governance : Bool) : Bool :=
  business && governance

theorem journal_needs_publication (s p r : Bool) (h : journalSendable s p r = true) :
    p = true := by
  unfold journalSendable at h
  cases s <;> cases p <;> simp at h

theorem practical_needs_product (i p : Bool) (h : practicallyUsable i p = true) :
    p = true := by
  unfold practicallyUsable at h
  cases i <;> cases p <;> simp at h

theorem commercial_needs_business (b g : Bool) (h : commerciallyClaimable b g = true) :
    b = true := by
  unfold commerciallyClaimable at h
  cases b <;> cases g <;> simp at h

end OCGoalReadiness
