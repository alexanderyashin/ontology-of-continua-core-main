namespace OCKIndividuationMSpaceComposition

/-!
# Causal-admission contract

The empirical OC layer must distinguish a predictive/observational gain from a
causal claim.  This module is the small proof kernel for that distinction.  It
does not assert that any concrete dataset satisfies the premises; it only makes
the seven admission obligations explicit and derives the corresponding
abstention/no-go rules.
-/

/-- The seven premises carried by the executable causal-admission contract. -/
structure CausalAdmissionPremises where
  intervention : Prop
  consistency : Prop
  exchangeability : Prop
  positivity : Prop
  selection : Prop
  measurement : Prop
  transport : Prop

/-- All premises required before a transported causal claim may be admitted. -/
def CausalAdmission (premises : CausalAdmissionPremises) : Prop :=
  premises.intervention ∧
    premises.consistency ∧
      premises.exchangeability ∧
        premises.positivity ∧
          premises.selection ∧
            premises.measurement ∧
              premises.transport

/-- Source/context causal admission uses P1-P6 and makes no transport claim. -/
def SourceCausalAdmission (premises : CausalAdmissionPremises) : Prop :=
  premises.intervention ∧
    premises.consistency ∧
      premises.exchangeability ∧
        premises.positivity ∧
          premises.selection ∧
            premises.measurement

/-- Transported causal admission is source admission plus the P7 contract. -/
def TransportedCausalAdmission (premises : CausalAdmissionPremises) : Prop :=
  SourceCausalAdmission premises ∧ premises.transport

theorem sourceCausalAdmission_implies_all_source_premises
    {premises : CausalAdmissionPremises}
    (admitted : SourceCausalAdmission premises) :
    premises.intervention ∧
      premises.consistency ∧
        premises.exchangeability ∧
          premises.positivity ∧
            premises.selection ∧
              premises.measurement := by
  exact admitted

theorem transportedCausalAdmission_implies_source_and_transport
    {premises : CausalAdmissionPremises}
    (admitted : TransportedCausalAdmission premises) :
    SourceCausalAdmission premises ∧ premises.transport := by
  exact admitted

theorem missing_source_premise_blocks_source_causal_admission
    {premises : CausalAdmissionPremises}
    (missing :
      ¬ premises.intervention ∨
        ¬ premises.consistency ∨
          ¬ premises.exchangeability ∨
            ¬ premises.positivity ∨
              ¬ premises.selection ∨
                ¬ premises.measurement) :
    ¬ SourceCausalAdmission premises := by
  intro admitted
  rcases missing with h | h | h | h | h | h
  · exact h admitted.1
  · exact h admitted.2.1
  · exact h admitted.2.2.1
  · exact h admitted.2.2.2.1
  · exact h admitted.2.2.2.2.1
  · exact h admitted.2.2.2.2.2

theorem missing_transport_blocks_transported_causal_admission
    {premises : CausalAdmissionPremises}
    (missing : ¬ premises.transport) :
    ¬ TransportedCausalAdmission premises := by
  intro admitted
  exact missing admitted.2

theorem causalAdmission_implies_all_premises
    {premises : CausalAdmissionPremises}
    (admitted : CausalAdmission premises) :
    premises.intervention ∧
      premises.consistency ∧
        premises.exchangeability ∧
          premises.positivity ∧
            premises.selection ∧
              premises.measurement ∧
                premises.transport := by
  exact admitted

theorem causalAdmission_requires_intervention
    {premises : CausalAdmissionPremises}
    (admitted : CausalAdmission premises) :
    premises.intervention := by
  exact admitted.1

theorem causalAdmission_requires_consistency
    {premises : CausalAdmissionPremises}
    (admitted : CausalAdmission premises) :
    premises.consistency := by
  exact admitted.2.1

theorem causalAdmission_requires_exchangeability
    {premises : CausalAdmissionPremises}
    (admitted : CausalAdmission premises) :
    premises.exchangeability := by
  exact admitted.2.2.1

theorem causalAdmission_requires_positivity
    {premises : CausalAdmissionPremises}
    (admitted : CausalAdmission premises) :
    premises.positivity := by
  exact admitted.2.2.2.1

theorem causalAdmission_requires_selection
    {premises : CausalAdmissionPremises}
    (admitted : CausalAdmission premises) :
    premises.selection := by
  exact admitted.2.2.2.2.1

theorem causalAdmission_requires_measurement
    {premises : CausalAdmissionPremises}
    (admitted : CausalAdmission premises) :
    premises.measurement := by
  exact admitted.2.2.2.2.2.1

theorem causalAdmission_requires_transport
    {premises : CausalAdmissionPremises}
    (admitted : CausalAdmission premises) :
    premises.transport := by
  exact admitted.2.2.2.2.2.2

theorem missing_intervention_blocks_causal_admission
    {premises : CausalAdmissionPremises}
    (missing : ¬ premises.intervention) :
    ¬ CausalAdmission premises := by
  intro admitted
  exact missing (causalAdmission_requires_intervention admitted)

theorem missing_consistency_blocks_causal_admission
    {premises : CausalAdmissionPremises}
    (missing : ¬ premises.consistency) :
    ¬ CausalAdmission premises := by
  intro admitted
  exact missing (causalAdmission_requires_consistency admitted)

theorem missing_exchangeability_blocks_causal_admission
    {premises : CausalAdmissionPremises}
    (missing : ¬ premises.exchangeability) :
    ¬ CausalAdmission premises := by
  intro admitted
  exact missing (causalAdmission_requires_exchangeability admitted)

theorem missing_positivity_blocks_causal_admission
    {premises : CausalAdmissionPremises}
    (missing : ¬ premises.positivity) :
    ¬ CausalAdmission premises := by
  intro admitted
  exact missing (causalAdmission_requires_positivity admitted)

theorem missing_selection_blocks_causal_admission
    {premises : CausalAdmissionPremises}
    (missing : ¬ premises.selection) :
    ¬ CausalAdmission premises := by
  intro admitted
  exact missing (causalAdmission_requires_selection admitted)

theorem missing_measurement_blocks_causal_admission
    {premises : CausalAdmissionPremises}
    (missing : ¬ premises.measurement) :
    ¬ CausalAdmission premises := by
  intro admitted
  exact missing (causalAdmission_requires_measurement admitted)

theorem missing_transport_blocks_causal_admission
    {premises : CausalAdmissionPremises}
    (missing : ¬ premises.transport) :
    ¬ CausalAdmission premises := by
  intro admitted
  exact missing (causalAdmission_requires_transport admitted)

end OCKIndividuationMSpaceComposition
