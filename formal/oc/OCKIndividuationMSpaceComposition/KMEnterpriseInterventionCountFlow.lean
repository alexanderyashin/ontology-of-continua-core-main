import OCKIndividuationMSpaceComposition.KMEnterpriseCountFlowDynamics
import OCKIndividuationMSpaceComposition.EnterpriseDynamicsBridge

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe uPath uLiftCarrier uLiftCandidate uRepairCandidate

/-!
# Action-conditioned K/M carrier-count flow

The passive count flow only bounds what may happen. A controlled enterprise
run contains additional information: a valid occurrence-bound intervention
declares carrier evidence that execution is intended to add. This module
separates that declared contribution from residual dynamics and proves the
exact numerical margin at which an intervention forces one operational
carrier despite every residual trajectory allowed by the bounds.

Prior-art disposition: `REUSE` finite stock-flow balance and declared-action
conditioning; `ADAPT` them to the typed OC carrier profile and K/M bridge. No
new causal-identification claim is made here.
-/

/-- A run-bound plan contributes a nonnegative carrier-evidence increment at
each event. Active validity is explicit: a stale plan is not a prediction. -/
structure DeclaredCarrierIntervention where
  occurrenceToken : Nat
  validityActive : Bool
  plannedIncrement : Nat → EnterpriseCarrierCountProfile

/-- Total carrier evidence declared through, but excluding, the horizon. -/
def DeclaredCarrierIntervention.cumulative
    (intervention : DeclaredCarrierIntervention) :
    Nat → EnterpriseCarrierCountProfile
  | 0 => fun _ => 0
  | horizon + 1 => fun carrier =>
      intervention.cumulative horizon carrier +
        intervention.plannedIncrement horizon carrier

@[simp] theorem DeclaredCarrierIntervention.cumulative_zero
    (intervention : DeclaredCarrierIntervention) :
    intervention.cumulative 0 = fun _ => 0 := rfl

@[simp] theorem DeclaredCarrierIntervention.cumulative_succ
    (intervention : DeclaredCarrierIntervention) (horizon : Nat)
    (carrier : EnterpriseCarrier) :
    intervention.cumulative (horizon + 1) carrier =
      intervention.cumulative horizon carrier +
        intervention.plannedIncrement horizon carrier := rfl

/-- Actual action-conditioned counts are the declared contribution plus a
residual process. The residual includes initial evidence and every unplanned
but admissible addition. -/
structure ActionConditionedCarrierCountDynamics where
  intervention : DeclaredCarrierIntervention
  residual : CarrierCountDynamics

def ActionConditionedCarrierCountDynamics.countAt
    (dynamics : ActionConditionedCarrierCountDynamics) (horizon : Nat) :
    EnterpriseCarrierCountProfile :=
  fun carrier => dynamics.residual.countAt horizon carrier +
    dynamics.intervention.cumulative horizon carrier

def ActionConditionedCarrierCountDynamics.Respects
    (dynamics : ActionConditionedCarrierCountDynamics)
    (bounds : CarrierCountFlowBounds) : Prop :=
  dynamics.intervention.validityActive = true ∧
    dynamics.residual.Respects bounds

/-- The passive flow envelope translated by the exact declared contribution. -/
def actionConditionedCarrierEnvelope
    (bounds : CarrierCountFlowBounds)
    (intervention : DeclaredCarrierIntervention)
    (horizon : Nat) : CarrierCountEnvelope where
  lower carrier :=
    (carrierCountFlowEnvelope bounds horizon).lower carrier +
      intervention.cumulative horizon carrier
  upper carrier :=
    (carrierCountFlowEnvelope bounds horizon).upper carrier +
      intervention.cumulative horizon carrier
  valid carrier := Nat.add_le_add_right
    ((carrierCountFlowEnvelope bounds horizon).valid carrier) _

/-- Positive theorem: every conformant residual trajectory lies inside the
action-conditioned envelope. -/
theorem ActionConditionedCarrierCountDynamics.countAt_within_envelope
    (dynamics : ActionConditionedCarrierCountDynamics)
    (bounds : CarrierCountFlowBounds)
    (respects : dynamics.Respects bounds) (horizon : Nat) :
    ProfileWithin
      (actionConditionedCarrierEnvelope bounds dynamics.intervention horizon)
      (dynamics.countAt horizon) := by
  intro carrier
  have residualWithin := CarrierCountDynamics.countAt_within_flowEnvelope
    dynamics.residual bounds respects.2 horizon carrier
  exact ⟨Nat.add_le_add_right residualWithin.1 _,
    Nat.add_le_add_right residualWithin.2 _⟩

def lowerExtremalActionConditionedDynamics
    (bounds : CarrierCountFlowBounds)
    (intervention : DeclaredCarrierIntervention) :
    ActionConditionedCarrierCountDynamics where
  intervention := intervention
  residual := lowerExtremalCarrierCountDynamics bounds

def upperExtremalActionConditionedDynamics
    (bounds : CarrierCountFlowBounds)
    (intervention : DeclaredCarrierIntervention) :
    ActionConditionedCarrierCountDynamics where
  intervention := intervention
  residual := upperExtremalCarrierCountDynamics bounds

/-- Both translated endpoints remain attainable whenever the plan is active;
the action-conditioned interval is therefore sharp, not merely conservative. -/
theorem actionConditionedCarrierEnvelope_endpoints_attainable
    (bounds : CarrierCountFlowBounds)
    (intervention : DeclaredCarrierIntervention)
    (active : intervention.validityActive = true)
    (horizon : Nat) :
    ∃ lowerDynamics upperDynamics : ActionConditionedCarrierCountDynamics,
      lowerDynamics.Respects bounds ∧ upperDynamics.Respects bounds ∧
      lowerDynamics.countAt horizon =
        (actionConditionedCarrierEnvelope bounds intervention horizon).lower ∧
      upperDynamics.countAt horizon =
        (actionConditionedCarrierEnvelope bounds intervention horizon).upper := by
  refine ⟨lowerExtremalActionConditionedDynamics bounds intervention,
    upperExtremalActionConditionedDynamics bounds intervention,
    ⟨active, lowerExtremal_respects bounds⟩,
    ⟨active, upperExtremal_respects bounds⟩, ?_, ?_⟩
  · funext carrier
    simp only [ActionConditionedCarrierCountDynamics.countAt,
      lowerExtremalActionConditionedDynamics, actionConditionedCarrierEnvelope]
    rw [lowerExtremal_countAt_exact]
  · funext carrier
    simp only [ActionConditionedCarrierCountDynamics.countAt,
      upperExtremalActionConditionedDynamics, actionConditionedCarrierEnvelope]
    rw [upperExtremal_countAt_exact]

/-- Direct operational formula: after adding the plan, the selected lower
count must exceed every competitor's upper count. -/
def StrictInterventionMargin
    (bounds : CarrierCountFlowBounds)
    (intervention : DeclaredCarrierIntervention)
    (horizon : Nat) (selected : EnterpriseCarrier) : Prop :=
  ∀ other, other ≠ selected →
    bounds.initialUpper other + horizon * bounds.stepUpper other +
        intervention.cumulative horizon other <
      bounds.initialLower selected + horizon * bounds.stepLower selected +
        intervention.cumulative horizon selected

/-- If the declared-action signal exceeds worst-case residual uncertainty,
the selected carrier is forced for every admissible execution. -/
theorem strict_intervention_margin_forces_carrier
    (bounds : CarrierCountFlowBounds)
    (intervention : DeclaredCarrierIntervention)
    (horizon : Nat) (selected : EnterpriseCarrier)
    (margin : StrictInterventionMargin bounds intervention horizon selected) :
    EnvelopeForcesCarrier
      (actionConditionedCarrierEnvelope bounds intervention horizon) selected := by
  apply (envelope_forces_carrier_iff_adversarial_dominant _ _).mpr
  intro other
  by_cases same : other = selected
  · subst other
    exact Or.inr ⟨rfl, Nat.le_refl _⟩
  · left
    simpa [adversarialCarrierProfile, actionConditionedCarrierEnvelope,
      carrierCountFlowEnvelope, same] using margin other same

/-- Exact converse/no-go at the model boundary: if the translated adversarial
corner is not dominant, an admissible profile defeats the proposed carrier. -/
theorem failed_intervention_envelope_has_counterprofile
    (bounds : CarrierCountFlowBounds)
    (intervention : DeclaredCarrierIntervention)
    (horizon : Nat) (selected : EnterpriseCarrier)
    (failure : ¬ OperationallyDominant
      (adversarialCarrierProfile
        (actionConditionedCarrierEnvelope bounds intervention horizon) selected)
      selected) :
    ∃ profile,
      ProfileWithin
        (actionConditionedCarrierEnvelope bounds intervention horizon) profile ∧
      ¬ OperationallyDominant profile selected := by
  apply envelope_failure_has_admissible_counterprofile
  intro forces
  exact failure ((envelope_forces_carrier_iff_adversarial_dominant _ _).mp forces)

/-- Carrier-specific no-go: if two controlled runs have the same passive
observation but distinct carriers, omission of the action caps point accuracy
on the balanced pair at one half. -/
theorem omitted_carrier_intervention_pair_accuracy_at_most_half
    {State Observation : Type}
    (observeWithoutAction : State → Observation)
    (actualCarrier : State → EnterpriseCarrier)
    (predictor : Observation → EnterpriseCarrier)
    (left right : State)
    (samePassive : observeWithoutAction left = observeWithoutAction right)
    (differentCarrier : actualCarrier left ≠ actualCarrier right) :
    ZeroOneCorrect (predictor (observeWithoutAction left)) (actualCarrier left) +
      ZeroOneCorrect (predictor (observeWithoutAction right)) (actualCarrier right) ≤ 1 :=
  omitted_intervention_pair_correct_count_le_one
    observeWithoutAction actualCarrier predictor left right samePassive differentCarrier

/-!
## Executable numerical witnesses

The first registered science plan produced twelve scientific-claim signals and
two capability-realization signals. With a zero residual envelope its strict
margin is ten counts. The companion tie example has zero margin and loses to
the earlier frozen carrier priority.
-/

def zeroCarrierCountFlowBounds : CarrierCountFlowBounds where
  initialLower := fun _ => 0
  initialUpper := fun _ => 0
  stepLower := fun _ => 0
  stepUpper := fun _ => 0
  initialValid := by simp
  stepValid := by simp

def sciencePlanProfile : EnterpriseCarrierCountProfile
  | .capabilityRealization => 2
  | .scientificClaim => 12
  | _ => 0

def sciencePlanIntervention : DeclaredCarrierIntervention where
  occurrenceToken := 2
  validityActive := true
  plannedIncrement := fun t => if t = 0 then sciencePlanProfile else fun _ => 0

theorem sciencePlan_cumulative_one_exact :
    sciencePlanIntervention.cumulative 1 = sciencePlanProfile := by
  funext carrier
  cases carrier <;> simp [sciencePlanIntervention, sciencePlanProfile]

theorem sciencePlan_has_strict_margin_ten :
    StrictInterventionMargin zeroCarrierCountFlowBounds sciencePlanIntervention
      1 .scientificClaim := by
  intro other different
  cases other <;>
    simp [zeroCarrierCountFlowBounds, sciencePlanIntervention, sciencePlanProfile,
      DeclaredCarrierIntervention.cumulative] at different ⊢

theorem sciencePlan_forces_scientificClaim :
    EnvelopeForcesCarrier
      (actionConditionedCarrierEnvelope zeroCarrierCountFlowBounds
        sciencePlanIntervention 1)
      .scientificClaim :=
  strict_intervention_margin_forces_carrier zeroCarrierCountFlowBounds
    sciencePlanIntervention 1 .scientificClaim sciencePlan_has_strict_margin_ten

def tiedSciencePlanProfile : EnterpriseCarrierCountProfile
  | .assetRevision => 1
  | .scientificClaim => 1
  | _ => 0

def tiedSciencePlanIntervention : DeclaredCarrierIntervention where
  occurrenceToken := 99
  validityActive := true
  plannedIncrement := fun t => if t = 0 then tiedSciencePlanProfile else fun _ => 0

theorem zero_margin_scientific_plan_not_forced :
    ¬ EnvelopeForcesCarrier
      (actionConditionedCarrierEnvelope zeroCarrierCountFlowBounds
        tiedSciencePlanIntervention 1)
      .scientificClaim := by
  rw [envelope_forces_carrier_iff_adversarial_dominant]
  intro dominant
  have losesTie := dominant .assetRevision
  simp [adversarialCarrierProfile, actionConditionedCarrierEnvelope,
    carrierCountFlowEnvelope, zeroCarrierCountFlowBounds,
    tiedSciencePlanIntervention, tiedSciencePlanProfile,
    DeclaredCarrierIntervention.cumulative, enterpriseCarrierPriority] at losesTie

/-- K/M composition contract with an explicit run-bound intervention and a
bounded residual process for every tied resolving candidate. -/
structure KMActionConditionedCarrierFlowContract
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {Path : Type uPath}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (observePaths : interpretation.State → List Path)
    (classifier : CertifiedPathCarrierClassifier Path) where
  horizon : Nat
  bounds : CarrierCountFlowBounds
  intervention : DeclaredCarrierIntervention
  active : intervention.validityActive = true
  dynamicsOf : liftSearch.Candidate → ActionConditionedCarrierCountDynamics
  interventionExact : ∀ candidate,
    (dynamicsOf candidate).intervention = intervention
  respects : ∀ candidate, KMTiedResolvingCandidate resolution candidate →
    (dynamicsOf candidate).Respects bounds
  selectedTargetAgreement : ∀ target,
    interpretation.predictiveInterpretation.targetFutureAt
      resolution.selection.minimizer.1 target →
    extractedCarrierProfile classifier.evidence (observePaths target) =
      (dynamicsOf resolution.selection.minimizer.1).countAt horizon

/-- Full positive chain: K/M selection plus an active declared action and a
strict residual-robust margin yields singleton carrier support. -/
theorem km_action_conditioned_flow_yields_singleton_carrier_support
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {Path : Type uPath}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (observePaths : interpretation.State → List Path)
    (classifier : CertifiedPathCarrierClassifier Path)
    (contract : KMActionConditionedCarrierFlowContract resolution interpretation
      observePaths classifier)
    (selectedCarrier : EnterpriseCarrier)
    (margin : StrictInterventionMargin contract.bounds contract.intervention
      contract.horizon selectedCarrier)
    (witnessTarget : interpretation.State)
    (witnessFuture : interpretation.predictiveInterpretation.targetFutureAt
      resolution.selection.minimizer.1 witnessTarget) :
    ∀ carrier,
      KMDerivedEnterpriseCarrierSupport resolution interpretation
        (classifier.toOperationalProjection observePaths).carrier carrier ↔
          carrier = selectedCarrier := by
  apply km_count_envelope_yields_singleton_carrier_support
    resolution interpretation observePaths classifier
      (actionConditionedCarrierEnvelope contract.bounds contract.intervention
        contract.horizon)
      selectedCarrier
      ((envelope_forces_carrier_iff_adversarial_dominant _ _).mp
        (strict_intervention_margin_forces_carrier contract.bounds
          contract.intervention contract.horizon selectedCarrier margin))
      witnessTarget witnessFuture
  intro target future
  rw [contract.selectedTargetAgreement target future]
  have within := ActionConditionedCarrierCountDynamics.countAt_within_envelope
    (contract.dynamicsOf resolution.selection.minimizer.1) contract.bounds
    (contract.respects resolution.selection.minimizer.1
      (selected_is_km_tied_resolving resolution)) contract.horizon
  simpa [contract.interventionExact resolution.selection.minimizer.1] using within

end OCKIndividuationMSpaceComposition
