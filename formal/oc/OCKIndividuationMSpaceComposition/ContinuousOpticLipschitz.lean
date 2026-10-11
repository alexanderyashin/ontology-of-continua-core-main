import Mathlib.Data.Finset.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum

namespace OCKIndividuationMSpaceComposition

/-!
# Continuous optic geometry through a Lipschitz risk envelope

The finite Pareto selector is exact only over a registered finite catalogue.
For a real-valued optic parameter, the mathematically controlled replacement
is a covering contract plus a modulus of risk variation.  The theorem below is
an additive discretisation guarantee: a grid minimiser is within `L * δ` of
the best point whenever every target point has a grid representative at
distance at most `δ` and the risk is `L`-Lipschitz.

This is a genuine boundary, not a promise of universal continuous optimisation:
without a covering radius and a declared modulus, no numerical error claim is
licensed.  The empirical adapter must estimate or conservatively bound `L` and
the reachable covering radius.
-/

/-- A global absolute Lipschitz bound for a scalar optic risk. -/
def LipschitzRisk (risk : ℝ → ℝ) (constant : ℝ) : Prop :=
  0 ≤ constant ∧ ∀ left right,
    |risk left - risk right| ≤ constant * |left - right|

/-- A finite grid covers the declared target region at radius `delta`. -/
def GridCoversAtRadius
    (grid : Finset ℝ) (target : Set ℝ) (delta : ℝ) : Prop :=
  0 ≤ delta ∧ ∀ point, point ∈ target →
    ∃ gridPoint, gridPoint ∈ grid ∧ |point - gridPoint| ≤ delta

/-- Lipschitz transfer from a target optic to a nearby grid optic. -/
theorem lipschitz_risk_nearby_grid_upper_bound
    (risk : ℝ → ℝ) (constant delta target gridPoint : ℝ)
    (lipschitz : LipschitzRisk risk constant)
    (nearby : |target - gridPoint| ≤ delta) :
    risk gridPoint ≤ risk target + constant * delta := by
  have absolute_bound := lipschitz.2 gridPoint target
  have difference_le_abs : risk gridPoint - risk target ≤
      |risk gridPoint - risk target| := le_abs_self _
  have absolute_error_bound : |risk gridPoint - risk target| ≤ constant * delta := by
    calc
      |risk gridPoint - risk target| ≤ constant * |gridPoint - target| :=
        absolute_bound
      _ = constant * |target - gridPoint| := by rw [abs_sub_comm]
      _ ≤ constant * delta :=
        mul_le_mul_of_nonneg_left nearby lipschitz.1
  linarith

/-- Any grid minimiser has an additive `L*delta` regret bound relative to an
arbitrary target point covered by the grid. -/
theorem grid_minimizer_additive_regret_bound
    (risk : ℝ → ℝ) (grid : Finset ℝ) (constant delta target gridPoint chosen : ℝ)
    (lipschitz : LipschitzRisk risk constant)
    (gridPoint_member : gridPoint ∈ grid)
    (chosen_member : chosen ∈ grid)
    (chosen_minimal : ∀ candidate, candidate ∈ grid → risk chosen ≤ risk candidate)
    (nearby : |target - gridPoint| ≤ delta) :
    risk chosen ≤ risk target + constant * delta := by
  exact le_trans (chosen_minimal gridPoint gridPoint_member)
    (lipschitz_risk_nearby_grid_upper_bound risk constant delta target gridPoint
      lipschitz nearby)

/-- On a covered target set, the finite grid minimiser is uniformly within the
declared discretisation error of every target risk value. -/
theorem grid_minimizer_uniform_regret_on_covered_target
    (risk : ℝ → ℝ) (grid : Finset ℝ) (targetSet : Set ℝ)
    (constant delta chosen : ℝ)
    (lipschitz : LipschitzRisk risk constant)
    (chosen_member : chosen ∈ grid)
    (chosen_minimal : ∀ candidate, candidate ∈ grid → risk chosen ≤ risk candidate)
    (cover : GridCoversAtRadius grid targetSet delta) :
    ∀ target, target ∈ targetSet →
      risk chosen ≤ risk target + constant * delta := by
  intro target target_member
  obtain ⟨gridPoint, gridPoint_member, nearby⟩ := cover.2 target target_member
  exact grid_minimizer_additive_regret_bound risk grid constant delta target gridPoint
    chosen lipschitz gridPoint_member chosen_member chosen_minimal nearby

/-- The bound is numerically falsifiable: if an observed grid regret exceeds
`L*delta`, at least one declared premise (cover, Lipschitz modulus, or grid
minimality) is false. -/
theorem observed_regret_exceeding_lipschitz_budget_refutes_contract
    (risk : ℝ → ℝ) (constant delta target chosen : ℝ)
    (lipschitz : LipschitzRisk risk constant)
    (contract_bound : risk chosen ≤ risk target + constant * delta)
    (observed_excess : risk target + constant * delta < risk chosen) :
    False := by
  linarith

end OCKIndividuationMSpaceComposition
