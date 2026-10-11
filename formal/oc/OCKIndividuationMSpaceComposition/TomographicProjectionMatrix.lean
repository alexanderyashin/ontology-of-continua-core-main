import OCKIndividuationMSpaceComposition.TomographicRowAction
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite projection matrix and normal-energy certificates

`tomographicProjection` is the finite matrix action whose rows are the
registered views.  `tomographicNormalEnergy` is the squared residual energy of
the projection family (the discrete analogue of a normal-operator quadratic
form).  These identities certify algebraic consistency only: they do not
assert rank, conditioning, calibration, or semantic recovery.
-/


section ProjectionMatrix

variable {Coordinate View : Type*} [Fintype Coordinate] [Fintype View] [DecidableEq View]

def tomographicProjection
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) : View → ℝ :=
  fun view => tomographicDot (rows view) state

def tomographicRowL1Norm (row : Coordinate → ℝ) : ℝ :=
  ∑ coordinate, |row coordinate|

theorem tomographicRowL1Norm_nonnegative
    (row : Coordinate → ℝ) :
    0 ≤ tomographicRowL1Norm row := by
  unfold tomographicRowL1Norm
  exact Finset.sum_nonneg (fun coordinate _ => abs_nonneg _)

theorem tomographicRowL1Norm_eq_zero_iff
    (row : Coordinate → ℝ) :
    tomographicRowL1Norm row = 0 ↔
      ∀ coordinate, row coordinate = 0 := by
  constructor
  · intro normZero coordinate
    have everyAbsZero :
        (fun coordinate => |row coordinate|) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
        abs_nonneg (row coordinate))).mp (by
          simpa [tomographicRowL1Norm] using normZero)
    exact abs_eq_zero.mp (congrFun everyAbsZero coordinate)
  · intro rowZero
    unfold tomographicRowL1Norm
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun coordinate =>
      abs_nonneg (row coordinate))).mpr
    funext coordinate
    simp [rowZero coordinate]

theorem tomographicProjection_eq_rowMap
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) (view : View) :
    tomographicProjection rows state view =
      tomographicRowMap (rows view) state := rfl

theorem tomographicProjection_add
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicProjection rows (fun coordinate =>
      left coordinate + right coordinate) =
      fun view => tomographicProjection rows left view +
        tomographicProjection rows right view := by
  funext view
  simp [tomographicProjection, tomographicDot, mul_add, Finset.sum_add_distrib]

theorem tomographicProjection_smul
    (rows : View → Coordinate → ℝ)
    (scalar : ℝ) (state : Coordinate → ℝ) :
    tomographicProjection rows (fun coordinate =>
      scalar * state coordinate) =
      fun view => scalar * tomographicProjection rows state view := by
  funext view
  simp only [tomographicProjection, tomographicDot]
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro coordinate _
  ring

theorem tomographicProjection_sub
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicProjection rows (fun coordinate =>
      left coordinate - right coordinate) =
      fun view => tomographicProjection rows left view -
        tomographicProjection rows right view := by
  funext view
  simp only [tomographicProjection, tomographicDot]
  simp_rw [mul_sub]
  rw [Finset.sum_sub_distrib]

theorem tomographicProjection_abs_bound_by_rowL1_inf
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (view : View)
    (state_bound : ℝ)
    (state_bound_nonnegative : 0 ≤ state_bound)
    (state_abs_bound : ∀ coordinate, |state coordinate| ≤ state_bound) :
    |tomographicProjection rows state view| ≤
      tomographicRowL1Norm (rows view) * state_bound := by
  unfold tomographicProjection tomographicRowL1Norm tomographicDot
  calc
    |∑ coordinate, rows view coordinate * state coordinate| ≤
        ∑ coordinate, |rows view coordinate * state coordinate| :=
      Finset.abs_sum_le_sum_abs _ _
    _ = ∑ coordinate, |rows view coordinate| * |state coordinate| := by
      apply Finset.sum_congr rfl
      intro coordinate _
      rw [abs_mul]
    _ ≤ ∑ coordinate, |rows view coordinate| * state_bound := by
      apply Finset.sum_le_sum
      intro coordinate _
      exact mul_le_mul_of_nonneg_left (state_abs_bound coordinate)
        (abs_nonneg _)
    _ = (∑ coordinate, |rows view coordinate|) * state_bound := by
      rw [Finset.sum_mul]

theorem tomographicProjection_zero_of_rowL1Norm_zero
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (view : View)
    (row_zero : tomographicRowL1Norm (rows view) = 0) :
    tomographicProjection rows state view = 0 := by
  have row_values_zero : ∀ coordinate, rows view coordinate = 0 :=
    (tomographicRowL1Norm_eq_zero_iff (rows view)).mp row_zero
  unfold tomographicProjection tomographicDot
  apply Finset.sum_eq_zero
  intro coordinate _
  simp [row_values_zero coordinate]

theorem tomographicProjection_abs_sub_bound_by_rowL1_inf
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ)
    (view : View)
    (difference_bound : ℝ)
    (difference_bound_nonnegative : 0 ≤ difference_bound)
    (state_difference_abs_bound : ∀ coordinate,
      |left coordinate - right coordinate| ≤ difference_bound) :
    |tomographicProjection rows left view -
        tomographicProjection rows right view| ≤
      tomographicRowL1Norm (rows view) * difference_bound := by
  have projection_sub := congrFun
    (tomographicProjection_sub rows left right) view
  rw [← projection_sub]
  exact tomographicProjection_abs_bound_by_rowL1_inf rows
    (fun coordinate => left coordinate - right coordinate)
    view difference_bound difference_bound_nonnegative
    state_difference_abs_bound

def tomographicNormalEnergy
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) : ℝ :=
  ∑ view, (tomographicProjection rows state view) ^ 2

/-! Selected-view normal energy is the bounded counterpart used for
    incremental acquisition and checkpointed scan accounting. -/

def tomographicNormalEnergyOn
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) : ℝ :=
  ∑ view ∈ views, (tomographicProjection rows state view) ^ 2

theorem tomographicNormalEnergyOn_nonnegative
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    0 ≤ tomographicNormalEnergyOn views rows state := by
  unfold tomographicNormalEnergyOn
  exact Finset.sum_nonneg (fun view _ => sq_nonneg _)

theorem tomographicNormalEnergyOn_union
    (first second : Finset View)
    (disjoint : Disjoint first second)
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    tomographicNormalEnergyOn (first ∪ second) rows state =
      tomographicNormalEnergyOn first rows state +
        tomographicNormalEnergyOn second rows state := by
  unfold tomographicNormalEnergyOn
  rw [Finset.sum_union disjoint]

theorem tomographicNormalEnergyOn_univ_eq_normalEnergy
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    tomographicNormalEnergyOn Finset.univ rows state =
      tomographicNormalEnergy rows state := by
  simp [tomographicNormalEnergyOn, tomographicNormalEnergy]

theorem tomographicNormalEnergyOn_zero_iff_pointwise_invisible
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    tomographicNormalEnergyOn views rows state = 0 ↔
      ∀ view ∈ views, tomographicProjection rows state view = 0 := by
  constructor
  · intro energyZero view viewMem
    have energyZero' :
        (∑ member ∈ views,
          (tomographicProjection rows state member) ^ 2) = 0 := by
      simpa [tomographicNormalEnergyOn] using energyZero
    have everySquareZero :
        ∀ view ∈ views, (tomographicProjection rows state view) ^ 2 = 0 := by
      intro selected selectedMem
      exact (Finset.sum_eq_zero_iff_of_nonneg (fun member memberMem =>
        sq_nonneg (tomographicProjection rows state member))).mp energyZero'
        selected selectedMem
    exact sq_eq_zero_iff.mp (everySquareZero view viewMem)
  · intro everyInvisible
    unfold tomographicNormalEnergyOn
    apply Finset.sum_eq_zero
    intro view viewMem
    simp [everyInvisible view viewMem]

theorem tomographicNormalEnergyOn_mono
    (first second : Finset View)
    (subset : first ⊆ second)
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    tomographicNormalEnergyOn first rows state ≤
      tomographicNormalEnergyOn second rows state := by
  unfold tomographicNormalEnergyOn
  exact Finset.sum_le_sum_of_subset_of_nonneg subset
    (fun view _ _ => sq_nonneg (tomographicProjection rows state view))

theorem tomographicNormalEnergyOn_uniform_bound
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (bound : ℝ)
    (bound_nonnegative : 0 ≤ bound)
    (pointwise_bound : ∀ view, view ∈ views →
      |tomographicProjection rows state view| ≤ bound) :
    tomographicNormalEnergyOn views rows state ≤
      views.card * bound ^ 2 := by
  unfold tomographicNormalEnergyOn
  calc
    ∑ view ∈ views, (tomographicProjection rows state view) ^ 2 ≤
        ∑ view ∈ views, bound ^ 2 := by
      apply Finset.sum_le_sum
      intro view viewMem
      have pointwise := pointwise_bound view viewMem
      have squared_bound :
          |tomographicProjection rows state view| ^ 2 ≤ bound ^ 2 := by
        apply (sq_le_sq).2
        simpa [abs_of_nonneg bound_nonnegative] using pointwise
      simpa [sq_abs] using squared_bound
    _ = views.card * bound ^ 2 := by
      simp

theorem tomographicNormalEnergyOn_rowwise_bound
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (view_bound : View → ℝ)
    (view_bound_nonnegative : ∀ view, view ∈ views → 0 ≤ view_bound view)
    (pointwise_bound : ∀ view, view ∈ views →
      |tomographicProjection rows state view| ≤ view_bound view) :
    tomographicNormalEnergyOn views rows state ≤
      ∑ view ∈ views, (view_bound view) ^ 2 := by
  unfold tomographicNormalEnergyOn
  apply Finset.sum_le_sum
  intro view viewMem
  have pointwise := pointwise_bound view viewMem
  have squared_bound :
      |tomographicProjection rows state view| ^ 2 ≤
        (view_bound view) ^ 2 := by
    apply (sq_le_sq).2
    simpa [abs_of_nonneg (view_bound_nonnegative view viewMem)] using pointwise
  simpa [sq_abs] using squared_bound

theorem tomographicNormalEnergyOn_rowL1_inf_rowwise_bound
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (state_bound : ℝ)
    (state_bound_nonnegative : 0 ≤ state_bound)
    (state_abs_bound : ∀ coordinate, |state coordinate| ≤ state_bound) :
    tomographicNormalEnergyOn views rows state ≤
      ∑ view ∈ views,
        (tomographicRowL1Norm (rows view) * state_bound) ^ 2 := by
  apply tomographicNormalEnergyOn_rowwise_bound views rows state
    (fun view => tomographicRowL1Norm (rows view) * state_bound)
  · intro view viewMem
    exact mul_nonneg (tomographicRowL1Norm_nonnegative (rows view))
      state_bound_nonnegative
  · intro view viewMem
    exact tomographicProjection_abs_bound_by_rowL1_inf rows state view
      state_bound state_bound_nonnegative state_abs_bound

theorem tomographicNormalEnergyOn_difference_rowwise_bound
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ)
    (view_bound : View → ℝ)
    (view_bound_nonnegative : ∀ view, view ∈ views → 0 ≤ view_bound view)
    (pointwise_bound : ∀ view, view ∈ views →
      |tomographicProjection rows left view -
        tomographicProjection rows right view| ≤ view_bound view) :
    tomographicNormalEnergyOn views rows (fun coordinate =>
      left coordinate - right coordinate) ≤
      ∑ view ∈ views, (view_bound view) ^ 2 := by
  apply tomographicNormalEnergyOn_rowwise_bound views rows
    (fun coordinate => left coordinate - right coordinate) view_bound
    view_bound_nonnegative
  intro view viewMem
  rw [congrFun (tomographicProjection_sub rows left right) view]
  exact pointwise_bound view viewMem

theorem tomographicNormalEnergyOn_difference_rowL1_inf_rowwise_bound
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ)
    (difference_bound : ℝ)
    (difference_bound_nonnegative : 0 ≤ difference_bound)
    (state_difference_abs_bound : ∀ coordinate,
      |left coordinate - right coordinate| ≤ difference_bound) :
    tomographicNormalEnergyOn views rows (fun coordinate =>
      left coordinate - right coordinate) ≤
      ∑ view ∈ views,
        (tomographicRowL1Norm (rows view) * difference_bound) ^ 2 := by
  apply tomographicNormalEnergyOn_difference_rowwise_bound views rows left right
    (fun view => tomographicRowL1Norm (rows view) * difference_bound)
  · intro view viewMem
    exact mul_nonneg (tomographicRowL1Norm_nonnegative (rows view))
      difference_bound_nonnegative
  · intro view viewMem
    exact tomographicProjection_abs_sub_bound_by_rowL1_inf rows left right view
      difference_bound difference_bound_nonnegative state_difference_abs_bound

theorem tomographicNormalEnergyOn_difference_zero_iff_equal_selected_projections
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicNormalEnergyOn views rows (fun coordinate =>
      left coordinate - right coordinate) = 0 ↔
      ∀ view ∈ views,
        tomographicProjection rows left view =
          tomographicProjection rows right view := by
  constructor
  · intro energyZero view viewMem
    have invisible :=
      (tomographicNormalEnergyOn_zero_iff_pointwise_invisible views rows
        (fun coordinate => left coordinate - right coordinate)).mp energyZero
        view viewMem
    rw [congrFun (tomographicProjection_sub rows left right) view] at invisible
    exact sub_eq_zero.mp invisible
  · intro equal
    apply (tomographicNormalEnergyOn_zero_iff_pointwise_invisible views rows
      (fun coordinate => left coordinate - right coordinate)).mpr
    intro view viewMem
    rw [congrFun (tomographicProjection_sub rows left right) view]
    exact sub_eq_zero.mpr (equal view viewMem)

theorem tomographicNormalEnergyOn_difference_rowwise_lower_bound
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ)
    (margin : ℝ)
    (margin_nonnegative : 0 ≤ margin)
    (pointwise_lower_bound : ∀ view, view ∈ views →
      margin ≤ |tomographicProjection rows left view -
        tomographicProjection rows right view|) :
    views.card * margin ^ 2 ≤
      tomographicNormalEnergyOn views rows (fun coordinate =>
        left coordinate - right coordinate) := by
  unfold tomographicNormalEnergyOn
  calc
    views.card * margin ^ 2 = ∑ view ∈ views, margin ^ 2 := by simp
    _ ≤ ∑ view ∈ views,
        (tomographicProjection rows (fun coordinate =>
          left coordinate - right coordinate) view) ^ 2 := by
      apply Finset.sum_le_sum
      intro view viewMem
      have pointwise := pointwise_lower_bound view viewMem
      have squared_bound :
          margin ^ 2 ≤
            |tomographicProjection rows left view -
              tomographicProjection rows right view| ^ 2 := by
        apply (sq_le_sq).2
        simpa [abs_of_nonneg margin_nonnegative] using pointwise
      rw [congrFun (tomographicProjection_sub rows left right) view]
      simpa [sq_abs] using squared_bound

theorem tomographicNormalEnergyOn_rowL1_inf_bound
    (views : Finset View)
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (row_bound state_bound : ℝ)
    (row_bound_nonnegative : 0 ≤ row_bound)
    (state_bound_nonnegative : 0 ≤ state_bound)
    (row_l1_bound : ∀ view, view ∈ views →
      tomographicRowL1Norm (rows view) ≤ row_bound)
    (state_abs_bound : ∀ coordinate, |state coordinate| ≤ state_bound) :
    tomographicNormalEnergyOn views rows state ≤
      views.card * (row_bound * state_bound) ^ 2 := by
  apply tomographicNormalEnergyOn_uniform_bound views rows state
    (row_bound * state_bound)
    (mul_nonneg row_bound_nonnegative state_bound_nonnegative)
  intro view viewMem
  exact le_trans
    (tomographicProjection_abs_bound_by_rowL1_inf rows state view
      state_bound state_bound_nonnegative state_abs_bound)
    (mul_le_mul_of_nonneg_right (row_l1_bound view viewMem)
      state_bound_nonnegative)

theorem tomographicNormalEnergy_nonnegative
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    0 ≤ tomographicNormalEnergy rows state := by
  exact Finset.sum_nonneg (fun view _ => sq_nonneg _)

theorem tomographicNormalEnergy_zero_iff
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ) :
    tomographicNormalEnergy rows state = 0 ↔
      ∀ view, tomographicProjection rows state view = 0 := by
  constructor
  · intro energyZero
    have everySquareZero :
        (fun view => (tomographicProjection rows state view) ^ 2) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
        sq_nonneg (tomographicProjection rows state view))).mp energyZero
    intro view
    have selected := congrFun everySquareZero view
    exact sq_eq_zero_iff.mp selected
  · intro everyZero
    unfold tomographicNormalEnergy
    apply (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
      sq_nonneg (tomographicProjection rows state view))).mpr
    funext view
    simp [everyZero view]

theorem tomographicNormalEnergy_difference_zero_iff_equal_projections
    (rows : View → Coordinate → ℝ)
    (left right : Coordinate → ℝ) :
    tomographicNormalEnergy rows (fun coordinate =>
      left coordinate - right coordinate) = 0 ↔
      ∀ view, tomographicProjection rows left view =
        tomographicProjection rows right view := by
  constructor
  · intro energyZero view
    have invisible :=
      (tomographicNormalEnergy_zero_iff rows
        (fun coordinate => left coordinate - right coordinate)).mp energyZero view
    rw [congrFun (tomographicProjection_sub rows left right) view] at invisible
    exact sub_eq_zero.mp invisible
  · intro equal
    apply (tomographicNormalEnergy_zero_iff rows
      (fun coordinate => left coordinate - right coordinate)).mpr
    intro view
    rw [congrFun (tomographicProjection_sub rows left right) view]
    exact sub_eq_zero.mpr (equal view)

theorem tomographicNormalEnergy_zero_of_invisible
    (rows : View → Coordinate → ℝ)
    (state : Coordinate → ℝ)
    (invisible : ∀ view, tomographicProjection rows state view = 0) :
    tomographicNormalEnergy rows state = 0 :=
  (tomographicNormalEnergy_zero_iff rows state).mpr invisible

end ProjectionMatrix

end OCKIndividuationMSpaceComposition
