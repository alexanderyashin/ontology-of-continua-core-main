import OCMinimalObligationSpine.UnifiedEntityProjection

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

/--
A finite state space carrying two independent observable coordinates.  The two
coordinate encoders below are concrete functions, not assumed admissibility or
incomparability propositions.
-/
abbrev BranchKernelWitnessState := Bool × Bool

/-- The first branch retains only the first coordinate. -/
def firstCoordinateBranchEncoder :
    BranchKernelWitnessState → Bool :=
  Prod.fst

/-- The second branch retains only the second coordinate. -/
def secondCoordinateBranchEncoder :
    BranchKernelWitnessState → Bool :=
  Prod.snd

/--
The first encoder identifies these states, while the second encoder separates
them.  This is the explicit collision witness against refinement from the
first coordinate kernel to the second.
-/
theorem first_coordinate_collision :
    firstCoordinateBranchEncoder (false, false) =
      firstCoordinateBranchEncoder (false, true) := by
  rfl

theorem second_coordinate_separates_first_collision :
    secondCoordinateBranchEncoder (false, false) ≠
      secondCoordinateBranchEncoder (false, true) := by
  decide

/--
Symmetrically, the second encoder identifies these states, while the first
encoder separates them.
-/
theorem second_coordinate_collision :
    secondCoordinateBranchEncoder (false, false) =
      secondCoordinateBranchEncoder (true, false) := by
  rfl

theorem first_coordinate_separates_second_collision :
    firstCoordinateBranchEncoder (false, false) ≠
      firstCoordinateBranchEncoder (true, false) := by
  decide

/--
The first-coordinate kernel does not refine the second-coordinate kernel.
The proof evaluates the alleged refinement on the concrete first-coordinate
collision above.
-/
theorem first_coordinate_kernel_not_refines_second :
    ¬ EncoderKernelRefines
        firstCoordinateBranchEncoder
        secondCoordinateBranchEncoder := by
  intro refines
  exact second_coordinate_separates_first_collision
    (refines (false, false) (false, true) first_coordinate_collision)

/--
The second-coordinate kernel does not refine the first-coordinate kernel.
-/
theorem second_coordinate_kernel_not_refines_first :
    ¬ EncoderKernelRefines
        secondCoordinateBranchEncoder
        firstCoordinateBranchEncoder := by
  intro refines
  exact first_coordinate_separates_second_collision
    (refines (false, false) (true, false) second_coordinate_collision)

/--
The two explicit finite encoder kernels are mutually incomparable.
-/
theorem coordinate_branch_encoder_kernels_are_incomparable :
    (¬ EncoderKernelRefines
        firstCoordinateBranchEncoder
        secondCoordinateBranchEncoder) ∧
      (¬ EncoderKernelRefines
        secondCoordinateBranchEncoder
        firstCoordinateBranchEncoder) := by
  exact ⟨
    first_coordinate_kernel_not_refines_second,
    second_coordinate_kernel_not_refines_first
  ⟩

/--
Consequently encoder-kernel refinement is not a total relation, already on
encoders from the four-element state space `Bool × Bool` to `Bool`.

This is a structural K-order countermodel only.  It does not identify either
coordinate with a physical K0--K12 level and does not supply a cross-domain
realization.
-/
theorem encoderKernelRefines_is_not_total_on_finite_encoders :
    ¬ (∀ left right : BranchKernelWitnessState → Bool,
        EncoderKernelRefines left right ∨
          EncoderKernelRefines right left) := by
  intro total
  rcases total
      firstCoordinateBranchEncoder
      secondCoordinateBranchEncoder with
    leftRefines | rightRefines
  · exact first_coordinate_kernel_not_refines_second leftRefines
  · exact second_coordinate_kernel_not_refines_first rightRefines

end OCMinimalObligationSpine
