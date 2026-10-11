import OCKIndividuationMSpaceComposition.TaskConditionedOptics
import Mathlib.Data.Fintype.Card
import Mathlib.Tactic.NormNum

namespace OCKIndividuationMSpaceComposition

universe uWorld uTask uSignature uObservation

/-!
# Finite multi-task optic join

For a family of task signatures, the join records all task-relative
distinctions simultaneously.  It is the common refinement required for exact
multi-task prediction; it is not asserted to be minimal for any one task or
to be a universal physical ontology.
-/

def MultiTaskSignature
    {World : Type uWorld} {Task : Type uTask}
    (Signature : Task → Type uSignature)
    (signature : ∀ task, World → Signature task) :
    World → (∀ task, Signature task) :=
  fun world task => signature task world

def MultiTaskSufficient
    {World : Type uWorld} {Task : Type uTask}
    (Signature : Task → Type uSignature)
    (signature : ∀ task, World → Signature task)
    {Observation : Type uObservation}
    (observe : World → Observation) : Prop :=
  ∀ task left right,
    observe left = observe right → signature task left = signature task right

/-- The joint signature is sufficient for every task in the family. -/
theorem multiTaskSignature_is_sufficient_for_every_task
    {World : Type uWorld} {Task : Type uTask}
    (Signature : Task → Type uSignature)
    (signature : ∀ task, World → Signature task) :
    MultiTaskSufficient Signature signature
      (MultiTaskSignature Signature signature) := by
  intro task left right sameJoint
  exact congrFun sameJoint task

/-- Every observation sufficient for all tasks refines the joint signature.
This is the exact finite/common-sufficiency minimality statement. -/
theorem every_common_sufficient_observation_refines_multiTaskSignature
    {World : Type uWorld} {Task : Type uTask}
    (Signature : Task → Type uSignature)
    (signature : ∀ task, World → Signature task)
    {Observation : Type uObservation}
    (observe : World → Observation)
    (sufficient : MultiTaskSufficient Signature signature observe) :
    IsObservationRefinement
      (MultiTaskSignature Signature signature) observe := by
  intro left right sameObservation
  funext task
  exact sufficient task left right sameObservation

/-- The join projects back to every task signature without loss. -/
theorem multiTask_join_recovers_each_task
    {World : Type uWorld} {Task : Type uTask}
    (Signature : Task → Type uSignature)
    (signature : ∀ task, World → Signature task)
    (task : Task) (world : World) :
    MultiTaskSignature Signature signature world task = signature task world :=
  rfl

/-! ## Exact no-universal-minimal-ontology witness -/

def firstTaskOptic : Bool × Bool → Bool := Prod.fst
def secondTaskOptic : Bool × Bool → Bool := Prod.snd
def twoTaskJoinOptic : Bool × Bool → Bool × Bool := fun world => (world.1, world.2)

theorem first_task_optic_is_insufficient_for_second_task :
    ¬ (∀ left right : Bool × Bool,
      firstTaskOptic left = firstTaskOptic right →
        secondTaskOptic left = secondTaskOptic right) := by
  intro sufficient
  have impossible := sufficient (false, false) (false, true) rfl
  simp [secondTaskOptic] at impossible

theorem second_task_optic_is_insufficient_for_first_task :
    ¬ (∀ left right : Bool × Bool,
      secondTaskOptic left = secondTaskOptic right →
        firstTaskOptic left = firstTaskOptic right) := by
  intro sufficient
  have impossible := sufficient (false, false) (true, false) rfl
  simp [firstTaskOptic] at impossible

theorem twoTaskJoinOptic_is_sufficient_for_both_tasks :
    (∀ left right : Bool × Bool,
      twoTaskJoinOptic left = twoTaskJoinOptic right →
        firstTaskOptic left = firstTaskOptic right) ∧
      (∀ left right : Bool × Bool,
        twoTaskJoinOptic left = twoTaskJoinOptic right →
          secondTaskOptic left = secondTaskOptic right) := by
  constructor <;> intro left right sameJoin
  · exact congrArg Prod.fst sameJoin
  · exact congrArg Prod.snd sameJoin

theorem twoTask_join_has_strictly_more_cells_than_each_single_task :
    Fintype.card Bool < Fintype.card (Bool × Bool) := by
  norm_num [Fintype.card_prod]

/-- Exact scope theorem: neither single-task minimal signature is sufficient
for the other task, while their join is sufficient for both and has strictly
more finite cells. -/
theorem no_universal_single_task_minimal_ontology_countermodel :
    (¬ (∀ left right : Bool × Bool,
      firstTaskOptic left = firstTaskOptic right →
        secondTaskOptic left = secondTaskOptic right)) ∧
      (¬ (∀ left right : Bool × Bool,
        secondTaskOptic left = secondTaskOptic right →
          firstTaskOptic left = firstTaskOptic right)) ∧
      ((∀ left right : Bool × Bool,
        twoTaskJoinOptic left = twoTaskJoinOptic right →
          firstTaskOptic left = firstTaskOptic right) ∧
        (∀ left right : Bool × Bool,
          twoTaskJoinOptic left = twoTaskJoinOptic right →
            secondTaskOptic left = secondTaskOptic right)) ∧
      Fintype.card Bool < Fintype.card (Bool × Bool) := by
  exact ⟨first_task_optic_is_insufficient_for_second_task,
    second_task_optic_is_insufficient_for_first_task,
    twoTaskJoinOptic_is_sufficient_for_both_tasks,
    twoTask_join_has_strictly_more_cells_than_each_single_task⟩

end OCKIndividuationMSpaceComposition
