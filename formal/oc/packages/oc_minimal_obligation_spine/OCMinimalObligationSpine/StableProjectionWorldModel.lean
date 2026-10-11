import OCMinimalObligationSpine.UnifiedEntityProjection

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

universe uEntity uIndex uView uSource uReceiver uEffect uCarrier

/--
A typed family of views of one underlying entity.  The family contains no
assumption that one view, or even all views together, determine the entity.
-/
structure ProjectionFamily
    (Entity : Type uEntity)
    (Index : Type uIndex)
    (View : Index -> Type uView) where
  project : (index : Index) -> Entity -> View index

namespace ProjectionFamily

/-- The joint signature collects every declared projection of one entity. -/
def signature
    (family : ProjectionFamily Entity Index View)
    (entity : Entity) :
    (index : Index) -> View index :=
  fun index => family.project index entity

/--
Joint separation is exactly injectivity of the complete projection signature.
It is an additional property, not a consequence of merely declaring views.
-/
def JointlySeparates
    (family : ProjectionFamily Entity Index View) : Prop :=
  Function.Injective family.signature

/-- Every pair of distinct entities is distinguished by at least one view. -/
def JointlyDistinguishes
  (family : ProjectionFamily Entity Index View) : Prop :=
  forall {left right : Entity},
    left ≠ right ->
      Exists fun index => family.project index left ≠ family.project index right

theorem jointly_separates_iff_jointly_distinguishes
    (family : ProjectionFamily Entity Index View) :
    family.JointlySeparates <-> family.JointlyDistinguishes := by
  constructor
  · intro separates left right distinct
    apply Classical.byContradiction
    intro noDistinguishingProjection
    apply distinct
    apply separates
    funext index
    apply Classical.byContradiction
    intro differsAtIndex
    exact noDistinguishingProjection ⟨index, differsAtIndex⟩
  · intro distinguishes left right sameSignature
    apply Classical.byContradiction
    intro distinct
    obtain ⟨index, differsAtIndex⟩ := distinguishes distinct
    exact differsAtIndex (congrFun sameSignature index)

/--
A tuple of views is compatible when all of its components come from one and
the same entity.  This is image membership, not merely pairwise agreement.
-/
def Compatible
    (family : ProjectionFamily Entity Index View)
    (views : (index : Index) -> View index) : Prop :=
  Exists fun entity => family.signature entity = views

/-- Every actually generated joint signature is compatible. -/
theorem signature_is_compatible
    (family : ProjectionFamily Entity Index View)
    (entity : Entity) :
    family.Compatible (family.signature entity) := by
  exact ⟨entity, rfl⟩

/--
There is at most one entity realizing any compatible tuple of views.  The
definition deliberately makes the required separation premise explicit.
-/
def HasUniqueCompatibleRealizations
    (family : ProjectionFamily Entity Index View) : Prop :=
  forall (views : (index : Index) -> View index) (left right : Entity),
    family.signature left = views ->
    family.signature right = views ->
    left = right

theorem jointly_separates_iff_unique_compatible_realizations
    (family : ProjectionFamily Entity Index View) :
    family.JointlySeparates <-> family.HasUniqueCompatibleRealizations := by
  constructor
  · intro separates views left right leftRealizes rightRealizes
    exact separates (leftRealizes.trans rightRealizes.symm)
  · intro unique left right sameSignature
    exact unique (family.signature left) left right rfl sameSignature.symm

/--
Dynamic stability is the commuting square

  entity --entityTransition--> entity
     |                           |
  signature                  signature
     |                           |
     v                           v
  views  --signatureTransition-> views.

No metric, approximation tolerance, or empirical adequacy is hidden here.
-/
def DynamicsCommute
    (family : ProjectionFamily Entity Index View)
    (entityTransition : Entity -> Entity)
    (signatureTransition :
      ((index : Index) -> View index) -> (index : Index) -> View index) : Prop :=
  forall entity,
    family.signature (entityTransition entity) =
      signatureTransition (family.signature entity)

end ProjectionFamily

/--
An assumption package for interpreting a domain as a stable, jointly
separating family of projections.  In particular, this declaration does not
construct such a package for the physical world.  A domain application must
independently justify both fields with formal and empirical evidence.
-/
structure WorldModelRealizationHypothesis
    (Entity : Type uEntity)
    (Index : Type uIndex)
    (View : Index -> Type uView)
    (family : ProjectionFamily Entity Index View)
    (entityTransition : Entity -> Entity)
    (signatureTransition :
      ((index : Index) -> View index) -> (index : Index) -> View index) : Prop where
  jointlySeparates : family.JointlySeparates
  dynamicsCommute :
    family.DynamicsCommute entityTransition signatureTransition

theorem realization_hypothesis_gives_unique_reconstruction
    (hypothesis :
      WorldModelRealizationHypothesis Entity Index View family
        entityTransition signatureTransition)
    {views : (index : Index) -> View index}
    {left right : Entity}
    (leftRealizes : family.signature left = views)
    (rightRealizes : family.signature right = views) :
    left = right := by
  exact hypothesis.jointlySeparates
    (leftRealizes.trans rightRealizes.symm)

/--
The proved causal-trajectory metakernel is a concrete projection family:
projection `step` returns the receiver-indexed effect at that finite step.
-/
def trajectoryProjectionFamily
    {Source : Type uSource}
    {Receiver : Type uReceiver}
    {Effect : Type uEffect}
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    ProjectionFamily Source Nat (fun _ => Receiver -> Effect) :=
  { project := fun step source =>
      causalEffectSignature effect (evolveState transition step source) }

theorem trajectory_projection_signature_is_causal_trajectory_signature
    {Source : Type uSource}
    {Receiver : Type uReceiver}
    {Effect : Type uEffect}
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source)
    (source : Source) :
    (trajectoryProjectionFamily effect transition).signature source =
      causalTrajectorySignature effect transition source := by
  rfl

/--
Advancing the entity and then taking its complete trajectory signature equals
first taking the signature and then shifting it.  This reuses the already
proved closed-dynamics theorem rather than postulating stability anew.
-/
theorem trajectory_projection_dynamics_commute
    {Source : Type uSource}
    {Receiver : Type uReceiver}
    {Effect : Type uEffect}
    (effect : Source -> Receiver -> Effect)
    (transition : Source -> Source) :
    (trajectoryProjectionFamily effect transition).DynamicsCommute
      transition shiftCausalTrajectory := by
  exact causal_trajectory_signature_has_closed_dynamics effect transition

/--
Every exact closed encoder refines the joint trajectory projections: an
encoder collision forces equality of all finite-step receiver projections.
-/
theorem exact_encoder_refines_trajectory_projections
    {Source : Type uSource}
    {Receiver : Type uReceiver}
    {Effect : Type uEffect}
    {Carrier : Type uCarrier}
    {effect : Source -> Receiver -> Effect}
    {transition : Source -> Source}
    {encode : Source -> Carrier}
    {decode : Carrier -> Receiver -> Effect}
    {encodedTransition : Carrier -> Carrier}
    (preservesEffects :
      PreservesTypedReceiverEffects effect encode decode)
    (closedDynamics :
      PreservesTypedDeterministicDynamics transition encode
        encodedTransition)
    {left right : Source}
    (collision : encode left = encode right) :
    (trajectoryProjectionFamily effect transition).signature left =
      (trajectoryProjectionFamily effect transition).signature right := by
  exact exact_causal_dynamic_encoder_refines_trajectory_signature
    preservesEffects closedDynamics collision

/--
Reconstruction from all trajectory projections is unique only after joint
separation has been supplied.  Closed shift dynamics alone does not prove it.
-/
theorem trajectory_reconstruction_unique_of_joint_separation
    {Source : Type uSource}
    {Receiver : Type uReceiver}
    {Effect : Type uEffect}
    {effect : Source -> Receiver -> Effect}
    {transition : Source -> Source}
    (separates :
      (trajectoryProjectionFamily effect transition).JointlySeparates)
    {left right : Source}
    (sameTrajectory :
      causalTrajectorySignature effect transition left =
        causalTrajectorySignature effect transition right) :
    left = right := by
  exact separates sameTrajectory

end OCMinimalObligationSpine
