import OCMinimalObligationSpine.PhysicalAdmissibility
import OCMinimalObligationSpine.UniversalLift

namespace OCMinimalObligationSpine

universe uLiftCarrier uLiftCandidate uRepairCandidate uResource uObservable uCollapseResource uCollapseWitness

/-!
# Physical lift/collapse transfer contract

This module is the next fail-closed bridge after `PhysicalAdmissibility`.

The representational core can prove pressure, M-space membership, strict
successor certificates, and scoped no-lift results.  None of those statements
alone is a physical claim.  This module records the exact additional witness
shape needed to transfer a representational refinement or invalidation into a
physical transition claim:

* a physical lift transition requires a supplied `PhysicalRealizationPackage`;
* a physical collapse transition requires a supplied package containing scoped
  pressure, scoped same-K repair invalidation, scoped lift invalidation, and an
  admissible collapse witness/resource contract.

The theorems below are intentionally one-way.  They prevent both common
overclaims: bare refinement does not manufacture a physical lift, and bare
failure of one representation does not manufacture physical collapse.
-/

/--
A physical lift transition is a representational strict successor whose
resource/observable/error/falsification interface has been supplied by a
domain package.
-/
structure PhysicallyRealizedLiftTransition
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (package :
      PhysicalRealizationPackage.{uLiftCarrier, uLiftCandidate, uRepairCandidate, uResource, uObservable}
        repairSearch activeDemand d liftSearch) where
  certificate :
    StrictSuccessorCertificate K (liftSearch.lift package.member.1)
  resolves : LiftResolves (liftSearch.lift package.member.1) d
  resource_ok : package.resourceAdmissible package.resourceWitness

/--
Supplying a physical realization package transfers the representational
refinement into a physically realized lift transition for that package.

This does not infer that the package exists.
-/
theorem physicalLiftTransition_of_realizationPackage
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (package :
      PhysicalRealizationPackage.{uLiftCarrier, uLiftCandidate, uRepairCandidate, uResource, uObservable}
        repairSearch activeDemand d liftSearch) :
    Nonempty
      (PhysicallyRealizedLiftTransition package) := by
  obtain ⟨certificate⟩ := package.strictSuccessorCertificate
  exact ⟨{
    certificate := certificate
    resolves := package.liftResolves
    resource_ok := package.resourceWitness_admissible
  }⟩

/--
The lift transition's strict-successor certificate preserves old distinctions:
old encoder separation is never destroyed by the physically supplied lift.
-/
theorem PhysicallyRealizedLiftTransition.preserves_current_separation
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {package :
      PhysicalRealizationPackage.{uLiftCarrier, uLiftCandidate, uRepairCandidate, uResource, uObservable}
        repairSearch activeDemand d liftSearch}
    (transition : PhysicallyRealizedLiftTransition package)
    {left right : K.State}
    (oldSeparation : K.encode left ≠ K.encode right) :
    (liftSearch.lift package.member.1).encode left ≠
      (liftSearch.lift package.member.1).encode right :=
  transition.certificate.preserves_current_separation oldSeparation

/--
The lift transition is not a relabeling of the old carrier; it has a strict
kernel witness supplied by the strict-successor certificate.
-/
theorem PhysicallyRealizedLiftTransition.not_relabeling
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {package :
      PhysicalRealizationPackage.{uLiftCarrier, uLiftCandidate, uRepairCandidate, uResource, uObservable}
        repairSearch activeDemand d liftSearch}
    (transition : PhysicallyRealizedLiftTransition package) :
    Not
      (Nonempty
        (EncoderRelabeling K.encode
          (liftSearch.lift package.member.1).encode)) :=
  transition.certificate.not_relabeling

/--
A physical collapse package is stronger than a representational no-go.  It
contains scoped pressure, the scoped absence of a same-K repair, the scoped
absence of an admissible resolving lift, and a supplied physical collapse
witness/resource contract.
-/
structure PhysicalCollapsePackage
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (activeDemand : ActiveDemand K)
    (d : TrajectoryDistinction K)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K) where
  pressure : IrreduciblePressureWithin repairSearch activeDemand d
  no_lift : Not (AvailableLiftWithin liftSearch d)
  CollapseResource : Type uCollapseResource
  collapseResourceWitness : CollapseResource
  collapseResourceAdmissible : CollapseResource -> Prop
  collapse_resource_ok :
    collapseResourceAdmissible collapseResourceWitness
  CollapseWitness : Type uCollapseWitness
  collapseWitness : CollapseWitness
  collapseWitnessAdmissible : CollapseWitness -> Prop
  collapse_witness_ok :
    collapseWitnessAdmissible collapseWitness
  falsificationContract : CollapseWitness -> Prop

/--
The concrete physical-collapse transition certified by a collapse package.
-/
structure PhysicallyRealizedCollapseTransition
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (package :
      PhysicalCollapsePackage.{uLiftCarrier, uLiftCandidate, uRepairCandidate, uCollapseResource, uCollapseWitness}
        repairSearch activeDemand d liftSearch) where
  active : activeDemand d
  current_not_expressive : Not (Expresses K d)
  sameK_repair_invalidated : Not (RepairableWithin repairSearch d)
  lift_invalidated : Not (AvailableLiftWithin liftSearch d)
  collapse_resource_ok :
    package.collapseResourceAdmissible package.collapseResourceWitness
  collapse_witness_ok :
    package.collapseWitnessAdmissible package.collapseWitness

/--
Supplying a full physical collapse package transfers scoped representation
invalidation into a physically realized collapse transition.

This theorem is one-way: it does not infer collapse from one failed repair, one
failed lift, or one untyped observation.
-/
theorem physicalCollapseTransition_of_invalidationPackage
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (package :
      PhysicalCollapsePackage.{uLiftCarrier, uLiftCandidate, uRepairCandidate, uCollapseResource, uCollapseWitness}
        repairSearch activeDemand d liftSearch) :
    PhysicallyRealizedCollapseTransition package := {
  active := package.pressure.1
  current_not_expressive := package.pressure.2.1
  sameK_repair_invalidated := package.pressure.2.2
  lift_invalidated := package.no_lift
  collapse_resource_ok := package.collapse_resource_ok
  collapse_witness_ok := package.collapse_witness_ok
}

/--
If the declared lift class is the unrestricted state-adjoining class, physical
collapse cannot be certified, because the required no-lift premise contradicts
the universal structural lift.
-/
theorem no_physicalCollapsePackage_for_unrestricted_lift
    {K : CurrentK.{uLiftCarrier, uLiftCarrier, uLiftCarrier, uLiftCarrier}}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    (d : TrajectoryDistinction K) :
    Not
      (Nonempty
        (PhysicalCollapsePackage
          repairSearch activeDemand d (universalStateLiftSearch K))) := by
  intro packaged
  obtain ⟨package⟩ := packaged
  exact package.no_lift (universalStateLift_available K d)

end OCMinimalObligationSpine
