import OCKIndividuationMSpaceComposition.LikelihoodRecoverySandwich
import OCKIndividuationMSpaceComposition.FiniteObservationLearning

namespace OCKIndividuationMSpaceComposition

/-!
# Information sandwich for finite optic learning

The finite-class concentration upper bound cannot be minimax-sharp from the
number of candidate optics alone.  This module composes the existing Fano
lower certificate and finite-class upper certificate for a typed optic family,
then gives same-cardinality perfect and uninformative observation channels.
-/

/-- A typed finite-optic learning certificate carrying both the channel-level
Fano lower premise and the finite-class concentration upper premise. -/
structure OpticLearningInformationSandwich
    (Optic : Type) [Fintype Optic]
    (observations : ℕ) (epsilon delta : ℝ) where
  fanoChannel : FanoChannelCertificate (Fintype.card Optic) observations
  uniformUpper : UniformConcentrationCertificate
    observations (Fintype.card Optic) epsilon delta

/-- The typed sandwich simultaneously exposes the information-theoretic lower
floor and the registered finite-class sufficient budget at one sample count. -/
theorem opticLearningInformationSandwich_verified
    {Optic : Type} [Fintype Optic]
    {observations : ℕ} {epsilon delta : ℝ}
    (certificate : OpticLearningInformationSandwich
      Optic observations epsilon delta)
    (positiveCapacity : 0 < certificate.fanoChannel.perObservationCapacity) :
    fanoRequiredInformation (Fintype.card Optic)
          certificate.fanoChannel.error /
        certificate.fanoChannel.perObservationCapacity ≤ observations ∧
      2 * (Fintype.card Optic : ℝ) *
          Real.exp (-2 * (observations : ℝ) * epsilon ^ 2) ≤ delta := by
  constructor
  · exact fano_observations_lower_bound certificate.fanoChannel
      positiveCapacity
  · exact certificate.uniformUpper.2.2

/-- Below the typed optic family's Fano floor, no total-information assignment
can satisfy both the required-information and per-observation-capacity
contracts. -/
theorem below_optic_information_floor_no_learning_certificate
    {Optic : Type} [Fintype Optic]
    (observations : ℕ) (error capacity : ℝ)
    (positiveCapacity : 0 < capacity)
    (tooFew : (observations : ℝ) <
      fanoRequiredInformation (Fintype.card Optic) error / capacity) :
    ¬ ∃ totalInformation : ℝ,
      fanoRequiredInformation (Fintype.card Optic) error ≤ totalInformation ∧
      totalInformation ≤ (observations : ℝ) * capacity :=
  below_fano_capacity_floor_no_go error capacity positiveCapacity tooFew

/-- A single perfectly informative observation identifies every member of a
finite optic family. -/
def perfectOpticObservation {Optic : Type} (optic : Optic) : Optic := optic

def perfectOpticDecoder {Optic : Type} (observation : Optic) : Optic :=
  observation

theorem one_perfect_observation_exactly_identifies_optic
    {Optic : Type} (optic : Optic) :
    perfectOpticDecoder (perfectOpticObservation optic) = optic := rfl

/-- Repeating a completely uninformative observation any finite number of
times still cannot identify both members of a two-optic family. -/
theorem repeated_uninformative_observation_never_identifies_binary_optic
    (observations : ℕ)
    (decoder : (Fin observations → Unit) → Fin 2) :
    ∃ optic : Fin 2,
      decoder (fun _ => ()) ≠ optic := by
  by_cases predictsZero : decoder (fun _ => ()) = (0 : Fin 2)
  · refine ⟨1, ?_⟩
    rw [predictsZero]
    decide
  · exact ⟨0, predictsZero⟩

/-- The same two-optic cardinality admits both a one-observation exact channel
and a channel for which no finite repetition admits an everywhere-correct
decoder.  Hence candidate count alone cannot determine sharp sample
complexity. -/
theorem two_optics_same_cardinality_has_opposite_learnability_channels :
    (∀ optic : Fin 2,
      perfectOpticDecoder (perfectOpticObservation optic) = optic) ∧
      (∀ observations : ℕ, ∀ decoder : (Fin observations → Unit) → Fin 2,
        ∃ optic : Fin 2, decoder (fun _ => ()) ≠ optic) := by
  constructor
  · intro optic
    rfl
  · intro observations decoder
    exact repeated_uninformative_observation_never_identifies_binary_optic
      observations decoder

end OCKIndividuationMSpaceComposition
