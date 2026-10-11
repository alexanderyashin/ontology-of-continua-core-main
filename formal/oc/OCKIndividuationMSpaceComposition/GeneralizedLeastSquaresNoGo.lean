import OCKIndividuationMSpaceComposition.NonnegativeCovarianceDesign

namespace OCKIndividuationMSpaceComposition

section Kernel

variable {R Parameter Observation : Type*}
  [Semiring R]
  [AddCommMonoid Parameter] [Module R Parameter]
  [AddCommMonoid Observation] [Module R Observation]

/-- Abstract `Xᵀ W X`: the readout and weight may encode any GLS whitening. -/
def weightedInformation
    (design : Parameter →ₗ[R] Observation)
    (weight : Observation →ₗ[R] Observation)
    (readout : Observation →ₗ[R] Parameter) : Parameter →ₗ[R] Parameter :=
  readout.comp (weight.comp design)

/-- Every direction invisible to the design remains invisible after weighting. -/
theorem weightedInformation_vanishes_on_designKernel
    (design : Parameter →ₗ[R] Observation)
    (weight : Observation →ₗ[R] Observation)
    (readout : Observation →ₗ[R] Parameter)
    (direction : Parameter) (invisible : design direction = 0) :
    weightedInformation design weight readout direction = 0 := by
  simp [weightedInformation, invisible]

/-- Kernel inclusion is independent of the chosen covariance or whitening. -/
theorem designKernel_le_weightedInformationKernel
    (design : Parameter →ₗ[R] Observation)
    (weight : Observation →ₗ[R] Observation)
    (readout : Observation →ₗ[R] Parameter) :
    LinearMap.ker design ≤ LinearMap.ker (weightedInformation design weight readout) := by
  intro direction invisible
  simpa [LinearMap.mem_ker] using
    weightedInformation_vanishes_on_designKernel
      design weight readout direction (by simpa [LinearMap.mem_ker] using invisible)

/-- No-go: GLS information cannot be injective when the design has a nonzero null direction. -/
theorem weightedInformation_not_injective_of_design_null
    (design : Parameter →ₗ[R] Observation)
    (weight : Observation →ₗ[R] Observation)
    (readout : Observation →ₗ[R] Parameter)
    (direction : Parameter) (nonzero : direction ≠ 0)
    (invisible : design direction = 0) :
    ¬ Function.Injective (weightedInformation design weight readout) := by
  intro injectiveInformation
  apply nonzero
  apply injectiveInformation
  simp [weightedInformation, invisible]

/-- Conversely, injective weighted information certifies an injective design. -/
theorem design_injective_of_weightedInformation_injective
    (design : Parameter →ₗ[R] Observation)
    (weight : Observation →ₗ[R] Observation)
    (readout : Observation →ₗ[R] Parameter)
    (informationInjective :
      Function.Injective (weightedInformation design weight readout)) :
    Function.Injective design := by
  intro first second sameObservation
  apply informationInjective
  simp [weightedInformation, sameObservation]

end Kernel

section Estimator

variable {R Parameter Observation : Type*}
  [Ring R]
  [AddCommGroup Parameter] [Module R Parameter]
  [AddCommGroup Observation] [Module R Observation]

/-- A declared unbiased linear estimator is a left inverse of the design. -/
def IsLeftInverseEstimator
    (design : Parameter →ₗ[R] Observation)
    (estimator : Observation →ₗ[R] Parameter) : Prop :=
  ∀ parameter, estimator (design parameter) = parameter

/-- Positive law: without noise, a left-inverse estimator recovers exactly. -/
theorem leftInverseEstimator_exact_without_noise
    (design : Parameter →ₗ[R] Observation)
    (estimator : Observation →ₗ[R] Parameter)
    (unbiased : IsLeftInverseEstimator design estimator)
    (parameter : Parameter) :
    estimator (design parameter) = parameter :=
  unbiased parameter

/-- Exact error transport: estimation error is precisely the estimator image of noise. -/
theorem leftInverseEstimator_error_eq_noise_image
    (design : Parameter →ₗ[R] Observation)
    (estimator : Observation →ₗ[R] Parameter)
    (unbiased : IsLeftInverseEstimator design estimator)
    (parameter : Parameter) (noise : Observation) :
    estimator (design parameter + noise) - parameter = estimator noise := by
  rw [map_add, unbiased parameter]
  exact add_sub_cancel_left parameter (estimator noise)

end Estimator

end OCKIndividuationMSpaceComposition
