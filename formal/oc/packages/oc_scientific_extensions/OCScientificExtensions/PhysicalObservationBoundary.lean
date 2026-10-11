import OCMinimalObligationSpine.PhysicalLiftCollapse

namespace OCScientificExtensions.PhysicalObservationBoundary

open OCMinimalObligationSpine
open UnifiedEntityProjection

universe uLiftCarrier uLiftCandidate uRepairCandidate uObservable

variable {K : CurrentK}
variable {repairSearch : RepairSearchClass.{uRepairCandidate} K}
variable {activeDemand : ActiveDemand K}
variable {d : TrajectoryDistinction K}
variable {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}

/-- A formal decoration, deliberately not a measured physical realization. -/
def formalLiftPackage
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (member : MSpaceFiber liftSearch d) :
    PhysicalRealizationPackage.{uLiftCarrier, uLiftCandidate, uRepairCandidate, 0, 0}
      repairSearch activeDemand d liftSearch where
  pressure := pressure
  member := member
  Resource := Unit
  resourceWitness := ()
  resourceAdmissible := fun _ => True
  resource_ok := True.intro
  Observable := Unit
  observe := fun _ => ()
  errorContract := fun _ => False
  falsificationContract := fun _ => False

/-- At the smallest resource/observable universes the extra interfaces add no
existence obligation beyond the supplied pressure and resolving membership. -/
theorem realizationPackage_nonempty_iff :
    Nonempty (PhysicalRealizationPackage.{uLiftCarrier, uLiftCandidate, uRepairCandidate, 0, 0}
      repairSearch activeDemand d liftSearch) ↔
      IrreduciblePressureWithin repairSearch activeDemand d ∧
        AvailableLiftWithin liftSearch d := by
  constructor
  · rintro ⟨package⟩
    exact ⟨package.pressure, package.availableLiftWithin⟩
  · rintro ⟨pressure, ⟨member⟩⟩
    exact ⟨formalLiftPackage pressure member⟩

/-- The analogous formal decoration for a scoped no-lift result. -/
def formalCollapsePackage
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (noLift : ¬ AvailableLiftWithin liftSearch d) :
    PhysicalCollapsePackage.{uLiftCarrier, uLiftCandidate, uRepairCandidate, 0, 0}
      repairSearch activeDemand d liftSearch where
  pressure := pressure
  no_lift := noLift
  CollapseResource := Unit
  collapseResourceWitness := ()
  collapseResourceAdmissible := fun _ => True
  collapse_resource_ok := True.intro
  CollapseWitness := Unit
  collapseWitness := ()
  collapseWitnessAdmissible := fun _ => True
  collapse_witness_ok := True.intro
  falsificationContract := fun _ => False

/-- Package inhabitation alone does not strengthen the scoped no-lift premise. -/
theorem collapsePackage_nonempty_iff :
    Nonempty (PhysicalCollapsePackage.{uLiftCarrier, uLiftCandidate, uRepairCandidate, 0, 0}
      repairSearch activeDemand d liftSearch) ↔
      IrreduciblePressureWithin repairSearch activeDemand d ∧
        ¬ AvailableLiftWithin liftSearch d := by
  constructor
  · rintro ⟨package⟩
    exact ⟨package.pressure, package.no_lift⟩
  · rintro ⟨pressure, noLift⟩
    exact ⟨formalCollapsePackage pressure noLift⟩

theorem formalLiftPackage_constant_observation
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (member : MSpaceFiber liftSearch d)
    (left right : (liftSearch.lift member.1).Carrier) :
    (formalLiftPackage pressure member).observe left =
      (formalLiftPackage pressure member).observe right := rfl

theorem formalLiftPackage_error_rejected
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (member : MSpaceFiber liftSearch d)
    (carrier : (liftSearch.lift member.1).Carrier) :
    ¬ (formalLiftPackage pressure member).errorContract
      ((formalLiftPackage pressure member).observe carrier) := by
  intro impossible
  exact impossible

theorem formalLiftPackage_falsification_rejected
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (member : MSpaceFiber liftSearch d)
    (carrier : (liftSearch.lift member.1).Carrier) :
    ¬ (formalLiftPackage pressure member).falsificationContract
      ((formalLiftPackage pressure member).observe carrier) := by
  intro impossible
  exact impossible

/-- Even the inherited transition exists for this constant, unsatisfiable
interface. The theorem describes the formal record, not an empirical event. -/
theorem formalLiftPackage_transition_exists
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (member : MSpaceFiber liftSearch d) :
    Nonempty (PhysicallyRealizedLiftTransition (formalLiftPackage pressure member)) :=
  physicalLiftTransition_of_realizationPackage (formalLiftPackage pressure member)

theorem formalCollapsePackage_falsification_rejected
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (noLift : ¬ AvailableLiftWithin liftSearch d) :
    ¬ (formalCollapsePackage pressure noLift).falsificationContract
      (formalCollapsePackage pressure noLift).collapseWitness := by
  intro impossible
  exact impossible

/-- Receiver-effect reconstruction through the observation channel. This is a
separate premise; neither M-space membership nor an interface declaration gives it. -/
def ObservationAdequate (candidate : LiftCandidate.{uLiftCarrier} K)
    {Observable : Type uObservable} (observe : candidate.Carrier → Observable)
    (decodeObserved : Observable → K.Receiver → K.Effect) : Prop :=
  ∀ (state : K.State) (receiver : K.Receiver),
    decodeObserved (observe (candidate.encode state)) receiver =
      K.receiverEffect state receiver

/-- Observation distinguishes the encoded snapshots at the certified step.
This does not assert faithful observed dynamics or distinction at step zero. -/
def ObservesDistinction (candidate : LiftCandidate.{uLiftCarrier} K)
    {Observable : Type uObservable} (observe : candidate.Carrier → Observable)
    (distinction : TrajectoryDistinction K) : Prop :=
  observe (candidate.encode (evolveState K.stateTransition distinction.step distinction.left)) ≠
    observe (candidate.encode (evolveState K.stateTransition distinction.step distinction.right))

theorem observationAdequacy_separates_certified_step
    (candidate : LiftCandidate.{uLiftCarrier} K)
    {Observable : Type uObservable} (observe : candidate.Carrier → Observable)
    (decodeObserved : Observable → K.Receiver → K.Effect)
    (adequate : ObservationAdequate candidate observe decodeObserved)
    (distinction : TrajectoryDistinction K) :
    ObservesDistinction candidate observe distinction := by
  intro collision
  apply distinction.effect_ne
  rw [← adequate (evolveState K.stateTransition distinction.step distinction.left) distinction.receiver,
      ← adequate (evolveState K.stateTransition distinction.step distinction.right) distinction.receiver]
  exact congrArg (fun observation => decodeObserved observation distinction.receiver) collision

theorem constant_observation_not_adequate
    (candidate : LiftCandidate.{uLiftCarrier} K)
    (decodeObserved : Unit → K.Receiver → K.Effect)
    (distinction : TrajectoryDistinction K) :
    ¬ ObservationAdequate candidate (fun _ => ()) decodeObserved := by
  intro adequate
  exact observationAdequacy_separates_certified_step candidate (fun _ => ())
    decodeObserved adequate distinction rfl

end OCScientificExtensions.PhysicalObservationBoundary
