namespace OCMinimalObligationSpine.UnifiedEntityProjection

structure ContactRestriction (Global Local : Type) where
  restrict : Global -> Local

def ContactRestriction.comp
    (outer : ContactRestriction Global Outer)
    (inner : ContactRestriction Outer Inner) :
    ContactRestriction Global Inner :=
  { restrict := fun state => inner.restrict (outer.restrict state) }

theorem nested_contact_restriction_composes
    (outer : ContactRestriction Global Outer)
    (inner : ContactRestriction Outer Inner)
    (state : Global) :
    (outer.comp inner).restrict state = inner.restrict (outer.restrict state) := by
  rfl

structure SelfProjection (Global : Type) where
  project : Global -> Global
  idempotent : forall x, project (project x) = project x

def contactExpectation (anchor : Local) : Global × Local -> Global × Local
  | (global, _) => (global, anchor)

theorem contact_expectation_is_idempotent
    (anchor : Local) (state : Global × Local) :
    contactExpectation anchor (contactExpectation anchor state) =
      contactExpectation anchor state := by
  cases state
  rfl

inductive GHZPhase where
  | plus
  | minus
  deriving DecidableEq, Repr

def ghzAmplitude
    (phase : GHZPhase) (a b c : Bool) : Int :=
  if a = b ∧ b = c then
    if a = false then 1
    else match phase with
      | GHZPhase.plus => 1
      | GHZPhase.minus => -1
  else 0

def marginalAB
    (phase : GHZPhase) (a b a' b' : Bool) : Int :=
  ghzAmplitude phase a b false * ghzAmplitude phase a' b' false +
  ghzAmplitude phase a b true * ghzAmplitude phase a' b' true

def marginalAC
    (phase : GHZPhase) (a c a' c' : Bool) : Int :=
  ghzAmplitude phase a false c * ghzAmplitude phase a' false c' +
  ghzAmplitude phase a true c * ghzAmplitude phase a' true c'

def marginalBC
    (phase : GHZPhase) (b c b' c' : Bool) : Int :=
  ghzAmplitude phase false b c * ghzAmplitude phase false b' c' +
  ghzAmplitude phase true b c * ghzAmplitude phase true b' c'

def marginalA (phase : GHZPhase) (a a' : Bool) : Int :=
  marginalAB phase a false a' false + marginalAB phase a true a' true

def marginalB (phase : GHZPhase) (b b' : Bool) : Int :=
  marginalAB phase false b false b' + marginalAB phase true b true b'

def marginalC (phase : GHZPhase) (c c' : Bool) : Int :=
  marginalAC phase false c false c' + marginalAC phase true c true c'

structure ProperGHZMarginals where
  ab : Bool -> Bool -> Bool -> Bool -> Int
  ac : Bool -> Bool -> Bool -> Bool -> Int
  bc : Bool -> Bool -> Bool -> Bool -> Int
  a : Bool -> Bool -> Int
  b : Bool -> Bool -> Int
  c : Bool -> Bool -> Int

def properGHZMarginals (phase : GHZPhase) : ProperGHZMarginals :=
  { ab := marginalAB phase
    ac := marginalAC phase
    bc := marginalBC phase
    a := marginalA phase
    b := marginalB phase
    c := marginalC phase }

theorem proper_ghz_marginals_ext
    (left right : ProperGHZMarginals)
    (hab : left.ab = right.ab)
    (hac : left.ac = right.ac)
    (hbc : left.bc = right.bc)
    (ha : left.a = right.a)
    (hb : left.b = right.b)
    (hc : left.c = right.c) : left = right := by
  cases left
  cases right
  cases hab
  cases hac
  cases hbc
  cases ha
  cases hb
  cases hc
  rfl

theorem ghz_phases_are_distinct : GHZPhase.plus ≠ GHZPhase.minus := by
  decide

theorem all_proper_ghz_marginals_are_equal :
    properGHZMarginals GHZPhase.plus = properGHZMarginals GHZPhase.minus := by
  apply proper_ghz_marginals_ext
  · funext a b a' b'
    cases a <;> cases b <;> cases a' <;> cases b' <;> rfl
  · funext a c a' c'
    cases a <;> cases c <;> cases a' <;> cases c' <;> rfl
  · funext b c b' c'
    cases b <;> cases c <;> cases b' <;> cases c' <;> rfl
  · funext a a'
    cases a <;> cases a' <;> rfl
  · funext b b'
    cases b <;> cases b' <;> rfl
  · funext c c'
    cases c <;> cases c' <;> rfl

theorem proper_ghz_marginals_are_not_injective :
    ¬ Function.Injective properGHZMarginals := by
  intro injective
  exact ghz_phases_are_distinct (injective all_proper_ghz_marginals_are_equal)

abbrev Environment12 := Fin 12 -> Bool
abbrev Interaction12 := Bool × Environment12 -> Bool × Environment12

def zeroEnvironment : Environment12 := fun _ => false

def flipIf (pointer record : Bool) : Bool :=
  if pointer then !record else record

theorem flip_if_is_involutive (pointer record : Bool) :
    flipIf pointer (flipIf pointer record) = record := by
  cases pointer <;> cases record <;> rfl

def identityInteraction : Interaction12 := fun state => state

def fanoutInteraction : Interaction12 := fun state =>
  (state.1, fun index => flipIf state.1 (state.2 index))

def CarriesPointer (interaction : Interaction12) : Prop :=
  forall pointer index,
    (interaction (pointer, zeroEnvironment)).2 index = pointer

theorem identity_interaction_is_involutive (state : Bool × Environment12) :
    identityInteraction (identityInteraction state) = state := by
  rfl

theorem fanout_interaction_is_involutive (state : Bool × Environment12) :
    fanoutInteraction (fanoutInteraction state) = state := by
  rcases state with ⟨pointer, environment⟩
  apply Prod.ext
  · rfl
  · funext index
    exact flip_if_is_involutive pointer (environment index)

theorem identity_interaction_carries_no_pointer :
    ¬ CarriesPointer identityInteraction := by
  intro carries
  have impossible := carries true ⟨0, by decide⟩
  simp [identityInteraction, zeroEnvironment] at impossible

theorem fanout_interaction_carries_pointer :
    CarriesPointer fanoutInteraction := by
  intro pointer index
  cases pointer <;> rfl

theorem typed_identity_and_fanout_countermodels_exist :
    ∃ identity fanout : Interaction12,
      (forall state, identity (identity state) = state) ∧
      (forall state, fanout (fanout state) = state) ∧
      ¬ CarriesPointer identity ∧ CarriesPointer fanout := by
  exact ⟨identityInteraction, fanoutInteraction,
    identity_interaction_is_involutive,
    fanout_interaction_is_involutive,
    identity_interaction_carries_no_pointer,
    fanout_interaction_carries_pointer⟩

def minimalDisjointCarrierLift (contactCount carriersPerContact : Nat) : Nat :=
  contactCount * carriersPerContact

theorem three_noisy_contacts_require_twelve_declared_carriers :
    minimalDisjointCarrierLift 3 4 = 12 := by
  rfl

def contactSpot (left right : Bool) : Bool :=
  Bool.xor left right

theorem contact_spot_changes_with_each_parent (left right : Bool) :
    contactSpot (!left) right = !(contactSpot left right) ∧
      contactSpot left (!right) = !(contactSpot left right) := by
  cases left <;> cases right <;> decide

abbrev ContactRecord3 := Fin 3 -> Bool

def stableContactRecord
    (spot : Bool) : Bool × ContactRecord3 -> Bool × ContactRecord3
  | _ => (spot, fun _ => spot)

theorem stable_contact_record_is_idempotent
    (spot : Bool) (state : Bool × ContactRecord3) :
    stableContactRecord spot (stableContactRecord spot state) =
      stableContactRecord spot state := by
  cases state
  rfl

structure Ground4 where
  x0 : Bool
  x1 : Bool
  x2 : Bool
  x3 : Bool
  deriving DecidableEq, Repr

def firstOrderContacts (state : Ground4) : Bool × Bool :=
  (contactSpot state.x0 state.x1, contactSpot state.x2 state.x3)

def secondOrderContact (state : Bool × Bool) : Bool :=
  contactSpot state.1 state.2

def recursiveContact (state : Ground4) : Bool :=
  secondOrderContact (firstOrderContacts state)

theorem recursive_contact_closure (state : Ground4) :
    recursiveContact state =
      contactSpot (firstOrderContacts state).1 (firstOrderContacts state).2 := by
  rfl

def groundTransition (state : Ground4) : Ground4 :=
  { x0 := !state.x0
    x1 := state.x1
    x2 := !state.x2
    x3 := state.x3 }

def firstOrderTransition (state : Bool × Bool) : Bool × Bool :=
  (!state.1, !state.2)

def secondOrderTransition (state : Bool) : Bool :=
  state

theorem effective_view_dynamics_commute :
    (forall state : Ground4,
      firstOrderContacts (groundTransition state) =
        firstOrderTransition (firstOrderContacts state)) ∧
    (forall state : Bool × Bool,
      secondOrderContact (firstOrderTransition state) =
        secondOrderTransition (secondOrderContact state)) := by
  constructor
  · intro state
    rcases state with ⟨x0, x1, x2, x3⟩
    cases x0 <;> cases x1 <;> cases x2 <;> cases x3 <;> rfl
  · intro state
    rcases state with ⟨left, right⟩
    cases left <;> cases right <;> rfl

def contactHistory (state : Ground4) :
    Ground4 × (Bool × Bool) × Bool :=
  (state, firstOrderContacts state, recursiveContact state)

theorem contact_history_is_injective :
    Function.Injective contactHistory := by
  intro left right historiesEqual
  exact congrArg Prod.fst historiesEqual

def retainedContactNodeTotal
    (foundation firstOrder secondOrder : Nat) : Nat :=
  foundation + firstOrder + secondOrder

theorem retained_contact_graph_has_seven_nodes :
    retainedContactNodeTotal 4 2 1 = 7 := by
  rfl

def PreservesTypedReceiverEffects
    (effect : Source -> Receiver -> Effect)
    (encode : Source -> Carrier)
    (decode : Carrier -> Receiver -> Effect) : Prop :=
  forall source receiver,
    decode (encode source) receiver = effect source receiver

def causalEffectSignature
    (effect : Source -> Receiver -> Effect) (source : Source) :
    Receiver -> Effect :=
  fun receiver => effect source receiver

theorem causal_effect_signature_preserves_typed_receiver_effects
    (effect : Source -> Receiver -> Effect) :
    PreservesTypedReceiverEffects effect (causalEffectSignature effect)
      (fun signature receiver => signature receiver) := by
  intro source receiver
  rfl

theorem preserving_encoder_refines_causal_signature
    {effect : Source -> Receiver -> Effect}
    {encode : Source -> Carrier}
    {decode : Carrier -> Receiver -> Effect}
    (preserves : PreservesTypedReceiverEffects effect encode decode)
    {left right : Source}
    (sameEncoding : encode left = encode right) :
    causalEffectSignature effect left = causalEffectSignature effect right := by
  funext receiver
  calc
    effect left receiver = decode (encode left) receiver :=
      (preserves left receiver).symm
    _ = decode (encode right) receiver := by rw [sameEncoding]
    _ = effect right receiver := preserves right receiver

theorem causal_signature_factors_through_every_preserving_encoder
    {effect : Source -> Receiver -> Effect}
    {encode : Source -> Carrier}
    {decode : Carrier -> Receiver -> Effect}
    (preserves : PreservesTypedReceiverEffects effect encode decode) :
    causalEffectSignature effect =
      fun source receiver => decode (encode source) receiver := by
  funext source receiver
  exact (preserves source receiver).symm

theorem effect_distinct_collision_refutes_sufficiency
    {effect : Source -> Receiver -> Effect}
    {encode : Source -> Carrier}
    {decode : Carrier -> Receiver -> Effect}
    {left right : Source}
    (collision : encode left = encode right)
    (effectDistinct :
      causalEffectSignature effect left ≠ causalEffectSignature effect right) :
    ¬ PreservesTypedReceiverEffects effect encode decode := by
  intro preserves
  apply effectDistinct
  exact preserving_encoder_refines_causal_signature preserves collision

def IsCausallyMinimalEncoder
    (effect : Source -> Receiver -> Effect)
    (encode : Source -> Carrier) : Prop :=
  forall left right,
    causalEffectSignature effect left = causalEffectSignature effect right ->
      encode left = encode right

def EncoderKernelEquivalent
    (leftEncode : Source -> Carrier)
    (rightEncode : Source -> OtherCarrier) : Prop :=
  forall left right,
    leftEncode left = leftEncode right <->
      rightEncode left = rightEncode right

def EncoderKernelRefines
    (fineEncode : Source -> Carrier)
    (coarseEncode : Source -> OtherCarrier) : Prop :=
  forall left right,
    fineEncode left = fineEncode right ->
      coarseEncode left = coarseEncode right

/-- Every encoder kernel refines itself. -/
theorem encoderKernelRefines_refl
    (encode : Source -> Carrier) :
    EncoderKernelRefines encode encode := by
  intro left right sameEncoding
  exact sameEncoding

/-- Kernel refinement composes across carrier types. -/
theorem encoderKernelRefines_trans
    {fineEncode : Source -> Carrier}
    {middleEncode : Source -> OtherCarrier}
    {coarseEncode : Source -> Score}
    (fineMiddle : EncoderKernelRefines fineEncode middleEncode)
    (middleCoarse : EncoderKernelRefines middleEncode coarseEncode) :
    EncoderKernelRefines fineEncode coarseEncode := by
  intro left right fineCollision
  exact middleCoarse left right (fineMiddle left right fineCollision)

/--
Strict kernel refinement is the orientation of a genuine K-growth edge:
the fine encoder refines the coarse one, while the reverse refinement fails.
-/
def EncoderKernelStrictlyRefines
    (fineEncode : Source -> Carrier)
    (coarseEncode : Source -> OtherCarrier) : Prop :=
  EncoderKernelRefines fineEncode coarseEncode /\
    Not (EncoderKernelRefines coarseEncode fineEncode)

/-- No encoder strictly refines itself. -/
theorem encoderKernelStrictlyRefines_irrefl
    (encode : Source -> Carrier) :
    Not (EncoderKernelStrictlyRefines encode encode) := by
  intro strict
  exact strict.2 (encoderKernelRefines_refl encode)

/-- Strict kernel refinement is asymmetric. -/
theorem encoderKernelStrictlyRefines_asymm
    {leftEncode : Source -> Carrier}
    {rightEncode : Source -> OtherCarrier}
    (leftRight : EncoderKernelStrictlyRefines leftEncode rightEncode) :
    Not (EncoderKernelStrictlyRefines rightEncode leftEncode) := by
  intro rightLeft
  exact leftRight.2 rightLeft.1

/--
A strict refinement followed by an ordinary refinement is still strict.
Consequently a strict K-growth edge cannot be hidden by later coarsening along
the declared refinement direction.
-/
theorem encoderKernelStrictlyRefines_trans_refines
    {fineEncode : Source -> Carrier}
    {middleEncode : Source -> OtherCarrier}
    {coarseEncode : Source -> Score}
    (fineMiddle : EncoderKernelStrictlyRefines fineEncode middleEncode)
    (middleCoarse : EncoderKernelRefines middleEncode coarseEncode) :
    EncoderKernelStrictlyRefines fineEncode coarseEncode := by
  constructor
  · exact encoderKernelRefines_trans fineMiddle.1 middleCoarse
  · intro coarseFine
    exact fineMiddle.2
      (encoderKernelRefines_trans middleCoarse coarseFine)

/--
An ordinary refinement followed by a strict refinement is strict.  Together
with the previous theorem this makes every finite chain containing a strict
edge acyclic at its endpoints.
-/
theorem encoderKernelRefines_trans_strictlyRefines
    {fineEncode : Source -> Carrier}
    {middleEncode : Source -> OtherCarrier}
    {coarseEncode : Source -> Score}
    (fineMiddle : EncoderKernelRefines fineEncode middleEncode)
    (middleCoarse : EncoderKernelStrictlyRefines middleEncode coarseEncode) :
    EncoderKernelStrictlyRefines fineEncode coarseEncode := by
  constructor
  · exact encoderKernelRefines_trans fineMiddle middleCoarse.1
  · intro coarseFine
    exact middleCoarse.2
      (encoderKernelRefines_trans coarseFine fineMiddle)

def IsKernelCoarsestAdmissible
    (admissible : forall C : Type, (Source -> C) -> Prop)
    (encode : Source -> Carrier) : Prop :=
  admissible Carrier encode /\
    forall (C : Type) (otherEncode : Source -> C),
      admissible C otherEncode -> EncoderKernelRefines otherEncode encode

theorem coarsest_admissible_encoders_are_kernel_equivalent
    {admissible : forall C : Type, (Source -> C) -> Prop}
    {leftEncode : Source -> Carrier}
    {rightEncode : Source -> OtherCarrier}
    (leftCoarsest : IsKernelCoarsestAdmissible admissible leftEncode)
    (rightCoarsest : IsKernelCoarsestAdmissible admissible rightEncode) :
    EncoderKernelEquivalent leftEncode rightEncode := by
  intro left right
  constructor
  · exact rightCoarsest.2 Carrier leftEncode leftCoarsest.1 left right
  · exact leftCoarsest.2 OtherCarrier rightEncode rightCoarsest.1 left right

def evolveState
    (transition : Source -> Source) : Nat -> Source -> Source
  | 0, source => source
  | Nat.succ step, source => transition (evolveState transition step source)

def causalTrajectorySignature
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source)
    (source : Source) : Nat -> Receiver -> Effect :=
  fun step => causalEffectSignature effect (evolveState transition step source)

def PreservesTypedDeterministicDynamics
    (transition : Source -> Source)
    (encode : Source -> Carrier)
    (encodedTransition : Carrier -> Carrier) : Prop :=
  forall source,
    encode (transition source) = encodedTransition (encode source)

theorem encoding_collision_persists_under_closed_dynamics
    {transition : Source -> Source}
    {encode : Source -> Carrier}
    {encodedTransition : Carrier -> Carrier}
    (closedDynamics :
      PreservesTypedDeterministicDynamics transition encode encodedTransition)
    {left right : Source}
    (collision : encode left = encode right) :
    forall step,
      encode (evolveState transition step left) =
        encode (evolveState transition step right) := by
  intro step
  induction step with
  | zero => exact collision
  | succ previous ih =>
      calc
        encode (evolveState transition (Nat.succ previous) left) =
            encodedTransition
              (encode (evolveState transition previous left)) :=
          closedDynamics (evolveState transition previous left)
        _ = encodedTransition
              (encode (evolveState transition previous right)) := by rw [ih]
        _ = encode (evolveState transition (Nat.succ previous) right) :=
          (closedDynamics (evolveState transition previous right)).symm

theorem exact_causal_dynamic_encoder_refines_trajectory_signature
    {effect : Source -> Receiver -> Effect}
    {transition : Source -> Source}
    {encode : Source -> Carrier}
    {decode : Carrier -> Receiver -> Effect}
    {encodedTransition : Carrier -> Carrier}
    (preservesEffects : PreservesTypedReceiverEffects effect encode decode)
    (closedDynamics :
      PreservesTypedDeterministicDynamics transition encode encodedTransition)
    {left right : Source}
    (collision : encode left = encode right) :
    causalTrajectorySignature effect transition left =
      causalTrajectorySignature effect transition right := by
  funext step receiver
  have evolvedCollision :=
    encoding_collision_persists_under_closed_dynamics closedDynamics collision step
  exact congrFun
    (preserving_encoder_refines_causal_signature preservesEffects evolvedCollision)
    receiver

theorem evolve_state_after_transition
    (transition : Source -> Source) (step : Nat) (source : Source) :
    evolveState transition step (transition source) =
      evolveState transition (Nat.succ step) source := by
  induction step with
  | zero => rfl
  | succ previous ih =>
      change
        transition (evolveState transition previous (transition source)) =
          transition (evolveState transition (Nat.succ previous) source)
      exact congrArg transition ih

def shiftCausalTrajectory
    (trajectory : Nat -> Receiver -> Effect) : Nat -> Receiver -> Effect :=
  fun step => trajectory (Nat.succ step)

theorem causal_trajectory_signature_preserves_receiver_effects
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    PreservesTypedReceiverEffects effect
      (causalTrajectorySignature effect transition)
      (fun trajectory receiver => trajectory 0 receiver) := by
  intro source receiver
  rfl

theorem causal_trajectory_signature_has_closed_dynamics
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    PreservesTypedDeterministicDynamics transition
      (causalTrajectorySignature effect transition)
      shiftCausalTrajectory := by
  intro source
  funext step receiver
  simp only [causalTrajectorySignature, shiftCausalTrajectory]
  rw [evolve_state_after_transition]

def IsCausalDynamicallyMinimalEncoder
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source)
    (encode : Source -> Carrier) : Prop :=
  forall left right,
    causalTrajectorySignature effect transition left =
      causalTrajectorySignature effect transition right ->
        encode left = encode right

theorem exact_minimal_causal_dynamic_encoder_has_trajectory_kernel
    {effect : Source -> Receiver -> Effect}
    {transition : Source -> Source}
    {encode : Source -> Carrier}
    {decode : Carrier -> Receiver -> Effect}
    {encodedTransition : Carrier -> Carrier}
    (preservesEffects : PreservesTypedReceiverEffects effect encode decode)
    (closedDynamics :
      PreservesTypedDeterministicDynamics transition encode encodedTransition)
    (minimal : IsCausalDynamicallyMinimalEncoder effect transition encode) :
    EncoderKernelEquivalent encode
      (causalTrajectorySignature effect transition) := by
  intro left right
  constructor
  · exact exact_causal_dynamic_encoder_refines_trajectory_signature
      preservesEffects closedDynamics
  · exact minimal left right

/--
Observer/description invariance of the dynamic K-kernel under the exact
minimality contract.

Two encoders may use different carrier types and labels.  If both preserve the
same typed receiver effects, close the same deterministic dynamics, and are
minimal for the complete causal-trajectory signature, then they identify
exactly the same pairs of source states.  Thus the induced K-partition is
representation-invariant inside this admissible observer class.
-/
theorem exact_minimal_causal_dynamic_encoders_are_kernel_equivalent
    {effect : Source -> Receiver -> Effect}
    {transition : Source -> Source}
    {leftEncode : Source -> Carrier}
    {leftDecode : Carrier -> Receiver -> Effect}
    {leftEncodedTransition : Carrier -> Carrier}
    {rightEncode : Source -> OtherCarrier}
    {rightDecode : OtherCarrier -> Receiver -> Effect}
    {rightEncodedTransition : OtherCarrier -> OtherCarrier}
    (leftPreservesEffects :
      PreservesTypedReceiverEffects effect leftEncode leftDecode)
    (leftClosedDynamics :
      PreservesTypedDeterministicDynamics transition leftEncode
        leftEncodedTransition)
    (leftMinimal :
      IsCausalDynamicallyMinimalEncoder effect transition leftEncode)
    (rightPreservesEffects :
      PreservesTypedReceiverEffects effect rightEncode rightDecode)
    (rightClosedDynamics :
      PreservesTypedDeterministicDynamics transition rightEncode
        rightEncodedTransition)
    (rightMinimal :
      IsCausalDynamicallyMinimalEncoder effect transition rightEncode) :
    EncoderKernelEquivalent leftEncode rightEncode := by
  intro left right
  constructor
  · intro sameLeftEncoding
    exact rightMinimal left right
      (exact_causal_dynamic_encoder_refines_trajectory_signature
        leftPreservesEffects leftClosedDynamics sameLeftEncoding)
  · intro sameRightEncoding
    exact leftMinimal left right
      (exact_causal_dynamic_encoder_refines_trajectory_signature
        rightPreservesEffects rightClosedDynamics sameRightEncoding)

theorem trajectory_distinct_collision_refutes_exact_causal_dynamics
    {effect : Source -> Receiver -> Effect}
    {transition : Source -> Source}
    {encode : Source -> Carrier}
    {left right : Source}
    (collision : encode left = encode right)
    (trajectoryDistinct :
      causalTrajectorySignature effect transition left ≠
        causalTrajectorySignature effect transition right) :
    ¬ (∃ decode : Carrier -> Receiver -> Effect,
      ∃ encodedTransition : Carrier -> Carrier,
        PreservesTypedReceiverEffects effect encode decode /\
          PreservesTypedDeterministicDynamics transition encode encodedTransition) := by
  intro exactRealization
  rcases exactRealization with
    ⟨decode, encodedTransition, preservesEffects, closedDynamics⟩
  apply trajectoryDistinct
  exact exact_causal_dynamic_encoder_refines_trajectory_signature
    preservesEffects closedDynamics collision

def PreservesTypedProcessLaws
    (processLaw : Source -> Experiment -> Law)
    (encode : Source -> Carrier)
    (decode : Carrier -> Experiment -> Law) : Prop :=
  forall source experiment,
    decode (encode source) experiment = processLaw source experiment

def processLawSignature
    (processLaw : Source -> Experiment -> Law) (source : Source) :
    Experiment -> Law :=
  fun experiment => processLaw source experiment

theorem process_law_signature_preserves_typed_process_laws
    (processLaw : Source -> Experiment -> Law) :
    PreservesTypedProcessLaws processLaw (processLawSignature processLaw)
      (fun signature experiment => signature experiment) := by
  intro source experiment
  rfl

theorem preserving_process_law_encoder_refines_signature
    {processLaw : Source -> Experiment -> Law}
    {encode : Source -> Carrier}
    {decode : Carrier -> Experiment -> Law}
    (preserves : PreservesTypedProcessLaws processLaw encode decode)
    {left right : Source}
    (sameEncoding : encode left = encode right) :
    processLawSignature processLaw left =
      processLawSignature processLaw right := by
  funext experiment
  calc
    processLaw left experiment = decode (encode left) experiment :=
      (preserves left experiment).symm
    _ = decode (encode right) experiment := by rw [sameEncoding]
    _ = processLaw right experiment := preserves right experiment

theorem process_law_signature_factors_through_every_preserving_encoder
    {processLaw : Source -> Experiment -> Law}
    {encode : Source -> Carrier}
    {decode : Carrier -> Experiment -> Law}
    (preserves : PreservesTypedProcessLaws processLaw encode decode) :
    processLawSignature processLaw =
      fun source experiment => decode (encode source) experiment := by
  funext source experiment
  exact (preserves source experiment).symm

def IsProcessLawMinimalEncoder
    (processLaw : Source -> Experiment -> Law)
    (encode : Source -> Carrier) : Prop :=
  forall left right,
    processLawSignature processLaw left =
      processLawSignature processLaw right ->
        encode left = encode right

theorem exact_minimal_process_law_encoder_has_signature_kernel
    {processLaw : Source -> Experiment -> Law}
    {encode : Source -> Carrier}
    {decode : Carrier -> Experiment -> Law}
    (preserves : PreservesTypedProcessLaws processLaw encode decode)
    (minimal : IsProcessLawMinimalEncoder processLaw encode) :
    EncoderKernelEquivalent encode (processLawSignature processLaw) := by
  intro left right
  constructor
  · exact preserving_process_law_encoder_refines_signature preserves
  · exact minimal left right

theorem process_law_distinct_collision_refutes_exact_prediction
    {processLaw : Source -> Experiment -> Law}
    {encode : Source -> Carrier}
    {left right : Source}
    (collision : encode left = encode right)
    (lawDistinct :
      processLawSignature processLaw left ≠
        processLawSignature processLaw right) :
    ¬ (∃ decode : Carrier -> Experiment -> Law,
      PreservesTypedProcessLaws processLaw encode decode) := by
  intro realization
  rcases realization with ⟨decode, preserves⟩
  apply lawDistinct
  exact preserving_process_law_encoder_refines_signature preserves collision

def CanonicalScoreSeparatesCandidates
    (score : Candidate -> Score) : Prop :=
  Function.Injective score

theorem canonical_score_tie_identifies_one_candidate
    {score : Candidate -> Score}
    (separates : CanonicalScoreSeparatesCandidates score)
    {left right : Candidate}
    (sameScore : score left = score right) :
    left = right := by
  exact separates sameScore

theorem exact_minimal_causal_encoder_has_causal_signature_kernel
    {effect : Source -> Receiver -> Effect}
    {encode : Source -> Carrier}
    {decode : Carrier -> Receiver -> Effect}
    (preserves : PreservesTypedReceiverEffects effect encode decode)
    (minimal : IsCausallyMinimalEncoder effect encode) :
    EncoderKernelEquivalent encode (causalEffectSignature effect) := by
  intro left right
  constructor
  · exact preserving_encoder_refines_causal_signature preserves
  · exact minimal left right

theorem exact_minimal_causal_encoders_are_kernel_equivalent
    {effect : Source -> Receiver -> Effect}
    {leftEncode : Source -> Carrier}
    {leftDecode : Carrier -> Receiver -> Effect}
    {rightEncode : Source -> OtherCarrier}
    {rightDecode : OtherCarrier -> Receiver -> Effect}
    (leftPreserves :
      PreservesTypedReceiverEffects effect leftEncode leftDecode)
    (leftMinimal : IsCausallyMinimalEncoder effect leftEncode)
    (rightPreserves :
      PreservesTypedReceiverEffects effect rightEncode rightDecode)
    (rightMinimal : IsCausallyMinimalEncoder effect rightEncode) :
    EncoderKernelEquivalent leftEncode rightEncode := by
  intro left right
  constructor
  · intro sameLeft
    exact rightMinimal left right
      (preserving_encoder_refines_causal_signature leftPreserves sameLeft)
  · intro sameRight
    exact leftMinimal left right
      (preserving_encoder_refines_causal_signature rightPreserves sameRight)

abbrev CausalSource := Bool × Bool

def receiverEffect (source : CausalSource) (receiver : Bool) : Bool :=
  if receiver then source.2 else source.1

def PreservesReceiverEffects {Carrier : Type}
    (encode : CausalSource -> Carrier)
    (decode : Carrier -> Bool -> Bool) : Prop :=
  forall source receiver,
    decode (encode source) receiver = receiverEffect source receiver

def causalSignature (source : CausalSource) : CausalSource :=
  (receiverEffect source false, receiverEffect source true)

theorem causal_signature_is_identity (source : CausalSource) :
    causalSignature source = source := by
  cases source
  rfl

def complementedCausalEncoding (source : CausalSource) : CausalSource :=
  (!source.1, !source.2)

def complementedCausalDecoder
    (encoded : CausalSource) (receiver : Bool) : Bool :=
  if receiver then !encoded.2 else !encoded.1

theorem complemented_causal_encoding_preserves_receiver_effects :
    PreservesReceiverEffects complementedCausalEncoding
      complementedCausalDecoder := by
  intro source receiver
  rcases source with ⟨left, right⟩
  cases left <;> cases right <;> cases receiver <;> rfl

theorem complemented_causal_encoding_is_minimal :
    IsCausallyMinimalEncoder receiverEffect complementedCausalEncoding := by
  intro left right sameEffects
  have sameLeft := congrFun sameEffects false
  have sameRight := congrFun sameEffects true
  rcases left with ⟨leftFirst, leftSecond⟩
  rcases right with ⟨rightFirst, rightSecond⟩
  simp [causalEffectSignature, receiverEffect] at sameLeft sameRight
  simp [complementedCausalEncoding, sameLeft, sameRight]

theorem literal_minimal_causal_encoder_uniqueness_is_false :
    causalSignature ≠ complementedCausalEncoding := by
  intro sameEncoder
  have falseCase := congrFun sameEncoder (false, false)
  simp [causalSignature, receiverEffect, complementedCausalEncoding] at falseCase

theorem causal_signature_preserves_receiver_effects :
    PreservesReceiverEffects causalSignature receiverEffect := by
  intro source receiver
  cases source
  cases receiver <;> rfl

theorem no_one_bit_carrier_preserves_all_receiver_effects :
    ¬ ∃ encode : CausalSource -> Bool,
      ∃ decode : Bool -> Bool -> Bool,
        PreservesReceiverEffects encode decode := by
  rintro ⟨encode, decode, preserves⟩
  have h00f := preserves (false, false) false
  have h00t := preserves (false, false) true
  have h01f := preserves (false, true) false
  have h01t := preserves (false, true) true
  have h10f := preserves (true, false) false
  have h10t := preserves (true, false) true
  have h11f := preserves (true, true) false
  have h11t := preserves (true, true) true
  cases e00 : encode (false, false) <;>
    cases e01 : encode (false, true) <;>
    cases e10 : encode (true, false) <;>
    cases e11 : encode (true, true) <;>
    simp_all [receiverEffect]

def HasAvailableLift
    (admissible : forall C : Type, (Source -> C) -> Prop) : Prop :=
  Exists fun C : Type =>
    Exists fun encode : Source -> C => admissible C encode

theorem realized_admissible_lift_requires_available_witness
    {admissible : forall C : Type, (Source -> C) -> Prop}
    {encode : Source -> Carrier}
    (isAdmissible : admissible Carrier encode) :
    HasAvailableLift admissible := by
  exact ⟨Carrier, encode, isAdmissible⟩

theorem no_available_lift_rules_out_admissible_realization
    {admissible : forall C : Type, (Source -> C) -> Prop}
    (unavailable : Not (HasAvailableLift admissible)) :
    forall (C : Type) (encode : Source -> C),
      Not (admissible C encode) := by
  intro C encode isAdmissible
  exact unavailable ⟨C, encode, isAdmissible⟩

theorem expressivity_failure_from_trajectory_collision
    {effect : Source -> Receiver -> Effect}
    {transition : Source -> Source}
    {encode : Source -> Carrier}
    {left right : Source}
    (collision : encode left = encode right)
    (trajectoryDistinct :
      Not (causalTrajectorySignature effect transition left =
        causalTrajectorySignature effect transition right)) :
    Not (Exists fun decode : Carrier -> Receiver -> Effect =>
      Exists fun encodedTransition : Carrier -> Carrier =>
        PreservesTypedReceiverEffects effect encode decode /\
          PreservesTypedDeterministicDynamics transition encode
            encodedTransition) := by
  exact trajectory_distinct_collision_refutes_exact_causal_dynamics
    collision trajectoryDistinct

def BoundedExactContinuation
    (sameCarrierRepair availableLift : Prop) : Prop :=
  sameCarrierRepair \/ availableLift

def BoundedRepresentationalCollapse
    (sameCarrierRepair availableLift : Prop) : Prop :=
  Not (BoundedExactContinuation sameCarrierRepair availableLift)

theorem no_repair_and_no_lift_force_bounded_representational_collapse
    {sameCarrierRepair availableLift : Prop}
    (noRepair : Not sameCarrierRepair)
    (noLift : Not availableLift) :
    BoundedRepresentationalCollapse sameCarrierRepair availableLift := by
  intro continuation
  exact continuation.elim noRepair noLift

structure CollapseResidueCertificate
    (sameCarrierRepair availableLift residueRetained : Prop) : Prop where
  boundedCollapse :
    BoundedRepresentationalCollapse sameCarrierRepair availableLift
  residue : residueRetained

theorem bounded_collapse_retains_declared_residue
    {sameCarrierRepair availableLift residueRetained : Prop}
    (noRepair : Not sameCarrierRepair)
    (noLift : Not availableLift)
    (retained : residueRetained) :
    CollapseResidueCertificate sameCarrierRepair availableLift
      residueRetained := by
  exact ⟨
    no_repair_and_no_lift_force_bounded_representational_collapse
      noRepair noLift,
    retained
  ⟩

def exactRecordComultiplication
    (fragmentTotal : Nat) (value : RecordValue) :
    Fin fragmentTotal -> RecordValue :=
  fun _ => value

theorem exact_record_fragment_recovers
    (fragmentTotal : Nat) (value : RecordValue)
    (fragment : Fin fragmentTotal) :
    exactRecordComultiplication fragmentTotal value fragment = value := by
  rfl

theorem exact_recoverability_forces_record_comultiplication
    (fragmentTotal : Nat)
    (candidate : RecordValue -> Fin fragmentTotal -> RecordValue)
    (recovers : forall value fragment, candidate value fragment = value) :
    candidate = exactRecordComultiplication fragmentTotal := by
  funext value fragment
  exact recovers value fragment

def binaryNextGeneration (active : Nat) : Nat :=
  active + active

theorem binary_generation_equation (active : Nat) :
    binaryNextGeneration active = 2 * active := by
  simp [binaryNextGeneration, Nat.two_mul]

theorem binary_generation_strict_growth
    (active : Nat) (positive : 0 < active) :
    active < binaryNextGeneration active := by
  exact Nat.lt_add_of_pos_right (n := active) positive

def resourceRemaining (budget consumed : Nat) : Nat :=
  budget - consumed

theorem finite_resource_balance
    (budget consumed : Nat) (admissible : consumed <= budget) :
    resourceRemaining budget consumed + consumed = budget := by
  exact Nat.sub_add_cancel admissible

end OCMinimalObligationSpine.UnifiedEntityProjection
