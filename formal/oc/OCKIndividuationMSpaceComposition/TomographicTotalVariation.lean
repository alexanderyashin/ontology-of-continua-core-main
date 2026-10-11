import OCKIndividuationMSpaceComposition.TomographicTikhonov
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Tactic.Ring
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite total-variation regularisation for tomographic states

Tomographic image reconstruction often separates data agreement from a
total-variation (TV) penalty so that edges are not treated as independent
Gaussian energy.  Here the adjacency relation is an explicit finite contract;
no geometric neighbourhood, connectedness, or edge-preservation claim is
inferred from the coordinate type alone.
-/


section TotalVariation

variable {Coordinate : Type*} [Fintype Coordinate]

/-- Finite graph total variation over an explicitly declared adjacency relation. -/
def tomographicTotalVariation
    (adjacent : Coordinate → Coordinate → Prop)
    [DecidableRel adjacent]
    (state : Coordinate → ℝ) : ℝ :=
  ∑ left, ∑ right,
    if adjacent left right then |state left - state right| else 0

theorem tomographicTotalVariation_nonnegative
    (adjacent : Coordinate → Coordinate → Prop)
    [DecidableRel adjacent]
    (state : Coordinate → ℝ) :
    0 ≤ tomographicTotalVariation adjacent state := by
  unfold tomographicTotalVariation
  apply Finset.sum_nonneg
  intro left _
  apply Finset.sum_nonneg
  intro right _
  by_cases edge : adjacent left right <;> simp [edge, abs_nonneg]

theorem tomographicTotalVariation_zero_of_constant
    (adjacent : Coordinate → Coordinate → Prop)
    [DecidableRel adjacent]
    (state : Coordinate → ℝ)
    (constant : ℝ)
    (is_constant : ∀ coordinate, state coordinate = constant) :
    tomographicTotalVariation adjacent state = 0 := by
  unfold tomographicTotalVariation
  apply Finset.sum_eq_zero
  intro left _
  apply Finset.sum_eq_zero
  intro right _
  by_cases edge : adjacent left right <;>
    simp [edge, is_constant left, is_constant right]

theorem tomographicTotalVariation_shift_invariant
    (adjacent : Coordinate → Coordinate → Prop)
    [DecidableRel adjacent]
    (state : Coordinate → ℝ)
    (shift : ℝ) :
    tomographicTotalVariation adjacent (fun coordinate => state coordinate + shift) =
      tomographicTotalVariation adjacent state := by
  unfold tomographicTotalVariation
  apply Finset.sum_congr rfl
  intro left _
  apply Finset.sum_congr rfl
  intro right _
  by_cases edge : adjacent left right
  · simp only [if_pos edge]
    congr 1
    ring
  · simp [edge]

theorem tomographicTotalVariation_mono_of_adjacency
    (adjacent₁ adjacent₂ : Coordinate → Coordinate → Prop)
    [DecidableRel adjacent₁] [DecidableRel adjacent₂]
    (state : Coordinate → ℝ)
    (included : ∀ left right, adjacent₁ left right → adjacent₂ left right) :
    tomographicTotalVariation adjacent₁ state ≤
      tomographicTotalVariation adjacent₂ state := by
  unfold tomographicTotalVariation
  apply Finset.sum_le_sum
  intro left _
  apply Finset.sum_le_sum
  intro right _
  by_cases edge₁ : adjacent₁ left right
  · have edge₂ : adjacent₂ left right := included left right edge₁
    simp [edge₁, edge₂]
  · by_cases edge₂ : adjacent₂ left right
    · simp [edge₁, edge₂, abs_nonneg]
    · simp [edge₁, edge₂]

end TotalVariation

end OCKIndividuationMSpaceComposition