import OCMaturityCompletionCycle.IdentityAssembly

/-!
# Identity and predictive sufficiency

Identity and prediction are different encoders of the same history domain.
Their exact relationship is kernel inclusion. This module proves that
characterization, factorization on the used identity range, explicit boundary
fixtures, and a finite probability-law witness when sufficiency fails.
-/

namespace OCMaturityCompletionCycle

universe uHistory uOccurrence uIdentity uPredictive

/-- A typed map from histories to their terminal process occurrence. -/
structure HistoryEndpoint
    (History : Type uHistory)
    (Occurrence : Type uOccurrence) where
  endpoint : History → Occurrence

/-- Identity encoder induced by a history endpoint and occurrence assembly. -/
def HistoryEndpoint.identityEncoder
    {History : Type uHistory}
    {Occurrence : Type uOccurrence}
    {Identity : Type uIdentity}
    (historyEndpoint : HistoryEndpoint History Occurrence)
    (assembly : Occurrence → Identity) : History → Identity :=
  fun history => assembly (historyEndpoint.endpoint history)

/-- Equality kernel of an encoder. -/
def EncoderKernel
    {History : Type uHistory}
    {Code : Type uIdentity}
    (encoder : History → Code) : BinaryRelation History :=
  fun first second => encoder first = encoder second

/-- Inclusion of the left encoder kernel in the right encoder kernel. -/
def KernelIncluded
    {History : Type uHistory}
    {LeftCode : Type uIdentity}
    {RightCode : Type uPredictive}
    (left : History → LeftCode)
    (right : History → RightCode) : Prop :=
  RelationRefines (EncoderKernel left) (EncoderKernel right)

/-- Identity is sufficient when equal identity codes force equal future laws. -/
def PredictivelySufficientIdentity
    {History : Type uHistory}
    {Identity : Type uIdentity}
    {Predictive : Type uPredictive}
    (identity : History → Identity)
    (predictive : History → Predictive) : Prop :=
  KernelIncluded identity predictive

/-- Exact bridge: identity and predictive encoders induce the same kernel. -/
def ExactIdentityPredictiveBridge
    {History : Type uHistory}
    {Identity : Type uIdentity}
    {Predictive : Type uPredictive}
    (identity : History → Identity)
    (predictive : History → Predictive) : Prop :=
  ∀ first second,
    identity first = identity second ↔ predictive first = predictive second

theorem predictivelySufficientIdentity_iff_kernelInclusion
    {History : Type uHistory}
    {Identity : Type uIdentity}
    {Predictive : Type uPredictive}
    (identity : History → Identity)
    (predictive : History → Predictive) :
    PredictivelySufficientIdentity identity predictive ↔
      RelationRefines (EncoderKernel identity) (EncoderKernel predictive) := by
  rfl

theorem exactIdentityPredictiveBridge_iff_kernelEquality
    {History : Type uHistory}
    {Identity : Type uIdentity}
    {Predictive : Type uPredictive}
    (identity : History → Identity)
    (predictive : History → Predictive) :
    ExactIdentityPredictiveBridge identity predictive ↔
      ∀ first second,
        EncoderKernel identity first second ↔
          EncoderKernel predictive first second := by
  rfl

theorem exactIdentityPredictiveBridge_iff_mutualKernelInclusion
    {History : Type uHistory}
    {Identity : Type uIdentity}
    {Predictive : Type uPredictive}
    (identity : History → Identity)
    (predictive : History → Predictive) :
    ExactIdentityPredictiveBridge identity predictive ↔
      KernelIncluded identity predictive ∧
        KernelIncluded predictive identity := by
  constructor
  · intro exact
    constructor
    · intro first second sameIdentity
      exact (exact first second).1 sameIdentity
    · intro first second samePrediction
      exact (exact first second).2 samePrediction
  · rintro ⟨forward, backward⟩ first second
    exact ⟨fun sameIdentity => forward sameIdentity,
      fun samePrediction => backward samePrediction⟩

/-- The actually used identity codes, with a witness history for each code. -/
abbrev EncoderUsedRange
    {History : Type uHistory}
    {Code : Type uIdentity}
    (encoder : History → Code) :=
  { code : Code // ∃ history, encoder history = code }

/--
Exact used-range factorization. No arbitrary value outside the used identity
range and no global default future law is assumed.
-/
theorem factorization_on_usedRange_iff_kernelInclusion
    {History : Type uHistory}
    {Identity : Type uIdentity}
    {Predictive : Type uPredictive}
    (identity : History → Identity)
    (predictive : History → Predictive) :
    KernelIncluded identity predictive ↔
      ∃ factor : EncoderUsedRange identity → Predictive,
        ∀ history,
          factor ⟨identity history, ⟨history, rfl⟩⟩ = predictive history := by
  constructor
  · intro sufficient
    classical
    refine ⟨fun code => predictive (Classical.choose code.property), ?_⟩
    intro history
    apply sufficient
    exact Classical.choose_spec
      (show ∃ representative, identity representative = identity history from
        ⟨history, rfl⟩)
  · rintro ⟨factor, factorizes⟩ first second sameIdentity
    have sameRangeCode :
        (⟨identity first, ⟨first, rfl⟩⟩ : EncoderUsedRange identity) =
          ⟨identity second, ⟨second, rfl⟩⟩ := by
      exact Subtype.ext sameIdentity
    calc
      predictive first = factor ⟨identity first, ⟨first, rfl⟩⟩ :=
        (factorizes first).symm
      _ = factor ⟨identity second, ⟨second, rfl⟩⟩ :=
        congrArg factor sameRangeCode
      _ = predictive second := factorizes second

/-- Safe evidence closure: the generated equivalence never merges predictions. -/
def EvidenceGeneratedIdentitySafe
    {History : Type uHistory}
    {Predictive : Type uPredictive}
    (evidence : BinaryRelation History)
    (predictive : History → Predictive) : Prop :=
  ∀ ⦃first second⦄,
    EquivalenceGenerated evidence first second →
      predictive first = predictive second

/--
Evidence-generated quotient identity is predictively safe exactly when each
raw evidence edge already preserves the predictive law.
-/
theorem evidenceGeneratedIdentitySafe_iff_edgesPreservePrediction
    {History : Type uHistory}
    {Predictive : Type uPredictive}
    (evidence : BinaryRelation History)
    (predictive : History → Predictive) :
    EvidenceGeneratedIdentitySafe evidence predictive ↔
      ∀ ⦃first second⦄,
        evidence first second → predictive first = predictive second := by
  constructor
  · intro safe first second edge
    exact safe (.ofEvidence edge)
  · intro edgeSafe first second generated
    induction generated with
    | ofEvidence edge => exact edgeSafe edge
    | refl occurrence => rfl
    | symm _ inductionHypothesis => exact inductionHypothesis.symm
    | trans _ _ firstHypothesis secondHypothesis =>
        exact firstHypothesis.trans secondHypothesis

/--
A Bernoulli conditional law represented by natural weights with one common,
positive denominator. Equality of `trueWeight` is equality of the full law.
This representation avoids importing analytic probability machinery into the
finite characterization layer.
-/
structure PredictiveKernel (History : Type uHistory) where
  denominator : Nat
  denominatorPositive : 0 < denominator
  trueWeight : History → Nat
  trueWeightBounded : ∀ history, trueWeight history ≤ denominator

/-- The Boolean coordinate tested in a Bernoulli future law. -/
structure FutureTest where
  outcome : Bool

def FutureTest.observeWeight
    {History : Type uHistory}
    (test : FutureTest)
    (kernel : PredictiveKernel History)
    (history : History) : Nat :=
  if test.outcome then kernel.trueWeight history
  else kernel.denominator - kernel.trueWeight history

/-- Zero-one loss for an exact report of the Bernoulli true-event weight. -/
def ExactReportLoss (reported truth : Nat) : Nat :=
  if reported = truth then 0 else 1

theorem exactReportLoss_eq_one_of_ne
    {reported truth : Nat}
    (different : reported ≠ truth) :
    ExactReportLoss reported truth = 1 := by
  simp [ExactReportLoss, different]

/-- Any one shared report is wrong for at least one of two distinct laws. -/
theorem sharedReport_misses_at_least_one
    {left right : Nat}
    (different : left ≠ right) :
    ∀ reported,
      ExactReportLoss reported left = 1 ∨
        ExactReportLoss reported right = 1 := by
  intro reported
  by_cases matchesLeft : reported = left
  · right
    apply exactReportLoss_eq_one_of_ne
    intro matchesRight
    apply different
    exact matchesLeft.symm.trans matchesRight
  · left
    exact exactReportLoss_eq_one_of_ne matchesLeft

/-- Failure of kernel inclusion exposes two same-identity, distinct laws. -/
theorem predictive_insufficiency_yields_weightWitness
    {History : Type uHistory}
    {Identity : Type uIdentity}
    (identity : History → Identity)
    (kernel : PredictiveKernel History)
    (insufficient :
      ¬ PredictivelySufficientIdentity identity kernel.trueWeight) :
    ∃ first second,
      identity first = identity second ∧
        kernel.trueWeight first ≠ kernel.trueWeight second := by
  classical
  by_contra noWitness
  apply insufficient
  intro first second sameIdentity
  by_contra different
  apply noWitness
  exact ⟨first, second, sameIdentity, different⟩

/-- The true-event experiment distinguishes the witness laws. -/
theorem predictive_insufficiency_yields_futureTest
    {History : Type uHistory}
    {Identity : Type uIdentity}
    (identity : History → Identity)
    (kernel : PredictiveKernel History)
    (insufficient :
      ¬ PredictivelySufficientIdentity identity kernel.trueWeight) :
    ∃ first second, ∃ test : FutureTest,
      identity first = identity second ∧
        test.observeWeight kernel first ≠ test.observeWeight kernel second := by
  rcases predictive_insufficiency_yields_weightWitness identity kernel insufficient with
    ⟨first, second, sameIdentity, different⟩
  exact ⟨first, second, ⟨true⟩, sameIdentity, by
    simpa [FutureTest.observeWeight] using different⟩

/--
For a same-identity pair with distinct future laws, every identity-only exact
report incurs unit loss on at least one history. This is an exact-report loss
witness, not an expected control-regret theorem.
-/
theorem predictive_insufficiency_yields_unavoidable_exactReportLoss
    {History : Type uHistory}
    {Identity : Type uIdentity}
    (identity : History → Identity)
    (kernel : PredictiveKernel History)
    (insufficient :
      ¬ PredictivelySufficientIdentity identity kernel.trueWeight) :
    ∃ first second,
      identity first = identity second ∧
        ∀ reported,
          ExactReportLoss reported (kernel.trueWeight first) = 1 ∨
            ExactReportLoss reported (kernel.trueWeight second) = 1 := by
  rcases predictive_insufficiency_yields_weightWitness identity kernel insufficient with
    ⟨first, second, sameIdentity, different⟩
  exact ⟨first, second, sameIdentity,
    sharedReport_misses_at_least_one different⟩

/-- Atomic scoped verdicts for a context after the kernel tests. -/
inductive IdentityPredictiveVerdict
  | exactBridge
  | sufficientWithRedundantIdentity
  | insufficientIdentity
  | incomparable
  | noFunctionalBridgeUseLineage
  deriving DecidableEq, Repr

/--
Exhaustive proposition-level classification of the two encoder kernels. The
no-functional-map/lineage case is deliberately not folded into this relation:
it is a separate precondition failure proved by assembly countermodels.
-/
inductive KernelRelationCase
    {History : Type uHistory}
    {Identity : Type uIdentity}
    {Predictive : Type uPredictive}
    (identity : History → Identity)
    (predictive : History → Predictive) : Prop
  | equal :
      KernelIncluded identity predictive →
      KernelIncluded predictive identity →
      KernelRelationCase identity predictive
  | identityStrictlyFiner :
      KernelIncluded identity predictive →
      (¬ KernelIncluded predictive identity) →
      KernelRelationCase identity predictive
  | identityStrictlyCoarser :
      (¬ KernelIncluded identity predictive) →
      KernelIncluded predictive identity →
      KernelRelationCase identity predictive
  | incomparable :
      (¬ KernelIncluded identity predictive) →
      (¬ KernelIncluded predictive identity) →
      KernelRelationCase identity predictive

theorem kernelRelation_exhaustive
    {History : Type uHistory}
    {Identity : Type uIdentity}
    {Predictive : Type uPredictive}
    (identity : History → Identity)
    (predictive : History → Predictive) :
    KernelRelationCase identity predictive := by
  classical
  by_cases forward : KernelIncluded identity predictive
  · by_cases backward : KernelIncluded predictive identity
    · exact .equal forward backward
    · exact .identityStrictlyFiner forward backward
  · by_cases backward : KernelIncluded predictive identity
    · exact .identityStrictlyCoarser forward backward
    · exact .incomparable forward backward

/-! ## Four exact kernel-relation fixtures -/

abbrev BitHistory := Bool × Bool

def firstBit : BitHistory → Bool := fun history => history.1
def secondBit : BitHistory → Bool := fun history => history.2
def fullBitHistory : BitHistory → BitHistory := id

theorem identity_predictive_kernel_equality_fixture :
    ExactIdentityPredictiveBridge firstBit firstBit := by
  intro first second
  rfl

theorem identity_strictly_finer_than_prediction_fixture :
    KernelIncluded fullBitHistory firstBit ∧
      ¬ KernelIncluded firstBit fullBitHistory := by
  constructor
  · intro first second sameHistory
    exact congrArg Prod.fst sameHistory
  · intro reverseInclusion
    have impossible := reverseInclusion
      (source := (false, false)) (target := (false, true)) rfl
    exact Bool.false_ne_true (congrArg Prod.snd impossible)

theorem identity_strictly_coarser_than_prediction_fixture :
    ¬ KernelIncluded firstBit fullBitHistory ∧
      KernelIncluded fullBitHistory firstBit := by
  exact ⟨identity_strictly_finer_than_prediction_fixture.2,
    identity_strictly_finer_than_prediction_fixture.1⟩

theorem identity_prediction_incomparable_fixture :
    ¬ KernelIncluded firstBit secondBit ∧
      ¬ KernelIncluded secondBit firstBit := by
  constructor
  · intro inclusion
    have impossible := inclusion
      (source := (false, false)) (target := (false, true)) rfl
    exact Bool.false_ne_true impossible
  · intro inclusion
    have impossible := inclusion
      (source := (false, false)) (target := (true, false)) rfl
    exact Bool.false_ne_true impossible

theorem four_identity_predictive_kernel_relations_fixture :
    ExactIdentityPredictiveBridge firstBit firstBit ∧
    (KernelIncluded fullBitHistory firstBit ∧
      ¬ KernelIncluded firstBit fullBitHistory) ∧
    (¬ KernelIncluded firstBit fullBitHistory ∧
      KernelIncluded fullBitHistory firstBit) ∧
    (¬ KernelIncluded firstBit secondBit ∧
      ¬ KernelIncluded secondBit firstBit) := by
  exact ⟨identity_predictive_kernel_equality_fixture,
    identity_strictly_finer_than_prediction_fixture,
    identity_strictly_coarser_than_prediction_fixture,
    identity_prediction_incomparable_fixture⟩

/-! ## A valid finite stochastic insufficiency fixture -/

def secondBitPredictiveKernel : PredictiveKernel BitHistory where
  denominator := 1
  denominatorPositive := by decide
  trueWeight history := if history.2 then 1 else 0
  trueWeightBounded := by
    intro history
    cases history.2 <;> simp

theorem firstBit_identity_is_stochastically_insufficient :
    ¬ PredictivelySufficientIdentity
      firstBit secondBitPredictiveKernel.trueWeight := by
  intro sufficient
  have impossible := sufficient
    (source := (false, false)) (target := (false, true)) rfl
  change secondBitPredictiveKernel.trueWeight (false, false) =
    secondBitPredictiveKernel.trueWeight (false, true) at impossible
  simp [secondBitPredictiveKernel] at impossible

theorem finite_stochastic_exactReportLoss_fixture :
    ∃ first second,
      firstBit first = firstBit second ∧
        ∀ reported,
          ExactReportLoss reported
              (secondBitPredictiveKernel.trueWeight first) = 1 ∨
            ExactReportLoss reported
              (secondBitPredictiveKernel.trueWeight second) = 1 := by
  exact predictive_insufficiency_yields_unavoidable_exactReportLoss
    firstBit secondBitPredictiveKernel
      firstBit_identity_is_stochastically_insufficient

/--
If a branch has predictively distinct children, no identity encoder can both
collapse every continuation edge and remain predictively sufficient.
-/
theorem branching_predictive_distinction_precludes_collapsingIdentity
    {Occurrence : Type uOccurrence}
    {Identity : Type uIdentity}
    {Predictive : Type uPredictive}
    {evidence : BinaryRelation Occurrence}
    {predictive : Occurrence → Predictive}
    {parent leftChild rightChild : Occurrence}
    (leftBranch : evidence parent leftChild)
    (rightBranch : evidence parent rightChild)
    (predictivelyDistinct : predictive leftChild ≠ predictive rightChild) :
    ¬ ∃ identity : Occurrence → Identity,
      ContinuationPreserving evidence identity ∧
        PredictivelySufficientIdentity identity predictive := by
  rintro ⟨identity, preserves, sufficient⟩
  apply predictivelyDistinct
  apply sufficient
  exact (preserves leftBranch).symm.trans (preserves rightBranch)

def forkPrediction : ForkOccurrence → Bool
  | .root => false
  | .left => false
  | .right => true

/--
The fork rules out one functional encoder that both collapses all evidence
edges and is predictively sufficient. It does not by itself prove existence or
uniqueness of a particular two-layer lineage/prediction construction.
-/
theorem fork_precludes_edgeCollapsing_predictivelySufficient_functionalIdentity :
    ¬ ∃ identity : ForkOccurrence → Bool,
      ContinuationPreserving forkEvidence identity ∧
        PredictivelySufficientIdentity identity forkPrediction := by
  exact branching_predictive_distinction_precludes_collapsingIdentity
    (evidence := forkEvidence)
    (predictive := forkPrediction)
    (parent := .root) (leftChild := .left) (rightChild := .right)
    trivial trivial Bool.false_ne_true

end OCMaturityCompletionCycle
