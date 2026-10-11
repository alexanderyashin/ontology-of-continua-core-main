import OCKIndividuationMSpaceComposition.QuantitativeContinuationReliability

namespace OCKIndividuationMSpaceComposition

/-!
# Finite enterprise-dynamics bridge

This module separates a logical enterprise token from mutable revision,
location, content, and governance projections.  It also states the exact
finite-count estimator used by the executable Logion demonstrator and proves
the prediction/no-go and impact monotonicity results needed to interpret it.
-/

inductive EnterpriseCarrier where
  | assetRevision
  | capabilityRealization
  | commitmentRisk
  | controlDecision
  | deploymentInstance
  | releaseSurface
  | scientificClaim
  | workItemRun
  deriving DecidableEq, Repr, Fintype

/-- A binding record is deliberately multi-surface.  No mutable projection is
declared to be enterprise identity. -/
structure EnterpriseBindingRecord where
  enterpriseToken : Nat
  revisionToken : Nat
  contentDigest : Nat
  locationToken : Nat
  governanceStatus : Nat
  lineageAdmitted : Bool
  scopeActive : Bool
  deriving DecidableEq, Repr

/-- Operational binding needs a shared logical token plus admitted lineage and
active scope at the target occurrence. -/
def BindingAccepted (source target : EnterpriseBindingRecord) : Prop :=
  source.enterpriseToken = target.enterpriseToken ∧
  target.lineageAdmitted = true ∧
  target.scopeActive = true

theorem enterprise_token_alone_not_sufficient :
    ∃ source target : EnterpriseBindingRecord,
      source.enterpriseToken = target.enterpriseToken ∧
      ¬ BindingAccepted source target := by
  let source : EnterpriseBindingRecord := ⟨7, 10, 20, 30, 40, true, true⟩
  let target : EnterpriseBindingRecord := ⟨7, 11, 21, 31, 41, false, true⟩
  refine ⟨source, target, rfl, ?_⟩
  simp [BindingAccepted, target]

theorem mutable_projections_may_change_while_binding_is_preserved :
    ∃ source target : EnterpriseBindingRecord,
      BindingAccepted source target ∧
      source.revisionToken ≠ target.revisionToken ∧
      source.contentDigest ≠ target.contentDigest ∧
      source.locationToken ≠ target.locationToken ∧
      source.governanceStatus ≠ target.governanceStatus := by
  let source : EnterpriseBindingRecord := ⟨7, 10, 20, 30, 40, true, true⟩
  let target : EnterpriseBindingRecord := ⟨7, 11, 21, 31, 41, true, true⟩
  exact ⟨source, target, by simp [BindingAccepted, source, target]⟩

theorem equal_revision_path_and_status_not_sufficient :
    ∃ source target : EnterpriseBindingRecord,
      source.revisionToken = target.revisionToken ∧
      source.locationToken = target.locationToken ∧
      source.governanceStatus = target.governanceStatus ∧
      ¬ BindingAccepted source target := by
  let source : EnterpriseBindingRecord := ⟨7, 10, 20, 30, 40, true, true⟩
  let target : EnterpriseBindingRecord := ⟨8, 10, 99, 30, 40, true, true⟩
  exact ⟨source, target, rfl, rfl, rfl, by simp [BindingAccepted, source, target]⟩

/-- An observation is predictively sufficient exactly when it never collapses
two states having different next-event laws. -/
def PredictivelySufficient {State Observation Law : Type}
    (observe : State → Observation) (nextLaw : State → Law) : Prop :=
  ∀ x y, observe x = observe y → nextLaw x = nextLaw y

theorem collapsed_observation_no_exact_predictor
    {State Observation Law : Type}
    (observe : State → Observation) (nextLaw : State → Law)
    (x y : State)
    (sameObservation : observe x = observe y)
    (differentLaw : nextLaw x ≠ nextLaw y) :
    ¬ ∃ predictor : Observation → Law, ∀ state, predictor (observe state) = nextLaw state := by
  rintro ⟨predictor, exactPrediction⟩
  apply differentLaw
  calc
    nextLaw x = predictor (observe x) := (exactPrediction x).symm
    _ = predictor (observe y) := congrArg predictor sameObservation
    _ = nextLaw y := exactPrediction y

theorem exact_predictor_from_sufficient_observation_and_section
    {State Observation Law : Type}
    (observe : State → Observation) (nextLaw : State → Law)
    (representative : Observation → State)
    (sectionLaw : ∀ state, observe (representative (observe state)) = observe state)
    (sufficient : PredictivelySufficient observe nextLaw) :
    ∃ predictor : Observation → Law, ∀ state, predictor (observe state) = nextLaw state := by
  refine ⟨fun observation => nextLaw (representative observation), ?_⟩
  intro state
  exact sufficient (representative (observe state)) state (sectionLaw state)

/-- A controlled enterprise action declares the next observable outcome before
execution.  The occurrence token binds the declaration to one run rather than
to a mutable path, status, or branch head. -/
structure DeclaredIntervention (Outcome : Type) where
  occurrenceToken : Nat
  plannedOutcome : Outcome
  validityActive : Bool

/-- The action-conditioned predictor is intentionally transparent: it returns
the outcome bound into the active intervention occurrence. -/
def ActionConditionedPredictor {Outcome : Type}
    (intervention : DeclaredIntervention Outcome) : Outcome :=
  intervention.plannedOutcome

def InterventionConformant {Outcome : Type}
    (intervention : DeclaredIntervention Outcome) (actual : Outcome) : Prop :=
  intervention.validityActive = true ∧ actual = intervention.plannedOutcome

theorem action_conditioned_prediction_exact_when_conformant
    {Outcome : Type} (intervention : DeclaredIntervention Outcome) (actual : Outcome)
    (conformant : InterventionConformant intervention actual) :
    ActionConditionedPredictor intervention = actual := by
  exact conformant.2.symm

theorem action_conditioned_error_implies_nonconformance
    {Outcome : Type} (intervention : DeclaredIntervention Outcome) (actual : Outcome)
    (error : ActionConditionedPredictor intervention ≠ actual) :
    ¬ InterventionConformant intervention actual := by
  intro conformant
  exact error (action_conditioned_prediction_exact_when_conformant intervention actual conformant)

/-- Binary point score used for the formal optimum statement. -/
def ZeroOneCorrect {Outcome : Type} [DecidableEq Outcome]
    (predicted actual : Outcome) : Nat :=
  if predicted = actual then 1 else 0

theorem zero_one_correct_never_exceeds_one
    {Outcome : Type} [DecidableEq Outcome] (predicted actual : Outcome) :
    ZeroOneCorrect predicted actual ≤ 1 := by
  unfold ZeroOneCorrect
  split <;> simp

/-- On every conformant action occurrence the declared-action predictor reaches
the pointwise upper bound of the zero-one score.  Therefore no point predictor
can score strictly better on that occurrence. -/
theorem action_conditioned_predictor_is_pointwise_optimal
    {State Outcome : Type} [DecidableEq Outcome]
    (competitor : State → Outcome) (state : State)
    (intervention : DeclaredIntervention Outcome) (actual : Outcome)
    (conformant : InterventionConformant intervention actual) :
    ZeroOneCorrect (competitor state) actual ≤
      ZeroOneCorrect (ActionConditionedPredictor intervention) actual := by
  rw [action_conditioned_prediction_exact_when_conformant intervention actual conformant]
  simpa [ZeroOneCorrect] using zero_one_correct_never_exceeds_one (competitor state) actual

/-- If omission of the intervention collapses two controlled states with
different outcomes, no predictor on the reduced observation can be exact. -/
theorem omitted_intervention_no_exact_predictor
    {State Observation Outcome : Type}
    (observeWithoutAction : State → Observation) (actualOutcome : State → Outcome)
    (left right : State)
    (sameReducedObservation : observeWithoutAction left = observeWithoutAction right)
    (differentOutcome : actualOutcome left ≠ actualOutcome right) :
    ¬ ∃ predictor : Observation → Outcome,
      ∀ state, predictor (observeWithoutAction state) = actualOutcome state :=
  collapsed_observation_no_exact_predictor
    observeWithoutAction actualOutcome left right sameReducedObservation differentOutcome

/-- Quantitative form of the omitted-intervention no-go result.  On two
equally weighted states that the reduced observation identifies but whose
outcomes differ, every point predictor is correct on at most one state.  Hence
its empirical accuracy on that pair is at most `1 / 2`. -/
theorem omitted_intervention_pair_correct_count_le_one
    {State Observation Outcome : Type} [DecidableEq Outcome]
    (observeWithoutAction : State → Observation) (actualOutcome : State → Outcome)
    (predictor : Observation → Outcome) (left right : State)
    (sameReducedObservation : observeWithoutAction left = observeWithoutAction right)
    (differentOutcome : actualOutcome left ≠ actualOutcome right) :
    ZeroOneCorrect (predictor (observeWithoutAction left)) (actualOutcome left) +
        ZeroOneCorrect (predictor (observeWithoutAction right)) (actualOutcome right) ≤ 1 := by
  rw [sameReducedObservation]
  by_cases predictsLeft : predictor (observeWithoutAction right) = actualOutcome left
  · have notRight : predictor (observeWithoutAction right) ≠ actualOutcome right := by
      intro predictsRight
      exact differentOutcome (predictsLeft.symm.trans predictsRight)
    unfold ZeroOneCorrect
    rw [if_pos predictsLeft, if_neg notRight]
  · unfold ZeroOneCorrect
    rw [if_neg predictsLeft]
    split <;> simp

/-- Add-alpha mass used by the finite typed transition estimator. -/
def SmoothedTransitionMass {n : Nat}
    (counts : Fin n → Fin n → Nat) (alpha : Nat) (source target : Fin n) : Nat :=
  counts source target + alpha

def SmoothedTransitionDenominator {n : Nat}
    (counts : Fin n → Fin n → Nat) (alpha : Nat) (source : Fin n) : Nat :=
  (∑ target, counts source target) + Fintype.card (Fin n) * alpha

theorem smoothed_transition_row_mass_exact {n : Nat}
    (counts : Fin n → Fin n → Nat) (alpha : Nat) (source : Fin n) :
    (∑ target, SmoothedTransitionMass counts alpha source target) =
      SmoothedTransitionDenominator counts alpha source := by
  simp [SmoothedTransitionMass, SmoothedTransitionDenominator, Finset.sum_add_distrib]

theorem smoothed_transition_denominator_positive {n : Nat}
    (counts : Fin (n + 1) → Fin (n + 1) → Nat) (alpha : Nat)
    (source : Fin (n + 1)) (alphaPositive : 0 < alpha) :
    0 < SmoothedTransitionDenominator counts alpha source := by
  simp only [SmoothedTransitionDenominator, Fintype.card_fin]
  exact Nat.add_pos_right _ (Nat.mul_pos (Nat.succ_pos n) alphaPositive)

/-- Exact event-horizon currentness survival mass under a declared stationary
per-event survival numerator and denominator. -/
def HorizonSurvivalNumerator (singleEventSurvival : Nat) (horizon : Nat) : Nat :=
  singleEventSurvival ^ horizon

def HorizonSurvivalDenominator (denominator : Nat) (horizon : Nat) : Nat :=
  denominator ^ horizon

theorem head_sha_has_zero_currentness_survival_after_next_revision
    (horizon : Nat) (positiveHorizon : 0 < horizon) :
    HorizonSurvivalNumerator 0 horizon = 0 := by
  simp [HorizonSurvivalNumerator, Nat.ne_of_gt positiveHorizon]

/-- Finite nonnegative impact propagation.  The cumulative term is retained,
so impact cannot disappear merely by increasing the forecast horizon. -/
def PropagatedImpact {n : Nat}
    (weight : Fin n → Fin n → Nat) : Nat → (Fin n → Nat) → Fin n → Nat
  | 0, seed => seed
  | horizon + 1, seed => fun target =>
      PropagatedImpact weight horizon seed target +
        ∑ source, PropagatedImpact weight horizon seed source * weight source target

theorem propagated_impact_monotone_in_horizon {n : Nat}
    (weight : Fin n → Fin n → Nat) (horizon : Nat)
    (seed : Fin n → Nat) (target : Fin n) :
    PropagatedImpact weight horizon seed target ≤
      PropagatedImpact weight (horizon + 1) seed target := by
  simp only [PropagatedImpact]
  exact Nat.le_add_right _ _

def ExpectedRepairWorkNumerator (riskNumerator repairWork : Nat) : Nat :=
  riskNumerator * repairWork

theorem expected_repair_work_monotone_in_cost
    (riskNumerator lowCost highCost : Nat) (costOrder : lowCost ≤ highCost) :
    ExpectedRepairWorkNumerator riskNumerator lowCost ≤
      ExpectedRepairWorkNumerator riskNumerator highCost := by
  exact Nat.mul_le_mul_left riskNumerator costOrder

/-- Governance responsibility is an explicit institutional projection, not a
corollary of object binding. -/
structure AccountabilityAdapter where
  responsibleParty : EnterpriseBindingRecord → Nat
  acceptsTransfer : EnterpriseBindingRecord → EnterpriseBindingRecord → Prop

theorem binding_does_not_determine_accountability_adapter :
    ∃ record : EnterpriseBindingRecord, ∃ left right : AccountabilityAdapter,
      BindingAccepted record record ∧
      left.responsibleParty record ≠ right.responsibleParty record := by
  let record : EnterpriseBindingRecord := ⟨7, 10, 20, 30, 40, true, true⟩
  let left : AccountabilityAdapter := ⟨fun _ => 1, fun _ _ => True⟩
  let right : AccountabilityAdapter := ⟨fun _ => 2, fun _ _ => True⟩
  exact ⟨record, left, right, by simp [BindingAccepted, record, left, right]⟩

end OCKIndividuationMSpaceComposition
