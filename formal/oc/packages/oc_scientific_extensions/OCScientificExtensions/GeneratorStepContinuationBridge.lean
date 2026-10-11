import OCKIndividuationMSpaceComposition.ContinuationAwarePredictiveKernel

namespace OCScientificExtensions.GeneratorStepContinuationBridge

open OCKIndividuationMSpaceComposition
open OCMaturityCompletionCycle
open scoped BigOperators

universe uGenerator uCoordinate uInvariant
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame

variable {Generator : Type uGenerator} [Fintype Generator]
variable {Coordinate : Type uCoordinate} [Fintype Coordinate]
variable {Invariant : Type uInvariant} [Fintype Invariant]

/-- Exactly the five local head obligations, without a tail or an initial-state test. -/
def GeneratorStepAdmissible
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool)
    (state : Coordinate → Int) (generator : Generator) : Prop :=
  system.enabled generator = true ∧
  dynamicEnabled state generator = true ∧
  (∀ coordinate, system.lowerBound coordinate ≤
    generatorSingleStep system state generator coordinate) ∧
  (∀ coordinate, generatorSingleStep system state generator coordinate ≤
    system.upperBound coordinate) ∧
  (∀ invariant, (∑ coordinate, system.invariantCoefficient invariant coordinate *
    generatorSingleStep system state generator coordinate) = system.invariantTarget invariant)

theorem generator_order_cons_iff
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool)
    (state : Coordinate → Int) (generator : Generator) (remaining : List Generator) :
    GeneratorOrderAdmissible system dynamicEnabled state (generator :: remaining) ↔
      GeneratorStepAdmissible system dynamicEnabled state generator ∧
      GeneratorOrderAdmissible system dynamicEnabled
        (generatorSingleStep system state generator) remaining := by
  simp only [GeneratorOrderAdmissible, GeneratorStepAdmissible]
  tauto

/-- The executed endpoint, rather than an assumed equality to the incidence sum. -/
def runGeneratorOrder
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant) :
    (Coordinate → Int) → List Generator → (Coordinate → Int)
  | state, [] => state
  | state, generator :: remaining =>
      runGeneratorOrder system (generatorSingleStep system state generator) remaining

variable {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
variable {Task : Type uTask} {Projection : Type uProjection} {Boundary : Type uBoundary}
variable {Constraint : Type uConstraint} {Scope : Type uScope} {Frame : Type uFrame}
variable {C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame}
variable {system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant}
variable {dynamicEnabled : (Coordinate → Int) → Generator → Bool}

/-- A local typed simulation with explicit input/evidence data. No path law is a field. -/
structure StepContinuationMap
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool)
    (C : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame) where
  stateMap : (Coordinate → Int) → State
  inputMap : (Coordinate → Int) → Generator → Input
  evidenceMap : (Coordinate → Int) → Generator → Evidence
  transitionMap : ∀ state generator,
    GeneratorStepAdmissible system dynamicEnabled state generator →
    C.transition (stateMap state) (inputMap state generator)
      (stateMap (generatorSingleStep system state generator))
  admissionMap : ∀ state generator,
    GeneratorStepAdmissible system dynamicEnabled state generator →
    C.edgeAdmissible (stateMap state) (inputMap state generator)
      (stateMap (generatorSingleStep system state generator)) (evidenceMap state generator)
  sufficiencyMap : ∀ state generator,
    GeneratorStepAdmissible system dynamicEnabled state generator →
    C.evidenceSufficient (evidenceMap state generator)

def singleStepWitness (bridge : StepContinuationMap system dynamicEnabled C)
    (state : Coordinate → Int) (generator : Generator)
    (initialInvariant : C.invariant (bridge.stateMap state))
    (admissible : GeneratorStepAdmissible system dynamicEnabled state generator) :
    ContinuationWitness C (bridge.stateMap state)
      (bridge.stateMap (generatorSingleStep system state generator)) :=
  ⟨.extend .start (bridge.inputMap state generator)
      (bridge.transitionMap state generator admissible),
   .extend .start (bridge.inputMap state generator)
      (bridge.transitionMap state generator admissible) (bridge.evidenceMap state generator)
      (bridge.admissionMap state generator admissible)
      (bridge.sufficiencyMap state generator admissible), initialInvariant⟩

/-- Construct the path from local laws, deriving each intermediate invariant. -/
def orderWitness (bridge : StepContinuationMap system dynamicEnabled C) :
    (state : Coordinate → Int) → (order : List Generator) →
    C.invariant (bridge.stateMap state) →
    GeneratorOrderAdmissible system dynamicEnabled state order →
    ContinuationWitness C (bridge.stateMap state)
      (bridge.stateMap (runGeneratorOrder system state order))
  | state, [], initialInvariant, _ => .refl initialInvariant
  | state, generator :: remaining, initialInvariant, admissible =>
      let split := (generator_order_cons_iff system dynamicEnabled state generator remaining).mp admissible
      let first := singleStepWitness bridge state generator initialInvariant split.1
      first.comp (orderWitness bridge (generatorSingleStep system state generator)
        remaining first.endpointInvariant split.2)

/-- Chronological input values, including their dependence on each pre-step state. -/
def generatorInputTrace (bridge : StepContinuationMap system dynamicEnabled C) :
    (Coordinate → Int) → List Generator → List Input
  | _, [] => []
  | state, generator :: remaining =>
      bridge.inputMap state generator ::
        generatorInputTrace bridge (generatorSingleStep system state generator) remaining

/-- Chronological evidence values; the inherited witness trace reverses this list. -/
def generatorEvidenceTrace (bridge : StepContinuationMap system dynamicEnabled C) :
    (Coordinate → Int) → List Generator → List Evidence
  | _, [] => []
  | state, generator :: remaining =>
      bridge.evidenceMap state generator ::
        generatorEvidenceTrace bridge (generatorSingleStep system state generator) remaining

theorem order_witness_length (bridge : StepContinuationMap system dynamicEnabled C)
    (state : Coordinate → Int) (order : List Generator)
    (initialInvariant : C.invariant (bridge.stateMap state))
    (admissible : GeneratorOrderAdmissible system dynamicEnabled state order) :
    (orderWitness bridge state order initialInvariant admissible).history.length = order.length := by
  induction order generalizing state with
  | nil => rfl
  | cons generator remaining inductionHypothesis =>
      simp only [orderWitness, ContinuationWitness.comp, OpenHistory.length_append]
      rw [inductionHypothesis]
      simp [singleStepWitness, OpenHistory.length, Nat.add_comm]

theorem order_witness_input_trace (bridge : StepContinuationMap system dynamicEnabled C)
    (state : Coordinate → Int) (order : List Generator)
    (initialInvariant : C.invariant (bridge.stateMap state))
    (admissible : GeneratorOrderAdmissible system dynamicEnabled state order) :
    (orderWitness bridge state order initialInvariant admissible).history.inputTrace =
      (generatorInputTrace bridge state order).reverse := by
  induction order generalizing state with
  | nil => rfl
  | cons generator remaining inductionHypothesis =>
      simp only [orderWitness, ContinuationWitness.comp, OpenHistory.inputTrace_append]
      rw [inductionHypothesis]
      simp [singleStepWitness, OpenHistory.inputTrace, generatorInputTrace, List.reverse_cons]

theorem order_witness_evidence_trace (bridge : StepContinuationMap system dynamicEnabled C)
    (state : Coordinate → Int) (order : List Generator)
    (initialInvariant : C.invariant (bridge.stateMap state))
    (admissible : GeneratorOrderAdmissible system dynamicEnabled state order) :
    (orderWitness bridge state order initialInvariant admissible).evidence.evidenceTrace =
      (generatorEvidenceTrace bridge state order).reverse := by
  induction order generalizing state with
  | nil => rfl
  | cons generator remaining inductionHypothesis =>
      simp only [orderWitness, ContinuationWitness.comp, HistoryEvidence.evidenceTrace_append]
      rw [inductionHypothesis]
      simp [singleStepWitness, HistoryEvidence.evidenceTrace, generatorEvidenceTrace, List.reverse_cons]

theorem admitted_order_continues (bridge : StepContinuationMap system dynamicEnabled C)
    (state : Coordinate → Int) (order : List Generator)
    (initialInvariant : C.invariant (bridge.stateMap state))
    (admissible : GeneratorOrderAdmissible system dynamicEnabled state order) :
    Continues C (bridge.stateMap state) (bridge.stateMap (runGeneratorOrder system state order)) :=
  ⟨orderWitness bridge state order initialInvariant admissible⟩

theorem admitted_order_has_accepted_lineage (bridge : StepContinuationMap system dynamicEnabled C)
    (state : Coordinate → Int) (order : List Generator)
    (initialInvariant : C.invariant (bridge.stateMap state))
    (admissible : GeneratorOrderAdmissible system dynamicEnabled state order) :
    LineageGenerated (fun first last => ∃ input evidence,
      C.transition first input last ∧ C.edgeAdmissible first input last evidence ∧
        C.evidenceSufficient evidence)
      (bridge.stateMap state) (bridge.stateMap (runGeneratorOrder system state order)) :=
  (orderWitness bridge state order initialInvariant admissible).toLineage

section Registered

variable [DecidableEq Generator] [DecidableEq Coordinate] [DecidableEq Invariant]

/-- Models retain an actual registered admissible order as well as endpoint feasibility. -/
structure RegisteredAdmissibleOrder
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (enumeration : RegisteredGeneratorEnumeration Generator)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool) where
  incidence : Generator → Bool
  order : List Generator
  feasible : GeneratorIncidenceFeasible system incidence
  registered : order ∈ generatorIncidenceOrders enumeration incidence
  admissible : GeneratorOrderAdmissible system dynamicEnabled system.current order

theorem registered_model_inhabited_iff
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (enumeration : RegisteredGeneratorEnumeration Generator)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool) :
    Nonempty (RegisteredAdmissibleOrder system enumeration dynamicEnabled) ↔
      ∃ incidence, SequentiallyGeneratorReachable system enumeration dynamicEnabled incidence := by
  constructor
  · rintro ⟨model⟩
    exact ⟨model.incidence, model.feasible, model.order, model.registered, model.admissible⟩
  · rintro ⟨incidence, feasible, order, registered, admissible⟩
    exact ⟨⟨incidence, order, feasible, registered, admissible⟩⟩

/-- New instance: the outcome is the executed endpoint, not the aggregate state equation. -/
def sequentialPredictiveKernel
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (enumeration : RegisteredGeneratorEnumeration Generator)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool)
    (source target : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (inhabited : Nonempty (RegisteredAdmissibleOrder system enumeration dynamicEnabled)) :
    ContinuationAwarePredictiveAdmissibilityKernel where
  State := State
  Input := Input
  Evidence := Evidence
  Task := Task
  Projection := Projection
  Boundary := Boundary
  Constraint := Constraint
  Scope := Scope
  Frame := Frame
  Model := RegisteredAdmissibleOrder system enumeration dynamicEnabled
  Outcome := Coordinate → Int
  Execution := RegisteredAdmissibleOrder system enumeration dynamicEnabled
  CausalContext := Unit
  causalContextFintype := inferInstance
  sourceContext := source
  targetContext := target
  admissibleModel := fun _ => True
  predictedOutcome := fun model => runGeneratorOrder system system.current model.order
  modelExists := by rcases inhabited with ⟨model⟩; exact ⟨model, trivial⟩
  admissibleExecution := fun _ => True
  executionOutcome := fun model => runGeneratorOrder system system.current model.order

theorem sequential_kernel_possible_iff_executed_image
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (enumeration : RegisteredGeneratorEnumeration Generator)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool)
    (source target : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (inhabited : Nonempty (RegisteredAdmissibleOrder system enumeration dynamicEnabled))
    (outcome : Coordinate → Int) :
    KernelPossibleFuture (sequentialPredictiveKernel system enumeration dynamicEnabled source target inhabited) outcome ↔
      ∃ model : RegisteredAdmissibleOrder system enumeration dynamicEnabled,
        runGeneratorOrder system system.current model.order = outcome := by
  simp [KernelPossibleFuture, sequentialPredictiveKernel]

theorem sequential_kernel_possible_continues
    (bridge : StepContinuationMap system dynamicEnabled C)
    (enumeration : RegisteredGeneratorEnumeration Generator)
    (target : ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (inhabited : Nonempty (RegisteredAdmissibleOrder system enumeration dynamicEnabled))
    (initialInvariant : C.invariant (bridge.stateMap system.current))
    (outcome : Coordinate → Int)
    (possible : KernelPossibleFuture
      (sequentialPredictiveKernel system enumeration dynamicEnabled C target inhabited) outcome) :
    Continues C (bridge.stateMap system.current) (bridge.stateMap outcome) := by
  rcases (sequential_kernel_possible_iff_executed_image system enumeration dynamicEnabled C target inhabited outcome).mp possible with
    ⟨model, executed⟩
  rw [← executed]
  exact admitted_order_continues bridge system.current model.order initialInvariant model.admissible

end Registered

/-- A concrete micro-step context whose transition explicitly contains the local guards. -/
def generatorMicroContext
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool) :
    ContinuationContext (Coordinate → Int) Generator Unit Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := fun state generator next =>
    GeneratorStepAdmissible system dynamicEnabled state generator ∧
      next = generatorSingleStep system state generator
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun _ => True
  transitionPreservesInvariant := by intro _ _ _ _ _; trivial

def generatorMicroMap
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool) :
    StepContinuationMap system dynamicEnabled (generatorMicroContext system dynamicEnabled) where
  stateMap := id
  inputMap := fun _ generator => generator
  evidenceMap := fun _ _ => ()
  transitionMap := fun _ _ admissible => ⟨admissible, rfl⟩
  admissionMap := by intro _ _ _; trivial
  sufficiencyMap := by intro _ _ _; trivial

theorem wide_two_step_positive_witness :
    ∃ witness : ContinuationWitness
        (generatorMicroContext (twoGeneratorEndpointSystem (-1) 2) alwaysDynamicallyEnabled)
        (fun _ => 0)
        (runGeneratorOrder (twoGeneratorEndpointSystem (-1) 2) (fun _ => 0) [0, 1]),
      witness.history.length = 2 ∧ witness.history.inputTrace = [1, 0] ∧
      witness.evidence.evidenceTrace = [(), ()] ∧
      runGeneratorOrder (twoGeneratorEndpointSystem (-1) 2) (fun _ => 0) [0, 1] 0 = 1 := by
  let bridge := generatorMicroMap (twoGeneratorEndpointSystem (-1) 2) alwaysDynamicallyEnabled
  have admitted : GeneratorOrderAdmissible (twoGeneratorEndpointSystem (-1) 2)
      alwaysDynamicallyEnabled (fun _ => 0) [0, 1] :=
    (generatorOrderAdmissibleBool_eq_true_iff _ _ _ _).mp both_orders_admissible_under_wide_bounds.1
  let witness := orderWitness bridge (fun _ => 0) [0, 1] trivial admitted
  refine ⟨witness, order_witness_length bridge _ _ _ _, ?_, ?_, ?_⟩
  · exact order_witness_input_trace bridge _ _ _ _
  · exact order_witness_evidence_trace bridge _ _ _ _
  · decide

theorem wide_registered_kernel_model_exists :
    Nonempty (RegisteredAdmissibleOrder (twoGeneratorEndpointSystem (-1) 2)
      twoGeneratorEnumeration alwaysDynamicallyEnabled) := by
  apply (registered_model_inhabited_iff _ _ _).mpr
  exact ⟨bothGeneratorsPresent, widened_intermediate_bounds_restore_reachability⟩

/-- The original endpoint-feasibility counterexample remains outside sequential admission. -/
theorem endpoint_feasibility_still_does_not_supply_an_order :
    GeneratorIncidenceFeasible (twoGeneratorEndpointSystem 0 1) bothGeneratorsPresent ∧
      ¬ SequentiallyGeneratorReachable (twoGeneratorEndpointSystem 0 1)
        twoGeneratorEnumeration alwaysDynamicallyEnabled bothGeneratorsPresent :=
  endpoint_feasibility_does_not_imply_sequential_reachability

def oneStepSystem : GeneratorSuccessorConstraintSystem Unit Unit Unit where
  current := fun _ => 0
  generatorEffect := fun _ _ => 1
  lowerBound := fun _ => 0
  upperBound := fun _ => 1
  invariantCoefficient := fun _ _ => 0
  invariantTarget := fun _ => 0
  enabled := fun _ => true
  mandatory := fun _ => true
  requires := fun _ _ => false
  excludes := fun _ _ => false

def zeroOnlyEnabled (state : Unit → Int) (_ : Unit) : Bool := decide (state () = 0)

def bridgeStateOf (state : Unit → Int) : BridgeState :=
  if state () = 0 then .initial else .terminal

/-- Even all local raw transitions can be preserved while evidence sufficiency is absent. -/
theorem raw_one_step_map (state : Unit → Int)
    (admissible : GeneratorStepAdmissible oneStepSystem zeroOnlyEnabled state ()) :
    bridgeTransition (bridgeStateOf state) .advance
      (bridgeStateOf (generatorSingleStep oneStepSystem state ())) := by
  have zero : state () = 0 := of_decide_eq_true admissible.2.1
  simp [bridgeStateOf, generatorSingleStep, oneStepSystem, zero, bridgeTransition]

theorem raw_mapped_order_does_not_supply_evidence :
    GeneratorOrderAdmissible oneStepSystem zeroOnlyEnabled oneStepSystem.current [()] ∧
      bridgeTransition (bridgeStateOf oneStepSystem.current) .advance
        (bridgeStateOf (runGeneratorOrder oneStepSystem oneStepSystem.current [()])) ∧
      ¬ Continues (bridgeContext false false) (bridgeStateOf oneStepSystem.current)
        (bridgeStateOf (runGeneratorOrder oneStepSystem oneStepSystem.current [()])) := by
  constructor
  · apply (generatorOrderAdmissibleBool_eq_true_iff _ _ _ _).mp
    decide
  constructor
  · simp [bridgeStateOf, runGeneratorOrder, generatorSingleStep, oneStepSystem, bridgeTransition]
  · simpa [bridgeStateOf, runGeneratorOrder, generatorSingleStep, oneStepSystem] using
      raw_lineage_does_not_determine_contextual_continuation.2

def falseInvariantContext : ContinuationContext Unit Unit Unit Unit Unit Unit Unit Unit Unit where
  task := ()
  projection := ()
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := ()
  transition := fun _ _ _ => False
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun _ => False
  transitionPreservesInvariant := by intro _ _ _ invariant _; exact invariant

theorem empty_order_does_not_supply_initial_invariant :
    GeneratorOrderAdmissible oneStepSystem zeroOnlyEnabled oneStepSystem.current [] ∧
      ¬ Continues falseInvariantContext () () := by
  constructor
  · trivial
  · rintro ⟨witness⟩
    exact witness.initialInvariant

end OCScientificExtensions.GeneratorStepContinuationBridge
