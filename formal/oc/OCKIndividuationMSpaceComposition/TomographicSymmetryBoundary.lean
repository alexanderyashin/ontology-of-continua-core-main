import OCKIndividuationMSpaceComposition.TomographicTaskReconstruction
import OCKIndividuationMSpaceComposition.SymmetryFoundationsCore
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Symmetry boundaries for tomographic reconstruction

An optical symmetry is useful only when its action is declared relative to the
observations.  If every acquired projection is invariant under an involution,
the two endpoints of each generated OC axis are observationally identical.
This module records both sides of that boundary: a non-invariant task is
provably unreconstructible from those views, while an invariant task descends
to the existing `AxisQuotient`.  Neither result infers a symmetry from
similar-looking data.
-/

section SymmetryBoundary

variable {State View Answer : Type*} {Reading : View → Type*}

def TomographicProjectionInvariant
    (symmetry : FixedPointFreeInvolution State)
    (project : ∀ view, State → Reading view) : Prop :=
  ∀ view state, project view (symmetry.action state) = project view state

theorem tomographic_invariant_projection_axis_collision
    (symmetry : FixedPointFreeInvolution State)
    (project : ∀ view, State → Reading view)
    (invariant : TomographicProjectionInvariant symmetry project)
    (state : State) :
    MultiTaskSignature Reading project (symmetry.action state) =
      MultiTaskSignature Reading project state := by
  funext view
  exact invariant view state

theorem tomographic_symmetry_invariant_views_block_noninvariant_task
    (symmetry : FixedPointFreeInvolution State)
    (project : ∀ view, State → Reading view)
    (target : State → Answer)
    (invariant : TomographicProjectionInvariant symmetry project)
    (state : State)
    (distinguishes : target state ≠ target (symmetry.action state)) :
    ¬ ∃ decode : (∀ view, Reading view) → Answer,
      ∀ world, decode (MultiTaskSignature Reading project world) = target world := by
  apply tomographic_task_collision_blocks_postprocessing project target state
    (symmetry.action state)
  · intro view
    exact (invariant view state).symm
  · exact distinguishes

def TomographicAxisInvariantMap
    (symmetry : FixedPointFreeInvolution State)
    (target : State → Answer) : Prop :=
  ∀ state, target (symmetry.action state) = target state

theorem tomographic_axis_invariant_target_factors
    (symmetry : FixedPointFreeInvolution State)
    (target : State → Answer)
    (invariant : TomographicAxisInvariantMap symmetry target) :
    ∃ decode : AxisQuotient symmetry → Answer,
      ∀ state, decode (axisClass symmetry state) = target state := by
  let decode : AxisQuotient symmetry → Answer :=
    Quotient.lift target (by
      intro left right relation
      rcases relation with rfl | relation
      · rfl
      · subst right
        exact (invariant left).symm)
  refine ⟨decode, ?_⟩
  intro state
  rfl

end SymmetryBoundary

end OCKIndividuationMSpaceComposition