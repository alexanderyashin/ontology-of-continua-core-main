import OCKIndividuationMSpaceComposition.TomographicLinearVisibility
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Positivity
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite algebraic tomography: row-action reconstruction

Original Lean formulation of the classical ART/Kaczmarz row projection.
See Kak and Slaney, Principles of Computerized Tomographic Imaging, chapter 7.
No copied implementation. Exact-real arithmetic; floating point needs its own
error envelope. Theorems below concern one step / finite sweeps, NOT convergence
of an arbitrary schedule, a best runtime, or real-world model validity.
-/


variable {Coordinate : Type*} [Fintype Coordinate]

def tomographicDot (a x : Coordinate → ℝ) : ℝ := ∑ i, a i * x i
def tomographicEnergy (x : Coordinate → ℝ) : ℝ := ∑ i, (x i) ^ 2

/-- A matrix row as the typed linear functional consumed by the visibility
module. Coordinate labels may themselves be products or dependent tuples. -/
def tomographicRowMap (a : Coordinate → ℝ) : (Coordinate → ℝ) →ₗ[ℝ] ℝ where
  toFun := tomographicDot a
  map_add' := by
    intro x z
    simp [tomographicDot, mul_add, Finset.sum_add_distrib]
  map_smul' := by
    intro c x
    change (∑ i, a i * (c * x i)) = c * ∑ i, a i * x i
    rw [Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro i _
    ring

theorem tomographicEnergy_nonnegative (x : Coordinate → ℝ) :
    0 ≤ tomographicEnergy x := by
  exact Finset.sum_nonneg (fun i _ => sq_nonneg (x i))

theorem tomographicDot_sub (a x z : Coordinate → ℝ) :
    tomographicDot a (fun i => x i - z i) =
      tomographicDot a x - tomographicDot a z := by
  simp [tomographicDot, mul_sub, Finset.sum_sub_distrib]

theorem tomographicDot_shift (a x direction : Coordinate → ℝ) (t : ℝ) :
    tomographicDot a (fun i => x i + t * direction i) =
      tomographicDot a x + t * tomographicDot a direction := by
  unfold tomographicDot
  rw [Finset.mul_sum, ← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro i _
  ring

theorem tomographicDot_self (a : Coordinate → ℝ) :
    tomographicDot a a = tomographicEnergy a := by
  unfold tomographicDot tomographicEnergy
  apply Finset.sum_congr rfl
  intro i _
  ring

theorem tomographicEnergy_shift (x a : Coordinate → ℝ) (t : ℝ) :
    tomographicEnergy (fun i => x i + t * a i) =
      tomographicEnergy x + 2 * t * tomographicDot a x +
        t ^ 2 * tomographicEnergy a := by
  unfold tomographicEnergy tomographicDot
  simp only [Finset.mul_sum, ← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro i _
  ring

/-- One row projection. The total Lean function exists at zero energy, but
no correcting-step theorem is licensed there. Require positive row energy. -/
noncomputable def tomographicRowStep (a : Coordinate → ℝ) (reading : ℝ)
    (x : Coordinate → ℝ) : Coordinate → ℝ :=
  fun i => x i + ((reading - tomographicDot a x) / tomographicEnergy a) * a i

theorem tomographicRowStep_satisfies_row
    (a x : Coordinate → ℝ) (reading : ℝ)
    (positiveRow : 0 < tomographicEnergy a) :
    tomographicDot a (tomographicRowStep a reading x) = reading := by
  unfold tomographicRowStep
  rw [tomographicDot_shift, tomographicDot_self]
  field_simp [ne_of_gt positiveRow] <;> ring

/-- Pythagorean error decrease for a consistent noiseless equation. -/
theorem tomographicRowStep_energy_identity
    (a x truth : Coordinate → ℝ) (reading : ℝ)
    (positiveRow : 0 < tomographicEnergy a)
    (truthRow : tomographicDot a truth = reading) :
    tomographicEnergy (fun i => tomographicRowStep a reading x i - truth i) =
      tomographicEnergy (fun i => x i - truth i) -
        (reading - tomographicDot a x) ^ 2 / tomographicEnergy a := by
  have shifted : (fun i => tomographicRowStep a reading x i - truth i) =
      (fun i => (x i - truth i) +
        ((reading - tomographicDot a x) / tomographicEnergy a) * a i) := by
    funext i
    unfold tomographicRowStep
    ring
  rw [shifted, tomographicEnergy_shift, tomographicDot_sub, truthRow]
  field_simp [ne_of_gt positiveRow] <;> ring

theorem tomographicRowStep_noiseless_nonincrease
    (a x truth : Coordinate → ℝ) (reading : ℝ)
    (positiveRow : 0 < tomographicEnergy a)
    (truthRow : tomographicDot a truth = reading) :
    tomographicEnergy (fun i => tomographicRowStep a reading x i - truth i) ≤
      tomographicEnergy (fun i => x i - truth i) := by
  rw [tomographicRowStep_energy_identity a x truth reading positiveRow truthRow]
  exact sub_le_self _ (div_nonneg (sq_nonneg _) (le_of_lt positiveRow))

/-- Noise may erase or reverse progress. Exact identity separates the true
residual decrease from injected squared measurement error. -/
theorem tomographicRowStep_noisy_energy_identity
    (a x truth : Coordinate → ℝ) (reading error : ℝ)
    (positiveRow : 0 < tomographicEnergy a)
    (truthRow : tomographicDot a truth = reading) :
    tomographicEnergy
        (fun i => tomographicRowStep a (reading + error) x i - truth i) =
      tomographicEnergy (fun i => x i - truth i) -
        (reading - tomographicDot a x) ^ 2 / tomographicEnergy a +
        error ^ 2 / tomographicEnergy a := by
  have shifted :
      (fun i => tomographicRowStep a (reading + error) x i - truth i) =
      (fun i => (x i - truth i) +
        ((reading + error - tomographicDot a x) / tomographicEnergy a) * a i) := by
    funext i
    unfold tomographicRowStep
    ring
  rw [shifted, tomographicEnergy_shift, tomographicDot_sub, truthRow]
  field_simp [ne_of_gt positiveRow] <;> ring

theorem tomographicRowStep_noisy_progress
    (a x truth : Coordinate → ℝ) (reading error : ℝ)
    (positiveRow : 0 < tomographicEnergy a)
    (truthRow : tomographicDot a truth = reading)
    (signalExceedsNoise : error ^ 2 < (reading - tomographicDot a x) ^ 2) :
    tomographicEnergy
        (fun i => tomographicRowStep a (reading + error) x i - truth i) <
      tomographicEnergy (fun i => x i - truth i) := by
  rw [tomographicRowStep_noisy_energy_identity a x truth reading error
    positiveRow truthRow]
  have gap := div_lt_div_of_pos_right signalExceedsNoise positiveRow
  linarith

/-- For consistent noiseless measurements, maximal squared normalized residual
is exactly maximal one-step reduction of reconstruction energy. This does not
assert cheapest acquisition, globally optimal scheduling, or noisy optimality. -/
theorem tomographicRowStep_gain_order
    (selected other x truth : Coordinate → ℝ) (selectedData otherData : ℝ)
    (selectedPositive : 0 < tomographicEnergy selected)
    (otherPositive : 0 < tomographicEnergy other)
    (selectedTrue : tomographicDot selected truth = selectedData)
    (otherTrue : tomographicDot other truth = otherData)
    (gainOrder : (otherData - tomographicDot other x) ^ 2 /
        tomographicEnergy other ≤
      (selectedData - tomographicDot selected x) ^ 2 /
        tomographicEnergy selected) :
    tomographicEnergy
        (fun i => tomographicRowStep selected selectedData x i - truth i) ≤
      tomographicEnergy
        (fun i => tomographicRowStep other otherData x i - truth i) := by
  rw [tomographicRowStep_energy_identity selected x truth selectedData
    selectedPositive selectedTrue,
    tomographicRowStep_energy_identity other x truth otherData
    otherPositive otherTrue]
  linarith

/-- A separately justified informative-row gain gives contraction. The lower
gain premise is not manufactured from the mere existence of a next row. -/
theorem tomographicRowStep_contraction_from_gain
    (a x truth : Coordinate → ℝ) (reading fraction : ℝ)
    (positiveRow : 0 < tomographicEnergy a)
    (truthRow : tomographicDot a truth = reading)
    (gain : fraction * tomographicEnergy (fun i => x i - truth i) ≤
      (reading - tomographicDot a x) ^ 2 / tomographicEnergy a) :
    tomographicEnergy (fun i => tomographicRowStep a reading x i - truth i) ≤
      (1 - fraction) * tomographicEnergy (fun i => x i - truth i) := by
  rw [tomographicRowStep_energy_identity a x truth reading positiveRow truthRow]
  nlinarith

/-- The total formula at a zero row is a no-op, not a successful measurement
correction; callers must inspect the positive-energy premise. -/
theorem tomographicRowStep_zero_row (x : Coordinate → ℝ) (reading : ℝ) :
    tomographicRowStep (fun _ => 0) reading x = x := by
  funext i
  simp [tomographicRowStep]

/-- A row step cannot change a component orthogonal to that row. Thus an
algorithm can fit every acquired row while retaining unobserved initialization. -/
theorem tomographicRowStep_preserves_invisible_component
    (a x direction : Coordinate → ℝ) (reading : ℝ)
    (invisible : tomographicDot direction a = 0) :
    tomographicDot direction (tomographicRowStep a reading x) =
      tomographicDot direction x := by
  unfold tomographicRowStep
  rw [tomographicDot_shift, invisible]
  ring

noncomputable def tomographicSweep : List ((Coordinate → ℝ) × ℝ) →
    (Coordinate → ℝ) → (Coordinate → ℝ)
  | [], x => x
  | (row, reading) :: rest, x =>
      tomographicSweep rest (tomographicRowStep row reading x)

/-- Every finite sweep preserves jointly invisible components. More iterations
of the same measurements do not eliminate the common nullspace. -/
theorem tomographicSweep_preserves_invisible_component
    (rows : List ((Coordinate → ℝ) × ℝ)) (direction x : Coordinate → ℝ)
    (invisible : ∀ entry ∈ rows, tomographicDot direction entry.1 = 0) :
    tomographicDot direction (tomographicSweep rows x) =
      tomographicDot direction x := by
  induction rows generalizing x with
  | nil => rfl
  | cons entry rest ih =>
    obtain ⟨a, reading⟩ := entry
    change tomographicDot direction
      (tomographicSweep rest (tomographicRowStep a reading x)) = _
    rw [ih (tomographicRowStep a reading x)
      (fun e he => invisible e (List.mem_cons_of_mem _ he))]
    exact tomographicRowStep_preserves_invisible_component a x direction reading
      (invisible (a, reading) (by simp))

end OCKIndividuationMSpaceComposition