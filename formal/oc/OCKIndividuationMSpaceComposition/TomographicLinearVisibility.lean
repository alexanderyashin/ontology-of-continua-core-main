import OCKIndividuationMSpaceComposition.TomographicTaskReconstruction
import OCKIndividuationMSpaceComposition.RealValuedSparseRecovery
import OCKIndividuationMSpaceComposition.FramePressureMSpaceAdapter
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Joint invisible directions and task-relative tomography

Finite-dimensional matrices are instances of the linear maps below. A row is a
declared measurement functional, not an inferred causal edge. No dimension or
rank is assigned merely because another row is appended.
-/

section LinearVisibility

variable {State View Target : Type*}
  [AddCommGroup State] [Module ℝ State]
  [AddCommGroup Target] [Module ℝ Target]

/-- Intersection of the kernels of the acquired linear measurement rows. -/
def TomographicInvisible (row : View → State →ₗ[ℝ] ℝ) (d : State) : Prop :=
  ∀ view, row view d = 0

/-- The difference of two reconstructions is invisible exactly when every
acquired projection agrees. -/
theorem tomographic_equal_projections_iff_invisible_difference
    (row : View → State →ₗ[ℝ] ℝ) (x z : State) :
    (∀ view, row view x = row view z) ↔ TomographicInvisible row (x - z) := by
  simp only [TomographicInvisible, map_sub, sub_eq_zero]

/-- Reconstruction of a linear task needs invisibility only in the task's
kernel, not a globally injective scanner. -/
theorem tomographic_linear_task_iff_kernel_inclusion
    (row : View → State →ₗ[ℝ] ℝ) (target : State →ₗ[ℝ] Target) :
    TomographicTaskIdentifiable (fun view => row view) target ↔
      ∀ d, TomographicInvisible row d → target d = 0 := by
  constructor
  · intro sufficient d invisible
    have same : MultiTaskSignature (fun _ : View => ℝ) (fun v => row v) d =
        MultiTaskSignature (fun _ : View => ℝ) (fun v => row v) 0 := by
      funext v
      simpa [MultiTaskSignature] using invisible v
    simpa using sufficient d 0 same
  · intro kernel x z same
    apply sub_eq_zero.mp
    rw [← map_sub]
    apply kernel
    apply (tomographic_equal_projections_iff_invisible_difference row x z).mp
    intro v
    exact congrFun same v

/-- Adding an invisible component changes no acquired measurement. -/
theorem tomographic_invisible_translation
    (row : View → State →ₗ[ℝ] ℝ) (d : State)
    (invisible : TomographicInvisible row d) (x : State) :
    ∀ view, row view (x + d) = row view x := by
  intro view
  simp [map_add, invisible view]

/-- A fresh projection is useful on a witnessed ambiguity iff it detects that
specific direction. Redundant projections do not split the ambiguity. -/
theorem tomographic_new_row_splits_iff
    (fresh : State →ₗ[ℝ] ℝ) (x d : State) :
    fresh (x + d) ≠ fresh x ↔ fresh d ≠ 0 := by
  simp [map_add]

/-- Repeating or recombining old scalar measurements cannot observe an
invisible direction; this covers finite linear combinations without treating
derived rows as independent measurements. -/
theorem tomographic_derived_projection_keeps_collision
    (row : View → State →ₗ[ℝ] ℝ)
    (combine : (View → ℝ) → ℝ) (d x : State)
    (invisible : TomographicInvisible row d) :
    combine (fun view => row view (x + d)) =
      combine (fun view => row view x) := by
  apply congrArg combine
  exact funext (tomographic_invisible_translation row d invisible x)

end LinearVisibility

section ExistingFrameBridge

-- ObservationExperiment is the corpus's small-universeSet registered frame.
variable {State View Target : Type}
  [AddCommGroup State] [Module ℝ State]
  [AddCommGroup Target] [Module ℝ Target]

def tomographicObservationExperiment
    (row : View → State →ₗ[ℝ] ℝ) (target : State →ₗ[ℝ] Target) :
    ObservationExperiment where
  World := State
  Observation := View → ℝ
  Outcome := Target
  observe := fun x view => row view x
  outcome := target

/-- A task-visible kernel direction becomes an actual existing OC collision.
Irreducible pressure STILL requires active demand and exhaustion of a declared
same-carrier repair class via ObservationPressureQualification. -/
def tomographicKernelOutcomeCollision
    (row : View → State →ₗ[ℝ] ℝ) (target : State →ₗ[ℝ] Target)
    (d : State) (invisible : TomographicInvisible row d)
    (taskVisible : target d ≠ 0) :
    OutcomeCollision (tomographicObservationExperiment row target) where
  left := d
  right := (0 : State)
  sameObservation := by
    funext view
    simpa [tomographicObservationExperiment] using invisible view
  differentOutcome := by
    simpa [tomographicObservationExperiment] using taskVisible

/-- A row extension becomes an existing projective resolving frame ONLY when
the augmented observations determine the complete declared task. Splitting one
example collision alone is insufficient. -/
def tomographicProjectiveResolution
    (row : View → State →ₗ[ℝ] ℝ) (target : State →ₗ[ℝ] Target)
    (fresh : State →ₗ[ℝ] ℝ)
    (remainingInvisibleHarmless : ∀ d,
      TomographicInvisible row d → fresh d = 0 → target d = 0) :
    ProjectiveResolvingFrameExtension
      (tomographicObservationExperiment row target) ((View → ℝ) × ℝ) where
  fine := fun x => ((fun view => row view x), fresh x)
  refines := by
    intro x z same
    exact congrArg Prod.fst same
  sufficient := by
    intro x z same
    change State at x z
    have old := congrArg Prod.fst same
    have new := congrArg Prod.snd same
    have invisible : TomographicInvisible row (x - z : State) := by
      intro view
      rw [map_sub, sub_eq_zero]
      exact congrFun old view
    have freshZero : fresh (x - z : State) = (0 : ℝ) := by
      rw [map_sub, sub_eq_zero]
      exact new
    change target x = target z
    apply sub_eq_zero.mp
    rw [← map_sub]
    exact remainingInvisibleHarmless (x - z : State) invisible freshZero
  project := Prod.fst
  project_encode := fun _ => rfl

end ExistingFrameBridge

end OCKIndividuationMSpaceComposition
