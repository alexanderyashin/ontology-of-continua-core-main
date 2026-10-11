import Mathlib.Data.Finset.Basic
import Mathlib.Topology.MetricSpace.Pseudo.Defs
import Mathlib.Tactic.Linarith

namespace OCKIndividuationMSpaceComposition

universe uOptic

/-!
# Metric (hence multidimensional) adaptive-optic geometry

The scalar `ContinuousOpticLipschitz` contract is a one-dimensional instance
of a more useful statement.  A risk on any pseudo-metric optic space with a
declared Lipschitz modulus transfers from a finite covering grid with the
same additive `L * delta` regret.  No coordinates, convexity, differentiability,
or existence of a global optimum are smuggled in.  A Euclidean or product
optic domain is admitted only through its registered metric and a finite cover.
-/

/-- A global metric-Lipschitz bound for a real-valued optic risk. -/
def MetricLipschitzRisk
    {Optic : Type uOptic}
    [PseudoMetricSpace Optic]
    (risk : Optic → ℝ)
    (constant : ℝ) : Prop :=
  0 ≤ constant ∧ ∀ left right,
    |risk left - risk right| ≤ constant * dist left right

/-- A finite optic catalogue covers a target region at metric radius `delta`. -/
def MetricGridCoversAtRadius
    {Optic : Type uOptic}
    [PseudoMetricSpace Optic]
    (grid : Finset Optic)
    (target : Set Optic)
    (delta : ℝ) : Prop :=
  0 ≤ delta ∧ ∀ point, point ∈ target →
    ∃ gridPoint, gridPoint ∈ grid ∧ dist point gridPoint ≤ delta

/-- Metric Lipschitz transfer from a target optic to a nearby grid optic. -/
theorem metric_lipschitz_nearby_grid_upper_bound
    {Optic : Type uOptic}
    [PseudoMetricSpace Optic]
    (risk : Optic → ℝ)
    (constant delta : ℝ)
    (target gridPoint : Optic)
    (lipschitz : MetricLipschitzRisk risk constant)
    (nearby : dist target gridPoint ≤ delta) :
    risk gridPoint ≤ risk target + constant * delta := by
  have absolute_bound := lipschitz.2 gridPoint target
  have difference_le_abs : risk gridPoint - risk target ≤
      |risk gridPoint - risk target| := le_abs_self _
  have absolute_error_bound : |risk gridPoint - risk target| ≤
      constant * delta := by
    calc
      |risk gridPoint - risk target| ≤ constant * dist gridPoint target :=
        absolute_bound
      _ = constant * dist target gridPoint := by rw [dist_comm]
      _ ≤ constant * delta :=
        mul_le_mul_of_nonneg_left nearby lipschitz.1
  linarith

/-- Any metric-grid minimiser has additive `L*delta` regret. -/
theorem metric_grid_minimizer_additive_regret_bound
    {Optic : Type uOptic}
    [PseudoMetricSpace Optic]
    (risk : Optic → ℝ)
    (grid : Finset Optic)
    (constant delta : ℝ)
    (target gridPoint chosen : Optic)
    (lipschitz : MetricLipschitzRisk risk constant)
    (gridPoint_member : gridPoint ∈ grid)
    (chosen_minimal : ∀ candidate, candidate ∈ grid →
      risk chosen ≤ risk candidate)
    (nearby : dist target gridPoint ≤ delta) :
    risk chosen ≤ risk target + constant * delta := by
  exact le_trans (chosen_minimal gridPoint gridPoint_member)
    (metric_lipschitz_nearby_grid_upper_bound risk constant delta target gridPoint
      lipschitz nearby)

/-- Uniform metric-grid regret on a covered target set. -/
theorem metric_grid_minimizer_uniform_regret_on_covered_target
    {Optic : Type uOptic}
    [PseudoMetricSpace Optic]
    (risk : Optic → ℝ)
    (grid : Finset Optic)
    (targetSet : Set Optic)
    (constant delta : ℝ)
    (chosen : Optic)
    (lipschitz : MetricLipschitzRisk risk constant)
    (chosen_minimal : ∀ candidate, candidate ∈ grid →
      risk chosen ≤ risk candidate)
    (cover : MetricGridCoversAtRadius grid targetSet delta) :
    ∀ target, target ∈ targetSet →
      risk chosen ≤ risk target + constant * delta := by
  intro target target_member
  obtain ⟨gridPoint, gridPoint_member, nearby⟩ := cover.2 target target_member
  exact metric_grid_minimizer_additive_regret_bound risk grid constant delta
    target gridPoint chosen lipschitz gridPoint_member
    chosen_minimal nearby

/-- An observed excess above the metric budget refutes at least one declared
cover, modulus, or minimisation premise. -/
theorem observed_metric_regret_exceeding_lipschitz_budget_refutes_contract
    {Optic : Type uOptic}
    [PseudoMetricSpace Optic]
    (risk : Optic → ℝ)
    (constant delta : ℝ)
    (target chosen : Optic)
    (contract_bound : risk chosen ≤ risk target + constant * delta)
    (observed_excess : risk target + constant * delta < risk chosen) :
    False := by
  linarith

end OCKIndividuationMSpaceComposition
