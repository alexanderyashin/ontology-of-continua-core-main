import OCMaturityCompletionCycle.ProcessTVBounds

/-!
# Capability profiles derived from semantic witnesses

`DynamicsCapabilityProfile.supports` is only a lattice carrier.  A capability
is counted here only when the model supplies the corresponding operational
witness; assigning a profile label is never sufficient.
-/

namespace OCMaturityCompletionCycle

universe uState uAction uContext uBoundaryIn uBoundaryOut uMemory uObservation

/-- Every controlled row is a point mass at a unique outcome. -/
def FiniteKernelDeterministic
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action) : Prop :=
  ∀ state action, ∃! target, kernel.mass state action target = 1

/-- Some controlled row gives positive mass to two distinct outcomes. -/
def FiniteKernelGenuinelyStochastic
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action) : Prop :=
  ∃ state action left right,
    left ≠ right ∧
    0 < kernel.mass state action left ∧
    0 < kernel.mass state action right

/-- Randomness evidence is indexed by the declared mode. -/
def FiniteKernelRandomnessEvidence
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action) :
    RandomnessCapability → Prop
  | .deterministic => FiniteKernelDeterministic kernel
  | .stochastic => FiniteKernelGenuinelyStochastic kernel

/-- Joint open row is deterministic exactly when it has one mass-one outcome. -/
def JointOpenProcessDeterministic
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut) :
    Prop :=
  ∀ state control, ∃! outcome, process.mass state control outcome = 1

/-- Some open-process row has two positive, distinct joint outcomes. -/
def JointOpenProcessGenuinelyStochastic
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut) :
    Prop :=
  ∃ state control left right,
    left ≠ right ∧
    0 < process.mass state control left ∧
    0 < process.mass state control right

/-- Randomness evidence for a joint open process. -/
def JointOpenRandomnessEvidence
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut) :
    RandomnessCapability → Prop
  | .deterministic => JointOpenProcessDeterministic process
  | .stochastic => JointOpenProcessGenuinelyStochastic process

/-- A declared action intervention changes at least one joint transition row. -/
def JointOpenActionEffect
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut) :
    Prop :=
  ∃ state context boundary leftAction rightAction outcome,
    leftAction ≠ rightAction ∧
      process.mass state (context, boundary, leftAction) outcome ≠
        process.mass state (context, boundary, rightAction) outcome

/-- Passive is explicit; controlled requires a real action-sensitive row. -/
def JointOpenControlEvidence
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut) :
    ControlCapability → Prop
  | .passive => True
  | .controlled => JointOpenActionEffect process

/-- Full observation means exact state recovery by injectivity. -/
structure FullObservationWitness
    (State : Type uState)
    (Observation : Type uObservation) where
  observe : State → Observation
  injective : Function.Injective observe

/-- Partial observation has an explicit pair of hidden-distinct states. -/
structure PartialObservationWitness
    (State : Type uState)
    (Observation : Type uObservation) where
  observe : State → Observation
  left : State
  right : State
  states_differ : left ≠ right
  observations_equal : observe left = observe right

/-- Profile inferred from injective observation evidence. -/
def FullObservationWitness.profile
    {State : Type uState}
    {Observation : Type uObservation}
    (_ : FullObservationWitness State Observation) : DynamicsCapabilityProfile :=
  singletonCapabilityProfile (.observation .fullObservation)

/-- Profile inferred from an explicit observation collision. -/
def PartialObservationWitness.profile
    {State : Type uState}
    {Observation : Type uObservation}
    (_ : PartialObservationWitness State Observation) : DynamicsCapabilityProfile :=
  singletonCapabilityProfile (.observation .partialObservation)

theorem fullObservationWitness_supports_fullObservation
    {State : Type uState}
    {Observation : Type uObservation}
    (witness : FullObservationWitness State Observation) :
    witness.profile.supports (.observation .fullObservation) := rfl

theorem partialObservationWitness_supports_partialObservation
    {State : Type uState}
    {Observation : Type uObservation}
    (witness : PartialObservationWitness State Observation) :
    witness.profile.supports (.observation .partialObservation) := rfl

/--
Open-boundary evidence requires both an input intervention that changes the
joint law and an emitted boundary coordinate with two possible values.
-/
structure JointOpenBoundarySemantics
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut) where
  input_changes_joint_law : ∃ state context leftInput rightInput action outcome,
    leftInput ≠ rightInput ∧
      process.mass state (context, leftInput, action) outcome ≠
        process.mass state (context, rightInput, action) outcome
  context_changes_joint_law : ∃ state leftContext rightContext boundary action outcome,
    leftContext ≠ rightContext ∧
      process.mass state (leftContext, boundary, action) outcome ≠
        process.mass state (rightContext, boundary, action) outcome
  output_is_nontrivial : ∃ leftState leftControl leftOutcome
      rightState rightControl rightOutcome,
    leftOutcome.2 ≠ rightOutcome.2 ∧
      0 < process.mass leftState leftControl leftOutcome ∧
      0 < process.mass rightState rightControl rightOutcome

/-- A feedback policy genuinely uses history beyond the current state. -/
def HistoryFeedbackPolicyUsesPast
    {Memory : Type uMemory}
    {State : Type uState}
    {Action : Type uAction}
    [Fintype Memory]
    [Fintype State]
    (machine : FiniteHistoryFeedbackMachine Memory State Action) : Prop :=
  ∃ left right,
    machine.currentState left = machine.currentState right ∧
    machine.representedHistory left ≠ machine.representedHistory right ∧
    machine.policy left ≠ machine.policy right

/-- Verified finite controlled state path with semantic randomness evidence. -/
structure VerifiedFiniteControlledStatePath
    (State : Type uState)
    (Action : Type uAction)
    [Fintype State] where
  kernel : FiniteControlledKernel State Action
  horizon : Nat
  initial : FiniteProbabilityMass State
  schedule : Nat → Action
  horizon_positive : 0 < horizon
  actionEffect : ∃ state leftAction rightAction target,
    leftAction ≠ rightAction ∧
      kernel.mass state leftAction target ≠ kernel.mass state rightAction target
  randomnessMode : RandomnessCapability
  randomnessEvidence : FiniteKernelRandomnessEvidence kernel randomnessMode

/-- Profile inferred from a normalized finite controlled-state witness. -/
def VerifiedFiniteControlledStatePath.profile
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (witness : VerifiedFiniteControlledStatePath State Action) :
    DynamicsCapabilityProfile where
  supports capability :=
    capability = .control .controlled ∨
    capability = .randomness witness.randomnessMode ∨
    capability = .memory .memoryless ∨
    capability = .approximation .exact ∨
    capability = .composition .sequential

theorem verifiedFiniteControlledStatePath_supports_witnessed_interfaces
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (witness : VerifiedFiniteControlledStatePath State Action) :
    witness.profile.supports (.control .controlled) ∧
    witness.profile.supports (.randomness witness.randomnessMode) ∧
    witness.profile.supports (.memory .memoryless) ∧
    witness.profile.supports (.approximation .exact) ∧
    witness.profile.supports (.composition .sequential) := by
  simp [VerifiedFiniteControlledStatePath.profile]

/-- Verified normalized joint boundary-output process. -/
structure VerifiedJointOpenBoundaryOutput
    (State : Type uState)
    (Context : Type uContext)
    (BoundaryIn : Type uBoundaryIn)
    (Action : Type uAction)
    (BoundaryOut : Type uBoundaryOut)
    [Fintype State]
    [Fintype BoundaryOut] where
  process : FiniteJointOpenProcess State Context BoundaryIn Action BoundaryOut
  controlMode : ControlCapability
  controlEvidence : JointOpenControlEvidence process controlMode
  randomnessMode : RandomnessCapability
  randomnessEvidence : JointOpenRandomnessEvidence process randomnessMode
  boundarySemantics : JointOpenBoundarySemantics process

/-- Profile inferred from the witnessed open interface. -/
def VerifiedJointOpenBoundaryOutput.profile
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (witness : VerifiedJointOpenBoundaryOutput State Context BoundaryIn Action
      BoundaryOut) : DynamicsCapabilityProfile where
  supports capability :=
    capability = .control witness.controlMode ∨
    capability = .randomness witness.randomnessMode ∨
    capability = .openness .openBoundary ∨
    capability = .context .indexed ∨
    capability = .approximation .exact ∨
    capability = .composition .sequential

theorem verifiedJointOpenBoundaryOutput_supports_witnessed_interfaces
    {State : Type uState}
    {Context : Type uContext}
    {BoundaryIn : Type uBoundaryIn}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    (witness : VerifiedJointOpenBoundaryOutput State Context BoundaryIn Action
      BoundaryOut) :
    witness.profile.supports (.control witness.controlMode) ∧
    witness.profile.supports (.randomness witness.randomnessMode) ∧
    witness.profile.supports (.openness .openBoundary) ∧
    witness.profile.supports (.context .indexed) ∧
    witness.profile.supports (.approximation .exact) ∧
    witness.profile.supports (.composition .sequential) := by
  simp [VerifiedJointOpenBoundaryOutput.profile]

/--
Verified history feedback requires actual use of the past and an actual strict
contraction theorem for the induced closed-loop evolution.
-/
structure VerifiedHistoryFeedback
    (Memory : Type uMemory)
    (State : Type uState)
    (Action : Type uAction)
    [Fintype Memory]
    [DecidableEq Memory]
    [Fintype State] where
  plant : FiniteControlledKernel State Action
  machine : FiniteHistoryFeedbackMachine Memory State Action
  initial : FiniteProbabilityMass Memory
  witnessLeft : Memory
  witnessRight : Memory
  witnesses_same_current :
    machine.currentState witnessLeft = machine.currentState witnessRight
  witnesses_distinct_histories :
    machine.representedHistory witnessLeft ≠ machine.representedHistory witnessRight
  witnesses_distinct_actions : machine.policy witnessLeft ≠ machine.policy witnessRight
  witnessLeft_reachable : 0 < initial.mass witnessLeft
  witnessRight_reachable : 0 < initial.mass witnessRight
  action_changes_plant_row : ∃ target,
    plant.mass (machine.currentState witnessLeft) (machine.policy witnessLeft) target ≠
      plant.mass (machine.currentState witnessRight) (machine.policy witnessRight) target
  feedbackMemory : Memory
  feedbackMemory_reachable : 0 < initial.mass feedbackMemory
  feedbackNextLeft : State
  feedbackNextRight : State
  feedback_next_states_differ : feedbackNextLeft ≠ feedbackNextRight
  feedbackNextLeft_positive :
    0 < plant.mass (machine.currentState feedbackMemory)
      (machine.policy feedbackMemory) feedbackNextLeft
  feedbackNextRight_positive :
    0 < plant.mass (machine.currentState feedbackMemory)
      (machine.policy feedbackMemory) feedbackNextRight
  sampled_state_changes_future_action :
    machine.policy (machine.update feedbackMemory feedbackNextLeft) ≠
      machine.policy (machine.update feedbackMemory feedbackNextRight)
  randomnessMode : RandomnessCapability
  randomnessEvidence : FiniteKernelRandomnessEvidence
    (closeHistoryFeedbackKernel plant machine) randomnessMode
  contractionCoefficient : ℚ
  coefficient_nonnegative : 0 ≤ contractionCoefficient
  coefficient_below_one : contractionCoefficient < 1
  contraction : FiniteEvolutionContraction
    (closeHistoryFeedbackKernel plant machine) () contractionCoefficient

/-- Profile inferred from the explicit feedback/contraction witness. -/
def VerifiedHistoryFeedback.profile
    {Memory : Type uMemory}
    {State : Type uState}
    {Action : Type uAction}
    [Fintype Memory]
    [DecidableEq Memory]
    [Fintype State]
    (witness : VerifiedHistoryFeedback Memory State Action) :
    DynamicsCapabilityProfile where
  supports capability :=
    capability = .control .controlled ∨
    capability = .randomness witness.randomnessMode ∨
    capability = .openness .feedback ∨
    capability = .approximation .exact ∨
    capability = .composition .feedback

theorem verifiedHistoryFeedback_supports_witnessed_interfaces
    {Memory : Type uMemory}
    {State : Type uState}
    {Action : Type uAction}
    [Fintype Memory]
    [DecidableEq Memory]
    [Fintype State]
    (witness : VerifiedHistoryFeedback Memory State Action) :
    witness.profile.supports (.control .controlled) ∧
    witness.profile.supports (.randomness witness.randomnessMode) ∧
    witness.profile.supports (.openness .feedback) ∧
    witness.profile.supports (.approximation .exact) ∧
    witness.profile.supports (.composition .feedback) := by
  simp [VerifiedHistoryFeedback.profile]

/-- Prefix/path evidence is intentionally required before adding history dependence. -/
theorem verifiedHistoryFeedback_baseProfile_omits_historyDependent
    {Memory : Type uMemory}
    {State : Type uState}
    {Action : Type uAction}
    [Fintype Memory]
    [DecidableEq Memory]
    [Fintype State]
    (witness : VerifiedHistoryFeedback Memory State Action) :
    ¬ witness.profile.supports (.memory .historyDependent) := by
  simp [VerifiedHistoryFeedback.profile]

/-- A profile label without a semantic witness. -/
def selfDeclaredOpenProfile : DynamicsCapabilityProfile :=
  singletonCapabilityProfile (.openness .openBoundary)

theorem selfDeclaredOpenProfile_claims_openBoundary :
    selfDeclaredOpenProfile.supports (.openness .openBoundary) := rfl

/-- No normalized joint process can emit into an empty output type. -/
theorem noFiniteJointOpenProcess_with_emptyBoundaryOutput :
    IsEmpty (FiniteJointOpenProcess Unit Unit Unit Unit Empty) := by
  refine ⟨?_⟩
  intro process
  have normalized := process.normalized () ((), (), ())
  simpa using normalized

/-- A declared label cannot manufacture the required normalized interface. -/
theorem declaredCapability_does_not_supply_verifiedJointOpenWitness :
    selfDeclaredOpenProfile.supports (.openness .openBoundary) ∧
      IsEmpty (FiniteJointOpenProcess Unit Unit Unit Unit Empty) :=
  ⟨selfDeclaredOpenProfile_claims_openBoundary,
    noFiniteJointOpenProcess_with_emptyBoundaryOutput⟩

end OCMaturityCompletionCycle
