import OCKIndividuationMSpaceComposition.TomographicTotalVariation
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite variational fusion: data, state energy and graph variation

The data residual, coordinate energy and graph total variation are kept as
separate terms.  This is a finite objective contract only: no minimizer,
convexity, prior validity or denoising claim is inferred from its definition.
-/

section VariationalFusion

variable {Coordinate View : Type*} [Fintype Coordinate] [Fintype View]

/-- A finite variational fusion objective with explicit L2 and TV weights. -/
def tomographicVariationalFusionObjective
    (adjacent : Coordinate → Coordinate → Prop)
    [DecidableRel adjacent]
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (state_weight variation_weight : ℝ) : ℝ :=
  tomographicTikhonovObjective rows state observations state_weight +
    variation_weight * tomographicTotalVariation adjacent state

theorem tomographicVariationalFusionObjective_nonnegative
    (adjacent : Coordinate → Coordinate → Prop)
    [DecidableRel adjacent]
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (state_weight variation_weight : ℝ)
    (state_weight_nonnegative : 0 ≤ state_weight)
    (variation_weight_nonnegative : 0 ≤ variation_weight) :
    0 ≤ tomographicVariationalFusionObjective adjacent rows state observations
      state_weight variation_weight := by
  unfold tomographicVariationalFusionObjective
  exact add_nonneg
    (tomographicTikhonovObjective_nonnegative rows state observations
      state_weight_nonnegative)
    (mul_nonneg variation_weight_nonnegative
      (tomographicTotalVariation_nonnegative adjacent state))

theorem tomographicVariationalFusionObjective_zero_variation
    (adjacent : Coordinate → Coordinate → Prop)
    [DecidableRel adjacent]
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (state_weight : ℝ) :
    tomographicVariationalFusionObjective adjacent rows state observations
      state_weight 0 = tomographicTikhonovObjective rows state observations state_weight := by
  simp [tomographicVariationalFusionObjective]

theorem tomographicVariationalFusionObjective_state_energy_bound
    (adjacent : Coordinate → Coordinate → Prop)
    [DecidableRel adjacent]
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (state_weight variation_weight budget : ℝ)
    (state_weight_positive : 0 < state_weight)
    (variation_weight_nonnegative : 0 ≤ variation_weight)
    (objective_upper :
      tomographicVariationalFusionObjective adjacent rows state observations
        state_weight variation_weight ≤ budget) :
    tomographicStateEnergy state ≤ budget / state_weight := by
  apply (le_div_iff₀ state_weight_positive).mpr
  have tikhonov_nonnegative :=
    tomographicTikhonovObjective_nonnegative rows state observations
      (le_of_lt state_weight_positive)
  have variation_nonnegative :=
    mul_nonneg variation_weight_nonnegative
      (tomographicTotalVariation_nonnegative adjacent state)
  have tikhonov_upper :
      tomographicTikhonovObjective rows state observations state_weight ≤ budget := by
    unfold tomographicVariationalFusionObjective at objective_upper
    linarith
  exact (le_div_iff₀ state_weight_positive).mp
    (tomographicTikhonovObjective_state_energy_bound rows state observations
      state_weight budget state_weight_positive tikhonov_upper)

theorem tomographicVariationalFusionObjective_residual_bound
    (adjacent : Coordinate → Coordinate → Prop)
    [DecidableRel adjacent]
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (state_weight variation_weight budget : ℝ)
    (state_weight_nonnegative : 0 ≤ state_weight)
    (variation_weight_nonnegative : 0 ≤ variation_weight)
    (objective_upper :
      tomographicVariationalFusionObjective adjacent rows state observations
        state_weight variation_weight ≤ budget) :
    tomographicResidualEnergy rows state observations ≤ budget := by
  classical
  have residual_nonnegative :=
    tomographicResidualEnergy_nonnegative rows state observations
  have state_term_nonnegative :
      0 ≤ state_weight * tomographicStateEnergy state :=
    mul_nonneg state_weight_nonnegative
      (tomographicStateEnergy_nonnegative state)
  have variation_term_nonnegative :
      0 ≤ variation_weight * tomographicTotalVariation adjacent state :=
    mul_nonneg variation_weight_nonnegative
      (tomographicTotalVariation_nonnegative adjacent state)
  unfold tomographicVariationalFusionObjective tomographicTikhonovObjective at objective_upper
  linarith

theorem tomographicVariationalFusionObjective_zero_iff_exact_and_zero
    (adjacent : Coordinate → Coordinate → Prop)
    [DecidableRel adjacent]
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (observations : View → ℝ)
    (state_weight variation_weight : ℝ)
    (state_weight_positive : 0 < state_weight)
    (variation_weight_nonnegative : 0 ≤ variation_weight) :
    tomographicVariationalFusionObjective adjacent rows state observations
      state_weight variation_weight = 0 ↔
      (∀ view, tomographicProjection rows state view = observations view) ∧
      (∀ coordinate, state coordinate = 0) := by
  constructor
  · intro objectiveZero
    have tikhonovNonnegative :=
      tomographicTikhonovObjective_nonnegative rows state observations
        (le_of_lt state_weight_positive)
    have variationNonnegative :=
      mul_nonneg variation_weight_nonnegative
        (tomographicTotalVariation_nonnegative adjacent state)
    have tikhonovZero :
        tomographicTikhonovObjective rows state observations state_weight = 0 := by
      unfold tomographicVariationalFusionObjective at objectiveZero
      nlinarith
    exact (tomographicTikhonovObjective_zero_iff_exact_and_zero rows state
      observations state_weight_positive).mp tikhonovZero
  · rintro ⟨exactData, zeroState⟩
    have tikhonovZero := tomographicTikhonovObjective_zero_of_exact_zero rows
      state observations state_weight exactData zeroState
    have variationZero := tomographicTotalVariation_zero_of_constant adjacent
      state 0 zeroState
    unfold tomographicVariationalFusionObjective
    rw [tikhonovZero, variationZero]
    simp

end VariationalFusion

end OCKIndividuationMSpaceComposition
