import OCKIndividuationMSpaceComposition.FixedEnergyExperimentalDesign
import Mathlib.Algebra.BigOperators.Ring.Finset

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/--
Anisotropic information conservation.  Coordinate `j` has nonnegative cost
`cost j` and required information `target j`; every trial has weighted energy
at most `energy`.  No distributional or nonadaptivity premise is used.
-/
theorem weightedCoordinateInformation_budget_bound
    {trials dimensions : ℕ}
    (probe : Fin trials → Fin dimensions → ℝ)
    (cost target : Fin dimensions → ℝ) (energy : ℝ)
    (costNonnegative : ∀ j, 0 ≤ cost j)
    (coordinateInfo : ∀ j, target j ≤ ∑ i, (probe i j) ^ 2)
    (trialEnergy : ∀ i, ∑ j, cost j * (probe i j) ^ 2 ≤ energy) :
    (∑ j, cost j * target j) ≤ (trials : ℝ) * energy := by
  calc
    (∑ j, cost j * target j) ≤
        ∑ j, cost j * (∑ i, (probe i j) ^ 2) :=
      Finset.sum_le_sum fun j _ =>
        mul_le_mul_of_nonneg_left (coordinateInfo j) (costNonnegative j)
    _ = ∑ j, ∑ i, cost j * (probe i j) ^ 2 := by
      apply Finset.sum_congr rfl
      intro j _
      rw [Finset.mul_sum]
    _ = ∑ i, ∑ j, cost j * (probe i j) ^ 2 := by
      rw [Finset.sum_comm]
    _ ≤ ∑ _i : Fin trials, energy :=
      Finset.sum_le_sum fun i _ => trialEnergy i
    _ = (trials : ℝ) * energy := by simp

/-- Weighted trial lower bound for positive per-trial energy. -/
theorem weighted_trials_lower_bound
    {trials dimensions : ℕ}
    (probe : Fin trials → Fin dimensions → ℝ)
    (cost target : Fin dimensions → ℝ) (energy : ℝ)
    (energyPositive : 0 < energy)
    (costNonnegative : ∀ j, 0 ≤ cost j)
    (coordinateInfo : ∀ j, target j ≤ ∑ i, (probe i j) ^ 2)
    (trialEnergy : ∀ i, ∑ j, cost j * (probe i j) ^ 2 ≤ energy) :
    (∑ j, cost j * target j) / energy ≤ trials := by
  apply (div_le_iff₀ energyPositive).2
  simpa [mul_comm] using weightedCoordinateInformation_budget_bound
    probe cost target energy costNonnegative coordinateInfo trialEnergy

/--
An adaptive policy is evaluated on an arbitrary realized history.  Since the
bound is pathwise, choosing later probes from earlier observations cannot beat
the weighted energy-information lower bound.
-/
theorem adaptivePolicy_realization_obeys_weighted_budget
    {trials dimensions : ℕ} {History : Type*}
    (policy : Fin trials → History → Fin dimensions → ℝ)
    (history : Fin trials → History)
    (cost target : Fin dimensions → ℝ) (energy : ℝ)
    (costNonnegative : ∀ j, 0 ≤ cost j)
    (coordinateInfo :
      ∀ j, target j ≤ ∑ i, (policy i (history i) j) ^ 2)
    (trialEnergy :
      ∀ i, ∑ j, cost j * (policy i (history i) j) ^ 2 ≤ energy) :
    (∑ j, cost j * target j) ≤ (trials : ℝ) * energy := by
  exact weightedCoordinateInformation_budget_bound
    (fun i j => policy i (history i) j) cost target energy
    costNonnegative coordinateInfo trialEnergy

/-- Adaptive no-go below the anisotropic information/energy floor. -/
theorem adaptivePolicy_insufficient_trials_no_go
    {trials dimensions : ℕ} {History : Type*}
    (policy : Fin trials → History → Fin dimensions → ℝ)
    (history : Fin trials → History)
    (cost target : Fin dimensions → ℝ) (energy : ℝ)
    (energyPositive : 0 < energy)
    (costNonnegative : ∀ j, 0 ≤ cost j)
    (tooFew :
      (trials : ℝ) < (∑ j, cost j * target j) / energy) :
    ¬ ((∀ j, target j ≤ ∑ i, (policy i (history i) j) ^ 2) ∧
       (∀ i, ∑ j, cost j * (policy i (history i) j) ^ 2 ≤ energy)) := by
  intro contracts
  have lower := weighted_trials_lower_bound
    (fun i j => policy i (history i) j) cost target energy energyPositive
    costNonnegative contracts.1 contracts.2
  exact (not_le_of_gt tooFew) lower

/-- Known-support sparse information conservation. -/
theorem sparseActiveSet_information_budget_bound
    {trials dimensions : ℕ}
    (active : Finset (Fin dimensions))
    (probe : Fin trials → Fin dimensions → ℝ)
    (target energy : ℝ)
    (coordinateInfo : ∀ j ∈ active, target ≤ ∑ i, (probe i j) ^ 2)
    (trialActiveEnergy : ∀ i, ∑ j ∈ active, (probe i j) ^ 2 ≤ energy) :
    (active.card : ℝ) * target ≤ (trials : ℝ) * energy := by
  calc
    (active.card : ℝ) * target = ∑ _j ∈ active, target := by simp
    _ ≤ ∑ j ∈ active, ∑ i : Fin trials, (probe i j) ^ 2 :=
      Finset.sum_le_sum fun j inActive => coordinateInfo j inActive
    _ = ∑ i : Fin trials, ∑ j ∈ active, (probe i j) ^ 2 := by
      rw [Finset.sum_comm]
    _ ≤ ∑ _i : Fin trials, energy :=
      Finset.sum_le_sum fun i _ => trialActiveEnergy i
    _ = (trials : ℝ) * energy := by simp

/-- Sparse no-go below `|active| * target / energy`. -/
theorem sparse_insufficient_trials_no_go
    {trials dimensions : ℕ}
    (active : Finset (Fin dimensions))
    (probe : Fin trials → Fin dimensions → ℝ)
    (target energy : ℝ) (energyPositive : 0 < energy)
    (tooFew : (trials : ℝ) < (active.card : ℝ) * target / energy) :
    ¬ ((∀ j ∈ active, target ≤ ∑ i, (probe i j) ^ 2) ∧
       (∀ i, ∑ j ∈ active, (probe i j) ^ 2 ≤ energy)) := by
  intro contracts
  have budget := sparseActiveSet_information_budget_bound
    active probe target energy contracts.1 contracts.2
  have lower : (active.card : ℝ) * target / energy ≤ trials := by
    apply (div_le_iff₀ energyPositive).2
    simpa [mul_comm] using budget
  exact (not_le_of_gt tooFew) lower

end OCKIndividuationMSpaceComposition
