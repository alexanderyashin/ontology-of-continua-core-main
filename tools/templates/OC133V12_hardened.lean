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

def boolStatus (b : Bool) : Status :=
  if b then Status.pass else Status.fail

structure Resolution (S : Type) where
  cell : S -> Nat

structure RawSeparation (S : Type) where
  separated : S -> S -> Bool

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

theorem k0_resolution_does_not_force_raw_separation {S : Type}
    (rho : Resolution S) (raw : RawSeparation S) (a b : S) :
    sameCell rho a b -> raw.separated a b = true -> distinguished rho a b = False := by
  intro hs _
  exact k0_same_cell_not_distinguished rho a b hs

structure MaintenanceEvidence where
  obligationChecked : Bool
  supportAvailable : Bool

def nonVacuousMaintenance (m : MaintenanceEvidence) : Prop :=
  m.obligationChecked = true /\ m.supportAvailable = true

structure Realization where
  Carrier : Type
  admissible : Carrier -> Bool
  live : Carrier -> Bool
  cycle : Carrier -> Option CycleMode
  maintenance : Carrier -> Option MaintenanceEvidence

def cycleWitnessed (R : Realization) (x : R.Carrier) : Prop :=
  R.cycle x != none

def maintenanceWitnessed (R : Realization) (x : R.Carrier) : Prop :=
  exists m, R.maintenance x = some m /\ nonVacuousMaintenance m

def supportWitnessed (R : Realization) (x : R.Carrier) : Prop :=
  cycleWitnessed R x \/ maintenanceWitnessed R x

def eligibleLive (R : Realization) (x : R.Carrier) : Prop :=
  R.admissible x = true /\ R.live x = true /\ supportWitnessed R x

theorem eligible_live_requires_cycle (R : Realization) (x : R.Carrier) :
    eligibleLive R x -> supportWitnessed R x := by
  intro h
  exact h.right.right

theorem eligible_live_requires_cycle_or_maintenance (R : Realization) (x : R.Carrier) :
    eligibleLive R x -> cycleWitnessed R x \/ maintenanceWitnessed R x := by
  intro h
  exact h.right.right

theorem eligible_live_requires_admissible (R : Realization) (x : R.Carrier) :
    eligibleLive R x -> R.admissible x = true := by
  intro h
  exact h.left

theorem cycle_mode_required_for_eligible_live (R : Realization) (x : R.Carrier) :
    eligibleLive R x -> (R.maintenance x = none) -> R.cycle x != none := by
  intro h hm
  cases h.right.right with
  | inl hc => exact hc
  | inr hmnt =>
      rcases hmnt with ⟨m, hsome, _⟩
      rw [hm] at hsome
      cases hsome

structure Lifecycle (S Residue NewLive : Type) where
  admissible : S -> Bool
  live : S -> Bool
  death : S -> Bool
  deathBlocksLive : forall x : S, death x = true -> live x = false
  residueOf : S -> Option Residue
  rebirthOf : Residue -> Option NewLive
  identityInvariant : S -> NewLive -> Bool

theorem declared_death_blocks_live {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) :
    L.death x = true -> L.live x = false := by
  intro h
  exact L.deathBlocksLive x h

structure MorphismEvidence where
  class : MorphismClass
  invariantPreserved : Bool

def isIdentityMorphism (m : MorphismEvidence) : Prop :=
  m.class = MorphismClass.identity /\ m.invariantPreserved = true

theorem residue_is_not_identity :
    MorphismClass.residue != MorphismClass.identity := by
  decide

theorem rebirth_is_not_identity :
    MorphismClass.rebirth != MorphismClass.identity := by
  decide

theorem residue_preservation_not_identity_without_invariant (m : MorphismEvidence) :
    m.class = MorphismClass.residue -> m.invariantPreserved = false -> Not (isIdentityMorphism m) := by
  intro hc _
  intro hid
  rw [hc] at hid
  exact residue_is_not_identity hid.left

theorem rebirth_not_identity_without_invariant (m : MorphismEvidence) :
    m.class = MorphismClass.rebirth -> m.invariantPreserved = false -> Not (isIdentityMorphism m) := by
  intro hc _
  intro hid
  rw [hc] at hid
  exact rebirth_is_not_identity hid.left

def restartClass {S Residue NewLive : Type} (L : Lifecycle S Residue NewLive) (x : S) (y : NewLive) : MorphismClass :=
  if L.identityInvariant x y then MorphismClass.identity else MorphismClass.rebirth

theorem invariant_preserved_classifies_identity {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (y : NewLive) :
    L.identityInvariant x y = true -> restartClass L x y = MorphismClass.identity := by
  intro h
  unfold restartClass
  rw [h]

theorem invariant_lost_blocks_identity {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (y : NewLive) :
    L.identityInvariant x y = false -> restartClass L x y != MorphismClass.identity := by
  intro h
  unfold restartClass
  rw [h]
  decide

structure ZeroCause where
  flow : Bool
  coherence : Bool
  identity : Bool
  embedding : Bool

def hasZeroCauseBool (z : ZeroCause) : Bool :=
  z.flow || z.coherence || z.identity || z.embedding

def hasZeroCause (z : ZeroCause) : Prop :=
  hasZeroCauseBool z = true

def computedK (z : ZeroCause) : Nat :=
  if hasZeroCauseBool z then 0 else 1

def kZeroLicensed (z : ZeroCause) : Prop :=
  computedK z = 0

theorem zero_cause_has_cause (z : ZeroCause) :
    z.flow = true -> hasZeroCause z := by
  intro h
  unfold hasZeroCause hasZeroCauseBool
  rw [h]
  simp

theorem k_zero_iff_declared_zero_cause (z : ZeroCause) :
    kZeroLicensed z <-> hasZeroCause z := by
  unfold kZeroLicensed computedK hasZeroCause
  cases h : hasZeroCauseBool z <;> simp [h]

structure ContinuumnessCase where
  admissibleNonempty : Bool
  cycleWitness : Bool
  causes : ZeroCause

def continuumnessZeroAccepted (c : ContinuumnessCase) : Prop :=
  c.admissibleNonempty = true /\ c.cycleWitness = true /\ hasZeroCause c.causes

theorem k_zero_can_have_nonempty_support (c : ContinuumnessCase) :
    continuumnessZeroAccepted c -> c.admissibleNonempty = true /\ c.cycleWitness = true := by
  intro h
  exact And.intro h.left h.right.left

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
  step_eq_flow_one : forall x : State, step x = flow 1 x
  derivativeAvailable : Bool
  derivative_requires_chart : derivativeAvailable = true -> charted = true

def smoothAsUpdate (s : SmoothSystem) : UpdateSystem :=
  { State := s.State, step := s.step, admissible := s.admissible }

theorem smooth_operator_is_update_special_case (s : SmoothSystem) (x : s.State) :
    (smoothAsUpdate s).step x = s.flow 1 x := by
  exact s.step_eq_flow_one x

theorem differential_notation_requires_chart (s : SmoothSystem) :
    s.derivativeAvailable = true -> s.charted = true := by
  intro h
  exact s.derivative_requires_chart h

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

structure AxisTrajectory where
  hist0 : Nat
  hist1 : Nat
  hist2 : Nat
  eff0 : Nat
  eff1 : Nat
  eff2 : Nat

def historicalMonotone (t : AxisTrajectory) : Prop :=
  t.hist0 <= t.hist1 /\ t.hist1 <= t.hist2

def effectiveRankDrops (t : AxisTrajectory) : Prop :=
  t.eff2 < t.eff1

theorem historical_axis_survives_rank_drop :
    exists t : AxisTrajectory, historicalMonotone t /\ effectiveRankDrops t := by
  refine Exists.intro { hist0 := 1, hist1 := 2, hist2 := 2, eff0 := 1, eff1 := 2, eff2 := 1 } ?_
  exact And.intro (And.intro (by decide) (by decide)) (by decide)

theorem rank_drop_not_historical_erasure (r : AxisRecord) :
    rankDropped r -> r.historical = 0 -> False := by
  intro h hz
  unfold rankDropped at h
  rw [hz] at h
  exact Nat.not_lt_zero r.effective h

structure OCSemanticCase where
  carrierWitness : Bool
  realizationInterprets : Bool
  lawfulTransitionOnly : Bool
  liveSupportWitness : Bool
  residueSeparated : Bool
  morphismInvariantChecked : Bool
  boundaryRejectsBadState : Bool
  typedOperatorUpdate : Bool
  cycleOrMaintenance : Bool
  dimensionAxesSeparated : Bool
  kZeroCauseDeclared : Bool
deriving Repr

def semanticObligation (s : OCSemanticCase) : Component -> Bool
  | Component.carrier => s.carrierWitness
  | Component.realization => s.realizationInterprets
  | Component.lawfulPossibility => s.lawfulTransitionOnly
  | Component.liveness => s.liveSupportWitness
  | Component.residue => s.residueSeparated
  | Component.morphisms => s.morphismInvariantChecked
  | Component.boundaries => s.boundaryRejectsBadState
  | Component.operators => s.typedOperatorUpdate
  | Component.cycles => s.cycleOrMaintenance
  | Component.dimension => s.dimensionAxesSeparated
  | Component.kFunctional => s.kZeroCauseDeclared

def semanticVerdict (s : OCSemanticCase) : Status :=
  boolStatus (
    s.carrierWitness
    && s.realizationInterprets
    && s.lawfulTransitionOnly
    && s.liveSupportWitness
    && s.residueSeparated
    && s.morphismInvariantChecked
    && s.boundaryRejectsBadState
    && s.typedOperatorUpdate
    && s.cycleOrMaintenance
    && s.dimensionAxesSeparated
    && s.kZeroCauseDeclared
  )

def fullSemanticCase : OCSemanticCase :=
  {
    carrierWitness := true,
    realizationInterprets := true,
    lawfulTransitionOnly := true,
    liveSupportWitness := true,
    residueSeparated := true,
    morphismInvariantChecked := true,
    boundaryRejectsBadState := true,
    typedOperatorUpdate := true,
    cycleOrMaintenance := true,
    dimensionAxesSeparated := true,
    kZeroCauseDeclared := true
  }

def dropSemanticComponent (s : OCSemanticCase) : Component -> OCSemanticCase
  | Component.carrier => { s with carrierWitness := false }
  | Component.realization => { s with realizationInterprets := false }
  | Component.lawfulPossibility => { s with lawfulTransitionOnly := false }
  | Component.liveness => { s with liveSupportWitness := false }
  | Component.residue => { s with residueSeparated := false }
  | Component.morphisms => { s with morphismInvariantChecked := false }
  | Component.boundaries => { s with boundaryRejectsBadState := false }
  | Component.operators => { s with typedOperatorUpdate := false }
  | Component.cycles => { s with cycleOrMaintenance := false }
  | Component.dimension => { s with dimensionAxesSeparated := false }
  | Component.kFunctional => { s with kZeroCauseDeclared := false }

theorem full_semantic_case_passes :
    semanticVerdict fullSemanticCase = Status.pass := by
  rfl

theorem dropped_semantic_component_fails (c : Component) :
    semanticVerdict (dropSemanticComponent fullSemanticCase c) = Status.fail := by
  cases c <;> rfl

theorem every_component_has_witness (c : Component) :
    semanticVerdict fullSemanticCase = Status.pass /\
    semanticVerdict (dropSemanticComponent fullSemanticCase c) = Status.fail := by
  exact And.intro full_semantic_case_passes (dropped_semantic_component_fails c)

theorem component_witness_is_one_component_delta (c : Component) :
    semanticObligation fullSemanticCase c = true /\
    semanticObligation (dropSemanticComponent fullSemanticCase c) c = false := by
  cases c <;> exact And.intro rfl rfl

inductive ReductionVerdict where
  | preserves
  | losesWitness
deriving DecidableEq, Repr

structure KTransitionModel where
  transition : AdjacentK
  lowerLevel : Nat
  upperLevel : Nat
  upperAxisValue : Nat
  reducedAxisValue : Nat
  threshold : Nat
deriving Repr

def lowerCode : AdjacentK -> Nat
  | AdjacentK.k0_k1 => 0
  | AdjacentK.k1_k2 => 1
  | AdjacentK.k2_k3 => 2
  | AdjacentK.k3_k4 => 3
  | AdjacentK.k4_k5 => 4
  | AdjacentK.k5_k6 => 5
  | AdjacentK.k6_k7 => 6
  | AdjacentK.k7_k8 => 7
  | AdjacentK.k8_k9 => 8
  | AdjacentK.k9_k10 => 9
  | AdjacentK.k10_k11 => 10
  | AdjacentK.k11_k12 => 11

def upperCode (k : AdjacentK) : Nat :=
  lowerCode k + 1

def axisVerdict (value threshold : Nat) : Bool :=
  decide (value > threshold)

def upperKVerdict (m : KTransitionModel) : Bool :=
  axisVerdict m.upperAxisValue m.threshold

def reducedKVerdict (m : KTransitionModel) : Bool :=
  axisVerdict m.reducedAxisValue m.threshold

def reductionFails (m : KTransitionModel) : Prop :=
  upperKVerdict m = true /\ reducedKVerdict m = false

def lawfulDemotion (m : KTransitionModel) : Prop :=
  upperKVerdict m = reducedKVerdict m

def retainedTransitionEvidence (k : AdjacentK) : KTransitionModel :=
  {
    transition := k,
    lowerLevel := lowerCode k,
    upperLevel := upperCode k,
    upperAxisValue := upperCode k,
    reducedAxisValue := 0,
    threshold := 0
  }

def demotedTransitionEvidence (k : AdjacentK) : KTransitionModel :=
  {
    transition := k,
    lowerLevel := lowerCode k,
    upperLevel := upperCode k,
    upperAxisValue := 0,
    reducedAxisValue := 0,
    threshold := 0
  }

theorem retained_transition_reduction_fails (k : AdjacentK) :
    reductionFails (retainedTransitionEvidence k) := by
  cases k <;> decide

theorem demoted_transition_is_lawful (k : AdjacentK) :
    lawfulDemotion (demotedTransitionEvidence k) := by
  cases k <;> decide

theorem adjacent_witness_blocks_reduction (m : KTransitionModel) :
    upperKVerdict m = true -> reducedKVerdict m = false -> reductionFails m := by
  intro hu hr
  exact And.intro hu hr

theorem every_adjacent_transition_has_witness (k : AdjacentK) :
    exists m : KTransitionModel, m.transition = k /\ reductionFails m := by
  refine Exists.intro (retainedTransitionEvidence k) ?_
  exact And.intro rfl (retained_transition_reduction_fails k)

theorem demotion_requires_lost_witness (m : KTransitionModel) :
    lawfulDemotion m -> upperKVerdict m = reducedKVerdict m := by
  intro h
  exact h

theorem every_adjacent_transition_has_lawful_demotion_case (k : AdjacentK) :
    exists m : KTransitionModel, m.transition = k /\ lawfulDemotion m := by
  refine Exists.intro (demotedTransitionEvidence k) ?_
  exact And.intro rfl (demoted_transition_is_lawful k)

end OC133V12
