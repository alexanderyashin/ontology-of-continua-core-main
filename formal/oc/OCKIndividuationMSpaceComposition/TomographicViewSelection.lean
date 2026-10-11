import OCKIndividuationMSpaceComposition.FiniteObservationRefinementBudget
import Mathlib.Data.Fintype.Card
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite task-relevant view selection

This is the finite bridge from tomography to adaptive optics: score a candidate
view by the number of *task-relevant* collisions it removes, then price that
reduction separately. It is not a claim of globally optimal experiment design,
and it never treats a derived feature of an existing view as new information.
-/

section FiniteView

variable {World Base View Outcome : Type*}
  [Fintype World] [DecidableEq World] [DecidableEq Base]
  [DecidableEq View] [DecidableEq Outcome]

def tomographicAugmentedObservation
    (base : World → Base) (view : World → View) : World → Base × View :=
  fun world => (base world, view world)

noncomputable def tomographicViewCollisionReduction
    (base : World → Base) (view : World → View) (target : World → Outcome) : Nat :=
  observationCollisionPairCount base target -
    observationCollisionPairCount (tomographicAugmentedObservation base view) target

theorem tomographicAugmentedObservation_refines
    (base : World → Base) (view : World → View) :
    ObservationRefines base (tomographicAugmentedObservation base view) := by
  exact ⟨Prod.fst, fun world => rfl⟩

theorem tomographicAugmentedObservation_eq_iff_base_eq_of_derived_view
    (base : World → Base) (view : World → View) (derive : Base → View)
    (view_is_derived : ∀ world, view world = derive (base world))
    (left right : World) :
    tomographicAugmentedObservation base view left =
        tomographicAugmentedObservation base view right ↔
      base left = base right := by
  constructor
  · intro equal
    exact congrArg Prod.fst equal
  · intro equal
    apply Prod.ext equal
    calc
      view left = derive (base left) := view_is_derived left
      _ = derive (base right) := by rw [equal]
      _ = view right := (view_is_derived right).symm

theorem tomographicViewCollisionReduction_nonnegative
    (base : World → Base) (view : World → View) (target : World → Outcome) :
    0 ≤ tomographicViewCollisionReduction base view target := by
  unfold tomographicViewCollisionReduction
  exact Nat.zero_le _

theorem tomographicViewCollisionReduction_le_base
    (base : World → Base) (view : World → View) (target : World → Outcome) :
    tomographicViewCollisionReduction base view target ≤
      observationCollisionPairCount base target := by
  unfold tomographicViewCollisionReduction
  exact Nat.sub_le _ _

/-- If every base collision is split by the candidate view, the augmented
collision budget is zero and the finite task predictor exists. -/
theorem tomographicView_splits_all_task_collisions
    (base : World → Base) (view : World → View) (target : World → Outcome)
    (splits : ∀ pair : ObservationCollisionPair base target,
      tomographicAugmentedObservation base view pair.1.1 ≠
        tomographicAugmentedObservation base view pair.1.2) :
    observationCollisionPairCount
        (tomographicAugmentedObservation base view) target = 0 := by
  classical
  letI : Fintype (ObservationCollisionPair
      (tomographicAugmentedObservation base view) target) :=
    observationCollisionPairFintype
      (tomographicAugmentedObservation base view) target
  letI : IsEmpty (ObservationCollisionPair
      (tomographicAugmentedObservation base view) target) :=
    ⟨fun pair => by
      let baseCollision : ObservationCollisionPair base target :=
        ⟨(pair.1.1, pair.1.2), by
          exact ⟨pair.2.1,
            congrArg Prod.fst pair.2.2.1,
            pair.2.2.2⟩⟩
      simpa [baseCollision] using (splits baseCollision) pair.2.2.1⟩
  change Fintype.card (ObservationCollisionPair
      (tomographicAugmentedObservation base view) target) = 0
  exact Fintype.card_eq_zero

theorem tomographicView_zero_budget_has_exact_task_predictor
    [Inhabited Outcome]
    (base : World → Base) (view : World → View) (target : World → Outcome)
    (splits : ∀ pair : ObservationCollisionPair base target,
      tomographicAugmentedObservation base view pair.1.1 ≠
        tomographicAugmentedObservation base view pair.1.2) :
    ∃ predict : (Base × View) → Outcome, ∀ world,
      predict (tomographicAugmentedObservation base view world) = target world := by
  apply zero_collision_pair_budget_has_exact_predictor
  exact tomographicView_splits_all_task_collisions base view target splits

/-- Exact reduction is the entire finite unresolved budget when the candidate
view splits all task-relevant aliases. -/
theorem tomographicView_full_reduction_of_collision_split
    (base : World → Base) (view : World → View) (target : World → Outcome)
    (splits : ∀ pair : ObservationCollisionPair base target,
      tomographicAugmentedObservation base view pair.1.1 ≠
        tomographicAugmentedObservation base view pair.1.2) :
    tomographicViewCollisionReduction base view target =
      observationCollisionPairCount base target := by
  have zero := tomographicView_splits_all_task_collisions base view target splits
  unfold tomographicViewCollisionReduction
  rw [zero, Nat.sub_zero]

/-- A positive collision reduction is still not a semantic identity claim: it
only counts aliases on this frozen finite world/target registration. -/
theorem tomographicView_positive_reduction_is_bounded_claim
    (base : World → Base) (view : World → View) (target : World → Outcome)
    (positive : 0 < tomographicViewCollisionReduction base view target) :
    observationCollisionPairCount
        (tomographicAugmentedObservation base view) target <
      observationCollisionPairCount base target := by
  unfold tomographicViewCollisionReduction at positive
  exact (Nat.sub_pos_iff_lt).mp positive

end FiniteView

end OCKIndividuationMSpaceComposition
