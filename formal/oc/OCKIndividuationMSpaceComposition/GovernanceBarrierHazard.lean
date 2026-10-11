import OCKIndividuationMSpaceComposition.TemporalGovernanceRequalification
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-! Finite discrete survival mechanics for governance barriers. -/

/-- Probability of no barrier before `horizon`, for rational conditional hazards. -/
def barrierSurvival (hazard : ℕ → ℚ) (horizon : ℕ) : ℚ :=
  ∏ t ∈ Finset.range horizon, (1 - hazard t)

/-- Probability mass assigned to a first barrier at exactly `t`. -/
def firstBarrierMass (hazard : ℕ → ℚ) (t : ℕ) : ℚ :=
  barrierSurvival hazard t * hazard t

/-- Cumulative probability of a barrier before the declared horizon. -/
def barrierCdf (hazard : ℕ → ℚ) (horizon : ℕ) : ℚ :=
  1 - barrierSurvival hazard horizon

/-- Every conditional hazard lies in the probability interval. -/
def ValidBarrierHazard (hazard : ℕ → ℚ) : Prop :=
  ∀ t, 0 ≤ hazard t ∧ hazard t ≤ 1

@[simp] theorem barrierSurvival_zero (hazard : ℕ → ℚ) :
    barrierSurvival hazard 0 = 1 := by
  simp [barrierSurvival]

theorem barrierSurvival_succ (hazard : ℕ → ℚ) (horizon : ℕ) :
    barrierSurvival hazard (horizon + 1) =
      barrierSurvival hazard horizon * (1 - hazard horizon) := by
  simp [barrierSurvival, Finset.prod_range_succ]

/-- One-step CDF increment is exactly the first-barrier mass. -/
theorem barrierCdf_succ_sub (hazard : ℕ → ℚ) (horizon : ℕ) :
    barrierCdf hazard (horizon + 1) - barrierCdf hazard horizon =
      firstBarrierMass hazard horizon := by
  rw [barrierCdf, barrierCdf, barrierSurvival_succ]
  ring_nf
  simp [firstBarrierMass]

/-- Finite conservation: cumulative incidence is the sum of first-event masses. -/
theorem barrierCdf_eq_sum_firstBarrierMass (hazard : ℕ → ℚ) (horizon : ℕ) :
    barrierCdf hazard horizon =
      ∑ t ∈ Finset.range horizon, firstBarrierMass hazard t := by
  induction horizon with
  | zero => simp [barrierCdf]
  | succ horizon ih =>
      rw [Finset.sum_range_succ, ← ih]
      simp only [barrierCdf, barrierSurvival_succ, firstBarrierMass]
      ring

/-- Valid hazards keep survival and cumulative incidence within `[0,1]`. -/
theorem barrierSurvival_bounds
    (hazard : ℕ → ℚ) (valid : ValidBarrierHazard hazard) (horizon : ℕ) :
    0 ≤ barrierSurvival hazard horizon ∧ barrierSurvival hazard horizon ≤ 1 := by
  induction horizon with
  | zero => simp
  | succ horizon ih =>
      rw [barrierSurvival_succ]
      have factorNonnegative : 0 ≤ 1 - hazard horizon := sub_nonneg.mpr (valid horizon).2
      have factorAtMostOne : 1 - hazard horizon ≤ 1 := by linarith [(valid horizon).1]
      constructor
      · exact mul_nonneg ih.1 factorNonnegative
      · calc
          barrierSurvival hazard horizon * (1 - hazard horizon) ≤
              1 * (1 - hazard horizon) :=
            mul_le_mul_of_nonneg_right ih.2 factorNonnegative
          _ ≤ 1 * 1 := mul_le_mul_of_nonneg_left factorAtMostOne (by norm_num)
          _ = 1 := by ring

theorem barrierCdf_bounds
    (hazard : ℕ → ℚ) (valid : ValidBarrierHazard hazard) (horizon : ℕ) :
    0 ≤ barrierCdf hazard horizon ∧ barrierCdf hazard horizon ≤ 1 := by
  have survivalBounds := barrierSurvival_bounds hazard valid horizon
  simp only [barrierCdf]
  constructor <;> linarith

/-- Cumulative barrier probability is monotone in the horizon. -/
theorem barrierCdf_mono_succ
    (hazard : ℕ → ℚ) (valid : ValidBarrierHazard hazard) (horizon : ℕ) :
    barrierCdf hazard horizon ≤ barrierCdf hazard (horizon + 1) := by
  have survivalNonnegative := (barrierSurvival_bounds hazard valid horizon).1
  have hazardNonnegative := (valid horizon).1
  have massNonnegative : 0 ≤ firstBarrierMass hazard horizon :=
    mul_nonneg survivalNonnegative hazardNonnegative
  linarith [barrierCdf_succ_sub hazard horizon]

/-- Constant conditional hazard. -/
def constantBarrierHazard (rate : ℚ) : ℕ → ℚ := fun _ => rate

/-- Exact geometric survival law for a constant hazard. -/
theorem constantBarrierHazard_survival (rate : ℚ) (horizon : ℕ) :
    barrierSurvival (constantBarrierHazard rate) horizon = (1 - rate) ^ horizon := by
  induction horizon with
  | zero => simp
  | succ horizon ih =>
      rw [barrierSurvival_succ, ih]
      simp [constantBarrierHazard, pow_succ]

theorem constantBarrierHazard_cdf (rate : ℚ) (horizon : ℕ) :
    barrierCdf (constantBarrierHazard rate) horizon = 1 - (1 - rate) ^ horizon := by
  rw [barrierCdf, constantBarrierHazard_survival]

/-- First horizon at which the barrier CDF reaches a declared probability. -/
def BarrierQuantileAt (hazard : ℕ → ℚ) (probability : ℚ) (horizon : ℕ) : Prop :=
  probability ≤ barrierCdf hazard horizon ∧
    ∀ earlier, earlier < horizon → barrierCdf hazard earlier < probability

theorem barrierQuantileAt_unique
    (hazard : ℕ → ℚ) (probability : ℚ) {first second : ℕ}
    (firstQuantile : BarrierQuantileAt hazard probability first)
    (secondQuantile : BarrierQuantileAt hazard probability second) :
    first = second := by
  rcases lt_trichotomy first second with before | equal | after
  · exact False.elim ((not_lt_of_ge firstQuantile.1) (secondQuantile.2 first before))
  · exact equal
  · exact False.elim ((not_lt_of_ge secondQuantile.1) (firstQuantile.2 second after))

theorem first_barrier_quantile_exists_of_reaches
    (hazard : ℕ → ℚ) (probability : ℚ) (observedHorizon : ℕ)
    (reaches : probability ≤ barrierCdf hazard observedHorizon) :
    ∃ first, BarrierQuantileAt hazard probability first := by
  let predicate : ℕ → Prop := fun horizon => probability ≤ barrierCdf hazard horizon
  have existsPredicate : ∃ horizon, predicate horizon := ⟨observedHorizon, reaches⟩
  refine ⟨Nat.find existsPredicate, Nat.find_spec existsPredicate, ?_⟩
  intro earlier before
  exact lt_of_not_ge (Nat.find_min existsPredicate before)

/-- Independent competing risks combine through complement multiplication. -/
def combinedStepHazard (trigger revoke expiry : ℚ) : ℚ :=
  1 - (1 - trigger) * (1 - revoke) * (1 - expiry)

theorem combinedStepHazard_complement
    (trigger revoke expiry : ℚ) :
    1 - combinedStepHazard trigger revoke expiry =
      (1 - trigger) * (1 - revoke) * (1 - expiry) := by
  simp [combinedStepHazard]

/--
No-go: the same total hazard is compatible with a trigger-only and a
revocation-only mechanism, so total event times do not identify the cause.
-/
theorem combined_hazard_does_not_identify_cause
    (total : ℚ) (nonzero : total ≠ 0) :
    combinedStepHazard total 0 0 = combinedStepHazard 0 total 0 ∧
      total ≠ 0 := by
  constructor
  · simp [combinedStepHazard]
  · exact nonzero

end OCKIndividuationMSpaceComposition
