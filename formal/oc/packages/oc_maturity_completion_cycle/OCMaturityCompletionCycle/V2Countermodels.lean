import OCMaturityCompletionCycle.JointOpenHistoryDefect
import OCMaturityCompletionCycle.FiniteJointFeedbackPath
import OCMaturityCompletionCycle.VerifiedDynamicsCapabilities
import OCMaturityCompletionCycle.AbstractionCostPareto
import OCMaturityCompletionCycle.IterativeCountermodels
import Init.Tactics

/-!
# Countermodels for the V2 coherence gates
-/

namespace OCMaturityCompletionCycle

/-- Deterministic controlled kernel whose action selects the next state. -/
def actionSelectedControlledKernel : FiniteControlledKernel Bool Bool where
  mass _ action := (finiteDirac action).mass
  nonnegative _ action := (finiteDirac action).nonnegative
  normalized _ action := (finiteDirac action).normalized

theorem actionSelectedControlledKernel_is_deterministic :
    FiniteKernelDeterministic actionSelectedControlledKernel := by
  intro state action
  refine ⟨action, ?_, ?_⟩
  · simp [actionSelectedControlledKernel, finiteDirac]
  · intro target targetMassOne
    simpa [actionSelectedControlledKernel, finiteDirac] using targetMassOne

/-- Concrete verified deterministic controlled-state profile. -/
def verifiedActionSelectedControlledPath :
    VerifiedFiniteControlledStatePath Bool Bool where
  kernel := actionSelectedControlledKernel
  horizon := 1
  initial := finiteDirac false
  schedule _ := true
  horizon_positive := by norm_num
  actionEffect := by
    refine ⟨false, false, true, true, ?_, ?_⟩
    · decide
    · norm_num [actionSelectedControlledKernel, finiteDirac]
  randomnessMode := .deterministic
  randomnessEvidence := actionSelectedControlledKernel_is_deterministic

/-- Exact state observation. -/
def boolFullObservationWitness : FullObservationWitness Bool Bool where
  observe := id
  injective := Function.injective_id

/-- Explicitly lossy observation. -/
def boolPartialObservationWitness : PartialObservationWitness Bool Unit where
  observe _ := ()
  left := false
  right := true
  states_differ := by decide
  observations_equal := rfl

/--
Finite stochastic open process.  Both context and boundary input change the
joint law, and both boundary-output values occur with positive probability.
-/
def switchingContextBoundaryProcess :
    FiniteJointOpenProcess Unit Bool Bool Unit Bool where
  mass _ control outcome :=
    if control.1 then
      if control.2.1 then
        if outcome.2 then 3 / 4 else 1 / 4
      else
        if outcome.2 then 1 / 2 else 1 / 2
    else
      if control.2.1 then
        if outcome.2 then 1 / 4 else 3 / 4
      else
        if outcome.2 then 1 / 2 else 1 / 2
  nonnegative _ control outcome := by
    rcases control with ⟨context, boundary, action⟩
    cases action
    rcases outcome with ⟨state, output⟩
    cases state
    cases context <;> cases boundary <;> cases output <;> norm_num
  normalized _ control := by
    rcases control with ⟨context, boundary, action⟩
    cases action
    cases context <;> cases boundary <;>
      norm_num [Fintype.sum_prod_type, Fintype.sum_bool]

theorem switchingContextBoundaryProcess_is_genuinelyStochastic :
    JointOpenProcessGenuinelyStochastic switchingContextBoundaryProcess := by
  refine ⟨(), (false, false, ()), ((), false), ((), true), ?_, ?_, ?_⟩
  · decide
  · norm_num [switchingContextBoundaryProcess]
  · norm_num [switchingContextBoundaryProcess]

theorem switchingContextBoundaryProcess_has_open_semantics :
    JointOpenBoundarySemantics switchingContextBoundaryProcess := by
  refine {
    input_changes_joint_law := ?_
    context_changes_joint_law := ?_
    output_is_nontrivial := ?_
  }
  · refine ⟨(), true, false, true, (), ((), true), ?_, ?_⟩
    · decide
    · norm_num [switchingContextBoundaryProcess]
  · refine ⟨(), false, true, true, (), ((), true), ?_, ?_⟩
    · decide
    · norm_num [switchingContextBoundaryProcess]
  · refine ⟨(), (false, false, ()), ((), false),
      (), (false, false, ()), ((), true), ?_, ?_, ?_⟩
    · decide
    · norm_num [switchingContextBoundaryProcess]
    · norm_num [switchingContextBoundaryProcess]

/-- Concrete verified stochastic open profile. -/
def verifiedSwitchingContextBoundaryProcess :
    VerifiedJointOpenBoundaryOutput Unit Bool Bool Unit Bool where
  process := switchingContextBoundaryProcess
  controlMode := .passive
  controlEvidence := trivial
  randomnessMode := .stochastic
  randomnessEvidence :=
    switchingContextBoundaryProcess_is_genuinelyStochastic
  boundarySemantics := switchingContextBoundaryProcess_has_open_semantics

/-- Identity abstraction used to test nontrivial context covariance. -/
def switchingContextIdentityAbstraction :
    FiniteJointContextualAbstraction Unit Bool Bool Unit Bool
      Unit Bool Bool Unit Bool where
  fine := switchingContextBoundaryProcess
  abstract := switchingContextBoundaryProcess
  stateMap := id
  contextMap := id
  boundaryInMap := id
  actionMap := id
  boundaryOutMap := id

/-- Two one-observation histories indexed by distinct declared contexts. -/
def switchingContextHistorySupport :
    FrozenOperationalHistorySupport Bool Unit Bool Bool Unit where
  observations _ := [()]
  controls _ := []
  currentContext := id
  currentBoundaryIn _ := true
  currentAction _ := ()
  observations_nonempty _ := by simp
  history_shape _ := by simp

/-- Primitive next laws are the two context-indexed open rows at boundary `true`. -/
def switchingContextHistoryProcess :
    FiniteHistoryJointOpenProcess Bool Unit Unit Bool Bool Unit Bool where
  support := switchingContextHistorySupport
  nextLaw context :=
    jointStepProbability switchingContextBoundaryProcess () (context, true, ())

def switchingContextHistoryAbstraction :
    OperationalHistoryAbstraction
      (Observation := Unit) switchingContextIdentityAbstraction where
  observeState _ := ()
  qChi _ _ _ := ()
  singleton_compatibility _ _ := rfl

def switchingContextHistoryExperiment (context : Bool) :
    FiniteJointOpenExperiment Unit Bool Bool Unit Bool where
  process := switchingContextBoundaryProcess
  horizon := 0
  initial := finiteDirac ()
  policy _ := (context, true, ())

/-- The frozen context histories are actual endpoint laws of the joint plant. -/
def switchingContextHistoryRealization :
    FrozenHistoryMarkovRealization switchingContextHistoryProcess
      switchingContextBoundaryProcess where
  observeState _ := ()
  experiment := switchingContextHistoryExperiment
  experiment_uses_plant _ := rfl
  horizon_agrees _ := rfl
  policy_agrees index step stepBeforeZero :=
    (Nat.not_lt_zero step stepBeforeZero).elim
  witnessedPath _ := ULift.up ()
  witnessed_path_positive context := by
    cases context <;> decide
  observations_realized _ := rfl
  next_law_realized context := by
    cases context <;>
      rfl

/-- The two declared histories have equal length, so no strict-prefix pair is hidden. -/
def switchingContextHistoryPrefixConsistency :
    FrozenHistoryPrefixConsistency switchingContextHistoryRealization where
  state_trace_prefix short long strictPrefix := by
    cases short <;> cases long <;> decide
  output_trace_prefix short long strictPrefix := by
    cases short <;> cases long <;> decide

/-- Thin two-object context category: `false ≤ true`. -/
def boolContextRelated (left right : Bool) : Bool := (!left) || right

/-- Unique-arrow action: identities act trivially; the strict arrow flips Bool. -/
def boolContextArrowMap (left right value : Bool) : Bool :=
  if left = right then value else !value

/-- Total last-observation selector used by the finite history fixtures. -/
def lastBoolObservation : List Bool → Bool
  | [] => false
  | [observation] => observation
  | _ :: rest => lastBoolObservation rest

theorem boolContextRelated_reflexive (index : Bool) :
    boolContextRelated index index = true := by
  cases index <;> decide

theorem boolContextRelated_transitive (left middle right : Bool) :
    boolContextRelated left middle = true →
    boolContextRelated middle right = true →
    boolContextRelated left right = true := by
  cases left <;> cases middle <;> cases right <;> decide

theorem boolContextArrowMap_identity (index : Bool) :
    boolContextArrowMap index index = id := by
  funext value
  cases index <;> cases value <;> rfl

theorem boolContextArrowMap_composition (left middle right : Bool) :
    boolContextRelated left middle = true →
    boolContextRelated middle right = true →
    boolContextArrowMap middle right ∘ boolContextArrowMap left middle =
      boolContextArrowMap left right := by
  intro leftRelated middleRelated
  funext value
  cases left <;> cases middle <;> cases right <;> cases value <;>
    simp [boolContextRelated, boolContextArrowMap, Function.comp_def] at *

theorem boolContextArrowMap_sends_source_to_target (left right : Bool) :
    boolContextRelated left right = true →
      boolContextArrowMap left right left = right := by
  cases left <;> cases right <;>
    simp [boolContextRelated, boolContextArrowMap]

/--
The context morphism flips the context and the emitted Boolean output.  It is
nontrivial and relates `false` to `true`; it is not a same-control fibre.
-/
def switchingContextTransport :
    OperationalHistoryContextFunctor switchingContextIdentityAbstraction
      switchingContextHistoryAbstraction switchingContextHistoryProcess where
  related := boolContextRelated
  anchor := false
  anchor_covers index := by cases index <;> rfl
  related_reflexive := boolContextRelated_reflexive
  related_transitive := boolContextRelated_transitive
  contextMap := boolContextArrowMap
  boundaryInMap _ _ := id
  actionMap _ _ := id
  stateMap _ _ := id
  context_identity := boolContextArrowMap_identity
  boundaryIn_identity _ := rfl
  action_identity _ := rfl
  state_identity _ := rfl
  context_composition := boolContextArrowMap_composition
  boundaryIn_composition _ _ _ _ _ := rfl
  action_composition _ _ _ _ _ := rfl
  state_composition _ _ _ _ _ := rfl
  context_aligned left right related := by
    exact boolContextArrowMap_sends_source_to_target left right related
  boundaryIn_aligned _ _ _ := rfl
  action_aligned _ _ _ := rfl
  encodedState_aligned _ _ _ := rfl

def switchingContextZeroHorizonExperiments (context : Bool) :
    AlignedJointOpenExperiments switchingContextIdentityAbstraction where
  horizon := 0
  fineInitial := finiteDirac ()
  abstractInitial := finiteDirac ()
  finePolicy _ := (context, true, ())
  abstractPolicy _ := (context, true, ())

def switchingContextHistoryStudy :
    JointOpenHistoryStudy Bool Unit Unit Bool Bool Unit Bool
      Unit Bool Bool Unit Bool where
  abstraction := switchingContextIdentityAbstraction
  historyAbstraction := switchingContextHistoryAbstraction
  historyProcess := switchingContextHistoryProcess
  historyRealization := switchingContextHistoryRealization
  observationMap_agrees := rfl
  historyPrefixConsistency := switchingContextHistoryPrefixConsistency
  contextTransport := switchingContextTransport
  pathExperiment := switchingContextZeroHorizonExperiments
  pathExperiment_binds_history _ := rfl
  memoryCost := 1
  stateCost := 1
  resourceCost := 1

/-- State prediction is natural here; output covariance is tested separately. -/
theorem switchingContextTransport_is_natural :
    HistoryContextNatural switchingContextHistoryStudy := by
  intro left right related
  funext state
  cases state
  cases left <;> cases right <;>
    norm_num [transportedHistoryContextLaw, abstractHistoryStateLaw,
      abstractHistoryJointLaw, switchingContextHistoryStudy,
      switchingContextTransport, switchingContextHistoryProcess,
      switchingContextHistorySupport, switchingContextHistoryAbstraction,
      switchingContextIdentityAbstraction, switchingContextBoundaryProcess,
      boolContextArrowMap, boolContextRelated, jointStepProbability,
      pushforwardFiniteProbability, finiteDirac, Fintype.sum_prod_type,
      Fintype.sum_bool] at related ⊢

theorem switchingContextTransport_pair_not_lumpabilityAligned :
    ¬ HistoryComparisonAligned switchingContextHistoryAbstraction
      switchingContextHistoryProcess false true := by
  intro aligned
  simpa [HistoryComparisonAligned, operationalHistoryAbstractState,
    operationalHistoryAbstractControl, switchingContextHistoryAbstraction,
    switchingContextHistoryProcess, switchingContextHistorySupport,
    switchingContextIdentityAbstraction] using aligned

theorem switchingContextNaturalityDefect_is_zero :
    historyContextNaturalityDefect switchingContextHistoryStudy = 0 :=
  (historyContextNaturalityDefect_eq_zero_iff_natural
    switchingContextHistoryStudy).2 switchingContextTransport_is_natural

/-! Nontrivial state-law covariance canary for the context coordinate. -/

def contextSelectedStateProcess :
    FiniteJointOpenProcess Bool Bool Unit Unit Unit where
  mass _ control := (finiteDirac (control.1, ())).mass
  nonnegative _ control := (finiteDirac (control.1, ())).nonnegative
  normalized _ control := (finiteDirac (control.1, ())).normalized

def contextSelectedStateAbstraction :
    FiniteJointContextualAbstraction Bool Bool Unit Unit Unit
      Bool Bool Unit Unit Unit where
  fine := contextSelectedStateProcess
  abstract := contextSelectedStateProcess
  stateMap := id
  contextMap := id
  boundaryInMap := id
  actionMap := id
  boundaryOutMap := id

def contextSelectedHistorySupport :
    FrozenOperationalHistorySupport Bool Bool Bool Unit Unit where
  observations context := [context]
  controls _ := []
  currentContext := id
  currentBoundaryIn _ := ()
  currentAction _ := ()
  observations_nonempty _ := by simp
  history_shape _ := by simp

def contextSelectedHistoryProcess :
    FiniteHistoryJointOpenProcess Bool Bool Bool Bool Unit Unit Unit where
  support := contextSelectedHistorySupport
  nextLaw context := finiteDirac (context, ())

def contextSelectedHistoryAbstraction :
    OperationalHistoryAbstraction
      (Observation := Bool) contextSelectedStateAbstraction where
  observeState := id
  qChi _ observations _ := lastBoolObservation observations
  singleton_compatibility _ state := by
    cases state <;> rfl

def contextSelectedHistoryExperiment (context : Bool) :
    FiniteJointOpenExperiment Bool Bool Unit Unit Unit where
  process := contextSelectedStateProcess
  horizon := 0
  initial := finiteDirac context
  policy _ := (context, (), ())

def contextSelectedHistoryRealization :
    FrozenHistoryMarkovRealization contextSelectedHistoryProcess
      contextSelectedStateProcess where
  observeState := id
  experiment := contextSelectedHistoryExperiment
  experiment_uses_plant _ := rfl
  horizon_agrees _ := rfl
  policy_agrees _ _ impossible := (Nat.not_lt_zero _ impossible).elim
  witnessedPath context := ULift.up context
  witnessed_path_positive context := by
    cases context <;> decide
  observations_realized context := by
    cases context <;> rfl
  next_law_realized context := by
    cases context <;>
      norm_num [contextSelectedHistoryProcess, contextSelectedStateProcess,
        contextSelectedHistoryExperiment, contextSelectedHistorySupport,
        FiniteHistoryJointOpenProcess.currentControl, jointStepProbability,
        finiteStateOutputPathLastState, finiteDirac]

def contextSelectedHistoryPrefixConsistency :
    FrozenHistoryPrefixConsistency contextSelectedHistoryRealization where
  state_trace_prefix short long strictPrefix := by
    cases short <;> cases long <;>
      norm_num [StrictOperationalHistoryPrefix, contextSelectedHistoryProcess,
        contextSelectedHistorySupport] at strictPrefix
  output_trace_prefix short long strictPrefix := by
    cases short <;> cases long <;>
      norm_num [StrictOperationalHistoryPrefix, contextSelectedHistoryProcess,
        contextSelectedHistorySupport] at strictPrefix

def contextSelectedTransport :
    OperationalHistoryContextFunctor contextSelectedStateAbstraction
      contextSelectedHistoryAbstraction contextSelectedHistoryProcess where
  related := boolContextRelated
  anchor := false
  anchor_covers index := by cases index <;> rfl
  related_reflexive := boolContextRelated_reflexive
  related_transitive := boolContextRelated_transitive
  contextMap := boolContextArrowMap
  boundaryInMap _ _ := id
  actionMap _ _ := id
  stateMap := boolContextArrowMap
  context_identity := boolContextArrowMap_identity
  boundaryIn_identity _ := rfl
  action_identity _ := rfl
  state_identity := boolContextArrowMap_identity
  context_composition := boolContextArrowMap_composition
  boundaryIn_composition _ _ _ _ _ := rfl
  action_composition _ _ _ _ _ := rfl
  state_composition := boolContextArrowMap_composition
  context_aligned := boolContextArrowMap_sends_source_to_target
  boundaryIn_aligned _ _ _ := rfl
  action_aligned _ _ _ := rfl
  encodedState_aligned left right related :=
    boolContextArrowMap_sends_source_to_target left right related

def contextSelectedZeroHorizonExperiments (context : Bool) :
    AlignedJointOpenExperiments contextSelectedStateAbstraction where
  horizon := 0
  fineInitial := finiteDirac context
  abstractInitial := finiteDirac context
  finePolicy _ := (context, (), ())
  abstractPolicy _ := (context, (), ())

def contextSelectedHistoryStudy :
    JointOpenHistoryStudy Bool Bool Bool Bool Unit Unit Unit
      Bool Bool Unit Unit Unit where
  abstraction := contextSelectedStateAbstraction
  historyAbstraction := contextSelectedHistoryAbstraction
  historyProcess := contextSelectedHistoryProcess
  historyRealization := contextSelectedHistoryRealization
  observationMap_agrees := rfl
  historyPrefixConsistency := contextSelectedHistoryPrefixConsistency
  contextTransport := contextSelectedTransport
  pathExperiment := contextSelectedZeroHorizonExperiments
  pathExperiment_binds_history _ := rfl
  memoryCost := 1
  stateCost := 2
  resourceCost := 1

theorem contextSelectedStateLaws_differ_without_transport :
    (abstractHistoryStateLaw contextSelectedStateAbstraction
      contextSelectedHistoryAbstraction contextSelectedHistoryProcess false).mass ≠
    (abstractHistoryStateLaw contextSelectedStateAbstraction
      contextSelectedHistoryAbstraction contextSelectedHistoryProcess true).mass := by
  intro equalLaw
  have atFalse := congrFun equalLaw false
  norm_num [abstractHistoryStateLaw, abstractHistoryJointLaw,
    contextSelectedStateAbstraction, contextSelectedHistoryAbstraction,
    contextSelectedHistoryProcess, contextSelectedHistorySupport,
    contextSelectedStateProcess, lastBoolObservation, jointStepProbability,
    pushforwardFiniteProbability, finiteDirac, Fintype.sum_prod_type,
    Fintype.sum_bool] at atFalse

theorem contextSelectedTransport_is_natural :
    HistoryContextNatural contextSelectedHistoryStudy := by
  intro left right related
  have stateMap_def :
      contextSelectedHistoryStudy.contextTransport.stateMap =
        boolContextArrowMap := rfl
  cases left <;> cases right
  · funext state
    cases state <;>
      norm_num [stateMap_def, transportedHistoryContextLaw, abstractHistoryStateLaw,
        abstractHistoryJointLaw, contextSelectedHistoryStudy,
        contextSelectedTransport, contextSelectedHistoryAbstraction,
        contextSelectedHistoryProcess, contextSelectedHistorySupport,
        contextSelectedStateAbstraction, contextSelectedStateProcess,
        boolContextArrowMap, pushforwardFiniteProbability,
        jointStepProbability, finiteDirac, Fintype.sum_prod_type,
        Fintype.sum_bool]
  · funext state
    cases state <;>
      norm_num [stateMap_def, transportedHistoryContextLaw, abstractHistoryStateLaw,
        abstractHistoryJointLaw, contextSelectedHistoryStudy,
        contextSelectedTransport, contextSelectedHistoryAbstraction,
        contextSelectedHistoryProcess, contextSelectedHistorySupport,
        contextSelectedStateAbstraction, contextSelectedStateProcess,
        boolContextArrowMap, pushforwardFiniteProbability,
        jointStepProbability, finiteDirac, Fintype.sum_prod_type,
        Fintype.sum_bool]
  · simp [contextSelectedHistoryStudy, contextSelectedTransport,
      boolContextRelated] at related
  · funext state
    cases state <;>
      norm_num [stateMap_def, transportedHistoryContextLaw, abstractHistoryStateLaw,
        abstractHistoryJointLaw, contextSelectedHistoryStudy,
        contextSelectedTransport, contextSelectedHistoryAbstraction,
        contextSelectedHistoryProcess, contextSelectedHistorySupport,
        contextSelectedStateAbstraction, contextSelectedStateProcess,
        boolContextArrowMap, pushforwardFiniteProbability,
        jointStepProbability, finiteDirac, Fintype.sum_prod_type,
        Fintype.sum_bool]

theorem contextSelectedNaturalityDefect_is_zero :
    historyContextNaturalityDefect contextSelectedHistoryStudy = 0 :=
  (historyContextNaturalityDefect_eq_zero_iff_natural
    contextSelectedHistoryStudy).2 contextSelectedTransport_is_natural

/-- Action-sensitive noisy plant with row TV exactly one half. -/
def quarterThreeQuarterPlant : FiniteControlledKernel Bool Bool where
  mass _ action target :=
    if target then
      if action then 3 / 4 else 1 / 4
    else
      if action then 1 / 4 else 3 / 4
  nonnegative _ action target := by
    cases action <;> cases target <;> norm_num
  normalized _ action := by
    cases action <;> norm_num

/-! A nonvacuous strict-prefix history family on the same noisy controlled plant. -/

def quarterThreeQuarterJointPlant :
    FiniteJointOpenProcess Bool Unit Unit Bool Unit where
  mass state control outcome :=
    quarterThreeQuarterPlant.mass state control.2.2 outcome.1
  nonnegative state control outcome :=
    quarterThreeQuarterPlant.nonnegative state control.2.2 outcome.1
  normalized state control := by
    rcases control with ⟨context, boundary, action⟩
    cases context
    cases boundary
    simpa [Fintype.sum_prod_type] using
      quarterThreeQuarterPlant.normalized state action

def strictPrefixIdentityAbstraction :
    FiniteJointContextualAbstraction Bool Unit Unit Bool Unit
      Bool Unit Unit Bool Unit where
  fine := quarterThreeQuarterJointPlant
  abstract := quarterThreeQuarterJointPlant
  stateMap := id
  contextMap := id
  boundaryInMap := id
  actionMap := id
  boundaryOutMap := id

def strictPrefixHistorySupport :
    FrozenOperationalHistorySupport Bool Bool Unit Unit Bool where
  observations
    | false => [false]
    | true => [false, false]
  controls
    | false => []
    | true => [((), (), false)]
  currentContext _ := ()
  currentBoundaryIn _ := ()
  currentAction _ := false
  observations_nonempty index := by cases index <;> simp
  history_shape index := by cases index <;> simp

def strictPrefixHistoryProcess :
    FiniteHistoryJointOpenProcess Bool Bool Bool Unit Unit Bool Unit where
  support := strictPrefixHistorySupport
  nextLaw _ := jointStepProbability quarterThreeQuarterJointPlant false
    ((), (), false)

def strictPrefixHistoryAbstraction :
    OperationalHistoryAbstraction
      (Observation := Bool) strictPrefixIdentityAbstraction where
  observeState := id
  qChi _ observations _ := lastBoolObservation observations
  singleton_compatibility _ state := by cases state <;> rfl

def strictPrefixHistoryExperiment :
    (index : Bool) → FiniteJointOpenExperiment Bool Unit Unit Bool Unit
  | false => {
      process := quarterThreeQuarterJointPlant
      horizon := 0
      initial := finiteDirac false
      policy _ := ((), (), false)
    }
  | true => {
      process := quarterThreeQuarterJointPlant
      horizon := 1
      initial := finiteDirac false
      policy _ := ((), (), false)
    }

def strictPrefixHistoryRealization :
    FrozenHistoryMarkovRealization strictPrefixHistoryProcess
      quarterThreeQuarterJointPlant where
  observeState := id
  experiment := strictPrefixHistoryExperiment
  experiment_uses_plant index := by cases index <;> rfl
  horizon_agrees index := by cases index <;> rfl
  policy_agrees index step stepInHistory := by
    cases index
    · exact (Nat.not_lt_zero step stepInHistory).elim
    · have step_lt_one : step < 1 := by
        simpa [strictPrefixHistoryProcess, strictPrefixHistorySupport] using
          stepInHistory
      have step_eq : step = 0 := by omega
      subst step
      simp [strictPrefixHistoryExperiment, strictPrefixHistoryProcess,
        strictPrefixHistorySupport]
  witnessedPath
    | false => ULift.up false
    | true => (ULift.up false, (false, ()))
  witnessed_path_positive index := by
    cases index
    · simp only [strictPrefixHistoryExperiment]
      norm_num [strictPrefixHistoryExperiment,
        inducedFiniteStateOutputPathLaw, inducedJointPathWeightAt, finiteDirac]
    · simp only [strictPrefixHistoryExperiment]
      norm_num [strictPrefixHistoryExperiment, quarterThreeQuarterJointPlant,
        quarterThreeQuarterPlant, inducedFiniteStateOutputPathLaw,
        inducedJointPathWeightAt, finiteDirac]
  observations_realized index := by cases index <;> rfl
  next_law_realized index := by
    cases index <;> funext outcome
    <;> rcases outcome with ⟨state, output⟩
    <;> cases state <;> cases output
    <;> norm_num [strictPrefixHistoryProcess, strictPrefixHistoryExperiment,
      strictPrefixHistorySupport, quarterThreeQuarterJointPlant,
      quarterThreeQuarterPlant, FiniteHistoryJointOpenProcess.currentControl,
      jointStepProbability, finiteStateOutputPathLastState,
      FiniteStateOutputPath, finiteDirac]

def strictPrefixHistoryPrefixConsistency :
    FrozenHistoryPrefixConsistency strictPrefixHistoryRealization where
  state_trace_prefix short long strictPrefix := by
    cases short <;> cases long
    · decide
    · decide
    · norm_num [StrictOperationalHistoryPrefix, strictPrefixHistoryProcess,
        strictPrefixHistorySupport] at strictPrefix
    · decide
  output_trace_prefix short long strictPrefix := by
    cases short <;> cases long
    · decide
    · decide
    · norm_num [StrictOperationalHistoryPrefix, strictPrefixHistoryProcess,
        strictPrefixHistorySupport] at strictPrefix
    · decide

def strictPrefixContextFunctor :
    OperationalHistoryContextFunctor strictPrefixIdentityAbstraction
      strictPrefixHistoryAbstraction strictPrefixHistoryProcess where
  related _ _ := true
  anchor := false
  anchor_covers _ := rfl
  related_reflexive _ := rfl
  related_transitive _ _ _ _ _ := rfl
  contextMap _ _ := id
  boundaryInMap _ _ := id
  actionMap _ _ := id
  stateMap _ _ := id
  context_identity _ := rfl
  boundaryIn_identity _ := rfl
  action_identity _ := rfl
  state_identity _ := rfl
  context_composition _ _ _ _ _ := rfl
  boundaryIn_composition _ _ _ _ _ := rfl
  action_composition _ _ _ _ _ := rfl
  state_composition _ _ _ _ _ := rfl
  context_aligned _ _ _ := rfl
  boundaryIn_aligned _ _ _ := rfl
  action_aligned _ _ _ := rfl
  encodedState_aligned left right _ := by cases left <;> cases right <;> rfl

def strictPrefixAlignedExperiments :
    (index : Bool) → AlignedJointOpenExperiments strictPrefixIdentityAbstraction
  | false => {
      horizon := 0
      fineInitial := finiteDirac false
      abstractInitial := finiteDirac false
      finePolicy _ := ((), (), false)
      abstractPolicy _ := ((), (), false)
    }
  | true => {
      horizon := 1
      fineInitial := finiteDirac false
      abstractInitial := finiteDirac false
      finePolicy _ := ((), (), false)
      abstractPolicy _ := ((), (), false)
    }

theorem strictPrefixAlignedExperiments_has_transportAlignment (index : Bool) :
    JointExperimentTransportAlignment (strictPrefixAlignedExperiments index) := by
  cases index
  · refine { initial_transport := ?_, policy_transport := ?_ }
    · funext state
      cases state <;>
        norm_num [strictPrefixAlignedExperiments, strictPrefixIdentityAbstraction,
          pushforwardFiniteProbability, finiteDirac, Fintype.sum_bool]
    · intro step impossible
      exact (Nat.not_lt_zero step impossible).elim
  · refine { initial_transport := ?_, policy_transport := ?_ }
    · funext state
      cases state <;>
        norm_num [strictPrefixAlignedExperiments, strictPrefixIdentityAbstraction,
          pushforwardFiniteProbability, finiteDirac, Fintype.sum_bool]
    · intro _ _
      rfl

theorem strictPrefixIdentityAbstraction_kernelCommutes :
    JointOpenKernelCommutes strictPrefixIdentityAbstraction := by
  intro state context boundary action
  funext outcome
  cases context
  cases boundary
  rcases outcome with ⟨target, output⟩
  cases output
  cases state <;> cases action <;> cases target <;>
    norm_num [strictPrefixIdentityAbstraction, quarterThreeQuarterJointPlant,
      quarterThreeQuarterPlant, jointStepProbability, jointOutcomeMap,
      pushforwardFiniteProbability, finiteDirac, Fintype.sum_bool]

def strictPrefixHistoryStudy :
    JointOpenHistoryStudy Bool Bool Bool Unit Unit Bool Unit
      Bool Unit Unit Bool Unit where
  abstraction := strictPrefixIdentityAbstraction
  historyAbstraction := strictPrefixHistoryAbstraction
  historyProcess := strictPrefixHistoryProcess
  historyRealization := strictPrefixHistoryRealization
  observationMap_agrees := rfl
  historyPrefixConsistency := strictPrefixHistoryPrefixConsistency
  contextTransport := strictPrefixContextFunctor
  pathExperiment := strictPrefixAlignedExperiments
  pathExperiment_binds_history index := by cases index <;> rfl
  memoryCost := 2
  stateCost := 2
  resourceCost := 1

theorem strictPrefixHistory_paths_transport_exact (index : Bool) :
    (transportedFineJointPathLaw
        (strictPrefixHistoryStudy.pathExperiment index)).mass =
      (inducedFiniteStateOutputPathLaw
        (strictPrefixHistoryStudy.pathExperiment index).abstractExperiment).mass :=
  jointOpenKernelCommutes_and_alignment_imply_pathLawExact
    (strictPrefixHistoryStudy.pathExperiment index)
    (strictPrefixAlignedExperiments_has_transportAlignment index)
    strictPrefixIdentityAbstraction_kernelCommutes

/--
Nonvacuous history witness: the short support row is a strict observation/control
prefix, its realized state/output trace is a prefix, and both projected path laws
are induced by the same plant and transport exactly.
-/
theorem strictPrefixHistory_has_nonvacuous_realized_exact_extension :
    StrictOperationalHistoryPrefix strictPrefixHistorySupport false true ∧
    (finiteStateOutputPathStates
        (strictPrefixHistoryRealization.experiment false).horizon
        (strictPrefixHistoryRealization.witnessedPath false)).IsPrefix
      (finiteStateOutputPathStates
        (strictPrefixHistoryRealization.experiment true).horizon
        (strictPrefixHistoryRealization.witnessedPath true)) ∧
    (finiteStateOutputPathOutputs
        (strictPrefixHistoryRealization.experiment false).horizon
        (strictPrefixHistoryRealization.witnessedPath false)).IsPrefix
      (finiteStateOutputPathOutputs
        (strictPrefixHistoryRealization.experiment true).horizon
        (strictPrefixHistoryRealization.witnessedPath true)) ∧
    (∀ index, (transportedFineJointPathLaw
        (strictPrefixHistoryStudy.pathExperiment index)).mass =
      (inducedFiniteStateOutputPathLaw
        (strictPrefixHistoryStudy.pathExperiment index).abstractExperiment).mass) := by
  have strict : StrictOperationalHistoryPrefix strictPrefixHistorySupport false true := by
    simp [StrictOperationalHistoryPrefix, strictPrefixHistorySupport]
  exact ⟨strict,
    strictPrefixHistoryPrefixConsistency.state_trace_prefix false true strict,
    strictPrefixHistoryPrefixConsistency.output_trace_prefix false true strict,
    strictPrefixHistory_paths_transport_exact⟩

/-- Two-bit finite memory: first bit records past context, second is current state. -/
def contractiveHistoryMachine :
    FiniteHistoryFeedbackMachine (Bool × Bool) Bool Bool where
  representedHistory memory :=
    if memory.1 then [memory.2, memory.2] else [memory.2]
  currentState memory := memory.2
  current_agrees memory := by
    rcases memory with ⟨mode, state⟩
    cases mode <;> simp
  update _ nextState := (nextState, nextState)
  update_current _ _ := rfl
  policy memory := memory.1

theorem contractiveHistoryMachine_policy_uses_past :
    HistoryFeedbackPolicyUsesPast contractiveHistoryMachine := by
  refine ⟨(false, false), (true, false), ?_, ?_, ?_⟩ <;>
    simp [contractiveHistoryMachine]

/-- Same noisy law viewed as a channel from an action bit to a next-state bit. -/
def quarterThreeQuarterActionChannel : FiniteControlledKernel Bool Unit where
  mass action _ target := quarterThreeQuarterPlant.mass false action target
  nonnegative action _ target :=
    quarterThreeQuarterPlant.nonnegative false action target
  normalized action _ := quarterThreeQuarterPlant.normalized false action

theorem quarterThreeQuarterActionChannel_trueMass
    (initial : FiniteProbabilityMass Bool) :
    (evolveFiniteProbability quarterThreeQuarterActionChannel () initial).mass true =
      1 / 4 + (1 / 2) * initial.mass true := by
  have normalization : initial.mass false + initial.mass true = 1 := by
    rw [add_comm]
    simpa [Fintype.sum_bool] using initial.normalized
  simp [evolveFiniteProbability, Fintype.sum_bool,
    quarterThreeQuarterActionChannel, quarterThreeQuarterPlant]
  rw [show initial.mass false = 1 - initial.mass true by
    calc
      initial.mass false =
          (initial.mass false + initial.mass true) - initial.mass true := by ring
      _ = 1 - initial.mass true := by rw [normalization]]
  ring

theorem quarterThreeQuarterActionChannel_has_half_contraction :
    FiniteEvolutionContraction quarterThreeQuarterActionChannel () (1 / 2) := by
  intro left right
  rw [finiteBoolTotalVariation_eq_abs_trueMass,
    finiteBoolTotalVariation_eq_abs_trueMass]
  rw [quarterThreeQuarterActionChannel_trueMass,
    quarterThreeQuarterActionChannel_trueMass]
  have halfNonnegative : (0 : ℚ) ≤ 1 / 2 := by norm_num
  rw [show
    1 / 4 + (1 / 2) * left.mass true -
        (1 / 4 + (1 / 2) * right.mass true) =
      (1 / 2) * (left.mass true - right.mass true) by ring]
  rw [abs_mul, abs_of_nonneg halfNonnegative]

/-- The closed feedback evolution factors through action then noisy state. -/
theorem contractiveHistoryEvolution_factorization
    (initial : FiniteProbabilityMass (Bool × Bool)) :
    (evolveFiniteProbability
      (closeHistoryFeedbackKernel quarterThreeQuarterPlant
        contractiveHistoryMachine)
      () initial).mass =
    (pushforwardFiniteProbability (fun state : Bool => (state, state))
      (evolveFiniteProbability quarterThreeQuarterActionChannel ()
        (pushforwardFiniteProbability contractiveHistoryMachine.policy
          initial))).mass := by
  classical
  funext target
  rcases target with ⟨past, current⟩
  cases past <;> cases current <;>
    simp [evolveFiniteProbability, closeHistoryFeedbackKernel,
      historyFeedbackRowProbability, kernelRowProbability,
      pushforwardFiniteProbability, quarterThreeQuarterPlant,
      quarterThreeQuarterActionChannel, contractiveHistoryMachine,
      Fintype.sum_bool, Fintype.sum_prod_type] <;> ring

theorem contractiveHistoryClosedKernel_is_genuinelyStochastic :
    FiniteKernelGenuinelyStochastic
      (closeHistoryFeedbackKernel quarterThreeQuarterPlant
        contractiveHistoryMachine) := by
  refine ⟨(true, false), (), (false, false), (true, true), ?_, ?_, ?_⟩
  · decide
  · norm_num [closeHistoryFeedbackKernel, historyFeedbackRowProbability,
      kernelRowProbability, pushforwardFiniteProbability,
      quarterThreeQuarterPlant, contractiveHistoryMachine, finiteDirac,
      Fintype.sum_bool]
  · norm_num [closeHistoryFeedbackKernel, historyFeedbackRowProbability,
      kernelRowProbability, pushforwardFiniteProbability,
      quarterThreeQuarterPlant, contractiveHistoryMachine, finiteDirac,
      Fintype.sum_bool]

theorem contractiveHistoryMachine_action_affects_closedLoop :
    ∃ left right target,
      contractiveHistoryMachine.currentState left =
          contractiveHistoryMachine.currentState right ∧
      (closeHistoryFeedbackKernel quarterThreeQuarterPlant
        contractiveHistoryMachine).mass left () target ≠
      (closeHistoryFeedbackKernel quarterThreeQuarterPlant
        contractiveHistoryMachine).mass right () target := by
  refine ⟨(false, false), (true, false), (true, true), rfl, ?_⟩
  norm_num [closeHistoryFeedbackKernel, historyFeedbackRowProbability,
    kernelRowProbability, pushforwardFiniteProbability,
    quarterThreeQuarterPlant, contractiveHistoryMachine, finiteDirac,
    Fintype.sum_bool]

theorem contractiveHistoryClosedKernel_has_half_contraction :
    FiniteEvolutionContraction
      (closeHistoryFeedbackKernel quarterThreeQuarterPlant
        contractiveHistoryMachine)
      () (1 / 2) := by
  intro left right
  let leftAction :=
    pushforwardFiniteProbability contractiveHistoryMachine.policy left
  let rightAction :=
    pushforwardFiniteProbability contractiveHistoryMachine.policy right
  let diagonal := fun state : Bool => (state, state)
  calc
    finiteTotalVariation
        (evolveFiniteProbability
          (closeHistoryFeedbackKernel quarterThreeQuarterPlant
            contractiveHistoryMachine) () left)
        (evolveFiniteProbability
          (closeHistoryFeedbackKernel quarterThreeQuarterPlant
            contractiveHistoryMachine) () right) =
      finiteTotalVariation
        (pushforwardFiniteProbability diagonal
          (evolveFiniteProbability quarterThreeQuarterActionChannel () leftAction))
        (pushforwardFiniteProbability diagonal
          (evolveFiniteProbability quarterThreeQuarterActionChannel () rightAction)) := by
        simp only [finiteTotalVariation]
        rw [contractiveHistoryEvolution_factorization,
          contractiveHistoryEvolution_factorization]
    _ ≤ finiteTotalVariation
        (evolveFiniteProbability quarterThreeQuarterActionChannel () leftAction)
        (evolveFiniteProbability quarterThreeQuarterActionChannel () rightAction) :=
      pushforwardFiniteProbability_nonexpansive diagonal _ _
    _ ≤ (1 / 2) * finiteTotalVariation leftAction rightAction :=
      quarterThreeQuarterActionChannel_has_half_contraction leftAction rightAction
    _ ≤ (1 / 2) * finiteTotalVariation left right := by
      exact mul_le_mul_of_nonneg_left
        (pushforwardFiniteProbability_nonexpansive
          contractiveHistoryMachine.policy left right) (by norm_num)

/-- Initial support contains both past-distinct memories at the same current state. -/
def contractiveHistoryInitial : FiniteProbabilityMass (Bool × Bool) where
  mass memory := if memory.2 then 0 else 1 / 2
  nonnegative memory := by
    rcases memory with ⟨past, current⟩
    cases past <;> cases current <;> norm_num
  normalized := by
    norm_num [Fintype.sum_prod_type, Fintype.sum_bool]

/--
Concrete history-dependent feedback: two reachable pasts choose distinct plant
rows, and a positive-probability sampled next state changes the next action.
-/
def verifiedContractiveHistoryFeedback :
    VerifiedHistoryFeedback (Bool × Bool) Bool Bool where
  plant := quarterThreeQuarterPlant
  machine := contractiveHistoryMachine
  initial := contractiveHistoryInitial
  witnessLeft := (false, false)
  witnessRight := (true, false)
  witnesses_same_current := rfl
  witnesses_distinct_histories := by decide
  witnesses_distinct_actions := by decide
  witnessLeft_reachable := by norm_num [contractiveHistoryInitial]
  witnessRight_reachable := by norm_num [contractiveHistoryInitial]
  action_changes_plant_row := by
    refine ⟨true, ?_⟩
    norm_num [quarterThreeQuarterPlant, contractiveHistoryMachine]
  feedbackMemory := (false, false)
  feedbackMemory_reachable := by norm_num [contractiveHistoryInitial]
  feedbackNextLeft := false
  feedbackNextRight := true
  feedback_next_states_differ := by decide
  feedbackNextLeft_positive := by
    norm_num [quarterThreeQuarterPlant, contractiveHistoryMachine]
  feedbackNextRight_positive := by
    norm_num [quarterThreeQuarterPlant, contractiveHistoryMachine]
  sampled_state_changes_future_action := by
    decide
  randomnessMode := .stochastic
  randomnessEvidence := contractiveHistoryClosedKernel_is_genuinelyStochastic
  contractionCoefficient := 1 / 2
  coefficient_nonnegative := by norm_num
  coefficient_below_one := by norm_num
  contraction := contractiveHistoryClosedKernel_has_half_contraction

/--
Only this evidence-bearing bundle may add `historyDependent` to the feedback
profile.  The generic feedback witness deliberately does not self-assign it.
-/
structure ContractiveHistoryCapabilityCertificate where
  feedback : VerifiedHistoryFeedback (Bool × Bool) Bool Bool
  plant_is_prefix_plant : feedback.plant = quarterThreeQuarterPlant
  prefixConsistency : FrozenHistoryPrefixConsistency
    strictPrefixHistoryRealization
  prefixEvidence : StrictOperationalHistoryPrefix strictPrefixHistorySupport
    false true
  feedback_short_history :
    feedback.machine.representedHistory feedback.witnessLeft =
      strictPrefixHistorySupport.observations false
  feedback_long_history :
    feedback.machine.representedHistory feedback.witnessRight =
      strictPrefixHistorySupport.observations true
  projectedPathLawCompatible : ∀ index,
    (transportedFineJointPathLaw
        (strictPrefixHistoryStudy.pathExperiment index)).mass =
      (inducedFiniteStateOutputPathLaw
        (strictPrefixHistoryStudy.pathExperiment index).abstractExperiment).mass

def ContractiveHistoryCapabilityCertificate.profile
    (certificate : ContractiveHistoryCapabilityCertificate) :
    DynamicsCapabilityProfile where
  supports capability :=
    certificate.feedback.profile.supports capability ∨
      capability = .memory .historyDependent

def verifiedContractiveHistoryCapabilityCertificate :
    ContractiveHistoryCapabilityCertificate where
  feedback := verifiedContractiveHistoryFeedback
  plant_is_prefix_plant := rfl
  prefixConsistency := strictPrefixHistoryPrefixConsistency
  prefixEvidence :=
    strictPrefixHistory_has_nonvacuous_realized_exact_extension.1
  feedback_short_history := by
    simp [verifiedContractiveHistoryFeedback, contractiveHistoryMachine,
      strictPrefixHistorySupport]
  feedback_long_history := by
    simp [verifiedContractiveHistoryFeedback, contractiveHistoryMachine,
      strictPrefixHistorySupport]
  projectedPathLawCompatible :=
    strictPrefixHistory_has_nonvacuous_realized_exact_extension.2.2.2

theorem verifiedContractiveHistoryFeedback_has_prefixConsistentHistoryEvidence :
    verifiedContractiveHistoryCapabilityCertificate.profile.supports
        (.memory .historyDependent) ∧
    StrictOperationalHistoryPrefix strictPrefixHistorySupport false true ∧
    verifiedContractiveHistoryCapabilityCertificate.feedback.machine.representedHistory
        verifiedContractiveHistoryCapabilityCertificate.feedback.witnessLeft =
      strictPrefixHistorySupport.observations false ∧
    verifiedContractiveHistoryCapabilityCertificate.feedback.machine.representedHistory
        verifiedContractiveHistoryCapabilityCertificate.feedback.witnessRight =
      strictPrefixHistorySupport.observations true ∧
    (finiteStateOutputPathStates
        (strictPrefixHistoryRealization.experiment false).horizon
        (strictPrefixHistoryRealization.witnessedPath false)).IsPrefix
      (finiteStateOutputPathStates
        (strictPrefixHistoryRealization.experiment true).horizon
        (strictPrefixHistoryRealization.witnessedPath true)) ∧
    (finiteStateOutputPathOutputs
        (strictPrefixHistoryRealization.experiment false).horizon
        (strictPrefixHistoryRealization.witnessedPath false)).IsPrefix
      (finiteStateOutputPathOutputs
        (strictPrefixHistoryRealization.experiment true).horizon
        (strictPrefixHistoryRealization.witnessedPath true)) ∧
    (∀ index, (transportedFineJointPathLaw
        (strictPrefixHistoryStudy.pathExperiment index)).mass =
      (inducedFiniteStateOutputPathLaw
        (strictPrefixHistoryStudy.pathExperiment index).abstractExperiment).mass) :=
  ⟨Or.inr rfl,
    verifiedContractiveHistoryCapabilityCertificate.prefixEvidence,
    verifiedContractiveHistoryCapabilityCertificate.feedback_short_history,
    verifiedContractiveHistoryCapabilityCertificate.feedback_long_history,
    verifiedContractiveHistoryCapabilityCertificate.prefixConsistency.state_trace_prefix
      false true verifiedContractiveHistoryCapabilityCertificate.prefixEvidence,
    verifiedContractiveHistoryCapabilityCertificate.prefixConsistency.output_trace_prefix
      false true verifiedContractiveHistoryCapabilityCertificate.prefixEvidence,
    verifiedContractiveHistoryCapabilityCertificate.projectedPathLawCompatible⟩

/-- Identity plant used to show that strict feedback contraction is substantive. -/
def persistentBoolPlant : FiniteControlledKernel Bool Unit where
  mass state _ := (finiteDirac state).mass
  nonnegative state _ := (finiteDirac state).nonnegative
  normalized state _ := (finiteDirac state).normalized

def persistentBoolFeedbackMachine :
    FiniteHistoryFeedbackMachine Bool Bool Unit where
  representedHistory state := [state]
  currentState := id
  current_agrees state := by simp
  update _ nextState := nextState
  update_current _ _ := rfl
  policy _ := ()

theorem persistentBoolClosedLoop_evolves_dirac_to_itself (state : Bool) :
    (evolveFiniteProbability
      (closeHistoryFeedbackKernel persistentBoolPlant
        persistentBoolFeedbackMachine)
      () (finiteDirac state)).mass = (finiteDirac state).mass := by
  funext target
  classical
  cases state <;> cases target <;>
    norm_num [evolveFiniteProbability, closeHistoryFeedbackKernel,
      historyFeedbackRowProbability, kernelRowProbability,
      pushforwardFiniteProbability, persistentBoolPlant,
      persistentBoolFeedbackMachine, finiteDirac, Fintype.sum_bool]

/-- No coefficient below one contracts this explicit recurrent closed loop. -/
theorem persistentBoolClosedLoop_has_no_strict_tv_contraction
    (alpha : ℚ)
    (alphaBelowOne : alpha < 1) :
    ¬ FiniteEvolutionContraction
      (closeHistoryFeedbackKernel persistentBoolPlant
        persistentBoolFeedbackMachine) () alpha := by
  intro contraction
  have bound := contraction (finiteDirac false) (finiteDirac true)
  have leftEvolution := persistentBoolClosedLoop_evolves_dirac_to_itself false
  have rightEvolution := persistentBoolClosedLoop_evolves_dirac_to_itself true
  have distinctTV :
      finiteTotalVariation (finiteDirac false) (finiteDirac true) = 1 := by
    norm_num [finiteTotalVariation, finiteDirac, Fintype.sum_bool]
  simp only [finiteTotalVariation] at bound
  rw [leftEvolution, rightEvolution] at bound
  norm_num [finiteDirac, Fintype.sum_bool] at bound
  exact (not_le_of_gt alphaBelowOne) bound

/-- Three complete dynamic witnesses yield genuinely incomparable profiles. -/
theorem concreteVerifiedProfiles_are_pairwise_distinguishable :
    verifiedActionSelectedControlledPath.profile.supports
        (.randomness .deterministic) ∧
    verifiedSwitchingContextBoundaryProcess.profile.supports
        (.openness .openBoundary) ∧
    verifiedContractiveHistoryCapabilityCertificate.profile.supports
        (.composition .feedback) ∧
    ¬ verifiedActionSelectedControlledPath.profile ≤
        verifiedSwitchingContextBoundaryProcess.profile ∧
    ¬ verifiedSwitchingContextBoundaryProcess.profile ≤
        verifiedActionSelectedControlledPath.profile ∧
    ¬ verifiedSwitchingContextBoundaryProcess.profile ≤
        verifiedContractiveHistoryCapabilityCertificate.profile ∧
    ¬ verifiedContractiveHistoryCapabilityCertificate.profile ≤
        verifiedSwitchingContextBoundaryProcess.profile ∧
    ¬ verifiedActionSelectedControlledPath.profile ≤
        verifiedContractiveHistoryCapabilityCertificate.profile ∧
    ¬ verifiedContractiveHistoryCapabilityCertificate.profile ≤
        verifiedActionSelectedControlledPath.profile := by
  constructor
  · simp [VerifiedFiniteControlledStatePath.profile,
      verifiedActionSelectedControlledPath]
  constructor
  · simp [VerifiedJointOpenBoundaryOutput.profile,
      verifiedSwitchingContextBoundaryProcess]
  constructor
  · simp [ContractiveHistoryCapabilityCertificate.profile,
      verifiedContractiveHistoryCapabilityCertificate,
      VerifiedHistoryFeedback.profile, verifiedContractiveHistoryFeedback]
  constructor
  · intro inclusion
    have impossible := inclusion (.randomness .deterministic) (by
      simp [VerifiedFiniteControlledStatePath.profile,
        verifiedActionSelectedControlledPath])
    simp [VerifiedJointOpenBoundaryOutput.profile,
      verifiedSwitchingContextBoundaryProcess] at impossible
  constructor
  · intro inclusion
    have impossible := inclusion (.openness .openBoundary) (by
      simp [VerifiedJointOpenBoundaryOutput.profile,
        verifiedSwitchingContextBoundaryProcess])
    simp [VerifiedFiniteControlledStatePath.profile,
      verifiedActionSelectedControlledPath] at impossible
  constructor
  · intro inclusion
    have impossible := inclusion (.openness .openBoundary) (by
      simp [VerifiedJointOpenBoundaryOutput.profile,
        verifiedSwitchingContextBoundaryProcess])
    simpa [ContractiveHistoryCapabilityCertificate.profile,
      verifiedContractiveHistoryCapabilityCertificate,
      VerifiedHistoryFeedback.profile, verifiedContractiveHistoryFeedback] using
      impossible
  constructor
  · intro inclusion
    have impossible := inclusion (.composition .feedback) (by
      simp [ContractiveHistoryCapabilityCertificate.profile,
        verifiedContractiveHistoryCapabilityCertificate,
        VerifiedHistoryFeedback.profile, verifiedContractiveHistoryFeedback])
    simp [VerifiedJointOpenBoundaryOutput.profile,
      verifiedSwitchingContextBoundaryProcess] at impossible
  constructor
  · intro inclusion
    have impossible := inclusion (.randomness .deterministic) (by
      simp [VerifiedFiniteControlledStatePath.profile,
        verifiedActionSelectedControlledPath])
    simpa [ContractiveHistoryCapabilityCertificate.profile,
      verifiedContractiveHistoryCapabilityCertificate,
      VerifiedHistoryFeedback.profile, verifiedContractiveHistoryFeedback] using
      impossible
  · intro inclusion
    have impossible := inclusion (.composition .feedback) (by
      simp [ContractiveHistoryCapabilityCertificate.profile,
        verifiedContractiveHistoryCapabilityCertificate,
        VerifiedHistoryFeedback.profile, verifiedContractiveHistoryFeedback])
    simp [VerifiedFiniteControlledStatePath.profile,
      verifiedActionSelectedControlledPath] at impossible

/-- Deterministic joint process whose action chooses the next Boolean state. -/
def actionSelectedJointProcess :
    FiniteJointOpenProcess Bool Unit Unit Bool Unit where
  mass _ control := (finiteDirac (control.2.2, ())).mass
  nonnegative _ control := (finiteDirac (control.2.2, ())).nonnegative
  normalized _ control := (finiteDirac (control.2.2, ())).normalized

/-- Identity abstraction for the action-selected joint process. -/
def actionSelectedIdentityAbstraction :
    FiniteJointContextualAbstraction Bool Unit Unit Bool Unit
      Bool Unit Unit Bool Unit where
  fine := actionSelectedJointProcess
  abstract := actionSelectedJointProcess
  stateMap := id
  contextMap := id
  boundaryInMap := id
  actionMap := id
  boundaryOutMap := id

/-- Same horizon and kernel, but deliberately misaligned fine/abstract policy. -/
def misalignedActionExperiments :
    AlignedJointOpenExperiments actionSelectedIdentityAbstraction where
  horizon := 1
  fineInitial := finiteDirac false
  abstractInitial := finiteDirac false
  finePolicy _ := ((), (), false)
  abstractPolicy _ := ((), (), true)

/-- A shared kernel does not manufacture policy transport. -/
theorem misalignedPolicies_have_no_transportAlignment :
    IsEmpty (JointExperimentTransportAlignment misalignedActionExperiments) := by
  refine ⟨?_⟩
  intro alignment
  have stepZero := alignment.policy_transport 0 (by
    norm_num [misalignedActionExperiments])
  simpa [misalignedActionExperiments, actionSelectedIdentityAbstraction] using
    stepZero

theorem actionSelectedIdentityAbstraction_kernelCommutesWitness :
    JointOpenKernelCommutes actionSelectedIdentityAbstraction := by
  intro state context boundary action
  funext outcome
  rcases outcome with ⟨target, output⟩
  cases output
  cases state <;> cases action <;> cases target <;>
    norm_num [actionSelectedIdentityAbstraction, actionSelectedJointProcess,
      jointStepProbability, pushforwardFiniteProbability, jointOutcomeMap,
      finiteDirac, Fintype.sum_bool]

/-- A genuine state-reactive policy: the current state selects the next action. -/
def stateReactiveJointFeedbackPolicy
    (step : Nat) (path : FiniteStateOutputPath Bool Unit step) :
    JointOpenControl Unit Unit Bool :=
  ((), (), finiteStateOutputPathLastState step path)

def stateReactiveAlignedFeedbackData :
    AlignedJointFeedbackExperiments actionSelectedIdentityAbstraction where
  horizon := 2
  fineInitial := finiteDirac false
  abstractInitial := finiteDirac false
  finePolicy := stateReactiveJointFeedbackPolicy
  abstractPolicy := stateReactiveJointFeedbackPolicy

theorem stateReactiveAlignedFeedbackData_has_transportAlignment :
    JointFeedbackExperimentTransportAlignment stateReactiveAlignedFeedbackData := by
  refine {
    initial_transport := ?_
    policy_transport := ?_
  }
  · funext state
    cases state <;>
      norm_num [stateReactiveAlignedFeedbackData,
        actionSelectedIdentityAbstraction, pushforwardFiniteProbability,
        finiteDirac, Fintype.sum_bool]
  · intro step finePrefix
    change
      ((), (), finiteStateOutputPathLastState step
        (mapFiniteStateOutputPath id id step finePrefix)) =
      ((), (), finiteStateOutputPathLastState step finePrefix)
    rw [finiteStateOutputPathLastState_map]
    rfl

theorem stateReactiveFeedbackPath_transport_is_exact :
    (transportedFineFeedbackJointPathLaw stateReactiveAlignedFeedbackData).mass =
      (inducedFiniteFeedbackStateOutputPathLaw
        stateReactiveAlignedFeedbackData.abstractExperiment).mass :=
  jointOpenKernelCommutes_and_feedbackAlignment_imply_pathLawExact
    stateReactiveAlignedFeedbackData
    stateReactiveAlignedFeedbackData_has_transportAlignment
    actionSelectedIdentityAbstraction_kernelCommutesWitness

def actionFalseSingletonIdentity : IdentityPresentation Unit Bool where
  stateOf _ := false
  continuationEvidence _ _ := False
  assembledTogether _ _ := False

def misalignedFineIdentityBridge :
    IdentityProcessBridge actionFalseSingletonIdentity
      misalignedActionExperiments.fineExperiment where
  candidate := {
    witnessedPath := (ULift.up false, (false, ()))
    occurrenceTime _ := 0
    occurrenceOutput _ := none
    occurrenceHistory _ := [false]
  }
  compatible := by
    simp [IdentityProcessCompatibility, misalignedActionExperiments,
      AlignedJointOpenExperiments.fineExperiment, actionSelectedIdentityAbstraction,
      actionSelectedJointProcess, inducedFiniteStateOutputPathLaw,
      inducedJointPathWeightAt, finiteStateOutputPathStates,
      finiteStateOutputPathOutputs, actionFalseSingletonIdentity, finiteDirac]

def misalignedAbstractInducedLaw :
    FiniteProbabilityMass
      (FiniteStateOutputPath Bool Unit
        misalignedActionExperiments.abstractExperiment.horizon) :=
  inducedFiniteStateOutputPathLaw misalignedActionExperiments.abstractExperiment

/-- Alignment is independent: the other four coherence gates can all hold. -/
theorem misalignedCandidate_has_all_typed_gates_except_transportAlignment :
    JointOpenKernelCommutes actionSelectedIdentityAbstraction ∧
    Nonempty (IdentityProcessBridge actionFalseSingletonIdentity
      misalignedActionExperiments.fineExperiment) ∧
    JointIdentityAbstractionCompatibility misalignedFineIdentityBridge ∧
    JointLawRealization misalignedActionExperiments.abstractExperiment
      misalignedAbstractInducedLaw ∧
    IsEmpty (JointExperimentTransportAlignment misalignedActionExperiments) :=
  ⟨actionSelectedIdentityAbstraction_kernelCommutesWitness,
    ⟨misalignedFineIdentityBridge⟩, (by
      intro left right assembled
      exact False.elim assembled), rfl,
    misalignedPolicies_have_no_transportAlignment⟩

/-- Abstract process deliberately ignores the action and always emits `false`. -/
def alwaysFalseJointProcess :
    FiniteJointOpenProcess Bool Unit Unit Bool Unit where
  mass _ _ := (finiteDirac (false, ())).mass
  nonnegative _ _ := (finiteDirac (false, ())).nonnegative
  normalized _ _ := (finiteDirac (false, ())).normalized

def noncommutingActionAbstraction :
    FiniteJointContextualAbstraction Bool Unit Unit Bool Unit
      Bool Unit Unit Bool Unit where
  fine := actionSelectedJointProcess
  abstract := alwaysFalseJointProcess
  stateMap := id
  contextMap := id
  boundaryInMap := id
  actionMap := id
  boundaryOutMap := id

def noncommutingAlignedData :
    AlignedJointOpenExperiments noncommutingActionAbstraction where
  horizon := 1
  fineInitial := finiteDirac false
  abstractInitial := finiteDirac false
  finePolicy _ := ((), (), true)
  abstractPolicy _ := ((), (), true)

theorem noncommutingAlignedData_has_transportAlignment :
    JointExperimentTransportAlignment noncommutingAlignedData := by
  refine {
    initial_transport := ?_
    policy_transport := ?_
  }
  · funext state
    cases state <;>
      norm_num [noncommutingAlignedData, noncommutingActionAbstraction,
        pushforwardFiniteProbability, finiteDirac, Fintype.sum_bool]
  · intro step _
    rfl

def noncommutingFineIdentityBridge :
    IdentityProcessBridge actionFalseSingletonIdentity
      noncommutingAlignedData.fineExperiment where
  candidate := {
    witnessedPath := (ULift.up false, (true, ()))
    occurrenceTime _ := 0
    occurrenceOutput _ := none
    occurrenceHistory _ := [false]
  }
  compatible := by
    simp [IdentityProcessCompatibility, noncommutingAlignedData,
      AlignedJointOpenExperiments.fineExperiment, noncommutingActionAbstraction,
      actionSelectedJointProcess, inducedFiniteStateOutputPathLaw,
      inducedJointPathWeightAt, finiteStateOutputPathStates,
      finiteStateOutputPathOutputs, actionFalseSingletonIdentity, finiteDirac]

def noncommutingAbstractInducedLaw :
    FiniteProbabilityMass
      (FiniteStateOutputPath Bool Unit
        noncommutingAlignedData.abstractExperiment.horizon) :=
  inducedFiniteStateOutputPathLaw noncommutingAlignedData.abstractExperiment

theorem noncommutingActionAbstraction_fails_kernelCommutes :
    ¬ JointOpenKernelCommutes noncommutingActionAbstraction := by
  intro commutes
  have atTrue := congrFun (commutes false () () true) (true, ())
  norm_num [noncommutingActionAbstraction, alwaysFalseJointProcess,
    actionSelectedJointProcess, jointStepProbability,
    pushforwardFiniteProbability, jointOutcomeMap, finiteDirac,
    Fintype.sum_bool] at atTrue

/-- One-step commutation is independent of the other four typed gates. -/
theorem noncommutingCandidate_has_all_typed_gates_except_kernelCommutes :
    Nonempty (JointExperimentTransportAlignment noncommutingAlignedData) ∧
    Nonempty (IdentityProcessBridge actionFalseSingletonIdentity
      noncommutingAlignedData.fineExperiment) ∧
    JointIdentityAbstractionCompatibility noncommutingFineIdentityBridge ∧
    JointLawRealization noncommutingAlignedData.abstractExperiment
      noncommutingAbstractInducedLaw ∧
    ¬ JointOpenKernelCommutes noncommutingActionAbstraction :=
  ⟨⟨noncommutingAlignedData_has_transportAlignment⟩,
    ⟨noncommutingFineIdentityBridge⟩, (by
      intro left right assembled
      exact False.elim assembled), rfl,
    noncommutingActionAbstraction_fails_kernelCommutes⟩

/-- Zero-horizon experiment with a point mass at `false`. -/
def falseZeroHorizonJointExperiment :
    FiniteJointOpenExperiment Bool Unit Unit Bool Unit where
  process := actionSelectedJointProcess
  horizon := 0
  initial := finiteDirac false
  policy _ := ((), (), false)

def falseZeroHorizonAlignedData :
    AlignedJointOpenExperiments actionSelectedIdentityAbstraction where
  horizon := 0
  fineInitial := finiteDirac false
  abstractInitial := finiteDirac false
  finePolicy _ := ((), (), false)
  abstractPolicy _ := ((), (), false)

theorem falseZeroHorizonAlignedData_has_transportAlignment :
    JointExperimentTransportAlignment falseZeroHorizonAlignedData := by
  refine {
    initial_transport := ?_
    policy_transport := ?_
  }
  · funext state
    cases state <;>
      norm_num [falseZeroHorizonAlignedData, actionSelectedIdentityAbstraction,
        pushforwardFiniteProbability, finiteDirac, Fintype.sum_bool]
  · intro step stepBeforeZero
    exact (Nat.not_lt_zero step stepBeforeZero).elim

theorem actionSelectedIdentityAbstraction_kernelCommutes :
    JointOpenKernelCommutes actionSelectedIdentityAbstraction :=
  actionSelectedIdentityAbstraction_kernelCommutesWitness

def falseSingletonIdentity : IdentityPresentation Unit Bool where
  stateOf _ := false
  continuationEvidence _ _ := False
  assembledTogether _ _ := False

def falseSingletonIdentityProcessBridge :
    IdentityProcessBridge falseSingletonIdentity
      falseZeroHorizonAlignedData.fineExperiment where
  candidate := {
    witnessedPath := ULift.up false
    occurrenceTime _ := 0
    occurrenceOutput _ := none
    occurrenceHistory _ := [false]
  }
  compatible := by
    simp [IdentityProcessCompatibility, falseZeroHorizonAlignedData,
      AlignedJointOpenExperiments.fineExperiment, inducedFiniteStateOutputPathLaw,
      inducedJointPathWeightAt, falseSingletonIdentity,
      finiteStateOutputPathStates, finiteStateOutputPathOutputs, finiteDirac]

/-- Wrong normalized candidate point mass at `true`. -/
def wrongFalseZeroHorizonJointLaw :
    FiniteProbabilityMass
      (FiniteStateOutputPath Bool Unit falseZeroHorizonJointExperiment.horizon) :=
  finiteDirac (ULift.up true)

/-- Normalization does not imply realization by the declared process. -/
theorem wrongFalseZeroHorizonJointLaw_not_realized :
    ¬ JointLawRealization falseZeroHorizonJointExperiment
      wrongFalseZeroHorizonJointLaw := by
  intro realization
  have atFalse := congrFun realization (ULift.up false)
  have lawsDiffer :
      wrongFalseZeroHorizonJointLaw.mass (ULift.up false) ≠
        (inducedFiniteStateOutputPathLaw falseZeroHorizonJointExperiment).mass
          (ULift.up false) := by decide
  exact lawsDiffer atFalse

/-- All other typed gates can hold while an independently supplied law fails. -/
theorem wrongCandidate_has_all_typed_gates_except_lawRealization :
    Nonempty (JointExperimentTransportAlignment falseZeroHorizonAlignedData) ∧
    JointOpenKernelCommutes actionSelectedIdentityAbstraction ∧
    Nonempty (IdentityProcessBridge falseSingletonIdentity
      falseZeroHorizonAlignedData.fineExperiment) ∧
    JointIdentityAbstractionCompatibility falseSingletonIdentityProcessBridge ∧
    ¬ JointLawRealization falseZeroHorizonAlignedData.abstractExperiment
      wrongFalseZeroHorizonJointLaw := by
  exact ⟨⟨falseZeroHorizonAlignedData_has_transportAlignment⟩,
    actionSelectedIdentityAbstraction_kernelCommutes,
    ⟨falseSingletonIdentityProcessBridge⟩,
    (by
      intro left right assembled
      exact False.elim assembled),
    wrongFalseZeroHorizonJointLaw_not_realized⟩

/-- Two occurrence states that cannot both occupy one zero-horizon trace. -/
def incompatibleZeroHorizonIdentity : IdentityPresentation Bool Bool where
  stateOf := id
  continuationEvidence _ _ := False
  assembledTogether _ _ := False

/-- Exact law realization cannot create a missing identity/process bridge. -/
theorem exactZeroHorizonLaw_has_no_incompatibleIdentityBridge :
    IsEmpty (IdentityProcessBridge incompatibleZeroHorizonIdentity
      falseZeroHorizonJointExperiment) := by
  refine ⟨?_⟩
  intro bridge
  rcases bridge.compatible with ⟨_, statePosition, _, _, _, _⟩
  have falsePosition := statePosition false
  have truePosition := statePosition true
  cases hFalse : bridge.candidate.occurrenceTime false <;>
    cases hTrue : bridge.candidate.occurrenceTime true <;>
      simp_all [falseZeroHorizonJointExperiment,
        incompatibleZeroHorizonIdentity, finiteStateOutputPathStates]

/-- Correct path law supplied by the primitive process itself. -/
def correctFalseZeroHorizonJointLaw :
    FiniteProbabilityMass
      (FiniteStateOutputPath Bool Unit
        falseZeroHorizonAlignedData.abstractExperiment.horizon) :=
  inducedFiniteStateOutputPathLaw falseZeroHorizonAlignedData.abstractExperiment

/-- All nonidentity gates can hold while the single-trace identity bridge fails. -/
theorem incompatibleIdentity_has_all_typed_gates_except_identityBridge :
    Nonempty (JointExperimentTransportAlignment falseZeroHorizonAlignedData) ∧
    JointOpenKernelCommutes actionSelectedIdentityAbstraction ∧
    JointLawRealization falseZeroHorizonAlignedData.abstractExperiment
      correctFalseZeroHorizonJointLaw ∧
    IsEmpty (IdentityProcessBridge incompatibleZeroHorizonIdentity
      falseZeroHorizonAlignedData.fineExperiment) := by
  exact ⟨⟨falseZeroHorizonAlignedData_has_transportAlignment⟩,
    actionSelectedIdentityAbstraction_kernelCommutes, rfl,
    exactZeroHorizonLaw_has_no_incompatibleIdentityBridge⟩

/-! A separate leave-one-out fixture for identity-to-abstraction compatibility. -/

def trueStepAlignedData :
    AlignedJointOpenExperiments actionSelectedIdentityAbstraction where
  horizon := 1
  fineInitial := finiteDirac false
  abstractInitial := finiteDirac false
  finePolicy _ := ((), (), true)
  abstractPolicy _ := ((), (), true)

theorem trueStepAlignedData_has_transportAlignment :
    JointExperimentTransportAlignment trueStepAlignedData := by
  refine {
    initial_transport := ?_
    policy_transport := ?_
  }
  · funext state
    cases state <;>
      norm_num [trueStepAlignedData, actionSelectedIdentityAbstraction,
        pushforwardFiniteProbability, finiteDirac, Fintype.sum_bool]
  · intro step _
    rfl

/-- Assembly asserts that the two consecutive, predictively distinct states are one. -/
def assembledDistinctTraceIdentity : IdentityPresentation Bool Bool where
  stateOf := id
  continuationEvidence left right := left = false ∧ right = true
  assembledTogether left right := left = false ∧ right = true

def assembledDistinctTraceIdentityBridge :
    IdentityProcessBridge assembledDistinctTraceIdentity
      trueStepAlignedData.fineExperiment where
  candidate := {
    witnessedPath := (ULift.up false, (true, ()))
    occurrenceTime occurrence := if occurrence then 1 else 0
    occurrenceOutput occurrence := if occurrence then some () else none
    occurrenceHistory occurrence := if occurrence then [false, true] else [false]
  }
  compatible := by
    refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩
    · simp only [trueStepAlignedData, AlignedJointOpenExperiments.fineExperiment]
      norm_num [trueStepAlignedData, AlignedJointOpenExperiments.fineExperiment,
        actionSelectedIdentityAbstraction, actionSelectedJointProcess,
        inducedFiniteStateOutputPathLaw, inducedJointPathWeightAt, finiteDirac]
    · intro occurrence
      cases occurrence <;> decide
    · intro occurrence
      cases occurrence <;> decide
    · intro occurrence
      cases occurrence <;> decide
    · intro left right evidence
      rcases evidence with ⟨rfl, rfl⟩
      norm_num
    · intro left right assembled
      exact Relation.ReflTransGen.single (Or.inl assembled)

def trueStepAbstractInducedLaw :
    FiniteProbabilityMass
      (FiniteStateOutputPath Bool Unit trueStepAlignedData.horizon) :=
  inducedFiniteStateOutputPathLaw trueStepAlignedData.abstractExperiment

theorem assembledDistinctTraceIdentity_fails_abstractionCompatibility :
    ¬ JointIdentityAbstractionCompatibility assembledDistinctTraceIdentityBridge := by
  intro compatible
  have falseEqualsTrue := compatible (left := false) (right := true) ⟨rfl, rfl⟩
  simpa [actionSelectedIdentityAbstraction, assembledDistinctTraceIdentity] using
    falseEqualsTrue

/-- The fifth gate is independent: process, transport, kernel, and law remain exact. -/
theorem assembledDistinctTrace_has_all_typed_gates_except_identityAbstraction :
    Nonempty (JointExperimentTransportAlignment trueStepAlignedData) ∧
    JointOpenKernelCommutes actionSelectedIdentityAbstraction ∧
    Nonempty (IdentityProcessBridge assembledDistinctTraceIdentity
      trueStepAlignedData.fineExperiment) ∧
    JointLawRealization trueStepAlignedData.abstractExperiment
      trueStepAbstractInducedLaw ∧
    ¬ JointIdentityAbstractionCompatibility assembledDistinctTraceIdentityBridge :=
  ⟨⟨trueStepAlignedData_has_transportAlignment⟩,
    actionSelectedIdentityAbstraction_kernelCommutes,
    ⟨assembledDistinctTraceIdentityBridge⟩, rfl,
    assembledDistinctTraceIdentity_fails_abstractionCompatibility⟩

/-- Joint process used only as the abstract candidate for a history fixture. -/
def unitFalseBoundaryProcess :
    FiniteJointOpenProcess Unit Unit Unit Unit Bool where
  mass _ _ := (finiteDirac ((), false)).mass
  nonnegative _ _ := (finiteDirac ((), false)).nonnegative
  normalized _ _ := (finiteDirac ((), false)).normalized

def unitBoundaryIdentityAbstraction :
    FiniteJointContextualAbstraction Unit Unit Unit Unit Bool
      Unit Unit Unit Unit Bool where
  fine := unitFalseBoundaryProcess
  abstract := unitFalseBoundaryProcess
  stateMap := id
  contextMap := id
  boundaryInMap := id
  actionMap := id
  boundaryOutMap := id

/--
History-encoder consistency for the emitted-boundary marginal.  This is a
separate lane from `HistoryEncoderKernelConsistent`, which compares only the
transported state marginal.
-/
def HistoryEncoderBoundaryConsistent
    {HistoryIndex Observation State Context BoundaryIn Action BoundaryOut
      AbstractState AbstractContext AbstractBoundaryIn AbstractAction
      AbstractBoundaryOut : Type*}
    [Fintype HistoryIndex] [Fintype State] [Fintype BoundaryOut]
    [Fintype AbstractState] [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState] [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (historyAbstraction :
      OperationalHistoryAbstraction (Observation := Observation) abstraction)
    (historyProcess : FiniteHistoryJointOpenProcess HistoryIndex Observation
      State Context BoundaryIn Action BoundaryOut) : Prop :=
  ∀ left right,
    HistoryComparisonAligned historyAbstraction historyProcess left right →
      (transportedFineHistoryBoundaryLaw abstraction historyProcess left).mass =
        (transportedFineHistoryBoundaryLaw abstraction historyProcess right).mass

/-- History-encoder consistency for the full transported state/output law. -/
def HistoryEncoderJointConsistent
    {HistoryIndex Observation State Context BoundaryIn Action BoundaryOut
      AbstractState AbstractContext AbstractBoundaryIn AbstractAction
      AbstractBoundaryOut : Type*}
    [Fintype HistoryIndex] [Fintype State] [Fintype BoundaryOut]
    [Fintype AbstractState] [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState] [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (historyAbstraction :
      OperationalHistoryAbstraction (Observation := Observation) abstraction)
    (historyProcess : FiniteHistoryJointOpenProcess HistoryIndex Observation
      State Context BoundaryIn Action BoundaryOut) : Prop :=
  ∀ left right,
    HistoryComparisonAligned historyAbstraction historyProcess left right →
      (transportedFineHistoryJointLaw abstraction historyProcess left).mass =
        (transportedFineHistoryJointLaw abstraction historyProcess right).mass

theorem historyEncoderJointConsistent_implies_stateKernelConsistent
    {HistoryIndex Observation State Context BoundaryIn Action BoundaryOut
      AbstractState AbstractContext AbstractBoundaryIn AbstractAction
      AbstractBoundaryOut : Type*}
    [Fintype HistoryIndex] [Fintype State] [Fintype BoundaryOut]
    [Fintype AbstractState] [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState] [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (historyAbstraction :
      OperationalHistoryAbstraction (Observation := Observation) abstraction)
    (historyProcess : FiniteHistoryJointOpenProcess HistoryIndex Observation
      State Context BoundaryIn Action BoundaryOut)
    (jointConsistent :
      HistoryEncoderJointConsistent historyAbstraction historyProcess) :
    HistoryEncoderKernelConsistent historyAbstraction historyProcess := by
  intro left right aligned
  have jointEquality := jointConsistent left right aligned
  funext state
  simp only [transportedFineHistoryStateLaw, pushforwardFiniteProbability]
  apply Finset.sum_congr rfl
  intro outcome _
  rw [congrFun jointEquality outcome]

theorem historyEncoderJointConsistent_implies_boundaryConsistent
    {HistoryIndex Observation State Context BoundaryIn Action BoundaryOut
      AbstractState AbstractContext AbstractBoundaryIn AbstractAction
      AbstractBoundaryOut : Type*}
    [Fintype HistoryIndex] [Fintype State] [Fintype BoundaryOut]
    [Fintype AbstractState] [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState] [DecidableEq AbstractBoundaryOut]
    {abstraction : FiniteJointContextualAbstraction State Context BoundaryIn
      Action BoundaryOut AbstractState AbstractContext AbstractBoundaryIn
      AbstractAction AbstractBoundaryOut}
    (historyAbstraction :
      OperationalHistoryAbstraction (Observation := Observation) abstraction)
    (historyProcess : FiniteHistoryJointOpenProcess HistoryIndex Observation
      State Context BoundaryIn Action BoundaryOut)
    (jointConsistent :
      HistoryEncoderJointConsistent historyAbstraction historyProcess) :
    HistoryEncoderBoundaryConsistent historyAbstraction historyProcess := by
  intro left right aligned
  have jointEquality := jointConsistent left right aligned
  funext output
  simp only [transportedFineHistoryBoundaryLaw, pushforwardFiniteProbability]
  apply Finset.sum_congr rfl
  intro outcome _
  rw [congrFun jointEquality outcome]

/-- Two histories with the same final observation and same current control. -/
def historyCollisionSupport :
    FrozenOperationalHistorySupport Bool Bool Unit Unit Unit where
  observations
    | false => [false, false]
    | true => [true, false]
  controls _ := [((), (), ())]
  currentContext _ := ()
  currentBoundaryIn _ := ()
  currentAction _ := ()
  observations_nonempty index := by cases index <;> simp
  history_shape index := by cases index <;> simp

/-- Primitive history laws remain distinguishable despite equal final observation. -/
def historyCollisionProcess :
    FiniteHistoryJointOpenProcess Bool Bool Unit Unit Unit Unit Bool where
  support := historyCollisionSupport
  nextLaw
    | false => finiteDirac ((), false)
    | true => finiteDirac ((), true)

/-- Last-observation encoder, deliberately insufficient for the fixture. -/
def lastObservationHistoryAbstraction :
    OperationalHistoryAbstraction
      (Observation := Bool) unitBoundaryIdentityAbstraction where
  observeState _ := false
  qChi _ _ _ := ()
  singleton_compatibility _ _ := rfl

theorem historyCollision_pair_is_aligned :
    HistoryComparisonAligned lastObservationHistoryAbstraction
      historyCollisionProcess false true := by
  exact ⟨rfl, rfl⟩

/--
The fixture is state-kernel consistent: its two histories differ only in the
emitted-boundary coordinate, and both transported state laws live on `Unit`.
-/
theorem historyCollision_encoder_is_stateKernelConsistent :
    HistoryEncoderKernelConsistent lastObservationHistoryAbstraction
      historyCollisionProcess := by
  intro left right aligned
  funext state
  cases state
  cases left <;> cases right <;>
    norm_num [transportedFineHistoryStateLaw,
      transportedFineHistoryJointLaw, historyCollisionProcess,
      unitBoundaryIdentityAbstraction, jointOutcomeMap,
      pushforwardFiniteProbability, finiteDirac, Fintype.sum_prod_type,
      Fintype.sum_bool] at aligned ⊢

/-- Equal state marginals do not manufacture emitted-boundary consistency. -/
theorem historyCollision_encoder_not_boundaryConsistent :
    ¬ HistoryEncoderBoundaryConsistent lastObservationHistoryAbstraction
      historyCollisionProcess := by
  intro consistent
  have equalLaw := consistent false true historyCollision_pair_is_aligned
  have atFalse := congrFun equalLaw false
  norm_num [transportedFineHistoryBoundaryLaw,
    transportedFineHistoryJointLaw, historyCollisionProcess,
    unitBoundaryIdentityAbstraction, jointOutcomeMap,
    pushforwardFiniteProbability, finiteDirac, Fintype.sum_prod_type,
    Fintype.sum_bool] at atFalse

/-- Hence the full transported state/output law is not encoder-consistent. -/
theorem historyCollision_encoder_not_jointConsistent :
    ¬ HistoryEncoderJointConsistent lastObservationHistoryAbstraction
      historyCollisionProcess := by
  intro jointConsistent
  exact historyCollision_encoder_not_boundaryConsistent
    (historyEncoderJointConsistent_implies_boundaryConsistent
      lastObservationHistoryAbstraction historyCollisionProcess jointConsistent)

/-- Hidden-state histories with identical observations but different endpoints. -/
def hiddenStateHistorySupport :
    FrozenOperationalHistorySupport Bool Unit Unit Unit Unit where
  observations _ := [(), ()]
  controls _ := [((), (), ())]
  currentContext _ := ()
  currentBoundaryIn _ := ()
  currentAction _ := ()
  observations_nonempty _ := by simp
  history_shape _ := by simp

def hiddenStateHistoryProcess :
    FiniteHistoryJointOpenProcess Bool Unit Bool Unit Unit Unit Bool where
  support := hiddenStateHistorySupport
  nextLaw hidden := finiteDirac (hidden, hidden)

def hiddenStateMarkovPlant :
    FiniteJointOpenProcess Bool Unit Unit Unit Bool where
  mass state _ := (finiteDirac (state, state)).mass
  nonnegative state _ := (finiteDirac (state, state)).nonnegative
  normalized state _ := (finiteDirac (state, state)).normalized

def hiddenStateHistoryExperiment (hidden : Bool) :
    FiniteJointOpenExperiment Bool Unit Unit Unit Bool where
  process := hiddenStateMarkovPlant
  horizon := 1
  initial := finiteDirac hidden
  policy _ := ((), (), ())

/--
Concrete existence witness: a history-dependent visible law is realized by a
memoryless Markov plant on a richer hidden state and a positive state/output
path, with the recorded control trace matched exactly.
-/
def hiddenStateHistory_has_markov_realization :
    FrozenHistoryMarkovRealization hiddenStateHistoryProcess
      hiddenStateMarkovPlant where
  observeState _ := ()
  experiment := hiddenStateHistoryExperiment
  experiment_uses_plant _ := rfl
  horizon_agrees _ := rfl
  policy_agrees _ _ _ := rfl
  witnessedPath hidden := (ULift.up hidden, (hidden, hidden))
  witnessed_path_positive hidden := by
    cases hidden
    · simp only [hiddenStateHistoryExperiment]
      norm_num [hiddenStateHistoryExperiment, hiddenStateMarkovPlant,
        inducedFiniteStateOutputPathLaw, inducedJointPathWeightAt,
        finiteStateOutputPathLastState, finiteDirac]
    · simp only [hiddenStateHistoryExperiment]
      norm_num [hiddenStateHistoryExperiment, hiddenStateMarkovPlant,
        inducedFiniteStateOutputPathLaw, inducedJointPathWeightAt,
        finiteStateOutputPathLastState, finiteDirac]
  observations_realized hidden := by
    cases hidden <;> rfl
  next_law_realized hidden := by
    cases hidden <;> decide

/-- Equal-length hidden alternatives do not create a missing strict-prefix case. -/
def hiddenStateHistoryPrefixConsistency :
    FrozenHistoryPrefixConsistency hiddenStateHistory_has_markov_realization where
  state_trace_prefix short long strictPrefix := by
    cases short <;> cases long <;>
      norm_num [StrictOperationalHistoryPrefix, hiddenStateHistoryProcess,
        hiddenStateHistorySupport] at strictPrefix
  output_trace_prefix short long strictPrefix := by
    cases short <;> cases long <;>
      norm_num [StrictOperationalHistoryPrefix, hiddenStateHistoryProcess,
        hiddenStateHistorySupport] at strictPrefix

/-- Collapse the hidden state but retain the emitted Boolean outcome. -/
def hiddenStateCollapsedAbstraction :
    FiniteJointContextualAbstraction Bool Unit Unit Unit Bool
      Unit Unit Unit Unit Bool where
  fine := hiddenStateMarkovPlant
  abstract := unitFalseBoundaryProcess
  stateMap _ := ()
  contextMap := id
  boundaryInMap := id
  actionMap := id
  boundaryOutMap := id

def hiddenStateCollapsedHistoryAbstraction :
    OperationalHistoryAbstraction
      (Observation := Unit) hiddenStateCollapsedAbstraction where
  observeState _ := ()
  qChi _ _ _ := ()
  singleton_compatibility _ _ := rfl

theorem hiddenStateCollapsedHistories_are_encoderAligned :
    HistoryComparisonAligned hiddenStateCollapsedHistoryAbstraction
      hiddenStateHistoryProcess false true := by
  exact ⟨rfl, rfl⟩

/--
Two-component state: the first bit is a latent mode and the second bit is the
visible coordinate.  Historical action `false` preserves the current state;
the current action `true` exposes the mode in the next visible coordinate.
-/
def latentVisiblePlant :
    FiniteJointOpenProcess (Bool × Bool) Unit Unit Bool Unit where
  mass state control :=
    (finiteDirac
      ((if control.2.2 then state.1 else state.1,
        if control.2.2 then state.1 else state.2), ())).mass
  nonnegative state control :=
    (finiteDirac
      ((if control.2.2 then state.1 else state.1,
        if control.2.2 then state.1 else state.2), ())).nonnegative
  normalized state control :=
    (finiteDirac
      ((if control.2.2 then state.1 else state.1,
        if control.2.2 then state.1 else state.2), ())).normalized

def latentVisibleHistorySupport :
    FrozenOperationalHistorySupport Bool Bool Unit Unit Bool where
  observations _ := [false, false]
  controls _ := [((), (), false)]
  currentContext _ := ()
  currentBoundaryIn _ := ()
  currentAction _ := true
  observations_nonempty _ := by simp
  history_shape _ := by simp

def latentVisibleHistoryProcess :
    FiniteHistoryJointOpenProcess Bool Bool (Bool × Bool) Unit Unit Bool Unit where
  support := latentVisibleHistorySupport
  nextLaw hidden := finiteDirac ((hidden, hidden), ())

def latentVisibleHistoryExperiment (hidden : Bool) :
    FiniteJointOpenExperiment (Bool × Bool) Unit Unit Bool Unit where
  process := latentVisiblePlant
  horizon := 1
  initial := finiteDirac (hidden, false)
  policy _ := ((), (), false)

def latentVisibleHistoryRealization :
    FrozenHistoryMarkovRealization latentVisibleHistoryProcess
      latentVisiblePlant where
  observeState state := state.2
  experiment := latentVisibleHistoryExperiment
  experiment_uses_plant _ := rfl
  horizon_agrees _ := rfl
  policy_agrees hidden step stepInHistory := by
    have step_lt_one : step < 1 := by
      simpa [latentVisibleHistoryProcess, latentVisibleHistorySupport] using
        stepInHistory
    have step_eq : step = 0 := by omega
    subst step
    simp [latentVisibleHistoryExperiment, latentVisibleHistoryProcess,
      latentVisibleHistorySupport]
  witnessedPath hidden := (ULift.up (hidden, false), ((hidden, false), ()))
  witnessed_path_positive hidden := by
    cases hidden
    · simp only [latentVisibleHistoryExperiment]
      norm_num [latentVisibleHistoryExperiment, latentVisiblePlant,
        inducedFiniteStateOutputPathLaw, inducedJointPathWeightAt,
        finiteStateOutputPathLastState, finiteDirac]
    · simp only [latentVisibleHistoryExperiment]
      norm_num [latentVisibleHistoryExperiment, latentVisiblePlant,
        inducedFiniteStateOutputPathLaw, inducedJointPathWeightAt,
        finiteStateOutputPathLastState, finiteDirac]
  observations_realized hidden := by
    cases hidden <;> rfl
  next_law_realized hidden := by
    cases hidden <;> decide

def latentVisibleHistoryPrefixConsistency :
    FrozenHistoryPrefixConsistency latentVisibleHistoryRealization where
  state_trace_prefix short long strictPrefix := by
    cases short <;> cases long <;>
      norm_num [StrictOperationalHistoryPrefix, latentVisibleHistoryProcess,
        latentVisibleHistorySupport] at strictPrefix
  output_trace_prefix short long strictPrefix := by
    cases short <;> cases long <;>
      norm_num [StrictOperationalHistoryPrefix, latentVisibleHistoryProcess,
        latentVisibleHistorySupport] at strictPrefix

def persistentVisibleAbstractPlant :
    FiniteJointOpenProcess Bool Unit Unit Bool Unit where
  mass state _ := (finiteDirac (state, ())).mass
  nonnegative state _ := (finiteDirac (state, ())).nonnegative
  normalized state _ := (finiteDirac (state, ())).normalized

def latentVisibleAbstraction :
    FiniteJointContextualAbstraction (Bool × Bool) Unit Unit Bool Unit
      Bool Unit Unit Bool Unit where
  fine := latentVisiblePlant
  abstract := persistentVisibleAbstractPlant
  stateMap state := state.2
  contextMap := id
  boundaryInMap := id
  actionMap := id
  boundaryOutMap := id

def latentVisibleHistoryAbstraction :
    OperationalHistoryAbstraction
      (Observation := Bool) latentVisibleAbstraction where
  observeState state := state.2
  qChi _ observations _ := lastBoolObservation observations
  singleton_compatibility _ state := by
    cases state <;> rfl

theorem latentVisibleHistories_are_encoderAligned :
    HistoryComparisonAligned latentVisibleHistoryAbstraction
      latentVisibleHistoryProcess false true := by
  exact ⟨rfl, rfl⟩

/--
Process-realized qChi no-go: two positive, prefix-consistent Markov traces have
the same visible history and current control, yet their next visible-state laws
differ.  The failure is encoder insufficiency, not an arbitrary supplied law.
-/
theorem realizedHiddenStateHistory_encoder_not_kernelConsistent :
    Nonempty (FrozenHistoryMarkovRealization latentVisibleHistoryProcess
      latentVisiblePlant) ∧
    Nonempty (FrozenHistoryPrefixConsistency
      latentVisibleHistoryRealization) ∧
    ¬ HistoryEncoderKernelConsistent latentVisibleHistoryAbstraction
      latentVisibleHistoryProcess := by
  refine ⟨⟨latentVisibleHistoryRealization⟩,
    ⟨latentVisibleHistoryPrefixConsistency⟩, ?_⟩
  intro consistent
  have equalLaw := consistent false true
    latentVisibleHistories_are_encoderAligned
  have atFalse := congrFun equalLaw false
  norm_num [transportedFineHistoryStateLaw, transportedFineHistoryJointLaw,
    latentVisibleHistoryProcess, latentVisibleAbstraction, latentVisiblePlant,
    jointOutcomeMap, pushforwardFiniteProbability, finiteDirac,
    Fintype.sum_prod_type, Fintype.sum_bool] at atFalse

/-! State prediction and emitted-boundary exactness are independent coordinates. -/

def unitTrueBoundaryProcess :
    FiniteJointOpenProcess Unit Unit Unit Unit Bool where
  mass _ _ := (finiteDirac ((), true)).mass
  nonnegative _ _ := (finiteDirac ((), true)).nonnegative
  normalized _ _ := (finiteDirac ((), true)).normalized

def boundaryMismatchAbstraction :
    FiniteJointContextualAbstraction Unit Unit Unit Unit Bool
      Unit Unit Unit Unit Bool where
  fine := unitTrueBoundaryProcess
  abstract := unitFalseBoundaryProcess
  stateMap := id
  contextMap := id
  boundaryInMap := id
  actionMap := id
  boundaryOutMap := id

def boundaryMismatchHistorySupport :
    FrozenOperationalHistorySupport Unit Unit Unit Unit Unit where
  observations _ := [()]
  controls _ := []
  currentContext _ := ()
  currentBoundaryIn _ := ()
  currentAction _ := ()
  observations_nonempty _ := by simp
  history_shape _ := by simp

def boundaryMismatchHistoryProcess :
    FiniteHistoryJointOpenProcess Unit Unit Unit Unit Unit Unit Bool where
  support := boundaryMismatchHistorySupport
  nextLaw _ := finiteDirac ((), true)

def boundaryMismatchHistoryAbstraction :
    OperationalHistoryAbstraction
      (Observation := Unit) boundaryMismatchAbstraction where
  observeState _ := ()
  qChi _ _ _ := ()
  singleton_compatibility _ _ := rfl

/-- Exact next-state prediction does not force exact boundary-output prediction. -/
theorem statePredictionExact_boundaryOutputNotExact :
    FiniteLawFamilyExact
        (transportedFineHistoryStateLaw boundaryMismatchAbstraction
          boundaryMismatchHistoryProcess)
        (abstractHistoryStateLaw boundaryMismatchAbstraction
          boundaryMismatchHistoryAbstraction boundaryMismatchHistoryProcess) ∧
    ¬ FiniteLawFamilyExact
        (transportedFineHistoryBoundaryLaw boundaryMismatchAbstraction
          boundaryMismatchHistoryProcess)
        (abstractHistoryBoundaryLaw boundaryMismatchAbstraction
          boundaryMismatchHistoryAbstraction boundaryMismatchHistoryProcess) := by
  constructor
  · intro index
    cases index
    funext state
    cases state
    norm_num [transportedFineHistoryStateLaw, transportedFineHistoryJointLaw,
      abstractHistoryStateLaw, abstractHistoryJointLaw,
      boundaryMismatchAbstraction, boundaryMismatchHistoryProcess,
      boundaryMismatchHistorySupport, boundaryMismatchHistoryAbstraction,
      unitTrueBoundaryProcess, unitFalseBoundaryProcess,
      jointStepProbability, jointOutcomeMap, pushforwardFiniteProbability,
      finiteDirac]
  · intro boundaryExact
    have atFalse := congrFun (boundaryExact ()) false
    norm_num [transportedFineHistoryBoundaryLaw,
      transportedFineHistoryJointLaw, abstractHistoryBoundaryLaw,
      abstractHistoryJointLaw, boundaryMismatchAbstraction,
      boundaryMismatchHistoryProcess, boundaryMismatchHistorySupport,
      boundaryMismatchHistoryAbstraction, unitTrueBoundaryProcess,
      unitFalseBoundaryProcess, jointStepProbability, jointOutcomeMap,
      pushforwardFiniteProbability, finiteDirac, Fintype.sum_prod_type,
      Fintype.sum_bool] at atFalse

/-- Existing equal-marginal fixture is a state/output correlation no-go. -/
theorem jointStateBoundaryLaw_not_determined_by_separateMarginals :
    (∀ state : Bool,
      ∑ output : Bool, correlatedPairMass (state, output) =
        ∑ output : Bool, anticorrelatedPairMass (state, output)) ∧
    (∀ output : Bool,
      ∑ state : Bool, correlatedPairMass (state, output) =
        ∑ state : Bool, anticorrelatedPairMass (state, output)) ∧
    finiteTotalVariation correlatedPairProbability anticorrelatedPairProbability = 1 :=
  correlatedParallel_equalMarginals_but_jointTVOne

end OCMaturityCompletionCycle
