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
  maintenance : Carrier -> Bool

structure Lifecycle (S Residue NewLive : Type) where
  admissible : S -> Bool
  live : S -> Bool
  death : S -> Bool
  residueOf : S -> Option Residue
  rebirthOf : Residue -> Option NewLive
  identityInvariant : S -> NewLive -> Bool

def cycleWitnessed (R : Realization) (x : R.Carrier) : Prop :=
  R.cycle x != none

def supportWitnessed (R : Realization) (x : R.Carrier) : Prop :=
  cycleWitnessed R x \/ R.maintenance x = true

def eligibleLive (R : Realization) (x : R.Carrier) : Prop :=
  R.admissible x = true /\ R.live x = true /\ supportWitnessed R x

theorem eligible_live_requires_cycle (R : Realization) (x : R.Carrier) :
    eligibleLive R x -> supportWitnessed R x := by
  intro h
  exact h.right.right

theorem eligible_live_requires_cycle_or_maintenance (R : Realization) (x : R.Carrier) :
    eligibleLive R x -> cycleWitnessed R x \/ R.maintenance x = true := by
  intro h
  exact h.right.right

theorem eligible_live_requires_admissible (R : Realization) (x : R.Carrier) :
    eligibleLive R x -> R.admissible x = true := by
  intro h
  exact h.left

theorem cycle_mode_required_for_eligible_live (R : Realization) (x : R.Carrier) :
    eligibleLive R x -> R.maintenance x = false -> R.cycle x != none := by
  intro h
  intro hm
  cases h.right.right with
  | inl hc => exact hc
  | inr hmaint =>
      rw [hm] at hmaint
      cases hmaint

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
  derivativeAvailable : Bool
  derivative_requires_chart : derivativeAvailable = true -> charted = true

def smoothAsUpdate (s : SmoothSystem) : UpdateSystem :=
  { State := s.State, step := s.step, admissible := s.admissible }

theorem smooth_operator_is_update_special_case (s : SmoothSystem) :
    (smoothAsUpdate s).step = s.step := by
  rfl

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

theorem declared_death_blocks_live {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) :
    L.death x = true -> L.live x = false -> L.live x = true -> False := by
  intro _ hnot hlive
  rw [hnot] at hlive
  cases hlive

structure OCTupleFlags where
  carrier : Bool
  realization : Bool
  lawfulPossibility : Bool
  liveness : Bool
  residue : Bool
  morphisms : Bool
  boundaries : Bool
  operators : Bool
  cycles : Bool
  dimension : Bool
  kFunctional : Bool
deriving Repr

def fullOCTuple : OCTupleFlags :=
  {
    carrier := true,
    realization := true,
    lawfulPossibility := true,
    liveness := true,
    residue := true,
    morphisms := true,
    boundaries := true,
    operators := true,
    cycles := true,
    dimension := true,
    kFunctional := true
  }

def componentPresent (s : OCTupleFlags) : Component -> Bool
  | Component.carrier => s.carrier
  | Component.realization => s.realization
  | Component.lawfulPossibility => s.lawfulPossibility
  | Component.liveness => s.liveness
  | Component.residue => s.residue
  | Component.morphisms => s.morphisms
  | Component.boundaries => s.boundaries
  | Component.operators => s.operators
  | Component.cycles => s.cycles
  | Component.dimension => s.dimension
  | Component.kFunctional => s.kFunctional

def dropComponent (s : OCTupleFlags) : Component -> OCTupleFlags
  | Component.carrier => { s with carrier := false }
  | Component.realization => { s with realization := false }
  | Component.lawfulPossibility => { s with lawfulPossibility := false }
  | Component.liveness => { s with liveness := false }
  | Component.residue => { s with residue := false }
  | Component.morphisms => { s with morphisms := false }
  | Component.boundaries => { s with boundaries := false }
  | Component.operators => { s with operators := false }
  | Component.cycles => { s with cycles := false }
  | Component.dimension => { s with dimension := false }
  | Component.kFunctional => { s with kFunctional := false }

def allComponentsPresent (s : OCTupleFlags) : Bool :=
  s.carrier
    && s.realization
    && s.lawfulPossibility
    && s.liveness
    && s.residue
    && s.morphisms
    && s.boundaries
    && s.operators
    && s.cycles
    && s.dimension
    && s.kFunctional

def ocTupleVerdict (s : OCTupleFlags) : Status :=
  if allComponentsPresent s then Status.pass else Status.fail

theorem full_oc_tuple_passes :
    ocTupleVerdict fullOCTuple = Status.pass := by
  rfl

theorem dropped_component_fails (c : Component) :
    ocTupleVerdict (dropComponent fullOCTuple c) = Status.fail := by
  cases c <;> rfl

theorem every_component_has_witness (c : Component) :
    ocTupleVerdict fullOCTuple = Status.pass /\
    ocTupleVerdict (dropComponent fullOCTuple c) = Status.fail := by
  exact And.intro full_oc_tuple_passes (dropped_component_fails c)

theorem component_witness_is_one_component_delta (c : Component) :
    componentPresent fullOCTuple c = true /\
    componentPresent (dropComponent fullOCTuple c) c = false := by
  cases c <;> exact And.intro rfl rfl

inductive ReductionVerdict where
  | preserves
  | losesWitness
deriving DecidableEq, Repr

structure TransitionEvidence where
  transition : AdjacentK
  lowerCode : Nat
  upperCode : Nat
  addedAxisCode : Nat
  witnessCode : Nat
  witnessRetained : Bool
  addedAxisObservable : Bool
  demotionAllowed : Bool
  reduction : ReductionVerdict

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

def witnessCode (k : AdjacentK) : Nat :=
  upperCode k * 100 + 7

def transitionCodesAlign (w : TransitionEvidence) : Prop :=
  w.upperCode = w.lowerCode + 1 /\
  w.addedAxisCode = w.upperCode /\
  w.witnessCode = w.upperCode * 100 + 7

def reductionFails (w : TransitionEvidence) : Prop :=
  transitionCodesAlign w /\
  w.witnessRetained = true /\
  w.addedAxisObservable = true /\
  w.reduction = ReductionVerdict.losesWitness

def lawfulDemotion (w : TransitionEvidence) : Prop :=
  transitionCodesAlign w /\
  w.witnessRetained = false /\
  w.addedAxisObservable = false /\
  w.demotionAllowed = true /\
  w.reduction = ReductionVerdict.preserves

def retainedTransitionEvidence (k : AdjacentK) : TransitionEvidence :=
  {
    transition := k,
    lowerCode := lowerCode k,
    upperCode := upperCode k,
    addedAxisCode := upperCode k,
    witnessCode := witnessCode k,
    witnessRetained := true,
    addedAxisObservable := true,
    demotionAllowed := false,
    reduction := ReductionVerdict.losesWitness
  }

def demotedTransitionEvidence (k : AdjacentK) : TransitionEvidence :=
  {
    transition := k,
    lowerCode := lowerCode k,
    upperCode := upperCode k,
    addedAxisCode := upperCode k,
    witnessCode := witnessCode k,
    witnessRetained := false,
    addedAxisObservable := false,
    demotionAllowed := true,
    reduction := ReductionVerdict.preserves
  }

theorem retained_transition_codes_align (k : AdjacentK) :
    transitionCodesAlign (retainedTransitionEvidence k) := by
  cases k <;> decide

theorem demoted_transition_codes_align (k : AdjacentK) :
    transitionCodesAlign (demotedTransitionEvidence k) := by
  cases k <;> decide

theorem adjacent_witness_blocks_reduction (w : TransitionEvidence) :
    transitionCodesAlign w ->
    w.witnessRetained = true ->
    w.addedAxisObservable = true ->
    w.reduction = ReductionVerdict.losesWitness ->
    reductionFails w := by
  intro hc hr ho hl
  exact And.intro hc (And.intro hr (And.intro ho hl))

theorem every_adjacent_transition_has_witness (k : AdjacentK) :
    exists w : TransitionEvidence,
      w.transition = k /\ reductionFails w /\ w.demotionAllowed = false := by
  refine Exists.intro (retainedTransitionEvidence k) ?_
  exact And.intro rfl (And.intro (And.intro (retained_transition_codes_align k) (And.intro rfl (And.intro rfl rfl))) rfl)

theorem demotion_requires_lost_witness (w : TransitionEvidence) :
    lawfulDemotion w -> w.witnessRetained = false := by
  intro h
  exact h.right.left

theorem every_adjacent_transition_has_lawful_demotion_case (k : AdjacentK) :
    exists w : TransitionEvidence,
      w.transition = k /\ lawfulDemotion w := by
  refine Exists.intro (demotedTransitionEvidence k) ?_
  exact And.intro rfl (And.intro (demoted_transition_codes_align k) (And.intro rfl (And.intro rfl (And.intro rfl rfl))))

end OC133V12
