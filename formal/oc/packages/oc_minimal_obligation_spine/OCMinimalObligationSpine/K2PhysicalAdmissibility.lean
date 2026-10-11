import OCMinimalObligationSpine.PhysicalLiftCollapse
import OCMinimalObligationSpine.K2DiffusionStructural

namespace OCMinimalObligationSpine.K2PhysicalAdmissibility

open K2DiffusionStructural

/-!
# Bounded K2 physical-admissibility package

This module connects the already proved K2 structural witness to the generic
`PhysicalRealizationPackage` bridge.

It does not prove a universal physical law and it does not derive the Spot-On
replay result from Lean.  The replay admission remains a hash-bound external
evidence contract in the release graph.  Lean records the fail-closed shape of
the domain package: a supplied scoped resource token, a concrete M-space
member, an observable interface, an error contract, and a falsification
contract.  From such a package the generic physical bridge yields only the
existing strict-successor and lift-resolution certificates for this bounded K2
instantiation.
-/

/-- A scoped external replay resource token admitted by the release graph. -/
inductive K2SpotOnReplayResource where
  | spotOnEndpointZipHashBound
deriving DecidableEq, Repr

/--
Resource admissibility is intentionally a predicate over a supplied token.
The predicate is not manufactured by Lean from local files; the UMG binds this
token to the hash-bound Spot-On replay contract.
-/
def k2ReplayResourceAdmissible : K2SpotOnReplayResource -> Prop
  | .spotOnEndpointZipHashBound => True

/-- The finite structural observable exposed by the selected timestamp lift. -/
structure K2TimestampObservable where
  signature : Nat
  timestamp : Nat
deriving DecidableEq, Repr

/-- Observe the selected timestamp-channel carrier. -/
def observeTimestampCarrier (carrier : Nat × Nat) : K2TimestampObservable where
  signature := carrier.1
  timestamp := carrier.2

/--
The bounded error contract for the two-state endpoint: when the old scalar
signature is the matched collision value `4`, the admitted timestamp observable
must be one of the two declared finite endpoint timestamps.
-/
def k2EndpointErrorContract (obs : K2TimestampObservable) : Prop :=
  obs.signature = 4 -> obs.timestamp = 1 \/ obs.timestamp = 2

/--
Falsification mode for this finite endpoint: the matched old signature appears
with a timestamp outside the declared two-state endpoint.
-/
def k2EndpointFalsificationContract (obs : K2TimestampObservable) : Prop :=
  obs.signature = 4 /\ obs.timestamp ≠ 1 /\ obs.timestamp ≠ 2

/-- The selected timestamp lift yields the early endpoint observable. -/
def observedEarlyFast : K2TimestampObservable :=
  observeTimestampCarrier ((diffusionLift .timestampChannel).encode .earlyFast)

/-- The selected timestamp lift yields the late endpoint observable. -/
def observedLateSlow : K2TimestampObservable :=
  observeTimestampCarrier ((diffusionLift .timestampChannel).encode .lateSlow)

theorem observedEarlyFast_satisfies_error_contract :
    k2EndpointErrorContract observedEarlyFast := by
  intro _matchedSignature
  exact Or.inl rfl

theorem observedLateSlow_satisfies_error_contract :
    k2EndpointErrorContract observedLateSlow := by
  intro _matchedSignature
  exact Or.inr rfl

theorem observedEarlyFast_not_falsified :
    Not (k2EndpointFalsificationContract observedEarlyFast) := by
  intro h
  exact h.2.1 rfl

theorem observedLateSlow_not_falsified :
    Not (k2EndpointFalsificationContract observedLateSlow) := by
  intro h
  exact h.2.2 rfl

/--
The bounded K2 physical-realization package.

The package supplies the structural pressure witness, the timestamp M-space
member, a scoped replay-resource token, and the finite observable/error/
falsification interface.  It is one domain package, not a universal physical
realization theorem.
-/
def k2TimestampPhysicalRealizationPackage :
    PhysicalRealizationPackage
      postprocessingRepairSearch
      timestampDemand
      timestampDistinction
      diffusionLiftSearch where
  pressure := postprocessing_irreducible_pressure
  member := timestampMember
  Resource := K2SpotOnReplayResource
  resourceWitness := .spotOnEndpointZipHashBound
  resourceAdmissible := k2ReplayResourceAdmissible
  resource_ok := by
    trivial
  Observable := K2TimestampObservable
  observe := observeTimestampCarrier
  errorContract := k2EndpointErrorContract
  falsificationContract := k2EndpointFalsificationContract

/-- The bounded K2 package inherits the generic strict-successor certificate. -/
theorem k2PhysicalPackageStrictSuccessor :
    Nonempty
      (StrictSuccessorCertificate diffusionVarianceK
        (diffusionLiftSearch.lift
          k2TimestampPhysicalRealizationPackage.member.1)) :=
  k2TimestampPhysicalRealizationPackage.strictSuccessorCertificate

/-- The bounded K2 package resolves the declared timestamp distinction. -/
theorem k2PhysicalPackageLiftResolves :
    LiftResolves
      (diffusionLiftSearch.lift
        k2TimestampPhysicalRealizationPackage.member.1)
      timestampDistinction :=
  k2TimestampPhysicalRealizationPackage.liftResolves

/-- The bounded K2 package realizes the generic physical lift transition. -/
theorem k2PhysicalPackageLiftTransition :
    Nonempty
      (PhysicallyRealizedLiftTransition
        k2TimestampPhysicalRealizationPackage) :=
  physicalLiftTransition_of_realizationPackage
    k2TimestampPhysicalRealizationPackage

/-- The replay resource token is explicitly admissible in the package. -/
theorem k2PhysicalPackageResourceAdmissible :
    k2TimestampPhysicalRealizationPackage.resourceAdmissible
      k2TimestampPhysicalRealizationPackage.resourceWitness :=
  k2TimestampPhysicalRealizationPackage.resourceWitness_admissible

end OCMinimalObligationSpine.K2PhysicalAdmissibility
