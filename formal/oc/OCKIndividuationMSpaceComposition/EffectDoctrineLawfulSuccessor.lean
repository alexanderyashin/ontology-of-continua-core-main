import OCKIndividuationMSpaceComposition.EffectDoctrineV2
import OCMaturityCompletionCycle.JointPathTransport
import OCMaturityCompletionCycle.FiniteJointFeedbackPath
import OCMaturityCompletionCycle.OpenStandardBorelSpecialization
import Mathlib.Tactic.Ring

set_option autoImplicit false
set_option warningAsError true

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle
open MeasureTheory

universe uA uB uC uD uE uF uX uY uEffect uEvidence

/-!
# Lawful quantitative and witnessed-feedback successor

This additive module closes the purely formal finite-rational algebra left open
by `EffectDoctrineV2`, separates normalized stochastic rows from arbitrary
signed weights, characterizes exactly when positive support respects sequence
and independent parallel, and proves a scoped deterministic trace package by
transporting explicit fixed-point witnesses.

It also exposes the already proved finite joint/path transport theorems and the
measurable one-step theorem through this import closure.  Measurable path-space
construction, a bridge from categorical loop feedback to policy feedback, and
domain calibration remain explicit typed residuals at the end of the file.
-/

/-! ## The finite analogue of the five-law fragment -/

/--
The finite-carrier analogue of `FiveLawTypedEffectFragment`.  Every law states
exactly the `Fintype`/`DecidableEq` premises needed by the chosen occurrence of
finite summation or identity.  It is not a traced or enriched doctrine.
-/
structure FiniteFiveLawTypedEffectFragment
    (Effect : Type uEffect -> Type uEffect -> Type uEffect)
    (operations : FiniteTypedEffectOperations Effect) : Prop where
  identity_sequential : {A B : Type uEffect} ->
    [Fintype B] -> [DecidableEq B] ->
    (effect : Effect A B) ->
      operations.sequential operations.identity effect = effect
  sequential_identity : {A B : Type uEffect} ->
    [Fintype A] -> [DecidableEq A] ->
    (effect : Effect A B) ->
      operations.sequential effect operations.identity = effect
  sequential_assoc : {A B C D : Type uEffect} ->
    [Fintype B] -> [Fintype C] ->
    (third : Effect C D) ->
    (second : Effect B C) ->
    (first : Effect A B) ->
      operations.sequential third
          (operations.sequential second first) =
        operations.sequential
          (operations.sequential third second) first
  parallel_identity : {A C : Type uEffect} ->
    [Fintype A] -> [DecidableEq A] ->
    [Fintype C] -> [DecidableEq C] ->
      operations.parallel
          (operations.identity (Carrier := A))
          (operations.identity (Carrier := C)) =
        operations.identity (Carrier := A × C)
  parallel_interchange : {A B C D E F : Type uEffect} ->
    [Fintype B] -> [Fintype E] ->
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

theorem rationalWeightedSequential_identity_left
    {A : Type uA} {B : Type uB}
    [Fintype B] [DecidableEq B]
    (effect : RationalWeightedEffect A B) :
    rationalWeightedSequential rationalWeightedIdentity effect = effect := by
  funext source target
  simp [rationalWeightedSequential, rationalWeightedIdentity]

theorem rationalWeightedSequential_identity_right
    {A : Type uA} {B : Type uB}
    [Fintype A] [DecidableEq A]
    (effect : RationalWeightedEffect A B) :
    rationalWeightedSequential effect rationalWeightedIdentity = effect := by
  funext source target
  simp [rationalWeightedSequential, rationalWeightedIdentity]

theorem rationalWeightedSequential_assoc
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    [Fintype B] [Fintype C]
    (third : RationalWeightedEffect C D)
    (second : RationalWeightedEffect B C)
    (first : RationalWeightedEffect A B) :
    rationalWeightedSequential third
        (rationalWeightedSequential second first) =
      rationalWeightedSequential
        (rationalWeightedSequential third second) first := by
  classical
  funext source target
  simp only [rationalWeightedSequential]
  simp_rw [Finset.sum_mul]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro middleB _
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro middleC _
  ring

theorem rationalWeightedParallel_identity
    {A : Type uA} {C : Type uC}
    [Fintype A] [DecidableEq A]
    [Fintype C] [DecidableEq C] :
    rationalWeightedParallel
        (rationalWeightedIdentity (Carrier := A))
        (rationalWeightedIdentity (Carrier := C)) =
      rationalWeightedIdentity (Carrier := A × C) := by
  funext source target
  by_cases leftEqual : source.1 = target.1 <;>
    by_cases rightEqual : source.2 = target.2 <;>
      simp [rationalWeightedParallel, rationalWeightedIdentity,
        leftEqual, rightEqual, Prod.ext_iff]

theorem rationalWeightedParallel_interchange
    {A : Type uA} {B : Type uB} {C : Type uC}
    {D : Type uD} {E : Type uE} {F : Type uF}
    [Fintype B] [Fintype E]
    (laterLeft : RationalWeightedEffect B C)
    (earlierLeft : RationalWeightedEffect A B)
    (laterRight : RationalWeightedEffect E F)
    (earlierRight : RationalWeightedEffect D E) :
    rationalWeightedParallel
        (rationalWeightedSequential laterLeft earlierLeft)
        (rationalWeightedSequential laterRight earlierRight) =
      rationalWeightedSequential
        (rationalWeightedParallel laterLeft laterRight)
        (rationalWeightedParallel earlierLeft earlierRight) := by
  classical
  funext source target
  simp only [rationalWeightedParallel, rationalWeightedSequential]
  rw [Fintype.sum_prod_type, Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro middleLeft _
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro middleRight _
  ring

/-- Raw exact rational weights satisfy all five finite-carrier laws. -/
def finiteRationalEffectOperations_fiveLaw :
    FiniteFiveLawTypedEffectFragment
      (fun (A B : Type uEffect) =>
        RationalWeightedEffect.{uEffect, uEffect} A B)
      finiteRationalEffectOperations.{uEffect} where
  identity_sequential := rationalWeightedSequential_identity_left
  sequential_identity := rationalWeightedSequential_identity_right
  sequential_assoc := rationalWeightedSequential_assoc
  parallel_identity := rationalWeightedParallel_identity
  parallel_interchange := rationalWeightedParallel_interchange

/-! ## Normalized nonnegative stochastic subfamily -/

def RationalEffectNonnegative
    {A : Type uA} {B : Type uB}
    (effect : RationalWeightedEffect A B) : Prop :=
  ∀ source target, 0 ≤ effect source target

def RationalEffectNormalized
    {A : Type uA} {B : Type uB}
    [Fintype B]
    (effect : RationalWeightedEffect A B) : Prop :=
  ∀ source, (∑ target, effect source target) = 1

/-- A typed exact rational effect whose every target row is a probability law. -/
structure FiniteRationalStochasticEffect
    (A : Type uA) (B : Type uB) [Fintype B] where
  weight : RationalWeightedEffect A B
  nonnegative : RationalEffectNonnegative weight
  normalized : RationalEffectNormalized weight

theorem rationalWeightedIdentity_nonnegative
    {A : Type uA} [Fintype A] [DecidableEq A] :
    RationalEffectNonnegative
      (rationalWeightedIdentity (Carrier := A)) := by
  intro source target
  by_cases equal : source = target <;>
    simp [rationalWeightedIdentity, equal]

theorem rationalWeightedIdentity_normalized
    {A : Type uA} [Fintype A] [DecidableEq A] :
    RationalEffectNormalized
      (rationalWeightedIdentity (Carrier := A)) := by
  intro source
  simp [rationalWeightedIdentity]

theorem rationalWeightedSequential_nonnegative
    {A : Type uA} {B : Type uB} {C : Type uC}
    [Fintype B]
    {later : RationalWeightedEffect B C}
    {earlier : RationalWeightedEffect A B}
    (laterNonnegative : RationalEffectNonnegative later)
    (earlierNonnegative : RationalEffectNonnegative earlier) :
    RationalEffectNonnegative
      (rationalWeightedSequential later earlier) := by
  intro source target
  apply Finset.sum_nonneg
  intro middle _
  exact mul_nonneg
    (earlierNonnegative source middle)
    (laterNonnegative middle target)

theorem rationalWeightedSequential_normalized
    {A : Type uA} {B : Type uB} {C : Type uC}
    [Fintype B] [Fintype C]
    {later : RationalWeightedEffect B C}
    {earlier : RationalWeightedEffect A B}
    (laterNormalized : RationalEffectNormalized later)
    (earlierNormalized : RationalEffectNormalized earlier) :
    RationalEffectNormalized
      (rationalWeightedSequential later earlier) := by
  intro source
  simp only [rationalWeightedSequential]
  rw [Finset.sum_comm]
  calc
    (∑ middle, ∑ target,
        earlier source middle * later middle target) =
        ∑ middle, earlier source middle *
          (∑ target, later middle target) := by
      apply Finset.sum_congr rfl
      intro middle _
      rw [Finset.mul_sum]
    _ = ∑ middle, earlier source middle := by
      apply Finset.sum_congr rfl
      intro middle _
      rw [laterNormalized middle]
      ring
    _ = 1 := earlierNormalized source

theorem rationalWeightedParallel_nonnegative
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    {left : RationalWeightedEffect A B}
    {right : RationalWeightedEffect C D}
    (leftNonnegative : RationalEffectNonnegative left)
    (rightNonnegative : RationalEffectNonnegative right) :
    RationalEffectNonnegative (rationalWeightedParallel left right) := by
  intro source target
  exact mul_nonneg
    (leftNonnegative source.1 target.1)
    (rightNonnegative source.2 target.2)

theorem rationalWeightedParallel_normalized
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    [Fintype B] [Fintype D]
    {left : RationalWeightedEffect A B}
    {right : RationalWeightedEffect C D}
    (leftNormalized : RationalEffectNormalized left)
    (rightNormalized : RationalEffectNormalized right) :
    RationalEffectNormalized (rationalWeightedParallel left right) := by
  intro source
  simp only [rationalWeightedParallel]
  rw [Fintype.sum_prod_type]
  calc
    (∑ leftTarget, ∑ rightTarget,
        left source.1 leftTarget * right source.2 rightTarget) =
        (∑ leftTarget, left source.1 leftTarget) *
          (∑ rightTarget, right source.2 rightTarget) := by
      rw [Finset.sum_mul]
      apply Finset.sum_congr rfl
      intro leftTarget _
      rw [Finset.mul_sum]
    _ = 1 := by
      rw [leftNormalized source.1, rightNormalized source.2]
      norm_num

def finiteRationalStochasticIdentity
    {A : Type uA} [Fintype A] [DecidableEq A] :
    FiniteRationalStochasticEffect A A where
  weight := rationalWeightedIdentity
  nonnegative := rationalWeightedIdentity_nonnegative
  normalized := rationalWeightedIdentity_normalized

def FiniteRationalStochasticEffect.sequential
    {A : Type uA} {B : Type uB} {C : Type uC}
    [Fintype B] [Fintype C]
    (later : FiniteRationalStochasticEffect B C)
    (earlier : FiniteRationalStochasticEffect A B) :
    FiniteRationalStochasticEffect A C where
  weight := rationalWeightedSequential later.weight earlier.weight
  nonnegative := rationalWeightedSequential_nonnegative
    later.nonnegative earlier.nonnegative
  normalized := rationalWeightedSequential_normalized
    later.normalized earlier.normalized

def FiniteRationalStochasticEffect.parallel
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    [Fintype B] [Fintype D]
    (left : FiniteRationalStochasticEffect A B)
    (right : FiniteRationalStochasticEffect C D) :
    FiniteRationalStochasticEffect (A × C) (B × D) where
  weight := rationalWeightedParallel left.weight right.weight
  nonnegative := rationalWeightedParallel_nonnegative
    left.nonnegative right.nonnegative
  normalized := rationalWeightedParallel_normalized
    left.normalized right.normalized

/-! ## Exact comparison with positive relational support -/

theorem rationalPositiveSupport_identity
    {A : Type uA} [Fintype A] [DecidableEq A] :
    rationalPositiveSupport
        (rationalWeightedIdentity (Carrier := A)) =
      relIdentity := by
  funext source target
  apply propext
  change (0 < if source = target then (1 : ℚ) else 0) ↔ source = target
  by_cases equal : source = target <;> simp [equal]

theorem rationalPositiveSupport_sequential_iff
    {A : Type uA} {B : Type uB} {C : Type uC}
    [Fintype B]
    (later : RationalWeightedEffect B C)
    (earlier : RationalWeightedEffect A B)
    (laterNonnegative : RationalEffectNonnegative later)
    (earlierNonnegative : RationalEffectNonnegative earlier)
    (source : A) (target : C) :
    rationalPositiveSupport
        (rationalWeightedSequential later earlier) source target ↔
      ∃ middle,
        rationalPositiveSupport earlier source middle ∧
          rationalPositiveSupport later middle target := by
  classical
  change 0 < (∑ middle, earlier source middle * later middle target) ↔ _
  have termNonnegative : ∀ middle ∈ (Finset.univ : Finset B),
      0 ≤ earlier source middle * later middle target := by
    intro middle _
    exact mul_nonneg
      (earlierNonnegative source middle)
      (laterNonnegative middle target)
  rw [Finset.sum_pos_iff_of_nonneg termNonnegative]
  constructor
  · rintro ⟨middle, _, productPositive⟩
    rcases (mul_pos_iff.mp productPositive) with
      ⟨earlierPositive, laterPositive⟩ | ⟨earlierNegative, _⟩
    · exact ⟨middle, earlierPositive, laterPositive⟩
    · exact False.elim
        ((not_lt_of_ge (earlierNonnegative source middle)) earlierNegative)
  · rintro ⟨middle, earlierPositive, laterPositive⟩
    exact ⟨middle, Finset.mem_univ middle,
      mul_pos earlierPositive laterPositive⟩

theorem rationalPositiveSupport_sequential
    {A : Type uA} {B : Type uB} {C : Type uC}
    [Fintype B]
    (later : RationalWeightedEffect B C)
    (earlier : RationalWeightedEffect A B)
    (laterNonnegative : RationalEffectNonnegative later)
    (earlierNonnegative : RationalEffectNonnegative earlier) :
    rationalPositiveSupport
        (rationalWeightedSequential later earlier) =
      relCompose
        (rationalPositiveSupport later)
        (rationalPositiveSupport earlier) := by
  funext source target
  apply propext
  exact rationalPositiveSupport_sequential_iff later earlier
    laterNonnegative earlierNonnegative source target

theorem rationalPositiveSupport_parallel_iff
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    (left : RationalWeightedEffect A B)
    (right : RationalWeightedEffect C D)
    (leftNonnegative : RationalEffectNonnegative left)
    (rightNonnegative : RationalEffectNonnegative right)
    (source : A × C) (target : B × D) :
    rationalPositiveSupport (rationalWeightedParallel left right)
        source target ↔
      rationalPositiveSupport left source.1 target.1 ∧
        rationalPositiveSupport right source.2 target.2 := by
  change 0 < left source.1 target.1 * right source.2 target.2 ↔ _
  constructor
  · intro productPositive
    rcases (mul_pos_iff.mp productPositive) with
      ⟨leftPositive, rightPositive⟩ | ⟨leftNegative, rightNegative⟩
    · exact ⟨leftPositive, rightPositive⟩
    · exact False.elim
        ((not_lt_of_ge
          (add_nonneg
            (leftNonnegative source.1 target.1)
            (rightNonnegative source.2 target.2)))
          (add_neg leftNegative rightNegative))
  · rintro ⟨leftPositive, rightPositive⟩
    exact mul_pos leftPositive rightPositive

theorem rationalPositiveSupport_parallel
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    (left : RationalWeightedEffect A B)
    (right : RationalWeightedEffect C D)
    (leftNonnegative : RationalEffectNonnegative left)
    (rightNonnegative : RationalEffectNonnegative right) :
    rationalPositiveSupport (rationalWeightedParallel left right) =
      relParallel
        (rationalPositiveSupport left)
        (rationalPositiveSupport right) := by
  funext source target
  apply propext
  exact rationalPositiveSupport_parallel_iff left right
    leftNonnegative rightNonnegative source target

/-! ## Explicit joint-marginal boundary -/

def rationalLeftMarginal
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    [Fintype D]
    (joint : RationalWeightedEffect (A × C) (B × D)) :
    RationalWeightedEffect (A × C) B :=
  fun source leftTarget => ∑ rightTarget, joint source (leftTarget, rightTarget)

def rationalRightMarginal
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    [Fintype B]
    (joint : RationalWeightedEffect (A × C) (B × D)) :
    RationalWeightedEffect (A × C) D :=
  fun source rightTarget => ∑ leftTarget, joint source (leftTarget, rightTarget)

/--
Marginal equalities for an exact rational joint weight.  The weights may be
signed: this certificate alone establishes neither probability-law validity
nor independence for an arbitrary supplied joint.
-/
structure RationalJointMarginalCertificate
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    [Fintype B] [Fintype D]
    (joint : RationalWeightedEffect (A × C) (B × D))
    (left : RationalWeightedEffect A B)
    (right : RationalWeightedEffect C D) : Prop where
  left_marginal : ∀ source leftTarget,
    rationalLeftMarginal joint source leftTarget =
      left source.1 leftTarget
  right_marginal : ∀ source rightTarget,
    rationalRightMarginal joint source rightTarget =
      right source.2 rightTarget

theorem rationalWeightedParallel_leftMarginal
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    [Fintype D]
    (left : RationalWeightedEffect A B)
    (right : RationalWeightedEffect C D)
    (rightNormalized : RationalEffectNormalized right)
    (source : A × C) (leftTarget : B) :
    rationalLeftMarginal (rationalWeightedParallel left right)
        source leftTarget =
      left source.1 leftTarget := by
  simp only [rationalLeftMarginal, rationalWeightedParallel]
  rw [← Finset.mul_sum, rightNormalized source.2]
  ring

theorem rationalWeightedParallel_rightMarginal
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    [Fintype B]
    (left : RationalWeightedEffect A B)
    (right : RationalWeightedEffect C D)
    (leftNormalized : RationalEffectNormalized left)
    (source : A × C) (rightTarget : D) :
    rationalRightMarginal (rationalWeightedParallel left right)
        source rightTarget =
      right source.2 rightTarget := by
  simp only [rationalRightMarginal, rationalWeightedParallel]
  rw [← Finset.sum_mul, leftNormalized source.1]
  ring

def rationalWeightedParallel_marginalCertificate
    {A : Type uA} {B : Type uB} {C : Type uC} {D : Type uD}
    [Fintype B] [Fintype D]
    (left : RationalWeightedEffect A B)
    (right : RationalWeightedEffect C D)
    (leftNormalized : RationalEffectNormalized left)
    (rightNormalized : RationalEffectNormalized right) :
    RationalJointMarginalCertificate
      (rationalWeightedParallel left right) left right where
  left_marginal := rationalWeightedParallel_leftMarginal
    left right rightNormalized
  right_marginal := rationalWeightedParallel_rightMarginal
    left right leftNormalized

theorem finiteKernelActionEffect_nonnegative
    {State : Type uA} {Action : Type uB}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (action : Action) :
    RationalEffectNonnegative (finiteKernelActionEffect kernel action) := by
  intro source target
  exact kernel.nonnegative source action target

theorem finiteKernelActionEffect_normalized
    {State : Type uA} {Action : Type uB}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (action : Action) :
    RationalEffectNormalized (finiteKernelActionEffect kernel action) := by
  intro source
  exact kernel.normalized source action

def finiteKernelActionStochasticEffect
    {State : Type uA} {Action : Type uB}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (action : Action) :
    FiniteRationalStochasticEffect State State where
  weight := finiteKernelActionEffect kernel action
  nonnegative := finiteKernelActionEffect_nonnegative kernel action
  normalized := finiteKernelActionEffect_normalized kernel action

/-! ## Witness-dependent deterministic trace laws -/

/-- Exact reparameterization of a deterministic loop carrier. -/
structure DeterministicLoopConjugacy
    {A : Type uA} {B : Type uB} {X : Type uX} {Y : Type uY}
    (loopEquiv : X ≃ Y)
    (effectX : A × X -> B × X)
    (effectY : A × Y -> B × Y) : Prop where
  commutes : ∀ source loop,
    effectY (source, loopEquiv loop) =
      ((effectX (source, loop)).1,
        loopEquiv (effectX (source, loop)).2)

def DeterministicFeedbackSolution.transport
    {A : Type uA} {B : Type uB} {X : Type uX} {Y : Type uY}
    {loopEquiv : X ≃ Y}
    {effectX : A × X -> B × X}
    {effectY : A × Y -> B × Y}
    (solution : DeterministicFeedbackSolution effectX)
    (conjugacy : DeterministicLoopConjugacy loopEquiv effectX effectY) :
    DeterministicFeedbackSolution effectY where
  loop source := loopEquiv (solution.loop source)
  closes source := by
    calc
      (effectY (source, loopEquiv (solution.loop source))).2 =
          loopEquiv (effectX (source, solution.loop source)).2 :=
        congrArg Prod.snd (conjugacy.commutes source (solution.loop source))
      _ = loopEquiv (solution.loop source) :=
        congrArg loopEquiv (solution.closes source)

theorem deterministicFeedback_transport
    {A : Type uA} {B : Type uB} {X : Type uX} {Y : Type uY}
    {loopEquiv : X ≃ Y}
    {effectX : A × X -> B × X}
    {effectY : A × Y -> B × Y}
    (conjugacy : DeterministicLoopConjugacy loopEquiv effectX effectY)
    (solution : DeterministicFeedbackSolution effectX) :
    deterministicFeedback (solution.transport conjugacy) =
      deterministicFeedback solution := by
  funext source
  simpa [deterministicFeedback, DeterministicFeedbackSolution.transport] using
    congrArg Prod.fst
      (conjugacy.commutes source (solution.loop source))

def DeterministicFeedbackOutputUnique
    {A : Type uA} {B : Type uB} {X : Type uX}
    (effect : A × X -> B × X) : Prop :=
  ∀ source leftLoop rightLoop,
    (effect (source, leftLoop)).2 = leftLoop ->
    (effect (source, rightLoop)).2 = rightLoop ->
      (effect (source, leftLoop)).1 =
        (effect (source, rightLoop)).1

theorem deterministicFeedback_solution_independent
    {A : Type uA} {B : Type uB} {X : Type uX}
    {effect : A × X -> B × X}
    (outputUnique : DeterministicFeedbackOutputUnique effect)
    (left right : DeterministicFeedbackSolution effect) :
    deterministicFeedback left = deterministicFeedback right := by
  funext source
  exact outputUnique source (left.loop source) (right.loop source)
    (left.closes source) (right.closes source)

/-- A fixed point can be selected in two ways with observably different output. -/
def boolChoiceFeedbackEffect : Unit × Bool -> Bool × Bool :=
  fun state => (state.2, state.2)

def boolChoiceFeedbackFalseSolution :
    DeterministicFeedbackSolution boolChoiceFeedbackEffect where
  loop _ := false
  closes _ := rfl

def boolChoiceFeedbackTrueSolution :
    DeterministicFeedbackSolution boolChoiceFeedbackEffect where
  loop _ := true
  closes _ := rfl

theorem boolChoiceFeedback_solutions_have_distinct_outputs :
    deterministicFeedback boolChoiceFeedbackFalseSolution ≠
      deterministicFeedback boolChoiceFeedbackTrueSolution := by
  intro equal
  have atUnit := congrFun equal ()
  simp [deterministicFeedback, boolChoiceFeedbackFalseSolution,
    boolChoiceFeedbackTrueSolution, boolChoiceFeedbackEffect] at atUnit

theorem boolChoiceFeedback_not_outputUnique :
    ¬ DeterministicFeedbackOutputUnique boolChoiceFeedbackEffect := by
  intro outputUnique
  exact boolChoiceFeedback_solutions_have_distinct_outputs
    (deterministicFeedback_solution_independent outputUnique
      boolChoiceFeedbackFalseSolution boolChoiceFeedbackTrueSolution)

def deterministicFeedbackTightenEffect
    {A' : Type uA} {A : Type uB} {B : Type uC}
    {B' : Type uD} {X : Type uX}
    (before : A' -> A)
    (after : B -> B')
    (effect : A × X -> B × X) :
    A' × X -> B' × X :=
  fun state =>
    let output := effect (before state.1, state.2)
    (after output.1, output.2)

def DeterministicFeedbackSolution.tighten
    {A' : Type uA} {A : Type uB} {B : Type uC}
    {B' : Type uD} {X : Type uX}
    {before : A' -> A}
    {after : B -> B'}
    {effect : A × X -> B × X}
    (solution : DeterministicFeedbackSolution effect) :
    DeterministicFeedbackSolution
      (deterministicFeedbackTightenEffect before after effect) where
  loop source := solution.loop (before source)
  closes source := solution.closes (before source)

theorem deterministicFeedback_tightening
    {A' : Type uA} {A : Type uB} {B : Type uC}
    {B' : Type uD} {X : Type uX}
    {before : A' -> A}
    {after : B -> B'}
    {effect : A × X -> B × X}
    (solution : DeterministicFeedbackSolution effect) :
    deterministicFeedback (solution.tighten (before := before) (after := after)) =
      after ∘ deterministicFeedback solution ∘ before := by
  rfl

def deterministicFeedbackSlideLeftEffect
    {A : Type uA} {B : Type uB} {X : Type uX} {Y : Type uY}
    (effect : A × X -> B × Y)
    (slide : Y -> X) : A × X -> B × X :=
  fun state =>
    let output := effect state
    (output.1, slide output.2)

def deterministicFeedbackSlideRightEffect
    {A : Type uA} {B : Type uB} {X : Type uX} {Y : Type uY}
    (effect : A × X -> B × Y)
    (slide : Y -> X) : A × Y -> B × Y :=
  fun state => effect (state.1, slide state.2)

def DeterministicFeedbackSolution.slide
    {A : Type uA} {B : Type uB} {X : Type uX} {Y : Type uY}
    {effect : A × X -> B × Y}
    {slide : Y -> X}
    (solution : DeterministicFeedbackSolution
      (deterministicFeedbackSlideLeftEffect effect slide)) :
    DeterministicFeedbackSolution
      (deterministicFeedbackSlideRightEffect effect slide) where
  loop source := (effect (source, solution.loop source)).2
  closes source := by
    have closes :
        slide (effect (source, solution.loop source)).2 =
          solution.loop source := by
      simpa [deterministicFeedbackSlideLeftEffect] using
        solution.closes source
    rw [deterministicFeedbackSlideRightEffect, closes]

theorem deterministicFeedback_sliding
    {A : Type uA} {B : Type uB} {X : Type uX} {Y : Type uY}
    {effect : A × X -> B × Y}
    {slide : Y -> X}
    (solution : DeterministicFeedbackSolution
      (deterministicFeedbackSlideLeftEffect effect slide)) :
    deterministicFeedback solution.slide =
      deterministicFeedback solution := by
  funext source
  have closes :
      slide (effect (source, solution.loop source)).2 =
        solution.loop source := by
    simpa [deterministicFeedbackSlideLeftEffect] using
      solution.closes source
  change
    (effect (source,
      slide (effect (source, solution.loop source)).2)).1 =
      (effect (source, solution.loop source)).1
  rw [closes]

def deterministicUnitFeedbackSolution
    {A : Type uA} {B : Type uB}
    (effect : A × Unit -> B × Unit) :
    DeterministicFeedbackSolution effect where
  loop _ := ()
  closes _ := Subsingleton.elim _ _

theorem deterministicFeedback_vanishing_one
    {A : Type uA} {B : Type uB}
    (effect : A × Unit -> B × Unit) :
    deterministicFeedback (deterministicUnitFeedbackSolution effect) =
      fun source => (effect (source, ())).1 := by
  rfl

def deterministicFeedbackSuperposeEffect
    {A : Type uA} {B : Type uB} {C : Type uC}
    {D : Type uD} {X : Type uX}
    (effect : A × X -> B × X)
    (other : C -> D) :
    (A × C) × X -> (B × D) × X :=
  fun state =>
    let output := effect (state.1.1, state.2)
    ((output.1, other state.1.2), output.2)

def DeterministicFeedbackSolution.superpose
    {A : Type uA} {B : Type uB} {C : Type uC}
    {D : Type uD} {X : Type uX}
    {effect : A × X -> B × X}
    {other : C -> D}
    (solution : DeterministicFeedbackSolution effect) :
    DeterministicFeedbackSolution
      (deterministicFeedbackSuperposeEffect effect other) where
  loop source := solution.loop source.1
  closes source := solution.closes source.1

theorem deterministicFeedback_superposing
    {A : Type uA} {B : Type uB} {C : Type uC}
    {D : Type uD} {X : Type uX}
    {effect : A × X -> B × X}
    {other : C -> D}
    (solution : DeterministicFeedbackSolution effect) :
    deterministicFeedback (solution.superpose (other := other)) =
      fun source => (deterministicFeedback solution source.1, other source.2) := by
  rfl

def deterministicFeedbackSwapEffect
    {X : Type uX} : X × X -> X × X :=
  fun state => (state.2, state.1)

def deterministicFeedbackSwapSolution
    {X : Type uX} :
    DeterministicFeedbackSolution
      (deterministicFeedbackSwapEffect (X := X)) where
  loop source := source
  closes _ := rfl

theorem deterministicFeedback_yanking
    {X : Type uX} :
    deterministicFeedback
        (deterministicFeedbackSwapSolution (X := X)) =
      id := by
  rfl

def deterministicNestedInnerEffect
    {A : Type uA} {B : Type uB} {X : Type uX} {Y : Type uY}
    (effect : A × (X × Y) -> B × (X × Y)) :
    (A × X) × Y -> (B × X) × Y :=
  fun state =>
    let output := effect (state.1.1, (state.1.2, state.2))
    ((output.1, output.2.1), output.2.2)

def DeterministicFeedbackSolution.nest
    {A : Type uA} {B : Type uB} {X : Type uX} {Y : Type uY}
    {effect : A × (X × Y) -> B × (X × Y)}
    (inner : DeterministicFeedbackSolution
      (deterministicNestedInnerEffect effect))
    (outer : DeterministicFeedbackSolution
      (deterministicFeedback inner)) :
    DeterministicFeedbackSolution effect where
  loop source := (outer.loop source, inner.loop (source, outer.loop source))
  closes source := by
    apply Prod.ext
    · simpa [deterministicFeedback, deterministicNestedInnerEffect] using
        outer.closes source
    · simpa [deterministicNestedInnerEffect] using
        inner.closes (source, outer.loop source)

theorem deterministicFeedback_vanishing_two
    {A : Type uA} {B : Type uB} {X : Type uX} {Y : Type uY}
    {effect : A × (X × Y) -> B × (X × Y)}
    (inner : DeterministicFeedbackSolution
      (deterministicNestedInnerEffect effect))
    (outer : DeterministicFeedbackSolution
      (deterministicFeedback inner)) :
    deterministicFeedback (inner.nest outer) =
      deterministicFeedback outer := by
  rfl

theorem relFeedback_mono
    {A : Type uA} {B : Type uB} {X : Type uX}
    {left right : RelOperator (A × X) (B × X)}
    (included : ∀ source target, left source target → right source target) :
    ∀ source target,
      relFeedback left source target → relFeedback right source target := by
  intro source target
  rintro ⟨loop, edge⟩
  exact ⟨loop, included _ _ edge⟩

theorem relFeedback_yanking
    {X : Type uX} :
    relFeedback
        (deterministicAsRel
          (deterministicFeedbackSwapEffect (X := X))) =
      relIdentity := by
  funext source target
  apply propext
  constructor
  · rintro ⟨loop, edge⟩
    change (target, loop) = (loop, source) at edge
    have target_eq_loop := congrArg Prod.fst edge
    have loop_eq_source := congrArg Prod.snd edge
    exact (target_eq_loop.trans loop_eq_source).symm
  · intro source_eq_target
    refine ⟨source, ?_⟩
    change (target, source) = (source, source)
    rw [← source_eq_target]

/-!
## Existing exact path/measurable surfaces in the unified effect closure

The direct import closure exposes these already proved theorem surfaces without
manufacturing weaker aliases:

* `OCMaturityCompletionCycle.jointOpenKernelCommutes_and_alignment_imply_pathLawExact`;
* `OCMaturityCompletionCycle.jointOpenKernelCommutes_and_feedbackAlignment_imply_pathLawExact`;
* `OCMaturityCompletionCycle.quotientJointOpenKernel_commutes_on_measurableEvent`.
-/

/-! ## Typed residuals not discharged by this formal package -/

/--
The exact data still required at one declared finite horizon.  The path
carriers and laws are indexed by that horizon; cross-horizon consistency is a
separate obligation.  No value is manufactured from the one-step theorem.
-/
structure FiniteHorizonMeasurablePathTransportCertificate
    (horizon : ℕ)
    (FinePath : ℕ -> Type uA)
    (AbstractPath : ℕ -> Type uB)
    [MeasurableSpace (FinePath horizon)]
    [MeasurableSpace (AbstractPath horizon)]
    (encodePath : FinePath horizon -> AbstractPath horizon)
    (finePathLaw : Measure (FinePath horizon))
    (abstractPathLaw : Measure (AbstractPath horizon)) : Prop where
  measurable_encodePath : Measurable encodePath
  transport : ∀ event,
    MeasurableSet event →
      abstractPathLaw event = finePathLaw (encodePath ⁻¹' event)

/--
Infinite-path transport is a separate obligation from every fixed finite
horizon: it must compare measures on the declared infinite path spaces.
-/
structure InfiniteMeasurablePathTransportCertificate
    (FinePath : Type uA)
    (AbstractPath : Type uB)
    [MeasurableSpace FinePath]
    [MeasurableSpace AbstractPath]
    (encodePath : FinePath -> AbstractPath)
    (finePathLaw : Measure FinePath)
    (abstractPathLaw : Measure AbstractPath) : Prop where
  measurable_encodePath : Measurable encodePath
  transport : ∀ event,
    MeasurableSet event →
      abstractPathLaw event = finePathLaw (encodePath ⁻¹' event)

/--
The finite-rational/measurable representation bridge must be supplied against
an explicit mass embedding.  Exactness is required on every finite event, not
only on positive support or singleton names.
-/
structure FiniteRationalMeasurableRepresentationCertificate
    {A : Type uA} {B : Type uB}
    [Fintype B]
    [MeasurableSpace B]
    (effect : RationalWeightedEffect A B)
    (embedMass : ℚ -> ENNReal)
    (rows : A -> Measure B) : Prop where
  effect_nonnegative : RationalEffectNonnegative effect
  effect_normalized : RationalEffectNormalized effect
  embed_zero : embedMass 0 = 0
  embed_one : embedMass 1 = 1
  embed_add_nonnegative : ∀ left right,
    0 ≤ left → 0 ≤ right →
      embedMass (left + right) = embedMass left + embedMass right
  embed_faithful_nonnegative : ∀ {left right},
    0 ≤ left → 0 ≤ right →
      embedMass left = embedMass right → left = right
  finite_event_measurable : ∀ event : Finset B,
    MeasurableSet (event : Set B)
  finite_event_exact : ∀ source (event : Finset B),
    rows source (event : Set B) =
      ∑ target ∈ event, embedMass (effect source target)

/--
The missing bridge between loop-closing feedback and a policy/path feedback
construction must identify their presented relations, not merely their names.
-/
structure PolicyLoopFeedbackBridgeCertificate
    (LoopEffect : Type uA)
    (PolicyEffect : Type uB)
    (Source : Type uC)
    (Target : Type uD)
    (presentLoop : LoopEffect -> RelOperator Source Target)
    (presentPolicy : PolicyEffect -> RelOperator Source Target) : Type _ where
  loopEffect : LoopEffect
  policyEffect : PolicyEffect
  presentation_exact :
    presentLoop loopEffect = presentPolicy policyEffect

/--
Domain calibration is an external certificate against a declared meaning
predicate.  Lean proves no instance merely from algebraic normalization.
-/
structure QuantitativeDomainCalibrationCertificate
    {A : Type uA} {B : Type uB}
    (effect : RationalWeightedEffect A B)
    (CalibratedMeaning : A -> B -> ℚ -> Prop) : Type _ where
  Evidence : Type uEvidence
  evidence : Evidence
  validates : ∀ source target,
    CalibratedMeaning source target (effect source target)

/--
A deterministic feedback doctrine can be total only on an explicitly admitted
effect class.  The existing Boolean-negation no-go rules out the universal
class; this structure records the exact restricted-selection residual.
-/
structure ScopedDeterministicFeedbackSelection
    {A : Type uA} {B : Type uB} {X : Type uX}
    (Admissible : (A × X -> B × X) -> Prop) where
  select : ∀ effect,
    Admissible effect → DeterministicFeedbackSolution effect
  output_unique : ∀ effect,
    Admissible effect → DeterministicFeedbackOutputUnique effect

/-!
Closure obtained here is therefore exact but bounded:

* all raw finite-rational identity/associativity/parallel/interchange laws;
* normalization and nonnegativity closure for the stochastic subfamily;
* exact positive-support comparison under nonnegativity;
* independent-product marginal equalities for possibly signed rational
  weights; stochastic-law validity is supplied separately by
  `FiniteRationalStochasticEffect.parallel`, and arbitrary correlated joints
  are not inferred;
* witness-transported deterministic tightening, sliding, vanishing I/II,
  superposing, yanking, and solution independence under output uniqueness;
* finite ordinary/feedback path transport and measurable one-step transport.

Finite- and infinite-horizon measurable path transport, a finite-rational to
measurable representation bridge, policy-loop feedback identification,
unrestricted deterministic totality, and domain calibration are not inferred.
-/

end OCKIndividuationMSpaceComposition
