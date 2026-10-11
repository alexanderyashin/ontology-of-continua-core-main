import OCMinimalObligationSpine.StrictSuccessor

namespace OCMinimalObligationSpine

universe uLiftCarrier uLiftCandidate uRepairCandidate uResource uObservable

/-!
`PhysicalAdmissibility` is the fail-closed bridge between the formal
representational calculus and any physical-domain claim.

The earlier modules prove that, under scoped pressure plus an inhabited
M-space fiber, a strict successor representation exists.  That is still only a
representational theorem.  This module makes the missing physical witness
explicit: a physical realization package must provide the M-space member,
resource admissibility, an observable interface, an error contract, and a
falsification contract.  Without such a package, publication may discuss a
formal lift or no-go boundary, but must not claim physical axis birth, physical
collapse, or empirical validation.
-/

/--
An admitted physical realization of one declared lift.

The package deliberately keeps resource, observable, error, and falsification
types abstract.  A domain instance must supply those objects and proofs; this
core bridge does not manufacture them from the quotient theorem.
-/
structure PhysicalRealizationPackage
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (activeDemand : ActiveDemand K)
    (d : TrajectoryDistinction K)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K) where
  pressure : IrreduciblePressureWithin repairSearch activeDemand d
  member : MSpaceFiber liftSearch d
  Resource : Type uResource
  resourceWitness : Resource
  resourceAdmissible : Resource -> Prop
  resource_ok : resourceAdmissible resourceWitness
  Observable : Type uObservable
  observe : (liftSearch.lift member.1).Carrier -> Observable
  errorContract : Observable -> Prop
  falsificationContract : Observable -> Prop

/-- A physical package necessarily contains a constructive M-space witness. -/
theorem PhysicalRealizationPackage.availableLiftWithin
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (package :
      PhysicalRealizationPackage repairSearch activeDemand d liftSearch) :
    AvailableLiftWithin liftSearch d := by
  exact ⟨package.member⟩

/--
An admitted physical package inherits the strict-successor certificate already
proved by the M-space/pressure layer.
-/
theorem PhysicalRealizationPackage.strictSuccessorCertificate
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (package :
      PhysicalRealizationPackage repairSearch activeDemand d liftSearch) :
    Nonempty
      (StrictSuccessorCertificate K
        (liftSearch.lift package.member.1)) :=
  strictSuccessorCertificate_of_pressure_mSpaceMember
    package.pressure liftSearch package.member

/--
The resource proof in a physical package is an explicit assumption, not a
consequence of representational refinement.
-/
theorem PhysicalRealizationPackage.resourceWitness_admissible
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (package :
      PhysicalRealizationPackage repairSearch activeDemand d liftSearch) :
    package.resourceAdmissible package.resourceWitness :=
  package.resource_ok

/--
If a physical package is supplied, the represented distinction is resolved by
the selected lift.  The theorem is intentionally one-way: it does not infer a
physical package from a bare resolved distinction.
-/
theorem PhysicalRealizationPackage.liftResolves
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (package :
      PhysicalRealizationPackage repairSearch activeDemand d liftSearch) :
    LiftResolves (liftSearch.lift package.member.1) d :=
  mSpaceMember_resolves package.member

end OCMinimalObligationSpine
