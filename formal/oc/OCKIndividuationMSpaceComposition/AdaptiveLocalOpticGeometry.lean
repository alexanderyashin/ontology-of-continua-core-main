import Mathlib.Data.Finset.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Topology.MetricSpace.Pseudo.Defs
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

universe uOptic

open scoped BigOperators

/-!
# Adaptive local and anisotropic optic geometry

The global `L * delta` grid guarantee is often needlessly pessimistic.  This
module separates three claims which an empirical optic adapter must not blur:

* a target-indexed local modulus and target-indexed cover radius license the
  local numerical budget `L(target) * delta(target)`;
* a coordinatewise modulus licenses the sharper anisotropic budget
  `sum_i L_i * delta_i`, and that expression is attained by a linear risk;
* without any modulus, observations on a finite grid give no finite control of
  off-grid regret: an arbitrarily deep spike is observationally identical on
  every sampled grid point.

The first two statements are OC adapters of standard Lipschitz discretisation
mathematics.  The third is the exact information boundary that tells the
experimental layer which regularity assumption must be measured or falsified.
-/

/-- A target-indexed risk modulus.  The modulus may be small in a benign local
region even when no useful global Lipschitz constant exists. -/
def PointwiseMetricRiskModulus
    {Optic : Type uOptic}
    [PseudoMetricSpace Optic]
    (risk : Optic → ℝ)
    (modulus : Optic → ℝ) : Prop :=
  (∀ target, 0 ≤ modulus target) ∧
    ∀ target candidate,
      |risk candidate - risk target| ≤ modulus target * dist candidate target

/-- A finite catalogue with a target-indexed cover radius. -/
def AdaptiveMetricGridCover
    {Optic : Type uOptic}
    [PseudoMetricSpace Optic]
    (grid : Finset Optic)
    (targetSet : Set Optic)
    (radius : Optic → ℝ) : Prop :=
  ∀ target, target ∈ targetSet →
    0 ≤ radius target ∧
      ∃ gridPoint, gridPoint ∈ grid ∧ dist target gridPoint ≤ radius target

/-- A nearby catalogue point inherits a target-specific risk budget. -/
theorem pointwise_metric_nearby_grid_upper_bound
    {Optic : Type uOptic}
    [PseudoMetricSpace Optic]
    (risk : Optic → ℝ)
    (modulus radius : Optic → ℝ)
    (target gridPoint : Optic)
    (regularity : PointwiseMetricRiskModulus risk modulus)
    (nearby : dist target gridPoint ≤ radius target) :
    risk gridPoint ≤ risk target + modulus target * radius target := by
  have absolute_bound := regularity.2 target gridPoint
  have difference_le_abs :
      risk gridPoint - risk target ≤ |risk gridPoint - risk target| :=
    le_abs_self _
  have absolute_error_bound :
      |risk gridPoint - risk target| ≤ modulus target * radius target := by
    calc
      |risk gridPoint - risk target| ≤
          modulus target * dist gridPoint target := absolute_bound
      _ = modulus target * dist target gridPoint := by rw [dist_comm]
      _ ≤ modulus target * radius target :=
        mul_le_mul_of_nonneg_left nearby (regularity.1 target)
  linarith

/-- A grid minimiser obeys the local, rather than worst-case global, budget. -/
theorem adaptive_local_grid_minimizer_regret_bound
    {Optic : Type uOptic}
    [PseudoMetricSpace Optic]
    (risk : Optic → ℝ)
    (grid : Finset Optic)
    (targetSet : Set Optic)
    (modulus radius : Optic → ℝ)
    (chosen : Optic)
    (regularity : PointwiseMetricRiskModulus risk modulus)
    (chosen_minimal : ∀ candidate, candidate ∈ grid → risk chosen ≤ risk candidate)
    (cover : AdaptiveMetricGridCover grid targetSet radius) :
    ∀ target, target ∈ targetSet →
      risk chosen ≤ risk target + modulus target * radius target := by
  intro target target_member
  obtain ⟨_, gridPoint, gridPoint_member, nearby⟩ := cover target target_member
  exact le_trans (chosen_minimal gridPoint gridPoint_member)
    (pointwise_metric_nearby_grid_upper_bound risk modulus radius target gridPoint
      regularity nearby)

/-- Measured regret above the local budget falsifies at least one premise of
the local regularity, cover, or minimisation contract. -/
theorem observed_local_regret_excess_refutes_adaptive_contract
    {Optic : Type uOptic}
    [PseudoMetricSpace Optic]
    (risk : Optic → ℝ)
    (modulus radius : Optic → ℝ)
    (target chosen : Optic)
    (contract_bound :
      risk chosen ≤ risk target + modulus target * radius target)
    (observed_excess :
      risk target + modulus target * radius target < risk chosen) :
    False := by
  linarith

/-- A risk with an arbitrarily deep value at one unobserved target and zero
everywhere else. -/
def OffGridSpikeRisk
    {Optic : Type uOptic}
    [DecidableEq Optic]
    (target : Optic)
    (gap : ℝ)
    (point : Optic) : ℝ :=
  if point = target then -gap else 0

/-- **No-go theorem.**  For every requested gap, a finite grid that omits the
target admits a risk indistinguishable from zero on the whole grid yet having
exactly that regret at the target.  Finite samples alone therefore cannot
license any off-grid numerical bound without a regularity premise. -/
theorem finite_grid_without_modulus_has_unbounded_off_grid_regret
    {Optic : Type uOptic}
    [DecidableEq Optic]
    (grid : Finset Optic)
    (target chosen : Optic)
    (target_not_observed : target ∉ grid)
    (chosen_observed : chosen ∈ grid)
    (gap : ℝ) :
    (∀ point, point ∈ grid → OffGridSpikeRisk target gap point = 0) ∧
      OffGridSpikeRisk target gap chosen - OffGridSpikeRisk target gap target = gap := by
  have chosen_ne_target : chosen ≠ target := by
    intro chosen_eq_target
    apply target_not_observed
    simpa [chosen_eq_target] using chosen_observed
  constructor
  · intro point point_observed
    have point_ne_target : point ≠ target := by
      intro point_eq_target
      apply target_not_observed
      simpa [point_eq_target] using point_observed
    simp [OffGridSpikeRisk, point_ne_target]
  · simp [OffGridSpikeRisk, chosen_ne_target]

/-- Coordinatewise weighted regularity on a finite-dimensional optic. -/
def CoordinatewiseRiskModulus
    {dimension : ℕ}
    (risk : (Fin dimension → ℝ) → ℝ)
    (weight : Fin dimension → ℝ) : Prop :=
  (∀ coordinate, 0 ≤ weight coordinate) ∧
    ∀ left right,
      |risk left - risk right| ≤
        ∑ coordinate, weight coordinate * |left coordinate - right coordinate|

/-- Coordinatewise cover tolerances between two optic settings. -/
def CoordinatewiseNear
    {dimension : ℕ}
    (left right tolerance : Fin dimension → ℝ) : Prop :=
  ∀ coordinate,
    |left coordinate - right coordinate| ≤ tolerance coordinate

/-- A coordinatewise modulus turns a vector cover into the additive anisotropic
budget `sum_i L_i * delta_i`. -/
theorem coordinatewise_nearby_optic_upper_bound
    {dimension : ℕ}
    (risk : (Fin dimension → ℝ) → ℝ)
    (weight tolerance : Fin dimension → ℝ)
    (target gridPoint : Fin dimension → ℝ)
    (regularity : CoordinatewiseRiskModulus risk weight)
    (nearby : CoordinatewiseNear gridPoint target tolerance) :
    risk gridPoint ≤ risk target +
      ∑ coordinate, weight coordinate * tolerance coordinate := by
  have absolute_bound := regularity.2 gridPoint target
  have coordinate_budget :
      (∑ coordinate, weight coordinate *
        |gridPoint coordinate - target coordinate|) ≤
      ∑ coordinate, weight coordinate * tolerance coordinate := by
    apply Finset.sum_le_sum
    intro coordinate _
    exact mul_le_mul_of_nonneg_left (nearby coordinate)
      (regularity.1 coordinate)
  have difference_le_abs :
      risk gridPoint - risk target ≤ |risk gridPoint - risk target| :=
    le_abs_self _
  linarith

/-- A finite-catalogue minimiser inherits the anisotropic budget. -/
theorem anisotropic_grid_minimizer_regret_bound
    {dimension : ℕ}
    (risk : (Fin dimension → ℝ) → ℝ)
    (grid : Finset (Fin dimension → ℝ))
    (weight tolerance : Fin dimension → ℝ)
    (target gridPoint chosen : Fin dimension → ℝ)
    (regularity : CoordinatewiseRiskModulus risk weight)
    (gridPoint_member : gridPoint ∈ grid)
    (chosen_minimal : ∀ candidate, candidate ∈ grid → risk chosen ≤ risk candidate)
    (nearby : CoordinatewiseNear gridPoint target tolerance) :
    risk chosen ≤ risk target +
      ∑ coordinate, weight coordinate * tolerance coordinate := by
  exact le_trans (chosen_minimal gridPoint gridPoint_member)
    (coordinatewise_nearby_optic_upper_bound risk weight tolerance target gridPoint
      regularity nearby)

/-- Linear coordinate risk witnesses sharpness of the anisotropic expression. -/
def LinearCoordinateRisk
    {dimension : ℕ}
    (weight : Fin dimension → ℝ)
    (optic : Fin dimension → ℝ) : ℝ :=
  ∑ coordinate, weight coordinate * optic coordinate

/-- Nonnegative linear coordinate risk satisfies exactly the declared
coordinatewise modulus. -/
theorem linear_coordinate_risk_has_coordinatewise_modulus
    {dimension : ℕ}
    (weight : Fin dimension → ℝ)
    (weight_nonnegative : ∀ coordinate, 0 ≤ weight coordinate) :
    CoordinatewiseRiskModulus (LinearCoordinateRisk weight) weight := by
  constructor
  · exact weight_nonnegative
  · intro left right
    calc
      |LinearCoordinateRisk weight left - LinearCoordinateRisk weight right| =
          |∑ coordinate, weight coordinate *
            (left coordinate - right coordinate)| := by
            rw [LinearCoordinateRisk, LinearCoordinateRisk,
              ← Finset.sum_sub_distrib]
            congr 1
            apply Finset.sum_congr rfl
            intro coordinate _
            ring
      _ ≤ ∑ coordinate,
          |weight coordinate * (left coordinate - right coordinate)| :=
            Finset.abs_sum_le_sum_abs _ _
      _ = ∑ coordinate,
          weight coordinate * |left coordinate - right coordinate| := by
            apply Finset.sum_congr rfl
            intro coordinate _
            rw [abs_mul, abs_of_nonneg (weight_nonnegative coordinate)]

/-- The anisotropic budget is sharp: for nonnegative coordinate displacements,
linear risk attains `sum_i L_i * delta_i` exactly. -/
theorem anisotropic_lipschitz_budget_is_attainable
    {dimension : ℕ}
    (weight tolerance : Fin dimension → ℝ)
    (weight_nonnegative : ∀ coordinate, 0 ≤ weight coordinate)
    (tolerance_nonnegative : ∀ coordinate, 0 ≤ tolerance coordinate) :
    CoordinatewiseRiskModulus (LinearCoordinateRisk weight) weight ∧
      CoordinatewiseNear tolerance (fun _ => 0) tolerance ∧
        LinearCoordinateRisk weight tolerance -
          LinearCoordinateRisk weight (fun _ => 0) =
            ∑ coordinate, weight coordinate * tolerance coordinate := by
  constructor
  · exact linear_coordinate_risk_has_coordinatewise_modulus weight
      weight_nonnegative
  · constructor
    · intro coordinate
      simp [abs_of_nonneg (tolerance_nonnegative coordinate)]
    · simp [LinearCoordinateRisk]

/-- Exceeding the anisotropic budget is a direct falsifier of the registered
coordinatewise regularity/cover/minimisation chain. -/
theorem observed_anisotropic_regret_excess_refutes_contract
    {dimension : ℕ}
    (risk : (Fin dimension → ℝ) → ℝ)
    (weight tolerance : Fin dimension → ℝ)
    (target chosen : Fin dimension → ℝ)
    (contract_bound :
      risk chosen ≤ risk target +
        ∑ coordinate, weight coordinate * tolerance coordinate)
    (observed_excess :
      risk target +
        ∑ coordinate, weight coordinate * tolerance coordinate < risk chosen) :
    False := by
  linarith

end OCKIndividuationMSpaceComposition
