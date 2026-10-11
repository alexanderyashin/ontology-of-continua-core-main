import OCKIndividuationMSpaceComposition.TomographicNormalOperator
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite Tikhonov objective for tomographic fusion

The residual term enforces agreement with all registered projections, while a
nonnegative state penalty expresses an explicit regularization choice.  The
definitions are finite and auditable; a minimizer, prior, or noise law must be
provided separately and is never inferred from a small residual.
-/


section Tikhonov

variable {Coordinate View : Type*} [Fintype Coordinate] [Fintype View]

/-- Squared energy of a reconstructed finite state. -/
def tomographicStateEnergy
    (state : Coordinate → ℝ) : ℝ :=
  ∑ coordinate, (state coordinate) ^ 2

theorem tomographicStateEnergy_nonnegative
    (state : Coordinate → ℝ) :
    0 ≤ tomographicStateEnergy state := by
  exact Finset.sum_nonneg (fun coordinate _ => sq_nonneg _)

theorem tomographicStateEnergy_zero_iff
    (state : Coordinate → ℝ) :
    tomographicStateEnergy state = 0 ↔
      ∀ coordinate, state coordinate = 0 := by
  classical
  constructor
  · intro energyZero
    have everySquareZero :
        (fun coordinate => (state coordinate) ^ 2) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
        sq_nonneg (state coordinate))).mp energyZero
    intro coordinate
    exact sq_eq_zero_iff.mp (congrFun everySquareZero coordinate)
  · intro everyZero
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
      sq_nonneg (state coordinate))).mpr
    funext coordinate
    simp [everyZero coordinate]

/-- Finite Tikhonov objective: data residual plus explicit state penalty. -/
def tomographicTikhonovObjective
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (regularization : ℝ) : ℝ :=
  tomographicResidualEnergy rows state observations +
    regularization * tomographicStateEnergy state

theorem tomographicTikhonovObjective_nonnegative
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (regularization_nonnegative : 0 ≤ regularization) :
    0 ≤ tomographicTikhonovObjective rows state observations regularization := by
  classical
  unfold tomographicTikhonovObjective
  exact add_nonneg
    (tomographicResidualEnergy_nonnegative rows state observations)
    (mul_nonneg regularization_nonnegative (tomographicStateEnergy_nonnegative state))

theorem tomographicTikhonovObjective_zero_regularization
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ) :
    tomographicTikhonovObjective rows state observations 0 =
      tomographicResidualEnergy rows state observations := by
  simp [tomographicTikhonovObjective]

theorem tomographicTikhonovObjective_state_energy_bound
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (regularization budget : ℝ)
    (regularization_positive : 0 < regularization)
    (objective_upper :
      tomographicTikhonovObjective rows state observations regularization ≤ budget) :
    tomographicStateEnergy state ≤ budget / regularization := by
  classical
  apply (le_div_iff₀ regularization_positive).mpr
  have residual_nonnegative :=
    tomographicResidualEnergy_nonnegative rows state observations
  unfold tomographicTikhonovObjective at objective_upper
  linarith

theorem tomographicTikhonovObjective_residual_bound
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (regularization budget : ℝ)
    (regularization_nonnegative : 0 ≤ regularization)
    (objective_upper :
      tomographicTikhonovObjective rows state observations regularization ≤ budget) :
    tomographicResidualEnergy rows state observations ≤ budget := by
  classical
  have state_term_nonnegative :
      0 ≤ regularization * tomographicStateEnergy state :=
    mul_nonneg regularization_nonnegative
      (tomographicStateEnergy_nonnegative state)
  unfold tomographicTikhonovObjective at objective_upper
  linarith

theorem tomographicTikhonovObjective_zero_of_exact_zero
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (regularization : ℝ)
    (exact_data : ∀ view, tomographicProjection rows state view = observations view)
    (zero_state : ∀ coordinate, state coordinate = 0) :
    tomographicTikhonovObjective rows state observations regularization = 0 := by
  classical
  unfold tomographicTikhonovObjective
  rw [(tomographicResidualEnergy_zero_iff_exact rows state observations).mpr exact_data]
  rw [(tomographicStateEnergy_zero_iff state).mpr zero_state]
  simp

theorem tomographicTikhonovObjective_zero_iff_exact_and_zero
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (regularization_positive : 0 < regularization) :
    tomographicTikhonovObjective rows state observations regularization = 0 ↔
      (∀ view, tomographicProjection rows state view = observations view) ∧
      (∀ coordinate, state coordinate = 0) := by
  classical
  constructor
  · intro objectiveZero
    have residualNonnegative :=
      tomographicResidualEnergy_nonnegative rows state observations
    have stateEnergyNonnegative := tomographicStateEnergy_nonnegative state
    have regularizedNonnegative :
        0 ≤ regularization * tomographicStateEnergy state :=
      mul_nonneg (le_of_lt regularization_positive) stateEnergyNonnegative
    have residualZero : tomographicResidualEnergy rows state observations = 0 := by
      unfold tomographicTikhonovObjective at objectiveZero
      nlinarith
    have stateEnergyZero : tomographicStateEnergy state = 0 := by
      unfold tomographicTikhonovObjective at objectiveZero
      nlinarith
    exact ⟨(tomographicResidualEnergy_zero_iff_exact rows state observations).mp residualZero,
      (tomographicStateEnergy_zero_iff state).mp stateEnergyZero⟩
  · rintro ⟨exact_data, zero_state⟩
    exact tomographicTikhonovObjective_zero_of_exact_zero rows state observations
      regularization exact_data zero_state

end Tikhonov

end OCKIndividuationMSpaceComposition
