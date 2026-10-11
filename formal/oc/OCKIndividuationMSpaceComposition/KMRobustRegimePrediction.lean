import OCKIndividuationMSpaceComposition.KMOperatorCycleFlowPrediction
import OCKIndividuationMSpaceComposition.RegimeSwitchingCoupling

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe uLiftCarrier uLiftCandidate uRepairCandidate

/-!
# Robust nonlinear and regime-switching K/M prediction

This module composes the existing time-varying mismatch recursion with the v67
sharp K/M band.  A local gain/residual contract now generates a global,
finite-horizon model-class radius, sharp-band width bound and threshold
certificate.  A separate switched-system specialization exposes the exact
chronological product rather than commuting regime operators implicitly.
-/

/-- Nonnegative gains and residuals preserve a nonnegative error envelope. -/
theorem timeVaryingErrorEnvelope_nonnegative
    (gain residual : ℕ → ℚ) (initialError : ℚ)
    (initialNonnegative : 0 ≤ initialError)
    (gainNonnegative : ∀ t, 0 ≤ gain t)
    (residualNonnegative : ∀ t, 0 ≤ residual t)
    (horizon : ℕ) :
    0 ≤ timeVaryingErrorEnvelope gain residual initialError horizon := by
  induction horizon with
  | zero => exact initialNonnegative
  | succ horizon inductionHypothesis =>
      rw [timeVaryingErrorEnvelope]
      exact add_nonneg
        (mul_nonneg (gainNonnegative horizon) inductionHypothesis)
        (residualNonnegative horizon)

/-- The propagated envelope is monotone in its initial error. -/
theorem timeVaryingErrorEnvelope_mono_initial
    (gain residual : ℕ → ℚ)
    (gainNonnegative : ∀ t, 0 ≤ gain t)
    {smaller larger : ℚ} (initialOrder : smaller ≤ larger)
    (horizon : ℕ) :
    timeVaryingErrorEnvelope gain residual smaller horizon ≤
      timeVaryingErrorEnvelope gain residual larger horizon := by
  induction horizon with
  | zero => exact initialOrder
  | succ horizon inductionHypothesis =>
      simp only [timeVaryingErrorEnvelope]
      exact add_le_add
        (mul_le_mul_of_nonneg_left inductionHypothesis
          (gainNonnegative horizon)) (le_refl _)

/-- Common scalar trajectory interpretation for a tied K/M model class. -/
structure KMTimeVaryingTrajectoryInterpretation
    {K : CurrentK}
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K) where
  trajectoryOf : liftSearch.Candidate → ℕ → ℚ

/-- Inspectable local mismatch contract relative to the selected minimum. -/
structure KMTiedTimeVaryingMismatchContract
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMTimeVaryingTrajectoryInterpretation liftSearch) where
  gain : ℕ → ℚ
  residual : ℕ → ℚ
  initialError : ℚ
  initialErrorNonnegative : 0 ≤ initialError
  gainNonnegative : ∀ t, 0 ≤ gain t
  residualNonnegative : ∀ t, 0 ≤ residual t
  initialBound : ∀ candidate,
    KMTiedResolvingCandidate resolution candidate →
      |interpretation.trajectoryOf candidate 0 -
        interpretation.trajectoryOf resolution.selection.minimizer.1 0| ≤ initialError
  stepBound : ∀ candidate,
    KMTiedResolvingCandidate resolution candidate →
    ∀ t,
      |interpretation.trajectoryOf candidate (t + 1) -
          interpretation.trajectoryOf resolution.selection.minimizer.1 (t + 1)| ≤
        gain t *
          |interpretation.trajectoryOf candidate t -
            interpretation.trajectoryOf resolution.selection.minimizer.1 t| +
        residual t

/-- Local nonlinear mismatch propagates to a common finite-horizon radius for
every tied K/M candidate. -/
theorem KMTiedTimeVaryingMismatchContract.horizonErrorBound
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMTimeVaryingTrajectoryInterpretation liftSearch}
    (contract : KMTiedTimeVaryingMismatchContract resolution interpretation)
    (candidate : liftSearch.Candidate)
    (tied : KMTiedResolvingCandidate resolution candidate)
    (horizon : ℕ) :
    |interpretation.trajectoryOf candidate horizon -
        interpretation.trajectoryOf resolution.selection.minimizer.1 horizon| ≤
      timeVaryingErrorEnvelope contract.gain contract.residual
        contract.initialError horizon := by
  have propagated := timeVarying_model_mismatch_error_bound
    (interpretation.trajectoryOf candidate)
    (interpretation.trajectoryOf resolution.selection.minimizer.1)
    contract.gain contract.residual contract.gainNonnegative
    (contract.stepBound candidate tied) horizon
  exact propagated.trans
    (timeVaryingErrorEnvelope_mono_initial contract.gain contract.residual
      contract.gainNonnegative (contract.initialBound candidate tied) horizon)

/-- The propagated mismatch envelope is exactly a v67 contextual numerical
coherence radius at the selected horizon. -/
theorem KMTiedTimeVaryingMismatchContract.numericCoherenceAt
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMTimeVaryingTrajectoryInterpretation liftSearch}
    (contract : KMTiedTimeVaryingMismatchContract resolution interpretation)
    (horizon : ℕ) :
    KMContextualNumericCoherence resolution
      (fun candidate => interpretation.trajectoryOf candidate horizon)
      (timeVaryingErrorEnvelope contract.gain contract.residual
        contract.initialError horizon) := by
  constructor
  · exact timeVaryingErrorEnvelope_nonnegative
      contract.gain contract.residual contract.initialError
      contract.initialErrorNonnegative contract.gainNonnegative
      contract.residualNonnegative horizon
  · intro candidate tied
    have errorBound := contract.horizonErrorBound candidate tied horizon
    have twoSided := abs_le.mp errorBound
    constructor <;> linarith

/-- Consequently the information-optimal sharp K/M band is no wider than
twice the recursively computed nonlinear mismatch envelope. -/
theorem km_timeVarying_contract_bounds_sharp_band
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {interpretation : KMTimeVaryingTrajectoryInterpretation liftSearch}
    (contract : KMTiedTimeVaryingMismatchContract resolution interpretation)
    (horizon : ℕ)
    (band : KMSharpPredictionBand resolution
      (fun candidate => interpretation.trajectoryOf candidate horizon)) :
    band.width ≤ 2 *
      timeVaryingErrorEnvelope contract.gain contract.residual
        contract.initialError horizon :=
  km_contextual_radius_bounds_sharp_band_width band _
    (contract.numericCoherenceAt horizon)

/-- A selected-model forecast above threshold by more than the complete
envelope is a necessary above-threshold future for every tied model. -/
theorem km_timeVarying_margin_forces_necessary_above
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMTimeVaryingTrajectoryInterpretation liftSearch)
    (contract : KMTiedTimeVaryingMismatchContract resolution interpretation)
    (horizon : ℕ) (threshold : ℚ)
    (margin : threshold <
      interpretation.trajectoryOf resolution.selection.minimizer.1 horizon -
        timeVaryingErrorEnvelope contract.gain contract.residual
          contract.initialError horizon) :
    KMNecessaryFuture resolution
      (fun candidate (_ : Unit) =>
        threshold < interpretation.trajectoryOf candidate horizon) () := by
  intro candidate tied
  have errorBound := contract.horizonErrorBound candidate tied horizon
  have lowerBound := (abs_le.mp errorBound).1
  linarith

/-- Symmetric below-threshold necessary-future certificate. -/
theorem km_timeVarying_margin_forces_necessary_below
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMTimeVaryingTrajectoryInterpretation liftSearch)
    (contract : KMTiedTimeVaryingMismatchContract resolution interpretation)
    (horizon : ℕ) (threshold : ℚ)
    (margin :
      interpretation.trajectoryOf resolution.selection.minimizer.1 horizon +
        timeVaryingErrorEnvelope contract.gain contract.residual
          contract.initialError horizon < threshold) :
    KMNecessaryFuture resolution
      (fun candidate (_ : Unit) =>
        interpretation.trajectoryOf candidate horizon < threshold) () := by
  intro candidate tied
  have errorBound := contract.horizonErrorBound candidate tied horizon
  have upperBound := (abs_le.mp errorBound).2
  linarith

/-- No-go: a finite common prefix alone cannot provide any finite universal
next-step error guarantee. -/
theorem finite_prefix_has_no_universal_next_error_bound
    (horizon : ℕ) (claimedError : ℚ) :
    ∃ actual predicted : ℕ → ℚ,
      PrefixAgree actual predicted horizon ∧
      claimedError <
        |predicted (horizon + 1) - actual (horizon + 1)| := by
  obtain ⟨actual, predicted, prefixAgreement, gap⟩ :=
    finite_prefix_allows_arbitrary_next_gap horizon (|claimedError| + 1)
  refine ⟨actual, predicted, prefixAgreement, ?_⟩
  rw [gap, abs_of_nonneg]
  · have selfBound : claimedError ≤ |claimedError| := le_abs_self claimedError
    linarith
  · positivity

/-!
## Exact switched-regime specialization
-/

/-- With zero forcing, an arbitrary time-varying trajectory is exactly its
chronologically ordered propagation applied to the initial state. -/
theorem timeVaryingCoupledTrajectory_zero_forcing_eq_propagation
    {X : Type*} [AddCommGroup X]
    (operator : ℕ → X →+ X) (x0 : X) (horizon : ℕ) :
    timeVaryingCoupledTrajectory operator (fun _ => 0) x0 horizon =
      timeOrderedPropagation operator horizon x0 := by
  rw [timeVaryingCoupledTrajectory_exact_decomposition]
  have forcingZero :
      accumulatedTimeVaryingForcing operator (fun _ => 0) horizon = 0 := by
    induction horizon with
    | zero => rfl
    | succ horizon inductionHypothesis =>
        simp [accumulatedTimeVaryingForcing, inductionHypothesis]
  simp [forcingZero]

/-- Exact noncommutative two-regime endpoint formula. -/
theorem twoRegime_zero_forcing_endpoint_exact
    {X : Type*} [AddCommGroup X]
    (before after : X →+ X) (cut afterSteps : ℕ) (x0 : X) :
    timeVaryingCoupledTrajectory (twoRegimeOperator before after cut)
        (fun _ => 0) x0 (cut + afterSteps) =
      couplingPower after afterSteps (couplingPower before cut x0) := by
  rw [timeVaryingCoupledTrajectory_zero_forcing_eq_propagation,
    timeOrderedPropagation_twoRegime_at_cut_add]
  rfl

/-- Closed form for powers of a rational scaling endomorphism. -/
theorem couplingPower_rationalScale_apply
    (scale : ℚ) (horizon : ℕ) (x : ℚ) :
    couplingPower (rationalScaleEndomorphism scale) horizon x =
      scale ^ horizon * x := by
  induction horizon with
  | zero => simp [couplingPower]
  | succ horizon inductionHypothesis =>
      change scale *
        couplingPower (rationalScaleEndomorphism scale) horizon x =
          scale ^ (horizon + 1) * x
      rw [inductionHypothesis, pow_succ]
      ring

/-- Fully computable scalar switched-regime prediction. -/
theorem scalar_twoRegime_zero_forcing_endpoint_exact
    (beforeScale afterScale x0 : ℚ) (cut afterSteps : ℕ) :
    timeVaryingCoupledTrajectory
        (twoRegimeOperator (rationalScaleEndomorphism beforeScale)
          (rationalScaleEndomorphism afterScale) cut)
        (fun _ => 0) x0 (cut + afterSteps) =
      afterScale ^ afterSteps * beforeScale ^ cut * x0 := by
  rw [twoRegime_zero_forcing_endpoint_exact,
    couplingPower_rationalScale_apply, couplingPower_rationalScale_apply]
  ring

end OCKIndividuationMSpaceComposition
