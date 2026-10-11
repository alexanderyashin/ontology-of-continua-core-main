import OCMinimalObligationSpine.CurrentK
import OCKIndividuationMSpaceComposition.LevelClassification
import OCKIndividuationMSpaceComposition.DynamicObjectIdentity

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine
open OCMinimalObligationSpine.UnifiedEntityProjection
open OCMaturityCompletionCycle

universe
  uState uCandidate
  uMechanism uIntervention uOutcome uProvenance uTime
  uMemberOccurrence uMemberExperiment uMemberOutcome
  uObjectOccurrence uInput uObjectExperiment uObjectOutcome

/-!
# A context-relative K axis and the finite-horizon `CurrentK` bridge

This module isolates the part of the historical K language that survives the
current synthesis.  A K coordinate records *which pairwise distinctions a
specified context can make*.  More discriminating profiles are ordered by
inclusion of their distinctions.  A domain-supplied resolution step then
induces strongly connected level classes through the already accepted
`DerivedLevel` construction.

This is deliberately not an object ontology.  In particular, a `CurrentK` is
still a representation, and its finite-horizon profile below neither creates
an object token nor identifies compositional depth, time scale, or autonomy.
Those bridges require separate typed evidence.

`DynamicQualifiedObject.experimentLaw` must likewise be read as the declared
token-invariant identity-test semantics used by `identityConverges`, not as an
arbitrary instantaneous state measurement.  Instantaneous state observations
belong to `CurrentK` receiver effects or other explicit projections.  The
countermodel below makes this separation load-bearing: one token can change its
K-observable state even while the declared identity tests remain invariant.
-/

/-! ## Distinction profiles and their exact order -/

/-- The pairwise distinctions made available by one specified context. -/
abbrev DistinctionProfile (State : Type uState) := State → State → Prop

/-- `strong` is at least as discriminating as `weak` when it retains every
distinction made by `weak`. -/
def AtLeastAsDiscriminating
    {State : Type uState}
    (strong weak : DistinctionProfile State) : Prop :=
  ∀ ⦃left right⦄, weak left right → strong left right

theorem atLeastAsDiscriminating_refl
    {State : Type uState}
    (profile : DistinctionProfile State) :
    AtLeastAsDiscriminating profile profile := by
  intro left right distinguished
  exact distinguished

theorem atLeastAsDiscriminating_trans
    {State : Type uState}
    {first second third : DistinctionProfile State}
    (firstSecond : AtLeastAsDiscriminating first second)
    (secondThird : AtLeastAsDiscriminating second third) :
    AtLeastAsDiscriminating first third := by
  intro left right distinguished
  exact firstSecond (secondThird distinguished)

/-- Mutual discrimination inclusion is extensional equality, so the profile
order is antisymmetric rather than merely a preorder. -/
theorem atLeastAsDiscriminating_antisymm
    {State : Type uState}
    {first second : DistinctionProfile State}
    (firstSecond : AtLeastAsDiscriminating first second)
    (secondFirst : AtLeastAsDiscriminating second first) :
    first = second := by
  funext left right
  apply propext
  constructor
  · intro distinguished
    exact secondFirst distinguished
  · intro distinguished
    exact firstSecond distinguished

/-- The three order laws for context-relative distinction profiles. -/
theorem distinctionProfile_order_laws
    {State : Type uState} :
    (∀ profile : DistinctionProfile State,
      AtLeastAsDiscriminating profile profile) ∧
    (∀ first second third : DistinctionProfile State,
      AtLeastAsDiscriminating first second →
      AtLeastAsDiscriminating second third →
      AtLeastAsDiscriminating first third) ∧
    (∀ first second : DistinctionProfile State,
      AtLeastAsDiscriminating first second →
      AtLeastAsDiscriminating second first →
      first = second) :=
  ⟨atLeastAsDiscriminating_refl,
    fun _ _ _ => atLeastAsDiscriminating_trans,
    fun _ _ => atLeastAsDiscriminating_antisymm⟩

/-! ## Context-supplied resolution and SCC-derived K levels -/

/--
A scientific context supplies candidate descriptions, their distinction
profiles, and the admissible one-step increase in resolution.  Sound steps may
only add distinctions.  Nothing requires every pair of candidates to be
comparable.
-/
structure KResolutionContext (State : Type uState) where
  Candidate : Type uCandidate
  profile : Candidate → DistinctionProfile State
  ResolutionStep : Candidate → Candidate → Prop
  resolutionStep_sound : ∀ ⦃source target⦄,
    ResolutionStep source target →
      AtLeastAsDiscriminating (profile target) (profile source)

namespace KResolutionContext

variable {State : Type uState}
variable (context : KResolutionContext State)

/-- Every finite resolution path monotonically retains its source profile. -/
theorem reachable_atLeastAsDiscriminating
    {source target : context.Candidate}
    (path : RelationReachable context.ResolutionStep source target) :
    AtLeastAsDiscriminating (context.profile target)
      (context.profile source) := by
  induction path with
  | root => exact atLeastAsDiscriminating_refl _
  | tail previous edge inductionHypothesis =>
      exact atLeastAsDiscriminating_trans
        (context.resolutionStep_sound edge) inductionHypothesis

/-- Mutually reachable candidates have exactly the same distinction profile. -/
theorem profile_eq_of_mutuallyReachable
    {first second : context.Candidate}
    (sameLevel : MutuallyReachable context.ResolutionStep first second) :
    context.profile first = context.profile second := by
  apply atLeastAsDiscriminating_antisymm
  · exact context.reachable_atLeastAsDiscriminating sameLevel.2
  · exact context.reachable_atLeastAsDiscriminating sameLevel.1

/-- The K levels derived in this context are the SCC classes of its resolution
step, not positions in a universal fixed ladder. -/
abbrev ContextDerivedKLevel := DerivedLevel context.ResolutionStep

/-- Send a candidate description to its context-derived K level. -/
def contextDerivedKLevel
    (candidate : context.Candidate) : context.ContextDerivedKLevel :=
  derivedLevel context.ResolutionStep candidate

theorem contextDerivedKLevel_eq_of_mutuallyReachable
    {first second : context.Candidate}
    (sameLevel : MutuallyReachable context.ResolutionStep first second) :
    context.contextDerivedKLevel first =
      context.contextDerivedKLevel second :=
  derivedLevel_eq_of_mutuallyReachable sameLevel

/--
A finite K label atlas is exact precisely when it covers every derived SCC and
does not assign two indices to one SCC.  Thus labels such as `K0`–`K12` become
an exact coordinate system only after this context-relative criterion is
proved.
-/
theorem resolutionAtlasExact_iff
    {n : Nat}
    (atlas : FiniteLevelAtlas context.Candidate n) :
    AtlasExact context.ResolutionStep atlas ↔
      AtlasExhaustive context.ResolutionStep atlas ∧
      ∀ first second,
        context.contextDerivedKLevel (atlas first) =
          context.contextDerivedKLevel (atlas second) →
        first = second := by
  simpa [contextDerivedKLevel] using
    atlasExact_iff_exhaustive_and_no_duplicate_levels
      context.ResolutionStep atlas

end KResolutionContext

/-! ## The canonical K-resolution relation induced by discrimination itself -/

/--
When no narrower domain dynamics is intended, the profile order supplies the
canonical resolution step: a target is a one-step refinement of a source
exactly when it retains every distinction of the source.  The more general
`KResolutionContext` above remains available when a domain admits only a typed
subrelation of these information-preserving moves.
-/
def canonicalKResolutionContext
    {State : Type uState}
    {Candidate : Type uCandidate}
    (profile : Candidate → DistinctionProfile State) :
    KResolutionContext State where
  Candidate := Candidate
  profile := profile
  ResolutionStep := fun source target =>
    AtLeastAsDiscriminating (profile target) (profile source)
  resolutionStep_sound := by
    intro source target refinement
    exact refinement

/-- Canonical finite reachability is exactly discrimination refinement; no
additional arbitrary reachability structure is introduced. -/
theorem canonicalKResolution_reachable_iff_atLeastAsDiscriminating
    {State : Type uState}
    {Candidate : Type uCandidate}
    (profile : Candidate → DistinctionProfile State)
    (source target : Candidate) :
    RelationReachable
        (canonicalKResolutionContext profile).ResolutionStep source target ↔
      AtLeastAsDiscriminating (profile target) (profile source) := by
  constructor
  · intro reachable
    exact (canonicalKResolutionContext profile)
      |>.reachable_atLeastAsDiscriminating reachable
  · intro refinement
    exact .tail .root refinement

/-- Canonical mutual reachability identifies exactly equal distinction
profiles.  Hence the SCC level classes differ for a reason fixed by the
context's discriminations, not by an independently chosen scalar ladder. -/
theorem canonicalKResolution_mutuallyReachable_iff_profile_eq
    {State : Type uState}
    {Candidate : Type uCandidate}
    (profile : Candidate → DistinctionProfile State)
    (first second : Candidate) :
    MutuallyReachable
        (canonicalKResolutionContext profile).ResolutionStep first second ↔
      profile first = profile second := by
  constructor
  · intro sameLevel
    exact (canonicalKResolutionContext profile)
      |>.profile_eq_of_mutuallyReachable sameLevel
  · intro equalProfiles
    constructor
    · apply (canonicalKResolution_reachable_iff_atLeastAsDiscriminating
        profile first second).2
      simpa [equalProfiles] using
        atLeastAsDiscriminating_refl (profile first)
    · apply (canonicalKResolution_reachable_iff_atLeastAsDiscriminating
        profile second first).2
      simpa [equalProfiles] using
        atLeastAsDiscriminating_refl (profile first)

/-! ## The finite-horizon profile carried by a `CurrentK` -/

/-- Two states are distinguished up to `horizon` when some declared receiver
has unequal effects at some step no later than that horizon. -/
def currentKFiniteHorizonProfile
    (K : CurrentK)
    (horizon : Nat) : DistinctionProfile K.State :=
  fun left right =>
    ∃ step, step ≤ horizon ∧
      ∃ receiver,
        K.receiverEffect (evolveState K.stateTransition step left) receiver ≠
          K.receiverEffect (evolveState K.stateTransition step right) receiver

/-- Increasing the horizon can add distinctions but cannot remove old ones. -/
theorem currentKFiniteHorizonProfile_monotone
    (K : CurrentK)
    {short long : Nat}
    (horizonLe : short ≤ long) :
    AtLeastAsDiscriminating
      (currentKFiniteHorizonProfile K long)
      (currentKFiniteHorizonProfile K short) := by
  intro left right distinguished
  rcases distinguished with ⟨step, stepLe, receiver, effectNe⟩
  exact ⟨step, stepLe.trans horizonLe, receiver, effectNe⟩

/-- The distinctions made directly by the declared carrier encoding. -/
def currentKEncodingProfile (K : CurrentK) : DistinctionProfile K.State :=
  fun left right => K.encode left ≠ K.encode right

/-- Exact declared semantics forces the carrier encoding to retain every
finite-horizon receiver-effect distinction. -/
theorem exactCurrentKEncoding_atLeast_finiteHorizon
    (K : CurrentK)
    (exact : HasExactDeclaredSemantics K)
    (horizon : Nat) :
    AtLeastAsDiscriminating (currentKEncodingProfile K)
      (currentKFiniteHorizonProfile K horizon) := by
  intro left right distinguished
  rcases distinguished with ⟨step, stepLe, receiver, effectNe⟩
  let distinction : TrajectoryDistinction K :=
    { left := left
      right := right
      step := step
      receiver := receiver
      effect_ne := effectNe }
  exact exact_declared_semantics_expresses K exact distinction

/-! ## An explicit bridge from whole-object occurrences to a `CurrentK`

No field of `CurrentK` says which changing object it represents.  The following
record is therefore additional typed evidence, not a construction obtained
from exact representational semantics alone.
-/

/--
Evidence that one exact `CurrentK` describes the whole-object occurrence
dynamics of `object`.  `stateOf` need not be injective: two occurrences in one
or different operational tokens may legitimately have the same represented
state.  No token relation is inferred from raw K-state trajectories.
-/
structure CurrentKObjectBridge
    {Mechanism : Type uMechanism}
    {Intervention : Type uIntervention}
    {Outcome : Type uOutcome}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {Provenance : Type uProvenance}
    {Time : Type uTime}
    {formedBy : Mechanism → Provenance → Prop}
    {continuesAt : Mechanism → Time → Prop}
    {robustAtScale : (Mechanism → Prop) → Prop}
    {MemberOccurrence : Type uMemberOccurrence}
    {MemberExperiment : Type uMemberExperiment}
    {MemberOutcome : Type uMemberOutcome}
    {memberEvidence : BinaryRelation MemberOccurrence}
    {memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome}
    {ObjectOccurrence : Type uObjectOccurrence}
    {Input : Type uInput}
    {ObjectExperiment : Type uObjectExperiment}
    {ObjectOutcome : Type uObjectOutcome}
    (object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
      robustAtScale MemberOccurrence MemberExperiment MemberOutcome
      memberEvidence memberLaw ObjectOccurrence Input ObjectExperiment
      ObjectOutcome)
    (K : CurrentK) where
  stateOf : ObjectOccurrence → K.State
  exactK : HasExactDeclaredSemantics K
  step_commutes : ∀ {source input target},
    object.openStep source input target →
      K.stateTransition (stateOf source) = stateOf target

namespace CurrentKObjectBridge

variable
  {Mechanism : Type uMechanism}
  {Intervention : Type uIntervention}
  {Outcome : Type uOutcome}
  {model : ActiveConstraintModel Mechanism Intervention Outcome}
  {Provenance : Type uProvenance}
  {Time : Type uTime}
  {formedBy : Mechanism → Provenance → Prop}
  {continuesAt : Mechanism → Time → Prop}
  {robustAtScale : (Mechanism → Prop) → Prop}
  {MemberOccurrence : Type uMemberOccurrence}
  {MemberExperiment : Type uMemberExperiment}
  {MemberOutcome : Type uMemberOutcome}
  {memberEvidence : BinaryRelation MemberOccurrence}
  {memberLaw : MemberOccurrence → MemberExperiment → MemberOutcome}
  {ObjectOccurrence : Type uObjectOccurrence}
  {Input : Type uInput}
  {ObjectExperiment : Type uObjectExperiment}
  {ObjectOutcome : Type uObjectOutcome}
  {object : DynamicQualifiedObject model Provenance Time formedBy continuesAt
    robustAtScale MemberOccurrence MemberExperiment MemberOutcome memberEvidence
    memberLaw ObjectOccurrence Input ObjectExperiment ObjectOutcome}
  {K : CurrentK}

/-- Equality under every declared receiver at every represented time. -/
def KTrajectoryEquivalent
    (bridge : CurrentKObjectBridge object K)
    (first second : ObjectOccurrence) : Prop :=
  ∀ step receiver,
    K.receiverEffect
        (evolveState K.stateTransition step (bridge.stateOf first)) receiver =
      K.receiverEffect
        (evolveState K.stateTransition step (bridge.stateOf second)) receiver

/-- Optional synchronization contract: the chosen K view is invariant across
whole-object occurrences declared to belong to one operational token.  This is
not a field of the base bridge because a changing token need not satisfy it. -/
def TokenObservationInvariant
    (bridge : CurrentKObjectBridge object K) : Prop :=
  ∀ ⦃first second⦄, object.SameToken first second →
    bridge.KTrajectoryEquivalent first second

/-- Optional observational completeness contract in the reverse direction. -/
def KSeparatesTokens
    (bridge : CurrentKObjectBridge object K) : Prop :=
  ∀ ⦃first second⦄, bridge.KTrajectoryEquivalent first second →
    object.SameToken first second

theorem sameToken_implies_KTrajectoryEquivalent_of_invariant
    (bridge : CurrentKObjectBridge object K)
    (invariant : bridge.TokenObservationInvariant)
    {first second : ObjectOccurrence}
    (sameToken : object.SameToken first second) :
    bridge.KTrajectoryEquivalent first second :=
  invariant sameToken

/-- Token identity and K-trajectory equivalence coincide only when both
independent synchronization and separation contracts are supplied. -/
theorem KTrajectoryEquivalent_iff_sameToken_of_both_contracts
    (bridge : CurrentKObjectBridge object K)
    (invariant : bridge.TokenObservationInvariant)
    (separates : bridge.KSeparatesTokens)
    (first second : ObjectOccurrence) :
    bridge.KTrajectoryEquivalent first second ↔
      object.SameToken first second :=
  ⟨fun equivalent => separates equivalent,
    fun sameToken => invariant sameToken⟩

/-- The occurrence-level carrier projection selected by the explicit bridge. -/
def occurrenceProjection
    (bridge : CurrentKObjectBridge object K) :
    ObjectOccurrence → K.Carrier :=
  fun occurrence => K.encode (bridge.stateOf occurrence)

/-- Exact K semantics makes each occurrence's receiver effects decodable from
its selected carrier projection.  This is projection compatibility, not token
identity. -/
theorem occurrenceProjection_decodes_receiverEffect
    (bridge : CurrentKObjectBridge object K)
    (occurrence : ObjectOccurrence)
    (receiver : K.Receiver) :
    K.decodeReceiverEffect (bridge.occurrenceProjection occurrence) receiver =
      K.receiverEffect (bridge.stateOf occurrence) receiver :=
  bridge.exactK.1 (bridge.stateOf occurrence) receiver

/-- A bridged open object step commutes with the encoded deterministic step. -/
theorem step_commutes_encode
    (bridge : CurrentKObjectBridge object K)
    {source : ObjectOccurrence}
    {input : Input}
    {target : ObjectOccurrence}
    (step : object.openStep source input target) :
    K.carrierTransition (K.encode (bridge.stateOf source)) =
      K.encode (bridge.stateOf target) := by
  calc
    K.carrierTransition (bridge.occurrenceProjection source) =
        K.encode (K.stateTransition (bridge.stateOf source)) :=
      (bridge.exactK.2 (bridge.stateOf source)).symm
    _ = bridge.occurrenceProjection target :=
      congrArg K.encode (bridge.step_commutes step)

end CurrentKObjectBridge

/-! ## Exactness does not manufacture an object bridge

The countermodel below fixes an exact Boolean `CurrentK` whose transition has
no fixed point, and chooses valid whole-object dynamics containing a self-loop.
No `stateOf` can commute with that self-loop, so no `CurrentKObjectBridge`
exists.  This is the formal reason the bridge remains explicit evidence rather
than an inferred field of `HasExactDeclaredSemantics`.
-/

def boolFlipExactCurrentK : CurrentK where
  State := Bool
  Receiver := Unit
  Effect := Bool
  Carrier := Bool
  stateTransition := Bool.not
  receiverEffect := fun state _ => state
  encode := id
  carrierTransition := Bool.not
  decodeReceiverEffect := fun state _ => state

theorem boolFlipExactCurrentK_is_exact :
    HasExactDeclaredSemantics boolFlipExactCurrentK := by
  constructor
  · intro state receiver
    rfl
  · intro state
    rfl

theorem exactCurrentK_need_not_bridge_chosen_object :
    HasExactDeclaredSemantics boolFlipExactCurrentK ∧
      ¬ Nonempty
        (CurrentKObjectBridge boolDynamicQualifiedObject
          boolFlipExactCurrentK) := by
  refine ⟨boolFlipExactCurrentK_is_exact, ?_⟩
  rintro ⟨bridge⟩
  have impossible := bridge.step_commutes
    (source := false) (input := ()) (target := false) trivial
  cases state : bridge.stateOf false <;>
    simp [boolFlipExactCurrentK, state] at impossible

/-!
The next object has only flip steps.  Its identity evidence and declared
object-level identity tests are token-invariant, while the bridged `CurrentK`
receiver effect exposes the changing Boolean state.  Hence same token does not
imply raw K-trajectory equivalence without the separate
`TokenObservationInvariant` synchronization contract.
-/

def boolFlipWholeObjectEvidence : BinaryRelation Bool :=
  fun source target => target = Bool.not source

theorem bool_flip_whole_object_identity_converges :
    ForcedIdentity boolFlipWholeObjectEvidence =
      AllowedIdentity boolWholeObjectLaw := by
  funext first second
  apply propext
  constructor
  · intro generated experiment
    cases experiment
    rfl
  · intro allowed
    cases first <;> cases second
    · exact EquivalenceGenerated.refl false
    · exact EquivalenceGenerated.ofEvidence rfl
    · exact EquivalenceGenerated.ofEvidence rfl
    · exact EquivalenceGenerated.refl true

def boolFlipDynamicQualifiedObject :
    DynamicQualifiedObject toyConstraintModel Unit Bool toyFormedBy
      toyContinuesAt toyRobustAtScale ToyOccurrence Unit Bool
      toyIdentityEvidence toyIdentityLaw Bool Unit Unit Unit where
  seed := false
  snapshot := boolDynamicQualifiedObject.snapshot
  openStep := fun source _ target => target = Bool.not source
  continuationEvidence := boolFlipWholeObjectEvidence
  continuation_grounded := by
    intro source target evidence
    exact ⟨(), evidence⟩
  experimentLaw := boolWholeObjectLaw
  identityConverges := bool_flip_whole_object_identity_converges

def boolFlipObjectKBridge :
    CurrentKObjectBridge boolFlipDynamicQualifiedObject
      boolFlipExactCurrentK where
  stateOf := id
  exactK := boolFlipExactCurrentK_is_exact
  step_commutes := by
    intro source input target step
    simpa [boolFlipExactCurrentK] using step.symm

theorem sameToken_need_not_imply_KTrajectoryEquivalent :
    boolFlipDynamicQualifiedObject.SameToken false true ∧
      ¬ boolFlipObjectKBridge.KTrajectoryEquivalent false true := by
  constructor
  · exact EquivalenceGenerated.ofEvidence rfl
  · intro equivalent
    have atZero := equivalent 0 ()
    exact Bool.false_ne_true (by
      simpa [boolFlipObjectKBridge, boolFlipExactCurrentK, evolveState]
        using atZero)

def singletonExactCurrentK : CurrentK where
  State := Unit
  Receiver := Unit
  Effect := Unit
  Carrier := Unit
  stateTransition := id
  receiverEffect := fun _ _ => ()
  encode := id
  carrierTransition := id
  decodeReceiverEffect := fun _ _ => ()

theorem singletonExactCurrentK_is_exact :
    HasExactDeclaredSemantics singletonExactCurrentK := by
  constructor
  · intro state receiver
    rfl
  · intro state
    rfl

/-- Even for an exact K and a valid dynamic object, existence of a bridge is a
separate proposition.  The chosen Boolean object does admit a constant bridge;
this witness also demonstrates that `stateOf` need not be injective. -/
def boolObjectSingletonKBridge :
    CurrentKObjectBridge boolDynamicQualifiedObject singletonExactCurrentK where
  stateOf := fun _ => ()
  exactK := singletonExactCurrentK_is_exact
  step_commutes := by
    intro source input target step
    rfl

theorem distinct_sameToken_occurrences_can_share_K_state :
    boolDynamicQualifiedObject.SameToken false true ∧
      false ≠ true ∧
      boolObjectSingletonKBridge.stateOf false =
        boolObjectSingletonKBridge.stateOf true := by
  exact ⟨EquivalenceGenerated.ofEvidence trivial, by decide, rfl⟩

/-- Exactness of the K descriptor does not entail injectivity of a chosen
object-state presentation. -/
theorem exactCurrentK_does_not_force_injective_stateOf :
    HasExactDeclaredSemantics singletonExactCurrentK ∧
      ¬ Function.Injective boolObjectSingletonKBridge.stateOf := by
  refine ⟨singletonExactCurrentK_is_exact, ?_⟩
  intro injective
  have falseEqTrue : false = true := injective rfl
  exact Bool.false_ne_true falseEqTrue

/-! ## Product axes combine without becoming the same axis -/

/-- The join of two distinction axes keeps every distinction made by either. -/
def ProductDistinctionProfile
    {State : Type uState}
    (first second : DistinctionProfile State) : DistinctionProfile State :=
  fun left right => first left right ∨ second left right

theorem productDistinctionProfile_atLeast_first
    {State : Type uState}
    (first second : DistinctionProfile State) :
    AtLeastAsDiscriminating (ProductDistinctionProfile first second) first := by
  intro left right distinguished
  exact Or.inl distinguished

theorem productDistinctionProfile_atLeast_second
    {State : Type uState}
    (first second : DistinctionProfile State) :
    AtLeastAsDiscriminating (ProductDistinctionProfile first second) second := by
  intro left right distinguished
  exact Or.inr distinguished

/-- The product profile is the least upper bound in the distinction order. -/
theorem productDistinctionProfile_is_least_upper_bound
    {State : Type uState}
    {first second candidate : DistinctionProfile State}
    (candidateFirst : AtLeastAsDiscriminating candidate first)
    (candidateSecond : AtLeastAsDiscriminating candidate second) :
    AtLeastAsDiscriminating candidate
      (ProductDistinctionProfile first second) := by
  intro left right distinguished
  rcases distinguished with firstDistinction | secondDistinction
  · exact candidateFirst firstDistinction
  · exact candidateSecond secondDistinction

def firstCoordinateDistinctionProfile :
    DistinctionProfile (Bool × Bool) :=
  fun left right => left.1 ≠ right.1

def secondCoordinateDistinctionProfile :
    DistinctionProfile (Bool × Bool) :=
  fun left right => left.2 ≠ right.2

/-- Neither coordinate profile contains all distinctions of the other. -/
theorem coordinateDistinctionProfiles_incomparable :
    ¬ AtLeastAsDiscriminating firstCoordinateDistinctionProfile
        secondCoordinateDistinctionProfile ∧
      ¬ AtLeastAsDiscriminating secondCoordinateDistinctionProfile
        firstCoordinateDistinctionProfile := by
  constructor
  · intro inclusion
    have impossible := inclusion
      (left := (false, false)) (right := (false, true))
      (by simp [secondCoordinateDistinctionProfile])
    exact impossible rfl
  · intro inclusion
    have impossible := inclusion
      (left := (false, false)) (right := (true, false))
      (by simp [firstCoordinateDistinctionProfile])
    exact impossible rfl

/-- Joining the coordinate axes is strictly more discriminating than either
axis alone; a product does not erase the fact that its factors differ. -/
theorem coordinateProduct_strictly_refines_each :
    AtLeastAsDiscriminating
        (ProductDistinctionProfile firstCoordinateDistinctionProfile
          secondCoordinateDistinctionProfile)
        firstCoordinateDistinctionProfile ∧
      AtLeastAsDiscriminating
        (ProductDistinctionProfile firstCoordinateDistinctionProfile
          secondCoordinateDistinctionProfile)
        secondCoordinateDistinctionProfile ∧
      ¬ AtLeastAsDiscriminating firstCoordinateDistinctionProfile
        (ProductDistinctionProfile firstCoordinateDistinctionProfile
          secondCoordinateDistinctionProfile) ∧
      ¬ AtLeastAsDiscriminating secondCoordinateDistinctionProfile
        (ProductDistinctionProfile firstCoordinateDistinctionProfile
          secondCoordinateDistinctionProfile) := by
  refine ⟨productDistinctionProfile_atLeast_first _ _,
    productDistinctionProfile_atLeast_second _ _, ?_, ?_⟩
  · intro productToFirst
    exact coordinateDistinctionProfiles_incomparable.1
      (atLeastAsDiscriminating_trans productToFirst
        (productDistinctionProfile_atLeast_second _ _))
  · intro productToSecond
    exact coordinateDistinctionProfiles_incomparable.2
      (atLeastAsDiscriminating_trans productToSecond
        (productDistinctionProfile_atLeast_first _ _))

end OCKIndividuationMSpaceComposition
