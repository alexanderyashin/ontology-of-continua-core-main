import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Registered computational refocus

The operator below is the finite weighted shift-and-sum primitive used by
computational photography and light-field refocusing. `warp` is an explicit
registration map from a requested output coordinate to the sampled coordinate
of each view. The exactness theorem requires a normalized weight family and
pointwise registered agreement; it does not infer registration, depth, or
semantic identity from the operator's name.
-/


section Refocus

variable {Coordinate View : Type*} [Fintype View]

def tomographicWeightedRefocus
    (weight : View → ℝ)
    (image : View → Coordinate → ℝ)
    (warp : View → Coordinate → Coordinate) : Coordinate → ℝ :=
  fun coordinate => ∑ view, weight view * image view (warp view coordinate)

theorem tomographicWeightedRefocus_error_decomposition
    (weight : View → ℝ)
    (image : View → Coordinate → ℝ)
    (warp : View → Coordinate → Coordinate)
    (truth : Coordinate → ℝ) (coordinate : Coordinate) :
    tomographicWeightedRefocus weight image warp coordinate - truth coordinate =
      (∑ view, weight view *
        (image view (warp view coordinate) - truth coordinate)) +
        (∑ view, weight view - 1) * truth coordinate := by
  unfold tomographicWeightedRefocus
  simp_rw [mul_sub]
  rw [Finset.sum_sub_distrib, ← Finset.sum_mul]
  ring

theorem tomographicWeightedRefocus_error_bound
    (weight : View → ℝ)
    (image : View → Coordinate → ℝ)
    (warp : View → Coordinate → Coordinate)
    (truth : Coordinate → ℝ)
    (bound : View → ℝ)
    (coordinate : Coordinate)
    (weight_nonnegative : ∀ view, 0 ≤ weight view)
    (weights_normalized : ∑ view, weight view = 1)
    (registered_error : ∀ view,
      |image view (warp view coordinate) - truth coordinate| ≤ bound view) :
    |tomographicWeightedRefocus weight image warp coordinate - truth coordinate| ≤
      ∑ view, weight view * bound view := by
  rw [tomographicWeightedRefocus_error_decomposition]
  rw [weights_normalized]
  simp only [sub_self, zero_mul, add_zero]
  calc
    |∑ view, weight view *
        (image view (warp view coordinate) - truth coordinate)| ≤
        ∑ view, |weight view *
          (image view (warp view coordinate) - truth coordinate)| :=
      Finset.abs_sum_le_sum_abs _ _
    _ = ∑ view, weight view *
        |image view (warp view coordinate) - truth coordinate| := by
      apply Finset.sum_congr rfl
      intro view _
      rw [abs_mul, abs_of_nonneg (weight_nonnegative view)]
    _ ≤ ∑ view, weight view * bound view := by
      apply Finset.sum_le_sum
      intro view _
      exact mul_le_mul_of_nonneg_left (registered_error view)
        (weight_nonnegative view)

theorem tomographicWeightedRefocus_zero_weight
    (image : View → Coordinate → ℝ)
    (warp : View → Coordinate → Coordinate) :
    tomographicWeightedRefocus (fun _ => 0) image warp = 0 := by
  funext coordinate
  simp [tomographicWeightedRefocus]

theorem tomographicWeightedRefocus_add
    (weight : View → ℝ)
    (left right : View → Coordinate → ℝ)
    (warp : View → Coordinate → Coordinate) :
    tomographicWeightedRefocus weight
        (fun view coordinate => left view coordinate + right view coordinate) warp =
      fun coordinate =>
        tomographicWeightedRefocus weight left warp coordinate +
          tomographicWeightedRefocus weight right warp coordinate := by
  funext coordinate
  unfold tomographicWeightedRefocus
  rw [← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro view _
  rw [mul_add]

theorem tomographicWeightedRefocus_exact_if_registered
    (weight : View → ℝ)
    (image : View → Coordinate → ℝ)
    (warp : View → Coordinate → Coordinate)
    (truth : Coordinate → ℝ)
    (weights_normalized : ∑ view, weight view = 1)
    (registered : ∀ view coordinate,
      image view (warp view coordinate) = truth coordinate) :
    tomographicWeightedRefocus weight image warp = truth := by
  funext coordinate
  unfold tomographicWeightedRefocus
  calc
    (∑ view, weight view * image view (warp view coordinate)) =
        ∑ view, weight view * truth coordinate := by
      apply Finset.sum_congr rfl
      intro view _
      rw [registered]
    _ = (∑ view, weight view) * truth coordinate := by
      rw [Finset.sum_mul]
    _ = truth coordinate := by
      rw [weights_normalized]
      ring

end Refocus

end OCKIndividuationMSpaceComposition
