import OCKIndividuationMSpaceComposition.MultiTaskOpticJoin
import OCKIndividuationMSpaceComposition.CausalAdmissionContract

namespace OCKIndividuationMSpaceComposition

universe uWorld uObservation uOutcome

/-!
# Predictive versus causal task sufficiency

The same numerical codomain does not make an observational prediction task
and an interventional task identical.  In the exact finite potential-outcome
witness below, the passive optic observes `Y(0)` perfectly.  It is therefore
minimal and sufficient for predicting `Y(0)`, while two worlds with the same
`Y(0)` and different `Y(1)` remain observationally aliased.  No decoder of the
passive observation can recover the intervention target on every world.

The joint signature `(Y(0), Y(1))` is the coarsest exact representation
sufficient for both declared tasks.  Even that representational result is
kept separate from causal admission: the P1--P7 evidence contract remains an
independent premise.
-/

/-- Exact task sufficiency means the target is constant on every observation
fiber. -/
def ExactTaskSufficient
    {World : Type uWorld} {Observation : Type uObservation}
    {Outcome : Type uOutcome}
    (observe : World → Observation) (target : World → Outcome) : Prop :=
  ∀ left right, observe left = observe right → target left = target right

/-- A finite two-arm potential-outcome world: first coordinate is `Y(0)` and
second coordinate is `Y(1)`. -/
abbrev BinaryPotentialOutcomeWorld := Bool × Bool

def passiveOutcome : BinaryPotentialOutcomeWorld → Bool := Prod.fst
def interventionOutcome : BinaryPotentialOutcomeWorld → Bool := Prod.snd
def passiveOutcomeOptic : BinaryPotentialOutcomeWorld → Bool := passiveOutcome
def jointPotentialOutcomeSignature : BinaryPotentialOutcomeWorld → Bool × Bool := id

/-- Positive observational result: the passive-outcome optic is exactly
sufficient for the passive prediction task. -/
theorem passive_outcome_optic_is_predictively_sufficient :
    ExactTaskSufficient passiveOutcomeOptic passiveOutcome := by
  intro left right sameObservation
  exact sameObservation

/-- Exact no-go: the same passive optic is not sufficient for the
interventional target. -/
theorem passive_outcome_optic_is_not_intervention_sufficient :
    ¬ ExactTaskSufficient passiveOutcomeOptic interventionOutcome := by
  intro sufficient
  have impossible := sufficient (false, false) (false, true) rfl
  simp [interventionOutcome] at impossible

/-- Strong decoder form of the no-go: no deterministic rule of the passive
observation recovers `Y(1)` on every potential-outcome world. -/
theorem no_passive_observation_decoder_recovers_intervention_target :
    ¬ ∃ decode : Bool → Bool,
      ∀ world : BinaryPotentialOutcomeWorld,
        decode (passiveOutcomeOptic world) = interventionOutcome world := by
  rintro ⟨decode, exactEverywhere⟩
  have atFalse := exactEverywhere (false, false)
  have atTrue := exactEverywhere (false, true)
  simp [passiveOutcomeOptic, passiveOutcome, interventionOutcome] at atFalse atTrue
  have impossible : false = true := atFalse.symm.trans atTrue
  exact Bool.noConfusion impossible

/-- Positive repair: the joint potential-outcome signature is sufficient for
both the passive and interventional tasks. -/
theorem joint_potential_outcome_signature_is_sufficient_for_both_tasks :
    ExactTaskSufficient jointPotentialOutcomeSignature passiveOutcome ∧
      ExactTaskSufficient jointPotentialOutcomeSignature interventionOutcome := by
  constructor <;> intro left right sameJoint
  · exact congrArg Prod.fst sameJoint
  · exact congrArg Prod.snd sameJoint

/-- Minimality of the positive repair: every observation sufficient for both
tasks refines the joint potential-outcome signature. -/
theorem every_predictive_and_interventional_sufficient_observation_refines_joint
    {Observation : Type uObservation}
    (observe : BinaryPotentialOutcomeWorld → Observation)
    (predictivelySufficient : ExactTaskSufficient observe passiveOutcome)
    (interventionSufficient : ExactTaskSufficient observe interventionOutcome) :
    IsObservationRefinement jointPotentialOutcomeSignature observe := by
  intro left right sameObservation
  apply Prod.ext
  · exact predictivelySufficient left right sameObservation
  · exact interventionSufficient left right sameObservation

/-! ## Independent causal-admission boundary -/

def observationalOnlyCausalPremises : CausalAdmissionPremises where
  intervention := False
  consistency := True
  exchangeability := True
  positivity := True
  selection := True
  measurement := True
  transport := True

def fullySatisfiedCausalPremises : CausalAdmissionPremises where
  intervention := True
  consistency := True
  exchangeability := True
  positivity := True
  selection := True
  measurement := True
  transport := True

/-- Optic-level predictive success supplies neither intervention-target
sufficiency nor the missing intervention premise of the causal gate. -/
theorem predictive_sufficiency_does_not_imply_causal_sufficiency_or_admission :
    ExactTaskSufficient passiveOutcomeOptic passiveOutcome ∧
      ¬ ExactTaskSufficient passiveOutcomeOptic interventionOutcome ∧
      ¬ CausalAdmission observationalOnlyCausalPremises := by
  refine ⟨passive_outcome_optic_is_predictively_sufficient,
    passive_outcome_optic_is_not_intervention_sufficient, ?_⟩
  exact missing_intervention_blocks_causal_admission (by simp [observationalOnlyCausalPremises])

/-- Positive typed composition: a representation sufficient for both declared
targets and a separately satisfied P1--P7 contract jointly support the two
distinct obligations.  Neither conjunct is inferred from the other. -/
theorem joint_signature_and_full_admission_close_distinct_obligations :
    (ExactTaskSufficient jointPotentialOutcomeSignature passiveOutcome ∧
      ExactTaskSufficient jointPotentialOutcomeSignature interventionOutcome) ∧
      CausalAdmission fullySatisfiedCausalPremises := by
  constructor
  · exact joint_potential_outcome_signature_is_sufficient_for_both_tasks
  · simp [CausalAdmission, fullySatisfiedCausalPremises]

end OCKIndividuationMSpaceComposition
