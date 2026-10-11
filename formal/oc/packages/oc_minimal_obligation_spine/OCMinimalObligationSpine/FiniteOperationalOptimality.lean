import OCMinimalObligationSpine.OperationalPredictiveState

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

universe uHistory uPolicy uOutcome uCarrier uState uFine uCoarse uDecision

/-! ## Strict coarsening and refinement witnesses -/

theorem nonsufficient_encoder_has_distinguishing_witness
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    {encode : interface.History -> Carrier}
    (notSufficient : Not (PredictivelySufficient process encode)) :
    Exists fun left : interface.History =>
      Exists fun right : interface.History =>
        Exists fun policy : interface.Policy =>
          encode left = encode right /\
            process.futureLaw left policy ≠ process.futureLaw right policy := by
  by_contra noWitness
  apply notSufficient
  intro left right sameEncoding policy
  by_contra differentOutcome
  apply noWitness
  exact ⟨left, right, policy, sameEncoding, differentOutcome⟩

/-- Exact law identification is a bounded zero-one decision problem. -/
noncomputable def lawIdentificationDecisionProblem
    (Outcome : Type uOutcome) : DecisionProblem Outcome := by
  classical
  exact {
    Action := Outcome
    loss := fun truth action => if truth = action then 0 else 1
    bounded := fun truth action => by
      by_cases same : truth = action <;> simp [same]
  }

theorem lawIdentificationLoss_eq_zero_of_exact
    {Outcome : Type uOutcome}
    (truth : Outcome) :
    (lawIdentificationDecisionProblem Outcome).loss truth truth = 0 := by
  classical
  simp [lawIdentificationDecisionProblem]

theorem lawIdentificationLoss_eq_one_of_error
    {Outcome : Type uOutcome}
    {truth action : Outcome}
    (different : truth ≠ action) :
    (lawIdentificationDecisionProblem Outcome).loss truth action = 1 := by
  classical
  simp [lawIdentificationDecisionProblem, different]

/-- A collapsed pair with different outcomes defeats every decoder on one member. -/
theorem collapsed_distinct_outcomes_force_bounded_decision_error
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    {encode : interface.History -> Carrier}
    {left right : interface.History}
    {policy : interface.Policy}
    (sameEncoding : encode left = encode right)
    (differentOutcome :
      process.futureLaw left policy ≠ process.futureLaw right policy)
    (decide : Carrier -> interface.Outcome) :
    decide (encode left) ≠ process.futureLaw left policy \/
      decide (encode right) ≠ process.futureLaw right policy := by
  by_cases leftError :
      decide (encode left) = process.futureLaw left policy
  · right
    intro rightExact
    apply differentOutcome
    calc
      process.futureLaw left policy = decide (encode left) := leftError.symm
      _ = decide (encode right) := congrArg decide sameEncoding
      _ = process.futureLaw right policy := rightExact
  · exact Or.inl leftError

/-- On the collapsed two-history experiment every decoder has positive total loss. -/
theorem collapsed_pair_has_strict_total_decision_loss
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    {encode : interface.History -> Carrier}
    {left right : interface.History}
    {policy : interface.Policy}
    (sameEncoding : encode left = encode right)
    (differentOutcome :
      process.futureLaw left policy ≠ process.futureLaw right policy)
    (decide : Carrier -> interface.Outcome) :
    1 <=
      (lawIdentificationDecisionProblem interface.Outcome).loss
        (process.futureLaw left policy) (decide (encode left)) +
      (lawIdentificationDecisionProblem interface.Outcome).loss
        (process.futureLaw right policy) (decide (encode right)) := by
  rcases collapsed_distinct_outcomes_force_bounded_decision_error
      process sameEncoding differentOutcome decide with leftError | rightError
  · have one := lawIdentificationLoss_eq_one_of_error leftError.symm
    rw [one]
    exact Nat.le_add_right 1 _
  · have one := lawIdentificationLoss_eq_one_of_error rightError.symm
    rw [one]
    exact Nat.le_add_left 1 _

/-- The canonical quotient has a zero-error decoder for each admitted policy. -/
theorem canonical_state_has_exact_policy_decoder
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    (history : interface.History)
    (policy : interface.Policy) :
    canonicalFutureLaw process (canonicalPredictiveState process history) policy =
      process.futureLaw history policy :=
  canonicalFutureLaw_mk process history policy

theorem canonical_state_has_zero_law_identification_loss
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    (history : interface.History)
    (policy : interface.Policy) :
    (lawIdentificationDecisionProblem interface.Outcome).loss
      (process.futureLaw history policy)
      (canonicalFutureLaw process (canonicalPredictiveState process history) policy) = 0 := by
  rw [canonicalFutureLaw_mk]
  exact lawIdentificationLoss_eq_zero_of_exact _

/-- Every strict refinement of the canonical quotient distinguishes a redundant pair. -/
theorem strict_refinement_of_canonical_has_redundant_distinction
    {interface : ExperimentalInterface}
    (process : OperationalProcess interface)
    {encode : interface.History -> Carrier}
    (strict : EncoderKernelStrictlyRefines encode (canonicalPredictiveState process)) :
    Exists fun left : interface.History =>
      Exists fun right : interface.History =>
        PredictiveEquivalence process left right /\ encode left ≠ encode right := by
  by_contra noWitness
  apply strict.2
  intro left right sameCanonical
  by_contra differentEncoding
  apply noWitness
  exact ⟨left, right, Quotient.exact sameCanonical, differentEncoding⟩

/-! ## Blackwell/garbling characterization -/

/-- Every downstream deterministic rule available after the coarse view is simulable. -/
def DeterministicDecisionRuleSimulation
    {State : Type uState}
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    (fine : ObservationChannel State Fine)
    (coarse : ObservationChannel State Coarse) : Prop :=
  forall rule : Coarse -> Coarse,
    Exists fun lifted : Fine -> Coarse =>
      lifted ∘ fine.observe = rule ∘ coarse.observe

theorem deterministic_blackwell_iff_all_decision_rules_simulable
    {State : Type uState}
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    (fine : ObservationChannel State Fine)
    (coarse : ObservationChannel State Coarse) :
    DeterministicBlackwellDominates fine coarse <->
      DeterministicDecisionRuleSimulation fine coarse := by
  constructor
  · rintro ⟨garbling, coarseFactor⟩ rule
    refine ⟨rule ∘ garbling, ?_⟩
    rw [coarseFactor]
    rfl
  · intro simulates
    rcases simulates id with ⟨garbling, factor⟩
    refine ⟨garbling, ?_⟩
    simpa [Function.comp_def] using factor.symm

/-! ## Deterministic irreversibility -/

/-- Operational irreversibility is the absence of a two-sided process inverse. -/
def ProcessIrreversibility {State : Type uState} (transition : State -> State) : Prop :=
  Not (Exists fun inverse : State -> State =>
    Function.LeftInverse inverse transition /\
      Function.RightInverse inverse transition)

theorem noninjective_transition_is_irreversible
    {State : Type uState}
    {transition : State -> State}
    (notInjective : Not (Function.Injective transition)) :
    ProcessIrreversibility transition := by
  rintro ⟨inverse, leftInverse, _rightInverse⟩
  exact notInjective leftInverse.injective

/-! ## Exact quotient closure and a non-lumpable countermodel -/

inductive NonLumpableState where
  | left
  | right
  | sink
  deriving DecidableEq, Repr

def nonLumpableCoarse : NonLumpableState -> Bool
  | .left => false
  | .right => false
  | .sink => true

def nonLumpableStep : NonLumpableState -> NonLumpableState
  | .left => .left
  | .right => .sink
  | .sink => .sink

/-- Equal coarse states can have different coarse successors, so no closed quotient step exists. -/
theorem nonlumpable_coarse_graining_has_no_exact_markov_step :
    Not (Exists fun quotientStep : Bool -> Bool =>
      forall state,
        nonLumpableCoarse (nonLumpableStep state) =
          quotientStep (nonLumpableCoarse state)) := by
  rintro ⟨quotientStep, closes⟩
  have leftLaw := closes NonLumpableState.left
  have rightLaw := closes NonLumpableState.right
  have contradiction : false = true := by
    calc
      false = quotientStep false := by
        simpa [nonLumpableCoarse, nonLumpableStep] using leftLaw
      _ = true := by
        simpa [nonLumpableCoarse, nonLumpableStep] using rightLaw.symm
  exact Bool.false_ne_true contradiction

/-! ## Finite primitive-independence witnesses -/

def historyWitnessInterface : ExperimentalInterface where
  History := Bool
  Policy := Unit
  Outcome := Bool

def historyWitnessProcess : OperationalProcess historyWitnessInterface where
  futureLaw history _policy := history

theorem history_primitive_changes_an_admitted_future_law :
    historyWitnessProcess.futureLaw false () ≠
      historyWitnessProcess.futureLaw true () := by
  simp [historyWitnessProcess]

def policyWitnessInterface : ExperimentalInterface where
  History := Unit
  Policy := Bool
  Outcome := Bool

def policyWitnessProcess : OperationalProcess policyWitnessInterface where
  futureLaw _history policy := policy

theorem policy_primitive_changes_an_admitted_future_law :
    policyWitnessProcess.futureLaw () false ≠
      policyWitnessProcess.futureLaw () true := by
  simp [policyWitnessProcess]

theorem observable_outcome_has_an_independent_distinction :
    (false : Bool) ≠ true := by
  decide

def constantFalseProcess : OperationalProcess policyWitnessInterface where
  futureLaw _history _policy := false

def constantTrueProcess : OperationalProcess policyWitnessInterface where
  futureLaw _history _policy := true

theorem process_law_is_not_fixed_by_interface_types :
    constantFalseProcess ≠ constantTrueProcess := by
  intro sameProcess
  have sameLaw := congrArg OperationalProcess.futureLaw sameProcess
  have atHistory := congrFun sameLaw ()
  have atPolicy := congrFun atHistory false
  exact Bool.false_ne_true atPolicy

theorem causal_transition_is_not_fixed_by_current_carrier :
    (id : Bool -> Bool) ≠ Bool.not := by
  intro sameTransition
  have atFalse := congrFun sameTransition false
  simp at atFalse

theorem sequential_composition_has_independent_two_step_content :
    Bool.not (Bool.not false) = false /\ Bool.not false ≠ false := by
  decide

/-! ## Finite path-law asymmetry -/

def directedPairAsymmetry (forward reverse : Nat) : Nat :=
  (forward - reverse) + (reverse - forward)

theorem directedPairAsymmetry_eq_zero_iff
    (forward reverse : Nat) :
    directedPairAsymmetry forward reverse = 0 <-> forward = reverse := by
  constructor
  · intro zero
    have parts := Nat.add_eq_zero_iff.mp zero
    exact Nat.le_antisymm
      (Nat.sub_eq_zero_iff_le.mp parts.1)
      (Nat.sub_eq_zero_iff_le.mp parts.2)
  · intro same
    subst reverse
    simp [directedPairAsymmetry]

def finitePathAsymmetry : List (Nat × Nat) -> Nat
  | [] => 0
  | pair :: rest =>
      directedPairAsymmetry pair.1 pair.2 + finitePathAsymmetry rest

theorem finitePathAsymmetry_nonnegative
    (pathWeights : List (Nat × Nat)) :
    0 <= finitePathAsymmetry pathWeights :=
  Nat.zero_le _

theorem finitePathAsymmetry_eq_zero_iff_reversible
    (pathWeights : List (Nat × Nat)) :
    finitePathAsymmetry pathWeights = 0 <->
      forall pair, pair ∈ pathWeights -> pair.1 = pair.2 := by
  induction pathWeights with
  | nil => simp [finitePathAsymmetry]
  | cons pair rest inductionHypothesis =>
      simp [finitePathAsymmetry, directedPairAsymmetry_eq_zero_iff,
        inductionHypothesis]

/-! ## Identifiability and no-free-lunch boundaries -/

/-- A finite observation can erase the difference between distinct generators. -/
theorem finite_observation_does_not_identify_hidden_generator :
    Exists fun firstGenerator : Bool -> Bool =>
      Exists fun secondGenerator : Bool -> Bool =>
        firstGenerator ≠ secondGenerator /\
          (fun _state => () : Bool -> Unit) ∘ firstGenerator =
            (fun _state => () : Bool -> Unit) ∘ secondGenerator := by
  refine ⟨id, Bool.not, ?_, ?_⟩
  · intro same
    have atFalse := congrFun same false
    simp at atFalse
  · funext state
    simp

def boolZeroOneLoss (truth prediction : Bool) : Nat :=
  if truth = prediction then 0 else 1

/-- Across the unrestricted two-law class, every binary predictor has equal total loss. -/
theorem binary_interface_free_no_free_lunch (predictor : Bool) :
    boolZeroOneLoss false predictor + boolZeroOneLoss true predictor = 1 := by
  cases predictor <;> decide

theorem binary_predictors_have_equal_unrestricted_risk
    (leftPredictor rightPredictor : Bool) :
    boolZeroOneLoss false leftPredictor + boolZeroOneLoss true leftPredictor =
      boolZeroOneLoss false rightPredictor + boolZeroOneLoss true rightPredictor := by
  rw [binary_interface_free_no_free_lunch, binary_interface_free_no_free_lunch]

/-! ## No unique scalar selector and the Pareto boundary -/

theorem description_length_alone_has_a_tie :
    Exists fun left : PredictiveDeficiency =>
      Exists fun right : PredictiveDeficiency =>
        left ≠ right /\
          left.representationComplexity = right.representationComplexity := by
  exact ⟨⟨0, 1⟩, ⟨1, 1⟩, by decide, rfl⟩

def DeficiencyParetoDominates
    (left right : PredictiveDeficiency) : Prop :=
  left.worstCaseLoss <= right.worstCaseLoss /\
    left.representationComplexity <= right.representationComplexity

theorem predictive_deficiency_frontier_can_have_incomparable_points :
    Exists fun left : PredictiveDeficiency =>
      Exists fun right : PredictiveDeficiency =>
        Not (DeficiencyParetoDominates left right) /\
          Not (DeficiencyParetoDominates right left) := by
  refine ⟨⟨0, 1⟩, ⟨1, 0⟩, ?_, ?_⟩
  · intro dominates
    exact Nat.not_succ_le_zero 0 dominates.2
  · intro dominates
    exact Nat.not_succ_le_zero 0 dominates.1

end OCMinimalObligationSpine
