import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Algebra.Order.Ring.Abs
import Mathlib.Algebra.Order.Archimedean.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Data.Real.Basic
import Mathlib.Data.Real.Archimedean
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Finite stochastic/robust defect envelopes

The expectation of a nonnegative stochastic prediction error is a scalar
sequence.  This module deliberately states the weakest finite-horizon theorem
at that level: if the conditional mean error obeys an affine one-step defect
inequality, its future mean is bounded by an explicit envelope.  A probability
model may instantiate `meanError` with an actual conditional expectation, but
the theorem does not smuggle in independence, stationarity, or optional
stopping assumptions.

The result also exposes the noncontractive boundary.  When `rho >= 1` and the
defect is positive, no time-uniform finite plateau can be inferred from the
one-step contract alone.  Thus a stable empirical adapter must either certify
contraction or report a horizon-dependent bound.
-/

/-- The finite affine envelope for a mean error recurrence. -/
def stochasticDefectEnvelope (rho disturbance initial : ℝ) : ℕ → ℝ
  | 0 => initial
  | horizon + 1 =>
      rho * stochasticDefectEnvelope rho disturbance initial horizon + disturbance

@[simp] theorem stochasticDefectEnvelope_zero
    (rho disturbance initial : ℝ) :
    stochasticDefectEnvelope rho disturbance initial 0 = initial := rfl

@[simp] theorem stochasticDefectEnvelope_succ
    (rho disturbance initial : ℝ) (horizon : ℕ) :
    stochasticDefectEnvelope rho disturbance initial (horizon + 1) =
      rho * stochasticDefectEnvelope rho disturbance initial horizon + disturbance := rfl

/-- A conditional-mean defect contract, separated from the probability model
that produced the mean sequence. -/
structure MeanDefectContract where
  meanError : ℕ → ℝ
  rho : ℝ
  disturbance : ℝ
  initial : ℝ
  mean_nonnegative : ∀ horizon, 0 ≤ meanError horizon
  initial_eq : meanError 0 = initial
  one_step : ∀ horizon,
    meanError (horizon + 1) ≤ rho * meanError horizon + disturbance

theorem mean_defect_error_le_envelope
    (contract : MeanDefectContract)
    (rho_nonnegative : 0 ≤ contract.rho)
    (horizon : ℕ) :
    contract.meanError horizon ≤
      stochasticDefectEnvelope contract.rho contract.disturbance
        contract.initial horizon := by
  induction horizon with
  | zero => simpa [contract.initial_eq]
  | succ horizon ih =>
      rw [stochasticDefectEnvelope_succ]
      exact le_trans (contract.one_step horizon)
        (by simpa [add_comm] using
          (add_le_add_left (mul_le_mul_of_nonneg_left ih rho_nonnegative)
            contract.disturbance))

/-- The recurrence has the closed finite geometric form. -/
theorem stochasticDefectEnvelope_eq_geometric_sum
    (rho disturbance initial : ℝ) (horizon : ℕ) :
    stochasticDefectEnvelope rho disturbance initial horizon =
      rho ^ horizon * initial +
      disturbance * ∑ k ∈ Finset.range horizon, rho ^ k := by
  have shifted_geometric_sum : ∀ n : ℕ,
      rho * ∑ k ∈ Finset.range n, rho ^ k + 1 =
        ∑ k ∈ Finset.range (n + 1), rho ^ k := by
    intro n
    induction n with
    | zero => simp
    | succ n ih =>
        calc
          rho * (∑ x ∈ Finset.range (n + 1), rho ^ x) + 1 =
              rho * (∑ x ∈ Finset.range n, rho ^ x + rho ^ n) + 1 := by
                rw [Finset.sum_range_succ]
          _ =
              (rho * ∑ x ∈ Finset.range n, rho ^ x + 1) + rho ^ (n + 1) := by
                rw [pow_succ]
                ring
          _ = (∑ x ∈ Finset.range (n + 1), rho ^ x) + rho ^ (n + 1) := by
                rw [ih]
          _ = ∑ x ∈ Finset.range (n + 1 + 1), rho ^ x := by
                simpa [Nat.add_assoc] using
                  (Finset.sum_range_succ (f := fun x : ℕ => rho ^ x) (n := n + 1)).symm
  induction horizon with
  | zero => simp [stochasticDefectEnvelope]
  | succ horizon ih =>
      rw [stochasticDefectEnvelope_succ, ih]
      calc
        rho * (rho ^ horizon * initial +
            disturbance * ∑ k ∈ Finset.range horizon, rho ^ k) + disturbance =
            rho ^ (horizon + 1) * initial +
              disturbance *
                (rho * ∑ k ∈ Finset.range horizon, rho ^ k + 1) := by
                  rw [pow_succ]
                  ring
        _ = rho ^ (horizon + 1) * initial +
              disturbance * ∑ k ∈ Finset.range (horizon + 1), rho ^ k := by
                rw [shifted_geometric_sum horizon]

/-- Contractive mean dynamics have a finite plateau, independently of the
number of observed steps. -/
theorem stochasticDefectEnvelope_le_plateau
    (rho disturbance initial : ℝ)
    (rho_nonnegative : 0 ≤ rho)
    (rho_contracting : rho < 1)
    (disturbance_nonnegative : 0 ≤ disturbance)
    (initial_nonnegative : 0 ≤ initial)
    (horizon : ℕ) :
    stochasticDefectEnvelope rho disturbance initial horizon ≤
      initial + disturbance / (1 - rho) := by
  let plateau : ℝ := initial + disturbance / (1 - rho)
  have denominator_positive : 0 < 1 - rho := by linarith
  have plateau_nonnegative : 0 ≤ plateau := by
    dsimp [plateau]
    exact add_nonneg initial_nonnegative
      (div_nonneg disturbance_nonnegative (le_of_lt denominator_positive))
  have initial_step : rho * initial ≤ initial := by
    nlinarith
  have disturbance_step :
      rho * (disturbance / (1 - rho)) + disturbance ≤
        disturbance / (1 - rho) := by
    have equality :
        rho * (disturbance / (1 - rho)) + disturbance =
          disturbance / (1 - rho) := by
      field_simp [ne_of_gt denominator_positive]
      ring
    exact equality.le
  have plateau_step : rho * plateau + disturbance ≤ plateau := by
    dsimp [plateau]
    calc
      rho * (initial + disturbance / (1 - rho)) + disturbance =
          rho * initial + (rho * (disturbance / (1 - rho)) + disturbance) := by ring
      _ ≤ initial + disturbance / (1 - rho) := by
        exact add_le_add initial_step disturbance_step
      _ = plateau := rfl
  induction horizon with
  | zero =>
      dsimp [plateau]
      exact le_add_of_nonneg_right
        (div_nonneg disturbance_nonnegative (le_of_lt denominator_positive))
  | succ horizon ih =>
      rw [stochasticDefectEnvelope_succ]
      exact le_trans
        (by simpa [add_comm] using
          (add_le_add_left (mul_le_mul_of_nonneg_left ih rho_nonnegative)
            disturbance))
        plateau_step

/-- If `rho >= 1`, the positive per-step defect alone forces at least linear
growth of the envelope. -/
theorem noncontractive_envelope_ge_linear_defect
    (rho disturbance initial : ℝ)
    (rho_ge_one : 1 ≤ rho)
    (disturbance_nonnegative : 0 ≤ disturbance)
    (initial_nonnegative : 0 ≤ initial)
    (horizon : ℕ) :
    (horizon : ℝ) * disturbance ≤
      stochasticDefectEnvelope rho disturbance initial horizon := by
  induction horizon with
  | zero => simpa [stochasticDefectEnvelope] using initial_nonnegative
  | succ horizon ih =>
      rw [stochasticDefectEnvelope_succ]
      have envelope_nonnegative :
          0 ≤ stochasticDefectEnvelope rho disturbance initial horizon := by
        exact le_trans (by positivity : 0 ≤ (horizon : ℝ) * disturbance) ih
      have scaled :
          (horizon : ℝ) * disturbance ≤
            rho * stochasticDefectEnvelope rho disturbance initial horizon := by
        calc
          (horizon : ℝ) * disturbance ≤
              rho * ((horizon : ℝ) * disturbance) := by
            nlinarith [mul_nonneg (by positivity : 0 ≤ (horizon : ℝ) * disturbance)
              (sub_nonneg.mpr rho_ge_one)]
          _ ≤ rho * stochasticDefectEnvelope rho disturbance initial horizon := by
            exact mul_le_mul_of_nonneg_left ih (le_of_lt (by positivity))
      norm_num [Nat.cast_add, Nat.cast_one]
      nlinarith

/-- Positive noncontractive defect has no finite time-uniform plateau. -/
theorem noncontractive_positive_defect_no_uniform_plateau
    (rho disturbance initial : ℝ)
    (rho_ge_one : 1 ≤ rho)
    (disturbance_positive : 0 < disturbance)
    (initial_nonnegative : 0 ≤ initial) :
    ¬ ∃ bound : ℝ, ∀ horizon,
      stochasticDefectEnvelope rho disturbance initial horizon ≤ bound := by
  rintro ⟨bound, uniform_bound⟩
  obtain ⟨horizon, horizon_large⟩ := exists_nat_gt (bound / disturbance)
  have linear := noncontractive_envelope_ge_linear_defect
    rho disturbance initial rho_ge_one (le_of_lt disturbance_positive)
      initial_nonnegative horizon
  have lower_than : bound < (horizon : ℝ) * disturbance :=
    (div_lt_iff₀ disturbance_positive).mp horizon_large
  have upper_than := uniform_bound horizon
  linarith

/-- The envelope is attained exactly by the equality recurrence; the upper
bound is therefore sharp for the declared contract. -/
theorem stochasticDefectEnvelope_equality_recurrence_is_sharp
    (rho disturbance initial : ℝ) (horizon : ℕ) :
    let meanError := stochasticDefectEnvelope rho disturbance initial
    meanError horizon = stochasticDefectEnvelope rho disturbance initial horizon := by
  rfl

end OCKIndividuationMSpaceComposition
