import OCKIndividuationMSpaceComposition.NestedObservationAcquisition

namespace OCKIndividuationMSpaceComposition

/-!
# Forecast-origin decision policy

Nested information can reduce optimal predictive risk, but an operational
policy must also type schedule availability, deadlines, acquisition cost and
opportunity cost.  This module gives the minimum decision adapter needed by the
OC observation-acquisition curve.  It also gives sharp certification and
transport boundaries: an estimated preference is safe only with a separated
loss interval, and a source ordering transports only when its margin pays the
declared loss-transport error.
-/

/-- One candidate forecast origin together with the quantities needed to turn
predictive quality into an operational decision. -/
structure ForecastOriginDecision where
  origin : ℕ
  predictiveRisk : ℝ
  acquisitionCost : ℝ
  opportunityCost : ℝ
  available : Prop

namespace ForecastOriginDecision

/-- Total decision loss.  Every term must be expressed in the same declared
decision-loss units before this sum is meaningful. -/
def totalLoss (decision : ForecastOriginDecision) : ℝ :=
  decision.predictiveRisk + decision.acquisitionCost + decision.opportunityCost

/-- Availability and a hard decision deadline are separate from low loss. -/
def Admissible (decision : ForecastOriginDecision) (deadline : ℕ) : Prop :=
  decision.available ∧ decision.origin ≤ deadline

/-- A later decision is operationally preferred only when it is admissible and
does not exceed the comparison decision's total loss. -/
def Preferred
    (later earlier : ForecastOriginDecision) (deadline : ℕ) : Prop :=
  later.Admissible deadline ∧ later.totalLoss ≤ earlier.totalLoss

/-- Exact value-of-information accounting: a lower-risk origin wins precisely
when its predictive-risk reduction covers its incremental acquisition and
opportunity costs. -/
theorem totalLoss_preference_iff_value_covers_incremental_cost
    (later earlier : ForecastOriginDecision) :
    later.totalLoss ≤ earlier.totalLoss ↔
      earlier.predictiveRisk - later.predictiveRisk ≥
        (later.acquisitionCost + later.opportunityCost) -
          (earlier.acquisitionCost + earlier.opportunityCost) := by
  simp only [totalLoss]
  constructor <;> intro h <;> linarith

/-- Positive operational rule: a schedule-bound origin is preferred when it
is available by the deadline and its information value covers incremental
cost. -/
theorem preferred_of_available_value_covers_incremental_cost
    (later earlier : ForecastOriginDecision) (deadline : ℕ)
    (available : later.available) (withinDeadline : later.origin ≤ deadline)
    (valueCoversCost :
      earlier.predictiveRisk - later.predictiveRisk ≥
        (later.acquisitionCost + later.opportunityCost) -
          (earlier.acquisitionCost + earlier.opportunityCost)) :
    later.Preferred earlier deadline := by
  exact ⟨⟨available, withinDeadline⟩,
    (totalLoss_preference_iff_value_covers_incremental_cost later earlier).2
      valueCoversCost⟩

/-- No-go: lower total loss cannot license a forecast origin that is absent
from the real schedule or misses the deadline. -/
theorem lower_loss_without_schedule_availability_is_not_operational :
    ∃ earlier later : ForecastOriginDecision, ∃ deadline : ℕ,
      later.totalLoss < earlier.totalLoss ∧
      ¬ later.Preferred earlier deadline := by
  let earlier : ForecastOriginDecision :=
    { origin := 0, predictiveRisk := 1, acquisitionCost := 0,
      opportunityCost := 0, available := True }
  let later : ForecastOriginDecision :=
    { origin := 1, predictiveRisk := 0, acquisitionCost := 0,
      opportunityCost := 0, available := False }
  refine ⟨earlier, later, 1, ?_, ?_⟩
  · norm_num [totalLoss, earlier, later]
  · simp [Preferred, Admissible, later]

/-- Interval-separation certificate.  If the later upper loss bound is already
below the earlier lower loss bound, every compatible realization prefers the
later origin. -/
theorem certified_preference_of_separated_loss_bounds
    (laterTrue earlierTrue laterUpper earlierLower : ℝ)
    (laterSound : laterTrue ≤ laterUpper)
    (earlierSound : earlierLower ≤ earlierTrue)
    (separated : laterUpper ≤ earlierLower) :
    laterTrue ≤ earlierTrue :=
  laterSound.trans (separated.trans earlierSound)

/-- No-go: overlapping loss intervals can contain worlds with opposite policy
orderings, so point estimates alone do not identify a unique decision. -/
theorem overlapping_loss_bounds_do_not_identify_preference :
    ∃ lower upper laterA earlierA laterB earlierB : ℝ,
      lower ≤ laterA ∧ laterA ≤ upper ∧
      lower ≤ earlierA ∧ earlierA ≤ upper ∧
      laterA < earlierA ∧
      lower ≤ laterB ∧ laterB ≤ upper ∧
      lower ≤ earlierB ∧ earlierB ≤ upper ∧
      earlierB < laterB := by
  exact ⟨0, 1, 0, 1, 1, 0, by norm_num⟩

/-- A strict source policy transports under uniform total-loss error when the
source margin is larger than the two-sided transport bill `2ε`. -/
theorem strict_preference_transports_under_uniform_loss_error
    (sourceLater sourceEarlier targetLater targetEarlier ε : ℝ)
    (laterError : |targetLater - sourceLater| ≤ ε)
    (earlierError : |targetEarlier - sourceEarlier| ≤ ε)
    (sourceMargin : sourceLater + 2 * ε < sourceEarlier) :
    targetLater < targetEarlier := by
  have laterUpper : targetLater ≤ sourceLater + ε := by
    have := (abs_le.mp laterError).2
    linarith
  have earlierLower : sourceEarlier - ε ≤ targetEarlier := by
    have := (abs_le.mp earlierError).1
    linarith
  linarith

/-- Sharp obstruction for the transport rule: with a source margin below the
two-sided error bill, two target losses within the same declared error radius
may reverse the source preference. -/
theorem source_preference_without_transport_margin_can_reverse :
    ∃ sourceLater sourceEarlier targetLater targetEarlier ε : ℝ,
      |targetLater - sourceLater| ≤ ε ∧
      |targetEarlier - sourceEarlier| ≤ ε ∧
      sourceLater < sourceEarlier ∧
      targetEarlier < targetLater := by
  exact ⟨0, 1, 1, 0, 1, by norm_num⟩

end ForecastOriginDecision

/-- A finite schedule is globally auditable through a certificate: one
admissible origin and its pairwise loss dominance over every other admissible
origin. -/
structure FiniteForecastPolicyCertificate
    (Origin : Type) [Fintype Origin]
    (admissible : Origin → Prop) (loss : Origin → ℝ) where
  chosen : Origin
  chosenAdmissible : admissible chosen
  dominates : ∀ other, admissible other → loss chosen ≤ loss other

namespace FiniteForecastPolicyCertificate

/-- The finite certificate directly entails global optimality on the declared
admissible schedule. -/
theorem globally_optimal
    {Origin : Type} [Fintype Origin]
    {admissible : Origin → Prop} {loss : Origin → ℝ}
    (certificate : FiniteForecastPolicyCertificate Origin admissible loss)
    (other : Origin) (otherAdmissible : admissible other) :
    loss certificate.chosen ≤ loss other :=
  certificate.dominates other otherAdmissible

/-- If no origin is operationally admissible, no finite optimal-policy
certificate exists; abstention or schedule acquisition is compulsory. -/
theorem no_certificate_without_admissible_origin
    {Origin : Type} [Fintype Origin]
    (admissible : Origin → Prop) (loss : Origin → ℝ)
    (noneAdmissible : ∀ origin, ¬ admissible origin) :
    ¬ Nonempty (FiniteForecastPolicyCertificate Origin admissible loss) := by
  rintro ⟨certificate⟩
  exact noneAdmissible certificate.chosen certificate.chosenAdmissible

/-- For a finite schedule with decidable admissibility and a computably ordered
loss representation (for example exact rationals), checking a declared origin
is executable.  Exact real comparison is intentionally not smuggled in as a
computable operation. -/
def finite_declared_policyValidation
    {Origin Cost : Type} [Fintype Origin] [LinearOrder Cost]
    (admissible : Origin → Prop) [DecidablePred admissible]
    [DecidableRel (fun first second : Cost => first ≤ second)]
    (loss : Origin → Cost) (chosen : Origin) :
    Decidable (admissible chosen ∧
      ∀ other, admissible other → loss chosen ≤ loss other) := by
  infer_instance

end FiniteForecastPolicyCertificate

end OCKIndividuationMSpaceComposition
