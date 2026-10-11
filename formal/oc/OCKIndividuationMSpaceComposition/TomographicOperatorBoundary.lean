import OCKIndividuationMSpaceComposition.TomographicCapturedField
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

universe uWorld uView uReading uAnswer

/-!
# Typed observation and reconstruction operators

This module supplies the smallest operator boundary needed by the imaging
transfer.  An observation operator produces a dependent full-view signature;
a reconstruction operator consumes that signature.  Exact state recovery and
task-only recovery are separate contracts, so a task answer is never silently
promoted to a unique reconstructed world.
-/

section OperatorBoundary

variable {World : Type uWorld} {View : Type uView}
  {Reading : View → Type uReading} {Answer : Type uAnswer}

/-- A typed family of observations indexed by view. -/
abbrev TomographicObservationOperator := ∀ view, World → Reading view

/-- The complete dependent signature produced by an observation operator. -/
def tomographicObservationSignature
    (observe : TomographicObservationOperator (World := World)
      (View := View) (Reading := Reading)) (world : World) :
    ∀ view, Reading view :=
  fun view => observe view world

/-- A reconstruction operator consumes one reading at every view. -/
abbrev TomographicReconstructionOperator :=
  (∀ view, Reading view) → World

/-- Exact state reconstruction from the full registered signature. -/
def TomographicExactReconstruction
    (observe : TomographicObservationOperator (World := World)
      (View := View) (Reading := Reading))
    (reconstruct : TomographicReconstructionOperator (World := World)
      (View := View) (Reading := Reading)) : Prop :=
  ∀ world,
    reconstruct (tomographicObservationSignature observe world) = world

/-- Task-only reconstruction does not require the hidden state to be unique. -/
def TomographicExactTaskReconstruction
    (observe : TomographicObservationOperator (World := World)
      (View := View) (Reading := Reading))
    (decode : (∀ view, Reading view) → Answer)
    (target : World → Answer) : Prop :=
  ∀ world,
    decode (tomographicObservationSignature observe world) = target world

theorem tomographicExactReconstruction_implies_observation_injective
    (observe : TomographicObservationOperator (World := World)
      (View := View) (Reading := Reading))
    (reconstruct : TomographicReconstructionOperator (World := World)
      (View := View) (Reading := Reading))
    (exact : TomographicExactReconstruction observe reconstruct) :
    ∀ left right,
      tomographicObservationSignature observe left =
        tomographicObservationSignature observe right →
      left = right := by
  intro left right equal
  calc
    left = reconstruct (tomographicObservationSignature observe left) :=
      (exact left).symm
    _ = reconstruct (tomographicObservationSignature observe right) := by
      rw [equal]
    _ = right := exact right

theorem tomographicExactTaskReconstruction_implies_claimSupport
    (observe : TomographicObservationOperator (World := World)
      (View := View) (Reading := Reading))
    (decode : (∀ view, Reading view) → Answer)
    (target : World → Answer)
    (exact : TomographicExactTaskReconstruction observe decode target) :
    ∀ left right,
      tomographicObservationSignature observe left =
        tomographicObservationSignature observe right →
      target left = target right := by
  intro left right equal
  rw [← exact left, ← exact right, equal]

theorem tomographicExactReconstruction_implies_exactTaskReconstruction
    (observe : TomographicObservationOperator (World := World)
      (View := View) (Reading := Reading))
    (reconstruct : TomographicReconstructionOperator (World := World)
      (View := View) (Reading := Reading))
    (target : World → Answer)
    (decode : World → Answer)
    (exact : TomographicExactReconstruction observe reconstruct)
    (target_of_reconstruction : ∀ world,
      decode (reconstruct (tomographicObservationSignature observe world)) =
        target (reconstruct (tomographicObservationSignature observe world))) :
    TomographicExactTaskReconstruction observe
      (fun readings => decode (reconstruct readings)) target := by
  intro world
  change decode (reconstruct (tomographicObservationSignature observe world)) = target world
  rw [target_of_reconstruction world, exact world]

end OperatorBoundary

end OCKIndividuationMSpaceComposition
