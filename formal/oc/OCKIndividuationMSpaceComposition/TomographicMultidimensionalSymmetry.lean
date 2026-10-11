import OCKIndividuationMSpaceComposition.TomographicMultidimensionalFusion
import OCKIndividuationMSpaceComposition.SymmetryFoundationsCore
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Symmetry boundaries for the multidimensional observation stack

The modality × view × ray index is part of the observation, not decoration.
This module makes the corresponding OC boundary explicit: if a registered
stack is invariant under a fixed-point-free involution, no decoder can recover
a task that separates the two axis endpoints.  Conversely, any decoder for
such a task must contain at least one registered observation that breaks the
symmetry.  These are identifiability conditions, not empirical claims about
an unexamined dataset.
-/

section MultidimensionalSymmetry

variable {State Modality View Ray Reading Answer : Type*}

def tomographicMultidimensionalSignature
    (project : Modality → View → Ray → State → Reading) :
    State → Modality → View → Ray → Reading :=
  fun state modality view ray => project modality view ray state

def TomographicMultidimensionalProjectionInvariant
    (symmetry : FixedPointFreeInvolution State)
    (project : Modality → View → Ray → State → Reading) : Prop :=
  ∀ modality view ray state,
    project modality view ray (symmetry.action state) =
      project modality view ray state

theorem tomographic_multidimensional_invariant_projection_axis_collision
    (symmetry : FixedPointFreeInvolution State)
    (project : Modality → View → Ray → State → Reading)
    (invariant : TomographicMultidimensionalProjectionInvariant symmetry project)
    (state : State) :
    tomographicMultidimensionalSignature project (symmetry.action state) =
      tomographicMultidimensionalSignature project state := by
  funext modality view ray
  exact invariant modality view ray state

theorem tomographic_multidimensional_symmetry_blocks_noninvariant_task
    (symmetry : FixedPointFreeInvolution State)
    (project : Modality → View → Ray → State → Reading)
    (target : State → Answer)
    (invariant : TomographicMultidimensionalProjectionInvariant symmetry project)
    (state : State)
    (distinguishes : target state ≠ target (symmetry.action state)) :
    ¬ ∃ decode : (Modality → View → Ray → Reading) → Answer,
      ∀ world, decode (tomographicMultidimensionalSignature project world) =
        target world := by
  rintro ⟨decode, correct⟩
  apply distinguishes
  rw [← correct state, ← correct (symmetry.action state)]
  exact congrArg decode
    (tomographic_multidimensional_invariant_projection_axis_collision
      symmetry project invariant state).symm

theorem tomographic_multidimensional_decoder_requires_symmetry_break
    (symmetry : FixedPointFreeInvolution State)
    (project : Modality → View → Ray → State → Reading)
    (target : State → Answer)
    (state : State)
    (distinguishes : target state ≠ target (symmetry.action state))
    (decodes : ∃ decode : (Modality → View → Ray → Reading) → Answer,
      ∀ world, decode (tomographicMultidimensionalSignature project world) =
        target world) :
    ∃ modality view ray,
      project modality view ray (symmetry.action state) ≠
        project modality view ray state := by
  by_contra no_break
  push_neg at no_break
  rcases decodes with ⟨decode, correct⟩
  apply distinguishes
  rw [← correct state, ← correct (symmetry.action state)]
  congr 1
  funext modality view ray
  simpa [tomographicMultidimensionalSignature] using
    (no_break modality view ray).symm

end MultidimensionalSymmetry

end OCKIndividuationMSpaceComposition
