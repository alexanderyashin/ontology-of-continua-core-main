import OCMaturityCompletionCycle.OperationalHistoryAbstraction
import OCMaturityCompletionCycle.QuantitativeComposition

/-!
# Process-level finite total-variation bounds

These bounds are stated on actual normalized finite kernels and their induced
evolution operators.  Scalar bookkeeping lemmas are used only after the
process-level inequalities have been established.
-/

namespace OCMaturityCompletionCycle

universe uState uAction uMemory uContext uBoundary uAbstractState
  uAbstractContext uAbstractBoundary uAbstractAction uBoundaryOut
  uAbstractBoundaryOut

/-- One normalized row of a finite controlled kernel. -/
def kernelRowProbability
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (state : State)
    (action : Action) : FiniteProbabilityMass State where
  mass := kernel.mass state action
  nonnegative := kernel.nonnegative state action
  normalized := kernel.normalized state action

/-- Uniform same-input row error for one pair of finite kernels. -/
def KernelUniformRowTVBound
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (first second : FiniteControlledKernel State Action)
    (action : Action)
    (epsilon : ℚ) : Prop :=
  ∀ state,
    finiteTotalVariation
      (kernelRowProbability first state action)
      (kernelRowProbability second state action) ≤ epsilon

/-- Every normalized finite probability pair has total variation at most one. -/
theorem finiteTotalVariation_le_one
    {State : Type uState}
    [Fintype State]
    (left right : FiniteProbabilityMass State) :
    finiteTotalVariation left right ≤ 1 := by
  simp only [finiteTotalVariation]
  apply (div_le_iff₀ (by norm_num : (0 : ℚ) < 2)).2
  calc
    (∑ state, |left.mass state - right.mass state|) ≤
        ∑ state, (left.mass state + right.mass state) := by
      apply Finset.sum_le_sum
      intro state _
      simpa [abs_of_nonneg (left.nonnegative state),
        abs_of_nonneg (right.nonnegative state)] using
        (abs_sub_le (left.mass state) 0 (right.mass state))
    _ = 2 := by
      rw [Finset.sum_add_distrib, left.normalized, right.normalized]
      norm_num
    _ = 1 * 2 := by norm_num

/--
A uniform row-TV bound controls the mixture error for every normalized input
law.  This is the process lemma needed by sequential telescoping.
-/
theorem evolve_same_initial_le_uniformRowTV
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (first second : FiniteControlledKernel State Action)
    (action : Action)
    (initial : FiniteProbabilityMass State)
    (epsilon : ℚ)
    (epsilonNonnegative : 0 ≤ epsilon)
    (uniform : KernelUniformRowTVBound first second action epsilon) :
    finiteTotalVariation
      (evolveFiniteProbability first action initial)
      (evolveFiniteProbability second action initial) ≤ epsilon := by
  simp only [finiteTotalVariation, evolveFiniteProbability]
  apply (div_le_iff₀ (by norm_num : (0 : ℚ) < 2)).2
  calc
    (∑ target : State,
      |(∑ source : State, initial.mass source * first.mass source action target) -
        ∑ source : State, initial.mass source * second.mass source action target|) =
        ∑ target : State,
          |∑ source : State,
            initial.mass source *
              (first.mass source action target - second.mass source action target)| := by
      apply Finset.sum_congr rfl
      intro target _
      congr 1
      rw [← Finset.sum_sub_distrib]
      apply Finset.sum_congr rfl
      intro source _
      ring
    _ ≤ ∑ target : State,
        ∑ source : State,
          |initial.mass source *
            (first.mass source action target - second.mass source action target)| := by
      exact Finset.sum_le_sum fun target _ => Finset.abs_sum_le_sum_abs _ _
    _ = ∑ source : State,
        initial.mass source *
          ∑ target : State,
            |first.mass source action target - second.mass source action target| := by
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro source _
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro target _
      rw [abs_mul, abs_of_nonneg (initial.nonnegative source)]
    _ ≤ ∑ source : State, initial.mass source * (epsilon * 2) := by
      apply Finset.sum_le_sum
      intro source _
      apply mul_le_mul_of_nonneg_left _ (initial.nonnegative source)
      have rowBound := uniform source
      have scaled :=
        (div_le_iff₀ (by norm_num : (0 : ℚ) < 2)).1 rowBound
      simpa [finiteTotalVariation, kernelRowProbability] using scaled
    _ = epsilon * 2 := by
      rw [← Finset.sum_mul, initial.normalized]
      simp

/-- Inhomogeneous left-to-right evolution through a kernel/action schedule. -/
def evolveMany
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (kernels : Nat → FiniteControlledKernel State Action)
    (actions : Nat → Action) : Nat →
      FiniteProbabilityMass State → FiniteProbabilityMass State
  | 0, initial => initial
  | horizon + 1, initial =>
      evolveFiniteProbability (kernels horizon) (actions horizon)
        (evolveMany kernels actions horizon initial)

/--
Actual finite-TV telescoping for two inhomogeneous kernel schedules.  Every
local term is a uniform row error at the corresponding process step.
-/
theorem evolveMany_tv_le_initial_add_sum_rowError
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (first second : Nat → FiniteControlledKernel State Action)
    (actions : Nat → Action)
    (leftInitial rightInitial : FiniteProbabilityMass State)
    (rowError : Nat → ℚ)
    (rowErrorNonnegative : ∀ step, 0 ≤ rowError step)
    (uniform : ∀ step,
      KernelUniformRowTVBound (first step) (second step)
        (actions step) (rowError step)) :
    ∀ horizon,
      finiteTotalVariation
        (evolveMany first actions horizon leftInitial)
        (evolveMany second actions horizon rightInitial) ≤
      finiteTotalVariation leftInitial rightInitial +
        ∑ step ∈ Finset.range horizon, rowError step := by
  intro horizon
  induction horizon with
  | zero => simp [evolveMany]
  | succ prior inductionHypothesis =>
      have mixtureBound :
          finiteTotalVariation
            (evolveFiniteProbability (first prior) (actions prior)
              (evolveMany second actions prior rightInitial))
            (evolveFiniteProbability (second prior) (actions prior)
              (evolveMany second actions prior rightInitial)) ≤ rowError prior :=
        evolve_same_initial_le_uniformRowTV
          (first prior) (second prior) (actions prior)
          (evolveMany second actions prior rightInitial) (rowError prior)
          (rowErrorNonnegative prior) (uniform prior)
      calc
        finiteTotalVariation
            (evolveMany first actions (prior + 1) leftInitial)
            (evolveMany second actions (prior + 1) rightInitial) ≤
          finiteTotalVariation
              (evolveMany first actions prior leftInitial)
              (evolveMany second actions prior rightInitial) + rowError prior := by
            exact sequentialKernelPerturbation_le_previous_add_rowBound
              (first prior) (second prior) (actions prior)
              (evolveMany first actions prior leftInitial)
              (evolveMany second actions prior rightInitial)
              (rowError prior) mixtureBound
        _ ≤ (finiteTotalVariation leftInitial rightInitial +
              ∑ step ∈ Finset.range prior, rowError step) + rowError prior :=
          by
            simpa [add_comm] using
              (add_le_add_right inductionHypothesis (rowError prior))
        _ = finiteTotalVariation leftInitial rightInitial +
              ∑ step ∈ Finset.range (prior + 1), rowError step := by
          rw [Finset.sum_range_succ]
          ring

/-- Probability clipping gives the exact `min 1` process bound. -/
theorem evolveMany_tv_le_min_one_initial_add_sum_rowError
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (first second : Nat → FiniteControlledKernel State Action)
    (actions : Nat → Action)
    (leftInitial rightInitial : FiniteProbabilityMass State)
    (rowError : Nat → ℚ)
    (rowErrorNonnegative : ∀ step, 0 ≤ rowError step)
    (uniform : ∀ step,
      KernelUniformRowTVBound (first step) (second step)
        (actions step) (rowError step))
    (horizon : Nat) :
    finiteTotalVariation
        (evolveMany first actions horizon leftInitial)
        (evolveMany second actions horizon rightInitial) ≤
      min 1 (finiteTotalVariation leftInitial rightInitial +
        ∑ step ∈ Finset.range horizon, rowError step) := by
  apply le_min
  · exact finiteTotalVariation_le_one _ _
  · exact evolveMany_tv_le_initial_add_sum_rowError first second actions
      leftInitial rightInitial rowError rowErrorNonnegative uniform horizon

/-- Uniform `epsilon` specialization of the inhomogeneous process bound. -/
theorem evolveMany_tv_le_min_one_initial_add_horizon_mul
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (first second : Nat → FiniteControlledKernel State Action)
    (actions : Nat → Action)
    (leftInitial rightInitial : FiniteProbabilityMass State)
    (epsilon : ℚ)
    (epsilonNonnegative : 0 ≤ epsilon)
    (uniform : ∀ step,
      KernelUniformRowTVBound (first step) (second step)
        (actions step) epsilon)
    (horizon : Nat) :
    finiteTotalVariation
        (evolveMany first actions horizon leftInitial)
        (evolveMany second actions horizon rightInitial) ≤
      min 1 (finiteTotalVariation leftInitial rightInitial +
        (horizon : ℚ) * epsilon) := by
  simpa using
    (evolveMany_tv_le_min_one_initial_add_sum_rowError first second actions
      leftInitial rightInitial (fun _ => epsilon) (fun _ => epsilonNonnegative)
      uniform horizon)

/-- Close a controlled plant with an explicit current-state policy. -/
def closeStateFeedbackKernel
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (plant : FiniteControlledKernel State Action)
    (policy : State → Action) : FiniteControlledKernel State Unit where
  mass state _ target := plant.mass state (policy state) target
  nonnegative state _ target := plant.nonnegative state (policy state) target
  normalized state _ := plant.normalized state (policy state)

/--
Finite memory summary used by a history-dependent controller.  The update law
must expose the sampled plant state as the next current state; the represented
history may be compressed and is not claimed to be the unbounded raw history.
-/
structure FiniteHistoryFeedbackMachine
    (Memory : Type uMemory)
    (State : Type uState)
    (Action : Type uAction)
    [Fintype Memory]
    [Fintype State] where
  representedHistory : Memory → List State
  currentState : Memory → State
  current_agrees : ∀ memory,
    (representedHistory memory).getLast? = some (currentState memory)
  update : Memory → State → Memory
  update_current : ∀ memory nextState,
    currentState (update memory nextState) = nextState
  policy : Memory → Action

/-- One normalized memory-state row of the history-dependent closed loop. -/
def historyFeedbackRowProbability
    {Memory : Type uMemory}
    {State : Type uState}
    {Action : Type uAction}
    [Fintype Memory]
    [DecidableEq Memory]
    [Fintype State]
    (plant : FiniteControlledKernel State Action)
    (machine : FiniteHistoryFeedbackMachine Memory State Action)
    (memory : Memory) : FiniteProbabilityMass Memory :=
  pushforwardFiniteProbability (machine.update memory)
    (kernelRowProbability plant (machine.currentState memory)
      (machine.policy memory))

/-- Closed-loop kernel on the explicit finite history/memory state. -/
def closeHistoryFeedbackKernel
    {Memory : Type uMemory}
    {State : Type uState}
    {Action : Type uAction}
    [Fintype Memory]
    [DecidableEq Memory]
    [Fintype State]
    (plant : FiniteControlledKernel State Action)
    (machine : FiniteHistoryFeedbackMachine Memory State Action) :
    FiniteControlledKernel Memory Unit where
  mass memory _ target :=
    (historyFeedbackRowProbability plant machine memory).mass target
  nonnegative memory _ target :=
    (historyFeedbackRowProbability plant machine memory).nonnegative target
  normalized memory _ :=
    (historyFeedbackRowProbability plant machine memory).normalized

/-- Finite-horizon evolution of an explicit history-dependent feedback loop. -/
def evolveHistoryFeedback
    {Memory : Type uMemory}
    {State : Type uState}
    {Action : Type uAction}
    [Fintype Memory]
    [DecidableEq Memory]
    [Fintype State]
    (plant : FiniteControlledKernel State Action)
    (machine : FiniteHistoryFeedbackMachine Memory State Action)
    (horizon : Nat)
    (initial : FiniteProbabilityMass Memory) : FiniteProbabilityMass Memory :=
  evolveMany (fun _ => closeHistoryFeedbackKernel plant machine)
    (fun _ => ()) horizon initial

/--
Finite-horizon perturbation bound for two plants closed by the same explicit
history-dependent feedback machine.
-/
theorem evolveHistoryFeedback_tv_le_min_one_initial_add_horizon_mul
    {Memory : Type uMemory}
    {State : Type uState}
    {Action : Type uAction}
    [Fintype Memory]
    [DecidableEq Memory]
    [Fintype State]
    (first second : FiniteControlledKernel State Action)
    (machine : FiniteHistoryFeedbackMachine Memory State Action)
    (leftInitial rightInitial : FiniteProbabilityMass Memory)
    (epsilon : ℚ)
    (epsilonNonnegative : 0 ≤ epsilon)
    (uniform : ∀ memory,
      finiteTotalVariation
          (historyFeedbackRowProbability first machine memory)
          (historyFeedbackRowProbability second machine memory) ≤ epsilon)
    (horizon : Nat) :
    finiteTotalVariation
        (evolveHistoryFeedback first machine horizon leftInitial)
        (evolveHistoryFeedback second machine horizon rightInitial) ≤
      min 1 (finiteTotalVariation leftInitial rightInitial +
        (horizon : ℚ) * epsilon) := by
  exact evolveMany_tv_le_min_one_initial_add_horizon_mul
    (fun _ => closeHistoryFeedbackKernel first machine)
    (fun _ => closeHistoryFeedbackKernel second machine)
    (fun _ => ()) leftInitial rightInitial epsilon epsilonNonnegative
    (fun _ memory => by
      simpa [KernelUniformRowTVBound, kernelRowProbability,
        closeHistoryFeedbackKernel] using uniform memory)
    horizon

/-- Actual contraction predicate for one normalized finite evolution operator. -/
def FiniteEvolutionContraction
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (action : Action)
    (alpha : ℚ) : Prop :=
  ∀ left right,
    finiteTotalVariation
      (evolveFiniteProbability kernel action left)
      (evolveFiniteProbability kernel action right) ≤
    alpha * finiteTotalVariation left right

/--
An approximate fixed point is within `epsilon / (1 - alpha)` of an exact fixed
point under an actual strict TV contraction.
-/
theorem approximateFixedPoint_tv_le_residual_div_one_sub_contraction
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (action : Action)
    (approximate fixed : FiniteProbabilityMass State)
    (epsilon alpha : ℚ)
    (alphaBelowOne : alpha < 1)
    (contraction : FiniteEvolutionContraction kernel action alpha)
    (fixedPoint : evolveFiniteProbability kernel action fixed = fixed)
    (residual :
      finiteTotalVariation approximate
        (evolveFiniteProbability kernel action approximate) ≤ epsilon) :
    finiteTotalVariation approximate fixed ≤ epsilon / (1 - alpha) := by
  apply recurrentFeedbackError_le_geometricScale _ epsilon alpha alphaBelowOne
  calc
    finiteTotalVariation approximate fixed ≤
        finiteTotalVariation approximate
            (evolveFiniteProbability kernel action approximate) +
          finiteTotalVariation
            (evolveFiniteProbability kernel action approximate) fixed :=
      finiteTotalVariation_triangle _ _ _
    _ = finiteTotalVariation approximate
            (evolveFiniteProbability kernel action approximate) +
          finiteTotalVariation
            (evolveFiniteProbability kernel action approximate)
            (evolveFiniteProbability kernel action fixed) := by
      rw [fixedPoint]
    _ ≤ epsilon + alpha * finiteTotalVariation approximate fixed :=
      add_le_add residual (contraction approximate fixed)
    _ = alpha * finiteTotalVariation approximate fixed + epsilon := by ring

/-- State transport of an actual contextual abstraction is nonexpansive. -/
theorem contextualAbstraction_stateTransport_nonexpansive
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    [Fintype State]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (abstraction : ContextualAbstraction State Context Boundary Action
      AbstractState AbstractContext AbstractBoundary AbstractAction)
    (left right : FiniteProbabilityMass State) :
    finiteTotalVariation
        (pushforwardFiniteProbability abstraction.stateMap left)
        (pushforwardFiniteProbability abstraction.stateMap right) ≤
      finiteTotalVariation left right :=
  pushforwardFiniteProbability_nonexpansive abstraction.stateMap left right

/-- Joint state/output transport of an actual open abstraction is nonexpansive. -/
theorem jointOpenAbstraction_outcomeTransport_nonexpansive
    {State : Type uState}
    {Context : Type uContext}
    {Boundary : Type uBoundary}
    {Action : Type uAction}
    {BoundaryOut : Type uBoundaryOut}
    {AbstractState : Type uAbstractState}
    {AbstractContext : Type uAbstractContext}
    {AbstractBoundary : Type uAbstractBoundary}
    {AbstractAction : Type uAbstractAction}
    {AbstractBoundaryOut : Type uAbstractBoundaryOut}
    [Fintype State]
    [Fintype BoundaryOut]
    [Fintype AbstractState]
    [Fintype AbstractBoundaryOut]
    [DecidableEq AbstractState]
    [DecidableEq AbstractBoundaryOut]
    (abstraction : FiniteJointContextualAbstraction State Context Boundary Action
      BoundaryOut AbstractState AbstractContext AbstractBoundary AbstractAction
      AbstractBoundaryOut)
    (left right : FiniteProbabilityMass (State × BoundaryOut)) :
    finiteTotalVariation
        (pushforwardFiniteProbability
          (jointOutcomeMap abstraction.stateMap abstraction.boundaryOutMap) left)
        (pushforwardFiniteProbability
          (jointOutcomeMap abstraction.stateMap abstraction.boundaryOutMap) right) ≤
      finiteTotalVariation left right :=
  pushforwardFiniteProbability_nonexpansive
    (jointOutcomeMap abstraction.stateMap abstraction.boundaryOutMap) left right

end OCMaturityCompletionCycle
