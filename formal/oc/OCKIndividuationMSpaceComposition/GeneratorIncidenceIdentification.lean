import OCKIndividuationMSpaceComposition.GeneralizedLeastSquaresNoGo
import OCKIndividuationMSpaceComposition.GeneratedDeviationCone
import Mathlib.LinearAlgebra.Dimension.StrongRankCondition
import Mathlib.LinearAlgebra.Dimension.Constructions
import Mathlib.Tactic.Abel

namespace OCKIndividuationMSpaceComposition

/-!
# Identification of event-to-generator incidence laws

The unknown generator law is a parameter, a registered intervention design is
a linear map, and the measured profile contrast is its observation.  This is
an OC adapter to mature linear inverse-problem algebra, not a claim that every
domain is linear or noise-free.
-/

universe uScalar uParameter uObservation uCarrier

section ProfileContrast

/-- Signed profile contrast used by the controlled occurrence adapter. -/
def signedProfileDifference
    {Carrier : Type uCarrier} (actual baseline : Carrier → Int) : Carrier → Int :=
  fun carrier => actual carrier - baseline carrier

/-- A single additive event generator is recovered exactly by differencing. -/
theorem signed_profile_difference_recovers_added_generator
    {Carrier : Type uCarrier} (baseline generator : Carrier → Int) :
    signedProfileDifference (addScoreProfiles baseline generator) baseline = generator := by
  funext carrier
  simp [signedProfileDifference, addScoreProfiles]

/-- With additive observation error, the recovered generator error is exactly
the error profile, coordinate by coordinate. -/
theorem signed_profile_difference_with_noise
    {Carrier : Type uCarrier}
    (baseline generator noise : Carrier → Int) :
    signedProfileDifference
        (addScoreProfiles (addScoreProfiles baseline generator) noise) baseline =
      addScoreProfiles generator noise := by
  funext carrier
  simp [signedProfileDifference, addScoreProfiles]
  omega

end ProfileContrast

section LinearIncidence

variable {R : Type uScalar} {Parameter : Type uParameter}
  {Observation : Type uObservation}
  [Ring R]
  [AddCommGroup Parameter] [Module R Parameter]
  [AddCommGroup Observation] [Module R Observation]

/-- Baseline plus the response of a registered intervention design. -/
def generatorExperimentObservation
    (design : Parameter →ₗ[R] Observation)
    (baseline : Observation) (parameter : Parameter) : Observation :=
  baseline + design parameter

/-- Baseline-corrected linear estimator for the generator parameter. -/
def recoverGeneratorParameter
    (estimator : Observation →ₗ[R] Parameter)
    (baseline measured : Observation) : Parameter :=
  estimator (measured - baseline)

/-- A left inverse is a sufficient rank-covering contract for exact recovery. -/
theorem left_inverse_recovers_generator_parameter_exactly
    (design : Parameter →ₗ[R] Observation)
    (estimator : Observation →ₗ[R] Parameter)
    (leftInverse : IsLeftInverseEstimator design estimator)
    (baseline : Observation) (parameter : Parameter) :
    recoverGeneratorParameter estimator baseline
        (generatorExperimentObservation design baseline parameter) = parameter := by
  have corrected :
      generatorExperimentObservation design baseline parameter - baseline =
        design parameter := by
    simp [generatorExperimentObservation]
  rw [recoverGeneratorParameter, corrected]
  exact leftInverse parameter

/-- Exact noise transport: the estimation error is the estimator image of the
observation noise.  No probabilistic approximation is hidden here. -/
theorem generator_parameter_error_eq_estimator_noise
    (design : Parameter →ₗ[R] Observation)
    (estimator : Observation →ₗ[R] Parameter)
    (leftInverse : IsLeftInverseEstimator design estimator)
    (baseline : Observation) (parameter : Parameter) (noise : Observation) :
    recoverGeneratorParameter estimator baseline
        (generatorExperimentObservation design baseline parameter + noise) - parameter =
      estimator noise := by
  have corrected :
      generatorExperimentObservation design baseline parameter + noise - baseline =
        design parameter + noise := by
    simp only [generatorExperimentObservation]
    abel
  rw [recoverGeneratorParameter, corrected]
  exact leftInverseEstimator_error_eq_noise_image
    design estimator leftInverse parameter noise

/-- A left inverse makes the intervention design identifiable. -/
theorem left_inverse_makes_generator_design_injective
    (design : Parameter →ₗ[R] Observation)
    (estimator : Observation →ₗ[R] Parameter)
    (leftInverse : IsLeftInverseEstimator design estimator) :
    Function.Injective design := by
  intro first second sameObservation
  calc
    first = estimator (design first) := (leftInverse first).symm
    _ = estimator (design second) := congrArg estimator sameObservation
    _ = second := leftInverse second

/-- Sharp aliasing witness: every nonzero null direction produces distinct
generator laws with identical observations under every common baseline. -/
theorem invisible_generator_direction_produces_alias
    (design : Parameter →ₗ[R] Observation)
    (direction : Parameter) (nonzero : direction ≠ 0)
    (invisible : design direction = 0)
    (baseline : Observation) :
    ∃ first second : Parameter,
      first ≠ second ∧
      generatorExperimentObservation design baseline first =
        generatorExperimentObservation design baseline second := by
  refine ⟨direction, 0, nonzero, ?_⟩
  simp [generatorExperimentObservation, invisible]

/-- No-go: with a nonzero design-null direction, no observation-only rule can
recover every generator law, even in the noiseless model. -/
theorem invisible_generator_direction_no_universal_exact_recovery
    (design : Parameter →ₗ[R] Observation)
    (direction : Parameter) (nonzero : direction ≠ 0)
    (invisible : design direction = 0) :
    ¬ ∃ recover : Observation → Parameter,
      ∀ baseline parameter,
        recover (generatorExperimentObservation design baseline parameter) = parameter := by
  rintro ⟨recover, recovers⟩
  have sameObservation :
      generatorExperimentObservation design 0 direction =
        generatorExperimentObservation design 0 0 := by
    simp [generatorExperimentObservation, invisible]
  have sameRecovery := congrArg recover sameObservation
  rw [recovers 0 direction, recovers 0 0] at sameRecovery
  exact nonzero sameRecovery

end LinearIncidence

section ObservationBudget

variable {R : Type uScalar} {Parameter : Type uParameter}
  {Observation : Type uObservation}
  [Semiring R] [StrongRankCondition R]
  [AddCommMonoid Parameter] [Module R Parameter]
  [AddCommMonoid Observation] [Module R Observation]
  [Module.Finite R Observation]

/-- Necessary resource law: an identifiable linear generator family cannot
have greater parameter dimension than its complete observation space. -/
theorem identifiable_generator_design_requires_finrank_budget
    (design : Parameter →ₗ[R] Observation)
    (identifiable : Function.Injective design) :
    Module.finrank R Parameter ≤ Module.finrank R Observation :=
  LinearMap.finrank_le_finrank_of_injective identifiable

end ObservationBudget

section ScalarBudgets

/-- For scalar observations, identifying `generatorCount` free coordinates
requires at least that many independent scalar observation coordinates. -/
theorem scalar_generator_identification_budget
    {K : Type uScalar} [DivisionRing K]
    (generatorCount observationCount : Nat)
    (design : (Fin generatorCount → K) →ₗ[K] (Fin observationCount → K))
    (identifiable : Function.Injective design) :
    generatorCount ≤ observationCount := by
  have budget := LinearMap.finrank_le_finrank_of_injective identifiable
  rw [Module.finrank_fin_fun K, Module.finrank_fin_fun K] at budget
  exact budget

/-- Equivalent experiment/readout form: experiments times independent
readouts must cover the free generator dimension. -/
theorem experiment_readout_product_budget
    {K : Type uScalar} [DivisionRing K]
    (generatorCount experimentCount readoutCount : Nat)
    (design :
      (Fin generatorCount → K) →ₗ[K]
        (Fin (experimentCount * readoutCount) → K))
    (identifiable : Function.Injective design) :
    generatorCount ≤ experimentCount * readoutCount := by
  have budget := LinearMap.finrank_le_finrank_of_injective identifiable
  rw [Module.finrank_fin_fun K, Module.finrank_fin_fun K] at budget
  exact budget

/-- Sharp finite-dimensional no-go: fewer scalar observation coordinates than
free generator coordinates force non-identifiability for every linear design. -/
theorem fewer_scalar_observations_force_generator_nonidentifiability
    {K : Type uScalar} [DivisionRing K]
    (generatorCount observationCount : Nat)
    (fewer : observationCount < generatorCount)
    (design : (Fin generatorCount → K) →ₗ[K] (Fin observationCount → K)) :
    ¬ Function.Injective design := by
  intro identifiable
  have required := scalar_generator_identification_budget
    generatorCount observationCount design identifiable
  omega

/-- If every experiment returns all carrier coordinates and every generator's
carrier vector is free, an identifiable family needs at least one independent
experiment per generator.  Extra carrier readouts do not remove that rank
requirement because they add the same factor to parameters and observations. -/
theorem multi_carrier_generator_family_requires_experiment_count
    {K : Type uScalar} [DivisionRing K]
    (generatorCount carrierCount experimentCount : Nat)
    (carrierPositive : 0 < carrierCount)
    (design :
      (Fin (generatorCount * carrierCount) → K) →ₗ[K]
        (Fin (experimentCount * carrierCount) → K))
    (identifiable : Function.Injective design) :
    generatorCount ≤ experimentCount := by
  have scalarBudget := scalar_generator_identification_budget
    (generatorCount * carrierCount) (experimentCount * carrierCount)
    design identifiable
  exact Nat.le_of_mul_le_mul_right scalarBudget carrierPositive

/-- Sharp experiment-count no-go for the free multi-carrier incidence family. -/
theorem fewer_experiments_force_multi_carrier_generator_aliasing
    {K : Type uScalar} [DivisionRing K]
    (generatorCount carrierCount experimentCount : Nat)
    (carrierPositive : 0 < carrierCount)
    (fewer : experimentCount < generatorCount)
    (design :
      (Fin (generatorCount * carrierCount) → K) →ₗ[K]
        (Fin (experimentCount * carrierCount) → K)) :
    ¬ Function.Injective design := by
  intro identifiable
  have required := multi_carrier_generator_family_requires_experiment_count
    generatorCount carrierCount experimentCount carrierPositive design identifiable
  omega

end ScalarBudgets

end OCKIndividuationMSpaceComposition
