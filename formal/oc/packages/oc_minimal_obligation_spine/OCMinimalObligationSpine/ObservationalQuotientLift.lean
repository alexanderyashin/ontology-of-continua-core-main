import OCMinimalObligationSpine.ObservationalQuotientWorldModel
import OCMinimalObligationSpine.ScopedExactSuccessor

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

universe u uRepairCandidate

/-!
# Observational-quotient lift

The canonical observational quotient can be used as a constructive
representational augmentation of any `CurrentK`.  The new carrier retains the
declared old carrier as its first component and adds only the complete
receiver-effect trajectory quotient as its second component.

This closes a precise part of the first-principle chain:

* every certified finite trajectory distinction has an explicit member in this
  singleton M-space;
* under irreducible pressure, that member is a strict kernel successor; and
* if the old carrier transition already represents the source transition
  exactly, the augmentation has exact receiver-effect and transition semantics.

The construction is not a physical lift, an executable finite approximation of
an infinite trajectory signature, or a proof that a domain observation
interface is complete for raw ontology.
-/

/--
Augment the old carrier with the canonical observational quotient while
retaining an explicit projection back to the old carrier.
-/
def observationalQuotientLift
    (K : CurrentK.{u, u, u, u}) :
    LiftCandidate.{u} K where
  Carrier :=
    K.Carrier ×
      ObservationalState K.receiverEffect K.stateTransition
  encode state :=
    (K.encode state,
      observationalQuotient K.receiverEffect K.stateTransition state)
  carrierTransition carrier :=
    (K.carrierTransition carrier.1,
      observationalTransition K.receiverEffect K.stateTransition carrier.2)
  decodeReceiverEffect carrier receiver :=
    observationalTrajectorySignature
      K.receiverEffect K.stateTransition carrier.2 0 receiver
  project := Prod.fst
  projectEncode := by
    intro state
    rfl
  projectTransitionOnEncoded := by
    intro state
    rfl

/--
The quotient component separates every certified finite receiver-effect
distinction.  This is constructive M-space availability, not merely a
double-negated existence claim.
-/
theorem observationalQuotientLift_resolves
    (K : CurrentK.{u, u, u, u})
    (d : TrajectoryDistinction K) :
    LiftResolves (observationalQuotientLift K) d := by
  intro augmentedCollision
  have quotientCollision :
      observationalQuotient K.receiverEffect K.stateTransition d.left =
        observationalQuotient K.receiverEffect K.stateTransition d.right :=
    congrArg Prod.snd augmentedCollision
  have trajectoryCollision :
      observationalTrajectorySignature
          K.receiverEffect K.stateTransition
          (observationalQuotient
            K.receiverEffect K.stateTransition d.left) =
        observationalTrajectorySignature
          K.receiverEffect K.stateTransition
          (observationalQuotient
            K.receiverEffect K.stateTransition d.right) :=
    congrArg
      (observationalTrajectorySignature
        K.receiverEffect K.stateTransition)
      quotientCollision
  exact d.effect_ne
    (congrFun (congrFun trajectoryCollision d.step) d.receiver)

/-- The auditable singleton search class containing the quotient augmentation. -/
def observationalQuotientLiftSearch
    (K : CurrentK.{u, u, u, u}) :
    LiftSearchClass.{u, 0} K where
  Candidate := Unit
  lift _ := observationalQuotientLift K
  constraints _ := True

/-- Every certified distinction inhabits the singleton quotient-lift M-space. -/
def observationalQuotientMSpaceMember
    (K : CurrentK.{u, u, u, u})
    (d : TrajectoryDistinction K) :
    MSpaceFiber (observationalQuotientLiftSearch K) d :=
  mSpaceWitness
    (observationalQuotientLiftSearch K)
    d
    ()
    trivial
    (observationalQuotientLift_resolves K d)

theorem observationalQuotientLift_available
    (K : CurrentK.{u, u, u, u})
    (d : TrajectoryDistinction K) :
    AvailableLiftWithin (observationalQuotientLiftSearch K) d := by
  exact ⟨observationalQuotientMSpaceMember K d⟩

/--
The quotient component decodes every present receiver effect exactly.
-/
theorem observationalQuotientLift_preserves_receiver_effects
    (K : CurrentK.{u, u, u, u}) :
    PreservesTypedReceiverEffects
      K.receiverEffect
      (observationalQuotientLift K).encode
      (observationalQuotientLift K).decodeReceiverEffect := by
  intro state receiver
  rfl

/--
If the declared old carrier transition is already exact, the quotient
augmentation also represents the full declared deterministic dynamics exactly.
This premise is necessary because a `LiftCandidate` must preserve the old
carrier transition through its projection.
-/
theorem observationalQuotientLift_exact_of_current_transition_exact
    (K : CurrentK.{u, u, u, u})
    (currentTransitionExact :
      PreservesTypedDeterministicDynamics
        K.stateTransition K.encode K.carrierTransition) :
    HasExactDeclaredSemantics (observationalQuotientLift K).toCurrentK := by
  constructor
  · exact observationalQuotientLift_preserves_receiver_effects K
  · intro state
    apply Prod.ext
    · exact currentTransitionExact state
    · rfl

/--
Irreducible pressure plus the explicit quotient M-space member yields a strict
successor without any physical or domain-realization premise.
-/
theorem observationalQuotientLift_strictSuccessor_of_pressure
    {K : CurrentK.{u, u, u, u}}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d) :
    Nonempty (StrictSuccessorCertificate K (observationalQuotientLift K)) := by
  simpa [observationalQuotientLiftSearch] using
    strictSuccessorCertificate_of_pressure_mSpaceMember
      pressure
      (observationalQuotientLiftSearch K)
      (observationalQuotientMSpaceMember K d)

/--
When the old transition is exact, the same construction is an exact strict
successor.  Receiver-effect insufficiency is repaired by the observational
quotient while the already-correct old transition is retained.
-/
theorem observationalQuotientLift_exactStrictSuccessor_of_pressure
    {K : CurrentK.{u, u, u, u}}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (currentTransitionExact :
      PreservesTypedDeterministicDynamics
        K.stateTransition K.encode K.carrierTransition) :
    Nonempty
      (ExactStrictSuccessorCertificate K (observationalQuotientLift K)) := by
  obtain ⟨strictSuccessor⟩ :=
    observationalQuotientLift_strictSuccessor_of_pressure pressure
  exact ⟨{
    strictSuccessor := strictSuccessor
    exactSemantics :=
      observationalQuotientLift_exact_of_current_transition_exact
        K currentTransitionExact
  }⟩

end OCMinimalObligationSpine
