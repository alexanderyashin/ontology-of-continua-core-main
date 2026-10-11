import OCKIndividuationMSpaceComposition.EnterpriseCarrierExtractorBinding

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe uPath uState uLiftCarrier uLiftCandidate uRepairCandidate

/-!
# Sharp enterprise carrier prediction from count envelopes

A predictive K/M model need not identify every future path.  It may instead
bound each future carrier count.  For a rectangular count envelope, the worst
profile for a proposed carrier places that carrier at its lower bound and every
competitor at its upper bound.  The central theorem below proves that checking
this single adversarial corner is necessary and sufficient for dominance over
every profile in the envelope.
-/

structure CarrierCountEnvelope where
  lower : EnterpriseCarrierCountProfile
  upper : EnterpriseCarrierCountProfile
  valid : ∀ carrier, lower carrier ≤ upper carrier

def ProfileWithin (envelope : CarrierCountEnvelope)
    (profile : EnterpriseCarrierCountProfile) : Prop :=
  ∀ carrier,
    envelope.lower carrier ≤ profile carrier ∧
      profile carrier ≤ envelope.upper carrier

/-- Worst rectangular-envelope corner for one proposed dominant carrier. -/
def adversarialCarrierProfile (envelope : CarrierCountEnvelope)
    (selected : EnterpriseCarrier) : EnterpriseCarrierCountProfile :=
  fun carrier =>
    if carrier = selected then envelope.lower selected else envelope.upper carrier

theorem adversarialCarrierProfile_within
    (envelope : CarrierCountEnvelope) (selected : EnterpriseCarrier) :
    ProfileWithin envelope (adversarialCarrierProfile envelope selected) := by
  intro carrier
  by_cases same : carrier = selected
  · subst carrier
    simp [adversarialCarrierProfile, envelope.valid]
  · simp [adversarialCarrierProfile, same, envelope.valid]

/-- Dominance of the adversarial corner transports to every profile inside the
same rectangular envelope. -/
theorem adversarial_dominance_implies_all_profiles_dominance
    (envelope : CarrierCountEnvelope) (selected : EnterpriseCarrier)
    (cornerDominant : OperationallyDominant
      (adversarialCarrierProfile envelope selected) selected) :
    ∀ profile, ProfileWithin envelope profile →
      OperationallyDominant profile selected := by
  intro profile within other
  by_cases same : other = selected
  · subst other
    exact Or.inr ⟨rfl, Nat.le_refl _⟩
  obtain cornerStrict | ⟨cornerEqual, priority⟩ := cornerDominant other
  · left
    have otherUpper : profile other ≤ envelope.upper other := (within other).2
    have selectedLower : envelope.lower selected ≤ profile selected :=
      (within selected).1
    have cornerStrict' : envelope.upper other < envelope.lower selected := by
      simpa [adversarialCarrierProfile, same] using cornerStrict
    exact lt_of_le_of_lt otherUpper
      (lt_of_lt_of_le cornerStrict' selectedLower)
  · have otherUpper : profile other ≤ envelope.upper other := (within other).2
    have selectedLower : envelope.lower selected ≤ profile selected :=
      (within selected).1
    have cornerEqual' : envelope.upper other = envelope.lower selected := by
      simpa [adversarialCarrierProfile, same] using cornerEqual
    have countsLe : profile other ≤ profile selected := by
      calc
        profile other ≤ envelope.upper other := otherUpper
        _ = envelope.lower selected := cornerEqual'
        _ ≤ profile selected := selectedLower
    obtain countsStrict | countsEqual := Nat.lt_or_eq_of_le countsLe
    · exact Or.inl countsStrict
    · exact Or.inr ⟨countsEqual, priority⟩

def EnvelopeForcesCarrier (envelope : CarrierCountEnvelope)
    (selected : EnterpriseCarrier) : Prop :=
  ∀ profile, ProfileWithin envelope profile →
    OperationallyDominant profile selected

/-- Sharp theorem: one adversarial corner is both sufficient and necessary. -/
theorem envelope_forces_carrier_iff_adversarial_dominant
    (envelope : CarrierCountEnvelope) (selected : EnterpriseCarrier) :
    EnvelopeForcesCarrier envelope selected ↔
      OperationallyDominant (adversarialCarrierProfile envelope selected)
        selected := by
  constructor
  · intro forces
    exact forces _ (adversarialCarrierProfile_within envelope selected)
  · exact adversarial_dominance_implies_all_profiles_dominance envelope selected

/-- Sharp no-go: when the corner check fails, that corner itself is a lawful
future profile witnessing why the envelope cannot force the carrier. -/
theorem envelope_failure_has_admissible_counterprofile
    (envelope : CarrierCountEnvelope) (selected : EnterpriseCarrier)
    (notForced : ¬ EnvelopeForcesCarrier envelope selected) :
    ∃ profile,
      ProfileWithin envelope profile ∧
        ¬ OperationallyDominant profile selected := by
  refine ⟨adversarialCarrierProfile envelope selected,
    adversarialCarrierProfile_within envelope selected, ?_⟩
  intro dominant
  exact notForced
    ((envelope_forces_carrier_iff_adversarial_dominant envelope selected).mpr
      dominant)

/-- A K/M future envelope whose adversarial corner is dominant yields the exact
singleton carrier support after executable profile extraction. -/
theorem km_count_envelope_yields_singleton_carrier_support
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
    (envelope : CarrierCountEnvelope)
    (selectedCarrier : EnterpriseCarrier)
    (cornerDominant : OperationallyDominant
      (adversarialCarrierProfile envelope selectedCarrier) selectedCarrier)
    (witnessTarget : interpretation.State)
    (witnessFuture : interpretation.predictiveInterpretation.targetFutureAt
      resolution.selection.minimizer.1 witnessTarget)
    (futureWithin : ∀ target,
      interpretation.predictiveInterpretation.targetFutureAt
        resolution.selection.minimizer.1 target →
      ProfileWithin envelope
        (extractedCarrierProfile classifier.evidence (observePaths target))) :
    ∀ carrier,
      KMDerivedEnterpriseCarrierSupport resolution interpretation
        (classifier.toOperationalProjection observePaths).carrier carrier ↔
          carrier = selectedCarrier := by
  apply km_extractor_profile_dominance_yields_singleton_carrier_support
    resolution interpretation observePaths classifier selectedCarrier
      witnessTarget witnessFuture
  intro target future
  exact adversarial_dominance_implies_all_profiles_dominance envelope
    selectedCarrier cornerDominant _ (futureWithin target future)

/-- If the envelope check succeeds and context/continuation coherence holds,
every tied K/M minimum necessarily has the selected carrier. -/
theorem km_count_envelope_carrier_is_necessary_over_tied_models
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
    (coherent : KMTiedContextContinuationCoherent resolution interpretation)
    (selectedCarrier : EnterpriseCarrier)
    (singletonSupport : ∀ carrier,
      KMDerivedEnterpriseCarrierSupport resolution interpretation
        (classifier.toOperationalProjection observePaths).carrier carrier ↔
          carrier = selectedCarrier) :
    KMNecessaryFuture resolution
      (interpretation.carrierFutureAt
        (classifier.toOperationalProjection observePaths).carrier)
      selectedCarrier := by
  exact km_operational_singleton_carrier_is_necessary resolution interpretation
    (classifier.toOperationalProjection observePaths) coherent selectedCarrier
      singletonSupport

end OCKIndividuationMSpaceComposition
