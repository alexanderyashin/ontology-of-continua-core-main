import OCKIndividuationMSpaceComposition.ContinuationNumericAdapters

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
# Typed causal-TV/product adapter

This is the smallest semantic adapter needed by the finite OC packet.  It does
not infer a product law from arbitrary observed causal-TV values.  Instead it
requires the explicit conditional-retention equations as a contract, then
proves existence, exact product survival, and sharpness inside that contract.
-/

structure CausalTVProductAdapter (horizon : Nat) where
  causalTV : Nat → ℚ
  valid : ValidBarrierHazard causalTV
  survival : Nat → ℚ
  initial : survival 0 = 1
  conditionalRetention : ∀ t, t < horizon →
    survival (t + 1) = survival t * (1 - causalTV t)

def CausalTVProductAdapter.toRetentionContract
    (adapter : CausalTVProductAdapter horizon) :
    FiniteRetentionHazardContract horizon :=
  {
    hazard := adapter.causalTV
    valid := adapter.valid
    survival := adapter.survival
    initial := adapter.initial
    step := adapter.conditionalRetention
  }

theorem causalTVProductAdapter_survival_eq_product
    (adapter : CausalTVProductAdapter horizon) :
    adapter.survival horizon = barrierSurvival adapter.causalTV horizon := by
  exact retention_contract_survival_eq_product adapter.toRetentionContract

def canonicalCausalTVProductAdapter
    (causalTV : Nat → ℚ)
    (valid : ValidBarrierHazard causalTV)
    (horizon : Nat) : CausalTVProductAdapter horizon :=
  {
    causalTV := causalTV
    valid := valid
    survival := fun n => barrierSurvival causalTV n
    initial := barrierSurvival_zero causalTV
    conditionalRetention := by
      intro t _
      exact barrierSurvival_succ causalTV t
  }

theorem every_valid_causalTV_has_product_adapter
    (causalTV : Nat → ℚ)
    (valid : ValidBarrierHazard causalTV)
    (horizon : Nat) :
    ∃ adapter : CausalTVProductAdapter horizon,
      adapter.causalTV = causalTV ∧
        adapter.survival horizon = barrierSurvival causalTV horizon := by
  let adapter := canonicalCausalTVProductAdapter causalTV valid horizon
  refine ⟨adapter, rfl, ?_⟩
  exact causalTVProductAdapter_survival_eq_product adapter

theorem causalTV_product_drift_exact
    (adapter : CausalTVProductAdapter horizon) :
    1 - adapter.survival horizon =
      1 - ∏ t ∈ Finset.range horizon, (1 - adapter.causalTV t) := by
  rw [causalTVProductAdapter_survival_eq_product]
  rfl

theorem causalTV_product_drift_sharp
    (causalTV : Nat → ℚ)
    (valid : ValidBarrierHazard causalTV)
    (horizon : Nat) :
    ∃ adapter : CausalTVProductAdapter horizon,
      1 - adapter.survival horizon =
        1 - ∏ t ∈ Finset.range horizon, (1 - causalTV t) := by
  rcases every_valid_causalTV_has_product_adapter causalTV valid horizon with
    ⟨adapter, _, survivalEq⟩
  refine ⟨adapter, ?_⟩
  rw [survivalEq]
  rfl

end OCKIndividuationMSpaceComposition
