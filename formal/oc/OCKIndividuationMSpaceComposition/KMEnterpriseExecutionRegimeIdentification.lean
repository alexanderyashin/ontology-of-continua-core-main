import OCKIndividuationMSpaceComposition.KMEnterpriseSignedInterventionDeviation
import OCKIndividuationMSpaceComposition.FiniteObservationLearning

namespace OCKIndividuationMSpaceComposition

/-!
# Execution-regime identification for enterprise carrier deviations

Exact-path governance makes the observed signed deviation identically zero.
That is a valid deterministic prediction inside the governed regime, but it
does not identify an uncontrolled execution law.  This module connects the
enterprise profile adapter to the existing finite-observation coverage theory
instead of re-proving generic learning or transportability mathematics.
-/

/-- Signed actual-minus-planned deviation of an extracted carrier profile. -/
def carrierProfileDeviation
    (planned actual : EnterpriseCarrierCountProfile) :
    EnterpriseCarrierSignedProfile :=
  fun carrier => Int.ofNat (actual carrier) - Int.ofNat (planned carrier)

/-- Closed-world conformance at the profile surface.  Exact path equality is a
stronger executable witness that implies this equality through extraction. -/
def ExactCarrierProfileConformance
    (planned actual : EnterpriseCarrierCountProfile) : Prop :=
  actual = planned

theorem exact_conformance_iff_zero_signed_deviation
    (planned actual : EnterpriseCarrierCountProfile) :
    ExactCarrierProfileConformance planned actual ↔
      carrierProfileDeviation planned actual = fun _ => 0 := by
  constructor
  · intro conformant
    subst actual
    funext carrier
    simp [carrierProfileDeviation]
  · intro zeroDeviation
    apply funext
    intro carrier
    have coordinateZero := congrFun zeroDeviation carrier
    have signedEqual :
        Int.ofNat (actual carrier) = Int.ofNat (planned carrier) := by
      exact Int.sub_eq_zero.mp (by simpa [carrierProfileDeviation] using coordinateZero)
    exact Int.ofNat.inj signedEqual

theorem exact_conformance_transports_operational_dominance
    (planned actual : EnterpriseCarrierCountProfile)
    (selected : EnterpriseCarrier)
    (conformant : ExactCarrierProfileConformance planned actual)
    (dominant : OperationallyDominant planned selected) :
    OperationallyDominant actual selected := by
  change actual = planned at conformant
  rw [conformant]
  exact dominant

def zeroEnterpriseSignedProfile : EnterpriseCarrierSignedProfile :=
  fun _ => 0

def scientificUnitDeviationProfile : EnterpriseCarrierSignedProfile :=
  fun carrier => if carrier = .scientificClaim then 1 else 0

theorem zero_and_scientific_unit_deviation_are_distinct :
    zeroEnterpriseSignedProfile ≠ scientificUnitDeviationProfile := by
  intro equalProfiles
  have scientificCoordinate := congrFun equalProfiles EnterpriseCarrier.scientificClaim
  simp [zeroEnterpriseSignedProfile, scientificUnitDeviationProfile] at scientificCoordinate

/-- `true` denotes exact-path-enforced execution; `false` denotes an open
execution regime whose deviation mechanism has not yet been identified. -/
def conformanceOnlyDeviationLaw : Bool → EnterpriseCarrierSignedProfile :=
  fun _ => zeroEnterpriseSignedProfile

def openRegimeUnitDeviationLaw : Bool → EnterpriseCarrierSignedProfile :=
  fun exactPathEnforced =>
    if exactPathEnforced then zeroEnterpriseSignedProfile
    else scientificUnitDeviationProfile

/-- No-go: arbitrarily many observations from only the exact-path-enforced
regime cannot identify the deviation law in the open regime. -/
theorem controlled_only_samples_do_not_identify_open_deviation
    {sampleSize : Nat} (sample : Fin sampleSize → Bool)
    (allControlled : ∀ index, sample index = true) :
    (∀ index,
      conformanceOnlyDeviationLaw (sample index) =
        openRegimeUnitDeviationLaw (sample index)) ∧
      conformanceOnlyDeviationLaw false ≠ openRegimeUnitDeviationLaw false := by
  constructor
  · intro index
    simp [conformanceOnlyDeviationLaw, openRegimeUnitDeviationLaw,
      allControlled index]
  · simpa [conformanceOnlyDeviationLaw, openRegimeUnitDeviationLaw] using
      zero_and_scientific_unit_deviation_are_distinct

/-- Positive result: for a deterministic deviation response, coverage of every
registered execution-regime cell is sufficient for exact prediction in every
cell.  This is the minimum OC adapter to the mature coverage theorem. -/
theorem execution_regime_coverage_identifies_deterministic_deviation
    {sampleSize : Nat}
    (deviationLaw : Bool → EnterpriseCarrierSignedProfile)
    (sample : Fin sampleSize → Bool)
    (covers : ObservationDesignCovers (fun regime : Bool => regime) sample) :
    ∀ regime,
      coveredSamplePredictor (fun state : Bool => state) deviationLaw sample regime =
        deviationLaw regime := by
  apply covered_sufficient_sample_predictor_is_exact
    (fun regime : Bool => regime) deviationLaw sample covers
  intro left right sameRegime
  exact congrArg deviationLaw sameRegime

def fiveControlledExecutionRegimes : Fin 5 → Bool :=
  fun _ => true

/-- The five frozen OC occurrences sample exactly one of the two registered
execution regimes, so their count does not repair the missing state cell. -/
theorem five_controlled_occurrences_do_not_cover_open_regime :
    ¬ ObservationDesignCovers
      (fun regime : Bool => regime) fiveControlledExecutionRegimes := by
  intro covers
  obtain ⟨index, impossible⟩ := covers false
  simp [fiveControlledExecutionRegimes] at impossible

theorem five_controlled_occurrences_admit_distinct_open_regime_laws :
    (∀ index,
      conformanceOnlyDeviationLaw (fiveControlledExecutionRegimes index) =
        openRegimeUnitDeviationLaw (fiveControlledExecutionRegimes index)) ∧
      conformanceOnlyDeviationLaw false ≠ openRegimeUnitDeviationLaw false :=
  controlled_only_samples_do_not_identify_open_deviation
    fiveControlledExecutionRegimes (by intro index; rfl)

end OCKIndividuationMSpaceComposition
