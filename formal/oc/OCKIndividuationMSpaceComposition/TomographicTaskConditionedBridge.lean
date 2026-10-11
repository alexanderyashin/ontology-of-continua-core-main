import OCKIndividuationMSpaceComposition.TaskConditionedOptics
import OCKIndividuationMSpaceComposition.TomographicLinearVisibility
import OCKIndividuationMSpaceComposition.CanonicalTaskQuotient
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Tomography as a TaskConditionedOptic adapter

The linear tomography layer and the task-conditioned optic layer are two
different interfaces in the existing corpus.  This module is deliberately a
thin constructor between them: rows provide the observation field, while
representation, context, admissible operations, horizon and provenance stay
explicit caller-supplied fields.  No row family is silently promoted to a
canonical OC axis or to a causal model.
-/

section Adapter

variable {State View Vocabulary Context Operation Evidence Target : Type*}
  [AddCommGroup State] [Module ℝ State]

/-! A registered task optic whose observation is the complete family of rows. -/
def tomographicTaskConditionedOptic
    (row : View → State →ₗ[ℝ] ℝ)
    (represent : (View → ℝ) → Vocabulary)
    (context : State → Context)
    (horizon : Nat)
    (admissibleOperation : Operation → Prop)
    (provenance : Evidence) : TaskConditionedOptic State where
  Observation := View → ℝ
  Vocabulary := Vocabulary
  Context := Context
  Operation := Operation
  Evidence := Evidence
  observe := fun state view => row view state
  represent := represent
  context := context
  horizon := horizon
  admissibleOperation := admissibleOperation
  provenance := provenance

@[simp] theorem tomographicTaskConditionedOptic_observe
    (row : View → State →ₗ[ℝ] ℝ)
    (represent : (View → ℝ) → Vocabulary)
    (context : State → Context)
    (horizon : Nat)
    (admissibleOperation : Operation → Prop)
    (provenance : Evidence) (state : State) :
    (tomographicTaskConditionedOptic row represent context horizon
      admissibleOperation provenance).observe state =
        (fun view => row view state) := rfl

/-! The outcome experiment is the existing OC sufficiency interface. -/
def tomographicTaskObservationExperiment
    [AddCommGroup Target] [Module ℝ Target]
    (row : View → State →ₗ[ℝ] ℝ)
    (target : State →ₗ[ℝ] Target) : ObservationExperiment :=
  { World := State
    Observation := View → ℝ
    Outcome := Target
    observe := fun state view => row view state
    outcome := target }

/-! Kernel inclusion is exactly the sufficiency premise for this adapter. -/
theorem tomographicTaskConditioned_kernel_gives_observation_sufficiency
    {Target : Type*} [AddCommGroup Target] [Module ℝ Target]
    (row : View → State →ₗ[ℝ] ℝ)
    (target : State →ₗ[ℝ] Target)
    (kernel : ∀ d, TomographicInvisible row d → target d = 0) :
    ObservationSufficient (tomographicTaskObservationExperiment row target) := by
  intro left right same
  exact (tomographic_linear_task_iff_kernel_inclusion row target).mpr kernel
    left right same

/-! A failed kernel premise is an explicit task-level collision, not a bug in
the decoder. -/
theorem tomographicTaskConditioned_visible_kernel_blocks_exact_predictor
    {Target : Type*} [AddCommGroup Target] [Module ℝ Target]
    (row : View → State →ₗ[ℝ] ℝ)
    (target : State →ₗ[ℝ] Target)
    (d : State)
    (invisible : TomographicInvisible row d)
    (taskVisible : target d ≠ 0) :
    ¬ ∃ decode : (View → ℝ) → Target,
      ∀ state, decode (fun view => row view state) = target state := by
  exact tomographic_task_collision_blocks_postprocessing
    (fun view => row view) target d 0 (by
      intro view
      simpa using invisible view) (by
      simpa using taskVisible)

/-! Task sufficiency can use the existing canonical task quotient as its
representation target.  This is a factorisation result on reachable
observations; it does not claim that the quotient is a physical identity. -/
theorem tomographicTaskConditioned_identifiability_has_canonical_quotient_factor
    {Target : Type*} [Nonempty State]
    (row : View → State →ₗ[ℝ] ℝ)
    (target : State → Target)
    (identifiable : TomographicTaskIdentifiable (fun view => row view) target) :
    ∃ factor : (View → ℝ) → TaskQuotient target,
      ∀ state, factor (fun view => row view state) =
        taskQuotientObservation target state := by
  apply sufficient_observation_has_quotient_factor target
    (fun state view => row view state)
  intro left right same
  exact identifiable left right (by
    simpa [MultiTaskSignature] using same)

theorem tomographicTaskConditioned_kernel_has_canonical_quotient_factor
    {Target : Type*} [AddCommGroup Target] [Module ℝ Target]
    [Nonempty State]
    (row : View → State →ₗ[ℝ] ℝ)
    (target : State →ₗ[ℝ] Target)
    (kernel : ∀ d, TomographicInvisible row d → target d = 0) :
    ∃ factor : (View → ℝ) → TaskQuotient (fun state => target state),
      ∀ state, factor (fun view => row view state) =
        taskQuotientObservation (fun state => target state) state := by
  apply tomographicTaskConditioned_identifiability_has_canonical_quotient_factor
    row (fun state => target state)
  exact (tomographic_linear_task_iff_kernel_inclusion row target).mpr kernel

end Adapter

end OCKIndividuationMSpaceComposition
