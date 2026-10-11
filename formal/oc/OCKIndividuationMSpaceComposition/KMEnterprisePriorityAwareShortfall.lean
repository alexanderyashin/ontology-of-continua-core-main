import OCKIndividuationMSpaceComposition.KMEnterpriseSignedInterventionDeviation

namespace OCKIndividuationMSpaceComposition

/-!
# Exact priority-aware execution-shortfall budgets

The strict signed margin is deliberately tie-break independent and can be
conservative by one count. This module derives the exact selected-coordinate
shortfall budget for the frozen enterprise priority. A budget certificate
checks every competitor and names one limiting competitor. It proves both
preservation at the budget and loss after one additional omitted signal.
-/

/-- Reduce only the selected score by a signed nonnegative shortfall. -/
def selectedShortfallProfile
    (profile : EnterpriseCarrierSignedProfile)
    (selected : EnterpriseCarrier) (shortfall : Int) :
    EnterpriseCarrierSignedProfile :=
  fun carrier =>
    if carrier = selected then profile carrier - shortfall else profile carrier

/-- Maximum shortfall allowed against one competitor. If the competitor has
earlier frozen priority, one additional count is reserved to avoid a losing
tie. -/
def priorityAwareShortfallAllowance
    (profile : EnterpriseCarrierSignedProfile)
    (selected other : EnterpriseCarrier) : Int :=
  profile selected - profile other -
    (if enterpriseCarrierPriority selected ≤ enterpriseCarrierPriority other
      then (0 : Int) else 1)

/-- Exact pairwise characterization of carrier preservation under a selected-
coordinate shortfall. -/
theorem selected_shortfall_dominant_iff_pairwise_allowance
    (profile : EnterpriseCarrierSignedProfile)
    (selected : EnterpriseCarrier) (shortfall : Int) :
    SignedOperationallyDominant
        (selectedShortfallProfile profile selected shortfall) selected ↔
      ∀ other, other ≠ selected →
        shortfall ≤ priorityAwareShortfallAllowance profile selected other := by
  constructor
  · intro dominant other different
    have certificate := dominant other
    simp only [selectedShortfallProfile, if_neg different, if_pos] at certificate
    by_cases priority :
        enterpriseCarrierPriority selected ≤ enterpriseCarrierPriority other
    · simp [priorityAwareShortfallAllowance, priority]
      omega
    · simp [priorityAwareShortfallAllowance, priority]
      omega
  · intro allowances other
    by_cases same : other = selected
    · subst other
      exact Or.inr ⟨rfl, Nat.le_refl _⟩
    have allowance := allowances other same
    simp only [selectedShortfallProfile, if_neg same, if_pos]
    by_cases priority :
        enterpriseCarrierPriority selected ≤ enterpriseCarrierPriority other
    · have countsLe : profile other ≤ profile selected - shortfall := by
        simp [priorityAwareShortfallAllowance, priority] at allowance
        omega
      obtain strict | equal := lt_or_eq_of_le countsLe
      · exact Or.inl strict
      · exact Or.inr ⟨equal, priority⟩
    · left
      simp [priorityAwareShortfallAllowance, priority] at allowance
      omega

/-- A checkable certificate that `budget` is the exact maximum: it is safe
against every competitor and attained by a named limiting competitor. -/
structure ExactPriorityAwareShortfallBudgetCertificate
    (profile : EnterpriseCarrierSignedProfile)
    (selected : EnterpriseCarrier) (budget : Int) where
  nonnegative : 0 ≤ budget
  safe : ∀ other, other ≠ selected →
    budget ≤ priorityAwareShortfallAllowance profile selected other
  limitingCompetitor : EnterpriseCarrier
  limitingDistinct : limitingCompetitor ≠ selected
  limitingExact : budget =
    priorityAwareShortfallAllowance profile selected limitingCompetitor

theorem exact_shortfall_budget_preserves_carrier
    (profile : EnterpriseCarrierSignedProfile)
    (selected : EnterpriseCarrier) (budget : Int)
    (certificate : ExactPriorityAwareShortfallBudgetCertificate
      profile selected budget) :
    SignedOperationallyDominant
      (selectedShortfallProfile profile selected budget) selected := by
  exact (selected_shortfall_dominant_iff_pairwise_allowance
    profile selected budget).2 certificate.safe

/-- Sharp no-go: one more omitted selected signal than the certified exact
budget necessarily changes or destroys the selected dominance certificate. -/
theorem one_beyond_exact_shortfall_budget_loses_carrier
    (profile : EnterpriseCarrierSignedProfile)
    (selected : EnterpriseCarrier) (budget : Int)
    (certificate : ExactPriorityAwareShortfallBudgetCertificate
      profile selected budget) :
    ¬ SignedOperationallyDominant
      (selectedShortfallProfile profile selected (budget + 1)) selected := by
  rw [selected_shortfall_dominant_iff_pairwise_allowance]
  intro safe
  have beyond := safe certificate.limitingCompetitor certificate.limitingDistinct
  rw [← certificate.limitingExact] at beyond
  omega

/-- Any smaller nonnegative shortfall is also safe. -/
theorem shortfall_below_exact_budget_preserves_carrier
    (profile : EnterpriseCarrierSignedProfile)
    (selected : EnterpriseCarrier) (budget shortfall : Int)
    (certificate : ExactPriorityAwareShortfallBudgetCertificate
      profile selected budget)
    (below : shortfall ≤ budget) :
    SignedOperationallyDominant
      (selectedShortfallProfile profile selected shortfall) selected := by
  rw [selected_shortfall_dominant_iff_pairwise_allowance]
  intro other different
  exact le_trans below (certificate.safe other different)

/-!
## Four frozen prospective profiles
-/

def plumbingPlanSignedProfile : EnterpriseCarrierSignedProfile
  | .capabilityRealization => 4
  | .controlDecision => 1
  | .deploymentInstance => 1
  | .scientificClaim => 1
  | _ => 0

def sciencePlanSignedProfile : EnterpriseCarrierSignedProfile
  | .capabilityRealization => 2
  | .scientificClaim => 12
  | _ => 0

def governancePlanSignedProfile : EnterpriseCarrierSignedProfile
  | .capabilityRealization => 4
  | .controlDecision => 3
  | .releaseSurface => 1
  | .scientificClaim => 1
  | .workItemRun => 3
  | _ => 0

def closeoutPlanSignedProfile : EnterpriseCarrierSignedProfile
  | .capabilityRealization => 6
  | .scientificClaim => 21
  | .workItemRun => 1
  | _ => 0

def plumbing_exact_shortfall_budget_three :
    ExactPriorityAwareShortfallBudgetCertificate plumbingPlanSignedProfile
      .capabilityRealization 3 := by
  refine ⟨by norm_num, ?_, .controlDecision, by decide, by norm_num
    [priorityAwareShortfallAllowance, plumbingPlanSignedProfile,
      enterpriseCarrierPriority]⟩
  intro other different
  cases other <;>
    norm_num [priorityAwareShortfallAllowance, plumbingPlanSignedProfile,
      enterpriseCarrierPriority] at *

def science_exact_shortfall_budget_nine :
    ExactPriorityAwareShortfallBudgetCertificate sciencePlanSignedProfile
      .scientificClaim 9 := by
  refine ⟨by norm_num, ?_, .capabilityRealization, by decide, by norm_num
    [priorityAwareShortfallAllowance, sciencePlanSignedProfile,
      enterpriseCarrierPriority]⟩
  intro other different
  cases other <;>
    norm_num [priorityAwareShortfallAllowance, sciencePlanSignedProfile,
      enterpriseCarrierPriority] at *

def governance_exact_shortfall_budget_one :
    ExactPriorityAwareShortfallBudgetCertificate governancePlanSignedProfile
      .capabilityRealization 1 := by
  refine ⟨by norm_num, ?_, .controlDecision, by decide, by norm_num
    [priorityAwareShortfallAllowance, governancePlanSignedProfile,
      enterpriseCarrierPriority]⟩
  intro other different
  cases other <;>
    norm_num [priorityAwareShortfallAllowance, governancePlanSignedProfile,
      enterpriseCarrierPriority] at *

def closeout_exact_shortfall_budget_fourteen :
    ExactPriorityAwareShortfallBudgetCertificate closeoutPlanSignedProfile
      .scientificClaim 14 := by
  refine ⟨by norm_num, ?_, .capabilityRealization, by decide, by norm_num
    [priorityAwareShortfallAllowance, closeoutPlanSignedProfile,
      enterpriseCarrierPriority]⟩
  intro other different
  cases other <;>
    norm_num [priorityAwareShortfallAllowance, closeoutPlanSignedProfile,
      enterpriseCarrierPriority] at *

theorem four_frozen_exact_budgets_preserve_and_next_count_loses :
    SignedOperationallyDominant
        (selectedShortfallProfile plumbingPlanSignedProfile
          .capabilityRealization 3) .capabilityRealization ∧
      ¬ SignedOperationallyDominant
        (selectedShortfallProfile plumbingPlanSignedProfile
          .capabilityRealization 4) .capabilityRealization ∧
      SignedOperationallyDominant
        (selectedShortfallProfile sciencePlanSignedProfile
          .scientificClaim 9) .scientificClaim ∧
      ¬ SignedOperationallyDominant
        (selectedShortfallProfile sciencePlanSignedProfile
          .scientificClaim 10) .scientificClaim ∧
      SignedOperationallyDominant
        (selectedShortfallProfile governancePlanSignedProfile
          .capabilityRealization 1) .capabilityRealization ∧
      ¬ SignedOperationallyDominant
        (selectedShortfallProfile governancePlanSignedProfile
          .capabilityRealization 2) .capabilityRealization ∧
      SignedOperationallyDominant
        (selectedShortfallProfile closeoutPlanSignedProfile
          .scientificClaim 14) .scientificClaim ∧
      ¬ SignedOperationallyDominant
        (selectedShortfallProfile closeoutPlanSignedProfile
          .scientificClaim 15) .scientificClaim := by
  exact ⟨exact_shortfall_budget_preserves_carrier _ _ _
      plumbing_exact_shortfall_budget_three,
    one_beyond_exact_shortfall_budget_loses_carrier _ _ _
      plumbing_exact_shortfall_budget_three,
    exact_shortfall_budget_preserves_carrier _ _ _
      science_exact_shortfall_budget_nine,
    one_beyond_exact_shortfall_budget_loses_carrier _ _ _
      science_exact_shortfall_budget_nine,
    exact_shortfall_budget_preserves_carrier _ _ _
      governance_exact_shortfall_budget_one,
    one_beyond_exact_shortfall_budget_loses_carrier _ _ _
      governance_exact_shortfall_budget_one,
    exact_shortfall_budget_preserves_carrier _ _ _
      closeout_exact_shortfall_budget_fourteen,
    one_beyond_exact_shortfall_budget_loses_carrier _ _ _
      closeout_exact_shortfall_budget_fourteen⟩

end OCKIndividuationMSpaceComposition
