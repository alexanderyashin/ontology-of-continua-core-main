import OCKIndividuationMSpaceComposition.StochasticKernelDefectBridge
import OCMinimalObligationSpine.ObservableDemandPressure

/-!
# Demanded observables and exact finite stochastic quotients

The tests below are supplied independently of a proposed encoder. Their expected
one-step values are the receiver effects that a representation must distinguish.
A separate, explicit linear completeness certificate reconstructs each encoder
cell indicator from these tests. Finite linearity then derives controlled
lumpability; it is not assumed as a field of the certificate.

The finite rational kernel is normalized. The inherited mass-factor interface is
weaker than a normalized kernel on unused quotient points, so the full-kernel
construction below requires a surjective encoder. Nothing here infers a kernel,
test calibration, demand policy, or span certificate from sampled observations.
-/

namespace OCScientificExtensions.DemandedObservableQuotientBridge

open OCMaturityCompletionCycle
open OCKIndividuationMSpaceComposition
open OCMinimalObligationSpine
open scoped BigOperators

universe uState uAction uQuotient uTest

/-- Expected value of one fixed rational test after one controlled transition. -/
def expectedObservable
    {State : Type uState} {Action : Type uAction} {Test : Type uTest}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (test : Test → State → ℚ) (state : State) (action : Action)
    (coordinate : Test) : ℚ :=
  ∑ next, kernel.mass state action next * test coordinate next

/-- The encoder separates every difference in the declared expected effects.
This is a mathematical preservation policy, not empirical test acquisition. -/
def PreservesDemandedObservables
    {State : Type uState} {Action : Type uAction}
    {Quotient : Type uQuotient} {Test : Type uTest}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action) (encode : State → Quotient)
    (test : Test → State → ℚ) : Prop :=
  ∀ ⦃left right : State⦄ (action : Action) (coordinate : Test),
    expectedObservable kernel test left action coordinate ≠
        expectedObservable kernel test right action coordinate →
      encode left ≠ encode right

/-- Exact observational-equivalence form of the distinction-preservation rule. -/
theorem preservesDemandedObservables_iff_same_cell_effects
    {State : Type uState} {Action : Type uAction}
    {Quotient : Type uQuotient} {Test : Type uTest}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action) (encode : State → Quotient)
    (test : Test → State → ℚ) :
    PreservesDemandedObservables kernel encode test ↔
      ∀ ⦃left right : State⦄, encode left = encode right →
        ∀ action coordinate,
          expectedObservable kernel test left action coordinate =
            expectedObservable kernel test right action coordinate := by
  classical
  constructor
  · intro preserves left right sameCell action coordinate
    by_contra different
    exact preserves action coordinate different sameCell
  · intro sameEffects left right action coordinate different sameCell
    exact different (sameEffects sameCell action coordinate)

/-- A finite linear completeness certificate for the proposed quotient cells.
Coefficients may be signed. The tests are inputs; this identity must be proved,
and is not manufactured by naming a family complete. -/
structure QuotientIndicatorSpan
    {State : Type uState} {Quotient : Type uQuotient} {Test : Type uTest}
    [Fintype Test] [DecidableEq Quotient]
    (encode : State → Quotient) (test : Test → State → ℚ) where
  coefficient : Quotient → Test → ℚ
  reconstruct : ∀ target next,
    (if encode next = target then (1 : ℚ) else 0) =
      ∑ coordinate, coefficient target coordinate * test coordinate next

/-- Finite linear reconstruction of each pushed-forward transition mass. -/
theorem pushedMass_eq_linear_expectedObservables
    {State : Type uState} {Action : Type uAction}
    {Quotient : Type uQuotient} {Test : Type uTest}
    [Fintype State] [Fintype Test] [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action) (encode : State → Quotient)
    (test : Test → State → ℚ) (span : QuotientIndicatorSpan encode test)
    (state : State) (action : Action) (target : Quotient) :
    pushedMass kernel encode state action target =
      ∑ coordinate, span.coefficient target coordinate *
        expectedObservable kernel test state action coordinate := by
  calc
    pushedMass kernel encode state action target =
        ∑ next, kernel.mass state action next *
          (if encode next = target then (1 : ℚ) else 0) := by
      apply Finset.sum_congr rfl
      intro next _
      by_cases same : encode next = target <;> simp [same]
    _ = ∑ next, kernel.mass state action next *
          (∑ coordinate, span.coefficient target coordinate * test coordinate next) := by
      apply Finset.sum_congr rfl
      intro next _
      rw [span.reconstruct]
    _ = ∑ next, ∑ coordinate, span.coefficient target coordinate *
          (kernel.mass state action next * test coordinate next) := by
      apply Finset.sum_congr rfl
      intro next _
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro coordinate _
      ring
    _ = ∑ coordinate, ∑ next, span.coefficient target coordinate *
          (kernel.mass state action next * test coordinate next) :=
      Finset.sum_comm
    _ = ∑ coordinate, span.coefficient target coordinate *
          expectedObservable kernel test state action coordinate := by
      apply Finset.sum_congr rfl
      intro coordinate _
      rw [← Finset.mul_sum]
      rfl

/-- Complete demanded effects force representative-independent quotient rows. -/
theorem demanded_observables_and_span_imply_lumpability
    {State : Type uState} {Action : Type uAction}
    {Quotient : Type uQuotient} {Test : Type uTest}
    [Fintype State] [Fintype Test] [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action) (encode : State → Quotient)
    (test : Test → State → ℚ) (span : QuotientIndicatorSpan encode test)
    (preserves : PreservesDemandedObservables kernel encode test) :
    ControlledLumpability kernel encode := by
  intro left right sameCell action target
  rw [pushedMass_eq_linear_expectedObservables kernel encode test span,
    pushedMass_eq_linear_expectedObservables kernel encode test span]
  apply Finset.sum_congr rfl
  intro coordinate _
  rw [(preservesDemandedObservables_iff_same_cell_effects kernel encode test).1
    preserves sameCell action coordinate]

/-- The inherited exact mass factor exists. Unused quotient points need not
have normalized rows in this interface. -/
theorem demanded_observables_have_exact_quotient_factor
    {State : Type uState} {Action : Type uAction}
    {Quotient : Type uQuotient} {Test : Type uTest}
    [Fintype State] [Fintype Test] [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action) (encode : State → Quotient)
    (test : Test → State → ℚ) (span : QuotientIndicatorSpan encode test)
    (preserves : PreservesDemandedObservables kernel encode test) :
    Nonempty (QuotientControlledKernel kernel encode) :=
  (controlledLumpability_iff_quotientFactor kernel encode).1
    (demanded_observables_and_span_imply_lumpability
      kernel encode test span preserves)

/-- The same bridge discharges the existing numerical zero-defect criterion. -/
theorem demanded_observables_have_zero_pairwiseTV_defect
    {State : Type uState} {Action : Type uAction}
    {Quotient : Type uQuotient} {Test : Type uTest}
    [Fintype State] [Fintype Quotient] [Fintype Test] [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action) (encode : State → Quotient)
    (test : Test → State → ℚ) (span : QuotientIndicatorSpan encode test)
    (preserves : PreservesDemandedObservables kernel encode test) :
    ∀ action, pairwiseLumpabilityDefect kernel encode action = 0 :=
  (controlledLumpability_iff_pairwiseTV_defect_zero kernel encode).1
    (demanded_observables_and_span_imply_lumpability
      kernel encode test span preserves)

/-- A normalized row at every quotient point, using a representative guaranteed
by surjectivity. Exactness of this construction is proved separately below. -/
noncomputable def representativeQuotientKernel
    {State : Type uState} {Action : Type uAction} {Quotient : Type uQuotient}
    [Fintype State] [Fintype Quotient] [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action) (encode : State → Quotient)
    (onto : Function.Surjective encode) : FiniteControlledKernel Quotient Action where
  mass source action target :=
    (pushedKernelRowProbability kernel encode (Classical.choose (onto source)) action).mass target
  nonnegative source action target :=
    (pushedKernelRowProbability kernel encode
      (Classical.choose (onto source)) action).nonnegative target
  normalized source action :=
    (pushedKernelRowProbability kernel encode
      (Classical.choose (onto source)) action).normalized

/-- Span coverage and demand preservation make the normalized selected rows
commute with the actual source rows. -/
theorem representativeQuotientKernel_commutes
    {State : Type uState} {Action : Type uAction}
    {Quotient : Type uQuotient} {Test : Type uTest}
    [Fintype State] [Fintype Quotient] [Fintype Test] [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action) (encode : State → Quotient)
    (onto : Function.Surjective encode)
    (test : Test → State → ℚ) (span : QuotientIndicatorSpan encode test)
    (preserves : PreservesDemandedObservables kernel encode test)
    (state : State) (action : Action) (target : Quotient) :
    (representativeQuotientKernel kernel encode onto).mass
        (encode state) action target = pushedMass kernel encode state action target := by
  change pushedMass kernel encode (Classical.choose (onto (encode state)))
    action target = pushedMass kernel encode state action target
  exact demanded_observables_and_span_imply_lumpability
    kernel encode test span preserves
    (Classical.choose_spec (onto (encode state))) action target

/-- A full normalized finite quotient exists when every quotient state is used. -/
theorem demanded_observables_have_normalized_quotient
    {State : Type uState} {Action : Type uAction}
    {Quotient : Type uQuotient} {Test : Type uTest}
    [Fintype State] [Fintype Quotient] [Fintype Test] [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action) (encode : State → Quotient)
    (onto : Function.Surjective encode)
    (test : Test → State → ℚ) (span : QuotientIndicatorSpan encode test)
    (preserves : PreservesDemandedObservables kernel encode test) :
    ∃ quotient : FiniteControlledKernel Quotient Action,
      ∀ state action target,
        quotient.mass (encode state) action target =
          pushedMass kernel encode state action target := by
  exact ⟨representativeQuotientKernel kernel encode onto,
    representativeQuotientKernel_commutes kernel encode onto test span preserves⟩

/-- Actual CurrentK demand law at step zero, with an explicit interpretation of
its receiver effects as expected tests. No deterministic K transition is
silently identified with the stochastic source kernel. -/
theorem currentK_receiver_demand_and_span_imply_lumpability
    (representation : CurrentK)
    [Fintype representation.State] [DecidableEq representation.Carrier]
    {Action : Type uAction} {Test : Type uTest} [Fintype Test]
    (kernel : FiniteControlledKernel representation.State Action)
    (test : Test → representation.State → ℚ)
    (span : QuotientIndicatorSpan representation.encode test)
    (receiver : Action → Test → representation.Receiver)
    (readEffect : representation.Effect → ℚ)
    (effectLaw : ∀ state action coordinate,
      readEffect (representation.receiverEffect state (receiver action coordinate)) =
        expectedObservable kernel test state action coordinate)
    (constraint : ObservableReceiverConstraint
      representation.Receiver representation.Effect)
    (rejectUnequal : ∀ action coordinate leftEffect rightEffect,
      readEffect leftEffect ≠ readEffect rightEffect →
        constraint.acceptsMergedEffects 0 (receiver action coordinate)
          leftEffect rightEffect = false)
    (demandExpressed : ∀ distinction : TrajectoryDistinction representation,
      activeDemandFromReceiverConstraint constraint distinction →
        Expresses representation distinction) :
    ControlledLumpability kernel representation.encode := by
  apply demanded_observables_and_span_imply_lumpability
    kernel representation.encode test span
  intro left right action coordinate different
  have effectDifferent :
      representation.receiverEffect left (receiver action coordinate) ≠
        representation.receiverEffect right (receiver action coordinate) := by
    intro equal
    apply different
    rw [← effectLaw left action coordinate, ← effectLaw right action coordinate]
    exact congrArg readEffect equal
  let distinction : TrajectoryDistinction representation := {
    left := left
    right := right
    step := 0
    receiver := receiver action coordinate
    effect_ne := effectDifferent
  }
  apply demandExpressed distinction
  change constraint.acceptsMergedEffects 0 (receiver action coordinate)
    (representation.receiverEffect left (receiver action coordinate))
    (representation.receiverEffect right (receiver action coordinate)) = false
  apply rejectUnequal
  simpa only [effectLaw] using different

/-! ## Incomplete-test countermodel -/

/-- One normalized-mass test, incapable of resolving any transition law. -/
def constantTest : Unit → SupportState → ℚ := fun _ _ => 1

theorem constantTest_expected_one (state : SupportState) (action : Unit) :
    expectedObservable supportKernel constantTest state action () = 1 := by
  simp only [expectedObservable, constantTest, mul_one]
  exact supportKernel.normalized state action

theorem constantTest_demands_preserved :
    PreservesDemandedObservables supportKernel supportQuotient constantTest := by
  intro left right action coordinate different
  cases coordinate
  exact False.elim (different ((constantTest_expected_one left action).trans
    (constantTest_expected_one right action).symm))

/-- A normalized finite kernel preserves all selected test effects yet is not
lumpable: both source rows pass the constant test, but their quotient masses
are 1/3 versus 2/3 at the first target cell. -/
theorem incomplete_tests_do_not_certify_lumpability :
    PreservesDemandedObservables supportKernel supportQuotient constantTest ∧
      ¬ ControlledLumpability supportKernel supportQuotient :=
  ⟨constantTest_demands_preserved, equal_support_not_lumpable⟩

/-- The omitted completeness certificate cannot be supplied for this fixture. -/
theorem constantTest_has_no_indicator_span :
    ¬ Nonempty (QuotientIndicatorSpan supportQuotient constantTest) := by
  rintro ⟨span⟩
  exact equal_support_not_lumpable
    (demanded_observables_and_span_imply_lumpability
      supportKernel supportQuotient constantTest span constantTest_demands_preserved)

/-! ## A complete signed-test fixture with genuine state merging -/

/-- A four-state kernel with a two-cell alternating quotient. The source rows
have different fine target probabilities; both target states return to sourceZero. -/
def alternatingMass : SupportState → Unit → SupportState → ℚ
  | .sourceZero, _, .targetZero => 1 / 3
  | .sourceZero, _, .targetOne => 2 / 3
  | .sourceOne, _, .targetZero => 2 / 3
  | .sourceOne, _, .targetOne => 1 / 3
  | .targetZero, _, .sourceZero => 1
  | .targetOne, _, .sourceZero => 1
  | _, _, _ => 0

def alternatingKernel : FiniteControlledKernel SupportState Unit where
  mass := alternatingMass
  nonnegative := by
    intro state action target
    cases state <;> cases target <;> norm_num [alternatingMass]
  normalized := by
    intro state action
    rw [sum_supportState]
    cases state <;> norm_num [alternatingMass]

/-- Sources form one cell and targets another; both pairs of fine states merge. -/
def twoCellObservation : SupportState → Bool
  | .sourceZero | .sourceOne => false
  | .targetZero | .targetOne => true

/-- The constant test and a signed contrast, fixed explicitly on the four states. -/
def signedTests : Bool → SupportState → ℚ
  | false, _ => 1
  | true, .sourceZero | true, .sourceOne => -1
  | true, .targetZero | true, .targetOne => 1

/-- The two indicators are (constant - contrast)/2 and (constant + contrast)/2. -/
def signedTestsSpan : QuotientIndicatorSpan twoCellObservation signedTests where
  coefficient target coordinate :=
    if coordinate = false then 1 / 2 else if target = true then 1 / 2 else -1 / 2
  reconstruct := by
    have boolUniv : (Finset.univ : Finset Bool) = {false, true} := by decide
    intro target next
    cases target <;> cases next <;>
      norm_num [boolUniv, twoCellObservation, signedTests]

theorem signedTests_expected_formula (state : SupportState) (action : Unit)
    (coordinate : Bool) :
    expectedObservable alternatingKernel signedTests state action coordinate =
      if coordinate = false then 1 else if twoCellObservation state = true then -1 else 1 := by
  unfold expectedObservable
  rw [sum_supportState]
  cases state <;> cases coordinate <;>
    norm_num [alternatingKernel, alternatingMass, signedTests, twoCellObservation]

theorem signedTests_demands_preserved :
    PreservesDemandedObservables alternatingKernel twoCellObservation signedTests := by
  apply (preservesDemandedObservables_iff_same_cell_effects
    alternatingKernel twoCellObservation signedTests).2
  intro left right sameCell action coordinate
  rw [signedTests_expected_formula, signedTests_expected_formula, sameCell]

/-- The positive fixture has an actual demanded contrast, not only a vacuous policy. -/
theorem alternating_states_have_different_expected_effects :
    expectedObservable alternatingKernel signedTests .sourceZero () true ≠
      expectedObservable alternatingKernel signedTests .targetZero () true := by
  rw [signedTests_expected_formula, signedTests_expected_formula]
  norm_num [twoCellObservation]

/-- Equal quotient rows need not identify the underlying fine transition rows. -/
theorem merged_source_states_have_different_fine_rows :
    alternatingKernel.mass .sourceZero () .targetZero ≠
      alternatingKernel.mass .sourceOne () .targetZero := by
  norm_num [alternatingKernel, alternatingMass]

theorem twoCellObservation_lumpable :
    ControlledLumpability alternatingKernel twoCellObservation :=
  demanded_observables_and_span_imply_lumpability
    alternatingKernel twoCellObservation signedTests signedTestsSpan signedTests_demands_preserved

theorem twoCellObservation_surjective : Function.Surjective twoCellObservation := by
  intro value
  cases value with
  | false => exact ⟨.sourceZero, rfl⟩
  | true => exact ⟨.targetZero, rfl⟩

/-- The positive example is a genuine quotient, not an identity encoder. -/
theorem twoCellObservation_not_injective : ¬ Function.Injective twoCellObservation := by
  intro injective
  have equal : SupportState.sourceZero = SupportState.sourceOne := injective rfl
  cases equal

theorem twoCellObservation_has_normalized_quotient :
    ∃ quotient : FiniteControlledKernel Bool Unit,
      ∀ state action target,
        quotient.mass (twoCellObservation state) action target =
          pushedMass alternatingKernel twoCellObservation state action target :=
  demanded_observables_have_normalized_quotient
    alternatingKernel twoCellObservation twoCellObservation_surjective
    signedTests signedTestsSpan signedTests_demands_preserved

end OCScientificExtensions.DemandedObservableQuotientBridge
