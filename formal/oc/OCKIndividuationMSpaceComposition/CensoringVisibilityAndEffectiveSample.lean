import OCKIndividuationMSpaceComposition.OddsHazardInteractionCompetition
import OCKIndividuationMSpaceComposition.DependentInformationBudget

namespace OCKIndividuationMSpaceComposition

/-!
# Censoring visibility and dependence-corrected effective sample size

The factorization below is a declared independent-censoring observation
adapter.  It turns a latent first-event mass into an observed event mass by
multiplying by the probability of remaining uncensored through that time.  The
result exposes the exact signal loss instead of treating censoring as plumbing.
-/

/--
Observed event mass at `time` under the declared independent-censoring channel.
The event is visible only when no censoring barrier occurs through `time`.
-/
def independentCensoredEventMass
    (eventHazard censorHazard : ℕ → ℚ) (time : ℕ) : ℚ :=
  firstBarrierMass eventHazard time *
    barrierSurvival censorHazard (time + 1)

theorem independentCensoredEventMass_factorization
    (eventHazard censorHazard : ℕ → ℚ) (time : ℕ) :
    independentCensoredEventMass eventHazard censorHazard time =
      firstBarrierMass eventHazard time *
        barrierSurvival censorHazard (time + 1) := rfl

/-- Exact attenuation of a latent event-mass contrast by censoring visibility. -/
theorem censored_event_mass_gap_exact
    (firstEventHazard secondEventHazard censorHazard : ℕ → ℚ)
    (validCensor : ValidBarrierHazard censorHazard) (time : ℕ) :
    |independentCensoredEventMass firstEventHazard censorHazard time -
        independentCensoredEventMass secondEventHazard censorHazard time| =
      barrierSurvival censorHazard (time + 1) *
        |firstBarrierMass firstEventHazard time -
          firstBarrierMass secondEventHazard time| := by
  have visibilityNonnegative :
      0 ≤ barrierSurvival censorHazard (time + 1) :=
    (barrierSurvival_bounds censorHazard validCensor (time + 1)).1
  unfold independentCensoredEventMass
  rw [show firstBarrierMass firstEventHazard time *
          barrierSurvival censorHazard (time + 1) -
        firstBarrierMass secondEventHazard time *
          barrierSurvival censorHazard (time + 1) =
        (firstBarrierMass firstEventHazard time -
          firstBarrierMass secondEventHazard time) *
            barrierSurvival censorHazard (time + 1) by ring,
    abs_mul, abs_of_nonneg visibilityNonnegative]
  ring

/--
Positive theorem: a visible latent contrast remains distinguishable exactly
when the visibility-attenuated gap clears the universal `2 * epsilon` boundary.
-/
theorem censored_event_models_separated_at_visible_time
    (firstEventHazard secondEventHazard censorHazard : ℕ → ℚ)
    (validCensor : ValidBarrierHazard censorHazard)
    (time : ℕ) (epsilon : ℚ)
    (visibleGap :
      2 * epsilon < barrierSurvival censorHazard (time + 1) *
        |firstBarrierMass firstEventHazard time -
          firstBarrierMass secondEventHazard time|) :
    ModelsSeparatedBeyondError
      (fun eventHazard : ℕ → ℚ => fun observedTime : ℕ =>
        independentCensoredEventMass eventHazard censorHazard observedTime)
      firstEventHazard secondEventHazard epsilon := by
  refine ⟨time, ?_⟩
  rw [censored_event_mass_gap_exact
    firstEventHazard secondEventHazard censorHazard validCensor time]
  exact visibleGap

/-- Positive visibility makes the latent first-event mass algebraically recoverable. -/
theorem latent_event_mass_recovered_from_positive_visibility
    (eventHazard censorHazard : ℕ → ℚ) (time : ℕ)
    (visible : 0 < barrierSurvival censorHazard (time + 1)) :
    independentCensoredEventMass eventHazard censorHazard time /
        barrierSurvival censorHazard (time + 1) =
      firstBarrierMass eventHazard time := by
  unfold independentCensoredEventMass
  exact mul_div_cancel_right₀ _ visible.ne'

/-- Zero visibility erases every event model at that registered time. -/
theorem zero_visibility_erases_event_model_difference
    (firstEventHazard secondEventHazard censorHazard : ℕ → ℚ) (time : ℕ)
    (invisible : barrierSurvival censorHazard (time + 1) = 0) :
    independentCensoredEventMass firstEventHazard censorHazard time =
      independentCensoredEventMass secondEventHazard censorHazard time := by
  simp [independentCensoredEventMass, invisible]

/--
Constructive no-go: if every registered time is fully censored, the zero
observation is compatible with every pair of latent event models, even at zero
error.  More latent samples cannot repair an observation channel with no
visibility.
-/
theorem complete_censoring_admits_common_observation
    (firstEventHazard secondEventHazard censorHazard : ℕ → ℚ)
    (complete : ∀ time, barrierSurvival censorHazard (time + 1) = 0)
    (epsilon : ℚ) (epsilonNonnegative : 0 ≤ epsilon) :
    ∃ observed : ℕ → ℚ,
      ModelWithinLInfError
          (fun eventHazard : ℕ → ℚ => fun time =>
            independentCensoredEventMass eventHazard censorHazard time)
          firstEventHazard observed epsilon ∧
      ModelWithinLInfError
          (fun eventHazard : ℕ → ℚ => fun time =>
            independentCensoredEventMass eventHazard censorHazard time)
          secondEventHazard observed epsilon := by
  refine ⟨fun _ => 0, ?_, ?_⟩ <;> intro time <;>
    simp [independentCensoredEventMass, complete time, epsilonNonnegative]

/-! ## Visibility combined with exchangeable dependence -/

/--
Independent-equivalent visible observations when only a fraction `visibility`
of the exchangeable sample reaches the observation channel.
-/
noncomputable def censoredExchangeableEffectiveObservations
    (raw visibility correlation : ℝ) : ℝ :=
  visibility * exchangeableEffectiveObservations raw correlation

/-- Censoring and nonnegative dependence cannot increase usable sample size. -/
theorem censoredExchangeableEffectiveObservations_le_raw
    (raw visibility correlation : ℝ)
    (rawAtLeastOne : 1 ≤ raw)
    (visibilityAtMostOne : visibility ≤ 1)
    (correlationNonnegative : 0 ≤ correlation) :
    censoredExchangeableEffectiveObservations raw visibility correlation ≤ raw := by
  have denominatorPositive : 0 < 1 + (raw - 1) * correlation := by
    have offsetNonnegative : 0 ≤ raw - 1 := sub_nonneg.mpr rawAtLeastOne
    positivity
  have effectiveNonnegative :
      0 ≤ exchangeableEffectiveObservations raw correlation := by
    rw [exchangeableEffectiveObservations]
    exact div_nonneg (zero_le_one.trans rawAtLeastOne)
      (le_of_lt denominatorPositive)
  calc
    censoredExchangeableEffectiveObservations raw visibility correlation =
        visibility * exchangeableEffectiveObservations raw correlation := rfl
    _ ≤ 1 * exchangeableEffectiveObservations raw correlation :=
      mul_le_mul_of_nonneg_right visibilityAtMostOne effectiveNonnegative
    _ = exchangeableEffectiveObservations raw correlation := by ring
    _ ≤ raw := exchangeableEffectiveObservations_le_raw raw correlation
      rawAtLeastOne correlationNonnegative

/-- Complete censoring yields zero effective observations for every raw count. -/
theorem zero_visibility_has_zero_effective_observations
    (raw correlation : ℝ) :
    censoredExchangeableEffectiveObservations raw 0 correlation = 0 := by
  simp [censoredExchangeableEffectiveObservations]

/--
Persistent positive correlation imposes the visibility-scaled ceiling
`visibility / correlation` on one exchangeable block.
-/
theorem censored_exchangeable_effective_ceiling
    (raw visibility correlation : ℝ)
    (rawPositive : 0 < raw)
    (visibilityPositive : 0 < visibility)
    (correlationPositive : 0 < correlation)
    (correlationBelowOne : correlation < 1) :
    censoredExchangeableEffectiveObservations raw visibility correlation <
      visibility / correlation := by
  have baseCeiling := exchangeableEffectiveObservations_lt_inverseCorrelation
    raw correlation rawPositive correlationPositive correlationBelowOne
  rw [censoredExchangeableEffectiveObservations]
  have scaled := mul_lt_mul_of_pos_left baseCeiling visibilityPositive
  calc
    visibility * exchangeableEffectiveObservations raw correlation <
        visibility * (1 / correlation) := scaled
    _ = visibility / correlation := by ring

/--
Exact raw-sample design law after both visibility loss and exchangeable
dependence.  The requested visible target is first divided by visibility, then
the pre-existing dependence correction is applied.
-/
theorem censored_exchangeable_raw_threshold_sufficient
    (raw visibility correlation target : ℝ)
    (visibilityPositive : 0 < visibility)
    (targetPositive : 0 < target)
    (correlationNonnegative : 0 ≤ correlation)
    (correlationBelowOne : correlation < 1)
    (belowCeiling : (target / visibility) * correlation < 1)
    (enoughRaw :
      (target / visibility) * (1 - correlation) /
          (1 - (target / visibility) * correlation) ≤ raw) :
    target ≤ censoredExchangeableEffectiveObservations raw visibility correlation := by
  have scaledTargetPositive : 0 < target / visibility :=
    div_pos targetPositive visibilityPositive
  have base := exchangeable_raw_threshold_sufficient raw correlation
    (target / visibility) scaledTargetPositive correlationNonnegative
    correlationBelowOne belowCeiling enoughRaw
  rw [censoredExchangeableEffectiveObservations]
  have scaled := mul_le_mul_of_nonneg_left base (le_of_lt visibilityPositive)
  calc
    target = visibility * (target / visibility) := by field_simp
    _ ≤ visibility * exchangeableEffectiveObservations raw correlation := scaled

end OCKIndividuationMSpaceComposition
