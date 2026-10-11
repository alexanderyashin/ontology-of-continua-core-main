import OCKIndividuationMSpaceComposition.KMEnterpriseOperationalProjection

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe uPath uState uLiftCarrier uLiftCandidate uRepairCandidate

/-!
# Enterprise carrier extractor binding

The executable adapter counts typed evidence contributed by every observed
path.  This module states the exact mathematical contract of that computation:
the profile is the pointwise finite sum of path evidence, and the reported
carrier must carry an operational-dominance certificate for that profile.

This does not identify path strings with OC states.  It gives the minimum
domain adapter needed to compose a versioned extractor with the K/M,
context/continuation and numerical-support theorems.
-/

/-- One observed path contributes a nonnegative amount of evidence to each
enterprise carrier.  The current executable classifier contributes only zero
or one, while the formal contract permits later weighted adapters. -/
abbrev CarrierEvidence (Path : Type uPath) := Path → EnterpriseCarrier → Nat

/-- The exact count profile computed from a finite path observation. -/
def extractedCarrierProfile {Path : Type uPath}
    (evidence : CarrierEvidence Path) (paths : List Path) :
    EnterpriseCarrierCountProfile :=
  fun carrier => (paths.map fun path => evidence path carrier).sum

theorem extractedCarrierProfile_nil {Path : Type uPath}
    (evidence : CarrierEvidence Path) :
    extractedCarrierProfile evidence [] = fun _ => 0 := by
  funext carrier
  simp [extractedCarrierProfile]

/-- Evidence is additive under path-list composition. -/
theorem extractedCarrierProfile_append {Path : Type uPath}
    (evidence : CarrierEvidence Path) (left right : List Path)
    (carrier : EnterpriseCarrier) :
    extractedCarrierProfile evidence (left ++ right) carrier =
      extractedCarrierProfile evidence left carrier +
        extractedCarrierProfile evidence right carrier := by
  simp [extractedCarrierProfile]

/-- A certified classifier is an executable selection rule together with the
proof obligation that its selection is dominant for the exact count profile. -/
structure CertifiedPathCarrierClassifier (Path : Type uPath) where
  evidence : CarrierEvidence Path
  select : List Path → EnterpriseCarrier
  dominant : ∀ paths,
    OperationallyDominant (extractedCarrierProfile evidence paths) (select paths)

/-- Any state-to-path observation turns a certified path classifier into the
operational projection required by the K/M carrier bridge. -/
def CertifiedPathCarrierClassifier.toOperationalProjection
    {Path : Type uPath} {State : Type uState}
    (classifier : CertifiedPathCarrierClassifier Path)
    (observePaths : State → List Path) : EnterpriseOperationalProjection State where
  profile state := extractedCarrierProfile classifier.evidence (observePaths state)
  carrier state := classifier.select (observePaths state)
  dominant state := classifier.dominant (observePaths state)

/-- A replay certificate binds reported data to the formal profile rather than
trusting a carrier label alone. -/
structure ExtractorProfileCertificate (Path : Type uPath) where
  classifier : CertifiedPathCarrierClassifier Path
  paths : List Path
  reportedProfile : EnterpriseCarrierCountProfile
  reportedCarrier : EnterpriseCarrier
  profile_exact : reportedProfile =
    extractedCarrierProfile classifier.evidence paths
  carrier_exact : reportedCarrier = classifier.select paths

theorem ExtractorProfileCertificate.reportedCarrier_dominant
    {Path : Type uPath} (certificate : ExtractorProfileCertificate Path) :
    OperationallyDominant certificate.reportedProfile
      certificate.reportedCarrier := by
  rw [certificate.profile_exact, certificate.carrier_exact]
  exact certificate.classifier.dominant certificate.paths

/-- An independently checked dominant carrier must equal the certified
extractor result. -/
theorem ExtractorProfileCertificate.unique_reportedCarrier
    {Path : Type uPath} (certificate : ExtractorProfileCertificate Path)
    (carrier : EnterpriseCarrier)
    (dominant : OperationallyDominant certificate.reportedProfile carrier) :
    carrier = certificate.reportedCarrier :=
  operationallyDominant_unique certificate.reportedProfile dominant
    certificate.reportedCarrier_dominant

/-- Exact path replay preserves both the full count profile and the selected
carrier.  This is the formal core of the prospective path-conformance check. -/
theorem exact_path_replay_preserves_profile_and_carrier
    {Path : Type uPath} (classifier : CertifiedPathCarrierClassifier Path)
    {planned actual : List Path} (conformant : actual = planned) :
    extractedCarrierProfile classifier.evidence actual =
        extractedCarrierProfile classifier.evidence planned ∧
      classifier.select actual = classifier.select planned := by
  subst actual
  exact ⟨rfl, rfl⟩

/-- Once the extractor profile satisfies one carrier's inequalities over all
selected K/M terminal futures, the existing operational theorem yields exact
singleton support. -/
theorem km_extractor_profile_dominance_yields_singleton_carrier_support
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
    (selectedCarrier : EnterpriseCarrier)
    (witnessTarget : interpretation.State)
    (witnessFuture : interpretation.predictiveInterpretation.targetFutureAt
      resolution.selection.minimizer.1 witnessTarget)
    (dominance : ∀ target,
      interpretation.predictiveInterpretation.targetFutureAt
        resolution.selection.minimizer.1 target →
      OperationallyDominant
        (extractedCarrierProfile classifier.evidence (observePaths target))
        selectedCarrier) :
    ∀ carrier,
      KMDerivedEnterpriseCarrierSupport resolution interpretation
        (classifier.toOperationalProjection observePaths).carrier carrier ↔
          carrier = selectedCarrier := by
  apply km_operational_dominance_yields_singleton_carrier_support
    resolution interpretation (classifier.toOperationalProjection observePaths)
      selectedCarrier witnessTarget witnessFuture
  intro target future
  exact dominance target future

/-!
## Multiplicity-loss countermodel

The set of carrier labels touched by an event is weaker than the count profile.
Both examples below touch exactly `scientificClaim` and `controlDecision`, but
their multiplicities force opposite dominant carriers.
-/

inductive ExtractorSignal where
  | scientific
  | control
  deriving DecidableEq

def extractorSignalEvidence : CarrierEvidence ExtractorSignal
  | .scientific, .scientificClaim => 1
  | .control, .controlDecision => 1
  | _, _ => 0

def scientificHeavySignals : List ExtractorSignal :=
  [.scientific, .scientific, .control]

def controlHeavySignals : List ExtractorSignal :=
  [.scientific, .control, .control]

def profileSupport (profile : EnterpriseCarrierCountProfile)
    (carrier : EnterpriseCarrier) : Prop :=
  0 < profile carrier

theorem scientificHeavy_profile_is_scientific_dominant :
    OperationallyDominant
      (extractedCarrierProfile extractorSignalEvidence scientificHeavySignals)
      .scientificClaim := by
  intro other
  cases other <;> decide

theorem controlHeavy_profile_is_control_dominant :
    OperationallyDominant
      (extractedCarrierProfile extractorSignalEvidence controlHeavySignals)
      .controlDecision := by
  intro other
  cases other <;> decide

/-- No-go: carrier membership without multiplicity cannot determine the
dominant carrier. -/
theorem carrier_support_set_does_not_determine_dominant_carrier :
    (∀ carrier,
      profileSupport
          (extractedCarrierProfile extractorSignalEvidence scientificHeavySignals)
          carrier ↔
        profileSupport
          (extractedCarrierProfile extractorSignalEvidence controlHeavySignals)
          carrier) ∧
      OperationallyDominant
        (extractedCarrierProfile extractorSignalEvidence scientificHeavySignals)
        .scientificClaim ∧
      OperationallyDominant
        (extractedCarrierProfile extractorSignalEvidence controlHeavySignals)
        .controlDecision ∧
      EnterpriseCarrier.scientificClaim ≠ EnterpriseCarrier.controlDecision := by
  constructor
  · intro carrier
    cases carrier <;>
      simp [profileSupport, extractedCarrierProfile, scientificHeavySignals,
        controlHeavySignals, extractorSignalEvidence]
  exact ⟨scientificHeavy_profile_is_scientific_dominant,
    controlHeavy_profile_is_control_dominant, by decide⟩

end OCKIndividuationMSpaceComposition
