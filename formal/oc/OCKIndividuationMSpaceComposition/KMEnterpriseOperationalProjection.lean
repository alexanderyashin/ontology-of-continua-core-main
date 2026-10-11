import OCKIndividuationMSpaceComposition.KMEnterpriseCarrierProjection

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine
open scoped BigOperators

universe uLiftCarrier uLiftCandidate uRepairCandidate uState

/-!
# Operational enterprise-carrier projection

This module replaces an unconstrained state-to-carrier label with an auditable
operational rule.  A state exposes eight nonnegative carrier counts.  Dominance
is maximum count with the frozen enterprise vocabulary order as tie-break.
K/M predictions that force the corresponding inequalities therefore force a
carrier support and, in the singleton case, a numerical point mass.
-/

abbrev EnterpriseCarrierCountProfile := EnterpriseCarrier → Nat

/-- Frozen tie-break order shared with the executable enterprise adapter. -/
def enterpriseCarrierPriority : EnterpriseCarrier → Nat
  | .assetRevision => 0
  | .capabilityRealization => 1
  | .commitmentRisk => 2
  | .controlDecision => 3
  | .deploymentInstance => 4
  | .releaseSurface => 5
  | .scientificClaim => 6
  | .workItemRun => 7

/-- A carrier is operationally dominant when every other count is smaller, or
the counts tie and this carrier occurs no later in the frozen vocabulary. -/
def OperationallyDominant
    (profile : EnterpriseCarrierCountProfile)
    (carrier : EnterpriseCarrier) : Prop :=
  ∀ other,
    profile other < profile carrier ∨
      (profile other = profile carrier ∧
        enterpriseCarrierPriority carrier ≤ enterpriseCarrierPriority other)

/-- The frozen priority map has no collisions. -/
theorem enterpriseCarrierPriority_injective :
    Function.Injective enterpriseCarrierPriority := by
  intro left right equalScore
  cases left <;> cases right <;>
    simp [enterpriseCarrierPriority] at equalScore ⊢

/-- Consequently the operational dominance certificate identifies at most one
carrier. -/
theorem operationallyDominant_unique
    (profile : EnterpriseCarrierCountProfile)
    {left right : EnterpriseCarrier}
    (leftDominant : OperationallyDominant profile left)
    (rightDominant : OperationallyDominant profile right) :
    left = right := by
  obtain leftCountHigher | ⟨countEqual, leftPriorityEarlier⟩ :=
    leftDominant right
  · obtain rightCountHigher | ⟨reverseCountEqual, _⟩ :=
      rightDominant left
    · exact False.elim (Nat.lt_asymm leftCountHigher rightCountHigher)
    · rw [reverseCountEqual] at leftCountHigher
      exact False.elim (Nat.lt_irrefl _ leftCountHigher)
  · obtain rightCountHigher | ⟨_, rightPriorityEarlier⟩ :=
      rightDominant left
    · rw [countEqual] at rightCountHigher
      exact False.elim (Nat.lt_irrefl _ rightCountHigher)
    · apply enterpriseCarrierPriority_injective
      exact Nat.le_antisymm leftPriorityEarlier rightPriorityEarlier

/-- A lawful operational projection exposes its count profile, selected
carrier, and a checkable dominance certificate for every concrete state. -/
structure EnterpriseOperationalProjection (State : Type uState) where
  profile : State → EnterpriseCarrierCountProfile
  carrier : State → EnterpriseCarrier
  dominant : ∀ state, OperationallyDominant (profile state) (carrier state)

/-- Any independently established dominance certificate must agree with the
registered projection. -/
theorem EnterpriseOperationalProjection.carrier_eq_of_dominant
    {State : Type uState}
    (projection : EnterpriseOperationalProjection State)
    (state : State) (carrier : EnterpriseCarrier)
    (dominant : OperationallyDominant (projection.profile state) carrier) :
    projection.carrier state = carrier :=
  operationallyDominant_unique (projection.profile state)
    (projection.dominant state) dominant

/-- If every selected-model terminal future satisfies one carrier dominance
certificate and at least one such future exists, the OC-derived carrier support
is exactly that singleton. -/
theorem km_operational_dominance_yields_singleton_carrier_support
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (projection : EnterpriseOperationalProjection interpretation.State)
    (selectedCarrier : EnterpriseCarrier)
    (witnessTarget : interpretation.State)
    (witnessFuture : interpretation.predictiveInterpretation.targetFutureAt
      resolution.selection.minimizer.1 witnessTarget)
    (dominance : ∀ target,
      interpretation.predictiveInterpretation.targetFutureAt
        resolution.selection.minimizer.1 target →
      OperationallyDominant (projection.profile target) selectedCarrier) :
    ∀ carrier,
      KMDerivedEnterpriseCarrierSupport resolution interpretation
        projection.carrier carrier ↔ carrier = selectedCarrier := by
  intro carrier
  constructor
  · rintro ⟨target, future, observedCarrier⟩
    have projectedIsSelected := projection.carrier_eq_of_dominant
      target selectedCarrier (dominance target future)
    exact observedCarrier.symm.trans projectedIsSelected
  · intro carrierIsSelected
    subst carrier
    refine ⟨witnessTarget, witnessFuture, ?_⟩
    exact projection.carrier_eq_of_dominant witnessTarget selectedCarrier
      (dominance witnessTarget witnessFuture)

/-- With context/continuation coherence, the same operational singleton
certificate excludes every other carrier over all tied K/M minima. -/
theorem km_operational_singleton_excludes_other_carriers_for_all_tied
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (projection : EnterpriseOperationalProjection interpretation.State)
    (coherent : KMTiedContextContinuationCoherent resolution interpretation)
    (selectedCarrier carrier : EnterpriseCarrier)
    (singletonSupport : ∀ candidateCarrier,
      KMDerivedEnterpriseCarrierSupport resolution interpretation
        projection.carrier candidateCarrier ↔
          candidateCarrier = selectedCarrier)
    (different : carrier ≠ selectedCarrier) :
    ¬ KMPossibleFuture resolution
      (interpretation.carrierFutureAt projection.carrier) carrier := by
  apply km_context_coherence_excludes_carrier_for_all_tied_models
    resolution interpretation projection.carrier coherent carrier
  intro support
  exact different ((singletonSupport carrier).mp support)

/-- The selected operational singleton is necessary over the tied class. -/
theorem km_operational_singleton_carrier_is_necessary
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (projection : EnterpriseOperationalProjection interpretation.State)
    (coherent : KMTiedContextContinuationCoherent resolution interpretation)
    (selectedCarrier : EnterpriseCarrier)
    (singletonSupport : ∀ candidateCarrier,
      KMDerivedEnterpriseCarrierSupport resolution interpretation
        projection.carrier candidateCarrier ↔
          candidateCarrier = selectedCarrier) :
    KMNecessaryFuture resolution
      (interpretation.carrierFutureAt projection.carrier) selectedCarrier := by
  apply km_context_coherence_makes_selected_carrier_necessary
    resolution interpretation projection.carrier coherent selectedCarrier
  exact (singletonSupport selectedCarrier).mpr rfl

/-- Combining the operational singleton theorem with finite normalization
forces probability one on the selected carrier. -/
theorem km_operational_singleton_forces_numerical_point_mass
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (projection : EnterpriseOperationalProjection interpretation.State)
    (selectedCarrier : EnterpriseCarrier)
    (mass : EnterpriseCarrier → Nat) (total : Nat)
    (normalized : (∑ carrier, mass carrier) = total)
    (compatible : EnterpriseCarrierMassSupportCompatible
      (KMDerivedEnterpriseCarrierSupport resolution interpretation
        projection.carrier) mass)
    (singletonSupport : ∀ carrier,
      KMDerivedEnterpriseCarrierSupport resolution interpretation
        projection.carrier carrier ↔ carrier = selectedCarrier) :
    mass selectedCarrier = total :=
  singleton_formal_support_forces_point_mass
    (KMDerivedEnterpriseCarrierSupport resolution interpretation
      projection.carrier) mass total selectedCarrier normalized compatible
    singletonSupport

/-!
## Incomplete-observation countermodel
-/

def scientificOnlyDominantProfile : EnterpriseCarrierCountProfile
  | .scientificClaim => 1
  | _ => 0

def hiddenControlDominantProfile : EnterpriseCarrierCountProfile
  | .scientificClaim => 1
  | .controlDecision => 2
  | _ => 0

def observeScientificCount (profile : EnterpriseCarrierCountProfile) : Nat :=
  profile .scientificClaim

theorem scientificOnly_profile_is_scientific_dominant :
    OperationallyDominant scientificOnlyDominantProfile .scientificClaim := by
  intro other
  cases other <;>
    decide

theorem hiddenControl_profile_is_control_dominant :
    OperationallyDominant hiddenControlDominantProfile .controlDecision := by
  intro other
  cases other <;>
    decide

/-- No-go: observing only the scientific-change count collapses two profiles
with distinct operationally certified carriers.  A carrier forecast therefore
requires the complete registered operational profile (or a proved sufficient
compression), not a SHA, path, status, or single counter. -/
theorem scientific_count_alone_does_not_determine_dominant_carrier :
    observeScientificCount scientificOnlyDominantProfile =
        observeScientificCount hiddenControlDominantProfile ∧
      OperationallyDominant scientificOnlyDominantProfile .scientificClaim ∧
      OperationallyDominant hiddenControlDominantProfile .controlDecision ∧
      EnterpriseCarrier.scientificClaim ≠ EnterpriseCarrier.controlDecision := by
  exact ⟨rfl, scientificOnly_profile_is_scientific_dominant,
    hiddenControl_profile_is_control_dominant, by decide⟩

end OCKIndividuationMSpaceComposition
