import OCKIndividuationMSpaceComposition.OCGeneratorMechanicsBinding

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe uGenerator uCoordinate uInvariant

/-!
# Ordered multi-step generator reachability

The one-step state equation is insensitive to the order in which generators
fire.  Real paths are not: enabling, bounds and continuation invariants must
hold after every intermediate step.  This module enumerates every permutation
of the selected finite generator support and checks those obligations at each
prefix.  It thereby separates endpoint feasibility from path reachability.
-/

def generatorSingleStep
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (state : Coordinate → Int) (generator : Generator) : Coordinate → Int :=
  fun coordinate => state coordinate + system.generatorEffect generator coordinate

/-- Prefix-by-prefix admissibility for one chronological generator order. -/
def GeneratorOrderAdmissible
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool) :
    (Coordinate → Int) → List Generator → Prop
  | _, [] => True
  | state, generator :: remaining =>
      system.enabled generator = true ∧
      dynamicEnabled state generator = true ∧
      (∀ coordinate,
        system.lowerBound coordinate ≤
          generatorSingleStep system state generator coordinate) ∧
      (∀ coordinate,
        generatorSingleStep system state generator coordinate ≤
          system.upperBound coordinate) ∧
      (∀ invariant,
        (∑ coordinate,
          system.invariantCoefficient invariant coordinate *
            generatorSingleStep system state generator coordinate) =
          system.invariantTarget invariant) ∧
      GeneratorOrderAdmissible system dynamicEnabled
        (generatorSingleStep system state generator) remaining

/-- Executable checker for the same ordered-prefix obligations. -/
def generatorOrderAdmissibleBool
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool) :
    (Coordinate → Int) → List Generator → Bool
  | _, [] => true
  | state, generator :: remaining =>
      system.enabled generator &&
      dynamicEnabled state generator &&
      decide (∀ coordinate,
        system.lowerBound coordinate ≤
          generatorSingleStep system state generator coordinate) &&
      decide (∀ coordinate,
        generatorSingleStep system state generator coordinate ≤
          system.upperBound coordinate) &&
      decide (∀ invariant,
        (∑ coordinate,
          system.invariantCoefficient invariant coordinate *
            generatorSingleStep system state generator coordinate) =
          system.invariantTarget invariant) &&
      generatorOrderAdmissibleBool system dynamicEnabled
        (generatorSingleStep system state generator) remaining

theorem generatorOrderAdmissibleBool_eq_true_iff
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool)
    (state : Coordinate → Int) (order : List Generator) :
    generatorOrderAdmissibleBool system dynamicEnabled state order = true ↔
      GeneratorOrderAdmissible system dynamicEnabled state order := by
  induction order generalizing state with
  | nil => simp [generatorOrderAdmissibleBool, GeneratorOrderAdmissible]
  | cons generator remaining inductionHypothesis =>
      simp [generatorOrderAdmissibleBool, GeneratorOrderAdmissible,
        inductionHypothesis]
      tauto

/-- A proof-carrying executable generator enumeration.  Making the enumeration
explicit avoids hiding a noncomputable ordering choice in the model checker. -/
structure RegisteredGeneratorEnumeration
    (Generator : Type uGenerator) [Fintype Generator] [DecidableEq Generator] where
  order : List Generator
  nodup : order.Nodup
  complete : ∀ generator, generator ∈ order

/-- Kernel-reducible insertion at every list position. -/
def insertGeneratorEverywhere {Generator : Type uGenerator}
    (generator : Generator) : List Generator → List (List Generator)
  | [] => [[generator]]
  | head :: tail =>
      (generator :: head :: tail) ::
        (insertGeneratorEverywhere generator tail).map (head :: ·)

/-- Kernel-reducible finite permutation enumeration.  This is deliberately
small and local so exact examples need neither an oracle nor native code. -/
def allGeneratorOrders {Generator : Type uGenerator} :
    List Generator → List (List Generator)
  | [] => [[]]
  | generator :: remaining =>
      (allGeneratorOrders remaining).flatMap
        (insertGeneratorEverywhere generator)

/-- Every possible chronological order of the selected generators, each fired
exactly once. -/
def generatorIncidenceOrders
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    (enumeration : RegisteredGeneratorEnumeration Generator)
    (incidence : Generator → Bool) : List (List Generator) :=
  allGeneratorOrders
    (enumeration.order.filter fun generator => incidence generator)

/-- Endpoint feasibility plus existence of at least one admissible ordering. -/
def SequentiallyGeneratorReachable
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (enumeration : RegisteredGeneratorEnumeration Generator)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool)
    (incidence : Generator → Bool) : Prop :=
  GeneratorIncidenceFeasible system incidence ∧
    ∃ order ∈ generatorIncidenceOrders enumeration incidence,
      GeneratorOrderAdmissible system dynamicEnabled system.current order

def sequentiallyGeneratorReachableBool
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (enumeration : RegisteredGeneratorEnumeration Generator)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool)
    (incidence : Generator → Bool) : Bool :=
  generatorIncidenceFeasibleBool system incidence &&
    (generatorIncidenceOrders enumeration incidence).any fun order =>
      generatorOrderAdmissibleBool system dynamicEnabled system.current order

theorem sequentiallyGeneratorReachableBool_eq_true_iff
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (enumeration : RegisteredGeneratorEnumeration Generator)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool)
    (incidence : Generator → Bool) :
    sequentiallyGeneratorReachableBool system enumeration dynamicEnabled incidence = true ↔
      SequentiallyGeneratorReachable system enumeration dynamicEnabled incidence := by
  simp [sequentiallyGeneratorReachableBool, SequentiallyGeneratorReachable,
    generatorIncidenceFeasibleBool_eq_true_iff,
    generatorOrderAdmissibleBool_eq_true_iff]

/-- Positive bridge: ordered reachability always implies endpoint feasibility. -/
theorem sequential_reachability_implies_endpoint_feasibility
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    {system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant}
    {enumeration : RegisteredGeneratorEnumeration Generator}
    {dynamicEnabled : (Coordinate → Int) → Generator → Bool}
    {incidence : Generator → Bool}
    (reachable : SequentiallyGeneratorReachable system enumeration dynamicEnabled incidence) :
    GeneratorIncidenceFeasible system incidence :=
  reachable.1

/-- Positive construction from an explicitly admitted order. -/
theorem admitted_order_implies_sequential_reachability
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (enumeration : RegisteredGeneratorEnumeration Generator)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool)
    (incidence : Generator → Bool)
    (endpointFeasible : GeneratorIncidenceFeasible system incidence)
    (order : List Generator)
    (registeredOrder : order ∈ generatorIncidenceOrders enumeration incidence)
    (admissible : GeneratorOrderAdmissible system dynamicEnabled system.current order) :
    SequentiallyGeneratorReachable system enumeration dynamicEnabled incidence :=
  ⟨endpointFeasible, order, registeredOrder, admissible⟩

/-- Sharp obstruction: endpoint feasibility is insufficient when every
registered ordering violates an intermediate obligation. -/
theorem no_admissible_order_blocks_sequential_reachability
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (enumeration : RegisteredGeneratorEnumeration Generator)
    (dynamicEnabled : (Coordinate → Int) → Generator → Bool)
    (incidence : Generator → Bool)
    (blocked : ∀ order ∈ generatorIncidenceOrders enumeration incidence,
      ¬ GeneratorOrderAdmissible system dynamicEnabled system.current order) :
    ¬ SequentiallyGeneratorReachable system enumeration dynamicEnabled incidence := by
  rintro ⟨endpointFeasible, order, registered, admissible⟩
  exact blocked order registered admissible

/-! ## Endpoint-feasible but path-impossible countermodel -/

def twoGeneratorEndpointSystem (lower upper : Int) :
    GeneratorSuccessorConstraintSystem (Fin 2) (Fin 1) Unit where
  current := fun _ => 0
  generatorEffect := fun generator _ => if generator = 0 then 2 else -1
  lowerBound := fun _ => lower
  upperBound := fun _ => upper
  invariantCoefficient := fun _ _ => 0
  invariantTarget := fun _ => 0
  enabled := fun _ => true
  mandatory := fun _ => true
  requires := fun _ _ => false
  excludes := fun _ _ => false

def bothGeneratorsPresent (_ : Fin 2) : Bool := true

def twoGeneratorEnumeration : RegisteredGeneratorEnumeration (Fin 2) where
  order := [0, 1]
  nodup := by decide
  complete := by
    intro generator
    fin_cases generator <;> simp

def alwaysDynamicallyEnabled
    {Coordinate : Type uCoordinate} {Generator : Type uGenerator} :
    (Coordinate → Int) → Generator → Bool := fun _ _ => true

theorem bothGenerators_endpoint_successor_exact :
    generatorSuccessorState (twoGeneratorEndpointSystem 0 1)
      bothGeneratorsPresent 0 = 1 := by
  decide

theorem bothGenerators_endpoint_feasible_under_tight_bounds :
    GeneratorIncidenceFeasible (twoGeneratorEndpointSystem 0 1)
      bothGeneratorsPresent := by
  apply (generatorIncidenceFeasibleBool_eq_true_iff
    (twoGeneratorEndpointSystem 0 1) bothGeneratorsPresent).mp
  decide

theorem bothGenerator_orders_exact :
    generatorIncidenceOrders twoGeneratorEnumeration bothGeneratorsPresent =
      [[0, 1], [1, 0]] := by
  decide

theorem both_orders_violate_tight_intermediate_bounds :
    generatorOrderAdmissibleBool (twoGeneratorEndpointSystem 0 1)
        alwaysDynamicallyEnabled (fun _ => 0) [0, 1] = false ∧
      generatorOrderAdmissibleBool (twoGeneratorEndpointSystem 0 1)
        alwaysDynamicallyEnabled (fun _ => 0) [1, 0] = false := by
  decide

/-- Numerical state-equation false positive: endpoint `1` is feasible in
`[0,1]`, but the only two orders first visit `2` or `-1`; neither path exists. -/
theorem endpoint_feasibility_does_not_imply_sequential_reachability :
    GeneratorIncidenceFeasible (twoGeneratorEndpointSystem 0 1)
        bothGeneratorsPresent ∧
      ¬ SequentiallyGeneratorReachable (twoGeneratorEndpointSystem 0 1)
        twoGeneratorEnumeration alwaysDynamicallyEnabled bothGeneratorsPresent := by
  constructor
  · exact bothGenerators_endpoint_feasible_under_tight_bounds
  · rw [← sequentiallyGeneratorReachableBool_eq_true_iff]
    decide

/-- Widening the intermediate admissibility interval to `[-1,2]` restores both
orders and therefore path reachability to the same endpoint `1`. -/
theorem widened_intermediate_bounds_restore_reachability :
    SequentiallyGeneratorReachable (twoGeneratorEndpointSystem (-1) 2)
      twoGeneratorEnumeration alwaysDynamicallyEnabled bothGeneratorsPresent := by
  rw [← sequentiallyGeneratorReachableBool_eq_true_iff]
  decide

theorem both_orders_admissible_under_wide_bounds :
    generatorOrderAdmissibleBool (twoGeneratorEndpointSystem (-1) 2)
        alwaysDynamicallyEnabled (fun _ => 0) [0, 1] = true ∧
      generatorOrderAdmissibleBool (twoGeneratorEndpointSystem (-1) 2)
        alwaysDynamicallyEnabled (fun _ => 0) [1, 0] = true := by
  decide

end OCKIndividuationMSpaceComposition
