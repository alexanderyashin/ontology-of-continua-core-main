import OCKIndividuationMSpaceComposition.TomographicInverseCertificate
import OCKIndividuationMSpaceComposition.TomographicStability
import OCKIndividuationMSpaceComposition.TomographicNoisyAutofocus
import Mathlib.Tactic

namespace OCScientificExtensions.TomographicAdaptationDynamics

open OCKIndividuationMSpaceComposition

/-! E0004. Reconstruction-to-control coupling. All budgets are deterministic
premises; no acquisition, probability law, or physical optimum is inferred. -/

section ReconstructionAdapters

variable {Coordinate View : Type*} [Fintype Coordinate] [Fintype View]

/-- Stable inverse plus a scalar task modulus gives the estimated-centre error. -/
theorem inverse_task_centre_bound
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicStableLeftInverse rows)
    (target : (Coordinate → ℝ) → ℝ) (constant budget : ℝ)
    (constantNonnegative : 0 ≤ constant)
    (modulus : ∀ first second,
      dist (target first) (target second) ≤ constant * dist first second)
    (truth : Coordinate → ℝ) (data : View → ℝ)
    (measurement : dist data (tomographicProjection rows truth) ≤ budget) :
    |target (certificate.reconstruct data) - target truth| ≤
      constant * (certificate.lipschitzConstant * budget) := by
  have stateBound := tomographicStableInverse_error_bound certificate truth data budget measurement
  have taskBound := tomographic_task_error_from_state_budget target
    (certificate.reconstruct data) truth constant
    (certificate.lipschitzConstant * budget) constantNonnegative
    (modulus _ _) stateBound
  simpa [Real.dist_eq] using taskBound

end ReconstructionAdapters

section CalibratedAdapter

variable {State Observation : Type*}
  [PseudoMetricSpace State] [PseudoMetricSpace Observation]

/-- An alternative adapter permits solver, noise and forward-calibration error. -/
theorem calibrated_task_centre_bound
    (model actual : State → Observation) (admissible : State → Prop)
    (alpha residual noise calibration : ℝ) (alphaPositive : 0 < alpha)
    (lower : RestrictedSeparationLowerBound model admissible alpha)
    (target : State → ℝ) (constant : ℝ) (constantNonnegative : 0 ≤ constant)
    (modulus : ∀ first second,
      dist (target first) (target second) ≤ constant * dist first second)
    (candidate truth : State) (data : Observation)
    (candidateAdmissible : admissible candidate) (truthAdmissible : admissible truth)
    (solverBound : dist (model candidate) data ≤ residual)
    (noiseBound : dist data (actual truth) ≤ noise)
    (calibrationBound : dist (actual truth) (model truth) ≤ calibration) :
    |target candidate - target truth| ≤
      constant * ((residual + noise + calibration) / alpha) := by
  simpa [Real.dist_eq] using tomographic_calibrated_task_error_bound
    model actual admissible alpha residual noise calibration alphaPositive lower
    target constant constantNonnegative modulus candidate truth data
    candidateAdmissible truthAdmissible solverBound noiseBound calibrationBound

end CalibratedAdapter

/-- Rewriting around the actual current centre exposes all three error sources. -/
theorem estimated_update_error_identity
    (estimate centre nextCentre gain current disturbance : ℝ) :
    tomographicNoisyFocusUpdate estimate gain current disturbance - nextCentre =
      gain * (current - centre) + (1 - gain) * (estimate - centre) +
        disturbance + (centre - nextCentre) := by
  unfold tomographicNoisyFocusUpdate
  ring

/-- A moving centre and imperfect estimate are separate from actuator noise. -/
theorem estimated_update_error_bound
    (estimate centre nextCentre gain current disturbance error noise drift : ℝ)
    (gainNonnegative : 0 ≤ gain) (gainAtMostOne : gain ≤ 1)
    (estimateBound : |estimate - centre| ≤ error)
    (noiseBound : |disturbance| ≤ noise)
    (driftBound : |centre - nextCentre| ≤ drift) :
    |tomographicNoisyFocusUpdate estimate gain current disturbance - nextCentre| ≤
      gain * |current - centre| + (1 - gain) * error + noise + drift := by
  rw [estimated_update_error_identity]
  have oneMinus : 0 ≤ 1 - gain := sub_nonneg.mpr gainAtMostOne
  calc
    |gain * (current - centre) + (1 - gain) * (estimate - centre) +
        disturbance + (centre - nextCentre)| ≤
        |gain * (current - centre) + (1 - gain) * (estimate - centre) + disturbance| +
          |centre - nextCentre| := abs_add_le _ _
    _ ≤ (|gain * (current - centre) + (1 - gain) * (estimate - centre)| +
        |disturbance|) + |centre - nextCentre| := by
      have triangle := abs_add_le
        (gain * (current - centre) + (1 - gain) * (estimate - centre)) disturbance
      linarith
    _ ≤ ((|gain * (current - centre)| + |(1 - gain) * (estimate - centre)|) +
        |disturbance|) + |centre - nextCentre| := by
      have triangle := abs_add_le
        (gain * (current - centre)) ((1 - gain) * (estimate - centre))
      linarith
    _ = gain * |current - centre| + (1 - gain) * |estimate - centre| +
        |disturbance| + |centre - nextCentre| := by
      rw [abs_mul, abs_mul, abs_of_nonneg gainNonnegative, abs_of_nonneg oneMinus]
    _ ≤ gain * |current - centre| + (1 - gain) * error + noise + drift := by
      have estimateTerm := mul_le_mul_of_nonneg_left estimateBound oneMinus
      linarith

/-- End-to-end composition: the centre error is obtained from the inverse,
not postulated as the final control inequality. -/
theorem inverse_control_error_bound
    {Coordinate View : Type*} [Fintype Coordinate] [Fintype View]
    {rows : View → Coordinate → ℝ}
    (certificate : TomographicStableLeftInverse rows)
    (target : (Coordinate → ℝ) → ℝ) (constant budget : ℝ)
    (constantNonnegative : 0 ≤ constant)
    (modulus : ∀ first second,
      dist (target first) (target second) ≤ constant * dist first second)
    (truth : Coordinate → ℝ) (data : View → ℝ)
    (measurement : dist data (tomographicProjection rows truth) ≤ budget)
    (nextCentre gain current disturbance noise drift : ℝ)
    (gainNonnegative : 0 ≤ gain) (gainAtMostOne : gain ≤ 1)
    (noiseBound : |disturbance| ≤ noise)
    (driftBound : |target truth - nextCentre| ≤ drift) :
    |tomographicNoisyFocusUpdate (target (certificate.reconstruct data)) gain current
        disturbance - nextCentre| ≤
      gain * |current - target truth| +
        (1 - gain) * (constant * (certificate.lipschitzConstant * budget)) + noise + drift := by
  exact estimated_update_error_bound (target (certificate.reconstruct data)) (target truth)
    nextCentre gain current disturbance (constant * (certificate.lipschitzConstant * budget))
    noise drift gainNonnegative gainAtMostOne
    (inverse_task_centre_bound certificate target constant budget constantNonnegative
      modulus truth data measurement) noiseBound driftBound

/-- Strict progress needs a strict error allowance, not merely reconstruction. -/
theorem estimated_update_strict_progress
    (estimate centre nextCentre gain current disturbance error noise drift : ℝ)
    (gainNonnegative : 0 ≤ gain) (gainAtMostOne : gain ≤ 1)
    (estimateBound : |estimate - centre| ≤ error)
    (noiseBound : |disturbance| ≤ noise)
    (driftBound : |centre - nextCentre| ≤ drift)
    (allowance : (1 - gain) * error + noise + drift <
      (1 - gain) * |current - centre|) :
    |tomographicNoisyFocusUpdate estimate gain current disturbance - nextCentre| <
      |current - centre| := by
  have bound := estimated_update_error_bound estimate centre nextCentre gain current
    disturbance error noise drift gainNonnegative gainAtMostOne
    estimateBound noiseBound driftBound
  nlinarith

def adaptationTrajectory (estimate gain disturbance : ℕ → ℝ) (initial : ℝ) : ℕ → ℝ
  | 0 => initial
  | n + 1 => tomographicNoisyFocusUpdate (estimate n) (gain n)
      (adaptationTrajectory estimate gain disturbance initial n) (disturbance n)

def adaptationBudget (gain error noise drift : ℕ → ℝ) (initial : ℝ) : ℕ → ℝ
  | 0 => initial
  | n + 1 => gain n * adaptationBudget gain error noise drift initial n +
      (1 - gain n) * error n + noise n + drift n

/-- Only the steps inside the specified horizon require certificates. -/
theorem adaptation_finite_horizon_bound
    (estimate centre gain disturbance error noise drift : ℕ → ℝ)
    (initial initialBudget : ℝ) (horizon : ℕ)
    (initialBound : |initial - centre 0| ≤ initialBudget)
    (gains : ∀ n < horizon, 0 ≤ gain n ∧ gain n ≤ 1)
    (estimates : ∀ n < horizon, |estimate n - centre n| ≤ error n)
    (noises : ∀ n < horizon, |disturbance n| ≤ noise n)
    (drifts : ∀ n < horizon, |centre n - centre (n + 1)| ≤ drift n) :
    ∀ n ≤ horizon,
      |adaptationTrajectory estimate gain disturbance initial n - centre n| ≤
        adaptationBudget gain error noise drift initialBudget n := by
  intro n
  induction n with
  | zero => intro _; exact initialBound
  | succ n ih =>
    intro within
    have step : n < horizon := by omega
    have previous := ih (by omega)
    have bound := estimated_update_error_bound (estimate n) (centre n) (centre (n + 1))
      (gain n) (adaptationTrajectory estimate gain disturbance initial n)
      (disturbance n) (error n) (noise n) (drift n)
      (gains n step).1 (gains n step).2 (estimates n step) (noises n step) (drifts n step)
    change |tomographicNoisyFocusUpdate (estimate n) (gain n)
      (adaptationTrajectory estimate gain disturbance initial n) (disturbance n) -
        centre (n + 1)| ≤ gain n * adaptationBudget gain error noise drift initialBudget n +
          (1 - gain n) * error n + noise n + drift n
    apply bound.trans
    have previousTerm := mul_le_mul_of_nonneg_left previous (gains n step).1
    linarith

/-- The three injected budgets must jointly fit the available tube allowance. -/
theorem estimated_update_tube_invariant
    (estimate centre nextCentre gain current disturbance error noise drift radius : ℝ)
    (gainNonnegative : 0 ≤ gain) (gainAtMostOne : gain ≤ 1)
    (currentBound : |current - centre| ≤ radius)
    (estimateBound : |estimate - centre| ≤ error)
    (noiseBound : |disturbance| ≤ noise)
    (driftBound : |centre - nextCentre| ≤ drift)
    (allowance : (1 - gain) * error + noise + drift ≤ (1 - gain) * radius) :
    |tomographicNoisyFocusUpdate estimate gain current disturbance - nextCentre| ≤ radius := by
  have bound := estimated_update_error_bound estimate centre nextCentre gain current
    disturbance error noise drift gainNonnegative gainAtMostOne
    estimateBound noiseBound driftBound
  have previous := mul_le_mul_of_nonneg_left currentBound gainNonnegative
  nlinarith

theorem adaptation_finite_horizon_tube
    (estimate centre gain disturbance error noise drift : ℕ → ℝ)
    (initial radius : ℝ) (horizon : ℕ)
    (initialBound : |initial - centre 0| ≤ radius)
    (gains : ∀ n < horizon, 0 ≤ gain n ∧ gain n ≤ 1)
    (estimates : ∀ n < horizon, |estimate n - centre n| ≤ error n)
    (noises : ∀ n < horizon, |disturbance n| ≤ noise n)
    (drifts : ∀ n < horizon, |centre n - centre (n + 1)| ≤ drift n)
    (allowances : ∀ n < horizon,
      (1 - gain n) * error n + noise n + drift n ≤ (1 - gain n) * radius) :
    ∀ n ≤ horizon,
      |adaptationTrajectory estimate gain disturbance initial n - centre n| ≤ radius := by
  intro n
  induction n with
  | zero => intro _; exact initialBound
  | succ n ih =>
    intro within
    have step : n < horizon := by omega
    exact estimated_update_tube_invariant (estimate n) (centre n) (centre (n + 1))
      (gain n) (adaptationTrajectory estimate gain disturbance initial n)
      (disturbance n) (error n) (noise n) (drift n) radius
      (gains n step).1 (gains n step).2 (ih (by omega))
      (estimates n step) (noises n step) (drifts n step) (allowances n step)

/-- This nonzero error remains unchanged despite an exact stationary centre. -/
theorem exact_centre_unit_gain_no_progress :
    |tomographicNoisyFocusUpdate 0 1 1 0 - (0 : ℝ)| = |(1 : ℝ) - 0| := by
  norm_num [tomographicNoisyFocusUpdate]

/-- Exact reconstruction of the current centre does not predict its motion. -/
theorem moving_centre_creates_error :
    |tomographicNoisyFocusUpdate 0 0 0 0 - (1 : ℝ)| = 1 ∧ |(0 : ℝ) - 0| = 0 := by
  norm_num [tomographicNoisyFocusUpdate]

/-- Omitting the estimate error can make even an initially exact state worse. -/
theorem wrong_estimate_creates_error :
    |tomographicNoisyFocusUpdate 2 (1 / 2) 0 0 - (0 : ℝ)| = 1 ∧
      |(0 : ℝ) - 0| = 0 := by
  norm_num [tomographicNoisyFocusUpdate]

/-- A positive allowance is satisfiable with imperfect reconstruction. -/
theorem imperfect_estimate_tube_fixture :
    |tomographicNoisyFocusUpdate (1 / 10) (1 / 2) 1 0 - (0 : ℝ)| = 11 / 20 ∧
      (1 - (1 / 2 : ℝ)) * (1 / 10) + 0 + 0 ≤ (1 - (1 / 2 : ℝ)) * 1 := by
  norm_num [tomographicNoisyFocusUpdate]

end OCScientificExtensions.TomographicAdaptationDynamics
