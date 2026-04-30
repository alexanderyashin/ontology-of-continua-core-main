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

inductive K0CounterPoint where
  | a
  | b
deriving DecidableEq, Repr

def k0CounterResolution : Resolution K0CounterPoint :=
  { cell := fun _ => 0 }

def k0CounterRawSeparation : RawSeparation K0CounterPoint :=
  { separated := fun x y => decide (x != y) }

theorem k0_countermodel_raw_separation_not_resolution_distinction :
    sameCell k0CounterResolution K0CounterPoint.a K0CounterPoint.b /\
    k0CounterRawSeparation.separated K0CounterPoint.a K0CounterPoint.b = true /\
    distinguished k0CounterResolution K0CounterPoint.a K0CounterPoint.b = False := by
  exact And.intro rfl (And.intro (by decide) (k0_same_cell_not_distinguished k0CounterResolution K0CounterPoint.a K0CounterPoint.b rfl))

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

def maintenanceWitnessed (R : Realization) (x : R.Carrier) : Prop :=
  exists m, R.maintenance x = some m /\ nonVacuousMaintenance m

def cycleWitnessed (R : Realization) (x : R.Carrier) : Prop :=
  match R.cycle x with
  | none => False
  | some CycleMode.degenerate => maintenanceWitnessed R x
  | some _ => True

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
  | inl hc =>
      unfold cycleWitnessed at hc
      cases hcyc : R.cycle x with
      | none =>
          rw [hcyc] at hc
          cases hc
      | some c =>
          simp
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
  sourceToken : S -> Nat
  residueToken : Residue -> Nat
  newLiveToken : NewLive -> Nat
  sourceTokenInjective : forall x y : S, sourceToken x = sourceToken y -> x = y
  residueTokenInjective : forall x y : Residue, residueToken x = residueToken y -> x = y
  newLiveTokenInjective : forall x y : NewLive, newLiveToken x = newLiveToken y -> x = y

theorem declared_death_blocks_live {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) :
    L.death x = true -> L.live x = false := by
  intro h
  exact L.deathBlocksLive x h

theorem death_live_conflict_impossible {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) :
    L.death x = true -> L.live x = true -> False := by
  intro hdeath hlive
  have hblocked : L.live x = false := L.deathBlocksLive x hdeath
  rw [hlive] at hblocked
  cases hblocked

theorem residue_rebirth_are_typed_source_target_relations {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (r : Residue) (y : NewLive) :
    L.residueOf x = some r -> L.rebirthOf r = some y -> L.death x = true ->
    L.live x = false /\ L.residueOf x = some r /\ L.rebirthOf r = some y := by
  intro hres hreb hdeath
  exact And.intro (declared_death_blocks_live L x hdeath) (And.intro hres hreb)

theorem lifecycle_source_tokens_bind_carrier_endpoint {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x y : S) :
    L.sourceToken x = L.sourceToken y -> x = y := by
  exact L.sourceTokenInjective x y

theorem lifecycle_rebirth_tokens_bind_target_endpoint {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x y : NewLive) :
    L.newLiveToken x = L.newLiveToken y -> x = y := by
  exact L.newLiveTokenInjective x y

structure MorphismEvidence where
  sourceToken : Nat
  residueToken : Option Nat
  targetToken : Nat
  mclass : MorphismClass
  invariantPreserved : Bool

def isIdentityMorphism (m : MorphismEvidence) : Prop :=
  m.mclass = MorphismClass.identity /\
  m.invariantPreserved = true /\
  m.residueToken = none /\
  m.sourceToken = m.targetToken

def sameEndpointBool {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (y : NewLive) : Bool :=
  decide (L.sourceToken x = L.newLiveToken y)

def endpointBoundIdentity {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (y : NewLive) (m : MorphismEvidence) : Prop :=
  m.sourceToken = L.sourceToken x /\
  m.targetToken = L.newLiveToken y /\
  L.sourceToken x = L.newLiveToken y /\
  L.identityInvariant x y = true /\
  isIdentityMorphism m

def tokenSeparatedRebirth {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (r : Residue) (y : NewLive) : Prop :=
  L.sourceToken x ≠ L.residueToken r /\
  L.residueToken r ≠ L.newLiveToken y /\
  L.sourceToken x ≠ L.newLiveToken y

def typedRebirthMorphism {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (r : Residue) (y : NewLive) (m : MorphismEvidence) : Prop :=
  m.sourceToken = L.sourceToken x /\
  m.residueToken = some (L.residueToken r) /\
  m.targetToken = L.newLiveToken y /\
  m.mclass = MorphismClass.rebirth /\
  tokenSeparatedRebirth L x r y

def typedResidueMorphism {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (r : Residue) (m : MorphismEvidence) : Prop :=
  m.sourceToken = L.sourceToken x /\
  m.residueToken = some (L.residueToken r) /\
  m.targetToken = L.sourceToken x /\
  m.mclass = MorphismClass.residue /\
  L.sourceToken x ≠ L.residueToken r

theorem residue_is_not_identity :
    MorphismClass.residue ≠ MorphismClass.identity := by
  decide

theorem rebirth_is_not_identity :
    MorphismClass.rebirth ≠ MorphismClass.identity := by
  decide

theorem residue_is_not_rebirth :
    MorphismClass.residue ≠ MorphismClass.rebirth := by
  decide

theorem residue_preservation_not_identity_without_invariant (m : MorphismEvidence) :
    m.mclass = MorphismClass.residue -> m.invariantPreserved = false -> Not (isIdentityMorphism m) := by
  intro hc _
  intro hid
  have hclass := hid.left
  rw [hc] at hclass
  exact residue_is_not_identity hclass

theorem rebirth_not_identity_without_invariant (m : MorphismEvidence) :
    m.mclass = MorphismClass.rebirth -> m.invariantPreserved = false -> Not (isIdentityMorphism m) := by
  intro hc _
  intro hid
  have hclass := hid.left
  rw [hc] at hclass
  exact rebirth_is_not_identity hclass

theorem lifecycle_status_morphism_separation {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (m : MorphismEvidence) :
    L.death x = true ->
    m.mclass = MorphismClass.rebirth ->
    m.invariantPreserved = false ->
    L.live x = false /\ Not (isIdentityMorphism m) := by
  intro hdeath hclass hinv
  exact And.intro (declared_death_blocks_live L x hdeath) (rebirth_not_identity_without_invariant m hclass hinv)

theorem lifecycle_residue_rebirth_morphism_boundary {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (r : Residue) (y : NewLive)
    (mResidue mRebirth : MorphismEvidence) :
    L.death x = true ->
    L.residueOf x = some r ->
    L.rebirthOf r = some y ->
    typedResidueMorphism L x r mResidue ->
    typedRebirthMorphism L x r y mRebirth ->
    L.live x = false /\
      L.residueOf x = some r /\
      L.rebirthOf r = some y /\
      typedResidueMorphism L x r mResidue /\
      typedRebirthMorphism L x r y mRebirth /\
      mResidue.targetToken = L.sourceToken x /\
      L.sourceToken x ≠ L.residueToken r /\
      Not (endpointBoundIdentity L x y mResidue) /\
      Not (endpointBoundIdentity L x y mRebirth) := by
  intro hdeath hres hreb hresTyped hrebTyped
  have hresNotIdentity : Not (endpointBoundIdentity L x y mResidue) := by
    intro hid
    have hidentityClass := hid.right.right.right.right.left
    have hresidueClass := hresTyped.right.right.right.left
    rw [hresidueClass] at hidentityClass
    exact residue_is_not_identity hidentityClass
  have hrebNotIdentity : Not (endpointBoundIdentity L x y mRebirth) := by
    intro hid
    have hidentityClass := hid.right.right.right.right.left
    have hrebirthClass := hrebTyped.right.right.right.left
    rw [hrebirthClass] at hidentityClass
    exact rebirth_is_not_identity hidentityClass
  exact And.intro
    (declared_death_blocks_live L x hdeath)
    (And.intro hres
      (And.intro hreb
        (And.intro hresTyped
          (And.intro hrebTyped
            (And.intro hresTyped.right.right.left
              (And.intro hresTyped.right.right.right.right
                (And.intro hresNotIdentity hrebNotIdentity)))))))

theorem lifecycle_statuses_and_morphisms_separated {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) :
    L.death x = true ->
    L.live x = false /\
    (L.live x = true -> False) /\
    MorphismClass.residue ≠ MorphismClass.identity /\
    MorphismClass.rebirth ≠ MorphismClass.identity /\
    MorphismClass.residue ≠ MorphismClass.rebirth := by
  intro hdeath
  exact And.intro
    (declared_death_blocks_live L x hdeath)
    (And.intro
      (death_live_conflict_impossible L x hdeath)
      (And.intro residue_is_not_identity (And.intro rebirth_is_not_identity residue_is_not_rebirth)))

theorem residue_or_rebirth_not_identity_without_invariant (m : MorphismEvidence) :
    (m.mclass = MorphismClass.residue \/ m.mclass = MorphismClass.rebirth) ->
    m.invariantPreserved = false ->
    Not (isIdentityMorphism m) := by
  intro hclass hinv
  cases hclass with
  | inl hres => exact residue_preservation_not_identity_without_invariant m hres hinv
  | inr hreb => exact rebirth_not_identity_without_invariant m hreb hinv

theorem residue_or_rebirth_class_blocks_identity (m : MorphismEvidence) :
    (m.mclass = MorphismClass.residue \/ m.mclass = MorphismClass.rebirth) ->
    Not (isIdentityMorphism m) := by
  intro hclass hid
  cases hclass with
  | inl hres =>
      have hclass := hid.left
      rw [hres] at hclass
      exact residue_is_not_identity hclass
  | inr hreb =>
      have hclass := hid.left
      rw [hreb] at hclass
      exact rebirth_is_not_identity hclass

theorem identity_positive_case_when_invariant_preserved (m : MorphismEvidence) :
    m.mclass = MorphismClass.identity ->
    m.invariantPreserved = true ->
    m.residueToken = none ->
    m.sourceToken = m.targetToken ->
    isIdentityMorphism m := by
  intro hc hi hr hend
  exact And.intro hc (And.intro hi (And.intro hr hend))

theorem endpoint_bound_identity_positive {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (y : NewLive) (m : MorphismEvidence) :
    m.sourceToken = L.sourceToken x ->
    m.targetToken = L.newLiveToken y ->
    L.sourceToken x = L.newLiveToken y ->
    L.identityInvariant x y = true ->
    m.mclass = MorphismClass.identity ->
    m.invariantPreserved = true ->
    m.residueToken = none ->
    endpointBoundIdentity L x y m := by
  intro hsource htarget hend hinvdecl hc hi hr
  exact And.intro hsource (And.intro htarget (And.intro hend (And.intro hinvdecl
    (identity_positive_case_when_invariant_preserved m hc hi hr (by
      rw [hsource, htarget]
      exact hend)))))

theorem residue_rebirth_identity_boundary (m : MorphismEvidence) :
    (((m.mclass = MorphismClass.residue \/ m.mclass = MorphismClass.rebirth) ->
      Not (isIdentityMorphism m)) /\
    (m.mclass = MorphismClass.identity -> m.invariantPreserved = true -> m.residueToken = none -> m.sourceToken = m.targetToken -> isIdentityMorphism m)) := by
  exact And.intro
    (residue_or_rebirth_class_blocks_identity m)
    (identity_positive_case_when_invariant_preserved m)

theorem endpoint_bound_identity_classification {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (r : Residue) (y : NewLive) (m : MorphismEvidence) :
    (typedResidueMorphism L x r m -> Not (endpointBoundIdentity L x y m)) /\
    (typedRebirthMorphism L x r y m -> Not (endpointBoundIdentity L x y m)) /\
    (m.sourceToken = L.sourceToken x ->
      m.targetToken = L.newLiveToken y ->
      L.sourceToken x = L.newLiveToken y ->
      L.identityInvariant x y = true ->
      m.mclass = MorphismClass.identity ->
      m.invariantPreserved = true ->
      m.residueToken = none ->
      endpointBoundIdentity L x y m) := by
  exact And.intro
    (by
      intro htyped hid
      have hidentityClass := hid.right.right.right.right.left
      have hresidueClass := htyped.right.right.right.left
      rw [hresidueClass] at hidentityClass
      exact residue_is_not_identity hidentityClass)
    (And.intro
    (by
      intro htyped hid
      have hidentityClass := hid.right.right.right.right.left
      have hrebirthClass := htyped.right.right.right.left
      rw [hrebirthClass] at hidentityClass
      exact rebirth_is_not_identity hidentityClass)
    (endpoint_bound_identity_positive L x y m))

theorem invariant_lost_blocks_identity {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (y : NewLive) (m : MorphismEvidence) :
    L.identityInvariant x y = false -> Not (endpointBoundIdentity L x y m) := by
  intro hinv hend
  have hdeclared : L.identityInvariant x y = true := hend.right.right.right.left
  rw [hinv] at hdeclared
  cases hdeclared

theorem endpoint_mismatch_blocks_identity {S Residue NewLive : Type}
    (L : Lifecycle S Residue NewLive) (x : S) (y : NewLive) (m : MorphismEvidence) :
    sameEndpointBool L x y = false -> Not (endpointBoundIdentity L x y m) := by
  intro hsame hend
  have hendpoint : L.sourceToken x = L.newLiveToken y := hend.right.right.left
  unfold sameEndpointBool at hsame
  rw [hendpoint] at hsame
  simp at hsame

structure ZeroCause where
  flow : Bool
  coherence : Bool
  identity : Bool
  embedding : Bool

structure ContinuumnessObstruction where
  flowBlocked : Bool
  coherenceBroken : Bool
  identitySplit : Bool
  embeddingFailure : Bool

def hasZeroCauseBool (z : ZeroCause) : Bool :=
  z.flow || z.coherence || z.identity || z.embedding

def hasZeroCause (z : ZeroCause) : Prop :=
  hasZeroCauseBool z = true

def obstructionActiveBool (o : ContinuumnessObstruction) : Bool :=
  o.flowBlocked || o.coherenceBroken || o.identitySplit || o.embeddingFailure

def computedK (o : ContinuumnessObstruction) : Nat :=
  if obstructionActiveBool o then 1 else 0

def kZeroLicensed (z : ZeroCause) (o : ContinuumnessObstruction) : Prop :=
  hasZeroCause z /\ computedK o = 0

theorem zero_cause_has_cause (z : ZeroCause) :
    z.flow = true -> hasZeroCause z := by
  intro h
  unfold hasZeroCause hasZeroCauseBool
  rw [h]
  simp

theorem continuumness_score_zero_iff_no_obstruction (o : ContinuumnessObstruction) :
    computedK o = 0 <-> obstructionActiveBool o = false := by
  unfold computedK
  cases obstructionActiveBool o <;> simp

theorem zero_cause_does_not_compute_k_by_itself (z : ZeroCause) (o : ContinuumnessObstruction) :
    hasZeroCause z -> obstructionActiveBool o = true -> computedK o ≠ 0 := by
  intro _ h
  unfold computedK
  rw [h]
  simp

theorem declared_zero_cause_with_clear_obstruction_licenses_k_zero
    (z : ZeroCause) (o : ContinuumnessObstruction) :
    hasZeroCause z -> obstructionActiveBool o = false -> kZeroLicensed z o := by
  intro hz ho
  unfold kZeroLicensed
  exact And.intro hz ((continuumness_score_zero_iff_no_obstruction o).mpr ho)

structure ContinuumnessCase where
  liveSupport : Bool
  admissibleNonempty : Bool
  cycleWitness : Bool
  causes : ZeroCause
  obstructions : ContinuumnessObstruction

def continuumnessZeroAccepted (c : ContinuumnessCase) : Prop :=
  c.liveSupport = true /\
    c.admissibleNonempty = true /\
    c.cycleWitness = true /\
    hasZeroCause c.causes /\
    obstructionActiveBool c.obstructions = false

theorem k_zero_can_have_nonempty_support (c : ContinuumnessCase) :
    continuumnessZeroAccepted c -> c.liveSupport = true /\ c.admissibleNonempty = true /\ c.cycleWitness = true := by
  intro h
  exact And.intro h.left (And.intro h.right.left h.right.right.left)

theorem k_zero_with_nonempty_support_requires_cause_and_clear_obstruction (c : ContinuumnessCase) :
    c.liveSupport = true ->
    c.admissibleNonempty = true ->
    c.cycleWitness = true ->
    (kZeroLicensed c.causes c.obstructions <->
      hasZeroCause c.causes /\ obstructionActiveBool c.obstructions = false) := by
  intro _ _ _
  unfold kZeroLicensed
  constructor
  · intro h
    exact And.intro h.left ((continuumness_score_zero_iff_no_obstruction c.obstructions).mp h.right)
  · intro h
    exact And.intro h.left ((continuumness_score_zero_iff_no_obstruction c.obstructions).mpr h.right)

def continuumnessCaseZero (c : ContinuumnessCase) : Prop :=
  c.liveSupport = true /\
    c.admissibleNonempty = true /\
    c.cycleWitness = true /\
    kZeroLicensed c.causes c.obstructions

theorem continuumness_zero_case_iff_declared_zero_cause_with_support (c : ContinuumnessCase) :
    continuumnessCaseZero c <->
      (c.liveSupport = true /\
        c.admissibleNonempty = true /\
        c.cycleWitness = true /\
        hasZeroCause c.causes /\
        obstructionActiveBool c.obstructions = false) := by
  unfold continuumnessCaseZero
  constructor
  · intro h
    exact And.intro h.left
      (And.intro h.right.left
        (And.intro h.right.right.left
          (And.intro h.right.right.right.left
            ((continuumness_score_zero_iff_no_obstruction c.obstructions).mp h.right.right.right.right))))
  · intro h
    exact And.intro h.left
      (And.intro h.right.left
        (And.intro h.right.right.left
          (declared_zero_cause_with_clear_obstruction_licenses_k_zero c.causes c.obstructions h.right.right.right.left h.right.right.right.right)))

structure BoundaryClassifier (S StatusType : Type) where
  classify : S -> StatusType
  fails : StatusType -> Bool

def boundaryFails {S StatusType : Type} (b : BoundaryClassifier S StatusType) (x : S) : Bool :=
  b.fails (b.classify x)

structure MetricBoundary (S : Type) where
  distance : S -> S -> Nat
  center : S
  threshold : Nat

def metricMeasure {S : Type} (m : MetricBoundary S) : S -> Nat :=
  fun x => m.distance x m.center

def metricAsClassifier {S : Type} (m : MetricBoundary S) : BoundaryClassifier S Nat :=
  { classify := metricMeasure m, fails := fun n => decide (n > m.threshold) }

theorem metric_boundary_is_classifier {S : Type} (m : MetricBoundary S) :
    (metricAsClassifier m).classify = metricMeasure m := by
  rfl

theorem metric_boundary_failure_equiv {S : Type} (m : MetricBoundary S) (x : S) :
    boundaryFails (metricAsClassifier m) x = decide (m.distance x m.center > m.threshold) := by
  rfl

theorem metric_boundary_specialization {S : Type} (m : MetricBoundary S) (x : S) :
    (metricAsClassifier m).classify = metricMeasure m /\
    boundaryFails (metricAsClassifier m) x = decide (m.distance x m.center > m.threshold) := by
  exact And.intro (metric_boundary_is_classifier m) (metric_boundary_failure_equiv m x)

structure UpdateSystem where
  State : Type
  step : State -> State
  admissible : State -> Bool

structure SmoothChart (State : Type) where
  derivative : (State -> State) -> State -> State
  localLaw : (State -> State) -> State -> Prop
  inDomain : State -> Bool

structure SmoothSystem extends UpdateSystem where
  chart : Option (SmoothChart State)
  flow : Nat -> State -> State
  flow_zero : forall x : State, flow 0 x = x
  step_eq_flow_one : forall x : State, step x = flow 1 x

def chartRecordPresent (s : SmoothSystem) : Bool :=
  s.chart.isSome

def smoothFlowNotationAdmitted (s : SmoothSystem) : Bool :=
  chartRecordPresent s

def smoothAsUpdate (s : SmoothSystem) : UpdateSystem :=
  { State := s.State, step := s.step, admissible := s.admissible }

theorem smooth_operator_is_update_special_case (s : SmoothSystem) (x : s.State) :
    (smoothAsUpdate s).step x = s.flow 1 x := by
  exact s.step_eq_flow_one x

theorem differential_notation_requires_chart (s : SmoothSystem) :
    chartRecordPresent s = true -> exists c : SmoothChart s.State, s.chart = some c := by
  intro h
  cases hchart : s.chart with
  | none =>
      unfold chartRecordPresent at h
      rw [hchart] at h
      simp at h
  | some c =>
      exact Exists.intro c rfl

theorem no_chart_rejects_smooth_flow_notation (s : SmoothSystem) :
    s.chart = none -> smoothFlowNotationAdmitted s = false := by
  intro h
  unfold smoothFlowNotationAdmitted chartRecordPresent
  rw [h]
  rfl

theorem smooth_chart_has_domain_and_local_law
    (s : SmoothSystem) (c : SmoothChart s.State) (x : s.State) :
    s.chart = some c ->
    c.inDomain x = true ->
    c.localLaw s.step x ->
    c.inDomain x = true /\ c.localLaw s.step x := by
  intro _ hdomain hlaw
  exact And.intro hdomain hlaw

structure HybridSystem extends UpdateSystem where
  Mode : Type
  mode : State -> Mode
  resetSourceModeTyped : Mode -> Bool
  resetTargetModeTyped : Mode -> Bool
  guard : State -> Bool
  reset : State -> State

structure ProofRewriteSystem extends UpdateSystem where
  rewriteRulePresent : Bool
  flowNotationRequested : Bool

def proofRewriteDerivativeAllowed (_p : ProofRewriteSystem) : Bool :=
  false

inductive OperatorRoute where
  | smoothChart
  | guardResetHybrid
  | proofRewrite
deriving DecidableEq, Repr

structure OperatorAdmission where
  route : OperatorRoute
  chartDeclared : Bool
  chartDomainContainsSource : Bool
  chartLocalLawDeclared : Bool
  flowNotationRequested : Bool
  typedSourceTarget : Bool
  guardEvaluated : Bool
  guardValue : Bool
  resetSourceTyped : Bool
  resetTargetTyped : Bool
  resetAdmissible : Bool
  rewriteRulePresent : Bool

def operatorAdmitted (a : OperatorAdmission) : Bool :=
  a.typedSourceTarget &&
  match a.route with
  | OperatorRoute.smoothChart =>
      a.chartDeclared && a.chartDomainContainsSource && a.chartLocalLawDeclared
  | OperatorRoute.guardResetHybrid =>
      (!a.flowNotationRequested) && a.guardEvaluated && a.resetSourceTyped && a.resetTargetTyped && a.resetAdmissible
  | OperatorRoute.proofRewrite =>
      (!a.flowNotationRequested) && a.rewriteRulePresent

theorem admitted_operator_has_typed_source_target (a : OperatorAdmission) :
    operatorAdmitted a = true -> a.typedSourceTarget = true := by
  cases a with
  | mk route chart domain law requested typed guard guardValue resetSource resetTarget resetAdmit rewrite =>
      intro h
      simp [operatorAdmitted] at h
      exact h.left

theorem admitted_guard_reset_rejects_derivative (a : OperatorAdmission) :
    a.route = OperatorRoute.guardResetHybrid -> operatorAdmitted a = true -> a.flowNotationRequested = false := by
  cases a with
  | mk route chart domain law requested typed guard guardValue resetSource resetTarget resetAdmit rewrite =>
      intro hroute hadmit
      cases route
      · cases hroute
      · simp [operatorAdmitted] at hadmit
        exact hadmit.right.left.left.left.left
      · cases hroute

theorem admitted_proof_rewrite_rejects_derivative (a : OperatorAdmission) :
    a.route = OperatorRoute.proofRewrite -> operatorAdmitted a = true -> a.flowNotationRequested = false := by
  cases a with
  | mk route chart domain law requested typed guard guardValue resetSource resetTarget resetAdmit rewrite =>
      intro hroute hadmit
      cases route
      · cases hroute
      · cases hroute
      · simp [operatorAdmitted] at hadmit
        exact hadmit.right.left

theorem admitted_smooth_chart_requires_chart (a : OperatorAdmission) :
    a.route = OperatorRoute.smoothChart -> operatorAdmitted a = true -> a.chartDeclared = true := by
  cases a with
  | mk route chart domain law requested typed guard guardValue resetSource resetTarget resetAdmit rewrite =>
      intro hroute hadmit
      cases route
      · simp [operatorAdmitted] at hadmit
        exact hadmit.right.left.left
      · cases hroute
      · cases hroute

theorem admitted_smooth_chart_requires_domain_and_law (a : OperatorAdmission) :
    a.route = OperatorRoute.smoothChart -> operatorAdmitted a = true ->
    a.chartDomainContainsSource = true /\ a.chartLocalLawDeclared = true := by
  cases a with
  | mk route chart domain law requested typed guard guardValue resetSource resetTarget resetAdmit rewrite =>
      intro hroute hadmit
      cases route
      · simp [operatorAdmitted] at hadmit
        exact And.intro hadmit.right.left.right hadmit.right.right
      · cases hroute
      · cases hroute

theorem admitted_guard_reset_has_typed_reset_obligations (a : OperatorAdmission) :
    a.route = OperatorRoute.guardResetHybrid -> operatorAdmitted a = true ->
    a.guardEvaluated = true /\ a.resetSourceTyped = true /\ a.resetTargetTyped = true /\ a.resetAdmissible = true := by
  cases a with
  | mk route chart domain law requested typed guard guardValue resetSource resetTarget resetAdmit rewrite =>
      intro hroute hadmit
      cases route
      · cases hroute
      · simp [operatorAdmitted] at hadmit
        exact And.intro hadmit.right.left.left.left.right
          (And.intro hadmit.right.left.left.right
            (And.intro hadmit.right.left.right hadmit.right.right))
      · cases hroute

theorem admitted_proof_rewrite_has_rule (a : OperatorAdmission) :
    a.route = OperatorRoute.proofRewrite -> operatorAdmitted a = true -> a.rewriteRulePresent = true := by
  cases a with
  | mk route chart domain law requested typed guard guardValue resetSource resetTarget resetAdmit rewrite =>
      intro hroute hadmit
      cases route
      · cases hroute
      · cases hroute
      · simp [operatorAdmitted] at hadmit
        exact hadmit.right.right

theorem operator_admission_route_obligations (a : OperatorAdmission) :
    operatorAdmitted a = true ->
    (a.route = OperatorRoute.smoothChart ->
      a.chartDeclared = true /\ a.chartDomainContainsSource = true /\ a.chartLocalLawDeclared = true) /\
    (a.route = OperatorRoute.guardResetHybrid ->
      a.flowNotationRequested = false /\ a.guardEvaluated = true /\
      a.resetSourceTyped = true /\ a.resetTargetTyped = true /\ a.resetAdmissible = true) /\
    (a.route = OperatorRoute.proofRewrite ->
      a.flowNotationRequested = false /\ a.rewriteRulePresent = true) := by
  intro hadmit
  constructor
  · intro hroute
    exact And.intro
      (admitted_smooth_chart_requires_chart a hroute hadmit)
      (admitted_smooth_chart_requires_domain_and_law a hroute hadmit)
  constructor
  · intro hroute
    have hguard := admitted_guard_reset_has_typed_reset_obligations a hroute hadmit
    exact And.intro
      (admitted_guard_reset_rejects_derivative a hroute hadmit)
      hguard
  · intro hroute
    exact And.intro
      (admitted_proof_rewrite_rejects_derivative a hroute hadmit)
      (admitted_proof_rewrite_has_rule a hroute hadmit)

theorem derivative_request_requires_chart_or_rewrite_rejection (a : OperatorAdmission) :
    operatorAdmitted a = true -> a.flowNotationRequested = true ->
    (a.route = OperatorRoute.proofRewrite \/ a.route = OperatorRoute.guardResetHybrid -> False) /\
    (a.route = OperatorRoute.smoothChart -> a.chartDeclared = true) := by
  intro hadmit hreq
  cases a with
  | mk route chart domain law requested typed guard guardValue resetSource resetTarget resetAdmit rewrite =>
      simp [operatorAdmitted] at hadmit hreq
      subst hreq
      cases route
      · simp at hadmit
        constructor
        · intro h
          cases h with
          | inl hproof => cases hproof
          | inr hhybrid => cases hhybrid
        · intro _
          exact hadmit.right.left.left
      · simp at hadmit
      · simp at hadmit

def hybridStep (h : HybridSystem) (x : h.State) : h.State :=
  if h.guard x then h.reset x else h.step x

theorem hybrid_guard_uses_reset (h : HybridSystem) (x : h.State) :
    h.guard x = true -> hybridStep h x = h.reset x := by
  intro hg
  simp [hybridStep, hg]

theorem hybrid_no_guard_uses_update (h : HybridSystem) (x : h.State) :
    h.guard x = false -> hybridStep h x = h.step x := by
  intro hg
  simp [hybridStep, hg]

structure BoundHybridAdmission (h : HybridSystem) (x : h.State) where
  admission : OperatorAdmission
  route_bound : admission.route = OperatorRoute.guardResetHybrid
  guard_observed_bound : admission.guardEvaluated = true
  guard_value_bound : admission.guardValue = h.guard x
  reset_source_mode_bound : admission.resetSourceTyped = h.resetSourceModeTyped (h.mode x)
  reset_target_mode_bound : admission.resetTargetTyped = h.resetTargetModeTyped (h.mode (h.reset x))
  codomain_bound : admission.typedSourceTarget = true
  reset_admissible_value : admission.resetAdmissible = true
  reset_admissible_bound : admission.resetAdmissible = h.admissible (h.reset x)
  admitted_bound : operatorAdmitted admission = true

theorem bound_hybrid_admission_obligations
    (h : HybridSystem) (x : h.State) (b : BoundHybridAdmission h x) :
    b.admission.route = OperatorRoute.guardResetHybrid /\
    b.admission.guardEvaluated = true /\
    b.admission.guardValue = h.guard x /\
    b.admission.resetSourceTyped = h.resetSourceModeTyped (h.mode x) /\
    h.resetSourceModeTyped (h.mode x) = true /\
    b.admission.resetTargetTyped = h.resetTargetModeTyped (h.mode (h.reset x)) /\
    h.resetTargetModeTyped (h.mode (h.reset x)) = true /\
    b.admission.resetSourceTyped = true /\
    b.admission.resetTargetTyped = true /\
    b.admission.typedSourceTarget = true /\
    (h.guard x = true -> h.admissible (h.reset x) = true /\ hybridStep h x = h.reset x) /\
    (h.guard x = false -> hybridStep h x = h.step x) := by
  have hadmissTrue : h.admissible (h.reset x) = true := by
    rw [<- b.reset_admissible_bound]
    exact b.reset_admissible_value
  have hsourceTrue : b.admission.resetSourceTyped = true := by
    have hob := admitted_guard_reset_has_typed_reset_obligations b.admission b.route_bound b.admitted_bound
    exact hob.right.left
  have htargetTrue : b.admission.resetTargetTyped = true := by
    have hob := admitted_guard_reset_has_typed_reset_obligations b.admission b.route_bound b.admitted_bound
    exact hob.right.right.left
  have hsourceModeTrue : h.resetSourceModeTyped (h.mode x) = true := by
    rw [<- b.reset_source_mode_bound]
    exact hsourceTrue
  have htargetModeTrue : h.resetTargetModeTyped (h.mode (h.reset x)) = true := by
    rw [<- b.reset_target_mode_bound]
    exact htargetTrue
  exact And.intro b.route_bound
    (And.intro b.guard_observed_bound
      (And.intro b.guard_value_bound
        (And.intro b.reset_source_mode_bound
          (And.intro hsourceModeTrue
            (And.intro b.reset_target_mode_bound
              (And.intro htargetModeTrue
                (And.intro hsourceTrue
                  (And.intro htargetTrue
                    (And.intro b.codomain_bound
                      (And.intro
                        (fun htrue => And.intro hadmissTrue (hybrid_guard_uses_reset h x htrue))
                        (fun hfalse => hybrid_no_guard_uses_update h x hfalse)))))))))))

theorem proof_rewrite_update_has_no_derivative (p : ProofRewriteSystem) :
    proofRewriteDerivativeAllowed p = false := by
  rfl

theorem guard_reset_binding_obligations
    (h : HybridSystem) (xh : h.State) (a : OperatorAdmission) :
    a.route = OperatorRoute.guardResetHybrid ->
    a.guardEvaluated = true ->
    a.guardValue = h.guard xh ->
    a.resetSourceTyped = h.resetSourceModeTyped (h.mode xh) ->
    a.resetTargetTyped = h.resetTargetModeTyped (h.mode (h.reset xh)) ->
    a.resetAdmissible = h.admissible (h.reset xh) ->
    operatorAdmitted a = true ->
    a.guardEvaluated = true /\
    a.resetSourceTyped = h.resetSourceModeTyped (h.mode xh) /\
    h.resetSourceModeTyped (h.mode xh) = true /\
    a.resetTargetTyped = h.resetTargetModeTyped (h.mode (h.reset xh)) /\
    h.resetTargetModeTyped (h.mode (h.reset xh)) = true /\
    (h.guard xh = true -> h.admissible (h.reset xh) = true /\ hybridStep h xh = h.reset xh) /\
    (h.guard xh = false -> hybridStep h xh = h.step xh) := by
  intro hroute hobserved _ hsource htarget hadmiss hadmit
  have hob := admitted_guard_reset_has_typed_reset_obligations a hroute hadmit
  have hsourceModeTrue : h.resetSourceModeTyped (h.mode xh) = true := by
    rw [<- hsource]
    exact hob.right.left
  have htargetModeTrue : h.resetTargetModeTyped (h.mode (h.reset xh)) = true := by
    rw [<- htarget]
    exact hob.right.right.left
  have hadmissTrue : h.admissible (h.reset xh) = true := by
    rw [<- hadmiss]
    exact hob.right.right.right
  exact And.intro hob.left
    (And.intro
      hsource
      (And.intro
        hsourceModeTrue
        (And.intro
          htarget
          (And.intro
            htargetModeTrue
            (And.intro
              (fun htrue => And.intro hadmissTrue (hybrid_guard_uses_reset h xh htrue))
              (fun hfalse => hybrid_no_guard_uses_update h xh hfalse))))))

theorem proof_rewrite_binding_obligations
    (p : ProofRewriteSystem) (a : OperatorAdmission) :
    a.route = OperatorRoute.proofRewrite ->
    a.rewriteRulePresent = p.rewriteRulePresent ->
    operatorAdmitted a = true ->
    p.rewriteRulePresent = true /\ proofRewriteDerivativeAllowed p = false /\ a.flowNotationRequested = false := by
  intro hroute hrewrite hadmit
  have hrewriteA := admitted_proof_rewrite_has_rule a hroute hadmit
  have hderiv := admitted_proof_rewrite_rejects_derivative a hroute hadmit
  exact And.intro (by rw [<- hrewrite]; exact hrewriteA)
    (And.intro (proof_rewrite_update_has_no_derivative p) hderiv)

theorem smooth_hybrid_operator_semantics
    (s : SmoothSystem) (h : HybridSystem) (p : ProofRewriteSystem)
    (xs : s.State) (xh : h.State) (c : SmoothChart s.State)
    (aSmooth aHybrid aProof : OperatorAdmission) :
    s.chart = some c ->
    aSmooth.route = OperatorRoute.smoothChart ->
    aSmooth.chartDeclared = true ->
    aHybrid.route = OperatorRoute.guardResetHybrid ->
    aProof.route = OperatorRoute.proofRewrite ->
    operatorAdmitted aSmooth = true ->
    operatorAdmitted aHybrid = true ->
    operatorAdmitted aProof = true ->
    (smoothAsUpdate s).step xs = s.flow 1 xs /\
    s.chart = some c /\
    aSmooth.typedSourceTarget = true /\
    aSmooth.chartDeclared = true /\
    aHybrid.typedSourceTarget = true /\
    aProof.typedSourceTarget = true /\
    aHybrid.flowNotationRequested = false /\
    aProof.flowNotationRequested = false /\
    (chartRecordPresent s = true -> exists c : SmoothChart s.State, s.chart = some c) /\
    (s.chart = none -> smoothFlowNotationAdmitted s = false) /\
    (h.guard xh = true -> hybridStep h xh = h.reset xh) /\
    (h.guard xh = false -> hybridStep h xh = h.step xh) /\
    proofRewriteDerivativeAllowed p = false := by
  intro hchart hsmooth hsmoothChart hhybrid hproof hadmitSmooth hadmitHybrid hadmitProof
  exact And.intro
    (smooth_operator_is_update_special_case s xs)
    (And.intro
      hchart
      (And.intro
        (admitted_operator_has_typed_source_target aSmooth hadmitSmooth)
        (And.intro
          hsmoothChart
          (And.intro
            (admitted_operator_has_typed_source_target aHybrid hadmitHybrid)
            (And.intro
              (admitted_operator_has_typed_source_target aProof hadmitProof)
              (And.intro
                (admitted_guard_reset_rejects_derivative aHybrid hhybrid hadmitHybrid)
                (And.intro
                  (admitted_proof_rewrite_rejects_derivative aProof hproof hadmitProof)
                  (And.intro
                    (differential_notation_requires_chart s)
                    (And.intro
                      (no_chart_rejects_smooth_flow_notation s)
                      (And.intro (hybrid_guard_uses_reset h xh)
                        (And.intro (hybrid_no_guard_uses_update h xh) (proof_rewrite_update_has_no_derivative p))))))))))))

theorem integrated_operator_semantics
    (s : SmoothSystem) (h : HybridSystem) (p : ProofRewriteSystem)
    (xs : s.State) (xh : h.State) (c : SmoothChart s.State)
    (aSmooth aHybrid aProof : OperatorAdmission) :
    s.chart = some c ->
    c.inDomain xs = true ->
    c.localLaw s.step xs ->
    aSmooth.route = OperatorRoute.smoothChart ->
    aSmooth.chartDeclared = true ->
    aSmooth.chartDomainContainsSource = c.inDomain xs ->
    aSmooth.chartLocalLawDeclared = true ->
    aHybrid.route = OperatorRoute.guardResetHybrid ->
    aHybrid.guardEvaluated = true ->
    aHybrid.guardValue = h.guard xh ->
    aHybrid.resetSourceTyped = h.resetSourceModeTyped (h.mode xh) ->
    aHybrid.resetTargetTyped = h.resetTargetModeTyped (h.mode (h.reset xh)) ->
    aHybrid.resetAdmissible = h.admissible (h.reset xh) ->
    aProof.route = OperatorRoute.proofRewrite ->
    aProof.rewriteRulePresent = p.rewriteRulePresent ->
    operatorAdmitted aSmooth = true ->
    operatorAdmitted aHybrid = true ->
    operatorAdmitted aProof = true ->
    (smoothAsUpdate s).step xs = s.flow 1 xs /\
    c.inDomain xs = true /\
    c.localLaw s.step xs /\
    aSmooth.chartDeclared = true /\
    aSmooth.chartDomainContainsSource = true /\
    aSmooth.chartLocalLawDeclared = true /\
    aHybrid.guardEvaluated = true /\
    h.resetSourceModeTyped (h.mode xh) = true /\
    h.resetTargetModeTyped (h.mode (h.reset xh)) = true /\
    (h.guard xh = true -> h.admissible (h.reset xh) = true /\ hybridStep h xh = h.reset xh) /\
    (h.guard xh = false -> hybridStep h xh = h.step xh) /\
    p.rewriteRulePresent = true /\
    proofRewriteDerivativeAllowed p = false /\
    aHybrid.flowNotationRequested = false /\
    aProof.flowNotationRequested = false := by
  intro hchart hdomain hlaw hsmooth hsmoothChart hsmoothDomain hsmoothLaw hhybrid hguardEvaluated hguardValue hsource htarget hadmiss hproof hrewrite hadmitSmooth hadmitHybrid hadmitProof
  have hsDomainLaw := admitted_smooth_chart_requires_domain_and_law aSmooth hsmooth hadmitSmooth
  have hhybridBinding := guard_reset_binding_obligations h xh aHybrid hhybrid hguardEvaluated hguardValue hsource htarget hadmiss hadmitHybrid
  have hproofBinding := proof_rewrite_binding_obligations p aProof hproof hrewrite hadmitProof
  constructor
  · exact smooth_operator_is_update_special_case s xs
  constructor
  · exact hdomain
  constructor
  · exact hlaw
  constructor
  · exact hsmoothChart
  constructor
  · exact hsDomainLaw.left
  constructor
  · exact hsmoothLaw
  constructor
  · exact hhybridBinding.left
  constructor
  · exact hhybridBinding.right.right.left
  constructor
  · exact hhybridBinding.right.right.right.right.left
  constructor
  · exact hhybridBinding.right.right.right.right.right.left
  constructor
  · exact hhybridBinding.right.right.right.right.right.right
  constructor
  · exact hproofBinding.left
  constructor
  · exact hproofBinding.right.left
  constructor
  · exact admitted_guard_reset_rejects_derivative aHybrid hhybrid hadmitHybrid
  · exact hproofBinding.right.right

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
  unfold historicalMonotone effectiveRankDrops
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

def componentRegistryCode : Component -> Nat
  | Component.carrier => 0
  | Component.realization => 1
  | Component.lawfulPossibility => 2
  | Component.liveness => 3
  | Component.residue => 4
  | Component.morphisms => 5
  | Component.boundaries => 6
  | Component.operators => 7
  | Component.cycles => 8
  | Component.dimension => 9
  | Component.kFunctional => 10

def componentRegistryComplete (c : Component) : Prop :=
  componentRegistryCode c <= 10

theorem component_registry_complete_and_witnessed (c : Component) :
    componentRegistryComplete c /\
    semanticVerdict fullSemanticCase = Status.pass /\
    semanticVerdict (dropSemanticComponent fullSemanticCase c) = Status.fail /\
    semanticObligation fullSemanticCase c = true /\
    semanticObligation (dropSemanticComponent fullSemanticCase c) c = false := by
  cases c <;> exact And.intro (by unfold componentRegistryComplete; decide) (And.intro rfl (And.intro rfl (And.intro rfl rfl)))

structure ReleaseTuple where
  semanticCase : OCSemanticCase
  componentActive : Component -> Bool
  componentObligation : Component -> Bool

def promotedReleaseTuple : ReleaseTuple :=
  {
    semanticCase := fullSemanticCase,
    componentActive := fun _ => true,
    componentObligation := semanticObligation fullSemanticCase
  }

def eraseReleaseTupleComponent (c : Component) : ReleaseTuple :=
  {
    semanticCase := dropSemanticComponent fullSemanticCase c,
    componentActive := fun d => if d = c then false else true,
    componentObligation := semanticObligation (dropSemanticComponent fullSemanticCase c)
  }

def semanticDropReleaseTupleComponent (c : Component) : ReleaseTuple :=
  {
    semanticCase := dropSemanticComponent fullSemanticCase c,
    componentActive := fun _ => true,
    componentObligation := fun _ => true
  }

def allComponentsActive (t : ReleaseTuple) : Bool :=
  t.componentActive Component.carrier &&
  t.componentActive Component.realization &&
  t.componentActive Component.lawfulPossibility &&
  t.componentActive Component.liveness &&
  t.componentActive Component.residue &&
  t.componentActive Component.morphisms &&
  t.componentActive Component.boundaries &&
  t.componentActive Component.operators &&
  t.componentActive Component.cycles &&
  t.componentActive Component.dimension &&
  t.componentActive Component.kFunctional

def allComponentObligations (t : ReleaseTuple) : Bool :=
  t.componentObligation Component.carrier &&
  t.componentObligation Component.realization &&
  t.componentObligation Component.lawfulPossibility &&
  t.componentObligation Component.liveness &&
  t.componentObligation Component.residue &&
  t.componentObligation Component.morphisms &&
  t.componentObligation Component.boundaries &&
  t.componentObligation Component.operators &&
  t.componentObligation Component.cycles &&
  t.componentObligation Component.dimension &&
  t.componentObligation Component.kFunctional

def releaseTupleVerdict (t : ReleaseTuple) : Status :=
  if allComponentsActive t && allComponentObligations t then semanticVerdict t.semanticCase else Status.fail

def semanticOnlyReleaseTupleVerdict (t : ReleaseTuple) : Status :=
  if allComponentsActive t then semanticVerdict t.semanticCase else Status.fail

theorem release_tuple_component_irredundant (c : Component) :
    promotedReleaseTuple.componentActive c = true /\
    promotedReleaseTuple.componentObligation c = true /\
    releaseTupleVerdict promotedReleaseTuple = Status.pass /\
    releaseTupleVerdict (eraseReleaseTupleComponent c) = Status.fail /\
    (eraseReleaseTupleComponent c).componentActive c = false /\
    (eraseReleaseTupleComponent c).componentObligation c = false := by
  cases c <;> native_decide

theorem release_tuple_semantic_component_irredundant (c : Component) :
    promotedReleaseTuple.componentActive c = true /\
    (semanticDropReleaseTupleComponent c).componentActive c = true /\
    promotedReleaseTuple.componentObligation c = true /\
    (semanticDropReleaseTupleComponent c).componentObligation c = true /\
    semanticObligation promotedReleaseTuple.semanticCase c = true /\
    semanticObligation (semanticDropReleaseTupleComponent c).semanticCase c = false /\
    semanticOnlyReleaseTupleVerdict promotedReleaseTuple = Status.pass /\
    semanticOnlyReleaseTupleVerdict (semanticDropReleaseTupleComponent c) = Status.fail := by
  cases c <;> native_decide

inductive KAxis where
  | continuity
  | phaseThreshold
  | autocatalyticClosure
  | membraneBoundary
  | excitableRegulation
  | bindingPrediction
  | trustCoordination
  | regimeShift
  | theoryDynamics
  | recursiveSelfApplication
  | crossDomainCoherence
  | evidenceGovernance
deriving DecidableEq, Repr

inductive ReductionVerdict where
  | preserves
  | losesWitness
deriving DecidableEq, Repr

structure KTransitionModel where
  transition : AdjacentK
  lowerLevel : Nat
  upperLevel : Nat
  axis : KAxis
  witnessObservation : Nat
  upperObservation : Nat
  reducedObservation : Nat
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

def axisFor : AdjacentK -> KAxis
  | AdjacentK.k0_k1 => KAxis.continuity
  | AdjacentK.k1_k2 => KAxis.phaseThreshold
  | AdjacentK.k2_k3 => KAxis.autocatalyticClosure
  | AdjacentK.k3_k4 => KAxis.membraneBoundary
  | AdjacentK.k4_k5 => KAxis.excitableRegulation
  | AdjacentK.k5_k6 => KAxis.bindingPrediction
  | AdjacentK.k6_k7 => KAxis.trustCoordination
  | AdjacentK.k7_k8 => KAxis.regimeShift
  | AdjacentK.k8_k9 => KAxis.theoryDynamics
  | AdjacentK.k9_k10 => KAxis.recursiveSelfApplication
  | AdjacentK.k10_k11 => KAxis.crossDomainCoherence
  | AdjacentK.k11_k12 => KAxis.evidenceGovernance

def transitionMatchesAtlas (m : KTransitionModel) : Prop :=
  m.lowerLevel = lowerCode m.transition /\
  m.upperLevel = upperCode m.transition /\
  m.axis = axisFor m.transition

def upperKVerdict (m : KTransitionModel) : Bool :=
  decide (m.upperObservation = m.witnessObservation)

def reducedKVerdict (m : KTransitionModel) : Bool :=
  decide (m.reducedObservation = m.witnessObservation)

def reductionMapPreservesAddedAxis (m : KTransitionModel) : Bool :=
  decide (m.reducedObservation = m.upperObservation)

def reductionMapPreservesWitness (m : KTransitionModel) : Bool :=
  decide (m.reducedObservation = m.witnessObservation)

def reductionFails (m : KTransitionModel) : Prop :=
  transitionMatchesAtlas m /\
  upperKVerdict m = true /\
  reducedKVerdict m = false /\
  reductionMapPreservesAddedAxis m = false /\
  reductionMapPreservesWitness m = false

def lawfulDemotion (m : KTransitionModel) : Prop :=
  transitionMatchesAtlas m /\
  upperKVerdict m = false /\
  reducedKVerdict m = false /\
  reductionMapPreservesAddedAxis m = false /\
  reductionMapPreservesWitness m = false

def retainedTransitionEvidence (k : AdjacentK) : KTransitionModel :=
  {
    transition := k,
    lowerLevel := lowerCode k,
    upperLevel := upperCode k,
    axis := axisFor k,
    witnessObservation := (upperCode k) * 100 + 7,
    upperObservation := (upperCode k) * 100 + 7,
    reducedObservation := lowerCode k
  }

def demotedTransitionEvidence (k : AdjacentK) : KTransitionModel :=
  {
    transition := k,
    lowerLevel := lowerCode k,
    upperLevel := upperCode k,
    axis := axisFor k,
    witnessObservation := (upperCode k) * 100 + 7,
    upperObservation := upperCode k,
    reducedObservation := lowerCode k
  }

def allAdjacentK : List AdjacentK :=
  [
    AdjacentK.k0_k1,
    AdjacentK.k1_k2,
    AdjacentK.k2_k3,
    AdjacentK.k3_k4,
    AdjacentK.k4_k5,
    AdjacentK.k5_k6,
    AdjacentK.k6_k7,
    AdjacentK.k7_k8,
    AdjacentK.k8_k9,
    AdjacentK.k9_k10,
    AdjacentK.k10_k11,
    AdjacentK.k11_k12
  ]

def adjacentKCoverageTotal : Nat := allAdjacentK.length

def transitionIdFor : AdjacentK -> String
  | AdjacentK.k0_k1 => "K0_to_K1"
  | AdjacentK.k1_k2 => "K1_to_K2"
  | AdjacentK.k2_k3 => "K2_to_K3"
  | AdjacentK.k3_k4 => "K3_to_K4"
  | AdjacentK.k4_k5 => "K4_to_K5"
  | AdjacentK.k5_k6 => "K5_to_K6"
  | AdjacentK.k6_k7 => "K6_to_K7"
  | AdjacentK.k7_k8 => "K7_to_K8"
  | AdjacentK.k8_k9 => "K8_to_K9"
  | AdjacentK.k9_k10 => "K9_to_K10"
  | AdjacentK.k10_k11 => "K10_to_K11"
  | AdjacentK.k11_k12 => "K11_to_K12"

def leanConstructorTextFor : AdjacentK -> String
  | AdjacentK.k0_k1 => "AdjacentK.k0_k1"
  | AdjacentK.k1_k2 => "AdjacentK.k1_k2"
  | AdjacentK.k2_k3 => "AdjacentK.k2_k3"
  | AdjacentK.k3_k4 => "AdjacentK.k3_k4"
  | AdjacentK.k4_k5 => "AdjacentK.k4_k5"
  | AdjacentK.k5_k6 => "AdjacentK.k5_k6"
  | AdjacentK.k6_k7 => "AdjacentK.k6_k7"
  | AdjacentK.k7_k8 => "AdjacentK.k7_k8"
  | AdjacentK.k8_k9 => "AdjacentK.k8_k9"
  | AdjacentK.k9_k10 => "AdjacentK.k9_k10"
  | AdjacentK.k10_k11 => "AdjacentK.k10_k11"
  | AdjacentK.k11_k12 => "AdjacentK.k11_k12"

def retainedFiniteCaseIdFor (k : AdjacentK) : String :=
  "FM-KLEVEL-" ++ transitionIdFor k

def demotionFiniteCaseIdFor (k : AdjacentK) : String :=
  "FM-KLEVEL-" ++ transitionIdFor k ++ "-NEG"

structure ReleaseAtlasManifestRow where
  transition : AdjacentK
  transitionId : String
  fromK : Nat
  toK : Nat
  leanConstructor : String
  retainedFiniteCaseId : String
  demotionFiniteCaseId : String
  releaseClassifierBound : Bool
  retainedWitnessPresent : Bool
  demotionControlPresent : Bool
deriving Repr

def releaseAtlasManifestRow (k : AdjacentK) : ReleaseAtlasManifestRow :=
  {
    transition := k,
    transitionId := transitionIdFor k,
    fromK := lowerCode k,
    toK := upperCode k,
    leanConstructor := leanConstructorTextFor k,
    retainedFiniteCaseId := retainedFiniteCaseIdFor k,
    demotionFiniteCaseId := demotionFiniteCaseIdFor k,
    releaseClassifierBound := true,
    retainedWitnessPresent := true,
    demotionControlPresent := true
  }

def releaseAtlasRowValid (k : AdjacentK) (row : ReleaseAtlasManifestRow) : Prop :=
  row.transition = k /\
  row.transitionId = transitionIdFor k /\
  row.fromK = lowerCode k /\
  row.toK = upperCode k /\
  row.leanConstructor = leanConstructorTextFor k /\
  row.retainedFiniteCaseId = retainedFiniteCaseIdFor k /\
  row.demotionFiniteCaseId = demotionFiniteCaseIdFor k /\
  row.releaseClassifierBound = true /\
  row.retainedWitnessPresent = true /\
  row.demotionControlPresent = true

structure KReleaseClassifierEvidence where
  transition : AdjacentK
  transitionId : String
  finiteCaseId : String
  axisObserved : Bool
  retainedWitnessMatches : Bool
  verdictChanges : Bool
  demotionObservationInert : Bool
deriving Repr

def retainedClassifierEvidence (k : AdjacentK) : KReleaseClassifierEvidence :=
  {
    transition := k,
    transitionId := transitionIdFor k,
    finiteCaseId := retainedFiniteCaseIdFor k,
    axisObserved := true,
    retainedWitnessMatches := true,
    verdictChanges := true,
    demotionObservationInert := false
  }

def demotedClassifierEvidence (k : AdjacentK) : KReleaseClassifierEvidence :=
  {
    transition := k,
    transitionId := transitionIdFor k,
    finiteCaseId := demotionFiniteCaseIdFor k,
    axisObserved := false,
    retainedWitnessMatches := false,
    verdictChanges := false,
    demotionObservationInert := true
  }

def releaseReductionFails (k : AdjacentK) (e : KReleaseClassifierEvidence) : Prop :=
  e.transition = k /\
  e.transitionId = transitionIdFor k /\
  e.finiteCaseId = retainedFiniteCaseIdFor k /\
  e.axisObserved = true /\
  e.retainedWitnessMatches = true /\
  e.verdictChanges = true

def releaseLawfulDemotion (k : AdjacentK) (e : KReleaseClassifierEvidence) : Prop :=
  e.transition = k /\
  e.transitionId = transitionIdFor k /\
  e.finiteCaseId = demotionFiniteCaseIdFor k /\
  e.axisObserved = false /\
  e.retainedWitnessMatches = false /\
  e.verdictChanges = false /\
  e.demotionObservationInert = true

theorem retained_transition_reduction_fails (k : AdjacentK) :
    reductionFails (retainedTransitionEvidence k) := by
  cases k <;> simp [reductionFails, transitionMatchesAtlas, retainedTransitionEvidence, upperKVerdict,
    reducedKVerdict, reductionMapPreservesAddedAxis, reductionMapPreservesWitness, lowerCode, upperCode, axisFor]

theorem demoted_transition_is_lawful (k : AdjacentK) :
    lawfulDemotion (demotedTransitionEvidence k) := by
  cases k <;> simp [lawfulDemotion, transitionMatchesAtlas, demotedTransitionEvidence, upperKVerdict,
    reducedKVerdict, reductionMapPreservesAddedAxis, reductionMapPreservesWitness, lowerCode, upperCode, axisFor]

theorem adjacent_witness_blocks_reduction (m : KTransitionModel) :
    transitionMatchesAtlas m ->
    upperKVerdict m = true ->
    reducedKVerdict m = false ->
    reductionMapPreservesAddedAxis m = false ->
    reductionMapPreservesWitness m = false ->
    reductionFails m := by
  intro hmatch hu hr haxis hwit
  exact And.intro hmatch (And.intro hu (And.intro hr (And.intro haxis hwit)))

theorem every_adjacent_transition_has_witness (k : AdjacentK) :
    exists m : KTransitionModel, m.transition = k /\ reductionFails m := by
  refine Exists.intro (retainedTransitionEvidence k) ?_
  exact And.intro rfl (retained_transition_reduction_fails k)

theorem demotion_requires_lost_witness (m : KTransitionModel) :
    lawfulDemotion m -> upperKVerdict m = false /\ reducedKVerdict m = false := by
  intro h
  exact And.intro h.right.left h.right.right.left

theorem every_adjacent_transition_has_lawful_demotion_case (k : AdjacentK) :
    exists m : KTransitionModel, m.transition = k /\ lawfulDemotion m := by
  refine Exists.intro (demotedTransitionEvidence k) ?_
  exact And.intro rfl (demoted_transition_is_lawful k)

theorem every_adjacent_transition_has_witness_and_demotion (k : AdjacentK) :
    exists retained demoted : KTransitionModel,
      retained.transition = k /\
      demoted.transition = k /\
      retained.axis = axisFor k /\
      demoted.axis = axisFor k /\
      reductionFails retained /\
      lawfulDemotion demoted := by
  refine Exists.intro (retainedTransitionEvidence k) ?_
  refine Exists.intro (demotedTransitionEvidence k) ?_
  exact And.intro rfl (And.intro rfl (And.intro rfl (And.intro rfl (And.intro (retained_transition_reduction_fails k) (demoted_transition_is_lawful k)))))

theorem every_adjacent_transition_matches_atlas_with_witness_and_lawful_demotion (k : AdjacentK) :
    exists retained demoted : KTransitionModel,
      retained.transition = k /\
      demoted.transition = k /\
      transitionMatchesAtlas retained /\
      transitionMatchesAtlas demoted /\
      reductionFails retained /\
      lawfulDemotion demoted /\
      upperKVerdict retained = true /\
      reducedKVerdict retained = false /\
      upperKVerdict demoted = false /\
      reducedKVerdict demoted = false := by
  refine Exists.intro (retainedTransitionEvidence k) ?_
  refine Exists.intro (demotedTransitionEvidence k) ?_
  exact And.intro rfl
    (And.intro rfl
      (And.intro (by cases k <;> exact And.intro rfl (And.intro rfl rfl))
        (And.intro (by cases k <;> exact And.intro rfl (And.intro rfl rfl))
          (And.intro (retained_transition_reduction_fails k)
            (And.intro (demoted_transition_is_lawful k)
              (And.intro (by cases k <;> rfl)
                (And.intro (by cases k <;> rfl)
                  (And.intro (by cases k <;> rfl) (by cases k <;> rfl)))))))))

theorem release_atlas_manifest_row_valid (k : AdjacentK) :
    releaseAtlasRowValid k (releaseAtlasManifestRow k) := by
  cases k <;> simp [releaseAtlasRowValid, releaseAtlasManifestRow, transitionIdFor,
    retainedFiniteCaseIdFor, demotionFiniteCaseIdFor, leanConstructorTextFor, lowerCode, upperCode]

theorem release_atlas_manifest_has_total_finite_case_coverage (k : AdjacentK) :
    adjacentKCoverageTotal = 12 /\
    releaseAtlasRowValid k (releaseAtlasManifestRow k) /\
    releaseReductionFails k (retainedClassifierEvidence k) /\
    releaseLawfulDemotion k (demotedClassifierEvidence k) /\
    (releaseAtlasManifestRow k).retainedFiniteCaseId = retainedFiniteCaseIdFor k /\
    (releaseAtlasManifestRow k).demotionFiniteCaseId = demotionFiniteCaseIdFor k /\
    (releaseAtlasManifestRow k).releaseClassifierBound = true := by
  exact And.intro rfl
    (And.intro (release_atlas_manifest_row_valid k)
      (And.intro (by cases k <;> simp [releaseReductionFails, retainedClassifierEvidence, transitionIdFor, retainedFiniteCaseIdFor])
        (And.intro (by cases k <;> simp [releaseLawfulDemotion, demotedClassifierEvidence, transitionIdFor, demotionFiniteCaseIdFor])
          (And.intro (by cases k <;> rfl)
            (And.intro (by cases k <;> rfl) (by cases k <;> rfl))))))

end OC133V12
