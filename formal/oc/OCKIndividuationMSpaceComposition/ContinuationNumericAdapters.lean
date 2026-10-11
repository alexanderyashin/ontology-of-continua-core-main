import OCKIndividuationMSpaceComposition.GovernanceBarrierHazard
import OCKIndividuationMSpaceComposition.InterventionalContrastIdentification
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Minimal OC adapters from reusable finite laws to the numerical packet

The product/CDF algebra and symmetric arm-error propagation already exist in
the corpus.  This module adds only the typed finite adapter needed by the
continuation packet: a named TV-drift quantity and an asymmetric clipped ATE
interval.  It does not assert that an arbitrary TV sequence is a product
channel; that semantic contract remains an explicit premise of P1.
-/

def composedTVDrift (delta : ℕ → ℚ) (horizon : ℕ) : ℚ :=
  1 - ∏ t ∈ Finset.range horizon, (1 - delta t)

theorem composedTVDrift_eq_barrierCdf (delta : ℕ → ℚ) (horizon : ℕ) :
    composedTVDrift delta horizon = barrierCdf delta horizon := by
  rfl

theorem valid_composedTVDrift_bounds
    (delta : ℕ → ℚ) (valid : ValidBarrierHazard delta) (horizon : ℕ) :
    0 ≤ composedTVDrift delta horizon ∧ composedTVDrift delta horizon ≤ 1 := by
  rw [composedTVDrift_eq_barrierCdf]
  exact barrierCdf_bounds delta valid horizon

/-! ## Explicit retained-mass contract for the product law -/

structure FiniteRetentionHazardContract (horizon : Nat) where
  hazard : Nat → ℚ
  valid : ValidBarrierHazard hazard
  survival : Nat → ℚ
  initial : survival 0 = 1
  step : ∀ t, t < horizon → survival (t + 1) = survival t * (1 - hazard t)

theorem retention_contract_survival_eq_product
    (contract : FiniteRetentionHazardContract horizon) :
    contract.survival horizon = barrierSurvival contract.hazard horizon := by
  have prefixEquality : ∀ n, n ≤ horizon →
      contract.survival n = barrierSurvival contract.hazard n := by
    intro n bound
    induction n with
    | zero =>
        simpa [barrierSurvival] using contract.initial
    | succ n ih =>
        have below : n < horizon := Nat.lt_of_succ_le bound
        rw [contract.step n below, ih (Nat.le_of_lt below), barrierSurvival_succ]
  exact prefixEquality horizon le_rfl

def retentionContractDrift
    (contract : FiniteRetentionHazardContract horizon) : ℚ :=
  1 - contract.survival horizon

theorem retention_contract_drift_eq_composedTVDrift
    (contract : FiniteRetentionHazardContract horizon) :
    retentionContractDrift contract =
      composedTVDrift contract.hazard horizon := by
  rw [retentionContractDrift, retention_contract_survival_eq_product]
  rfl

theorem valid_retention_contract_drift_bounds
    (contract : FiniteRetentionHazardContract horizon) :
    0 ≤ retentionContractDrift contract ∧ retentionContractDrift contract ≤ 1 := by
  rw [retention_contract_drift_eq_composedTVDrift]
  exact valid_composedTVDrift_bounds contract.hazard contract.valid horizon

/-! ## Lean-to-packet finite canary -/

def packetTVHazard : ℕ → ℚ
  | 0 => 2 / 100
  | 1 => 3 / 100
  | 2 => 1 / 100
  | _ => 0

def packetRetentionWitness : FiniteRetentionHazardContract 3 where
  hazard := packetTVHazard
  valid := by
    intro t
    rcases t with _ | t
    · norm_num [packetTVHazard]
    · rcases t with _ | t
      · norm_num [packetTVHazard]
      · rcases t with _ | t
        · norm_num [packetTVHazard]
        · simp [packetTVHazard, Nat.add_assoc]
  survival := fun n => barrierSurvival packetTVHazard n
  initial := by simp [barrierSurvival]
  step := by
    intro t _
    rw [barrierSurvival_succ]

theorem packetRetentionWitness_drift :
    retentionContractDrift packetRetentionWitness = (58906 / 1000000 : ℚ) := by
  norm_num [retentionContractDrift, packetRetentionWitness, barrierSurvival,
    packetTVHazard, Finset.prod_range_succ]

def clippedLower (lower mean radius : ℚ) : ℚ := max lower (mean - radius)

def clippedUpper (upper mean radius : ℚ) : ℚ := min upper (mean + radius)

theorem packetClippedATEInterval_values :
    clippedLower 0 (4 / 5 : ℚ) (58906 / 1000000) -
          clippedUpper 1 (1 / 5 : ℚ) (58906 / 1000000) =
        (482188 / 1000000 : ℚ) ∧
      clippedUpper 1 (4 / 5 : ℚ) (58906 / 1000000) -
          clippedLower 0 (1 / 5 : ℚ) (58906 / 1000000) =
        (717812 / 1000000 : ℚ) := by
  norm_num [clippedLower, clippedUpper]

def unconstrainedSurvivalA (_ : ℕ) : ℚ := 1

def unconstrainedSurvivalB : ℕ → ℚ
  | 0 => 1
  | _ => 0

/-- Initial survival alone cannot identify a later survival mass. -/
theorem no_product_without_retention_contract :
    ∃ survivalA survivalB : ℕ → ℚ,
      survivalA 0 = 1 ∧ survivalB 0 = 1 ∧ survivalA 3 ≠ survivalB 3 := by
  refine ⟨unconstrainedSurvivalA, unconstrainedSurvivalB, ?_, ?_, ?_⟩
  · norm_num [unconstrainedSurvivalA]
  · norm_num [unconstrainedSurvivalB]
  · norm_num [unconstrainedSurvivalA, unconstrainedSurvivalB]

/-- A bounded target arm mean lies in its clipped source-radius interval. -/
theorem bounded_mean_in_clipped_interval
    (lower upper sourceMean targetMean radius : ℚ)
    (targetRange : lower ≤ targetMean ∧ targetMean ≤ upper)
    (errorBound : |targetMean - sourceMean| ≤ radius) :
    clippedLower lower sourceMean radius ≤ targetMean ∧
      targetMean ≤ clippedUpper upper sourceMean radius := by
  have errorBounds := abs_le.mp errorBound
  have radiusNonnegative : 0 ≤ radius :=
    le_trans (abs_nonneg (targetMean - sourceMean)) errorBound
  constructor
  · apply max_le
    · exact targetRange.1
    · linarith [radiusNonnegative]
  · apply le_min
    · exact targetRange.2
    · linarith [radiusNonnegative]

/-- Asymmetric clipped arm radii induce the packet's ATE identified interval. -/
theorem asymmetric_clipped_ate_interval_sound
    (lower upper sourceUntreated sourceTreated targetUntreated targetTreated
      untreatedRadius treatedRadius : ℚ)
    (untreatedTargetRange : lower ≤ targetUntreated ∧ targetUntreated ≤ upper)
    (treatedTargetRange : lower ≤ targetTreated ∧ targetTreated ≤ upper)
    (untreatedError : |targetUntreated - sourceUntreated| ≤ untreatedRadius)
    (treatedError : |targetTreated - sourceTreated| ≤ treatedRadius) :
    clippedLower lower sourceTreated treatedRadius -
          clippedUpper upper sourceUntreated untreatedRadius ≤
        targetTreated - targetUntreated ∧
      targetTreated - targetUntreated ≤
        clippedUpper upper sourceTreated treatedRadius -
          clippedLower lower sourceUntreated untreatedRadius := by
  have untreatedInterval := bounded_mean_in_clipped_interval lower upper
    sourceUntreated targetUntreated untreatedRadius untreatedTargetRange
    untreatedError
  have treatedInterval := bounded_mean_in_clipped_interval lower upper
    sourceTreated targetTreated treatedRadius treatedTargetRange treatedError
  constructor <;> linarith [untreatedInterval.1, untreatedInterval.2,
    treatedInterval.1, treatedInterval.2]

end OCKIndividuationMSpaceComposition
