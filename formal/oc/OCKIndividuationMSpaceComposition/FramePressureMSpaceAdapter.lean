import OCKIndividuationMSpaceComposition.FrameAdequacyAndPhase
import OCKIndividuationMSpaceComposition.FundamentalMetaMechanics

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

/-!
Explicit adapter from an outcome collision in an observation frame to the
existing CurrentK pressure and ranked M-space lift machinery.  The adapter does
not infer active demand or exhaustion of same-carrier repairs from a collision;
those remain separately supplied premises.
-/

/-- CurrentK induced by a task-relative observation experiment. -/
def observationCurrentK
    (experiment : ObservationExperiment) [Inhabited experiment.Outcome] : CurrentK where
  State := experiment.World
  Receiver := Unit
  Effect := experiment.Outcome
  Carrier := experiment.Observation
  stateTransition := id
  receiverEffect := fun state _ => experiment.outcome state
  encode := experiment.observe
  carrierTransition := id
  decodeReceiverEffect := fun _ _ => default

/-- Every outcome collision is a certified step-zero trajectory distinction. -/
def OutcomeCollision.toTrajectoryDistinction
    {experiment : ObservationExperiment} [Inhabited experiment.Outcome]
    (collision : OutcomeCollision experiment) :
    TrajectoryDistinction (observationCurrentK experiment) where
  left := collision.left
  right := collision.right
  step := 0
  receiver := ()
  effect_ne := by
    simpa [observationCurrentK] using collision.differentOutcome

/-- The coarse CurrentK encoder cannot express its generating collision. -/
theorem OutcomeCollision.not_expressed_by_observationCurrentK
    {experiment : ObservationExperiment} [Inhabited experiment.Outcome]
    (collision : OutcomeCollision experiment) :
    ¬ Expresses (observationCurrentK experiment)
      collision.toTrajectoryDistinction := by
  intro separates
  exact separates collision.sameObservation

/--
Qualification needed to promote an observed collision to irreducible pressure:
the distinction is active and the declared same-carrier repair class is
exhausted.  Neither premise is manufactured by the adapter.
-/
structure ObservationPressureQualification
    (experiment : ObservationExperiment) [Inhabited experiment.Outcome] where
  repairSearch : RepairSearchClass (observationCurrentK experiment)
  activeDemand : ActiveDemand (observationCurrentK experiment)
  collision : OutcomeCollision experiment
  demandActive : activeDemand collision.toTrajectoryDistinction
  noSameCarrierRepair :
    ¬ RepairableWithin repairSearch collision.toTrajectoryDistinction

theorem ObservationPressureQualification.toIrreduciblePressure
    {experiment : ObservationExperiment} [Inhabited experiment.Outcome]
    (qualification : ObservationPressureQualification experiment) :
    IrreduciblePressureWithin qualification.repairSearch
      qualification.activeDemand qualification.collision.toTrajectoryDistinction :=
  irreduciblePressureWithin_intro
    qualification.repairSearch qualification.activeDemand
    qualification.collision.toTrajectoryDistinction
    qualification.demandActive
    qualification.collision.not_expressed_by_observationCurrentK
    qualification.noSameCarrierRepair

/-- A resolving refinement with an explicit projection back to the old carrier. -/
structure ProjectiveResolvingFrameExtension
    (experiment : ObservationExperiment) (Fine : Type*)
    extends ResolvingFrameExtension experiment Fine where
  project : Fine → experiment.Observation
  project_encode : ∀ world, project (fine world) = experiment.observe world

/-- The projective resolving frame is a genuine existing-core LiftCandidate. -/
noncomputable def ProjectiveResolvingFrameExtension.toLiftCandidate
    {experiment : ObservationExperiment} {Fine : Type*}
    [Inhabited experiment.Outcome]
    (extension : ProjectiveResolvingFrameExtension experiment Fine) :
    LiftCandidate (observationCurrentK experiment) := by
  let outcomeInhabited : Inhabited extension.refinedExperiment.Outcome := by
    simpa [ResolvingFrameExtension.refinedExperiment] using
      (inferInstance : Inhabited experiment.Outcome)
  letI := outcomeInhabited
  exact {
    Carrier := Fine
    encode := extension.fine
    carrierTransition := id
    decodeReceiverEffect := fun fine _ =>
      sufficientObservationPredictor extension.refinedExperiment fine
    project := extension.project
    projectEncode := extension.project_encode
    projectTransitionOnEncoded := by
      intro world
      simpa [observationCurrentK] using extension.project_encode world
  }

/-- The induced lift separates the collision by the proved frame theorem. -/
theorem ProjectiveResolvingFrameExtension.lift_resolves_collision
    {experiment : ObservationExperiment} {Fine : Type*}
    [Inhabited experiment.Outcome]
    (extension : ProjectiveResolvingFrameExtension experiment Fine)
    (collision : OutcomeCollision experiment) :
    LiftResolves extension.toLiftCandidate collision.toTrajectoryDistinction := by
  simpa [LiftResolves, Expresses,
    ProjectiveResolvingFrameExtension.toLiftCandidate,
    OutcomeCollision.toTrajectoryDistinction] using
      extension.toResolvingFrameExtension.splits_collision collision

/-- A frozen singleton lift-search class generated by one checked extension. -/
noncomputable def ProjectiveResolvingFrameExtension.singletonLiftSearch
    {experiment : ObservationExperiment} {Fine : Type*}
    [Inhabited experiment.Outcome]
    (extension : ProjectiveResolvingFrameExtension experiment Fine) :
    LiftSearchClass (observationCurrentK experiment) where
  Candidate := Unit
  lift := fun _ => extension.toLiftCandidate
  constraints := fun _ => True

/-- The checked projective extension constructively inhabits the M-space fiber. -/
theorem ProjectiveResolvingFrameExtension.availableLiftWithin
    {experiment : ObservationExperiment} {Fine : Type*}
    [Inhabited experiment.Outcome]
    (extension : ProjectiveResolvingFrameExtension experiment Fine)
    (collision : OutcomeCollision experiment) :
    AvailableLiftWithin extension.singletonLiftSearch
      collision.toTrajectoryDistinction := by
  exact availableLiftWithin_of_witness extension.singletonLiftSearch
    collision.toTrajectoryDistinction () trivial
    (extension.lift_resolves_collision collision)

/-- Every natural cost on the checked frame-lift fiber has a global minimizer. -/
theorem ProjectiveResolvingFrameExtension.ranked_minimal_lift_exists
    {experiment : ObservationExperiment} {Fine : Type*}
    [Inhabited experiment.Outcome]
    (extension : ProjectiveResolvingFrameExtension experiment Fine)
    (collision : OutcomeCollision experiment)
    (rank : TransitionRank extension.singletonLiftSearch) :
    Nonempty (NatRankedMSpaceArgmin extension.singletonLiftSearch
      collision.toTrajectoryDistinction rank) :=
  natRanked_mSpace_argmin_exists extension.singletonLiftSearch
    collision.toTrajectoryDistinction rank
    (extension.availableLiftWithin collision)

end OCKIndividuationMSpaceComposition
