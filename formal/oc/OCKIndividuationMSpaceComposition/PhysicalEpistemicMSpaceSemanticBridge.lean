import OCKIndividuationMSpaceComposition.PhysicalEpistemicMSpace
import OCKIndividuationMSpaceComposition.OC14SemanticKernel

namespace OCKIndividuationMSpaceComposition

/-!
# Physical/epistemic optic bridge

The T5 witness is stated against the canonical continuation-space semantics,
not against two untyped labels.  `OC14SemanticKernel` is intentionally
downstream of `PhysicalEpistemicMSpace`, so this bridge is kept downstream to
avoid an import cycle while retaining the original theorem name.
-/

private def t5CoarseOptic : TaskConditionedOptic (Fin 2) where
  Observation := Bool
  Vocabulary := Bool
  Context := Unit
  Operation := Unit
  Evidence := Unit
  observe := fun _ => false
  represent := id
  context := fun _ => ()
  horizon := 0
  admissibleOperation := fun _ => True
  provenance := ()

private def t5FineOptic : TaskConditionedOptic (Fin 2) where
  Observation := Bool
  Vocabulary := Bool
  Context := Unit
  Operation := Unit
  Evidence := Unit
  observe := fun state => decide (state = 1)
  represent := id
  context := fun _ => ()
  horizon := 0
  admissibleOperation := fun _ => True
  provenance := ()

private def t5ModelWorld (model : Fin 2) : Fin 2 := model

private def t5PriorAdmits (_model : Fin 2) : Prop := True

private def t5OpticRefinement :
    OpticRefinement t5CoarseOptic t5FineOptic where
  coarsen := fun _ => false
  commutes := by
    intro world
    rfl

/-- Refining the optic can split canonical epistemic continuation classes
while the physical continuation set is unchanged.  The witness is finite,
constructive and conditional only on the explicitly exhibited optic/model
semantics; it is not a generic monotonicity law or a physical causal claim. -/
theorem optic_refinement_splits_epistemic_classes_without_physical_change :
    ∃ (physical : Set (Fin 2))
      (coarse fine : TaskConditionedOptic.{0, 0, 0, 0, 0, 0} (Fin 2))
      (refinement : OpticRefinement coarse fine)
      (coarseSnapshot fineSnapshot : ContinuationSnapshot (Fin 2)),
      coarseSnapshot.physical = physical ∧
        fineSnapshot.physical = physical ∧
        coarseSnapshot.epistemic =
          EpistemicContinuationSet coarse t5ModelWorld t5PriorAdmits 0 ∧
        fineSnapshot.epistemic =
          EpistemicContinuationSet fine t5ModelWorld t5PriorAdmits 0 ∧
        (∀ state,
          coarse.observe state = refinement.coarsen (fine.observe state)) ∧
        EpistemicContinuationSet coarse t5ModelWorld t5PriorAdmits 0 =
          Set.univ ∧
        fine.observe 0 ≠ fine.observe 1 ∧
        (∃ state,
          state ∈ EpistemicContinuationSet fine t5ModelWorld t5PriorAdmits 0) ∧
        (∃ state,
          state ∈ EpistemicContinuationSet fine t5ModelWorld t5PriorAdmits 1) ∧
        Disjoint
          (EpistemicContinuationSet fine t5ModelWorld t5PriorAdmits 0)
          (EpistemicContinuationSet fine t5ModelWorld t5PriorAdmits 1) := by
  let physical : Set (Fin 2) := Set.univ
  let coarseSnapshot : ContinuationSnapshot (Fin 2) :=
    { physical := physical
      epistemic :=
        EpistemicContinuationSet t5CoarseOptic t5ModelWorld
          t5PriorAdmits 0 }
  let fineSnapshot : ContinuationSnapshot (Fin 2) :=
    { physical := physical
      epistemic :=
        EpistemicContinuationSet t5FineOptic t5ModelWorld
          t5PriorAdmits 0 }
  refine ⟨physical, t5CoarseOptic, t5FineOptic, t5OpticRefinement,
    coarseSnapshot, fineSnapshot, rfl, rfl, rfl, rfl, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · exact t5OpticRefinement.commutes
  · ext state
    simp [EpistemicContinuationSet, OpticPosteriorAdmits,
      t5CoarseOptic, t5ModelWorld, t5PriorAdmits]
  · intro equal
    simp [t5FineOptic] at equal
  · refine ⟨0, ?_⟩
    refine ⟨0, ?_, rfl⟩
    simp [OpticPosteriorAdmits, t5FineOptic, t5ModelWorld,
      t5PriorAdmits]
  · refine ⟨1, ?_⟩
    refine ⟨1, ?_, rfl⟩
    simp [OpticPosteriorAdmits, t5FineOptic, t5ModelWorld,
      t5PriorAdmits]
  · rw [Set.disjoint_left]
    intro state inZero inOne
    simp [EpistemicContinuationSet, OpticPosteriorAdmits,
      t5FineOptic, t5ModelWorld, t5PriorAdmits] at inZero inOne
    exact inZero inOne

end OCKIndividuationMSpaceComposition
