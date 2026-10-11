import OCKIndividuationMSpaceComposition.SequentialMonitoringBounds

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

/-!
## Spending optimization: polynomial anytime schedules and universal limits

Geometric alpha spending is valid but assigns exponentially vanishing mass to
late looks.  The telescoping schedule

`delta_i = delta / ((i+1)(i+2))`

has the same global guarantee and only polynomial decay.  This module proves
its exact finite-prefix spend and also proves the finite-horizon maximin limit:
under total budget `delta`, at least one of `H` looks receives at most
`delta/H`.  Equal spending attains that bound.
-/

/-- Telescoping polynomial alpha allocation. -/
noncomputable def polynomialAlphaSpending (delta : ℝ) (index : ℕ) : ℝ :=
  delta / (((index : ℝ) + 1) * ((index : ℝ) + 2))

/-- Finite prefix of polynomial spending. -/
noncomputable def cumulativePolynomialAlphaSpending
    (delta : ℝ) (looks : ℕ) : ℝ :=
  ∑ index ∈ Finset.range looks, polynomialAlphaSpending delta index

theorem polynomialAlphaSpending_nonnegative
    (delta : ℝ) (index : ℕ) (deltaNonnegative : 0 ≤ delta) :
    0 ≤ polynomialAlphaSpending delta index := by
  unfold polynomialAlphaSpending
  positivity

theorem polynomialAlphaSpending_positive
    (delta : ℝ) (index : ℕ) (deltaPositive : 0 < delta) :
    0 < polynomialAlphaSpending delta index := by
  unfold polynomialAlphaSpending
  positivity

/-- Each polynomial spend is a difference of adjacent reciprocal terms. -/
theorem polynomialAlphaSpending_difference
    (delta : ℝ) (index : ℕ) :
    polynomialAlphaSpending delta index =
      delta / ((index : ℝ) + 1) - delta / ((index : ℝ) + 2) := by
  unfold polynomialAlphaSpending
  have firstPositive : 0 < (index : ℝ) + 1 := by positivity
  have secondPositive : 0 < (index : ℝ) + 2 := by positivity
  field_simp
  ring

/-- Exact prefix identity: after `looks` inspections the schedule has spent
`delta * looks/(looks+1)`. -/
theorem cumulativePolynomialAlphaSpending_exact
    (delta : ℝ) (looks : ℕ) :
    cumulativePolynomialAlphaSpending delta looks =
      delta * (looks : ℝ) / ((looks : ℝ) + 1) := by
  induction looks with
  | zero => simp [cumulativePolynomialAlphaSpending]
  | succ looks inductionHypothesis =>
      rw [cumulativePolynomialAlphaSpending, Finset.sum_range_succ]
      rw [show (∑ index ∈ Finset.range looks,
          polynomialAlphaSpending delta index) =
            cumulativePolynomialAlphaSpending delta looks from rfl]
      rw [inductionHypothesis]
      unfold polynomialAlphaSpending
      push_cast
      have firstPositive : 0 < (looks : ℝ) + 1 := by positivity
      have secondPositive : 0 < (looks : ℝ) + 2 := by positivity
      field_simp
      ring

/-- Every finite prefix is anytime-valid under the global budget. -/
theorem cumulativePolynomialAlphaSpending_le
    (delta : ℝ) (looks : ℕ) (deltaNonnegative : 0 ≤ delta) :
    cumulativePolynomialAlphaSpending delta looks ≤ delta := by
  rw [cumulativePolynomialAlphaSpending_exact]
  have denominatorPositive : 0 < (looks : ℝ) + 1 := by positivity
  apply (div_le_iff₀ denominatorPositive).2
  nlinarith

/-- Union-bound adapter for the polynomial schedule; dependence between looks
is unrestricted. -/
theorem polynomial_alpha_spending_controls_any_finite_monitor
    (delta : ℝ) (looks : ℕ)
    (perLookFailure : ℕ → ℝ) (familywiseFailure : ℝ)
    (deltaNonnegative : 0 ≤ delta)
    (perLookBound :
      ∀ index ∈ Finset.range looks,
        perLookFailure index ≤ polynomialAlphaSpending delta index)
    (unionBound :
      familywiseFailure ≤ ∑ index ∈ Finset.range looks, perLookFailure index) :
    familywiseFailure ≤ delta := by
  calc
    familywiseFailure ≤
        ∑ index ∈ Finset.range looks, perLookFailure index := unionBound
    _ ≤ ∑ index ∈ Finset.range looks,
        polynomialAlphaSpending delta index := Finset.sum_le_sum perLookBound
    _ = cumulativePolynomialAlphaSpending delta looks := rfl
    _ ≤ delta := cumulativePolynomialAlphaSpending_le
      delta looks deltaNonnegative

/-- Equal allocation on a declared finite horizon. -/
noncomputable def equalHorizonAlphaSpending
    (delta : ℝ) (horizon : ℕ) (_index : Fin horizon) : ℝ :=
  delta / (horizon : ℝ)

/-- Equal finite-horizon spending uses the complete budget. -/
theorem equalHorizonAlphaSpending_total
    (delta : ℝ) (horizon : ℕ) (horizonPositive : 0 < horizon) :
    (∑ index : Fin horizon,
      equalHorizonAlphaSpending delta horizon index) = delta := by
  simp [equalHorizonAlphaSpending, Fintype.card_fin]
  have horizonCastNonzero : (horizon : ℝ) ≠ 0 := by
    exact_mod_cast (Nat.ne_of_gt horizonPositive)
  field_simp

/-- Universal finite-horizon maximin upper bound: any allocation with total
spend at most `delta` has at least one look receiving no more than the average
`delta/horizon`. -/
theorem finite_horizon_spending_has_look_at_most_average
    (delta : ℝ) (horizon : ℕ) (horizonPositive : 0 < horizon)
    (spending : Fin horizon → ℝ)
    (totalBound : (∑ index, spending index) ≤ delta) :
    ∃ index, spending index ≤ delta / (horizon : ℝ) := by
  by_contra noSmallLook
  push_neg at noSmallLook
  have univNonempty : (Finset.univ : Finset (Fin horizon)).Nonempty := by
    exact ⟨⟨0, horizonPositive⟩, Finset.mem_univ _⟩
  have strictSum :
      (∑ _index : Fin horizon, delta / (horizon : ℝ)) <
        ∑ index : Fin horizon, spending index := by
    exact Finset.sum_lt_sum_of_nonempty univNonempty
      (fun index _ => noSmallLook index)
  have constantTotal :
      (∑ _index : Fin horizon, delta / (horizon : ℝ)) = delta := by
    simp [Fintype.card_fin]
    have horizonCastNonzero : (horizon : ℝ) ≠ 0 := by
      exact_mod_cast (Nat.ne_of_gt horizonPositive)
    field_simp
  rw [constantTotal] at strictSum
  linarith

/-- Consequently, if every one of `horizon` looks is required to receive a
strictly larger allocation than the equal share, no global budget certificate
can exist.  Equal spending is maximin-optimal for the smallest per-look alpha
on a fixed horizon. -/
theorem no_finite_horizon_schedule_beats_equal_share_at_every_look
    (delta : ℝ) (horizon : ℕ) (horizonPositive : 0 < horizon)
    (spending : Fin horizon → ℝ)
    (everyLookBetter :
      ∀ index, delta / (horizon : ℝ) < spending index) :
    ¬ (∑ index, spending index) ≤ delta := by
  intro totalBound
  obtain ⟨index, small⟩ := finite_horizon_spending_has_look_at_most_average
    delta horizon horizonPositive spending totalBound
  exact (not_lt_of_ge small) (everyLookBetter index)

/-- End-to-end polynomial-spending bridge to the pooled,
dependence-corrected quota at a registered look. -/
theorem polynomial_spending_pooled_threshold_guarantees_look_budget
    (groupCount outcomeClassCount index : ℕ)
    (epsilon delta raw designEffect : ℝ)
    (groupCountPositive : 0 < groupCount)
    (outcomeClassCountPositive : 0 < outcomeClassCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (designEffectPositive : 0 < designEffect)
    (enoughRaw :
      designEffect * populationRequiredEffectiveObservations
          (pooledHypothesisCount groupCount outcomeClassCount)
          epsilon (polynomialAlphaSpending delta index) ≤ raw) :
    designEffectPopulationBudget
        (pooledHypothesisCount groupCount outcomeClassCount)
        raw designEffect epsilon ≤ polynomialAlphaSpending delta index := by
  exact pooled_designEffect_threshold_guarantees_population_budget
    groupCount outcomeClassCount epsilon
    (polynomialAlphaSpending delta index) raw designEffect
    groupCountPositive outcomeClassCountPositive epsilonPositive
    (polynomialAlphaSpending_positive delta index deltaPositive)
    designEffectPositive enoughRaw

end OCKIndividuationMSpaceComposition
