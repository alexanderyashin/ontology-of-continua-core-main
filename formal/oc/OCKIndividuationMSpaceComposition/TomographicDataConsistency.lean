import OCKIndividuationMSpaceComposition.TomographicCompatibleSet
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite data-consistency residual

The squared residual over a registered finite view family is an explicit
compatibility gate.  Zero residual means that every declared projection agrees
with the observation; it does not imply that the compatible state is unique,
that the model class is correct, or that a scientific claim is accepted.
-/


section DataConsistency

variable {World View : Type*} [Fintype View] [DecidableEq View]

def tomographicDataResidualEnergy
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World) : ℝ :=
  ∑ view, (project view world - observation view) ^ 2

theorem tomographicDataResidualEnergy_nonnegative
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World) :
    0 ≤ tomographicDataResidualEnergy project observation world := by
  exact Finset.sum_nonneg (fun view _ => sq_nonneg _)

theorem tomographicDataResidualEnergy_zero_iff_pointwise
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World) :
    tomographicDataResidualEnergy project observation world = 0 ↔
      ∀ view, project view world = observation view := by
  constructor
  · intro energyZero
    have everySquareZero :
        (fun view => (project view world - observation view) ^ 2) = 0 :=
      (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
        sq_nonneg (project view world - observation view))).mp energyZero
    intro view
    have selected := congrFun everySquareZero view
    exact sub_eq_zero.mp (sq_eq_zero_iff.mp selected)
  · intro everyEqual
    have everySquareZero :
        (fun view => (project view world - observation view) ^ 2) = 0 := by
      funext view
      simp [everyEqual view]
    exact (Fintype.sum_eq_zero_iff_of_nonneg (fun view =>
      sq_nonneg (project view world - observation view))).mpr everySquareZero

theorem tomographicDataResidualEnergy_zero_iff_compatible
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World) :
    tomographicDataResidualEnergy project observation world = 0 ↔
      TomographicCompatible project observation world := by
  rw [tomographicDataResidualEnergy_zero_iff_pointwise]
  exact (tomographicCompatible_iff_pointwise project observation world).symm

theorem tomographicDataResidualEnergy_uniform_bound
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World)
    (bound : ℝ)
    (bound_nonnegative : 0 ≤ bound)
    (pointwise_bound : ∀ view,
      |project view world - observation view| ≤ bound) :
    tomographicDataResidualEnergy project observation world ≤
      Fintype.card View * bound ^ 2 := by
  unfold tomographicDataResidualEnergy
  calc
    ∑ view, (project view world - observation view) ^ 2 ≤
        ∑ view, bound ^ 2 := by
      apply Finset.sum_le_sum
      intro view _
      have pointwise := pointwise_bound view
      have squared_bound :
          |project view world - observation view| ^ 2 ≤ bound ^ 2 := by
        apply (sq_le_sq).2
        simpa [abs_of_nonneg bound_nonnegative] using pointwise
      simpa [sq_abs] using squared_bound
    _ = Fintype.card View * bound ^ 2 := by
      simp

/-! A bounded scan may expose only a selected finite batch of views.  The
    batch residual is kept separate so that later batches can be reconciled by
    exact finite additivity rather than by rescanning earlier views. -/

def tomographicDataResidualEnergyOn
    (views : Finset View)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World) : ℝ :=
  ∑ view ∈ views, (project view world - observation view) ^ 2

theorem tomographicDataResidualEnergyOn_nonnegative
    (views : Finset View)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World) :
    0 ≤ tomographicDataResidualEnergyOn views project observation world := by
  unfold tomographicDataResidualEnergyOn
  exact Finset.sum_nonneg (fun view _ => sq_nonneg _)

theorem tomographicDataResidualEnergyOn_union
    (first second : Finset View)
    (disjoint : Disjoint first second)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World) :
    tomographicDataResidualEnergyOn (first ∪ second) project observation world =
      tomographicDataResidualEnergyOn first project observation world +
      tomographicDataResidualEnergyOn second project observation world := by
  classical
  unfold tomographicDataResidualEnergyOn
  rw [Finset.sum_union disjoint]

theorem tomographicDataResidualEnergyOn_univ_eq_residualEnergy
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World) :
    tomographicDataResidualEnergyOn Finset.univ project observation world =
      tomographicDataResidualEnergy project observation world := by
  simp [tomographicDataResidualEnergyOn, tomographicDataResidualEnergy]

theorem tomographicDataResidualEnergyOn_zero_iff_pointwise
    (views : Finset View)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World) :
    tomographicDataResidualEnergyOn views project observation world = 0 ↔
      ∀ view ∈ views, project view world = observation view := by
  constructor
  · intro residualZero view viewMem
    have residualZero' :
        (∑ member ∈ views,
          (project member world - observation member) ^ 2) = 0 := by
      simpa [tomographicDataResidualEnergyOn] using residualZero
    have everySquareZero :
        ∀ view ∈ views, (project view world - observation view) ^ 2 = 0 := by
      intro selected selectedMem
      exact (Finset.sum_eq_zero_iff_of_nonneg (fun member memberMem =>
        sq_nonneg (project member world - observation member))).mp residualZero'
        selected selectedMem
    exact sub_eq_zero.mp (sq_eq_zero_iff.mp
      (everySquareZero view viewMem))
  · intro everyEqual
    unfold tomographicDataResidualEnergyOn
    apply Finset.sum_eq_zero
    intro view viewMem
    simp [everyEqual view viewMem]

theorem tomographicDataResidualEnergyOn_uniform_bound
    (views : Finset View)
    (project : View → World → ℝ)
    (observation : View → ℝ)
    (world : World)
    (bound : ℝ)
    (bound_nonnegative : 0 ≤ bound)
    (pointwise_bound : ∀ view, view ∈ views →
      |project view world - observation view| ≤ bound) :
    tomographicDataResidualEnergyOn views project observation world ≤
      views.card * bound ^ 2 := by
  unfold tomographicDataResidualEnergyOn
  calc
    ∑ view ∈ views, (project view world - observation view) ^ 2 ≤
        ∑ view ∈ views, bound ^ 2 := by
      apply Finset.sum_le_sum
      intro view viewMem
      have pointwise := pointwise_bound view viewMem
      have squared_bound :
          |project view world - observation view| ^ 2 ≤ bound ^ 2 := by
        apply (sq_le_sq).2
        simpa [abs_of_nonneg bound_nonnegative] using pointwise
      simpa [sq_abs] using squared_bound
    _ = views.card * bound ^ 2 := by
      simp

end DataConsistency

end OCKIndividuationMSpaceComposition
