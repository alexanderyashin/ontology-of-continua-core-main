import OCKIndividuationMSpaceComposition.SemanticPredictionContract

namespace OCKIndividuationMSpaceComposition

/-!
# Context-compatible requalification transport

A requalification trigger is an operator with its own empirical support.  It
does not propagate merely because the target quantity or predictor family has
the same name.  The target information context must carry explicit evidence
that the trigger is non-inferior to the base policy both on aggregate loss and
on the registered lower-tail safety order.
-/

/-- The semantic context in which a requalification operator is evaluated. -/
structure RequalificationContext where
  meaning : PredictionMeaning
  informationSetId : String
  evidencePolicyId : String
  deriving DecidableEq

namespace RequalificationContext

theorem ne_of_informationSetId_ne
    {first second : RequalificationContext}
    (different : first.informationSetId ≠ second.informationSetId) :
    first ≠ second := by
  intro equal
  apply different
  simpa [equal]

end RequalificationContext

/-- Gate evidence for transporting a trigger into one target context.
Lower aggregate loss is better; higher worst-block skill is better. -/
structure RequalificationGateEvidence (Loss Safety : Type*) where
  baseAggregateLoss : Loss
  triggerAggregateLoss : Loss
  baseWorstBlockSkill : Safety
  triggerWorstBlockSkill : Safety

/-- The minimal OC adapter contract used by the hydraulic repair. -/
def TriggerTransportAdmitted
    {Loss Safety : Type*} [LE Loss] [LE Safety]
    (evidence : RequalificationGateEvidence Loss Safety) : Prop :=
  evidence.triggerAggregateLoss ≤ evidence.baseAggregateLoss ∧
    evidence.baseWorstBlockSkill ≤ evidence.triggerWorstBlockSkill

/-- Positive theorem: explicit aggregate and tail compatibility admit trigger
transport. -/
theorem trigger_transport_admitted_of_gate_compatibility
    {Loss Safety : Type*} [LE Loss] [LE Safety]
    (evidence : RequalificationGateEvidence Loss Safety)
    (aggregateCompatible :
      evidence.triggerAggregateLoss ≤ evidence.baseAggregateLoss)
    (tailCompatible :
      evidence.baseWorstBlockSkill ≤ evidence.triggerWorstBlockSkill) :
    TriggerTransportAdmitted evidence :=
  ⟨aggregateCompatible, tailCompatible⟩

/-- No-go: aggregate degradation blocks transport even if every other semantic
coordinate happens to match. -/
theorem aggregate_incompatibility_blocks_trigger_transport
    {Loss Safety : Type*} [LE Loss] [LE Safety]
    (evidence : RequalificationGateEvidence Loss Safety)
    (aggregateIncompatible :
      ¬ evidence.triggerAggregateLoss ≤ evidence.baseAggregateLoss) :
    ¬ TriggerTransportAdmitted evidence := by
  intro admitted
  exact aggregateIncompatible admitted.1

/-- No-go: tail degradation independently blocks transport. -/
theorem tail_incompatibility_blocks_trigger_transport
    {Loss Safety : Type*} [LE Loss] [LE Safety]
    (evidence : RequalificationGateEvidence Loss Safety)
    (tailIncompatible :
      ¬ evidence.baseWorstBlockSkill ≤ evidence.triggerWorstBlockSkill) :
    ¬ TriggerTransportAdmitted evidence := by
  intro admitted
  exact tailIncompatible admitted.2

/-- Explicit countermodel to unconditional operator propagation: equal target
meaning does not force a harmful trigger to be transportable. -/
theorem same_prediction_meaning_does_not_imply_trigger_transport :
    let source : RequalificationContext := {
      meaning := diagnosticMeaning
      informationSetId := "full-profile"
      evidencePolicyId := "gate-v1"
    }
    let target : RequalificationContext := {
      meaning := diagnosticMeaning
      informationSetId := "sensor-history-only"
      evidencePolicyId := "gate-v1"
    }
    let harmful : RequalificationGateEvidence Nat Nat := {
      baseAggregateLoss := 1
      triggerAggregateLoss := 2
      baseWorstBlockSkill := 1
      triggerWorstBlockSkill := 0
    }
    source.meaning = target.meaning ∧
      source ≠ target ∧
      ¬ TriggerTransportAdmitted harmful := by
  dsimp
  constructor
  · rfl
  constructor
  · exact RequalificationContext.ne_of_informationSetId_ne (by decide)
  · intro admitted
    have impossible : ¬ (2 : Nat) ≤ 1 := by decide
    exact impossible admitted.1

/-- Aggregate improvement by itself is not a tail-risk guarantee.  This finite
countermodel is the formal reason the laboratory registers both coordinates. -/
theorem positive_aggregate_skill_does_not_imply_worst_floor :
    (0 : Int) < 1 ∧ ¬ ((-1 : Int) ≤ -2) := by
  decide

/-- A two-coordinate empirical acceptance surface. -/
def MeetsAggregateAndWorstFloor
    {Score : Type*} [LT Score] [LE Score]
    (zero worstFloor aggregateSkill worstSkill : Score) : Prop :=
  zero < aggregateSkill ∧ worstFloor ≤ worstSkill

theorem meets_aggregate_and_worst_floor
    {Score : Type*} [LT Score] [LE Score]
    (zero worstFloor aggregateSkill worstSkill : Score)
    (aggregatePositive : zero < aggregateSkill)
    (worstQualified : worstFloor ≤ worstSkill) :
    MeetsAggregateAndWorstFloor zero worstFloor aggregateSkill worstSkill :=
  ⟨aggregatePositive, worstQualified⟩

/-! ## Typed risk vectors

The hydraulic transition experiment exposes a stricter requirement than an
untyped temporal lower tail.  Every semantically registered critical context
is a separate risk coordinate. -/

/-- A candidate transports only when it is no worse than the base policy on
every registered typed risk coordinate.  Lower risk is better. -/
def TypedRiskTransportAdmitted
    {Context Score : Type*} [LE Score]
    (baseRisk candidateRisk : Context → Score) : Prop :=
  ∀ context, candidateRisk context ≤ baseRisk context

/-- Positive theorem: coordinatewise risk non-inferiority is sufficient for
typed transport admission. -/
theorem typed_risk_transport_admitted_of_coordinatewise_compatibility
    {Context Score : Type*} [LE Score]
    (baseRisk candidateRisk : Context → Score)
    (compatible : ∀ context, candidateRisk context ≤ baseRisk context) :
    TypedRiskTransportAdmitted baseRisk candidateRisk :=
  compatible

/-- No-go: one degraded registered context blocks typed transport, regardless
of performance on all other coordinates. -/
theorem one_context_incompatibility_blocks_typed_risk_transport
    {Context Score : Type*} [LE Score]
    (baseRisk candidateRisk : Context → Score)
    (context : Context)
    (incompatible : ¬ candidateRisk context ≤ baseRisk context) :
    ¬ TypedRiskTransportAdmitted baseRisk candidateRisk := by
  intro admitted
  exact incompatible (admitted context)

/-- The three coordinates distinguished by the current hydraulic mechanism
test.  Domain adapters may refine this finite family. -/
inductive HydraulicRiskCoordinate where
  | aggregate
  | temporalTail
  | transitionSubgroup
  deriving DecidableEq

/-- Finite countermodel: aggregate and an untyped temporal tail can both be
compatible while a transition subgroup is harmed.  Therefore the old pair of
coordinates cannot imply typed transition safety. -/
theorem aggregate_and_temporal_tail_do_not_imply_transition_safety :
    let baseRisk : HydraulicRiskCoordinate → Nat := fun _ => 1
    let candidateRisk : HydraulicRiskCoordinate → Nat
      | .aggregate => 0
      | .temporalTail => 1
      | .transitionSubgroup => 2
    candidateRisk .aggregate ≤ baseRisk .aggregate ∧
      candidateRisk .temporalTail ≤ baseRisk .temporalTail ∧
      ¬ TypedRiskTransportAdmitted baseRisk candidateRisk := by
  dsimp
  constructor
  · decide
  constructor
  · decide
  · intro admitted
    have harmed := admitted HydraulicRiskCoordinate.transitionSubgroup
    exact (Nat.not_succ_le_self 1) harmed

end OCKIndividuationMSpaceComposition
