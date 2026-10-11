import OCKIndividuationMSpaceComposition.TomographicProjectionMatrix
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition


/-!
# Finite Gram pairing of a registered projection family

The Gram pairing records how two candidate states co-vary across all declared
views.  Its diagonal is the normal energy already used by the projection
matrix layer, while the off-diagonal terms retain cross-view interaction
information without constructing an unverified inverse or covariance model.
-/

section GramPair

variable {Coordinate View : Type*} [Fintype Coordinate] [Fintype View] [DecidableEq View]

/-- Cross-view Gram pairing induced by a finite projection family. -/
def tomographicGramPair
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ) : ℝ :=
  ∑ view, tomographicProjection rows left view *
    tomographicProjection rows right view

theorem tomographicGramPair_symmetric
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicGramPair rows left right =
      tomographicGramPair rows right left := by
  unfold tomographicGramPair
  apply Finset.sum_congr rfl
  intro view _
  ring

theorem tomographicGramPair_self_eq_normalEnergy
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    tomographicGramPair rows state state =
      tomographicNormalEnergy rows state := by
  unfold tomographicGramPair tomographicNormalEnergy
  apply Finset.sum_congr rfl
  intro view _
  simp [pow_two]

theorem tomographicGramPair_self_nonnegative
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    0 ≤ tomographicGramPair rows state state := by
  rw [tomographicGramPair_self_eq_normalEnergy]
  exact tomographicNormalEnergy_nonnegative rows state

theorem tomographicGramPair_abs_bound
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ)
    (left_bound right_bound : View → ℝ)
    (left_bound_nonnegative : ∀ view, 0 ≤ left_bound view)
    (right_bound_nonnegative : ∀ view, 0 ≤ right_bound view)
    (left_projection_bound : ∀ view,
      |tomographicProjection rows left view| ≤ left_bound view)
    (right_projection_bound : ∀ view,
      |tomographicProjection rows right view| ≤ right_bound view) :
    |tomographicGramPair rows left right| ≤
      ∑ view, left_bound view * right_bound view := by
  unfold tomographicGramPair
  calc
    |∑ view, tomographicProjection rows left view *
        tomographicProjection rows right view| ≤
        ∑ view, |tomographicProjection rows left view *
          tomographicProjection rows right view| := by
      exact Finset.abs_sum_le_sum_abs _ _
    _ = ∑ view, |tomographicProjection rows left view| *
        |tomographicProjection rows right view| := by
      apply Finset.sum_congr rfl
      intro view _
      rw [abs_mul]
    _ ≤ ∑ view, left_bound view * right_bound view := by
      apply Finset.sum_le_sum
      intro view _
      calc
        |tomographicProjection rows left view| *
            |tomographicProjection rows right view| ≤
            |tomographicProjection rows left view| * right_bound view :=
          mul_le_mul_of_nonneg_left (right_projection_bound view)
            (abs_nonneg _)
        _ ≤ left_bound view * right_bound view :=
          mul_le_mul_of_nonneg_right (left_projection_bound view)
            (right_bound_nonnegative view)

theorem tomographicGramPair_self_zero_iff_all_views_zero
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    tomographicGramPair rows state state = 0 ↔
      ∀ view, tomographicProjection rows state view = 0 := by
  rw [tomographicGramPair_self_eq_normalEnergy]
  exact tomographicNormalEnergy_zero_iff rows state

/-! The dual finite matrix records inner products between the registered
    projection rows themselves.  It is deliberately a geometric diagnostic,
    not a claim that an inverse or covariance model has been identified. -/

/-- Finite Gram matrix of the projection rows across coordinates. -/
def tomographicViewGramMatrix
    (rows : View → Coordinate → ℝ) : View → View → ℝ :=
  fun left right => ∑ coordinate, rows left coordinate * rows right coordinate

theorem tomographicViewGramMatrix_symmetric
    (rows : View → Coordinate → ℝ)
    (left right : View) :
    tomographicViewGramMatrix rows left right =
      tomographicViewGramMatrix rows right left := by
  unfold tomographicViewGramMatrix
  apply Finset.sum_congr rfl
  intro coordinate _
  ring

theorem tomographicViewGramMatrix_diagonal_nonnegative
    (rows : View → Coordinate → ℝ)
    (view : View) :
    0 ≤ tomographicViewGramMatrix rows view view := by
  unfold tomographicViewGramMatrix
  simpa [pow_two] using
    (Finset.sum_nonneg (fun coordinate _ => sq_nonneg (rows view coordinate)))

theorem tomographicViewGramMatrix_diagonal_zero_iff_row_zero
    (rows : View → Coordinate → ℝ)
    (view : View) :
    tomographicViewGramMatrix rows view view = 0 ↔
      ∀ coordinate, rows view coordinate = 0 := by
  constructor
  · intro diagonalZero
    have everySquareZero :
        (fun coordinate => (rows view coordinate) ^ 2) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
        sq_nonneg (rows view coordinate))).mp (by
          simpa [tomographicViewGramMatrix, pow_two] using diagonalZero)
    intro coordinate
    have selected := congrFun everySquareZero coordinate
    exact sq_eq_zero_iff.mp selected
  · intro rowZero
    unfold tomographicViewGramMatrix
    simp_rw [← pow_two]
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
      sq_nonneg (rows view coordinate))).mpr
    funext coordinate
    simp [pow_two, rowZero coordinate]

theorem tomographicViewGramMatrix_all_diagonal_zero_iff_rows_zero
    (rows : View → Coordinate → ℝ) :
    (∀ view, tomographicViewGramMatrix rows view view = 0) ↔
      ∀ view coordinate, rows view coordinate = 0 := by
  constructor
  · intro allZero view coordinate
    exact (tomographicViewGramMatrix_diagonal_zero_iff_row_zero rows view).mp
      (allZero view) coordinate
  · intro allRowsZero view
    exact (tomographicViewGramMatrix_diagonal_zero_iff_row_zero rows view).mpr
      (allRowsZero view)

theorem tomographicViewGramMatrix_eq_zero_iff_rows_zero
    (rows : View → Coordinate → ℝ) :
    tomographicViewGramMatrix rows = 0 ↔
      ∀ view coordinate, rows view coordinate = 0 := by
  constructor
  · intro matrixZero
    apply (tomographicViewGramMatrix_all_diagonal_zero_iff_rows_zero rows).mp
    intro view
    have diagonalZero := congrFun (congrFun matrixZero view) view
    exact diagonalZero
  · intro allRowsZero
    funext left right
    unfold tomographicViewGramMatrix
    apply Finset.sum_eq_zero
    intro coordinate _
    simp [allRowsZero left coordinate, allRowsZero right coordinate]

/-! The row Gram matrix also carries a positive-semidefinite quadratic-energy
    certificate.  This is an algebraic PSD statement for the registered finite
    rows only; it does not assert rank, conditioning, or an identified inverse. -/

def tomographicViewGramQuadraticEnergy
    (rows : View → Coordinate → ℝ)
    (weights : View → ℝ) : ℝ :=
  ∑ coordinate, (∑ view, weights view * rows view coordinate) ^ 2

theorem tomographicViewGramQuadraticEnergy_nonnegative
    (rows : View → Coordinate → ℝ)
    (weights : View → ℝ) :
    0 ≤ tomographicViewGramQuadraticEnergy rows weights := by
  unfold tomographicViewGramQuadraticEnergy
  exact Finset.sum_nonneg (fun coordinate _ => sq_nonneg _)

theorem tomographicViewGramQuadraticEnergy_eq_gram_form
    (rows : View → Coordinate → ℝ)
    (weights : View → ℝ) :
    tomographicViewGramQuadraticEnergy rows weights =
      ∑ left, ∑ right,
        weights left * tomographicViewGramMatrix rows left right * weights right := by
  classical
  unfold tomographicViewGramQuadraticEnergy tomographicViewGramMatrix
  calc
    ∑ coordinate, (∑ view, weights view * rows view coordinate) ^ 2 =
        ∑ coordinate, ∑ left, ∑ right,
          (weights left * rows left coordinate) *
            (weights right * rows right coordinate) := by
      apply Finset.sum_congr rfl
      intro coordinate _
      rw [pow_two, Fintype.sum_mul_sum]
    _ = ∑ left, ∑ right, ∑ coordinate,
          (weights left * rows left coordinate) *
            (weights right * rows right coordinate) := by
      rw [Finset.sum_comm]
      apply Fintype.sum_congr
      intro left
      rw [Finset.sum_comm]
    _ = ∑ left, ∑ right,
          weights left * (∑ coordinate, rows left coordinate * rows right coordinate) *
            weights right := by
      apply Fintype.sum_congr
      intro left
      apply Fintype.sum_congr
      intro right
      rw [Finset.mul_sum, Finset.sum_mul]
      apply Finset.sum_congr rfl
      intro coordinate _
      ring

theorem tomographicViewGramQuadraticEnergy_zero_iff_weighted_row_zero
    (rows : View → Coordinate → ℝ)
    (weights : View → ℝ) :
    tomographicViewGramQuadraticEnergy rows weights = 0 ↔
      ∀ coordinate, ∑ view, weights view * rows view coordinate = 0 := by
  constructor
  · intro energyZero coordinate
    have everySquareZero :
        (fun coordinate =>
          (∑ view, weights view * rows view coordinate) ^ 2) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
        sq_nonneg (∑ view, weights view * rows view coordinate))).mp
        energyZero
    exact sq_eq_zero_iff.mp (congrFun everySquareZero coordinate)
  · intro everyZero
    unfold tomographicViewGramQuadraticEnergy
    change (∑ coordinate, (∑ view, weights view * rows view coordinate) ^ 2) = 0
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
      sq_nonneg (∑ view, weights view * rows view coordinate))).mpr
    funext coordinate
    simp [everyZero coordinate]

/-! Selected-view Gram energy is the bounded counterpart used by adaptive view
selection. Unlike normal energy it is not additive under view union because
the weighted row sum carries cross terms; its exact zero boundary remains
pointwise and therefore safe for pruning decisions. -/

def tomographicViewGramQuadraticEnergyOn
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (weights : View → ℝ) : ℝ :=
  ∑ coordinate, (∑ view ∈ views, weights view * rows view coordinate) ^ 2

theorem tomographicViewGramQuadraticEnergyOn_nonnegative
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (weights : View → ℝ) :
    0 ≤ tomographicViewGramQuadraticEnergyOn views rows weights := by
  unfold tomographicViewGramQuadraticEnergyOn
  exact Finset.sum_nonneg (fun coordinate _ => sq_nonneg _)

theorem tomographicViewGramQuadraticEnergyOn_univ_eq
    (rows : View → Coordinate → ℝ)
    (weights : View → ℝ) :
    tomographicViewGramQuadraticEnergyOn Finset.univ rows weights =
      tomographicViewGramQuadraticEnergy rows weights := by
  simp [tomographicViewGramQuadraticEnergyOn,
    tomographicViewGramQuadraticEnergy]

theorem tomographicViewGramQuadraticEnergyOn_eq_selected_gram_form
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (weights : View → ℝ) :
    tomographicViewGramQuadraticEnergyOn views rows weights =
      ∑ left ∈ views, ∑ right ∈ views,
        weights left * tomographicViewGramMatrix rows left right * weights right := by
  classical
  unfold tomographicViewGramQuadraticEnergyOn tomographicViewGramMatrix
  calc
    ∑ coordinate, (∑ view ∈ views, weights view * rows view coordinate) ^ 2 =
        ∑ coordinate, ∑ left ∈ views, ∑ right ∈ views,
          (weights left * rows left coordinate) *
            (weights right * rows right coordinate) := by
      apply Finset.sum_congr rfl
      intro coordinate _
      rw [pow_two, Finset.sum_mul_sum]
    _ = ∑ left ∈ views, ∑ right ∈ views, ∑ coordinate,
          (weights left * rows left coordinate) *
            (weights right * rows right coordinate) := by
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro left leftMem
      rw [Finset.sum_comm]
    _ = ∑ left ∈ views, ∑ right ∈ views,
          weights left * (∑ coordinate, rows left coordinate * rows right coordinate) *
            weights right := by
      apply Finset.sum_congr rfl
      intro left leftMem
      apply Finset.sum_congr rfl
      intro right rightMem
      rw [Finset.mul_sum, Finset.sum_mul]
      apply Finset.sum_congr rfl
      intro coordinate _
      ring

theorem tomographicViewGramQuadraticEnergyOn_zero_iff_weighted_row_zero
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (weights : View → ℝ) :
    tomographicViewGramQuadraticEnergyOn views rows weights = 0 ↔
      ∀ coordinate, ∑ view ∈ views, weights view * rows view coordinate = 0 := by
  constructor
  · intro energyZero coordinate
    have everySquareZero :
        (fun coordinate =>
          (∑ view ∈ views, weights view * rows view coordinate) ^ 2) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
        sq_nonneg (∑ view ∈ views, weights view * rows view coordinate))).mp
        (by simpa [tomographicViewGramQuadraticEnergyOn] using energyZero)
    exact sq_eq_zero_iff.mp (congrFun everySquareZero coordinate)
  · intro rowZero
    unfold tomographicViewGramQuadraticEnergyOn
    change (∑ coordinate, (∑ view ∈ views, weights view * rows view coordinate) ^ 2) = 0
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
      sq_nonneg (∑ view ∈ views, weights view * rows view coordinate))).mpr
    funext coordinate
    simp [rowZero coordinate]

end GramPair

end OCKIndividuationMSpaceComposition
