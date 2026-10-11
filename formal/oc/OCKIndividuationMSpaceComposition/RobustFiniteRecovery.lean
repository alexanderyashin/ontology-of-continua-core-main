import OCKIndividuationMSpaceComposition.FiniteNoisyIdentifiability

namespace OCKIndividuationMSpaceComposition

universe uObject uTest uOutcome

/-!
# Robust finite recovery by repetition and separated confidence sets

This module adds no empirical or asymptotic claim.  It isolates two finite,
deterministic facts used by the synthetic robust-recovery study.

* Strictly fewer than half of the repeated Boolean outcomes may be wrong at
  every typed test without changing its majority value.  Exact test separation
  then makes the recovered candidate unique.
* A discrepancy confidence set is subsingleton whenever its radius is strictly
  less than half the declared pairwise separation margin.

The two-vote tie at the end witnesses the sharp obstruction at one-half
adversarial contamination.  Exact observational aliases remain impossible by
`exactObservationAlias_no_observation_only_recovery` from the imported module.
-/

/-- Counts of repeated true and false outcomes for one Boolean typed test. -/
structure RepeatedBoolObservation where
  trueVotes : Nat
  falseVotes : Nat

namespace RepeatedBoolObservation

/-- Total number of repetitions represented by the two vote counts. -/
def repetitions (observation : RepeatedBoolObservation) : Nat :=
  observation.trueVotes + observation.falseVotes

/-- Number of repeated outcomes unequal to the declared true Boolean value. -/
def errorVotes
    (observation : RepeatedBoolObservation)
    (truth : Bool) : Nat :=
  if truth then observation.falseVotes else observation.trueVotes

/-- Strict majority decoder; an exact tie is conservatively decoded as false. -/
def majorityDecode (observation : RepeatedBoolObservation) : Bool :=
  decide (observation.falseVotes < observation.trueVotes)

/--
A strict minority of erroneous repetitions is sufficient for exact majority
decoding.  No independence or probability law is used.
-/
theorem majorityDecode_eq_of_strict_minority_errors
    (observation : RepeatedBoolObservation)
    (truth : Bool)
    (errorsAreMinority :
      2 * observation.errorVotes truth < observation.repetitions) :
    observation.majorityDecode = truth := by
  cases truth with
  | false =>
      have trueVotesLess :
          observation.trueVotes < observation.falseVotes := by
        simpa [errorVotes, repetitions, two_mul] using errorsAreMinority
      have notFalseLessTrue :
          ¬ observation.falseVotes < observation.trueVotes :=
        Nat.not_lt.mpr (Nat.le_of_lt trueVotesLess)
      simp [majorityDecode, notFalseLessTrue]
  | true =>
      have falseVotesLess :
          observation.falseVotes < observation.trueVotes := by
        simpa [errorVotes, repetitions, two_mul, Nat.add_comm] using
          errorsAreMinority
      simp [majorityDecode, falseVotesLess]

end RepeatedBoolObservation

/-- Majority signature reconstructed independently at every typed test. -/
def repeatedMajoritySignature
    {Test : Type uTest}
    (measured : Test → RepeatedBoolObservation) : Test → Bool :=
  fun test => (measured test).majorityDecode

/-- Every typed test has strictly fewer erroneous than correct repetitions. -/
def PerTestStrictMinorityErrors
    {Object : Type uObject}
    {Test : Type uTest}
    (family : FiniteTypedTestFamily Object Test Bool)
    (object : Object)
    (measured : Test → RepeatedBoolObservation) : Prop :=
  ∀ test,
    2 * (measured test).errorVotes (family.observe object test) <
      (measured test).repetitions

/-- Per-test strict-minority errors reconstruct the complete true signature. -/
theorem repeatedMajoritySignature_eq_true_signature
    {Object : Type uObject}
    {Test : Type uTest}
    {family : FiniteTypedTestFamily Object Test Bool}
    {object : Object}
    {measured : Test → RepeatedBoolObservation}
    (bounded : PerTestStrictMinorityErrors family object measured) :
    repeatedMajoritySignature measured = family.signature object := by
  funext test
  exact (measured test).majorityDecode_eq_of_strict_minority_errors
    (family.observe object test) (bounded test)

/--
When the declared tests separate candidates, strict-minority repeated errors
leave exactly one candidate with the reconstructed majority signature.
-/
theorem strictMinorityErrors_imply_unique_candidate
    {Object : Type uObject}
    {Test : Type uTest}
    {family : FiniteTypedTestFamily Object Test Bool}
    {object : Object}
    {measured : Test → RepeatedBoolObservation}
    (separates : ExactTestSeparation family)
    (bounded : PerTestStrictMinorityErrors family object measured) :
    ∃! candidate : Object,
      family.signature candidate = repeatedMajoritySignature measured := by
  have trueSignature := repeatedMajoritySignature_eq_true_signature bounded
  refine ⟨object, trueSignature.symm, ?_⟩
  intro candidate candidateSignature
  apply exactTestSeparation_implies_signature_injective separates
  exact candidateSignature.trans trueSignature

/-!
## Deterministic confidence-set consequence of the margin theorem
-/

/-- Candidates inside a declared rational discrepancy radius of a measurement. -/
def RatSignatureConfidenceSet
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    (geometry : RatOutcomeDiscrepancy Outcome)
    (family : FiniteTypedTestFamily Object Test Outcome)
    (measured : Test → Outcome)
    (error : ℚ) : Set Object :=
  {candidate |
    SignatureWithinRatError geometry family candidate measured error}

/-- The true candidate is covered whenever its discrepancy obeys the radius. -/
theorem true_candidate_mem_ratSignatureConfidenceSet
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    {geometry : RatOutcomeDiscrepancy Outcome}
    {family : FiniteTypedTestFamily Object Test Outcome}
    {measured : Test → Outcome}
    {error : ℚ}
    {object : Object}
    (withinRadius :
      SignatureWithinRatError geometry family object measured error) :
    object ∈ RatSignatureConfidenceSet geometry family measured error :=
  withinRadius

/--
Margin strictly greater than twice the radius makes the deterministic
confidence set subsingleton.  Together with true-candidate membership this is
the exact finite unique-recovery condition.
-/
theorem ratSignatureConfidenceSet_subsingleton_of_margin
    {Object : Type uObject}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    [Fintype Test]
    {geometry : RatOutcomeDiscrepancy Outcome}
    {family : FiniteTypedTestFamily Object Test Outcome}
    {measured : Test → Outcome}
    {margin error : ℚ}
    (separated : RatSeparationMargin geometry family margin)
    (strictGap : 2 * error < margin) :
    (RatSignatureConfidenceSet geometry family measured error).Subsingleton := by
  intro first firstCompatible second secondCompatible
  exact margin_gt_twice_error_implies_unique_recovery
    separated strictGap firstCompatible secondCompatible

/-!
## Sharp adversarial obstruction at one half
-/

/-- One true and one false vote: the smallest exact half-contamination tie. -/
def twoVoteTie : RepeatedBoolObservation where
  trueVotes := 1
  falseVotes := 1

/-- The same tied observation is exactly one-half erroneous for either truth. -/
theorem twoVoteTie_is_half_error_for_both_truths :
    2 * twoVoteTie.errorVotes false = twoVoteTie.repetitions ∧
      2 * twoVoteTie.errorVotes true = twoVoteTie.repetitions := by
  decide

/--
No deterministic decoder can assign the same half-corrupted observation to
both possible truths.  Thus the strict inequality in the majority theorem
cannot be weakened to permit the exact one-half boundary uniformly.
-/
theorem no_decoder_recovers_both_truths_at_half_contamination :
    ¬ ∃ recover : RepeatedBoolObservation → Bool,
      recover twoVoteTie = false ∧ recover twoVoteTie = true := by
  rintro ⟨recover, recoversFalse, recoversTrue⟩
  exact Bool.false_ne_true (recoversFalse.symm.trans recoversTrue)

end OCKIndividuationMSpaceComposition
