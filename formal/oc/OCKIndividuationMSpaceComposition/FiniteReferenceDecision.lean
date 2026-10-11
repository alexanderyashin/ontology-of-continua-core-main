import OCKIndividuationMSpaceComposition.ContextualReferenceResolution

namespace OCKIndividuationMSpaceComposition

universe uCandidate

/-!
# Finite reference decision and the infinite-evidence boundary

The finite resolver is exact on its declared universe.  The second half gives
a constructive counterexample to any claim that a fixed finite observation
prefix decides arbitrary future evidence.
-/

theorem finiteCandidateSet_length_le_universe
    {Signal Candidate Task Frame Projection Constraint : Type}
    (query : ReferenceQuery Signal Candidate Task Frame Projection Constraint)
    [DecidablePred (CandidateSatisfies query)]
    (candidateUniverse : List Candidate) :
    (finiteCandidateSet query candidateUniverse).length ≤ candidateUniverse.length := by
  simpa [finiteCandidateSet] using
    List.length_filter_le (p := CandidateSatisfies query) candidateUniverse

/-- At most one constraint check per candidate is needed by the abstract
finite scan; concrete multi-constraint costs multiply this bound by the number
of active constraints. -/
def finiteCandidateEvaluationBound (candidateUniverseSize : Nat) : Nat :=
  candidateUniverseSize

theorem finiteCandidateEvaluationBound_exact (candidateUniverseSize : Nat) :
    finiteCandidateEvaluationBound candidateUniverseSize = candidateUniverseSize := rfl

structure RepairCandidate where
  cost : Nat
  resolves : Bool
  deriving DecidableEq, Repr

def IsMinimalRepair (searchSpace : List RepairCandidate) (candidate : RepairCandidate) : Prop :=
  candidate ∈ searchSpace ∧ candidate.resolves = true ∧
    ∀ alternative, alternative ∈ searchSpace → alternative.resolves = true →
      candidate.cost ≤ alternative.cost

theorem minimalRepair_is_resolving
    {searchSpace : List RepairCandidate}
    {candidate : RepairCandidate}
    (minimal : IsMinimalRepair searchSpace candidate) :
    candidate.resolves = true :=
  minimal.2.1

def finiteEvidenceExists {n : Nat} (evidence : Fin n → Bool) : Bool :=
  decide (∃ index, evidence index = true)

theorem finiteEvidenceExists_correct
    {n : Nat} (evidence : Fin n → Bool) :
    finiteEvidenceExists evidence = true ↔ ∃ index, evidence index = true := by
  simp [finiteEvidenceExists]

def delayedEvidence (cutoff index : Nat) : Bool :=
  decide (index = cutoff)

def emptyEvidence (_ : Nat) : Bool := false

theorem delayed_and_empty_agree_before_cutoff (cutoff : Nat) :
    ∀ index, index < cutoff →
      delayedEvidence cutoff index = emptyEvidence index := by
  intro index before
  simp [delayedEvidence, emptyEvidence, Nat.ne_of_lt before]

theorem delayedEvidence_eventually_true (cutoff : Nat) :
    ∃ index, delayedEvidence cutoff index = true := by
  exact ⟨cutoff, by simp [delayedEvidence]⟩

theorem emptyEvidence_never_true :
    ¬ ∃ index, emptyEvidence index = true := by
  simp [emptyEvidence]

/-- For every finite prefix there are indistinguishable streams with opposite
eventual-existence answers.  General resolution therefore needs an oracle,
termination hypothesis or finite bound; the finite resolver cannot be lifted
for free. -/
theorem no_finite_prefix_decides_arbitrary_future_evidence (prefixLength : Nat) :
    ∃ positive negative : Nat → Bool,
      (∀ index, index < prefixLength → positive index = negative index) ∧
      (∃ index, positive index = true) ∧
      ¬ ∃ index, negative index = true := by
  refine ⟨delayedEvidence prefixLength, emptyEvidence, ?_, ?_, ?_⟩
  · exact delayed_and_empty_agree_before_cutoff prefixLength
  · exact delayedEvidence_eventually_true prefixLength
  · exact emptyEvidence_never_true

end OCKIndividuationMSpaceComposition
