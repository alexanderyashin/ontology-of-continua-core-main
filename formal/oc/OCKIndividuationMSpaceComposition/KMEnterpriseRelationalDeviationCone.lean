import OCKIndividuationMSpaceComposition.KMEnterpriseExecutionRegimeIdentification
import Mathlib.Tactic.Linarith

namespace OCKIndividuationMSpaceComposition

/-!
# Relational deviation cones

Coordinate boxes are unnecessarily weak when adaptive additions are coupled.
For the registered K7 research surface, every added path contributes to the
scientific carrier and may contribute to some other carriers.  The relevant
uncertainty set is therefore an unbounded relational cone, not a finite box.
-/

def DeviationConePreservesSelected
    (deviation : EnterpriseCarrierSignedProfile)
    (selected : EnterpriseCarrier) : Prop :=
  ∀ other, deviation other ≤ deviation selected

def StrictPlannedSignedMargin
    (planned : EnterpriseCarrierSignedProfile)
    (selected : EnterpriseCarrier) : Prop :=
  ∀ other, other ≠ selected → planned other < planned selected

def addSignedProfiles
    (planned deviation : EnterpriseCarrierSignedProfile) :
    EnterpriseCarrierSignedProfile :=
  fun carrier => planned carrier + deviation carrier

/-- Positive theorem: an unbounded deviation cone preserves the selected
carrier whenever relative additions cannot erode its strict planned margin. -/
theorem relational_deviation_cone_preserves_selected_carrier
    (planned deviation : EnterpriseCarrierSignedProfile)
    (selected : EnterpriseCarrier)
    (baseMargin : StrictPlannedSignedMargin planned selected)
    (cone : DeviationConePreservesSelected deviation selected) :
    SignedOperationallyDominant
      (addSignedProfiles planned deviation) selected := by
  intro other
  by_cases same : other = selected
  · subst other
    exact Or.inr ⟨rfl, Nat.le_refl _⟩
  · left
    have plannedStrict := baseMargin other same
    have deviationLe := cone other
    simp only [addSignedProfiles]
    linarith

def competitorOverturnDeviation
    (planned : EnterpriseCarrierSignedProfile)
    (selected competitor : EnterpriseCarrier) :
    EnterpriseCarrierSignedProfile :=
  fun carrier =>
    if carrier = competitor then
      planned selected - planned competitor + 1
    else 0

/-- Sharp no-go: without a relational restriction (or finite upper bound), any
finite planned profile can be overturned by an admissible competitor addition. -/
theorem arbitrary_unbounded_deviation_can_overturn_selected
    (planned : EnterpriseCarrierSignedProfile)
    (selected competitor : EnterpriseCarrier)
    (different : competitor ≠ selected) :
    ¬ SignedOperationallyDominant
      (addSignedProfiles planned
        (competitorOverturnDeviation planned selected competitor)) selected := by
  intro dominant
  have competitorHigher :
      addSignedProfiles planned
          (competitorOverturnDeviation planned selected competitor) selected <
        addSignedProfiles planned
          (competitorOverturnDeviation planned selected competitor) competitor := by
    simp [addSignedProfiles, competitorOverturnDeviation, Ne.symm different]
    linarith
  obtain selectedHigher | ⟨equalScores, _⟩ := dominant competitor
  · exact (not_lt_of_ge (le_of_lt competitorHigher)) selectedHigher
  · exact (ne_of_gt competitorHigher) equalScores

def openPlan06SignedProfile : EnterpriseCarrierSignedProfile
  | .assetRevision => 0
  | .capabilityRealization => 2
  | .commitmentRisk => 0
  | .controlDecision => 0
  | .deploymentInstance => 0
  | .releaseSurface => 0
  | .scientificClaim => 18
  | .workItemRun => 6

theorem openPlan06_has_strict_scientific_margin :
    StrictPlannedSignedMargin openPlan06SignedProfile .scientificClaim := by
  intro other different
  cases other <;> simp [openPlan06SignedProfile] at different ⊢

/-- Frozen occurrence-06 prediction: every deviation in the registered
unbounded relational cone preserves `scientificClaim` as carrier. -/
theorem openPlan06_relational_cone_forces_scientific_claim
    (deviation : EnterpriseCarrierSignedProfile)
    (cone : DeviationConePreservesSelected deviation .scientificClaim) :
    SignedOperationallyDominant
      (addSignedProfiles openPlan06SignedProfile deviation)
      .scientificClaim :=
  relational_deviation_cone_preserves_selected_carrier
    openPlan06SignedProfile deviation .scientificClaim
    openPlan06_has_strict_scientific_margin cone

end OCKIndividuationMSpaceComposition
