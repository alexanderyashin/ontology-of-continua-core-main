import OCKIndividuationMSpaceComposition.RealValuedSparseRecovery
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Quantitative reconstruction and task certification

Uses the current corpus's restricted geometry rather than introducing a second
sparse recovery definition. A calibrated lower bound is a premise, never an
output inferred from a small residual. Bounds are deterministic; probabilistic
coverage requires a separately validated simultaneous confidence event.
-/

section MetricStability

variable {State Observation : Type*}
  [PseudoMetricSpace State] [PseudoMetricSpace Observation]

/-- Reconstruction error from three distinct budgets: solver residual against
the model, observation noise against the actual forward map, and model error
at the truth. No beta-min/discrete separation is required for this approximate
bound. -/
theorem tomographic_calibrated_reconstruction_bound
    (model actual : State → Observation) (admissible : State → Prop)
    (alpha residual noise calibration : ℝ) (alphaPositive : 0 < alpha)
    (lower : RestrictedSeparationLowerBound model admissible alpha)
    (candidate truth : State) (data : Observation)
    (candidateAdmissible : admissible candidate)
    (truthAdmissible : admissible truth)
    (solverBound : dist (model candidate) data ≤ residual)
    (noiseBound : dist data (actual truth) ≤ noise)
    (calibrationBound : dist (actual truth) (model truth) ≤ calibration) :
    dist candidate truth ≤ (residual + noise + calibration) / alpha := by
  apply (le_div_iff₀ alphaPositive).mpr
  have geometric := lower candidateAdmissible truthAdmissible
  have forward : dist (model candidate) (model truth) ≤
      residual + noise + calibration := by
    calc
      dist (model candidate) (model truth) ≤
          dist (model candidate) data + dist data (model truth) :=
        dist_triangle _ _ _
      _ ≤ dist (model candidate) data +
           (dist data (actual truth) + dist (actual truth) (model truth)) :=
        by
          apply add_le_add_right
          exact dist_triangle data (actual truth) (model truth)
      _ ≤ residual + (noise + calibration) :=
        add_le_add solverBound (add_le_add noiseBound calibrationBound)
      _ = residual + noise + calibration := by ring
  nlinarith

/-- A task can be much easier to estimate than the full state. Its explicit
modulus transports a reconstruction budget into a task budget. -/
theorem tomographic_task_error_from_state_budget
    {Answer : Type*} [PseudoMetricSpace Answer]
    (target : State → Answer) (candidate truth : State)
    (constant budget : ℝ) (constantNonnegative : 0 ≤ constant)
    (taskModulus : dist (target candidate) (target truth) ≤
      constant * dist candidate truth)
    (stateBudget : dist candidate truth ≤ budget) :
    dist (target candidate) (target truth) ≤ constant * budget :=
  taskModulus.trans (mul_le_mul_of_nonneg_left stateBudget constantNonnegative)

/-- Compose the calibrated state-reconstruction bound with a supplied
state-to-task modulus.  The result is the end-to-end task error budget used by
an applied observer; it does not infer the modulus or any probabilistic claim. -/
theorem tomographic_calibrated_task_error_bound
    {Answer : Type*} [PseudoMetricSpace Answer]
    (model actual : State → Observation) (admissible : State → Prop)
    (alpha residual noise calibration : ℝ) (alphaPositive : 0 < alpha)
    (lower : RestrictedSeparationLowerBound model admissible alpha)
    (target : State → Answer) (targetConstant : ℝ)
    (targetConstantNonnegative : 0 ≤ targetConstant)
    (taskModulus : ∀ first second,
      dist (target first) (target second) ≤
        targetConstant * dist first second)
    (candidate truth : State) (data : Observation)
    (candidateAdmissible : admissible candidate)
    (truthAdmissible : admissible truth)
    (solverBound : dist (model candidate) data ≤ residual)
    (noiseBound : dist data (actual truth) ≤ noise)
    (calibrationBound : dist (actual truth) (model truth) ≤ calibration) :
    dist (target candidate) (target truth) ≤
      targetConstant * ((residual + noise + calibration) / alpha) := by
  have stateBound := tomographic_calibrated_reconstruction_bound model actual admissible
    alpha residual noise calibration alphaPositive lower candidate truth data
    candidateAdmissible truthAdmissible solverBound noiseBound calibrationBound
  exact (taskModulus candidate truth).trans
    (mul_le_mul_of_nonneg_left stateBound targetConstantNonnegative)

/-- Decision certificate: a margin larger than the complete task error budget
fixes the sign relative to the declared threshold. -/
theorem tomographic_task_threshold_certificate
    (estimated actualValue threshold budget : ℝ)
    (errorBound : |estimated - actualValue| ≤ budget)
    (margin : threshold + budget < estimated) : threshold < actualValue := by
  have upper := (abs_le.mp errorBound).2
  linarith

end MetricStability

section NormBridge

variable {State Observation : Type*}
  [NormedAddCommGroup State] [NormedSpace ℝ State]
  [NormedAddCommGroup Observation] [NormedSpace ℝ Observation]

/-- Direct integration with RealValuedSparseRecovery's existing restricted
singular-value contract. Approximate recovery does NOT need its beta-min premise. -/
theorem tomographic_restricted_norm_reconstruction_bound
    (model : State →ₗ[ℝ] Observation) (actual : State → Observation)
    (admissible differenceClass : State → Prop)
    (alpha residual noise calibration : ℝ) (alphaPositive : 0 < alpha)
    (lower : RestrictedNormLowerBound model differenceClass alpha)
    (closed : DifferenceClosed admissible differenceClass)
    (candidate truth : State) (data : Observation)
    (candidateAdmissible : admissible candidate)
    (truthAdmissible : admissible truth)
    (solverBound : dist (model candidate) data ≤ residual)
    (noiseBound : dist data (actual truth) ≤ noise)
    (calibrationBound : dist (actual truth) (model truth) ≤ calibration) :
    dist candidate truth ≤ (residual + noise + calibration) / alpha := by
  exact tomographic_calibrated_reconstruction_bound model actual admissible
    alpha residual noise calibration alphaPositive
    (restrictedNormLowerBound_yields_pairGeometry model admissible
      differenceClass alpha lower closed)
    candidate truth data candidateAdmissible truthAdmissible
    solverBound noiseBound calibrationBound

end NormBridge

section MultiProjectionBudget


variable {View : Type*} [Fintype View]

/-- Separate rowwise noise, solver and calibration budgets before aggregation. -/
theorem tomographic_row_error_budget
    (predicted observed physical modeled : ℝ)
    (residual noise calibration : ℝ)
    (solver : |predicted - observed| ≤ residual)
    (measurement : |observed - physical| ≤ noise)
    (modelError : |physical - modeled| ≤ calibration) :
    |predicted - modeled| ≤ residual + noise + calibration := by
  calc
    |predicted - modeled| ≤ |predicted - observed| + |observed - modeled| :=
      abs_sub_le _ _ _
    _ ≤ |predicted - observed| + (|observed - physical| + |physical - modeled|) :=
      by
        apply add_le_add_right
        exact abs_sub_le observed physical modeled
    _ ≤ residual + (noise + calibration) :=
      add_le_add solver (add_le_add measurement modelError)
    _ = residual + noise + calibration := by ring

/-- An explicitly weighted frame lower bound and heterogeneous row budgets
yield a squared reconstruction bound. Zero/negative information directions are
not repaired by this inequality. No independence of row errors is assumed. -/
theorem tomographic_weighted_frame_budget
    (weight error bound : View → ℝ) (alpha squaredStateError : ℝ)
    (nonnegativeWeight : ∀ view, 0 ≤ weight view)
    (frameLower : alpha * squaredStateError ≤
      ∑ view, weight view * (error view) ^ 2)
    (rowBounds : ∀ view, |error view| ≤ bound view) :
    alpha * squaredStateError ≤ ∑ view, weight view * (bound view) ^ 2 := by
  apply frameLower.trans
  apply Finset.sum_le_sum
  intro view _
  apply mul_le_mul_of_nonneg_left _ (nonnegativeWeight view)
  have h := rowBounds view
  have nonnegativeBound : 0 ≤ bound view := (abs_nonneg _).trans h
  have squaredBound : |error view| ^ 2 ≤ (bound view) ^ 2 := by
    apply (sq_le_sq).2
    simpa [abs_of_nonneg nonnegativeBound] using h
  simpa [sq_abs] using squaredBound

end MultiProjectionBudget

end OCKIndividuationMSpaceComposition
