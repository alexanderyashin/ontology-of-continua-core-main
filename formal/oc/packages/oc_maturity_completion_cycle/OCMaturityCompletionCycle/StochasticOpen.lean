import OCMaturityCompletionCycle.IdentityAssembly
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Data.Fintype.Order
import Mathlib.Tactic.DeriveFintype
import Mathlib.Tactic.NormNum

/-!
# Finite stochastic reduction and typed open composition

The probability layer uses exact nonnegative rational mass functions on finite
state spaces.  Quotient factorization, support, path-law equality, and open
composition are deliberately separate notions.
-/

namespace OCMaturityCompletionCycle

universe uState uAction uQuotient uFine uCoarse uBoundary uOutput

/-- A normalized finite controlled stochastic kernel with exact rational mass. -/
structure FiniteControlledKernel
    (State : Type uState)
    (Action : Type uAction)
    [Fintype State] where
  mass : State → Action → State → ℚ
  nonnegative : ∀ state action target, 0 ≤ mass state action target
  normalized : ∀ state action, ∑ target, mass state action target = 1

/-- Observable mass of one quotient target class. -/
def pushedMass
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (state : State)
    (action : Action)
    (target : Quotient) : ℚ :=
  ∑ nextState, if encode nextState = target then kernel.mass state action nextState else 0

/-- Strong controlled lumpability for the fixed action family and encoder. -/
def ControlledLumpability
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient) : Prop :=
  ∀ ⦃left right⦄,
    encode left = encode right →
      ∀ action target,
        pushedMass kernel encode left action target =
          pushedMass kernel encode right action target

/-- An exact memoryless quotient factor for one-step observable laws. -/
structure QuotientControlledKernel
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient) where
  mass : Quotient → Action → Quotient → ℚ
  commutes : ∀ state action target,
    mass (encode state) action target =
      pushedMass kernel encode state action target

/--
Exact finite characterization: representative-independent pushed mass is
equivalent to existence of a memoryless quotient factor.  Unused quotient
points receive zero mass and are outside the used-range claim.
-/
theorem controlledLumpability_iff_quotientFactor
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient) :
    ControlledLumpability kernel encode ↔
      Nonempty (QuotientControlledKernel kernel encode) := by
  constructor
  · intro lumpable
    classical
    let quotientMass : Quotient → Action → Quotient → ℚ :=
      fun source action target =>
        if existsRepresentative : ∃ state, encode state = source then
          pushedMass kernel encode (Classical.choose existsRepresentative) action target
        else 0
    refine ⟨{
      mass := quotientMass
      commutes := ?_
    }⟩
    intro state action target
    dsimp [quotientMass]
    split
    · rename_i existsRepresentative
      have representativeClass :
          encode (Classical.choose existsRepresentative) = encode state := by
        exact (Classical.choose_spec existsRepresentative).trans rfl
      exact lumpable representativeClass action target
    · rename_i noRepresentative
      exact False.elim (noRepresentative ⟨state, rfl⟩)
  · rintro ⟨factor⟩ left right sameClass action target
    calc
      pushedMass kernel encode left action target =
          factor.mass (encode left) action target :=
        (factor.commutes left action target).symm
      _ = factor.mass (encode right) action target := by rw [sameClass]
      _ = pushedMass kernel encode right action target :=
        factor.commutes right action target

/-- Nonlumpability is exactly a no-go for the fixed memoryless quotient. -/
theorem nonlumpable_no_exact_memoryless_quotient
    {State : Type uState}
    {Action : Type uAction}
    {Quotient : Type uQuotient}
    [Fintype State]
    [DecidableEq Quotient]
    (kernel : FiniteControlledKernel State Action)
    (encode : State → Quotient)
    (notLumpable : ¬ ControlledLumpability kernel encode) :
    IsEmpty (QuotientControlledKernel kernel encode) := by
  refine ⟨?_⟩
  intro factor
  exact notLumpable
    ((controlledLumpability_iff_quotientFactor kernel encode).2 ⟨factor⟩)

/-! ## Stochastic finite-horizon closure -/

/-- A signed mass vector.  Probability vectors are the normalized nonnegative instances. -/
abbrev MassVector (State : Type uState) := State → ℚ

/-- Linear evolution induced by one action of a finite stochastic kernel. -/
def evolveMass
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (action : Action)
    (initial : MassVector State) : MassVector State :=
  fun target => ∑ source, initial source * kernel.mass source action target

/-- Push a finite mass vector through a state encoder. -/
def pushforwardMass
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    [Fintype Fine]
    [DecidableEq Coarse]
    (encode : Fine → Coarse)
    (initial : MassVector Fine) : MassVector Coarse :=
  fun target => ∑ source, if encode source = target then initial source else 0

/-- Execute a frozen finite action schedule from left to right. -/
def applyActionSchedule
    {Action : Type uAction}
    {Mass : Type uState}
    (step : Action → Mass → Mass) : List Action → Mass → Mass
  | [], initial => initial
  | action :: remaining, initial =>
      applyActionSchedule step remaining (step action initial)

/-- The stochastic one-step commuting square, quantified over all input masses. -/
def StochasticOneStepCommutes
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    {Action : Type uAction}
    [Fintype Fine]
    [Fintype Coarse]
    [DecidableEq Coarse]
    (fineKernel : FiniteControlledKernel Fine Action)
    (coarseKernel : FiniteControlledKernel Coarse Action)
    (encode : Fine → Coarse) : Prop :=
  ∀ action initial,
    pushforwardMass encode (evolveMass fineKernel action initial) =
      evolveMass coarseKernel action (pushforwardMass encode initial)

/-- Commutation for every finite frozen action schedule. -/
def EveryStochasticActionScheduleCommutes
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    {Action : Type uAction}
    [Fintype Fine]
    [Fintype Coarse]
    [DecidableEq Coarse]
    (fineKernel : FiniteControlledKernel Fine Action)
    (coarseKernel : FiniteControlledKernel Coarse Action)
    (encode : Fine → Coarse) : Prop :=
  ∀ actions initial,
    pushforwardMass encode
        (applyActionSchedule (evolveMass fineKernel) actions initial) =
      applyActionSchedule (evolveMass coarseKernel) actions
        (pushforwardMass encode initial)

/--
For exact finite stochastic kernels, the one-step distribution square commutes
if and only if every finite frozen action schedule commutes.  This is an
operator theorem; it does not assert that a proposed quotient supplies the
required coarse kernel.
-/
theorem stochasticOneStep_iff_everyActionSchedule
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    {Action : Type uAction}
    [Fintype Fine]
    [Fintype Coarse]
    [DecidableEq Coarse]
    (fineKernel : FiniteControlledKernel Fine Action)
    (coarseKernel : FiniteControlledKernel Coarse Action)
    (encode : Fine → Coarse) :
    StochasticOneStepCommutes fineKernel coarseKernel encode ↔
      EveryStochasticActionScheduleCommutes fineKernel coarseKernel encode := by
  constructor
  · intro oneStep actions
    induction actions with
    | nil => intro initial; rfl
    | cons action remaining inductionHypothesis =>
        intro initial
        change
          pushforwardMass encode
              (applyActionSchedule (evolveMass fineKernel) remaining
                (evolveMass fineKernel action initial)) =
            applyActionSchedule (evolveMass coarseKernel) remaining
              (evolveMass coarseKernel action (pushforwardMass encode initial))
        rw [inductionHypothesis (evolveMass fineKernel action initial),
          oneStep action initial]
  · intro everySchedule action initial
    simpa [StochasticOneStepCommutes, EveryStochasticActionScheduleCommutes,
      applyActionSchedule] using everySchedule [action] initial

/-- Abstract stochastic operator commutation is stable under sequential composition. -/
theorem stochastic_operator_sequential_commutes
    {FineMass : Type uFine}
    {CoarseMass : Type uCoarse}
    (push : FineMass → CoarseMass)
    (fineFirst fineSecond : FineMass → FineMass)
    (coarseFirst coarseSecond : CoarseMass → CoarseMass)
    (firstCommutes : ∀ mass, push (fineFirst mass) = coarseFirst (push mass))
    (secondCommutes : ∀ mass, push (fineSecond mass) = coarseSecond (push mass)) :
    ∀ mass,
      push (fineSecond (fineFirst mass)) =
        coarseSecond (coarseFirst (push mass)) := by
  intro mass
  rw [secondCommutes, firstCommutes]

/-! ## Finite-horizon closure -/

/-- Iteration written explicitly to avoid any hidden semigroup assumption. -/
def iterateMap {α : Type uFine} (step : α → α) : Nat → α → α
  | 0 => id
  | horizon + 1 => fun state => iterateMap step horizon (step state)

def OneStepCommutes
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    (encode : Fine → Coarse)
    (step : Fine → Fine)
    (reduced : Coarse → Coarse) : Prop :=
  ∀ state, encode (step state) = reduced (encode state)

def EveryFiniteHorizonCommutes
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    (encode : Fine → Coarse)
    (step : Fine → Fine)
    (reduced : Coarse → Coarse) : Prop :=
  ∀ horizon state,
    encode (iterateMap step horizon state) =
      iterateMap reduced horizon (encode state)

/-- One-step commutation is equivalent to all finite-horizon commutation. -/
theorem oneStepCommutes_iff_everyFiniteHorizon
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    (encode : Fine → Coarse)
    (step : Fine → Fine)
    (reduced : Coarse → Coarse) :
    OneStepCommutes encode step reduced ↔
      EveryFiniteHorizonCommutes encode step reduced := by
  constructor
  · intro oneStep horizon
    induction horizon with
    | zero => intro state; rfl
    | succ horizon inductionHypothesis =>
        intro state
        change encode (iterateMap step horizon (step state)) =
          iterateMap reduced horizon (reduced (encode state))
        rw [inductionHypothesis (step state), oneStep state]
  · intro everyHorizon state
    simpa [OneStepCommutes, EveryFiniteHorizonCommutes, iterateMap] using
      everyHorizon 1 state

/-! ## Same support, different law -/

inductive SupportState
  | sourceZero
  | sourceOne
  | targetZero
  | targetOne
  deriving DecidableEq, Fintype, Repr

theorem supportState_univ :
    (Finset.univ : Finset SupportState) =
      {SupportState.sourceZero, SupportState.sourceOne,
        SupportState.targetZero, SupportState.targetOne} := by
  decide

theorem sum_supportState (mass : SupportState → ℚ) :
    (∑ state, mass state) =
      mass .sourceZero + mass .sourceOne + mass .targetZero + mass .targetOne := by
  rw [supportState_univ]
  simp [add_assoc]

def supportMass : SupportState → Unit → SupportState → ℚ
  | .sourceZero, _, .targetZero => 1 / 3
  | .sourceZero, _, .targetOne => 2 / 3
  | .sourceOne, _, .targetZero => 2 / 3
  | .sourceOne, _, .targetOne => 1 / 3
  | .targetZero, _, .targetZero => 1
  | .targetOne, _, .targetOne => 1
  | _, _, _ => 0

def supportKernel : FiniteControlledKernel SupportState Unit where
  mass := supportMass
  nonnegative := by
    intro state action target
    cases state <;> cases target <;> norm_num [supportMass]
  normalized := by
    intro state action
    rw [sum_supportState]
    cases state <;> norm_num [supportMass]

def supportQuotient : SupportState → Fin 3
  | .sourceZero | .sourceOne => 0
  | .targetZero => 1
  | .targetOne => 2

def PositiveSupport
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (state : State)
    (action : Action)
    (target : State) : Prop :=
  0 < kernel.mass state action target

theorem support_rows_have_identical_positive_support :
    ∀ target,
      PositiveSupport supportKernel .sourceZero () target ↔
        PositiveSupport supportKernel .sourceOne () target := by
  intro target
  cases target <;> norm_num [PositiveSupport, supportKernel, supportMass]

/-- Equal support does not imply equality of pushed-forward mass. -/
theorem equal_support_not_lumpable :
    ¬ ControlledLumpability supportKernel supportQuotient := by
  intro lumpable
  have unequal := @lumpable
    SupportState.sourceZero SupportState.sourceOne rfl () (1 : Fin 3)
  norm_num [pushedMass, supportKernel, supportMass, supportQuotient,
    sum_supportState, Fin.sum_univ_succ] at unequal
  simp [show (2 : Fin 3) ≠ 1 by decide] at unequal
  norm_num at unequal

/-! ## History state and exact memory -/

/-- A future law factors through an encoder exactly when the encoder is sufficient. -/
def LawFactorsThrough
    {History : Type uFine}
    {Memory : Type uCoarse}
    {Law : Type uOutput}
    (encode : History → Memory)
    (futureLaw : History → Law) : Prop :=
  ∃ reducedLaw : Memory → Law,
    ∀ history, reducedLaw (encode history) = futureLaw history

/-- Kernel inclusion for maps whose codomains may live in different universes. -/
def CrossUniverseKernelRefines
    {History : Type uFine}
    {Memory : Type uCoarse}
    {Law : Type uOutput}
    (encode : History → Memory)
    (futureLaw : History → Law) : Prop :=
  ∀ ⦃left right⦄, encode left = encode right → futureLaw left = futureLaw right

theorem lawFactorsThrough_iff_kernelRefinement
    {History : Type uFine}
    {Memory : Type uCoarse}
    {Law : Type uOutput}
    [Nonempty Law]
    (encode : History → Memory)
    (futureLaw : History → Law) :
    LawFactorsThrough encode futureLaw ↔
      CrossUniverseKernelRefines encode futureLaw := by
  constructor
  · rintro ⟨reducedLaw, factorization⟩ left right sameMemory
    calc
      futureLaw left = reducedLaw (encode left) := (factorization left).symm
      _ = reducedLaw (encode right) := by rw [sameMemory]
      _ = futureLaw right := factorization right
  · intro refinement
    classical
    let reducedLaw : Memory → Law := fun memory =>
      if hasRepresentative : ∃ history, encode history = memory then
        futureLaw (Classical.choose hasRepresentative)
      else Classical.choice inferInstance
    refine ⟨reducedLaw, ?_⟩
    intro history
    dsimp [reducedLaw]
    split
    · rename_i hasRepresentative
      apply refinement
      exact (Classical.choose_spec hasRepresentative).trans rfl
    · rename_i noRepresentative
      exact False.elim (noRepresentative ⟨history, rfl⟩)

/--
An explicitly witnessed summary collision is a no-go for exact memoryless
prediction through that summary.  No particular history representation is
privileged by this theorem.
-/
theorem insufficient_history_summary_no_factor
    {History : Type uFine}
    {Memory : Type uCoarse}
    {Law : Type uOutput}
    [Nonempty Law]
    (encode : History → Memory)
    (futureLaw : History → Law)
    (collision : ∃ left right,
      encode left = encode right ∧ futureLaw left ≠ futureLaw right) :
    ¬ LawFactorsThrough encode futureLaw := by
  intro factorization
  have refinement :=
    (lawFactorsThrough_iff_kernelRefinement encode futureLaw).1 factorization
  rcases collision with ⟨left, right, sameMemory, differentLaw⟩
  exact differentLaw (refinement sameMemory)

/-- Full history always factors its declared law, with no finiteness claim. -/
theorem raw_history_always_exact
    {History : Type uFine}
    {Law : Type uOutput}
    [Nonempty Law]
    (futureLaw : History → Law) :
    LawFactorsThrough id futureLaw := by
  exact ⟨futureLaw, fun _ => rfl⟩

/--
Finite exact memory must have at least as many states as any finite family of
pairwise law-distinguishable histories.  This is a cardinality price, not a
sample-complexity or rate-distortion bound.
-/
theorem finite_exact_memory_cardinality_lower_bound
    {History : Type uFine}
    {Memory : Type uCoarse}
    {Law : Type uOutput}
    [Fintype Memory]
    [Nonempty Law]
    (encode : History → Memory)
    (futureLaw : History → Law)
    (sample : Fin n → History)
    (factorization : LawFactorsThrough encode futureLaw)
    (distinguishable : Function.Injective (fun i => futureLaw (sample i))) :
    n ≤ Fintype.card Memory := by
  have refinement :=
    (lawFactorsThrough_iff_kernelRefinement encode futureLaw).1 factorization
  have encodedSampleInjective : Function.Injective (fun i => encode (sample i)) := by
    intro left right sameMemory
    exact distinguishable (refinement sameMemory)
  simpa using Fintype.card_le_of_injective _ encodedSampleInjective

/-- A history-indexed deterministic next occurrence, used as an exact fixture. -/
def historyNext : List Bool → Bool
  | [false, false] => false
  | [true, false] => true
  | _ => false

def lastObservation (history : List Bool) : Option Bool := history.getLast?

/-- Equal last observations can require different next laws. -/
theorem equal_last_state_different_history_law :
    lastObservation [false, false] = lastObservation [true, false] ∧
      historyNext [false, false] ≠ historyNext [true, false] := by
  decide

/-- The complete history state determines its declared next law by construction. -/
theorem full_history_is_exact_state :
    ∃ predictor : List Bool → Bool,
      ∀ history, predictor history = historyNext history := by
  exact ⟨historyNext, fun _ => rfl⟩

/-! ## Typed sequential/parallel composition -/

theorem sequential_abstraction_commutes
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    (encode : Fine → Coarse)
    (first second : Fine → Fine)
    (reducedFirst reducedSecond : Coarse → Coarse)
    (firstCommutes : OneStepCommutes encode first reducedFirst)
    (secondCommutes : OneStepCommutes encode second reducedSecond) :
    ∀ state,
      encode (second (first state)) =
        reducedSecond (reducedFirst (encode state)) := by
  intro state
  rw [secondCommutes, firstCommutes]

/-- Independent componentwise parallel composition preserves exact squares. -/
theorem independent_parallel_abstraction_commutes
    {FineLeft : Type uFine}
    {FineRight : Type uState}
    {CoarseLeft : Type uCoarse}
    {CoarseRight : Type uQuotient}
    (encodeLeft : FineLeft → CoarseLeft)
    (encodeRight : FineRight → CoarseRight)
    (stepLeft : FineLeft → FineLeft)
    (stepRight : FineRight → FineRight)
    (reducedLeft : CoarseLeft → CoarseLeft)
    (reducedRight : CoarseRight → CoarseRight)
    (leftCommutes : OneStepCommutes encodeLeft stepLeft reducedLeft)
    (rightCommutes : OneStepCommutes encodeRight stepRight reducedRight) :
    ∀ state : FineLeft × FineRight,
      (encodeLeft (stepLeft state.1), encodeRight (stepRight state.2)) =
        (reducedLeft (encodeLeft state.1), reducedRight (encodeRight state.2)) := by
  intro state
  exact Prod.ext (leftCommutes state.1) (rightCommutes state.2)

/-! ## Feedback and hidden-context obstructions -/

/-- A boundary-indexed stochastic mass operator. -/
abbrev BoundaryMassOperator
    (Boundary : Type uBoundary)
    (Mass : Type uState) := Boundary → Mass → Mass

/-- Uniform commutation over every admitted concrete boundary value. -/
def BoundaryOperatorCommutes
    {FineMass : Type uFine}
    {CoarseMass : Type uCoarse}
    {Boundary : Type uBoundary}
    {AbstractBoundary : Type uQuotient}
    (push : FineMass → CoarseMass)
    (encodeBoundary : Boundary → AbstractBoundary)
    (fine : BoundaryMassOperator Boundary FineMass)
    (coarse : BoundaryMassOperator AbstractBoundary CoarseMass) : Prop :=
  ∀ boundary mass,
    push (fine boundary mass) =
      coarse (encodeBoundary boundary) (push mass)

/-- Admissible sequential composition preserves uniform boundary commutation. -/
theorem boundary_conditioned_sequential_commutes
    {FineMass : Type uFine}
    {CoarseMass : Type uCoarse}
    {Boundary : Type uBoundary}
    {AbstractBoundary : Type uQuotient}
    (push : FineMass → CoarseMass)
    (encodeBoundary : Boundary → AbstractBoundary)
    (fineFirst fineSecond : BoundaryMassOperator Boundary FineMass)
    (coarseFirst coarseSecond : BoundaryMassOperator AbstractBoundary CoarseMass)
    (firstCommutes : BoundaryOperatorCommutes push encodeBoundary
      fineFirst coarseFirst)
    (secondCommutes : BoundaryOperatorCommutes push encodeBoundary
      fineSecond coarseSecond) :
    ∀ boundary mass,
      push (fineSecond boundary (fineFirst boundary mass)) =
        coarseSecond (encodeBoundary boundary)
          (coarseFirst (encodeBoundary boundary) (push mass)) := by
  intro boundary mass
  rw [secondCommutes, firstCommutes]

/-- Independent parallel state is represented by its two marginal mass vectors. -/
def independentParallelPush
    {FineLeft : Type uFine}
    {FineRight : Type uState}
    {CoarseLeft : Type uCoarse}
    {CoarseRight : Type uQuotient}
    (pushLeft : FineLeft → CoarseLeft)
    (pushRight : FineRight → CoarseRight) :
    FineLeft × FineRight → CoarseLeft × CoarseRight :=
  fun masses => (pushLeft masses.1, pushRight masses.2)

/--
Independent marginal parallel composition preserves exact commutation.  The
hidden-common-cause fixture below shows why this theorem cannot be extended to
arbitrary correlated joint laws without additional joint-state information.
-/
theorem independent_marginal_parallel_commutes
    {FineLeft : Type uFine}
    {FineRight : Type uState}
    {CoarseLeft : Type uCoarse}
    {CoarseRight : Type uQuotient}
    (pushLeft : FineLeft → CoarseLeft)
    (pushRight : FineRight → CoarseRight)
    (fineLeft : FineLeft → FineLeft)
    (fineRight : FineRight → FineRight)
    (coarseLeft : CoarseLeft → CoarseLeft)
    (coarseRight : CoarseRight → CoarseRight)
    (leftCommutes : ∀ mass, pushLeft (fineLeft mass) = coarseLeft (pushLeft mass))
    (rightCommutes : ∀ mass, pushRight (fineRight mass) = coarseRight (pushRight mass)) :
    ∀ masses : FineLeft × FineRight,
      independentParallelPush pushLeft pushRight
          (fineLeft masses.1, fineRight masses.2) =
        (coarseLeft (pushLeft masses.1), coarseRight (pushRight masses.2)) := by
  intro masses
  exact Prod.ext (leftCommutes masses.1) (rightCommutes masses.2)

def BoundaryResponseFactors
    {State : Type uState}
    {Boundary : Type uBoundary}
    {Quotient : Type uQuotient}
    {AbstractBoundary : Type uCoarse}
    {Output : Type uOutput}
    (encodeState : State → Quotient)
    (encodeBoundary : Boundary → AbstractBoundary)
    (response : State → Boundary → Output) : Prop :=
  ∃ reduced : Quotient → AbstractBoundary → Output,
    ∀ state boundary,
      reduced (encodeState state) (encodeBoundary boundary) =
        response state boundary

def BoundaryCongruence
    {State : Type uState}
    {Boundary : Type uBoundary}
    {Quotient : Type uQuotient}
    {AbstractBoundary : Type uCoarse}
    {Output : Type uOutput}
    (encodeState : State → Quotient)
    (encodeBoundary : Boundary → AbstractBoundary)
    (response : State → Boundary → Output) : Prop :=
  ∀ ⦃leftState rightState leftBoundary rightBoundary⦄,
    encodeState leftState = encodeState rightState →
    encodeBoundary leftBoundary = encodeBoundary rightBoundary →
      response leftState leftBoundary = response rightState rightBoundary

theorem feedback_factor_requires_boundary_congruence
    {State : Type uState}
    {Boundary : Type uBoundary}
    {Quotient : Type uQuotient}
    {AbstractBoundary : Type uCoarse}
    {Output : Type uOutput}
    (encodeState : State → Quotient)
    (encodeBoundary : Boundary → AbstractBoundary)
    (response : State → Boundary → Output)
    (factor : BoundaryResponseFactors encodeState encodeBoundary response) :
    BoundaryCongruence encodeState encodeBoundary response := by
  rcases factor with ⟨reduced, commutes⟩
  intro leftState rightState leftBoundary rightBoundary sameState sameBoundary
  calc
    response leftState leftBoundary =
        reduced (encodeState leftState) (encodeBoundary leftBoundary) :=
      (commutes leftState leftBoundary).symm
    _ = reduced (encodeState rightState) (encodeBoundary rightBoundary) := by
      rw [sameState, sameBoundary]
    _ = response rightState rightBoundary :=
      commutes rightState rightBoundary

def feedbackStateEncoder : Bool → Unit := fun _ => ()
def feedbackBoundaryEncoder : Unit → Unit := id
def feedbackResponse (state : Bool) (_ : Unit) : Bool := state

theorem feedback_without_boundary_congruence_no_go :
    ¬ BoundaryResponseFactors feedbackStateEncoder feedbackBoundaryEncoder
      feedbackResponse := by
  intro factor
  have congruence := feedback_factor_requires_boundary_congruence
    feedbackStateEncoder feedbackBoundaryEncoder feedbackResponse factor
  have impossible := congruence
    (leftState := false) (rightState := true)
    (leftBoundary := ()) (rightBoundary := ()) rfl rfl
  exact Bool.false_ne_true impossible

inductive CommonCause
  | correlated
  | anticorrelated
  deriving DecidableEq, Fintype, Repr

def jointMass : CommonCause → Bool × Bool → ℚ
  | .correlated, (false, false) => 1 / 2
  | .correlated, (true, true) => 1 / 2
  | .anticorrelated, (false, true) => 1 / 2
  | .anticorrelated, (true, false) => 1 / 2
  | _, _ => 0

def firstMarginal (cause : CommonCause) (value : Bool) : ℚ :=
  ∑ other : Bool, jointMass cause (value, other)

def secondMarginal (cause : CommonCause) (value : Bool) : ℚ :=
  ∑ other : Bool, jointMass cause (other, value)

/-- Two restricted local interfaces agree while a joint context distinguishes. -/
theorem hidden_common_cause_breaks_local_composition :
    (∀ value, firstMarginal .correlated value = firstMarginal .anticorrelated value) ∧
    (∀ value, secondMarginal .correlated value = secondMarginal .anticorrelated value) ∧
    jointMass .correlated (false, false) ≠
      jointMass .anticorrelated (false, false) := by
  constructor
  · intro value; cases value <;> norm_num [firstMarginal, jointMass]
  constructor
  · intro value; cases value <;> norm_num [secondMarginal, jointMass]
  · norm_num [jointMass]

end OCMaturityCompletionCycle
