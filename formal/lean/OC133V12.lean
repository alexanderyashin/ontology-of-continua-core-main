namespace OC133V12

inductive Status where
  | pass
  | fail
deriving DecidableEq, Repr

inductive CycleMode where
  | maintenance
  | renewal
  | replay
  | regulatory
  | degenerate
deriving DecidableEq, Repr

inductive MorphismClass where
  | identity
  | residue
  | rebirth
deriving DecidableEq, Repr

inductive Component where
  | carrier
  | realization
  | lawfulPossibility
  | liveness
  | residue
  | morphisms
  | boundaries
  | operators
  | cycles
  | dimension
  | kFunctional
deriving DecidableEq, Repr

inductive AdjacentK where
  | k0_k1
  | k1_k2
  | k2_k3
  | k3_k4
  | k4_k5
  | k5_k6
  | k6_k7
  | k7_k8
  | k8_k9
  | k9_k10
  | k10_k11
  | k11_k12
deriving DecidableEq, Repr

structure Resolution (S : Type) where
  cell : S -> Nat

def sameCell {S : Type} (rho : Resolution S) (a b : S) : Prop :=
  rho.cell a = rho.cell b

def distinguished {S : Type} (rho : Resolution S) (a b : S) : Prop :=
  rho.cell a != rho.cell b

theorem k0_same_cell_not_distinguished {S : Type} (rho : Resolution S) (a b : S) :
    sameCell rho a b -> distinguished rho a b = False := by
  intro h
  unfold distinguished
  rw [h]
  simp

theorem k0_distinguished_requires_resolved_delta {S : Type} (rho : Resolution S) (a b : S) :
    distinguished rho a b -> sameCell rho a b -> False := by
  intro hd hs
  rw [k0_same_cell_not_distinguished rho a b hs] at hd
  exact hd

structure Realization where
  Carrier : Type
  admissible : Carrier -> Bool
  live : Carrier -> Bool
  cycle : Carrier -> Option CycleMode

structure Lifecycle (S Residue NewLive : Type) where
  admissible : S -> Bool
  live : S -> Bool
  death : S -> Bool
  residueOf : S -> Option Residue
  rebirthOf : Residue -> Option NewLive
  identityInvariant : S -> NewLive -> Bool

def cycleWitnessed (R : Realization) (x : R.Carrier) : Prop :=
  R.cycle x != none

def eligibleLive (R : Realization) (x : R.Carrier) : Prop :=
  R.admissible x = true /\ R.live x = true /\ cycleWitnessed R x

theorem eligible_live_requires_cycle (R : Realization) (x : R.Carrier) :
    eligibleLive R x -> cycleWitnessed R x := by
  intro h
  exact h.right.right

theorem eligible_live_requires_admissible (R : Realization) (x : R.Carrier) :
    eligibleLive R x -> R.admissible x = true := by
  intro h
  exact h.left

theorem cycle_mode_required_for_eligible_live (R : Realization) (x : R.Carrier) :
    eligibleLive R x -> R.cycle x != none := by
  intro h
  exact h.right.right

structure ZeroCause where
  flow : Bool
  coherence : Bool
  identity : Bool
  embedding : Bool

def hasZeroCause (z : ZeroCause) : Prop :=
  z.flow = true \/ z.coherence = true \/ z.identity = true \/ z.embedding = true

def kZeroLicensed (z : ZeroCause) : Prop :=
  hasZeroCause z

theorem zero_cause_has_cause (z : ZeroCause) :
    z.flow = true -> hasZeroCause z := by
  intro h
  exact Or.inl h

theorem k_zero_iff_declared_zero_cause (z : ZeroCause) :
    kZeroLicensed z <-> hasZeroCause z := by
  exact Iff.rfl

structure BoundaryClassifier (S StatusType : Type) where
  classify : S -> StatusType
  fails : StatusType -> Bool

def boundaryFails {S StatusType : Type} (b : BoundaryClassifier S StatusType) (x : S) : Bool :=
  b.fails (b.classify x)

structure MetricBoundary (S : Type) where
  measure : S -> Nat
  threshold : Nat

def metricAsClassifier {S : Type} (m : MetricBoundary S) : BoundaryClassifier S Nat :=
  { classify := m.measure, fails := fun n => decide (n > m.threshold) }

theorem metric_boundary_is_classifier {S : Type} (m : MetricBoundary S) :
    (metricAsClassifier m).classify = m.measure := by
  rfl

theorem metric_boundary_failure_equiv {S : Type} (m : MetricBoundary S) (x : S) :
    boundaryFails (metricAsClassifier m) x = decide (m.measure x > m.threshold) := by
  rfl

structure UpdateSystem where
  State : Type
  step : State -> State
  admissible : State -> Bool

structure SmoothSystem extends UpdateSystem where
  charted : Bool
  flow : Nat -> State -> State
  flow_zero : forall x : State, flow 0 x = x

def smoothAsUpdate (s : SmoothSystem) : UpdateSystem :=
  { State := s.State, step := s.step, admissible := s.admissible }

theorem smooth_operator_is_update_special_case (s : SmoothSystem) :
    (smoothAsUpdate s).step = s.step := by
  rfl

structure HybridSystem extends UpdateSystem where
  Mode : Type
  mode : State -> Mode
  guard : State -> Bool
  reset : State -> State

def hybridStep (h : HybridSystem) (x : h.State) : h.State :=
  if h.guard x then h.reset x else h.step x

theorem hybrid_guard_uses_reset (h : HybridSystem) (x : h.State) :
    h.guard x = true -> hybridStep h x = h.reset x := by
  intro hg
  unfold hybridStep
  rw [hg]

theorem hybrid_no_guard_uses_update (h : HybridSystem) (x : h.State) :
    h.guard x = false -> hybridStep h x = h.step x := by
  intro hg
  unfold hybridStep
  rw [hg]

structure AxisRecord where
  historical : Nat
  effective : Nat

def rankDropped (r : AxisRecord) : Prop :=
  r.effective < r.historical

theorem historical_axis_survives_rank_drop :
    exists r : AxisRecord, r.historical = 2 /\ r.effective = 1 /\ rankDropped r := by
  exact Exists.intro { historical := 2, effective := 1 } (And.intro rfl (And.intro rfl (by decide)))

theorem rank_drop_not_historical_erasure (r : AxisRecord) :
    rankDropped r -> r.historical = 0 -> False := by
  intro h hz
  unfold rankDropped at h
  rw [hz] at h
  exact Nat.not_lt_zero r.effective h

theorem residue_is_not_identity :
    MorphismClass.residue != MorphismClass.identity := by
  decide

theorem rebirth_is_not_identity :
    MorphismClass.rebirth != MorphismClass.identity := by
  decide

structure VerdictClass where
  Case : Type
  verdict : Case -> Status

structure ComponentCase where
  component : Component
  present : Bool
deriving Repr

def componentVerdict (x : ComponentCase) : Status :=
  if x.present then Status.pass else Status.fail

def componentVerdictClass : VerdictClass :=
  { Case := ComponentCase, verdict := componentVerdict }

structure ComponentWitness (VC : VerdictClass) where
  keep : VC.Case
  drop : VC.Case
  keep_pass : VC.verdict keep = Status.pass
  drop_fail : VC.verdict drop = Status.fail

def witnessForComponent (c : Component) : ComponentWitness componentVerdictClass :=
  {
    keep := { component := c, present := true },
    drop := { component := c, present := false },
    keep_pass := by rfl,
    drop_fail := by rfl
  }

theorem component_witness_changes_verdict (VC : VerdictClass) (w : ComponentWitness VC) :
    VC.verdict w.keep != VC.verdict w.drop := by
  rw [w.keep_pass, w.drop_fail]
  decide

theorem every_component_has_witness (c : Component) :
    exists w : ComponentWitness componentVerdictClass,
      component_witness_changes_verdict componentVerdictClass w := by
  exact Exists.intro (witnessForComponent c) (component_witness_changes_verdict componentVerdictClass (witnessForComponent c))

theorem component_witness_is_one_component_delta (c : Component) :
    (witnessForComponent c).keep.component = c /\
    (witnessForComponent c).drop.component = c /\
    (witnessForComponent c).keep.present = true /\
    (witnessForComponent c).drop.present = false := by
  exact And.intro rfl (And.intro rfl (And.intro rfl rfl))

inductive ReductionVerdict where
  | preserves
  | losesWitness
deriving DecidableEq, Repr

structure TransitionEvidence where
  transition : AdjacentK
  witnessRetained : Bool
  addedAxisObservable : Bool
  demotionAllowed : Bool
  reduction : ReductionVerdict

def reductionFails (w : TransitionEvidence) : Prop :=
  w.witnessRetained = true /\ w.addedAxisObservable = true /\ w.reduction = ReductionVerdict.losesWitness

def lawfulDemotion (w : TransitionEvidence) : Prop :=
  w.witnessRetained = false /\ w.demotionAllowed = true /\ w.reduction = ReductionVerdict.preserves

def retainedTransitionEvidence (k : AdjacentK) : TransitionEvidence :=
  {
    transition := k,
    witnessRetained := true,
    addedAxisObservable := true,
    demotionAllowed := false,
    reduction := ReductionVerdict.losesWitness
  }

theorem adjacent_witness_blocks_reduction (w : TransitionEvidence) :
    w.witnessRetained = true ->
    w.addedAxisObservable = true ->
    w.reduction = ReductionVerdict.losesWitness ->
    reductionFails w := by
  intro hr ho hl
  exact And.intro hr (And.intro ho hl)

theorem every_adjacent_transition_has_witness (k : AdjacentK) :
    exists w : TransitionEvidence,
      w.transition = k /\ reductionFails w /\ w.demotionAllowed = false := by
  refine Exists.intro (retainedTransitionEvidence k) ?_
  exact And.intro rfl (And.intro (And.intro rfl (And.intro rfl rfl)) rfl)

theorem demotion_requires_lost_witness (w : TransitionEvidence) :
    lawfulDemotion w -> w.witnessRetained = false := by
  intro h
  exact h.left

end OC133V12
