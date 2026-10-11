import OCKIndividuationMSpaceComposition.KAxisAndCurrentKBridge
import Init.Tactics

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe uState uCandidate

/-!
# Robust K-profile inference

An estimator does not identify a K profile merely by returning one relation.
The formal input below is an evidence band.  Every admissible profile or
resolution relation must lie between its lower and upper surfaces.

Identification is deliberately relation-level.  All admissible profiles must
induce the same observational kernel and all admissible resolution relations
must induce the same reachability/SCC structure.  Those two invariances alone
are only weak co-registration.  Strong contextual coherence additionally
requires every admissible resolution edge to preserve every admissible profile
family and fixes all pairwise refinement comparisons across those families.
If admissible alternatives disagree, the formal result is an abstention or
insufficiency witness.  No theorem in this file asserts that a real dataset
supplies a correct band, a separated margin, or the strong coherence
certificate.
-/

/-! ## Uncertain distinction profiles -/

/-- Lower and upper pairwise distinctions supported by one frozen analysis. -/
structure ProfileEvidenceBand (State : Type uState) where
  lower : DistinctionProfile State
  upper : DistinctionProfile State
  coherent : AtLeastAsDiscriminating upper lower

/-- A profile is admissible exactly when it contains every lower distinction
and introduces no distinction outside the upper surface. -/
def ProfileAdmissible
    {State : Type uState}
    (band : ProfileEvidenceBand State)
    (profile : DistinctionProfile State) : Prop :=
  AtLeastAsDiscriminating profile band.lower ∧
    AtLeastAsDiscriminating band.upper profile

/-- The symmetric observational kernel induced by a distinction profile. -/
def ProfileKernel
    {State : Type uState}
    (profile : DistinctionProfile State) : BinaryRelation State :=
  fun first second => ¬ profile first second ∧ ¬ profile second first

/-- Robust profile identification asks for agreement over the complete
admissible set, not agreement of two selected point estimates. -/
def AllAdmissibleProfilesHaveSameKernel
    {State : Type uState}
    (band : ProfileEvidenceBand State) : Prop :=
  ∀ ⦃firstProfile secondProfile⦄,
    ProfileAdmissible band firstProfile →
    ProfileAdmissible band secondProfile →
    ∀ first second,
      ProfileKernel firstProfile first second ↔
        ProfileKernel secondProfile first second

/-- Two admissible profiles that induce different observational kernels are a
constructive profile-level ambiguity certificate. -/
def ProfileKernelAmbiguous
    {State : Type uState}
    (band : ProfileEvidenceBand State) : Prop :=
  ∃ firstProfile secondProfile,
    ProfileAdmissible band firstProfile ∧
    ProfileAdmissible band secondProfile ∧
    ∃ first second,
      ¬ (ProfileKernel firstProfile first second ↔
        ProfileKernel secondProfile first second)

theorem profileAmbiguity_blocks_kernelIdentification
    {State : Type uState}
    {band : ProfileEvidenceBand State}
    (ambiguous : ProfileKernelAmbiguous band) :
    ¬ AllAdmissibleProfilesHaveSameKernel band := by
  intro identified
  rcases ambiguous with
    ⟨firstProfile, secondProfile, firstAdmissible, secondAdmissible,
      first, second, disagree⟩
  exact disagree (identified firstAdmissible secondAdmissible first second)

/-- A collapsed evidence band forces every admissible profile to be the same
profile extensionally. -/
theorem profileAdmissible_eq_lower_of_exactBand
    {State : Type uState}
    {band : ProfileEvidenceBand State}
    (exactBand : band.lower = band.upper)
    {profile : DistinctionProfile State}
    (admissible : ProfileAdmissible band profile) :
    profile = band.lower := by
  apply atLeastAsDiscriminating_antisymm
  · exact admissible.1
  · simpa [exactBand] using admissible.2

/-- Exact profile bands identify the observational kernel. -/
theorem exactProfileBand_identifies_kernel
    {State : Type uState}
    (band : ProfileEvidenceBand State)
    (exactBand : band.lower = band.upper) :
    AllAdmissibleProfilesHaveSameKernel band := by
  intro firstProfile secondProfile firstAdmissible secondAdmissible first second
  have firstEq := profileAdmissible_eq_lower_of_exactBand
    exactBand firstAdmissible
  have secondEq := profileAdmissible_eq_lower_of_exactBand
    exactBand secondAdmissible
  rw [firstEq, secondEq]

/-! ## Deterministic repeated-observation estimator -/

/-- A frozen finite batch of repeated pairwise observations.  The observations
are raw Boolean outcomes; this structure contains no probability model and no
coverage/confidence assertion. -/
structure FiniteRepeatedPairObservations (Carrier : Type uState) where
  repetitions : Nat
  observed : Carrier → Carrier → Fin repetitions → Bool

namespace FiniteRepeatedPairObservations

variable {Carrier : Type uState}

/-- Number of observed positive outcomes for one ordered pair. -/
def positiveVotes
    (raw : FiniteRepeatedPairObservations Carrier)
    (first second : Carrier) : Nat :=
  ((Finset.univ : Finset (Fin raw.repetitions)).filter
    (fun trial => raw.observed first second trial = true)).card

/-- The uncorrected strict-majority point estimate. -/
def majorityRelation
    (raw : FiniteRepeatedPairObservations Carrier) : BinaryRelation Carrier :=
  fun first second =>
    raw.repetitions < 2 * raw.positiveVotes first second

/-- A true distinction is still possible after at most `errorBudget`
adversarially wrong repetitions. -/
def observationUpperRelation
    (raw : FiniteRepeatedPairObservations Carrier)
    (errorBudget : Nat) : BinaryRelation Carrier :=
  fun first second =>
    raw.repetitions ≤ raw.positiveVotes first second + errorBudget

/-- A distinction is forced when it is possible and the opposite label would
require more than the admitted adversarial-error budget. -/
def observationLowerRelation
    (raw : FiniteRepeatedPairObservations Carrier)
    (errorBudget : Nat) : BinaryRelation Carrier :=
  fun first second =>
    errorBudget < raw.positiveVotes first second ∧
      raw.observationUpperRelation errorBudget first second

theorem observationLower_refines_upper
    (raw : FiniteRepeatedPairObservations Carrier)
    (errorBudget : Nat) :
    RelationRefines (raw.observationLowerRelation errorBudget)
      (raw.observationUpperRelation errorBudget) := by
  intro first second lower
  exact lower.2

/-- The complete relation band computed from the raw repeated observations and
one declared worst-case error budget. -/
def toProfileEvidenceBand
    (raw : FiniteRepeatedPairObservations Carrier)
    (errorBudget : Nat) : ProfileEvidenceBand Carrier where
  lower := raw.observationLowerRelation errorBudget
  upper := raw.observationUpperRelation errorBudget
  coherent := raw.observationLower_refines_upper errorBudget

/-- Deterministic aggregate error certificate for an externally supplied true
relation.  It states only a worst-case count bound.  A probabilistic sampling
model or confidence guarantee, if any, must be supplied outside Lean. -/
structure AdversarialErrorCertificate
    (raw : FiniteRepeatedPairObservations Carrier)
    (truth : BinaryRelation Carrier)
    (errorBudget : Nat) : Prop where
  repetitions_positive : 0 < raw.repetitions
  true_errors_bounded : ∀ {first second},
    truth first second →
      raw.repetitions ≤ raw.positiveVotes first second + errorBudget
  false_errors_bounded : ∀ {first second},
    ¬ truth first second →
      raw.positiveVotes first second ≤ errorBudget

/-- Under the explicit adversarial-count certificate, the externally supplied
truth lies in the observation-derived uncertainty band. -/
theorem truth_is_admissible_in_observationBand
    (raw : FiniteRepeatedPairObservations Carrier)
    (truth : BinaryRelation Carrier)
    (errorBudget : Nat)
    (certificate : AdversarialErrorCertificate raw truth errorBudget) :
    ProfileAdmissible (raw.toProfileEvidenceBand errorBudget) truth := by
  constructor
  · intro first second lower
    by_contra notTrue
    have bounded := certificate.false_errors_bounded notTrue
    exact (Nat.not_lt_of_ge bounded) lower.1
  · intro first second truePair
    exact certificate.true_errors_bounded truePair

/-- A strict adversarial majority margin: fewer than half of the repeated
observations may be wrong. -/
def AdversarialMajorityMargin
    (raw : FiniteRepeatedPairObservations Carrier)
    (errorBudget : Nat) : Prop :=
  2 * errorBudget < raw.repetitions

/-- With a true worst-case error certificate and a strict majority margin, the
raw majority relation recovers the supplied truth exactly. -/
theorem majorityRelation_eq_truth_of_errorCertificate
    (raw : FiniteRepeatedPairObservations Carrier)
    (truth : BinaryRelation Carrier)
    (errorBudget : Nat)
    (certificate : AdversarialErrorCertificate raw truth errorBudget)
    (margin : raw.AdversarialMajorityMargin errorBudget) :
    raw.majorityRelation = truth := by
  funext first second
  apply propext
  constructor
  · intro majority
    change raw.repetitions < 2 * raw.positiveVotes first second at majority
    change 2 * errorBudget < raw.repetitions at margin
    by_contra notTrue
    have bounded := certificate.false_errors_bounded notTrue
    omega
  · intro truePair
    change 2 * errorBudget < raw.repetitions at margin
    have bounded := certificate.true_errors_bounded truePair
    change raw.repetitions < 2 * raw.positiveVotes first second
    omega

/-- Under the same explicit assumptions, the lower and upper uncertainty
surfaces both equal the true relation. -/
theorem observationBand_collapses_to_truth_of_errorCertificate
    (raw : FiniteRepeatedPairObservations Carrier)
    (truth : BinaryRelation Carrier)
    (errorBudget : Nat)
    (certificate : AdversarialErrorCertificate raw truth errorBudget)
    (margin : raw.AdversarialMajorityMargin errorBudget) :
    (raw.toProfileEvidenceBand errorBudget).lower = truth ∧
      (raw.toProfileEvidenceBand errorBudget).upper = truth := by
  constructor
  · funext first second
    apply propext
    constructor
    · intro lower
      by_contra notTrue
      have bounded := certificate.false_errors_bounded notTrue
      exact (Nat.not_lt_of_ge bounded) lower.1
    · intro truePair
      have bounded := certificate.true_errors_bounded truePair
      constructor
      · change errorBudget < raw.positiveVotes first second
        change 2 * errorBudget < raw.repetitions at margin
        omega
      · exact bounded
  · funext first second
    apply propext
    constructor
    · intro possibleTrue
      change raw.repetitions ≤
        raw.positiveVotes first second + errorBudget at possibleTrue
      change 2 * errorBudget < raw.repetitions at margin
      by_contra notTrue
      have bounded := certificate.false_errors_bounded notTrue
      omega
    · intro truePair
      exact certificate.true_errors_bounded truePair

/-- Explicit pair-level output of the deterministic adversarial estimator. -/
inductive AdversarialPairDecision
  | distinguished
  | notDistinguished
  | abstain
  deriving DecidableEq, Repr

/-- Decide only outside the uncertainty interval; otherwise abstain. -/
def pairDecision
    (raw : FiniteRepeatedPairObservations Carrier)
    (errorBudget : Nat)
    (first second : Carrier) : AdversarialPairDecision :=
  if errorBudget < raw.positiveVotes first second ∧
      raw.repetitions ≤ raw.positiveVotes first second + errorBudget then
    .distinguished
  else if raw.repetitions ≤
      raw.positiveVotes first second + errorBudget then
    .abstain
  else
    .notDistinguished

theorem pairDecision_eq_abstain_iff
    (raw : FiniteRepeatedPairObservations Carrier)
    (errorBudget : Nat)
    (first second : Carrier) :
    raw.pairDecision errorBudget first second = .abstain ↔
      ¬ raw.observationLowerRelation errorBudget first second ∧
        raw.observationUpperRelation errorBudget first second := by
  unfold observationLowerRelation observationUpperRelation
  by_cases lower : errorBudget < raw.positiveVotes first second ∧
      raw.repetitions ≤ raw.positiveVotes first second + errorBudget
  · simp [pairDecision, lower]
  · by_cases upper : raw.repetitions ≤
        raw.positiveVotes first second + errorBudget
    · simp [pairDecision, lower, upper]
    · simp [pairDecision, lower, upper]

/-- A valid strict-margin certificate rules out abstention and makes the
decision agree with the externally supplied truth. -/
theorem pairDecision_recovers_truth_of_errorCertificate
    (raw : FiniteRepeatedPairObservations Carrier)
    (truth : BinaryRelation Carrier)
    (errorBudget : Nat)
    (certificate : AdversarialErrorCertificate raw truth errorBudget)
    (margin : raw.AdversarialMajorityMargin errorBudget)
    (first second : Carrier) :
    raw.pairDecision errorBudget first second =
      @ite AdversarialPairDecision (truth first second)
        (Classical.propDecidable (truth first second))
        .distinguished .notDistinguished := by
  rcases raw.observationBand_collapses_to_truth_of_errorCertificate
    truth errorBudget certificate margin with ⟨lowerEq, upperEq⟩
  by_cases truePair : truth first second
  · have lowerPair : raw.observationLowerRelation errorBudget first second := by
      change (raw.toProfileEvidenceBand errorBudget).lower first second
      rw [lowerEq]
      exact truePair
    change errorBudget < raw.positiveVotes first second ∧
      raw.repetitions ≤ raw.positiveVotes first second + errorBudget at lowerPair
    simp [pairDecision, lowerPair, truePair]
  · have notLower :
        ¬ raw.observationLowerRelation errorBudget first second := by
      intro lowerPair
      have asBand :
          (raw.toProfileEvidenceBand errorBudget).lower first second :=
        lowerPair
      rw [lowerEq] at asBand
      exact truePair asBand
    have notUpper :
        ¬ raw.observationUpperRelation errorBudget first second := by
      intro upperPair
      have asBand :
          (raw.toProfileEvidenceBand errorBudget).upper first second :=
        upperPair
      rw [upperEq] at asBand
      exact truePair asBand
    change ¬ (errorBudget < raw.positiveVotes first second ∧
      raw.repetitions ≤ raw.positiveVotes first second + errorBudget) at notLower
    change ¬ (raw.repetitions ≤
      raw.positiveVotes first second + errorBudget) at notUpper
    simp [pairDecision, notLower, notUpper, truePair]

/-- The same certified strict majority identifies the complete admissible
profile kernel, not only the majority point estimate. -/
theorem adversarialMajority_identifies_profileKernel
    (raw : FiniteRepeatedPairObservations Carrier)
    (truth : BinaryRelation Carrier)
    (errorBudget : Nat)
    (certificate : AdversarialErrorCertificate raw truth errorBudget)
    (margin : raw.AdversarialMajorityMargin errorBudget) :
    AllAdmissibleProfilesHaveSameKernel
      (raw.toProfileEvidenceBand errorBudget) := by
  rcases raw.observationBand_collapses_to_truth_of_errorCertificate
    truth errorBudget certificate margin with ⟨lowerEq, upperEq⟩
  apply exactProfileBand_identifies_kernel
  change raw.observationLowerRelation errorBudget =
    raw.observationUpperRelation errorBudget
  exact lowerEq.trans upperEq.symm

end FiniteRepeatedPairObservations

/-! ## A score-margin constructor for evidence bands -/

/-- Pairwise score intervals around one frozen decision threshold. -/
structure PairwiseScoreBand (Carrier : Type uState) where
  lowerScore : Carrier → Carrier → ℚ
  upperScore : Carrier → Carrier → ℚ
  threshold : ℚ
  ordered : ∀ first second,
    lowerScore first second ≤ upperScore first second

namespace PairwiseScoreBand

variable {Carrier : Type uState}

def lowerRelation (band : PairwiseScoreBand Carrier) : BinaryRelation Carrier :=
  fun first second => band.threshold < band.lowerScore first second

def upperRelation (band : PairwiseScoreBand Carrier) : BinaryRelation Carrier :=
  fun first second => band.threshold < band.upperScore first second

theorem lowerRelation_refines_upperRelation
    (band : PairwiseScoreBand Carrier) :
    RelationRefines band.lowerRelation band.upperRelation := by
  intro first second lowerAbove
  exact lt_of_lt_of_le lowerAbove (band.ordered first second)

/-- A strict margin means that every interval lies wholly at or below the
threshold, or its lower endpoint lies strictly above the threshold. -/
def MarginSeparated (band : PairwiseScoreBand Carrier) : Prop :=
  ∀ first second,
    band.upperScore first second ≤ band.threshold ∨
      band.threshold < band.lowerScore first second

/-- A strict score margin collapses lower and upper relation surfaces. -/
theorem relations_equal_of_marginSeparated
    (band : PairwiseScoreBand Carrier)
    (separated : band.MarginSeparated) :
    band.lowerRelation = band.upperRelation := by
  funext first second
  apply propext
  constructor
  · intro lowerAbove
    exact band.lowerRelation_refines_upperRelation lowerAbove
  · intro upperAbove
    rcases separated first second with below | lowerAbove
    · exact False.elim ((not_lt_of_ge below) upperAbove)
    · exact lowerAbove

def toProfileEvidenceBand
    (band : PairwiseScoreBand Carrier) : ProfileEvidenceBand Carrier where
  lower := band.lowerRelation
  upper := band.upperRelation
  coherent := band.lowerRelation_refines_upperRelation

/-- The score-margin theorem is conditional: if the externally justified
intervals have a strict margin, the admissible profile kernel is identified. -/
theorem marginSeparated_identifies_profileKernel
    (band : PairwiseScoreBand Carrier)
    (separated : band.MarginSeparated) :
    AllAdmissibleProfilesHaveSameKernel band.toProfileEvidenceBand :=
  exactProfileBand_identifies_kernel _
    (band.relations_equal_of_marginSeparated separated)

end PairwiseScoreBand

/-! ## Uncertain K-resolution relations and quotient agreement -/

/-- Lower/upper evidence for the relation whose SCC quotient defines K levels. -/
structure ResolutionRelationEvidenceBand (Candidate : Type uCandidate) where
  lower : BinaryRelation Candidate
  upper : BinaryRelation Candidate
  coherent : RelationRefines lower upper

def ResolutionRelationAdmissible
    {Candidate : Type uCandidate}
    (band : ResolutionRelationEvidenceBand Candidate)
    (relation : BinaryRelation Candidate) : Prop :=
  RelationRefines band.lower relation ∧
    RelationRefines relation band.upper

/-- Pointwise agreement of reachability is a quotient-safe characterization:
it fixes both SCC classes and precedence between their representatives without
requiring equality between quotient types built from different relations. -/
def AllAdmissibleResolutionRelationsAgree
    {Candidate : Type uCandidate}
    (band : ResolutionRelationEvidenceBand Candidate) : Prop :=
  ∀ ⦃firstRelation secondRelation⦄,
    ResolutionRelationAdmissible band firstRelation →
    ResolutionRelationAdmissible band secondRelation →
    ∀ first second,
      RelationReachable firstRelation first second ↔
        RelationReachable secondRelation first second

/-- The induced SCC partition is also required explicitly for publication
claims that speak of K-level identity. -/
def AllAdmissibleResolutionRelationsHaveSameSCC
    {Candidate : Type uCandidate}
    (band : ResolutionRelationEvidenceBand Candidate) : Prop :=
  ∀ ⦃firstRelation secondRelation⦄,
    ResolutionRelationAdmissible band firstRelation →
    ResolutionRelationAdmissible band secondRelation →
    ∀ first second,
      MutuallyReachable firstRelation first second ↔
        MutuallyReachable secondRelation first second

theorem reachabilityAgreement_implies_sccAgreement
    {Candidate : Type uCandidate}
    {band : ResolutionRelationEvidenceBand Candidate}
    (agreement : AllAdmissibleResolutionRelationsAgree band) :
    AllAdmissibleResolutionRelationsHaveSameSCC band := by
  intro firstRelation secondRelation firstAdmissible secondAdmissible first second
  constructor
  · rintro ⟨forward, backward⟩
    exact ⟨
      (agreement firstAdmissible secondAdmissible first second).1 forward,
      (agreement firstAdmissible secondAdmissible second first).1 backward⟩
  · rintro ⟨forward, backward⟩
    exact ⟨
      (agreement firstAdmissible secondAdmissible first second).2 forward,
      (agreement firstAdmissible secondAdmissible second first).2 backward⟩

theorem resolutionRelationAdmissible_eq_lower_of_exactBand
    {Candidate : Type uCandidate}
    {band : ResolutionRelationEvidenceBand Candidate}
    (exactBand : band.lower = band.upper)
    {relation : BinaryRelation Candidate}
    (admissible : ResolutionRelationAdmissible band relation) :
    relation = band.lower := by
  funext first second
  apply propext
  constructor
  · intro edge
    have upperEdge := admissible.2 edge
    simpa [← exactBand] using upperEdge
  · intro edge
    exact admissible.1 edge

/-- A collapsed relation band identifies the complete reachability preorder
and hence its SCC quotient/partial-order presentation. -/
theorem exactResolutionBand_identifies_reachability
    {Candidate : Type uCandidate}
    (band : ResolutionRelationEvidenceBand Candidate)
    (exactBand : band.lower = band.upper) :
    AllAdmissibleResolutionRelationsAgree band := by
  intro firstRelation secondRelation firstAdmissible secondAdmissible first second
  have firstEq := resolutionRelationAdmissible_eq_lower_of_exactBand
    exactBand firstAdmissible
  have secondEq := resolutionRelationAdmissible_eq_lower_of_exactBand
    exactBand secondAdmissible
  rw [firstEq, secondEq]

namespace FiniteRepeatedPairObservations

variable {Carrier : Type uState}

/-- The same raw repeated observations can bound a candidate-resolution
relation when `Carrier` is the candidate type. -/
def toResolutionEvidenceBand
    (raw : FiniteRepeatedPairObservations Carrier)
    (errorBudget : Nat) : ResolutionRelationEvidenceBand Carrier where
  lower := raw.observationLowerRelation errorBudget
  upper := raw.observationUpperRelation errorBudget
  coherent := raw.observationLower_refines_upper errorBudget

/-- The true candidate-resolution relation lies in the raw observation band
under the same explicit adversarial-count certificate. -/
theorem truth_is_admissible_in_resolutionObservationBand
    (raw : FiniteRepeatedPairObservations Carrier)
    (truth : BinaryRelation Carrier)
    (errorBudget : Nat)
    (certificate : AdversarialErrorCertificate raw truth errorBudget) :
    ResolutionRelationAdmissible
      (raw.toResolutionEvidenceBand errorBudget) truth := by
  constructor
  · intro first second lower
    by_contra notTrue
    have bounded := certificate.false_errors_bounded notTrue
    exact (Nat.not_lt_of_ge bounded) lower.1
  · intro first second truePair
    exact certificate.true_errors_bounded truePair

/-- A certified strict majority collapses the raw candidate-relation band and
therefore identifies its complete reachability preorder and SCC quotient. -/
theorem adversarialMajority_identifies_resolutionReachability
    (raw : FiniteRepeatedPairObservations Carrier)
    (truth : BinaryRelation Carrier)
    (errorBudget : Nat)
    (certificate : AdversarialErrorCertificate raw truth errorBudget)
    (margin : raw.AdversarialMajorityMargin errorBudget) :
    AllAdmissibleResolutionRelationsAgree
      (raw.toResolutionEvidenceBand errorBudget) := by
  rcases raw.observationBand_collapses_to_truth_of_errorCertificate
    truth errorBudget certificate margin with ⟨lowerEq, upperEq⟩
  apply exactResolutionBand_identifies_reachability
  change raw.observationLowerRelation errorBudget =
    raw.observationUpperRelation errorBudget
  exact lowerEq.trans upperEq.symm

end FiniteRepeatedPairObservations

/-- Two admissible resolution relations that disagree on any reachability fact
are a constructive abstention certificate. -/
def ResolutionRelationAmbiguous
    {Candidate : Type uCandidate}
    (band : ResolutionRelationEvidenceBand Candidate) : Prop :=
  ∃ firstRelation secondRelation,
    ResolutionRelationAdmissible band firstRelation ∧
    ResolutionRelationAdmissible band secondRelation ∧
    ∃ first second,
      ¬ (RelationReachable firstRelation first second ↔
        RelationReachable secondRelation first second)

theorem ambiguity_blocks_resolutionIdentification
    {Candidate : Type uCandidate}
    {band : ResolutionRelationEvidenceBand Candidate}
    (ambiguous : ResolutionRelationAmbiguous band) :
    ¬ AllAdmissibleResolutionRelationsAgree band := by
  intro identified
  rcases ambiguous with
    ⟨firstRelation, secondRelation, firstAdmissible, secondAdmissible,
      first, second, disagree⟩
  exact disagree (identified firstAdmissible secondAdmissible first second)

/-- The only two receipt-level outcomes admitted by this formal interface.
The constructors do not claim that every external estimator supplies either
proof automatically. -/
inductive RobustKInferenceVerdict
    {Candidate : Type uCandidate}
    (band : ResolutionRelationEvidenceBand Candidate) : Type (uCandidate + 1)
  | identified : AllAdmissibleResolutionRelationsAgree band →
      RobustKInferenceVerdict band
  | abstain : ResolutionRelationAmbiguous band →
      RobustKInferenceVerdict band

def PairwiseScoreBand.toResolutionEvidenceBand
    {Candidate : Type uCandidate}
    (band : PairwiseScoreBand Candidate) :
    ResolutionRelationEvidenceBand Candidate where
  lower := band.lowerRelation
  upper := band.upperRelation
  coherent := band.lowerRelation_refines_upperRelation

/-- Strict separation of every score interval is sufficient for robust
resolution-preorder/SCC identification. -/
theorem marginSeparated_identifies_resolutionRelation
    {Candidate : Type uCandidate}
    (band : PairwiseScoreBand Candidate)
    (separated : band.MarginSeparated) :
    AllAdmissibleResolutionRelationsAgree band.toResolutionEvidenceBand :=
  exactResolutionBand_identifies_reachability _
    (band.relations_equal_of_marginSeparated separated)

/-! ## Joint profile-and-quotient adjudication -/

/-- A K structure is identified only when both its observational kernel and
its resolution reachability/SCC quotient are invariant over their complete
admissible sets. -/
structure RobustKStructureIdentified
    {State : Type uState}
    {Candidate : Type uCandidate}
    (profileBand : ProfileEvidenceBand State)
    (resolutionBand : ResolutionRelationEvidenceBand Candidate) : Prop where
  profileKernel : AllAdmissibleProfilesHaveSameKernel profileBand
  resolutionReachability :
    AllAdmissibleResolutionRelationsAgree resolutionBand

/-- Evidence bands bound to one actual `KResolutionContext`.  Candidate
profiles and the resolution relation cannot be supplied over unrelated
carriers: both fields depend on the same context, and the context's own
profile/relation must be admissible in their respective bands. -/
structure ContextBoundKInferenceEvidence
    {State : Type uState}
    (context : KResolutionContext State) where
  candidateProfileBand : context.Candidate → ProfileEvidenceBand State
  resolutionBand : ResolutionRelationEvidenceBand context.Candidate
  contextProfile_admissible : ∀ candidate,
    ProfileAdmissible (candidateProfileBand candidate)
      (context.profile candidate)
  contextResolution_admissible :
    ResolutionRelationAdmissible resolutionBand context.ResolutionStep

/-- Weak context-bound co-registration over one carrier and one resolution
context.  The SCC clause is explicit even though it follows from reachability,
so a receipt cannot report a profile kernel from one context and K-level SCCs
from another.  This legacy name does *not* assert that every admissible
resolution edge preserves every admissible profile family; use
`RobustContextualKCoherence` for that stronger claim. -/
structure ContextBoundKStructureIdentified
    {State : Type uState}
    {context : KResolutionContext State}
    (evidence : ContextBoundKInferenceEvidence context) : Prop where
  candidateProfileKernels : ∀ candidate,
    AllAdmissibleProfilesHaveSameKernel
      (evidence.candidateProfileBand candidate)
  resolutionReachability :
    AllAdmissibleResolutionRelationsAgree evidence.resolutionBand
  resolutionSCC :
    AllAdmissibleResolutionRelationsHaveSameSCC evidence.resolutionBand

/-- Honest successor name for the legacy weak record.  It co-registers robust
profile kernels and resolution SCCs but does not yet couple alternative
admissible profiles to alternative admissible resolution relations. -/
abbrev WeakContextBoundKCoregistration
    {State : Type uState}
    {context : KResolutionContext State}
    (evidence : ContextBoundKInferenceEvidence context) :=
  ContextBoundKStructureIdentified evidence

/-- Reachability identification supplies the explicit SCC field, but only for
the same context-bound evidence record. -/
def ContextBoundKStructureIdentified.ofReachability
    {State : Type uState}
    {context : KResolutionContext State}
    {evidence : ContextBoundKInferenceEvidence context}
    (profileKernels : ∀ candidate,
      AllAdmissibleProfilesHaveSameKernel
        (evidence.candidateProfileBand candidate))
    (reachability :
      AllAdmissibleResolutionRelationsAgree evidence.resolutionBand) :
    ContextBoundKStructureIdentified evidence where
  candidateProfileKernels := profileKernels
  resolutionReachability := reachability
  resolutionSCC := reachabilityAgreement_implies_sccAgreement reachability

/-! ## Strong joint profile/relation coherence -/

/-- An alternative complete candidate-profile family is admissible only when
each candidate profile lies in that candidate's band from the same bound
evidence record. -/
def ContextProfileFamilyAdmissible
    {State : Type uState}
    {context : KResolutionContext State}
    (evidence : ContextBoundKInferenceEvidence context)
    (profiles : context.Candidate → DistinctionProfile State) : Prop :=
  ∀ candidate,
    ProfileAdmissible (evidence.candidateProfileBand candidate)
      (profiles candidate)

/-- Joint-admissibility law missing from weak co-registration: for every
admissible profile family and every admissible resolution relation, every
admitted edge must preserve distinctions in the declared direction. -/
def AllAdmissibleCombinationsRespectRefinement
    {State : Type uState}
    {context : KResolutionContext State}
    (evidence : ContextBoundKInferenceEvidence context) : Prop :=
  ∀ ⦃profiles relation⦄,
    ContextProfileFamilyAdmissible evidence profiles →
    ResolutionRelationAdmissible evidence.resolutionBand relation →
    ∀ ⦃source target⦄,
      relation source target →
        AtLeastAsDiscriminating (profiles target) (profiles source)

/-- Every pairwise refinement comparison has the same truth value across all
admissible complete profile families.  This is stronger than equality of their
symmetric observational kernels. -/
def AllAdmissibleProfileFamiliesAgreeOnRefinement
    {State : Type uState}
    {context : KResolutionContext State}
    (evidence : ContextBoundKInferenceEvidence context) : Prop :=
  ∀ ⦃firstProfiles secondProfiles⦄,
    ContextProfileFamilyAdmissible evidence firstProfiles →
    ContextProfileFamilyAdmissible evidence secondProfiles →
    ∀ source target,
      AtLeastAsDiscriminating (firstProfiles target)
          (firstProfiles source) ↔
        AtLeastAsDiscriminating (secondProfiles target)
          (secondProfiles source)

/-- External certificate needed to upgrade weak co-registration to robust
contextual K coherence.  Both laws quantify over the complete admissible sets;
neither is inferred from kernel or SCC equality. -/
structure RobustContextualKCoherenceCertificate
    {State : Type uState}
    {context : KResolutionContext State}
    (evidence : ContextBoundKInferenceEvidence context) : Prop where
  allCombinations_resolutionSound :
    AllAdmissibleCombinationsRespectRefinement evidence
  allRefinementComparisons_invariant :
    AllAdmissibleProfileFamiliesAgreeOnRefinement evidence

/-- Publication-strength contextual K coherence: weak kernel/SCC
co-registration plus sound coupling of every admissible profile/relation
combination and invariant pairwise refinement comparisons. -/
structure RobustContextualKCoherence
    {State : Type uState}
    {context : KResolutionContext State}
    (evidence : ContextBoundKInferenceEvidence context) : Prop where
  weakCoregistration : WeakContextBoundKCoregistration evidence
  allCombinations_resolutionSound :
    AllAdmissibleCombinationsRespectRefinement evidence
  allRefinementComparisons_invariant :
    AllAdmissibleProfileFamiliesAgreeOnRefinement evidence

/-- The explicit certificate, together with weak co-registration, is exactly
the additional evidence needed by this interface for strong coherence. -/
theorem robustContextualKCoherence_of_certificate
    {State : Type uState}
    {context : KResolutionContext State}
    {evidence : ContextBoundKInferenceEvidence context}
    (weak : WeakContextBoundKCoregistration evidence)
    (certificate : RobustContextualKCoherenceCertificate evidence) :
    RobustContextualKCoherence evidence where
  weakCoregistration := weak
  allCombinations_resolutionSound :=
    certificate.allCombinations_resolutionSound
  allRefinementComparisons_invariant :=
    certificate.allRefinementComparisons_invariant

/-- The source context itself is one admissible profile/relation combination.
This theorem exhibits that instance under the same supplied strong certificate
used for all alternatives. -/
theorem sourceContext_instance_of_robustCertificate
    {State : Type uState}
    {context : KResolutionContext State}
    {evidence : ContextBoundKInferenceEvidence context}
    (weak : WeakContextBoundKCoregistration evidence)
    (certificate : RobustContextualKCoherenceCertificate evidence) :
    ContextProfileFamilyAdmissible evidence context.profile ∧
      ResolutionRelationAdmissible evidence.resolutionBand
        context.ResolutionStep ∧
      ∀ ⦃source target⦄,
        context.ResolutionStep source target →
          AtLeastAsDiscriminating (context.profile target)
            (context.profile source) := by
  let coherence : RobustContextualKCoherence evidence :=
    robustContextualKCoherence_of_certificate weak certificate
  refine ⟨evidence.contextProfile_admissible,
    evidence.contextResolution_admissible, ?_⟩
  intro source target edge
  exact coherence.allCombinations_resolutionSound
    evidence.contextProfile_admissible
    evidence.contextResolution_admissible edge

/-- The context's declared resolution steps retain the context's own profiles;
this is the cross-role coherence law inherited by every bound evidence record. -/
theorem ContextBoundKInferenceEvidence.context_resolution_preserves_profiles
    {State : Type uState}
    {context : KResolutionContext State}
    (evidence : ContextBoundKInferenceEvidence context)
    {source target : context.Candidate}
    (step : context.ResolutionStep source target) :
    AtLeastAsDiscriminating (context.profile target)
      (context.profile source) :=
  context.resolutionStep_sound step

def RobustKStructureAmbiguous
    {State : Type uState}
    {Candidate : Type uCandidate}
    (profileBand : ProfileEvidenceBand State)
    (resolutionBand : ResolutionRelationEvidenceBand Candidate) : Prop :=
  ProfileKernelAmbiguous profileBand ∨
    ResolutionRelationAmbiguous resolutionBand

theorem robustKStructureAmbiguity_blocks_identification
    {State : Type uState}
    {Candidate : Type uCandidate}
    {profileBand : ProfileEvidenceBand State}
    {resolutionBand : ResolutionRelationEvidenceBand Candidate}
    (ambiguous : RobustKStructureAmbiguous profileBand resolutionBand) :
    ¬ RobustKStructureIdentified profileBand resolutionBand := by
  intro identified
  rcases ambiguous with profileAmbiguous | resolutionAmbiguous
  · exact profileAmbiguity_blocks_kernelIdentification profileAmbiguous
      identified.profileKernel
  · exact ambiguity_blocks_resolutionIdentification resolutionAmbiguous
      identified.resolutionReachability

inductive RobustKStructureVerdict
    {State : Type uState}
    {Candidate : Type uCandidate}
    (profileBand : ProfileEvidenceBand State)
    (resolutionBand : ResolutionRelationEvidenceBand Candidate) :
    Type (max uState uCandidate) where
  | identified : RobustKStructureIdentified profileBand resolutionBand →
      RobustKStructureVerdict profileBand resolutionBand
  | abstain : RobustKStructureAmbiguous profileBand resolutionBand →
      RobustKStructureVerdict profileBand resolutionBand

/-- One separated pairwise score surface can identify both roles when the
scientific design intentionally uses it for both profile and resolution
evidence.  Other designs must provide their two bands separately. -/
theorem marginSeparated_identifies_jointKStructure
    {Carrier : Type uState}
    (band : PairwiseScoreBand Carrier)
    (separated : band.MarginSeparated) :
    RobustKStructureIdentified band.toProfileEvidenceBand
      band.toResolutionEvidenceBand where
  profileKernel := band.marginSeparated_identifies_profileKernel separated
  resolutionReachability :=
    marginSeparated_identifies_resolutionRelation band separated

/-! ## A finite ambiguity witness -/

def emptyBoolResolution : BinaryRelation Bool := fun _ _ => False

def falseToTrueResolution : BinaryRelation Bool :=
  fun source target => source = false ∧ target = true

def ambiguousBoolResolutionBand : ResolutionRelationEvidenceBand Bool where
  lower := emptyBoolResolution
  upper := falseToTrueResolution
  coherent := by
    intro source target edge
    exact False.elim edge

theorem emptyRelationReachable_iff_eq
    {Carrier : Type uCandidate}
    (first second : Carrier) :
    RelationReachable (fun _ _ => False) first second ↔ first = second := by
  constructor
  · intro path
    induction path with
    | root => rfl
    | tail previous edge inductionHypothesis => exact False.elim edge
  · intro equal
    subst second
    exact .root

theorem emptyBoolResolution_is_admissible :
    ResolutionRelationAdmissible ambiguousBoolResolutionBand
      emptyBoolResolution := by
  constructor
  · intro source target edge
    exact edge
  · exact ambiguousBoolResolutionBand.coherent

theorem falseToTrueResolution_is_admissible :
    ResolutionRelationAdmissible ambiguousBoolResolutionBand
      falseToTrueResolution := by
  constructor
  · exact ambiguousBoolResolutionBand.coherent
  · intro source target edge
    exact edge

/-- The evidence band admits both an empty preorder generator and a one-edge
generator.  Their reachability differs, so choosing either K poset would be an
unsupported point-estimate promotion. -/
theorem ambiguousBoolBand_requires_abstention :
    ResolutionRelationAmbiguous ambiguousBoolResolutionBand := by
  refine ⟨emptyBoolResolution, falseToTrueResolution,
    emptyBoolResolution_is_admissible,
    falseToTrueResolution_is_admissible, false, true, ?_⟩
  intro sameReachability
  have upperReachable :
      RelationReachable falseToTrueResolution false true :=
    .tail .root ⟨rfl, rfl⟩
  have lowerReachable := sameReachability.2 upperReachable
  have falseEqTrue : false = true :=
    (emptyRelationReachable_iff_eq false true).1 lowerReachable
  exact Bool.false_ne_true falseEqTrue

def ambiguousBoolInferenceVerdict :
    RobustKInferenceVerdict ambiguousBoolResolutionBand :=
  .abstain ambiguousBoolBand_requires_abstention

def exactEmptyBoolProfileBand : ProfileEvidenceBand Bool where
  lower := fun _ _ => False
  upper := fun _ _ => False
  coherent := by
    intro first second edge
    exact edge

def ambiguousBoolKStructureVerdict :
    RobustKStructureVerdict exactEmptyBoolProfileBand
      ambiguousBoolResolutionBand :=
  .abstain (Or.inr ambiguousBoolBand_requires_abstention)

/-! ## Weak co-registration is not joint contextual coherence -/

/-- One oriented distinction on the Boolean carrier. -/
def forwardOnlyBoolProfile : DistinctionProfile Bool :=
  fun first second => first = false ∧ second = true

/-- The opposite oriented distinction on the same carrier. -/
def backwardOnlyBoolProfile : DistinctionProfile Bool :=
  fun first second => first = true ∧ second = false

/-- Both oriented distinctions, but no diagonal distinction. -/
def unequalBoolProfile : DistinctionProfile Bool :=
  fun first second => first ≠ second

def forwardOrientationProfileBand : ProfileEvidenceBand Bool where
  lower := forwardOnlyBoolProfile
  upper := unequalBoolProfile
  coherent := by
    intro first second edge
    rcases edge with ⟨rfl, rfl⟩
    exact Bool.false_ne_true

def backwardOrientationProfileBand : ProfileEvidenceBand Bool where
  lower := backwardOnlyBoolProfile
  upper := unequalBoolProfile
  coherent := by
    intro first second edge
    rcases edge with ⟨rfl, rfl⟩
    exact fun equal => Bool.false_ne_true equal.symm

/-- Every admissible profile in the forward-orientation band has equality as
its symmetric kernel, even though its reverse oriented distinction may vary. -/
theorem forwardOrientationProfileBand_kernel_iff_eq
    {profile : DistinctionProfile Bool}
    (admissible : ProfileAdmissible forwardOrientationProfileBand profile)
    (first second : Bool) :
    ProfileKernel profile first second ↔ first = second := by
  cases first <;> cases second
  · have noDiagonal : ¬ profile false false := by
      intro edge
      have outsideUpper := admissible.2 edge
      exact outsideUpper rfl
    simp [ProfileKernel, noDiagonal]
  · have forward : profile false true := by
      apply admissible.1
      exact ⟨rfl, rfl⟩
    simp [ProfileKernel, forward]
  · have forward : profile false true := by
      apply admissible.1
      exact ⟨rfl, rfl⟩
    simp [ProfileKernel, forward]
  · have noDiagonal : ¬ profile true true := by
      intro edge
      have outsideUpper := admissible.2 edge
      exact outsideUpper rfl
    simp [ProfileKernel, noDiagonal]

/-- Every admissible profile in the backward-orientation band has the same
symmetric kernel, for the analogous reason. -/
theorem backwardOrientationProfileBand_kernel_iff_eq
    {profile : DistinctionProfile Bool}
    (admissible : ProfileAdmissible backwardOrientationProfileBand profile)
    (first second : Bool) :
    ProfileKernel profile first second ↔ first = second := by
  cases first <;> cases second
  · have noDiagonal : ¬ profile false false := by
      intro edge
      have outsideUpper := admissible.2 edge
      exact outsideUpper rfl
    simp [ProfileKernel, noDiagonal]
  · have backward : profile true false := by
      apply admissible.1
      exact ⟨rfl, rfl⟩
    simp [ProfileKernel, backward]
  · have backward : profile true false := by
      apply admissible.1
      exact ⟨rfl, rfl⟩
    simp [ProfileKernel, backward]
  · have noDiagonal : ¬ profile true true := by
      intro edge
      have outsideUpper := admissible.2 edge
      exact outsideUpper rfl
    simp [ProfileKernel, noDiagonal]

theorem forwardOrientationProfileBand_identifies_kernel :
    AllAdmissibleProfilesHaveSameKernel
      forwardOrientationProfileBand := by
  intro firstProfile secondProfile firstAdmissible secondAdmissible first second
  rw [forwardOrientationProfileBand_kernel_iff_eq firstAdmissible,
    forwardOrientationProfileBand_kernel_iff_eq secondAdmissible]

theorem backwardOrientationProfileBand_identifies_kernel :
    AllAdmissibleProfilesHaveSameKernel
      backwardOrientationProfileBand := by
  intro firstProfile secondProfile firstAdmissible secondAdmissible first second
  rw [backwardOrientationProfileBand_kernel_iff_eq firstAdmissible,
    backwardOrientationProfileBand_kernel_iff_eq secondAdmissible]

/-- The source context chooses a sound forward refinement: its target profile
contains both orientations while its source contains only the forward one. -/
def weakCoregistrationBoolProfiles :
    Bool → DistinctionProfile Bool
  | false => forwardOnlyBoolProfile
  | true => unequalBoolProfile

/-- An alternative admissible family reverses the directional comparison
without changing either candidate's symmetric observational kernel. -/
def weakCoregistrationAlternativeBoolProfiles :
    Bool → DistinctionProfile Bool
  | false => unequalBoolProfile
  | true => backwardOnlyBoolProfile

def weakCoregistrationBoolContext : KResolutionContext Bool where
  Candidate := Bool
  profile := weakCoregistrationBoolProfiles
  ResolutionStep := falseToTrueResolution
  resolutionStep_sound := by
    intro source target edge
    rcases edge with ⟨rfl, rfl⟩
    intro first second distinguished
    rcases distinguished with ⟨rfl, rfl⟩
    exact Bool.false_ne_true

def weakCoregistrationBoolProfileBand :
    Bool → ProfileEvidenceBand Bool
  | false => forwardOrientationProfileBand
  | true => backwardOrientationProfileBand

def exactFalseToTrueResolutionBand : ResolutionRelationEvidenceBand Bool where
  lower := falseToTrueResolution
  upper := falseToTrueResolution
  coherent := by
    intro source target edge
    exact edge

def weakCoregistrationBoolEvidence :
    ContextBoundKInferenceEvidence weakCoregistrationBoolContext where
  candidateProfileBand := weakCoregistrationBoolProfileBand
  resolutionBand := exactFalseToTrueResolutionBand
  contextProfile_admissible := by
    intro candidate
    cases candidate with
    | false =>
        constructor
        · exact atLeastAsDiscriminating_refl _
        · exact forwardOrientationProfileBand.coherent
    | true =>
        constructor
        · exact backwardOrientationProfileBand.coherent
        · exact atLeastAsDiscriminating_refl _
  contextResolution_admissible := by
    constructor <;> intro source target edge <;> exact edge

def weakCoregistrationBoolWitness :
    WeakContextBoundKCoregistration weakCoregistrationBoolEvidence :=
  ContextBoundKStructureIdentified.ofReachability
    (evidence := weakCoregistrationBoolEvidence)
    (by
      intro candidate
      cases candidate with
      | false => exact forwardOrientationProfileBand_identifies_kernel
      | true => exact backwardOrientationProfileBand_identifies_kernel)
    (exactResolutionBand_identifies_reachability
      exactFalseToTrueResolutionBand rfl)

theorem weakCoregistrationAlternativeBoolProfiles_admissible :
    ContextProfileFamilyAdmissible weakCoregistrationBoolEvidence
      weakCoregistrationAlternativeBoolProfiles := by
  intro candidate
  cases candidate with
  | false =>
      constructor
      · exact forwardOrientationProfileBand.coherent
      · exact atLeastAsDiscriminating_refl _
  | true =>
      constructor
      · exact atLeastAsDiscriminating_refl _
      · exact backwardOrientationProfileBand.coherent

/-- The exact admitted edge is sound for the source context but not for the
alternative admissible family.  Thus separate kernel and SCC invariance do not
imply the joint profile/relation law. -/
theorem weakCoregistrationBool_not_allCombinationsRespectRefinement :
    ¬ AllAdmissibleCombinationsRespectRefinement
      weakCoregistrationBoolEvidence := by
  intro joint
  have edge : weakCoregistrationBoolContext.ResolutionStep false true :=
    ⟨rfl, rfl⟩
  have preserves := joint
    weakCoregistrationAlternativeBoolProfiles_admissible
    weakCoregistrationBoolEvidence.contextResolution_admissible edge
  have sourceDistinction :
      weakCoregistrationAlternativeBoolProfiles false false true :=
    Bool.false_ne_true
  have impossible := preserves sourceDistinction
  simpa [weakCoregistrationAlternativeBoolProfiles,
    backwardOnlyBoolProfile] using impossible

/-- Pairwise refinement truth also changes between two admissible profile
families even though every candidate's symmetric kernel is invariant. -/
theorem weakCoregistrationBool_not_refinementComparisonInvariant :
    ¬ AllAdmissibleProfileFamiliesAgreeOnRefinement
      weakCoregistrationBoolEvidence := by
  intro invariant
  have comparison := invariant
    weakCoregistrationBoolEvidence.contextProfile_admissible
    weakCoregistrationAlternativeBoolProfiles_admissible false true
  have sourceComparison :
      AtLeastAsDiscriminating
        (weakCoregistrationBoolProfiles true)
        (weakCoregistrationBoolProfiles false) :=
    weakCoregistrationBoolContext.resolutionStep_sound ⟨rfl, rfl⟩
  have alternativeComparison := comparison.1 sourceComparison
  have sourceDistinction :
      weakCoregistrationAlternativeBoolProfiles false false true :=
    Bool.false_ne_true
  have impossible := alternativeComparison sourceDistinction
  simpa [weakCoregistrationAlternativeBoolProfiles,
    backwardOnlyBoolProfile] using impossible

theorem weakCoregistrationBool_not_robustContextualKCoherence :
    ¬ RobustContextualKCoherence weakCoregistrationBoolEvidence := by
  intro coherence
  exact weakCoregistrationBool_not_allCombinationsRespectRefinement
    coherence.allCombinations_resolutionSound

/-- Concrete P1 boundary: weak co-registration is inhabited while both strong
joint-coherence clauses fail. -/
theorem weakKernelAndSCCCoregistration_is_insufficient :
    WeakContextBoundKCoregistration weakCoregistrationBoolEvidence ∧
      ¬ RobustContextualKCoherence weakCoregistrationBoolEvidence ∧
      ¬ AllAdmissibleCombinationsRespectRefinement
        weakCoregistrationBoolEvidence ∧
      ¬ AllAdmissibleProfileFamiliesAgreeOnRefinement
        weakCoregistrationBoolEvidence :=
  ⟨weakCoregistrationBoolWitness,
    weakCoregistrationBool_not_robustContextualKCoherence,
    weakCoregistrationBool_not_allCombinationsRespectRefinement,
    weakCoregistrationBool_not_refinementComparisonInvariant⟩

end OCKIndividuationMSpaceComposition
