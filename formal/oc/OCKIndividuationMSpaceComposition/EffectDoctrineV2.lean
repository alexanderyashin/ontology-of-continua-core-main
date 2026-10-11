import OCKIndividuationMSpaceComposition.OperatorTransport
import OCMaturityCompletionCycle.StochasticOpen
import OCMaturityCompletionCycle.IterativeDynamicsExpansionV2Measurable
import Mathlib.Tactic.NormNum

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe uA uB uC uD uX uA' uB' uEffect

/-!
# A pluggable typed effect calculus

The universally reusable denominator is a typed interface, not a claim that
all effects are faithfully relational.  Sequential, independent parallel,
feedback, and context transport are separated below.  Deterministic maps and
finite stochastic kernels have exact comparison maps into the interface, while
the established support counterexample records what is lost.
-/

/-- Operations shared by a typed effect family before a feedback law is chosen. -/
structure TypedEffectOperations
    (Effect : Type uEffect -> Type uEffect -> Type uEffect) where
  identity : {Carrier : Type uEffect} -> Effect Carrier Carrier
  sequential : {A B C : Type uEffect} ->
    Effect B C -> Effect A B -> Effect A C
  parallel : {A B C D : Type uEffect} ->
    Effect A B -> Effect C D -> Effect (A × C) (B × D)

/-- Quantitative operations whose middle carrier is explicitly finite. -/
structure FiniteTypedEffectOperations
    (Effect : Type uEffect -> Type uEffect -> Type uEffect) where
  identity : {Carrier : Type uEffect} ->
    [Fintype Carrier] -> [DecidableEq Carrier] -> Effect Carrier Carrier
  sequential : {A B C : Type uEffect} -> [Fintype B] ->
    Effect B C -> Effect A B -> Effect A C
  parallel : {A B C D : Type uEffect} ->
    Effect A B -> Effect C D -> Effect (A × C) (B × D)

/-- Feedback is typed together with the witness required to close its loop. -/
structure WitnessedFeedbackOperation
    (Effect : Type uEffect -> Type uEffect -> Type uEffect) where
  Witness : {A B X : Type uEffect} ->
    Effect (A × X) (B × X) -> Type uEffect
  feedback : {A B X : Type uEffect} ->
    (effect : Effect (A × X) (B × X)) ->
      Witness effect -> Effect A B

/--
Optional extensional contract for a witnessed feedback presentation.  It says
exactly that presented feedback edges are the edges obtained by closing one
loop value.  It does not assert the categorical trace laws (sliding,
vanishing, superposing, or yanking), which require additional operations and
witness-transport data.
-/
structure RelationallyExactFeedbackContract
    (Effect : Type uEffect -> Type uEffect -> Type uEffect)
    (present : {A B : Type uEffect} ->
      Effect A B -> RelOperator A B)
    (feedbackOperation : WitnessedFeedbackOperation Effect) : Prop where
  feedback_iff : {A B X : Type uEffect} ->
    (effect : Effect (A × X) (B × X)) ->
    (witness : feedbackOperation.Witness effect) ->
    (source : A) -> (target : B) ->
      present (feedbackOperation.feedback effect witness) source target <->
        exists loop : X, present effect (source, loop) (target, loop)

/--
Lawfulness of the identity/sequential/independent-parallel fragment.  Feedback
is intentionally excluded: trace/fixed-point laws require a separate witness
and cannot be derived from these operations.
-/
structure FiveLawTypedEffectFragment
    (Effect : Type uEffect -> Type uEffect -> Type uEffect)
    (operations : TypedEffectOperations Effect) : Prop where
  identity_sequential : {A B : Type uEffect} ->
    (effect : Effect A B) ->
      operations.sequential operations.identity effect = effect
  sequential_identity : {A B : Type uEffect} ->
    (effect : Effect A B) ->
      operations.sequential effect operations.identity = effect
  sequential_assoc : {A B C D : Type uEffect} ->
    (third : Effect C D) ->
    (second : Effect B C) ->
    (first : Effect A B) ->
      operations.sequential third
          (operations.sequential second first) =
        operations.sequential
          (operations.sequential third second) first
  parallel_identity : {A C : Type uEffect} ->
    operations.parallel
        (operations.identity (Carrier := A))
        (operations.identity (Carrier := C)) =
      operations.identity (Carrier := A × C)
  parallel_interchange : {A B C D E F : Type uEffect} ->
    (laterLeft : Effect B C) ->
    (earlierLeft : Effect A B) ->
    (laterRight : Effect E F) ->
    (earlierRight : Effect D E) ->
      operations.parallel
          (operations.sequential laterLeft earlierLeft)
          (operations.sequential laterRight earlierRight) =
        operations.sequential
          (operations.parallel laterLeft laterRight)
          (operations.parallel earlierLeft earlierRight)

/--
Compatibility name for the earlier source candidate.  The structure is only
the five laws displayed above; it is not a complete monoidal category,
traced doctrine, enrichment, or stochastic theory.
-/
abbrev LawfulTypedEffectOperations
    (Effect : Type uEffect -> Type uEffect -> Type uEffect)
    (operations : TypedEffectOperations Effect) : Prop :=
  FiveLawTypedEffectFragment Effect operations

/-- Independent parallel composition of relational effects. -/
def relParallel
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    (left : RelOperator A B)
    (right : RelOperator C D) :
    RelOperator (A × C) (B × D) :=
  fun source target => left source.1 target.1 /\ right source.2 target.2

/-- The relation doctrine supplies identity, sequence, and independent tensor. -/
def relationalEffectOperations :
    TypedEffectOperations
      (fun (A B : Type uEffect) => RelOperator A B) where
  identity := relIdentity
  sequential := relCompose
  parallel := relParallel

/-- Relations satisfy the complete identity/sequence/parallel law fragment. -/
def relationalEffectOperations_fiveLaw :
    FiveLawTypedEffectFragment
      (fun (A B : Type uEffect) => RelOperator A B)
      relationalEffectOperations where
  identity_sequential := relCompose_identity_left
  sequential_identity := relCompose_identity_right
  sequential_assoc := relCompose_assoc
  parallel_identity := by
    intro A C
    funext source target
    apply propext
    constructor
    · rintro ⟨left, right⟩
      exact Prod.ext left right
    · intro equal
      subst target
      exact ⟨rfl, rfl⟩
  parallel_interchange := by
    intro A B C D E F laterLeft earlierLeft laterRight earlierRight
    funext source target
    apply propext
    constructor
    · rintro ⟨⟨middleLeft, firstLeft, secondLeft⟩,
          ⟨middleRight, firstRight, secondRight⟩⟩
      exact ⟨(middleLeft, middleRight),
        ⟨firstLeft, firstRight⟩, ⟨secondLeft, secondRight⟩⟩
    · rintro ⟨middle, ⟨firstLeft, firstRight⟩,
          ⟨secondLeft, secondRight⟩⟩
      exact ⟨⟨middle.1, firstLeft, secondLeft⟩,
        ⟨middle.2, firstRight, secondRight⟩⟩

/-- Compatibility wrapper for the earlier declaration name. -/
def relationalEffectOperations_lawful :
    LawfulTypedEffectOperations
      (fun (A B : Type uEffect) => RelOperator A B)
      relationalEffectOperations :=
  relationalEffectOperations_fiveLaw

/-- Deterministic maps have the same three typed operations. -/
def deterministicEffectOperations :
    TypedEffectOperations
      (fun (A B : Type uEffect) => A -> B) where
  identity := id
  sequential := fun later earlier => later ∘ earlier
  parallel := fun left right source => (left source.1, right source.2)

/-- Deterministic functions satisfy the same law fragment extensionally. -/
def deterministicEffectOperations_fiveLaw :
    FiveLawTypedEffectFragment
      (fun (A B : Type uEffect) => A -> B)
      deterministicEffectOperations where
  identity_sequential := by intro A B effect; rfl
  sequential_identity := by intro A B effect; rfl
  sequential_assoc := by intro A B C D third second first; rfl
  parallel_identity := by
    intro A C
    funext state
    exact Prod.eta state
  parallel_interchange := by
    intro A B C D E F laterLeft earlierLeft laterRight earlierRight
    rfl

/-- Compatibility wrapper for the earlier declaration name. -/
def deterministicEffectOperations_lawful :
    LawfulTypedEffectOperations
      (fun (A B : Type uEffect) => A -> B)
      deterministicEffectOperations :=
  deterministicEffectOperations_fiveLaw

/-- The deterministic-to-relational comparison is faithful on every typed role. -/
theorem deterministicEffectPresentation_faithful
    {Source : Type uA}
    {Target : Type uB} :
    Function.Injective (@deterministicAsRel Source Target) :=
  deterministicAsRel_injective

/-- Graph embedding preserves typed identity exactly. -/
theorem deterministicAsRel_identity
    {Carrier : Type uA} :
    deterministicAsRel (id : Carrier -> Carrier) = relIdentity := by
  funext source target
  apply propext
  constructor <;> intro equal
  · exact equal.symm
  · exact equal.symm

/-- Graph embedding preserves independent parallel composition exactly. -/
theorem deterministicAsRel_parallel
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    (left : A -> B)
    (right : C -> D) :
    deterministicAsRel (fun source : A × C =>
        (left source.1, right source.2)) =
      relParallel (deterministicAsRel left) (deterministicAsRel right) := by
  funext source target
  apply propext
  constructor
  · intro edge
    change target = (left source.1, right source.2) at edge
    exact ⟨congrArg Prod.fst edge, congrArg Prod.snd edge⟩
  · rintro ⟨leftEdge, rightEdge⟩
    change target = (left source.1, right source.2)
    exact Prod.ext leftEdge rightEdge

/-!
## Feedback is a separate admissibility problem
-/

/-- Relational feedback closes a declared loop coordinate existentially. -/
def relFeedback
    {A : Type uA} {B : Type uB} {X : Type uX}
    (effect : RelOperator (A × X) (B × X)) : RelOperator A B :=
  fun source target => exists loop, effect (source, loop) (target, loop)

/-- Relational feedback needs no extra witness beyond `Unit`. -/
def relationalFeedbackOperation :
    WitnessedFeedbackOperation (fun A B => RelOperator A B) where
  Witness := fun _ => Unit
  feedback := fun effect _ => relFeedback effect

/-- Existential relational loop closure satisfies the extensional contract. -/
def relationalFeedbackOperation_exact :
    RelationallyExactFeedbackContract
      (fun A B => RelOperator A B)
      (fun effect => effect)
      relationalFeedbackOperation where
  feedback_iff := by
    intro A B X effect witness source target
    rfl

/-- A supplied deterministic loop selector, including its fixed-point proof. -/
structure DeterministicFeedbackSolution
    {A : Type uA} {B : Type uB} {X : Type uX}
    (effect : A × X -> B × X) where
  loop : A -> X
  closes : forall source, (effect (source, loop source)).2 = loop source

/-- A deterministic feedback map exists after a fixed-point selector is supplied. -/
def deterministicFeedback
    {A : Type uA} {B : Type uB} {X : Type uX}
    {effect : A × X -> B × X}
    (solution : DeterministicFeedbackSolution effect) : A -> B :=
  fun source => (effect (source, solution.loop source)).1

/-- Deterministic feedback requires exactly a fixed-point selector. -/
def deterministicFeedbackOperation :
    WitnessedFeedbackOperation (fun A B => A -> B) where
  Witness := fun effect => DeterministicFeedbackSolution effect
  feedback := fun _ solution => deterministicFeedback solution

/-- The selected deterministic feedback edge belongs to relational feedback. -/
theorem deterministicFeedback_supported
    {A : Type uA} {B : Type uB} {X : Type uX}
    {effect : A × X -> B × X}
    (solution : DeterministicFeedbackSolution effect)
    (source : A) :
    relFeedback (deterministicAsRel effect) source
      (deterministicFeedback solution source) := by
  refine ⟨solution.loop source, ?_⟩
  change
    (deterministicFeedback solution source, solution.loop source) =
      effect (source, solution.loop source)
  apply Prod.ext
  · rfl
  · exact (solution.closes source).symm

/-- Boolean loop negation has no fixed-point selector. -/
def boolLoopNegation : Unit × Bool -> Unit × Bool :=
  fun state => ((), !state.2)

/-- There is no total deterministic feedback doctrine without solvability data. -/
theorem boolLoopNegation_has_no_deterministicFeedbackSolution :
    IsEmpty (DeterministicFeedbackSolution boolLoopNegation) := by
  constructor
  intro solution
  have closes : !solution.loop () = solution.loop () := by
    simpa [boolLoopNegation] using solution.closes ()
  cases value : solution.loop () <;> simp [value] at closes

/--
A scoped total-selection contract for one deterministic carrier triple.  This
is stronger than the witnessed operation: it must solve every loop circuit of
the declared type.
-/
structure TotalDeterministicFeedbackSelection
    (A : Type uA) (B : Type uB) (X : Type uX) where
  select : (effect : A × X -> B × X) ->
    DeterministicFeedbackSolution effect

/--
Even the `Unit`/`Bool` fragment has no total solver-based deterministic
feedback selection.  The result does not rule out partial feedback, feedback
on restricted effect classes, relational trace, or another traced semantics.
-/
theorem unitBool_has_no_total_deterministicFeedbackSelection :
    IsEmpty (TotalDeterministicFeedbackSelection Unit Unit Bool) := by
  constructor
  intro selection
  exact boolLoopNegation_has_no_deterministicFeedbackSolution.false
    (selection.select boolLoopNegation)

/-!
## Finite quantitative and stochastic presentations
-/

/-- An unnormalized exact rational-weight effect. -/
abbrev RationalWeightedEffect (A : Type uA) (B : Type uB) :=
  A -> B -> ℚ

def rationalWeightedIdentity
    {Carrier : Type uA}
    [DecidableEq Carrier] : RationalWeightedEffect Carrier Carrier :=
  fun source target => if source = target then 1 else 0

def rationalWeightedSequential
    {A : Type uA} {B : Type uB} {C : Type uC}
    [Fintype B]
    (later : RationalWeightedEffect B C)
    (earlier : RationalWeightedEffect A B) : RationalWeightedEffect A C :=
  fun source target =>
    ∑ middle, earlier source middle * later middle target

def rationalWeightedParallel
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    (left : RationalWeightedEffect A B)
    (right : RationalWeightedEffect C D) :
    RationalWeightedEffect (A × C) (B × D) :=
  fun source target => left source.1 target.1 * right source.2 target.2

/-- Finite rational weights instantiate the finite quantitative interface. -/
def finiteRationalEffectOperations :
    FiniteTypedEffectOperations (fun A B => RationalWeightedEffect A B) where
  identity := rationalWeightedIdentity
  sequential := rationalWeightedSequential
  parallel := rationalWeightedParallel

/-!
No finite-interface analogue of `FiveLawTypedEffectFragment` is exported here.
The exact open proof package must align the required `Fintype` and
`DecidableEq` instances, prove the two finite-sum unit laws, finite-sum
associativity, product identity, and sum/product interchange.  Stochastic
closure is stricter still: these raw `ℚ` weights permit negative and
unnormalized rows, so nonnegativity and row-sum preservation are separate
premises rather than consequences of the operations.
-/

/-- Forget a rational law to its strictly positive relational support. -/
def rationalPositiveSupport
    {A : Type uA} {B : Type uB}
    (effect : RationalWeightedEffect A B) : RelOperator A B :=
  fun source target => 0 < effect source target

/-- First exact rational effect in the support-forgetting countermodel. -/
def rationalUnitBoolWeightOne : RationalWeightedEffect Unit Bool :=
  fun _ target => if target then 1 else 0

/-- A distinct rational effect with the same strictly positive support. -/
def rationalUnitBoolWeightTwo : RationalWeightedEffect Unit Bool :=
  fun _ target => if target then 2 else 0

theorem rationalUnitBoolWeights_distinct :
    rationalUnitBoolWeightOne ≠ rationalUnitBoolWeightTwo := by
  intro equal
  have atTrue := congrArg
    (fun effect : RationalWeightedEffect Unit Bool => effect () true) equal
  change (1 : ℚ) = 2 at atTrue
  norm_num at atTrue

theorem rationalUnitBoolWeights_same_positiveSupport :
    rationalPositiveSupport rationalUnitBoolWeightOne =
      rationalPositiveSupport rationalUnitBoolWeightTwo := by
  funext source target
  apply propext
  cases target <;>
    norm_num [rationalPositiveSupport, rationalUnitBoolWeightOne,
      rationalUnitBoolWeightTwo]

/-- Positive-support forgetting is non-faithful already for exact `ℚ` weights. -/
theorem rationalPositiveSupport_not_faithful :
    Not (Function.Injective (@rationalPositiveSupport Unit Bool)) := by
  intro injective
  exact rationalUnitBoolWeights_distinct
    (injective rationalUnitBoolWeights_same_positiveSupport)

/-- One fixed action of a finite stochastic kernel is an exact weighted effect. -/
def finiteKernelActionEffect
    {State : Type uA} {Action : Type uB}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (action : Action) : RationalWeightedEffect State State :=
  fun source target => kernel.mass source action target

/-- Its relational presentation is exactly positive stochastic support. -/
theorem finiteKernelActionEffect_support
    {State : Type uA} {Action : Type uB}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (action : Action)
    (source target : State) :
    rationalPositiveSupport (finiteKernelActionEffect kernel action)
        source target <->
      0 < kernel.mass source action target :=
  Iff.rfl

theorem finiteKernelActionEffect_recovers_action_row
    {State : Type uA} {Action : Type uB}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (action : Action)
    (source target : State) :
    finiteKernelActionEffect kernel action source target =
      kernel.mass source action target :=
  rfl

/-- Forgetting exact rational weights to support is non-faithful. -/
theorem generalizedEffect_support_forgetting_not_faithful :
    Not (Function.Injective (@rationalPositiveSupport Unit Bool)) :=
  rationalPositiveSupport_not_faithful

/-!
## Exact context transport for presented effects
-/

/-- Context transport is exact transport of the explicitly declared presentation. -/
abbrev ExactPresentedEffectTransport
    {Effect : Type uA}
    {Effect' : Type uB}
    {Source : Type uC} {Target : Type uD}
    {Source' : Type uA'} {Target' : Type uB'}
    (present : Effect -> RelOperator Source Target)
    (present' : Effect' -> RelOperator Source' Target')
    (effect : Effect)
    (effect' : Effect') :=
  ExactRelTransport (present effect) (present' effect')

/-- Exact presented-effect transports compose through the relational denominator. -/
def exactPresentedEffectTransport_comp
    {A B C D E F : Type}
    {first : RelOperator A B}
    {second : RelOperator C D}
    {third : RelOperator E F}
    (later : ExactRelTransport second third)
    (earlier : ExactRelTransport first second) :
    ExactRelTransport first third :=
  later.comp earlier

/-!
## Exact bridges to the maturity contour

These wrappers expose the already proved conditions without pretending that
support alone carries probabilities, joint dependence, or feedback closure.
-/

theorem finiteStochasticSequentialBridge
    {FineMass : Type uA}
    {CoarseMass : Type uB}
    (push : FineMass -> CoarseMass)
    (fineFirst fineSecond : FineMass -> FineMass)
    (coarseFirst coarseSecond : CoarseMass -> CoarseMass)
    (firstCommutes : forall mass,
      push (fineFirst mass) = coarseFirst (push mass))
    (secondCommutes : forall mass,
      push (fineSecond mass) = coarseSecond (push mass)) :
    forall mass,
      push (fineSecond (fineFirst mass)) =
        coarseSecond (coarseFirst (push mass)) :=
  stochastic_operator_sequential_commutes push fineFirst fineSecond
    coarseFirst coarseSecond firstCommutes secondCommutes

theorem finiteStochasticParallelBridge
    {FineLeft : Type uA} {FineRight : Type uB}
    {CoarseLeft : Type uC} {CoarseRight : Type uD}
    (pushLeft : FineLeft -> CoarseLeft)
    (pushRight : FineRight -> CoarseRight)
    (fineLeft : FineLeft -> FineLeft)
    (fineRight : FineRight -> FineRight)
    (coarseLeft : CoarseLeft -> CoarseLeft)
    (coarseRight : CoarseRight -> CoarseRight)
    (leftCommutes : forall mass,
      pushLeft (fineLeft mass) = coarseLeft (pushLeft mass))
    (rightCommutes : forall mass,
      pushRight (fineRight mass) = coarseRight (pushRight mass)) :
    forall masses : FineLeft × FineRight,
      independentParallelPush pushLeft pushRight
          (fineLeft masses.1, fineRight masses.2) =
        (coarseLeft (pushLeft masses.1),
          coarseRight (pushRight masses.2)) :=
  independent_marginal_parallel_commutes pushLeft pushRight
    fineLeft fineRight coarseLeft coarseRight leftCommutes rightCommutes

/-- Feedback factorization requires the existing boundary-congruence condition. -/
theorem feedbackEffect_requires_boundaryCongruence
    {State : Type uA}
    {Boundary : Type uB}
    {Quotient : Type uC}
    {AbstractBoundary : Type uD}
    {Output : Type uX}
    (encodeState : State -> Quotient)
    (encodeBoundary : Boundary -> AbstractBoundary)
    (response : State -> Boundary -> Output)
    (factor : BoundaryResponseFactors encodeState encodeBoundary response) :
    BoundaryCongruence encodeState encodeBoundary response :=
  feedback_factor_requires_boundary_congruence
    encodeState encodeBoundary response factor

/-- Local marginals do not determine an arbitrary correlated parallel effect. -/
theorem arbitraryParallelEffect_requires_joint_information :
    (forall value,
      firstMarginal .correlated value = firstMarginal .anticorrelated value) /\
    (forall value,
      secondMarginal .correlated value = secondMarginal .anticorrelated value) /\
    jointMass .correlated (false, false) ≠
      jointMass .anticorrelated (false, false) :=
  hidden_common_cause_breaks_local_composition

/-- The measurable contour currently stops at the stated one-step boundary. -/
theorem measurableEffectBridge_current_ceiling :
    iterativeDynamicsExpansionV2MeasurableScope =
      "STANDARD_BOREL_ONE_STEP_OPEN_INPUT_OUTPUT_SPECIALIZATION_PENDING_PATH_TRANSPORT" :=
  rfl

/-!
Thus relation is one common structural presentation; deterministic graphs are
faithful and preserve identity/sequence/parallel; the proved algebraic package
is exactly a five-law fragment, not a complete effect doctrine; finite
stochastic action rows preserve exact rational mass; rational positive-support
forgetting is non-faithful; independent parallel and sequential transports are
conditional positive theorems; and feedback lawfulness beyond extensional
relational closure remains witness- and domain-supplied.
-/

end OCKIndividuationMSpaceComposition
