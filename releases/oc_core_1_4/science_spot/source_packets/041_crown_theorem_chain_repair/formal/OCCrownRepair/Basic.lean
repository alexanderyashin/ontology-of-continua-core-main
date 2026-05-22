namespace OCCrownRepair

structure TheoremGate where
  sourceBound : Bool
  proofBound : Bool
  falsifierBound : Bool
  dependencyClosed : Bool
deriving DecidableEq, Repr

def promotable (g : TheoremGate) : Bool :=
  g.sourceBound && g.proofBound && g.falsifierBound && g.dependencyClosed

theorem promotable_has_source (g : TheoremGate) (h : promotable g = true) : g.sourceBound = true := by
  unfold promotable at h
  cases g.sourceBound <;> simp at h

theorem promotable_has_proof (g : TheoremGate) (h : promotable g = true) : g.proofBound = true := by
  unfold promotable at h
  cases g.sourceBound <;> cases g.proofBound <;> simp at h

theorem promotable_has_falsifier (g : TheoremGate) (h : promotable g = true) : g.falsifierBound = true := by
  unfold promotable at h
  cases g.sourceBound <;> cases g.proofBound <;> cases g.falsifierBound <;> simp at h

theorem promotable_has_dependencies (g : TheoremGate) (h : promotable g = true) : g.dependencyClosed = true := by
  unfold promotable at h
  cases g.sourceBound <;> cases g.proofBound <;> cases g.falsifierBound <;> cases g.dependencyClosed <;> simp at h

inductive ResponseClass where
  | absorption
  | extension
  | collapse
  | underdetermined
deriving DecidableEq, Repr

structure ContinuumEvent where
  aliveAfter : Bool
  releasedConstraint : Bool
deriving DecidableEq, Repr

def ddRepaired (e : ContinuumEvent) : Bool :=
  (!e.aliveAfter) && e.releasedConstraint

theorem dd_not_postmortem_object (e : ContinuumEvent) (h : ddRepaired e = true) : e.aliveAfter = false := by
  unfold ddRepaired at h
  cases e.aliveAfter <;> simp at h

structure CapacityRegime where
  capacity : Nat
  tension : Nat
deriving DecidableEq, Repr

def carmaGap (r : CapacityRegime) : Prop :=
  r.capacity < r.tension

theorem carma_gap_is_capacity_insufficiency (r : CapacityRegime) :
    carmaGap r -> r.capacity < r.tension := by
  intro h
  exact h

structure RateRegime where
  interactionRate : Nat
  closureRate : Nat
deriving DecidableEq, Repr

def sirPressure (r : RateRegime) : Prop :=
  r.closureRate < r.interactionRate

theorem sir_pressure_requires_rate_excess (r : RateRegime) :
    sirPressure r -> r.closureRate < r.interactionRate := by
  intro h
  exact h

structure IdentityRegime where
  acceleration : Nat
  ruptureThreshold : Nat
deriving DecidableEq, Repr

def smdRuptureRisk (r : IdentityRegime) : Prop :=
  r.ruptureThreshold < r.acceleration

theorem smd_rupture_is_thresholded (r : IdentityRegime) :
    smdRuptureRisk r -> r.ruptureThreshold < r.acceleration := by
  intro h
  exact h

inductive LifeRegime where
  | birth
  | persistence
  | transformation
  | degeneration
  | death
deriving DecidableEq, Repr

theorem life_regime_total (r : LifeRegime) :
    r = LifeRegime.birth ∨ r = LifeRegime.persistence ∨ r = LifeRegime.transformation ∨
    r = LifeRegime.degeneration ∨ r = LifeRegime.death := by
  cases r <;> simp

structure AdaptiveFrictionRegime where
  friction : Nat
  minimumFriction : Nat
deriving DecidableEq, Repr

def brrLowFriction (r : AdaptiveFrictionRegime) : Prop :=
  r.friction < r.minimumFriction

theorem brr_regression_trigger_is_low_friction (r : AdaptiveFrictionRegime) :
    brrLowFriction r -> r.friction < r.minimumFriction := by
  intro h
  exact h

theorem ucm_response_taxonomy_total : ∀ r : ResponseClass, r = ResponseClass.absorption ∨
    r = ResponseClass.extension ∨ r = ResponseClass.collapse ∨ r = ResponseClass.underdetermined := by
  intro r
  cases r <;> simp

end OCCrownRepair
