import OCKIndividuationMSpaceComposition.OC14SemanticKernel
import OCKIndividuationMSpaceComposition.BlackwellAliasCorrespondence

namespace OCKIndividuationMSpaceComposition

/-!
# Finite POMDP-support correspondence and the path-sufficiency boundary

The physical and epistemic one-step M-spaces have a precise mature-theory
reading.  The physical space is the support of the controlled one-step
transition relation.  With a fully expressive state-indexed model class, the
epistemic space is exactly the prior support intersected with the fibre of the
actual deterministic observation: the support update of a deterministic
finite POMDP observation kernel.

The correspondence is deliberately conditional.  If a governance or
continuation decision depends on path information omitted from the endpoint
state, endpoint belief support cannot recover it.  The obstruction disappears
when the state is augmented by an admission-sufficient path statistic.  Thus
the result locates the exact modelling obligation instead of claiming that
POMDP semantics is either universally sufficient or universally inadequate.
-/

universe uWorld uInput uSummary uHistory

/-- Support of the controlled one-step transition relation from `current`. -/
def ControlledReachableSupport
    {World : Type uWorld} {Input : Type uInput}
    (transition : World → Input → World → Prop) (current : World) : Set World :=
  {next | ∃ input, transition current input next}

/-- Deterministic posterior support: prior-supported states observationally
aliased with the actual state. -/
def DeterministicBeliefSupport
    {World : Type uWorld}
    (optic : TaskConditionedOptic World)
    (priorSupport : Set World)
    (actual : World) : Set World :=
  {world | world ∈ priorSupport ∧ optic.observe world = optic.observe actual}

/-- The physical OC one-step M-space is exactly controlled reachability
support.  This is an equality of definitions, recorded as a public adapter. -/
theorem physical_mspace_eq_controlled_reachable_support
    {World : Type uWorld} {Input : Type uInput}
    (transition : World → Input → World → Prop) (current : World) :
    PhysicalContinuationSet transition current =
      ControlledReachableSupport transition current := by
  rfl

/-- With one model per world and a prior given directly as world support, the
OC epistemic M-space is exactly deterministic POMDP belief support. -/
theorem epistemic_mspace_eq_deterministic_belief_support
    {World : Type uWorld}
    (optic : TaskConditionedOptic World)
    (priorSupport : Set World)
    (actual : World) :
    EpistemicContinuationSet optic id (fun world => world ∈ priorSupport) actual =
      DeterministicBeliefSupport optic priorSupport actual := by
  ext world
  simp [EpistemicContinuationSet, OpticPosteriorAdmits,
    DeterministicBeliefSupport]

/-- The exact two-coordinate support state supplied by the correspondence. -/
structure POMDPSupportSnapshot (World : Type uWorld) where
  reachableSupport : Set World
  beliefSupport : Set World

/-- Canonical support snapshot generated from an OC transition law, optic and
prior support. -/
def ocPOMDPSupportSnapshot
    {World : Type uWorld} {Input : Type uInput}
    (transition : World → Input → World → Prop)
    (optic : TaskConditionedOptic World)
    (priorSupport : Set World)
    (current actual : World) : POMDPSupportSnapshot World where
  reachableSupport := PhysicalContinuationSet transition current
  beliefSupport := EpistemicContinuationSet optic id
    (fun world => world ∈ priorSupport) actual

/-- Both coordinates of the canonical snapshot have their exact support
interpretation simultaneously. -/
theorem oc_pomdp_support_snapshot_exact
    {World : Type uWorld} {Input : Type uInput}
    (transition : World → Input → World → Prop)
    (optic : TaskConditionedOptic World)
    (priorSupport : Set World)
    (current actual : World) :
    (ocPOMDPSupportSnapshot transition optic priorSupport current actual).reachableSupport =
        ControlledReachableSupport transition current ∧
      (ocPOMDPSupportSnapshot transition optic priorSupport current actual).beliefSupport =
        DeterministicBeliefSupport optic priorSupport actual := by
  exact ⟨physical_mspace_eq_controlled_reachable_support transition current,
    epistemic_mspace_eq_deterministic_belief_support optic priorSupport actual⟩

/-! ## Exact sufficiency criterion for path-sensitive decisions -/

/-- A summary is admission-sufficient exactly when admission factors through
that summary.  This is the deterministic decision-relevant sufficiency notion
needed by the endpoint-state boundary below. -/
def AdmissionSufficient
    {History : Type uHistory} {Summary : Type uSummary}
    (summary : History → Summary) (admit : History → Bool) : Prop :=
  ∃ decode : Summary → Bool, ∀ history, decode (summary history) = admit history

/-- Any collision of the proposed summary carrying different admission labels
is a formal obstruction to sufficiency. -/
theorem summary_collision_with_different_admission_is_not_sufficient
    {History : Type uHistory} {Summary : Type uSummary}
    (summary : History → Summary) (admit : History → Bool)
    (left right : History)
    (sameSummary : summary left = summary right)
    (differentAdmission : admit left ≠ admit right) :
    ¬ AdmissionSufficient summary admit := by
  rintro ⟨decode, recovers⟩
  apply differentAdmission
  rw [← recovers left, ← recovers right, sameSummary]

/-- A minimal path record: the endpoint and whether the path crossed a
requalification trigger. -/
structure TriggeredPath (Endpoint : Type uWorld) where
  endpoint : Endpoint
  crossedTrigger : Bool
  deriving DecidableEq

/-- Governance admission in the minimal countermodel: an otherwise identical
path is admitted exactly when no trigger was crossed. -/
def triggerFreeAdmission {Endpoint : Type uWorld}
    (history : TriggeredPath Endpoint) : Bool :=
  !history.crossedTrigger

/-- Endpoint-only state is insufficient for a path-sensitive decision.  Two
histories can have the same endpoint and therefore the same singleton belief
support, while one is admitted and the other requires requalification. -/
theorem endpoint_belief_support_is_not_admission_sufficient :
    ∃ (clean triggered : TriggeredPath Bool),
      ({clean.endpoint} : Set Bool) = {triggered.endpoint} ∧
      triggerFreeAdmission clean ≠ triggerFreeAdmission triggered ∧
      ¬ AdmissionSufficient
        (fun history : TriggeredPath Bool => ({history.endpoint} : Set Bool))
        triggerFreeAdmission := by
  let clean : TriggeredPath Bool := ⟨false, false⟩
  let triggered : TriggeredPath Bool := ⟨false, true⟩
  refine ⟨clean, triggered, rfl, by decide, ?_⟩
  exact summary_collision_with_different_admission_is_not_sufficient
    (fun history : TriggeredPath Bool => ({history.endpoint} : Set Bool))
    triggerFreeAdmission clean triggered rfl (by decide)

/-- The obstruction is representation-relative, not absolute: augmenting the
state with the one-bit trigger statistic is sufficient and exactly recovers
the path-sensitive admission decision. -/
theorem endpoint_plus_trigger_is_admission_sufficient :
    AdmissionSufficient
      (fun history : TriggeredPath Bool =>
        (history.endpoint, history.crossedTrigger))
      triggerFreeAdmission := by
  refine ⟨fun summary => !summary.2, ?_⟩
  intro history
  rfl

/-- Exact conditional boundary: endpoint support cannot carry the decision in
the countermodel, whereas the explicitly augmented state can. -/
theorem path_sensitive_admission_requires_sufficient_state_augmentation :
    (¬ AdmissionSufficient
      (fun history : TriggeredPath Bool => ({history.endpoint} : Set Bool))
      triggerFreeAdmission) ∧
    AdmissionSufficient
      (fun history : TriggeredPath Bool =>
        (history.endpoint, history.crossedTrigger))
      triggerFreeAdmission := by
  constructor
  · rcases endpoint_belief_support_is_not_admission_sufficient with
      ⟨_clean, _triggered, _sameEndpoint, _differentAdmission, obstruction⟩
    exact obstruction
  · exact endpoint_plus_trigger_is_admission_sufficient

/-! ## Exact decision-theoretic value of the missing path bit -/

/-- On the explicit equal-weight clean/triggered challenge, endpoint-only
observation has exact deterministic Bayes risk `1/2`. -/
theorem endpoint_only_path_admission_exact_bayes_risk :
    ∃ witness : OptimalRiskWitness
        (twoWorldChallengeRisk
          (fun history : TriggeredPath Bool => history.endpoint)
          triggerFreeAdmission
          (⟨false, false⟩ : TriggeredPath Bool)
          (⟨false, true⟩ : TriggeredPath Bool))
        (Set.univ : Set (Bool → Bool)),
      witness.value = (1 : ℝ) / 2 := by
  exact aliased_two_world_challenge_exact_bayes_risk
    (fun history : TriggeredPath Bool => history.endpoint)
    triggerFreeAdmission
    (⟨false, false⟩ : TriggeredPath Bool)
    (⟨false, true⟩ : TriggeredPath Bool)
    rfl
    (by decide)

/-- Adding the trigger bit separates the same pair and attains zero error. -/
theorem augmented_path_admission_zero_risk :
    ∃ predict : (Bool × Bool) → Bool,
      twoWorldChallengeRisk
        (fun history : TriggeredPath Bool =>
          (history.endpoint, history.crossedTrigger))
        triggerFreeAdmission
        (⟨false, false⟩ : TriggeredPath Bool)
        (⟨false, true⟩ : TriggeredPath Bool)
        predict = 0 := by
  exact separated_two_world_challenge_zero_is_attainable
    (fun history : TriggeredPath Bool =>
      (history.endpoint, history.crossedTrigger))
    triggerFreeAdmission
    (⟨false, false⟩ : TriggeredPath Bool)
    (⟨false, true⟩ : TriggeredPath Bool)
    (by decide)

/-- Exact numerical prediction: on the declared balanced collision challenge,
the missing path bit has gross zero-one decision value `1/2`. -/
theorem trigger_path_bit_has_exact_half_challenge_value :
    ∃ endpointWitness : OptimalRiskWitness
        (twoWorldChallengeRisk
          (fun history : TriggeredPath Bool => history.endpoint)
          triggerFreeAdmission
          (⟨false, false⟩ : TriggeredPath Bool)
          (⟨false, true⟩ : TriggeredPath Bool))
        (Set.univ : Set (Bool → Bool)),
      ∃ augmentedPredict : (Bool × Bool) → Bool,
        endpointWitness.value = (1 : ℝ) / 2 ∧
        twoWorldChallengeRisk
          (fun history : TriggeredPath Bool =>
            (history.endpoint, history.crossedTrigger))
          triggerFreeAdmission
          (⟨false, false⟩ : TriggeredPath Bool)
          (⟨false, true⟩ : TriggeredPath Bool)
          augmentedPredict = 0 ∧
        endpointWitness.value -
          twoWorldChallengeRisk
            (fun history : TriggeredPath Bool =>
              (history.endpoint, history.crossedTrigger))
            triggerFreeAdmission
            (⟨false, false⟩ : TriggeredPath Bool)
            (⟨false, true⟩ : TriggeredPath Bool)
            augmentedPredict = (1 : ℝ) / 2 := by
  exact separated_origin_information_has_exact_half_challenge_value
    (fun history : TriggeredPath Bool => history.endpoint)
    (fun history : TriggeredPath Bool =>
      (history.endpoint, history.crossedTrigger))
    triggerFreeAdmission
    (⟨false, false⟩ : TriggeredPath Bool)
    (⟨false, true⟩ : TriggeredPath Bool)
    rfl
    (by decide)
    (by decide)

end OCKIndividuationMSpaceComposition
