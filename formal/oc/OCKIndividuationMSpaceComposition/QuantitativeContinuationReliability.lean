import OCKIndividuationMSpaceComposition.ContinuationResearchClosure

namespace OCKIndividuationMSpaceComposition

/-!
# Quantitative reliability of an already typed continuation witness

This module does not turn a score into identity.  It quantifies whether the
evidence needed to observe at least one admissible witness survives a declared
finite stochastic experiment.  Independence is part of the model contract,
not a theorem inferred from edge marginals.
-/

/-- An exact non-normalized rational mass.  Well-formedness (`numerator ≤
denominator` and positive denominator) is a separate input contract. -/
structure RationalMass where
  numerator : Nat
  denominator : Nat
  deriving DecidableEq, Repr

namespace RationalMass

def one : RationalMass := ⟨1, 1⟩

def zero : RationalMass := ⟨0, 1⟩

def mul (left right : RationalMass) : RationalMass :=
  ⟨left.numerator * right.numerator,
    left.denominator * right.denominator⟩

end RationalMass

/-- Product prediction for a serial witness under explicitly independent edge
retention experiments. -/
def independentSeriesMass : List RationalMass → RationalMass
  | [] => RationalMass.one
  | head :: tail => head.mul (independentSeriesMass tail)

theorem independentSeriesMass_nil :
    independentSeriesMass [] = RationalMass.one := rfl

theorem independentSeriesMass_cons (head : RationalMass) (tail : List RationalMass) :
    independentSeriesMass (head :: tail) =
      head.mul (independentSeriesMass tail) := rfl

theorem zero_retention_annihilates_serial_numerator (tail : List RationalMass) :
    (independentSeriesMass (RationalMass.zero :: tail)).numerator = 0 := by
  simp [independentSeriesMass, RationalMass.zero, RationalMass.mul]

/-- Inclusion-exclusion for two independent alternative witness events. -/
def independentParallelMass (left right : RationalMass) : RationalMass :=
  ⟨left.numerator * right.denominator +
      right.numerator * left.denominator -
      left.numerator * right.numerator,
    left.denominator * right.denominator⟩

def axeSerialMass : RationalMass :=
  independentSeriesMass [⟨98, 100⟩, ⟨95, 100⟩]

/-- The reassembled object has the same terminal material projection in the
axe countermodel, but no admissible historical witness path. -/
def reassemblyNoPathMass : RationalMass := RationalMass.zero

theorem axe_serial_continuation_prediction :
    axeSerialMass = ⟨9310, 10000⟩ := rfl

def axeGovernanceMass : RationalMass :=
  independentSeriesMass [⟨98, 100⟩, ⟨95, 100⟩, ⟨99, 100⟩, ⟨97, 100⟩]

theorem axe_governance_prediction :
    axeGovernanceMass = ⟨89403930, 100000000⟩ := rfl

def disjointTwoPathMass : RationalMass :=
  independentParallelMass
    (independentSeriesMass [⟨9, 10⟩, ⟨9, 10⟩])
    (independentSeriesMass [⟨9, 10⟩, ⟨9, 10⟩])

theorem disjoint_two_path_prediction :
    disjointTwoPathMass = ⟨9639, 10000⟩ := rfl

/-- Probability that at least one of two task-equivalent aliases remains
evidenced. -/
def taskEquivalentAliasResolutionMass : RationalMass :=
  independentParallelMass ⟨9, 10⟩ ⟨4, 5⟩

theorem task_equivalent_alias_resolution_prediction :
    taskEquivalentAliasResolutionMass = ⟨49, 50⟩ := rfl

/-- Two aliases share a 0.9 provenance trunk and have 0.8 and 0.7 leaves. -/
def sharedProvenanceAliasResolutionMass : RationalMass :=
  RationalMass.mul ⟨9, 10⟩
    (independentParallelMass ⟨4, 5⟩ ⟨7, 10⟩)

def sharedProvenanceAmbiguityPairMass : RationalMass :=
  independentSeriesMass [⟨9, 10⟩, ⟨4, 5⟩, ⟨7, 10⟩]

theorem shared_provenance_alias_resolution_prediction :
    sharedProvenanceAliasResolutionMass = ⟨423, 500⟩ := rfl

theorem shared_provenance_ambiguity_pair_prediction :
    sharedProvenanceAmbiguityPairMass = ⟨252, 500⟩ := rfl

def sharedTrunkMass : RationalMass :=
  RationalMass.mul ⟨95, 100⟩
    (independentParallelMass ⟨9, 10⟩ ⟨9, 10⟩)

def naiveIndependentSharedPathMass : RationalMass :=
  independentParallelMass ⟨855, 1000⟩ ⟨855, 1000⟩

theorem shared_trunk_prediction :
    sharedTrunkMass = ⟨9405, 10000⟩ := rfl

theorem naive_path_independence_overestimates_shared_trunk :
    sharedTrunkMass.numerator * naiveIndependentSharedPathMass.denominator <
      naiveIndependentSharedPathMass.numerator * sharedTrunkMass.denominator := by
  decide

/-- Governance acceptance is a refinement of witness retention. -/
def retainedEverywhere (edgeTrace : List Bool) : Bool :=
  edgeTrace.all id

def governanceAccepted
    (edgeTrace : List Bool)
    (valid notRevoked noTrigger invariantPreserved : Bool) : Bool :=
  retainedEverywhere edgeTrace &&
    (valid && (notRevoked && (noTrigger && invariantPreserved)))

theorem governance_acceptance_implies_witness_retention
    {edgeTrace : List Bool}
    {valid notRevoked noTrigger invariantPreserved : Bool}
    (accepted :
      governanceAccepted edgeTrace valid notRevoked noTrigger invariantPreserved = true) :
    retainedEverywhere edgeTrace = true := by
  simp only [governanceAccepted, Bool.and_eq_true] at accepted
  exact accepted.1

/-! ## Dependence no-go theorem

Both finite experiments below have edge marginals 1/2.  In the correlated
experiment the serial witness survives with mass 1/2; in the anticorrelated
experiment it never survives.  Marginals therefore do not determine the path
probability without a dependence contract.
-/

structure TwoEdgeOutcome where
  first : Bool
  second : Bool
  deriving DecidableEq, Repr

def firstSuccessCount : List TwoEdgeOutcome → Nat
  | [] => 0
  | outcome :: tail => (if outcome.first then 1 else 0) + firstSuccessCount tail

def secondSuccessCount : List TwoEdgeOutcome → Nat
  | [] => 0
  | outcome :: tail => (if outcome.second then 1 else 0) + secondSuccessCount tail

def serialSuccessCount : List TwoEdgeOutcome → Nat
  | [] => 0
  | outcome :: tail =>
      (if outcome.first && outcome.second then 1 else 0) + serialSuccessCount tail

def correlatedOutcomes : List TwoEdgeOutcome :=
  [⟨true, true⟩, ⟨false, false⟩]

def anticorrelatedOutcomes : List TwoEdgeOutcome :=
  [⟨true, false⟩, ⟨false, true⟩]

theorem equal_edge_marginals_do_not_determine_serial_probability :
    firstSuccessCount correlatedOutcomes = firstSuccessCount anticorrelatedOutcomes ∧
    secondSuccessCount correlatedOutcomes = secondSuccessCount anticorrelatedOutcomes ∧
    serialSuccessCount correlatedOutcomes ≠ serialSuccessCount anticorrelatedOutcomes := by
  decide

/-- Equal endpoint projections remain compatible with explicitly different
numerical witness reliabilities: the historical axe has mass 0.931, whereas
the no-path reassembly has mass zero. -/
theorem endpoint_projection_does_not_determine_quantitative_reliability :
    axePhysicalProjection .a2 = axePhysicalProjection .b ∧
    axeSerialMass = ⟨9310, 10000⟩ ∧
    reassemblyNoPathMass = ⟨0, 1⟩ ∧
    axeSerialMass.numerator * reassemblyNoPathMass.denominator ≠
      reassemblyNoPathMass.numerator * axeSerialMass.denominator := by
  exact ⟨rfl, rfl, rfl, by decide⟩

end OCKIndividuationMSpaceComposition
