import Mathlib.Algebra.Order.Field.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.Finset.Card
import Mathlib.Data.Real.Basic

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/--
If every state coordinate must receive information at least `target`, while
each trial has squared probe energy at most `energy`, double counting forces
`dimensions * target ≤ trials * energy`.
-/
theorem coordinateInformation_budget_bound
    {trials dimensions : ℕ}
    (probe : Fin trials → Fin dimensions → ℝ)
    (target energy : ℝ)
    (coordinateInfo : ∀ j, target ≤ ∑ i, (probe i j) ^ 2)
    (trialEnergy : ∀ i, ∑ j, (probe i j) ^ 2 ≤ energy) :
    (dimensions : ℝ) * target ≤ (trials : ℝ) * energy := by
  calc
    (dimensions : ℝ) * target = ∑ _j : Fin dimensions, target := by simp
    _ ≤ ∑ j : Fin dimensions, ∑ i : Fin trials, (probe i j) ^ 2 :=
      Finset.sum_le_sum fun j _ => coordinateInfo j
    _ = ∑ i : Fin trials, ∑ j : Fin dimensions, (probe i j) ^ 2 := by
      rw [Finset.sum_comm]
    _ ≤ ∑ _i : Fin trials, energy :=
      Finset.sum_le_sum fun i _ => trialEnergy i
    _ = (trials : ℝ) * energy := by simp

/-- Positive lower-bound form when the per-trial energy budget is nonzero. -/
theorem trials_lower_bound_of_uniform_coordinate_information
    {trials dimensions : ℕ}
    (probe : Fin trials → Fin dimensions → ℝ)
    (target energy : ℝ) (energyPositive : 0 < energy)
    (coordinateInfo : ∀ j, target ≤ ∑ i, (probe i j) ^ 2)
    (trialEnergy : ∀ i, ∑ j, (probe i j) ^ 2 ≤ energy) :
    (dimensions : ℝ) * target / energy ≤ trials := by
  apply (div_le_iff₀ energyPositive).2
  simpa [mul_comm] using
    coordinateInformation_budget_bound probe target energy coordinateInfo trialEnergy

/--
No-go: a trial count strictly below the energy lower bound cannot provide the
registered information target in every state coordinate.
-/
theorem insufficient_trials_block_uniform_coordinate_information
    {trials dimensions : ℕ}
    (probe : Fin trials → Fin dimensions → ℝ)
    (target energy : ℝ) (energyPositive : 0 < energy)
    (tooFew : (trials : ℝ) < (dimensions : ℝ) * target / energy) :
    ¬ ((∀ j, target ≤ ∑ i, (probe i j) ^ 2) ∧
       (∀ i, ∑ j, (probe i j) ^ 2 ≤ energy)) := by
  intro contracts
  have lower := trials_lower_bound_of_uniform_coordinate_information
    probe target energy energyPositive contracts.1 contracts.2
  exact (not_le_of_gt tooFew) lower

/--
An affine intercept equal to one contributes exactly one unit of information
per trial, hence its target cannot exceed the trial count.
-/
theorem affineIntercept_information_bound
    {trials : ℕ} (target : ℝ)
    (interceptInfo : target ≤ ∑ _i : Fin trials, (1 : ℝ)) :
    target ≤ trials := by
  simpa using interceptInfo

/-- Combined state-energy and affine-intercept necessary lower bound. -/
theorem affine_uniform_information_lower_bound
    {trials dimensions : ℕ}
    (probe : Fin trials → Fin dimensions → ℝ)
    (target energy : ℝ) (energyPositive : 0 < energy)
    (coordinateInfo : ∀ j, target ≤ ∑ i, (probe i j) ^ 2)
    (trialEnergy : ∀ i, ∑ j, (probe i j) ^ 2 ≤ energy)
    (interceptInfo : target ≤ ∑ _i : Fin trials, (1 : ℝ)) :
    max target ((dimensions : ℝ) * target / energy) ≤ trials := by
  apply max_le
  · exact affineIntercept_information_bound target interceptInfo
  · exact trials_lower_bound_of_uniform_coordinate_information
      probe target energy energyPositive coordinateInfo trialEnergy

end OCKIndividuationMSpaceComposition
