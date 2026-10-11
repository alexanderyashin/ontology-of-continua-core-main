import OCKIndividuationMSpaceComposition.FiniteConditionalKLChain

namespace OCKIndividuationMSpaceComposition

/-!
## Information accumulation on an arbitrary finite horizon

This module turns the one-step conditional KL identity into a reusable
finite-horizon metamechanics.  `conditionalIncrement n` is the information
contributed by the registered observation at step `n`; `jointInformation n`
is the total information available after `n` steps.  The only structural
contract is the exact one-step chain rule.  Consequently every conclusion
below applies to finite adaptive histories once that one-step contract has
been discharged at each history state.
-/

/-- An exact finite-horizon information process.  This is deliberately not
an independence assumption: a conditional increment may already average
over the complete registered history. -/
structure FiniteHorizonInformationProcess where
  jointInformation : ℕ → ℝ
  conditionalIncrement : ℕ → ℝ
  chainRule : ∀ n,
    jointInformation (n + 1) =
      jointInformation n + conditionalIncrement n

namespace FiniteHorizonInformationProcess

/-- Every increment schedule and initial information value generate an exact
finite-horizon process. -/
noncomputable def ofIncrements (initial : ℝ) (increment : ℕ → ℝ) :
    FiniteHorizonInformationProcess where
  jointInformation n := initial + ∑ i ∈ Finset.range n, increment i
  conditionalIncrement := increment
  chainRule n := by
    rw [Finset.sum_range_succ]
    ring

@[simp]
theorem ofIncrements_jointInformation
    (initial : ℝ) (increment : ℕ → ℝ) (n : ℕ) :
    (ofIncrements initial increment).jointInformation n =
      initial + ∑ i ∈ Finset.range n, increment i := rfl

@[simp]
theorem ofIncrements_conditionalIncrement
    (initial : ℝ) (increment : ℕ → ℝ) (n : ℕ) :
    (ofIncrements initial increment).conditionalIncrement n = increment n := rfl

/-- Arbitrary-horizon chain rule: total information is initial information
plus the sum of all registered conditional increments. -/
theorem jointInformation_eq_initial_add_sum
    (process : FiniteHorizonInformationProcess) (n : ℕ) :
    process.jointInformation n = process.jointInformation 0 +
      ∑ i ∈ Finset.range n, process.conditionalIncrement i := by
  induction n with
  | zero => simp
  | succ n ih =>
      rw [process.chainRule n, ih, Finset.sum_range_succ]
      ring

/-- Windowed chain rule.  It is the formal license for replaying any finite
subhistory rather than only histories beginning at time zero. -/
theorem jointInformation_add_eq_add_window
    (process : FiniteHorizonInformationProcess) (start horizon : ℕ) :
    process.jointInformation (start + horizon) =
      process.jointInformation start +
        ∑ i ∈ Finset.range horizon,
          process.conditionalIncrement (start + i) := by
  induction horizon with
  | zero => simp
  | succ horizon ih =>
      rw [Nat.add_succ, process.chainRule (start + horizon), ih,
        Finset.sum_range_succ]
      ring

/-- Nonnegative conditional information makes the finite-horizon information
monotone. -/
theorem jointInformation_monotone
    (process : FiniteHorizonInformationProcess)
    (incrementNonnegative : ∀ n, 0 ≤ process.conditionalIncrement n) :
    Monotone process.jointInformation := by
  apply monotone_nat_of_le_succ
  intro n
  rw [process.chainRule n]
  exact le_add_of_nonneg_right (incrementNonnegative n)

/-- If all observations in a window are conditionally unchanged, that window
adds exactly zero information. -/
theorem zero_increment_window_is_information_flat
    (process : FiniteHorizonInformationProcess) (start horizon : ℕ)
    (zeroIncrement : ∀ i < horizon,
      process.conditionalIncrement (start + i) = 0) :
    process.jointInformation (start + horizon) =
      process.jointInformation start := by
  rw [process.jointInformation_add_eq_add_window start horizon]
  have sumZero :
      (∑ i ∈ Finset.range horizon,
        process.conditionalIncrement (start + i)) = 0 := by
    apply Finset.sum_eq_zero
    intro i hi
    exact zeroIncrement i (Finset.mem_range.mp hi)
  rw [sumZero, add_zero]

/-- A per-step observability ceiling yields an exact linear upper budget on
all information that any finite record can accumulate. -/
theorem jointInformation_le_initial_add_horizon_mul
    (process : FiniteHorizonInformationProcess) (capacity : ℝ) (horizon : ℕ)
    (incrementLe : ∀ i < horizon,
      process.conditionalIncrement i ≤ capacity) :
    process.jointInformation horizon ≤
      process.jointInformation 0 + horizon * capacity := by
  rw [process.jointInformation_eq_initial_add_sum horizon]
  gcongr
  calc
    (∑ i ∈ Finset.range horizon, process.conditionalIncrement i) ≤
        ∑ _i ∈ Finset.range horizon, capacity := by
      apply Finset.sum_le_sum
      intro i hi
      exact incrementLe i (Finset.mem_range.mp hi)
    _ = horizon * capacity := by simp

/-- Budget no-go theorem.  If the required discrimination exceeds the
initial information plus every possible observed increment, the target is
unreachable by that horizon for every predictor satisfying the capacity
contract. -/
theorem information_target_unreachable_under_capacity
    (process : FiniteHorizonInformationProcess) (capacity target : ℝ)
    (horizon : ℕ)
    (incrementLe : ∀ i < horizon,
      process.conditionalIncrement i ≤ capacity)
    (targetAboveCapacity :
      process.jointInformation 0 + horizon * capacity < target) :
    ¬ target ≤ process.jointInformation horizon := by
  have upper := process.jointInformation_le_initial_add_horizon_mul
    capacity horizon incrementLe
  linarith

/-- Matching positive theorem.  A certified lower information yield at every
step guarantees at least linear accumulation. -/
theorem initial_add_horizon_mul_le_jointInformation
    (process : FiniteHorizonInformationProcess) (yield : ℝ) (horizon : ℕ)
    (yieldLe : ∀ i < horizon,
      yield ≤ process.conditionalIncrement i) :
    process.jointInformation 0 + horizon * yield ≤
      process.jointInformation horizon := by
  rw [process.jointInformation_eq_initial_add_sum horizon]
  gcongr
  calc
    horizon * yield = ∑ _i ∈ Finset.range horizon, yield := by simp
    _ ≤ ∑ i ∈ Finset.range horizon,
        process.conditionalIncrement i := by
      apply Finset.sum_le_sum
      intro i hi
      exact yieldLe i (Finset.mem_range.mp hi)

/-- A sufficient horizon condition stated in the units used by experimental
design: if each registered occurrence contributes at least `yield`, then any
target below `initial + horizon * yield` is attained. -/
theorem information_target_reached_under_yield
    (process : FiniteHorizonInformationProcess) (yield target : ℝ)
    (horizon : ℕ)
    (yieldLe : ∀ i < horizon,
      yield ≤ process.conditionalIncrement i)
    (targetWithinYield :
      target ≤ process.jointInformation 0 + horizon * yield) :
    target ≤ process.jointInformation horizon :=
  targetWithinYield.trans
    (process.initial_add_horizon_mul_le_jointInformation yield horizon yieldLe)

/-- Exact closed form for a constant-yield experiment. -/
theorem constant_increment_information_exact
    (initial yield : ℝ) (horizon : ℕ) :
    (ofIncrements initial (fun _ => yield)).jointInformation horizon =
      initial + horizon * yield := by
  simp [ofIncrements]

/-- Any observation-dependent stopping rule whose realized index is bounded
by `horizon` remains inside the same capacity budget.  This is a deterministic
bounded-index theorem; a genuinely stochastic optional-stopping theorem still
requires a filtration and martingale/integrability hypotheses. -/
theorem jointInformation_at_bounded_index_le_budget
    (process : FiniteHorizonInformationProcess) (capacity : ℝ)
    (stop horizon : ℕ)
    (capacityNonnegative : 0 ≤ capacity)
    (stopLeHorizon : stop ≤ horizon)
    (incrementLe : ∀ i < horizon,
      process.conditionalIncrement i ≤ capacity) :
    process.jointInformation stop ≤
      process.jointInformation 0 + horizon * capacity := by
  have incrementLeStop : ∀ i < stop,
      process.conditionalIncrement i ≤ capacity := by
    intro i hi
    exact incrementLe i (lt_of_lt_of_le hi stopLeHorizon)
  have stopBudget := process.jointInformation_le_initial_add_horizon_mul
    capacity stop incrementLeStop
  have mulLe : (stop : ℝ) * capacity ≤ horizon * capacity := by
    gcongr
  linarith

/-- Bounded-stopping no-go: choosing when to stop cannot defeat a proved
per-observation information ceiling. -/
theorem bounded_stopping_cannot_reach_target_above_capacity
    (process : FiniteHorizonInformationProcess) (capacity target : ℝ)
    (stop horizon : ℕ)
    (capacityNonnegative : 0 ≤ capacity)
    (stopLeHorizon : stop ≤ horizon)
    (incrementLe : ∀ i < horizon,
      process.conditionalIncrement i ≤ capacity)
    (targetAboveCapacity :
      process.jointInformation 0 + horizon * capacity < target) :
    ¬ target ≤ process.jointInformation stop := by
  have upper := process.jointInformation_at_bounded_index_le_budget capacity
    stop horizon capacityNonnegative stopLeHorizon incrementLe
  linarith

/-- Information acquired immediately. -/
def earlyIncrement (n : ℕ) : ℝ := if n = 0 then 1 else 0

/-- The same total information acquired one registered occurrence later. -/
def lateIncrement (n : ℕ) : ℝ := if n = 1 then 1 else 0

theorem early_and_late_same_two_step_budget :
    (∑ i ∈ Finset.range 2, earlyIncrement i) =
      ∑ i ∈ Finset.range 2, lateIncrement i := by
  norm_num [earlyIncrement, lateIncrement]

theorem early_and_late_have_different_first_increment :
    earlyIncrement 0 ≠ lateIncrement 0 := by
  norm_num [earlyIncrement, lateIncrement]

/-- Endpoint no-go: even exact initial and final information do not identify
when an informative intervention occurred.  The two generated processes have
the same two-step endpoint but distinct first-step histories. -/
theorem equal_information_endpoint_does_not_identify_timing :
    (ofIncrements 0 earlyIncrement).jointInformation 2 =
        (ofIncrements 0 lateIncrement).jointInformation 2 ∧
      (ofIncrements 0 earlyIncrement).jointInformation 1 ≠
        (ofIncrements 0 lateIncrement).jointInformation 1 := by
  constructor
  · simp only [ofIncrements_jointInformation]
    rw [early_and_late_same_two_step_budget]
  · norm_num [ofIncrements, earlyIncrement, lateIncrement]

end FiniteHorizonInformationProcess

end OCKIndividuationMSpaceComposition
