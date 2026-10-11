import OCKIndividuationMSpaceComposition.KMEnterpriseCountEnvelope
import OCKIndividuationMSpaceComposition.KMOperatorCycleFlowPrediction

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe uPath uLiftCarrier uLiftCandidate uRepairCandidate

/-!
# K/M operator-flow to enterprise carrier-count envelopes

This is the vector-valued Nat-count adapter for the existing scalar OC
stock-flow theorem.  Each coordinate is one enterprise carrier.  Uniform
initial and per-step bounds generate a finite-horizon rectangular envelope;
both endpoints are attained by explicit dynamics, so no uniformly tighter
coordinate bound follows from the same premises.
-/

structure CarrierCountDynamics where
  initial : EnterpriseCarrierCountProfile
  increment : ℕ → EnterpriseCarrierCountProfile

def CarrierCountDynamics.countAt
    (dynamics : CarrierCountDynamics) : ℕ → EnterpriseCarrierCountProfile
  | 0 => dynamics.initial
  | horizon + 1 => fun carrier =>
      dynamics.countAt horizon carrier + dynamics.increment horizon carrier

@[simp] theorem CarrierCountDynamics.countAt_zero
    (dynamics : CarrierCountDynamics) :
    dynamics.countAt 0 = dynamics.initial := rfl

@[simp] theorem CarrierCountDynamics.countAt_succ
    (dynamics : CarrierCountDynamics) (horizon : ℕ)
    (carrier : EnterpriseCarrier) :
    dynamics.countAt (horizon + 1) carrier =
      dynamics.countAt horizon carrier + dynamics.increment horizon carrier := rfl

structure CarrierCountFlowBounds where
  initialLower : EnterpriseCarrierCountProfile
  initialUpper : EnterpriseCarrierCountProfile
  stepLower : EnterpriseCarrierCountProfile
  stepUpper : EnterpriseCarrierCountProfile
  initialValid : ∀ carrier, initialLower carrier ≤ initialUpper carrier
  stepValid : ∀ carrier, stepLower carrier ≤ stepUpper carrier

def CarrierCountDynamics.Respects
    (dynamics : CarrierCountDynamics) (bounds : CarrierCountFlowBounds) : Prop :=
  (∀ carrier,
    bounds.initialLower carrier ≤ dynamics.initial carrier ∧
      dynamics.initial carrier ≤ bounds.initialUpper carrier) ∧
  ∀ t carrier,
    bounds.stepLower carrier ≤ dynamics.increment t carrier ∧
      dynamics.increment t carrier ≤ bounds.stepUpper carrier

def carrierCountFlowEnvelope
    (bounds : CarrierCountFlowBounds) (horizon : ℕ) : CarrierCountEnvelope where
  lower carrier := bounds.initialLower carrier + horizon * bounds.stepLower carrier
  upper carrier := bounds.initialUpper carrier + horizon * bounds.stepUpper carrier
  valid carrier := by
    exact Nat.add_le_add (bounds.initialValid carrier)
      (Nat.mul_le_mul_left horizon (bounds.stepValid carrier))

/-- Per-step carrier flow bounds generate the claimed finite-horizon count
envelope. -/
theorem CarrierCountDynamics.countAt_within_flowEnvelope
    (dynamics : CarrierCountDynamics) (bounds : CarrierCountFlowBounds)
    (respects : dynamics.Respects bounds) (horizon : ℕ) :
    ProfileWithin (carrierCountFlowEnvelope bounds horizon)
      (dynamics.countAt horizon) := by
  intro carrier
  induction horizon with
  | zero => simpa [carrierCountFlowEnvelope] using respects.1 carrier
  | succ horizon inductionHypothesis =>
      have stepBounds := respects.2 horizon carrier
      constructor
      · calc
          bounds.initialLower carrier + (horizon + 1) * bounds.stepLower carrier =
              (bounds.initialLower carrier + horizon * bounds.stepLower carrier) +
                bounds.stepLower carrier := by ring
          _ ≤ dynamics.countAt horizon carrier + dynamics.increment horizon carrier :=
              Nat.add_le_add inductionHypothesis.1 stepBounds.1
          _ = dynamics.countAt (horizon + 1) carrier := rfl
      · calc
          dynamics.countAt (horizon + 1) carrier =
              dynamics.countAt horizon carrier + dynamics.increment horizon carrier := rfl
          _ ≤ (bounds.initialUpper carrier + horizon * bounds.stepUpper carrier) +
                bounds.stepUpper carrier :=
              Nat.add_le_add inductionHypothesis.2 stepBounds.2
          _ = bounds.initialUpper carrier + (horizon + 1) * bounds.stepUpper carrier := by ring

def lowerExtremalCarrierCountDynamics
    (bounds : CarrierCountFlowBounds) : CarrierCountDynamics where
  initial := bounds.initialLower
  increment := fun _ => bounds.stepLower

def upperExtremalCarrierCountDynamics
    (bounds : CarrierCountFlowBounds) : CarrierCountDynamics where
  initial := bounds.initialUpper
  increment := fun _ => bounds.stepUpper

theorem lowerExtremal_respects (bounds : CarrierCountFlowBounds) :
    (lowerExtremalCarrierCountDynamics bounds).Respects bounds := by
  constructor
  · intro carrier
    exact ⟨Nat.le_refl _, bounds.initialValid carrier⟩
  · intro t carrier
    exact ⟨Nat.le_refl _, bounds.stepValid carrier⟩

theorem upperExtremal_respects (bounds : CarrierCountFlowBounds) :
    (upperExtremalCarrierCountDynamics bounds).Respects bounds := by
  constructor
  · intro carrier
    exact ⟨bounds.initialValid carrier, Nat.le_refl _⟩
  · intro t carrier
    exact ⟨bounds.stepValid carrier, Nat.le_refl _⟩

theorem lowerExtremal_countAt_exact
    (bounds : CarrierCountFlowBounds) (horizon : ℕ)
    (carrier : EnterpriseCarrier) :
    (lowerExtremalCarrierCountDynamics bounds).countAt horizon carrier =
      (carrierCountFlowEnvelope bounds horizon).lower carrier := by
  induction horizon with
  | zero => simp [lowerExtremalCarrierCountDynamics, carrierCountFlowEnvelope]
  | succ horizon inductionHypothesis =>
      rw [CarrierCountDynamics.countAt_succ, inductionHypothesis]
      simp [lowerExtremalCarrierCountDynamics, carrierCountFlowEnvelope]
      ring

theorem upperExtremal_countAt_exact
    (bounds : CarrierCountFlowBounds) (horizon : ℕ)
    (carrier : EnterpriseCarrier) :
    (upperExtremalCarrierCountDynamics bounds).countAt horizon carrier =
      (carrierCountFlowEnvelope bounds horizon).upper carrier := by
  induction horizon with
  | zero => simp [upperExtremalCarrierCountDynamics, carrierCountFlowEnvelope]
  | succ horizon inductionHypothesis =>
      rw [CarrierCountDynamics.countAt_succ, inductionHypothesis]
      simp [upperExtremalCarrierCountDynamics, carrierCountFlowEnvelope]
      ring

/-- Sharpness of the generated envelope: both coordinatewise endpoints are
attained by admissible flow dynamics. -/
theorem carrierCountFlowEnvelope_endpoints_attainable
    (bounds : CarrierCountFlowBounds) (horizon : ℕ) :
    ∃ lowerDynamics upperDynamics : CarrierCountDynamics,
      lowerDynamics.Respects bounds ∧ upperDynamics.Respects bounds ∧
      lowerDynamics.countAt horizon = (carrierCountFlowEnvelope bounds horizon).lower ∧
      upperDynamics.countAt horizon = (carrierCountFlowEnvelope bounds horizon).upper := by
  refine ⟨lowerExtremalCarrierCountDynamics bounds,
    upperExtremalCarrierCountDynamics bounds, lowerExtremal_respects bounds,
    upperExtremal_respects bounds, ?_, ?_⟩
  · funext carrier
    exact lowerExtremal_countAt_exact bounds horizon carrier
  · funext carrier
    exact upperExtremal_countAt_exact bounds horizon carrier

/-- No strictly larger universal lower bound can be inferred from the same
flow premises. -/
theorem stricter_lower_bound_has_admissible_counterdynamics
    (bounds : CarrierCountFlowBounds) (horizon : ℕ)
    (carrier : EnterpriseCarrier) (claimedLower : ℕ)
    (strict : (carrierCountFlowEnvelope bounds horizon).lower carrier < claimedLower) :
    ∃ dynamics : CarrierCountDynamics,
      dynamics.Respects bounds ∧ dynamics.countAt horizon carrier < claimedLower := by
  exact ⟨lowerExtremalCarrierCountDynamics bounds, lowerExtremal_respects bounds,
    lowerExtremal_countAt_exact bounds horizon carrier ▸ strict⟩

/-- No strictly smaller universal upper bound can be inferred either. -/
theorem stricter_upper_bound_has_admissible_counterdynamics
    (bounds : CarrierCountFlowBounds) (horizon : ℕ)
    (carrier : EnterpriseCarrier) (claimedUpper : ℕ)
    (strict : claimedUpper < (carrierCountFlowEnvelope bounds horizon).upper carrier) :
    ∃ dynamics : CarrierCountDynamics,
      dynamics.Respects bounds ∧ claimedUpper < dynamics.countAt horizon carrier := by
  exact ⟨upperExtremalCarrierCountDynamics bounds, upperExtremal_respects bounds,
    upperExtremal_countAt_exact bounds horizon carrier ▸ strict⟩

/-- Common carrier-count dynamics and observation agreement for every tied K/M
model. -/
structure KMTiedCarrierCountFlowContract
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
  horizon : ℕ
  bounds : CarrierCountFlowBounds
  dynamicsOf : liftSearch.Candidate → CarrierCountDynamics
  respects : ∀ candidate, KMTiedResolvingCandidate resolution candidate →
    (dynamicsOf candidate).Respects bounds
  selectedTargetAgreement : ∀ target,
    interpretation.predictiveInterpretation.targetFutureAt
      resolution.selection.minimizer.1 target →
    extractedCarrierProfile classifier.evidence (observePaths target) =
      (dynamicsOf resolution.selection.minimizer.1).countAt horizon

/-- End-to-end generative composition: K/M flow premises yield a sharp count
envelope; a dominant adversarial corner then forces singleton enterprise
carrier support. -/
theorem km_count_flow_contract_yields_singleton_carrier_support
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
    (contract : KMTiedCarrierCountFlowContract resolution interpretation
      observePaths classifier)
    (selectedCarrier : EnterpriseCarrier)
    (cornerDominant : OperationallyDominant
      (adversarialCarrierProfile
        (carrierCountFlowEnvelope contract.bounds contract.horizon)
        selectedCarrier) selectedCarrier)
    (witnessTarget : interpretation.State)
    (witnessFuture : interpretation.predictiveInterpretation.targetFutureAt
      resolution.selection.minimizer.1 witnessTarget) :
    ∀ carrier,
      KMDerivedEnterpriseCarrierSupport resolution interpretation
        (classifier.toOperationalProjection observePaths).carrier carrier ↔
          carrier = selectedCarrier := by
  apply km_count_envelope_yields_singleton_carrier_support
    resolution interpretation observePaths classifier
      (carrierCountFlowEnvelope contract.bounds contract.horizon)
      selectedCarrier cornerDominant witnessTarget witnessFuture
  intro target future
  rw [contract.selectedTargetAgreement target future]
  exact CarrierCountDynamics.countAt_within_flowEnvelope
    (contract.dynamicsOf resolution.selection.minimizer.1) contract.bounds
    (contract.respects resolution.selection.minimizer.1
      (selected_is_km_tied_resolving resolution)) contract.horizon

end OCKIndividuationMSpaceComposition
