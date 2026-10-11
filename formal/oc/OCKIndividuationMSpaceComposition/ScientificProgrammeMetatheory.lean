import Mathlib.Order.Basic

namespace OCKIndividuationMSpaceComposition

/-!
# Scientific programme metatheory

Scientific readiness is a conjunction of independently auditable dimensions.
A failed empirical hypothesis is terminal only for that hypothesis version;
programme continuity requires a new hypothesis with an explanatory revision
witness and a new prospective falsifier.
-/

structure EvidenceProfile where
  formal : Nat
  identifiability : Nat
  empirical : Nat
  transfer : Nat
  reproducibility : Nat
  utility : Nat
  deriving DecidableEq

def EvidenceProfile.Meets (observed required : EvidenceProfile) : Prop :=
  required.formal ≤ observed.formal ∧
  required.identifiability ≤ observed.identifiability ∧
  required.empirical ≤ observed.empirical ∧
  required.transfer ≤ observed.transfer ∧
  required.reproducibility ≤ observed.reproducibility ∧
  required.utility ≤ observed.utility

def JournalReady (observed required : EvidenceProfile) : Prop :=
  observed.Meets required

theorem journal_ready_iff_all_dimensions_meet
    (observed required : EvidenceProfile) :
    JournalReady observed required ↔
      required.formal ≤ observed.formal ∧
      required.identifiability ≤ observed.identifiability ∧
      required.empirical ≤ observed.empirical ∧
      required.transfer ≤ observed.transfer ∧
      required.reproducibility ≤ observed.reproducibility ∧
      required.utility ≤ observed.utility :=
  Iff.rfl

theorem journal_ready_implies_formal_support
    {observed required : EvidenceProfile}
    (ready : JournalReady observed required) :
    required.formal ≤ observed.formal :=
  ready.1

theorem journal_ready_implies_empirical_support
    {observed required : EvidenceProfile}
    (ready : JournalReady observed required) :
    required.empirical ≤ observed.empirical :=
  ready.2.2.1

theorem journal_ready_implies_transfer_support
    {observed required : EvidenceProfile}
    (ready : JournalReady observed required) :
    required.transfer ≤ observed.transfer :=
  ready.2.2.2.1

theorem evidence_upgrade_is_monotone
    {earlier later required : EvidenceProfile}
    (upgrade : earlier.Meets later)
    (ready : JournalReady later required) :
    JournalReady earlier required := by
  exact ⟨
    Nat.le_trans ready.1 upgrade.1,
    Nat.le_trans ready.2.1 upgrade.2.1,
    Nat.le_trans ready.2.2.1 upgrade.2.2.1,
    Nat.le_trans ready.2.2.2.1 upgrade.2.2.2.1,
    Nat.le_trans ready.2.2.2.2.1 upgrade.2.2.2.2.1,
    Nat.le_trans ready.2.2.2.2.2 upgrade.2.2.2.2.2
  ⟩

inductive HypothesisDisposition where
  | active
  | supported
  | refuted
  | underidentified
  deriving DecidableEq

structure RevisionWitness (Hypothesis Failure Test : Type) where
  predecessor : Hypothesis
  observedFailure : Failure
  successor : Hypothesis
  explanation : Prop
  explanationEstablished : explanation
  prospectiveFalsifier : Test

def RefutationClosed
    {Hypothesis Failure Test : Type}
    (disposition : Hypothesis → HypothesisDisposition)
    (revision : Hypothesis → Failure → Option (RevisionWitness Hypothesis Failure Test)) : Prop :=
  ∀ hypothesis, disposition hypothesis = HypothesisDisposition.refuted →
    ∀ failure, ∃ witness, revision hypothesis failure = some witness

theorem refutation_requires_a_registered_revision
    {Hypothesis Failure Test : Type}
    {disposition : Hypothesis → HypothesisDisposition}
    {revision : Hypothesis → Failure → Option (RevisionWitness Hypothesis Failure Test)}
    (closed : RefutationClosed disposition revision)
    {hypothesis : Hypothesis}
    (refuted : disposition hypothesis = HypothesisDisposition.refuted)
    (failure : Failure) :
    ∃ witness, revision hypothesis failure = some witness :=
  closed hypothesis refuted failure

end OCKIndividuationMSpaceComposition
