import OCKIndividuationMSpaceComposition.KMEnterpriseInterventionCountFlow

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe uPath uLiftCarrier uLiftCandidate uRepairCandidate

/-!
# Signed execution deviations around a declared intervention

The nonnegative residual model is sound only when every declared contribution
is realized and uncertainty consists of extra evidence. Real execution may
also omit planned evidence. Signed deviations represent both shortfall and
addition while the actual extracted carrier profile remains Nat-valued.
-/

abbrev EnterpriseCarrierSignedProfile := EnterpriseCarrier → Int

def natCarrierProfileToSigned
    (profile : EnterpriseCarrierCountProfile) : EnterpriseCarrierSignedProfile :=
  fun carrier => Int.ofNat (profile carrier)

structure CarrierSignedDeviationEnvelope where
  lower : EnterpriseCarrierSignedProfile
  upper : EnterpriseCarrierSignedProfile
  valid : ∀ carrier, lower carrier ≤ upper carrier

def SignedProfileWithin (envelope : CarrierSignedDeviationEnvelope)
    (profile : EnterpriseCarrierSignedProfile) : Prop :=
  ∀ carrier,
    envelope.lower carrier ≤ profile carrier ∧
      profile carrier ≤ envelope.upper carrier

def plannedCarrierSignedProfile
    (intervention : DeclaredCarrierIntervention) (horizon : Nat) :
    EnterpriseCarrierSignedProfile :=
  natCarrierProfileToSigned (intervention.cumulative horizon)

def signedActionCarrierEnvelope
    (intervention : DeclaredCarrierIntervention) (horizon : Nat)
    (deviation : CarrierSignedDeviationEnvelope) :
    CarrierSignedDeviationEnvelope where
  lower carrier := plannedCarrierSignedProfile intervention horizon carrier +
    deviation.lower carrier
  upper carrier := plannedCarrierSignedProfile intervention horizon carrier +
    deviation.upper carrier
  valid carrier := Int.add_le_add_left (deviation.valid carrier) _

def SignedOperationallyDominant
    (profile : EnterpriseCarrierSignedProfile)
    (carrier : EnterpriseCarrier) : Prop :=
  ∀ other,
    profile other < profile carrier ∨
      (profile other = profile carrier ∧
        enterpriseCarrierPriority carrier ≤ enterpriseCarrierPriority other)

theorem signed_dominance_iff_nat_dominance
    (profile : EnterpriseCarrierCountProfile) (carrier : EnterpriseCarrier) :
    SignedOperationallyDominant (natCarrierProfileToSigned profile) carrier ↔
      OperationallyDominant profile carrier := by
  constructor
  · intro dominant other
    obtain strict | ⟨equal, priority⟩ := dominant other
    · left
      simpa [natCarrierProfileToSigned] using strict
    · right
      constructor
      · simpa [natCarrierProfileToSigned] using equal
      · exact priority
  · intro dominant other
    obtain strict | ⟨equal, priority⟩ := dominant other
    · left
      simpa [natCarrierProfileToSigned] using strict
    · right
      constructor
      · simpa [natCarrierProfileToSigned] using equal
      · exact priority

def signedAdversarialCarrierProfile
    (envelope : CarrierSignedDeviationEnvelope)
    (selected : EnterpriseCarrier) : EnterpriseCarrierSignedProfile :=
  fun carrier =>
    if carrier = selected then envelope.lower selected else envelope.upper carrier

theorem signedAdversarialCarrierProfile_within
    (envelope : CarrierSignedDeviationEnvelope)
    (selected : EnterpriseCarrier) :
    SignedProfileWithin envelope
      (signedAdversarialCarrierProfile envelope selected) := by
  intro carrier
  by_cases same : carrier = selected
  · subst carrier
    simp [signedAdversarialCarrierProfile, envelope.valid]
  · simp [signedAdversarialCarrierProfile, same, envelope.valid]

def SignedEnvelopeForcesCarrier
    (envelope : CarrierSignedDeviationEnvelope)
    (selected : EnterpriseCarrier) : Prop :=
  ∀ profile, SignedProfileWithin envelope profile →
    SignedOperationallyDominant profile selected

theorem signed_adversarial_dominance_implies_all_profiles
    (envelope : CarrierSignedDeviationEnvelope)
    (selected : EnterpriseCarrier)
    (cornerDominant : SignedOperationallyDominant
      (signedAdversarialCarrierProfile envelope selected) selected) :
    SignedEnvelopeForcesCarrier envelope selected := by
  intro profile within other
  by_cases same : other = selected
  · subst other
    exact Or.inr ⟨rfl, Nat.le_refl _⟩
  obtain cornerStrict | ⟨cornerEqual, priority⟩ := cornerDominant other
  · left
    have otherUpper := (within other).2
    have selectedLower := (within selected).1
    have cornerStrict' : envelope.upper other < envelope.lower selected := by
      simpa [signedAdversarialCarrierProfile, same] using cornerStrict
    exact lt_of_le_of_lt otherUpper (lt_of_lt_of_le cornerStrict' selectedLower)
  · have otherUpper := (within other).2
    have selectedLower := (within selected).1
    have cornerEqual' : envelope.upper other = envelope.lower selected := by
      simpa [signedAdversarialCarrierProfile, same] using cornerEqual
    have countsLe : profile other ≤ profile selected := by
      calc
        profile other ≤ envelope.upper other := otherUpper
        _ = envelope.lower selected := cornerEqual'
        _ ≤ profile selected := selectedLower
    obtain countsStrict | countsEqual := lt_or_eq_of_le countsLe
    · exact Or.inl countsStrict
    · exact Or.inr ⟨countsEqual, priority⟩

theorem signed_envelope_forces_iff_adversarial_dominant
    (envelope : CarrierSignedDeviationEnvelope)
    (selected : EnterpriseCarrier) :
    SignedEnvelopeForcesCarrier envelope selected ↔
      SignedOperationallyDominant
        (signedAdversarialCarrierProfile envelope selected) selected := by
  constructor
  · intro forces
    exact forces _ (signedAdversarialCarrierProfile_within envelope selected)
  · exact signed_adversarial_dominance_implies_all_profiles envelope selected

/-- Exact signed forcing rule. Planned evidence plus the worst permitted
selected shortfall must still exceed every competitor's worst addition. -/
def StrictSignedInterventionMargin
    (intervention : DeclaredCarrierIntervention) (horizon : Nat)
    (deviation : CarrierSignedDeviationEnvelope)
    (selected : EnterpriseCarrier) : Prop :=
  ∀ other, other ≠ selected →
    plannedCarrierSignedProfile intervention horizon other +
        deviation.upper other <
      plannedCarrierSignedProfile intervention horizon selected +
        deviation.lower selected

theorem strict_signed_intervention_margin_forces_carrier
    (intervention : DeclaredCarrierIntervention) (horizon : Nat)
    (deviation : CarrierSignedDeviationEnvelope)
    (selected : EnterpriseCarrier)
    (margin : StrictSignedInterventionMargin intervention horizon deviation selected) :
    SignedEnvelopeForcesCarrier
      (signedActionCarrierEnvelope intervention horizon deviation) selected := by
  apply (signed_envelope_forces_iff_adversarial_dominant _ _).mpr
  intro other
  by_cases same : other = selected
  · subst other
    exact Or.inr ⟨rfl, Nat.le_refl _⟩
  · left
    simpa [signedAdversarialCarrierProfile, signedActionCarrierEnvelope, same]
      using margin other same

theorem failed_signed_intervention_envelope_has_counterprofile
    (intervention : DeclaredCarrierIntervention) (horizon : Nat)
    (deviation : CarrierSignedDeviationEnvelope)
    (selected : EnterpriseCarrier)
    (failure : ¬ SignedOperationallyDominant
      (signedAdversarialCarrierProfile
        (signedActionCarrierEnvelope intervention horizon deviation) selected)
      selected) :
    ∃ profile,
      SignedProfileWithin
        (signedActionCarrierEnvelope intervention horizon deviation) profile ∧
      ¬ SignedOperationallyDominant profile selected := by
  exact ⟨signedAdversarialCarrierProfile
      (signedActionCarrierEnvelope intervention horizon deviation) selected,
    signedAdversarialCarrierProfile_within _ _, failure⟩

/-- Executable correspondence: the signed planned-plus-deviation score is
exactly the Nat-valued profile produced by the extractor. -/
structure SignedActionExecution
    (intervention : DeclaredCarrierIntervention) (horizon : Nat)
    (deviationEnvelope : CarrierSignedDeviationEnvelope) where
  actual : EnterpriseCarrierCountProfile
  deviation : EnterpriseCarrierSignedProfile
  deviationWithin : SignedProfileWithin deviationEnvelope deviation
  exact : ∀ carrier,
    natCarrierProfileToSigned actual carrier =
      plannedCarrierSignedProfile intervention horizon carrier + deviation carrier

theorem SignedActionExecution.actual_within_total_envelope
    (intervention : DeclaredCarrierIntervention) (horizon : Nat)
    (deviationEnvelope : CarrierSignedDeviationEnvelope)
    (execution : SignedActionExecution intervention horizon deviationEnvelope) :
    SignedProfileWithin
      (signedActionCarrierEnvelope intervention horizon deviationEnvelope)
      (natCarrierProfileToSigned execution.actual) := by
  intro carrier
  rw [execution.exact carrier]
  exact ⟨Int.add_le_add_left (execution.deviationWithin carrier).1 _,
    Int.add_le_add_left (execution.deviationWithin carrier).2 _⟩

theorem signed_execution_margin_forces_actual_carrier
    (intervention : DeclaredCarrierIntervention) (horizon : Nat)
    (deviationEnvelope : CarrierSignedDeviationEnvelope)
    (execution : SignedActionExecution intervention horizon deviationEnvelope)
    (selected : EnterpriseCarrier)
    (margin : StrictSignedInterventionMargin intervention horizon
      deviationEnvelope selected) :
    OperationallyDominant execution.actual selected := by
  apply (signed_dominance_iff_nat_dominance execution.actual selected).mp
  exact strict_signed_intervention_margin_forces_carrier intervention horizon
    deviationEnvelope selected margin _
      (execution.actual_within_total_envelope intervention horizon deviationEnvelope)

/-! The registered science plan has a ten-count lead. A shortfall of nine
retains a strict one-count lead over capability realization; a shortfall of ten
reaches a tie and loses to the earlier frozen priority. -/

theorem science_plan_shortfall_budget_boundary :
    ((12 : Int) - 9 > 2) ∧ ¬ ((12 : Int) - 10 > 2) := by norm_num

def scienceShortfallNineActual : EnterpriseCarrierCountProfile
  | .capabilityRealization => 2
  | .scientificClaim => 3
  | _ => 0

def scienceShortfallTenActual : EnterpriseCarrierCountProfile
  | .capabilityRealization => 2
  | .scientificClaim => 2
  | _ => 0

theorem science_shortfall_nine_preserves_carrier :
    OperationallyDominant scienceShortfallNineActual .scientificClaim := by
  intro other
  cases other <;> decide

theorem science_shortfall_ten_loses_carrier :
    ¬ OperationallyDominant scienceShortfallTenActual .scientificClaim := by
  intro dominant
  have losesTie := dominant .capabilityRealization
  simp [scienceShortfallTenActual, enterpriseCarrierPriority] at losesTie

/-- K/M composition using a signed execution certificate rather than the
one-sided nonnegative residual. -/
structure KMSignedActionCarrierContract
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {Path : Type uPath}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (observePaths : interpretation.State → List Path)
    (classifier : CertifiedPathCarrierClassifier Path) where
  horizon : Nat
  intervention : DeclaredCarrierIntervention
  active : intervention.validityActive = true
  deviationEnvelope : CarrierSignedDeviationEnvelope
  execution : SignedActionExecution intervention horizon deviationEnvelope
  targetAgreement : ∀ target,
    interpretation.predictiveInterpretation.targetFutureAt
      resolution.selection.minimizer.1 target →
    extractedCarrierProfile classifier.evidence (observePaths target) = execution.actual

theorem km_signed_action_flow_yields_singleton_carrier_support
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {Path : Type uPath}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMContextContinuationInterpretation liftSearch)
    (observePaths : interpretation.State → List Path)
    (classifier : CertifiedPathCarrierClassifier Path)
    (contract : KMSignedActionCarrierContract resolution interpretation
      observePaths classifier)
    (selected : EnterpriseCarrier)
    (margin : StrictSignedInterventionMargin contract.intervention
      contract.horizon contract.deviationEnvelope selected)
    (witnessTarget : interpretation.State)
    (witnessFuture : interpretation.predictiveInterpretation.targetFutureAt
      resolution.selection.minimizer.1 witnessTarget) :
    ∀ carrier,
      KMDerivedEnterpriseCarrierSupport resolution interpretation
        (classifier.toOperationalProjection observePaths).carrier carrier ↔
          carrier = selected := by
  apply km_extractor_profile_dominance_yields_singleton_carrier_support
    resolution interpretation observePaths classifier selected witnessTarget witnessFuture
  intro target future
  rw [contract.targetAgreement target future]
  exact signed_execution_margin_forces_actual_carrier contract.intervention
    contract.horizon contract.deviationEnvelope contract.execution selected margin

end OCKIndividuationMSpaceComposition
