import Mathlib.Algebra.Group.Hom.End
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Abel
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum

namespace OCKIndividuationMSpaceComposition

/-!
Time-varying and model-mismatch mechanics for coupled systems.  This extends
the constant coupling adapter without assuming that one frozen operator remains
valid across a frame change, deployment, reconfiguration, or phase regime.
-/

variable {X : Type*} [AddCommGroup X]

/-- `x(t+1) = A_t x(t) + b_t`. -/
def timeVaryingCoupledTrajectory
    (operator : ℕ → X →+ X) (forcing : ℕ → X) (x0 : X) : ℕ → X
  | 0 => x0
  | t + 1 => operator t (timeVaryingCoupledTrajectory operator forcing x0 t) +
      forcing t

@[simp] theorem timeVaryingCoupledTrajectory_zero
    (operator : ℕ → X →+ X) (forcing : ℕ → X) (x0 : X) :
    timeVaryingCoupledTrajectory operator forcing x0 0 = x0 := rfl

@[simp] theorem timeVaryingCoupledTrajectory_succ
    (operator : ℕ → X →+ X) (forcing : ℕ → X) (x0 : X) (t : ℕ) :
    timeVaryingCoupledTrajectory operator forcing x0 (t + 1) =
      operator t (timeVaryingCoupledTrajectory operator forcing x0 t) +
        forcing t := rfl

/-- Chronologically ordered product `P_t = A_(t-1) ... A_0`. -/
def timeOrderedPropagation (operator : ℕ → X →+ X) : ℕ → X →+ X
  | 0 => AddMonoidHom.id X
  | t + 1 => (operator t).comp (timeOrderedPropagation operator t)

/-- Accumulated response to the complete time-dependent forcing schedule. -/
def accumulatedTimeVaryingForcing
    (operator : ℕ → X →+ X) (forcing : ℕ → X) : ℕ → X
  | 0 => 0
  | t + 1 => operator t (accumulatedTimeVaryingForcing operator forcing t) +
      forcing t

/-- Exact noncommutative product decomposition at every finite horizon. -/
theorem timeVaryingCoupledTrajectory_exact_decomposition
    (operator : ℕ → X →+ X) (forcing : ℕ → X) (x0 : X)
    (horizon : ℕ) :
    timeVaryingCoupledTrajectory operator forcing x0 horizon =
      timeOrderedPropagation operator horizon x0 +
        accumulatedTimeVaryingForcing operator forcing horizon := by
  induction horizon with
  | zero => simp [timeVaryingCoupledTrajectory, timeOrderedPropagation,
      accumulatedTimeVaryingForcing]
  | succ horizon ih =>
      simp only [timeVaryingCoupledTrajectory_succ, timeOrderedPropagation,
        accumulatedTimeVaryingForcing, AddMonoidHom.comp_apply]
      rw [ih, (operator horizon).map_add]
      abel

/-- Exact intervention response under the same time-dependent forcing. -/
theorem timeVaryingCoupledTrajectory_initial_difference_eq_product
    (operator : ℕ → X →+ X) (forcing : ℕ → X) (first second : X)
    (horizon : ℕ) :
    timeVaryingCoupledTrajectory operator forcing first horizon -
        timeVaryingCoupledTrajectory operator forcing second horizon =
      timeOrderedPropagation operator horizon (first - second) := by
  induction horizon with
  | zero => simp [timeVaryingCoupledTrajectory, timeOrderedPropagation]
  | succ horizon ih =>
      simp only [timeVaryingCoupledTrajectory_succ, timeOrderedPropagation,
        AddMonoidHom.comp_apply]
      calc
        (operator horizon
              (timeVaryingCoupledTrajectory operator forcing first horizon) +
            forcing horizon) -
            (operator horizon
                (timeVaryingCoupledTrajectory operator forcing second horizon) +
              forcing horizon) =
            operator horizon
              (timeVaryingCoupledTrajectory operator forcing first horizon -
                timeVaryingCoupledTrajectory operator forcing second horizon) := by
                  rw [(operator horizon).map_sub]
                  abel
        _ = operator horizon
              (timeOrderedPropagation operator horizon (first - second)) := by
                rw [ih]

/-- Full superposition for two time-dependent forcing schedules. -/
theorem timeVaryingCoupledTrajectory_full_difference
    (operator : ℕ → X →+ X) (firstForcing secondForcing : ℕ → X)
    (first second : X) (horizon : ℕ) :
    timeVaryingCoupledTrajectory operator firstForcing first horizon -
        timeVaryingCoupledTrajectory operator secondForcing second horizon =
      timeVaryingCoupledTrajectory operator
        (fun t => firstForcing t - secondForcing t) (first - second) horizon := by
  induction horizon with
  | zero => simp [timeVaryingCoupledTrajectory]
  | succ horizon ih =>
      simp only [timeVaryingCoupledTrajectory_succ]
      calc
        (operator horizon
              (timeVaryingCoupledTrajectory operator firstForcing first horizon) +
            firstForcing horizon) -
            (operator horizon
                (timeVaryingCoupledTrajectory operator secondForcing second horizon) +
              secondForcing horizon) =
            operator horizon
                (timeVaryingCoupledTrajectory operator firstForcing first horizon -
                  timeVaryingCoupledTrajectory operator secondForcing second horizon) +
              (firstForcing horizon - secondForcing horizon) := by
                rw [(operator horizon).map_sub]
                abel
        _ = operator horizon
                (timeVaryingCoupledTrajectory operator
                  (fun t => firstForcing t - secondForcing t)
                  (first - second) horizon) +
              (firstForcing horizon - secondForcing horizon) := by rw [ih]

/-- Rational scaling as an additive endomorphism. -/
def rationalScaleEndomorphism (scale : ℚ) : ℚ →+ ℚ where
  toFun value := scale * value
  map_zero' := mul_zero scale
  map_add' first second := mul_add scale first second

/-- Two-step schedule: amplify first, then retain. -/
def earlyAmplificationSchedule : ℕ → ℚ →+ ℚ
  | 0 => rationalScaleEndomorphism 2
  | _ => AddMonoidHom.id ℚ

/-- Two-step schedule: retain first, then amplify. -/
def lateAmplificationSchedule : ℕ → ℚ →+ ℚ
  | 0 => AddMonoidHom.id ℚ
  | _ => rationalScaleEndomorphism 2

/--
Endpoint-product no-go: equal two-step endpoints do not identify the ordered
operator schedule.  The intermediate observation distinguishes the schedules.
-/
theorem endpoint_product_does_not_identify_operator_schedule :
    earlyAmplificationSchedule 0 ≠ lateAmplificationSchedule 0 ∧
    timeVaryingCoupledTrajectory earlyAmplificationSchedule (fun _ => 0) 1 2 =
      timeVaryingCoupledTrajectory lateAmplificationSchedule (fun _ => 0) 1 2 ∧
    timeVaryingCoupledTrajectory earlyAmplificationSchedule (fun _ => 0) 1 1 ≠
      timeVaryingCoupledTrajectory lateAmplificationSchedule (fun _ => 0) 1 1 := by
  constructor
  · intro equalOperators
    have atOne := DFunLike.congr_fun equalOperators (1 : ℚ)
    norm_num [earlyAmplificationSchedule, lateAmplificationSchedule,
      rationalScaleEndomorphism] at atOne
  · constructor <;>
      norm_num [timeVaryingCoupledTrajectory, earlyAmplificationSchedule,
        lateAmplificationSchedule, rationalScaleEndomorphism]

/-- Recursive worst-case error under time-dependent local gain and residual. -/
def timeVaryingErrorEnvelope
    (gain residual : ℕ → ℚ) (initialError : ℚ) : ℕ → ℚ
  | 0 => initialError
  | t + 1 => gain t * timeVaryingErrorEnvelope gain residual initialError t +
      residual t

/--
Positive robust theorem for nonlinear or misspecified dynamics: if each step's
error is bounded by a time-dependent gain times the previous error plus a
declared residual, the computable envelope bounds every finite horizon.
-/
theorem timeVarying_model_mismatch_error_bound
    (actual predicted : ℕ → ℚ) (gain residual : ℕ → ℚ)
    (gainNonnegative : ∀ t, 0 ≤ gain t)
    (stepBound : ∀ t,
      |actual (t + 1) - predicted (t + 1)| ≤
        gain t * |actual t - predicted t| + residual t)
    (horizon : ℕ) :
    |actual horizon - predicted horizon| ≤
      timeVaryingErrorEnvelope gain residual
        |actual 0 - predicted 0| horizon := by
  induction horizon with
  | zero => simp [timeVaryingErrorEnvelope]
  | succ horizon ih =>
      calc
        |actual (horizon + 1) - predicted (horizon + 1)| ≤
            gain horizon * |actual horizon - predicted horizon| +
              residual horizon := stepBound horizon
        _ ≤ gain horizon *
              timeVaryingErrorEnvelope gain residual
                |actual 0 - predicted 0| horizon + residual horizon := by
            have scaled :=
              mul_le_mul_of_nonneg_left ih (gainNonnegative horizon)
            linarith
        _ = timeVaryingErrorEnvelope gain residual
              |actual 0 - predicted 0| (horizon + 1) := rfl

/-- A forecast strictly below threshold by more than its error is certified below. -/
theorem forecast_margin_certifies_below_threshold
    (actual predicted error threshold : ℚ)
    (errorBound : |actual - predicted| ≤ error)
    (margin : predicted + error < threshold) :
    actual < threshold := by
  have bounds := (abs_le.mp errorBound).2
  linarith

/-- A forecast strictly above threshold by more than its error is certified above. -/
theorem forecast_margin_certifies_above_threshold
    (actual predicted error threshold : ℚ)
    (errorBound : |actual - predicted| ≤ error)
    (margin : threshold < predicted - error) :
    threshold < actual := by
  have bounds := (abs_le.mp errorBound).1
  linarith

end OCKIndividuationMSpaceComposition
