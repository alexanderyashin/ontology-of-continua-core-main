import OCKIndividuationMSpaceComposition.GeneratorSamplingFrameTransport
import OCKIndividuationMSpaceComposition.GeneratedDeviationCone
import OCKIndividuationMSpaceComposition.KMContextContinuationCoherence
import Mathlib.Algebra.BigOperators.Ring.Finset

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe uGenerator uCoordinate uInvariant uObservation

/-!
# Generator successor mechanics under OC constraints

Finite-state enumeration, vector-addition state equations and reachability are
mature prior art.  This module supplies the OC adapter: a frozen generator
incidence vector must satisfy enabled/mandatory/require/exclude relations,
K/M-derived coordinate bounds, and context/continuation invariant equations.
The resulting successor family is a generative set-valued prediction made before
the target transition is observed.

Theorems below identify exactly when that family collapses to one successor,
give an information-optimal coordinate band when its endpoints are attainable,
and prove an observation-alias no-go when two feasible incidence vectors remain.
-/

/-- Finite typed mechanics for one OC successor transition. -/
structure GeneratorSuccessorConstraintSystem
    (Generator : Type uGenerator) [Fintype Generator]
    (Coordinate : Type uCoordinate) [Fintype Coordinate]
    (Invariant : Type uInvariant) [Fintype Invariant] where
  current : Coordinate → Int
  generatorEffect : Generator → Coordinate → Int
  lowerBound : Coordinate → Int
  upperBound : Coordinate → Int
  invariantCoefficient : Invariant → Coordinate → Int
  invariantTarget : Invariant → Int
  enabled : Generator → Bool
  mandatory : Generator → Bool
  requires : Generator → Generator → Bool
  excludes : Generator → Generator → Bool

/-- Boolean generator-incidence state equation. -/
def generatorSuccessorState
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (incidence : Generator → Bool) : Coordinate → Int :=
  fun coordinate =>
    system.current coordinate +
      ∑ generator,
        if incidence generator then
          system.generatorEffect generator coordinate
        else 0

/-- All structural, relational, interval and invariant obligations for one
candidate incidence vector. -/
structure GeneratorIncidenceFeasible
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (incidence : Generator → Bool) : Prop where
  enabled : ∀ generator,
    incidence generator = true → system.enabled generator = true
  mandatory : ∀ generator,
    system.mandatory generator = true → incidence generator = true
  required : ∀ source target,
    incidence source = true → system.requires source target = true →
      incidence target = true
  excluded : ∀ left right,
    incidence left = true → incidence right = true →
      system.excludes left right = false
  lowerBounded : ∀ coordinate,
    system.lowerBound coordinate ≤
      generatorSuccessorState system incidence coordinate
  upperBounded : ∀ coordinate,
    generatorSuccessorState system incidence coordinate ≤
      system.upperBound coordinate
  invariantPreserved : ∀ invariant,
    (∑ coordinate,
      system.invariantCoefficient invariant coordinate *
        generatorSuccessorState system incidence coordinate) =
      system.invariantTarget invariant

/-- Propositional normal form used by the executable feasibility decider. -/
def generatorIncidenceFeasibleConditions
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (incidence : Generator → Bool) : Prop :=
  (∀ generator,
    incidence generator = true → system.enabled generator = true) ∧
  (∀ generator,
    system.mandatory generator = true → incidence generator = true) ∧
  (∀ source target,
    incidence source = true → system.requires source target = true →
      incidence target = true) ∧
  (∀ left right,
    incidence left = true → incidence right = true →
      system.excludes left right = false) ∧
  (∀ coordinate,
    system.lowerBound coordinate ≤
      generatorSuccessorState system incidence coordinate) ∧
  (∀ coordinate,
    generatorSuccessorState system incidence coordinate ≤
      system.upperBound coordinate) ∧
  (∀ invariant,
    (∑ coordinate,
      system.invariantCoefficient invariant coordinate *
        generatorSuccessorState system incidence coordinate) =
      system.invariantTarget invariant)

theorem generatorIncidenceFeasible_iff_conditions
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (incidence : Generator → Bool) :
    GeneratorIncidenceFeasible system incidence ↔
      generatorIncidenceFeasibleConditions system incidence := by
  constructor
  · intro feasible
    exact ⟨feasible.enabled, feasible.mandatory, feasible.required,
      feasible.excluded, feasible.lowerBounded, feasible.upperBounded,
      feasible.invariantPreserved⟩
  · rintro ⟨enabled, mandatory, required, excluded, lowerBounded,
      upperBounded, invariantPreserved⟩
    exact ⟨enabled, mandatory, required, excluded, lowerBounded, upperBounded,
      invariantPreserved⟩

/-- Executable finite feasibility decision, avoiding a classical oracle. -/
def generatorIncidenceFeasibleBool
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (incidence : Generator → Bool) : Bool :=
  decide (∀ generator,
      incidence generator = true → system.enabled generator = true) &&
  decide (∀ generator,
      system.mandatory generator = true → incidence generator = true) &&
  decide (∀ source target,
      incidence source = true → system.requires source target = true →
        incidence target = true) &&
  decide (∀ left right,
      incidence left = true → incidence right = true →
        system.excludes left right = false) &&
  decide (∀ coordinate,
      system.lowerBound coordinate ≤
        generatorSuccessorState system incidence coordinate) &&
  decide (∀ coordinate,
      generatorSuccessorState system incidence coordinate ≤
        system.upperBound coordinate) &&
  decide (∀ invariant,
      (∑ coordinate,
        system.invariantCoefficient invariant coordinate *
          generatorSuccessorState system incidence coordinate) =
        system.invariantTarget invariant)

theorem generatorIncidenceFeasibleBool_eq_true_iff
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (incidence : Generator → Bool) :
    generatorIncidenceFeasibleBool system incidence = true ↔
      GeneratorIncidenceFeasible system incidence := by
  rw [generatorIncidenceFeasible_iff_conditions]
  simp [generatorIncidenceFeasibleBool, generatorIncidenceFeasibleConditions]
  tauto

/-- Exact finite enumeration surface for every feasible incidence vector. -/
def feasibleGeneratorIncidences
    {Generator : Type uGenerator} [Fintype Generator]
    [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant) :
    Finset (Generator → Bool) :=
  Finset.univ.filter fun incidence =>
    generatorIncidenceFeasibleBool system incidence = true

/-- Enumeration is extensionally exact, not a heuristic search. -/
theorem incidence_mem_feasibleEnumeration_iff
    {Generator : Type uGenerator} [Fintype Generator]
    [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate] [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (incidence : Generator → Bool) :
    incidence ∈ feasibleGeneratorIncidences system ↔
      GeneratorIncidenceFeasible system incidence := by
  simp [feasibleGeneratorIncidences,
    generatorIncidenceFeasibleBool_eq_true_iff]

/-- Every generated feasible successor obeys the registered coordinate band. -/
theorem feasible_successor_within_registered_bounds
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant}
    {incidence : Generator → Bool}
    (feasible : GeneratorIncidenceFeasible system incidence)
    (coordinate : Coordinate) :
    generatorSuccessorState system incidence coordinate ∈
      Set.Icc (system.lowerBound coordinate) (system.upperBound coordinate) :=
  ⟨feasible.lowerBounded coordinate, feasible.upperBounded coordinate⟩

/-- Every generated feasible successor satisfies each registered linear
context/continuation invariant exactly. -/
theorem feasible_successor_preserves_registered_invariant
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant}
    {incidence : Generator → Bool}
    (feasible : GeneratorIncidenceFeasible system incidence)
    (invariant : Invariant) :
    (∑ coordinate,
      system.invariantCoefficient invariant coordinate *
        generatorSuccessorState system incidence coordinate) =
      system.invariantTarget invariant :=
  feasible.invariantPreserved invariant

/-- A structurally required generator is present in every feasible successor. -/
theorem required_generator_is_present
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant}
    {incidence : Generator → Bool}
    (feasible : GeneratorIncidenceFeasible system incidence)
    {source target : Generator}
    (sourcePresent : incidence source = true)
    (requiresTarget : system.requires source target = true) :
    incidence target = true :=
  feasible.required source target sourcePresent requiresTarget

/-- An excluded generator pair cannot coexist in a feasible successor. -/
theorem excluded_pair_cannot_be_jointly_present
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant}
    {incidence : Generator → Bool}
    (feasible : GeneratorIncidenceFeasible system incidence)
    {left right : Generator}
    (excluded : system.excludes left right = true) :
    ¬ (incidence left = true ∧ incidence right = true) := by
  rintro ⟨leftPresent, rightPresent⟩
  have mustBeFalse := feasible.excluded left right leftPresent rightPresent
  rw [excluded] at mustBeFalse
  contradiction

/-- Point identification means that a feasible incidence exists and every
feasible incidence produces the same successor state. -/
def GeneratorSuccessorPointIdentified
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant) :
    Prop :=
  (∃ incidence, GeneratorIncidenceFeasible system incidence) ∧
    ∀ left right,
      GeneratorIncidenceFeasible system left →
      GeneratorIncidenceFeasible system right →
      generatorSuccessorState system left =
        generatorSuccessorState system right

/-- A unique feasible incidence is sufficient for exact successor prediction. -/
theorem unique_feasible_incidence_point_identifies_successor
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (chosen : Generator → Bool)
    (unique : ∀ incidence,
      GeneratorIncidenceFeasible system incidence ↔ incidence = chosen) :
    GeneratorSuccessorPointIdentified system := by
  constructor
  · exact ⟨chosen, (unique chosen).mpr rfl⟩
  · intro left right leftFeasible rightFeasible
    rw [(unique left).mp leftFeasible, (unique right).mp rightFeasible]

/-- Zero-width bounds point-identify the successor whenever at least one
feasible incidence exists. -/
theorem zero_width_constraints_point_identify_successor
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (existsFeasible : ∃ incidence, GeneratorIncidenceFeasible system incidence)
    (zeroWidth : ∀ coordinate,
      system.lowerBound coordinate = system.upperBound coordinate) :
    GeneratorSuccessorPointIdentified system := by
  refine ⟨existsFeasible, ?_⟩
  intro left right leftFeasible rightFeasible
  funext coordinate
  have leftEqualsLower :
      generatorSuccessorState system left coordinate =
        system.lowerBound coordinate := by
    apply le_antisymm
    · rw [zeroWidth coordinate]
      exact leftFeasible.upperBounded coordinate
    · exact leftFeasible.lowerBounded coordinate
  have rightEqualsLower :
      generatorSuccessorState system right coordinate =
        system.lowerBound coordinate := by
    apply le_antisymm
    · rw [zeroWidth coordinate]
      exact rightFeasible.upperBounded coordinate
    · exact rightFeasible.lowerBounded coordinate
  exact leftEqualsLower.trans rightEqualsLower.symm

/-- If both registered bound endpoints are feasible, the coordinate interval is
information-optimal: no sound predictor over the same class has smaller width. -/
theorem attained_generator_constraint_band_is_information_optimal
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (coordinate : Coordinate)
    (lowerWitness upperWitness : Generator → Bool)
    (lowerFeasible : GeneratorIncidenceFeasible system lowerWitness)
    (upperFeasible : GeneratorIncidenceFeasible system upperWitness)
    (lowerAttained : generatorSuccessorState system lowerWitness coordinate =
      system.lowerBound coordinate)
    (upperAttained : generatorSuccessorState system upperWitness coordinate =
      system.upperBound coordinate)
    (claimedLower claimedUpper : Int)
    (sound : ∀ incidence,
      GeneratorIncidenceFeasible system incidence →
      claimedLower ≤ generatorSuccessorState system incidence coordinate ∧
        generatorSuccessorState system incidence coordinate ≤ claimedUpper) :
    system.upperBound coordinate - system.lowerBound coordinate ≤
      claimedUpper - claimedLower := by
  have coversLower := (sound lowerWitness lowerFeasible).1
  have coversUpper := (sound upperWitness upperFeasible).2
  rw [lowerAttained] at coversLower
  rw [upperAttained] at coversUpper
  omega

/-- Two feasible incidence vectors with distinct successors refute point
identification. -/
theorem distinct_feasible_successors_block_point_identification
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (left right : Generator → Bool)
    (leftFeasible : GeneratorIncidenceFeasible system left)
    (rightFeasible : GeneratorIncidenceFeasible system right)
    (different : generatorSuccessorState system left ≠
      generatorSuccessorState system right) :
    ¬ GeneratorSuccessorPointIdentified system := by
  intro identified
  exact different (identified.2 left right leftFeasible rightFeasible)

/-- Sharp observation no-go: equal observations of two feasible but different
successors preclude a universally exact observation-only decoder. -/
theorem feasible_generator_observation_alias_blocks_exact_decoder
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {Observation : Type uObservation}
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (observe : (Generator → Bool) → Observation)
    (left right : Generator → Bool)
    (leftFeasible : GeneratorIncidenceFeasible system left)
    (rightFeasible : GeneratorIncidenceFeasible system right)
    (sameObservation : observe left = observe right)
    (differentSuccessor : generatorSuccessorState system left ≠
      generatorSuccessorState system right) :
    ¬ ∃ decoder : Observation → (Coordinate → Int),
      ∀ incidence,
        GeneratorIncidenceFeasible system incidence →
        decoder (observe incidence) = generatorSuccessorState system incidence := by
  rintro ⟨decoder, exactDecoder⟩
  have sameDecoded := congrArg decoder sameObservation
  rw [exactDecoder left leftFeasible, exactDecoder right rightFeasible] at sameDecoded
  exact differentSuccessor sameDecoded

/-! ## Exact three-generator example -/

def threeGeneratorEffect (generator : Fin 3) (coordinate : Bool) : Int :=
  if generator = 0 then
    if coordinate then -2 else 2
  else if generator = 1 then
    if coordinate then 1 else -1
  else if coordinate then 0 else 4

def threeGeneratorRequires (source target : Fin 3) : Bool :=
  decide (source = 0 ∧ target = 1)

def threeGeneratorBaseSystem :
    GeneratorSuccessorConstraintSystem (Fin 3) Bool Unit where
  current := fun _ => 5
  generatorEffect := threeGeneratorEffect
  lowerBound := fun _ => 4
  upperBound := fun _ => 6
  invariantCoefficient := fun _ _ => 1
  invariantTarget := fun _ => 10
  enabled := fun _ => true
  mandatory := fun _ => false
  requires := threeGeneratorRequires
  excludes := fun _ _ => false

def incidence000 (_generator : Fin 3) : Bool := false

def incidence010 (generator : Fin 3) : Bool := decide (generator = 1)

def incidence110 (generator : Fin 3) : Bool :=
  decide (generator = 0 ∨ generator = 1)

/-- The complete feasible class is exactly `000`, `010`, `110`; generator 2 is
excluded by the conservation invariant and generator 0 requires generator 1. -/
theorem threeGeneratorBase_feasible_iff (incidence : Fin 3 → Bool) :
    GeneratorIncidenceFeasible threeGeneratorBaseSystem incidence ↔
      incidence = incidence000 ∨ incidence = incidence010 ∨
        incidence = incidence110 := by
  rw [← generatorIncidenceFeasibleBool_eq_true_iff]
  decide +revert

/-- The three exact successors are `(5,5)`, `(4,6)`, `(6,4)`. -/
theorem threeGeneratorBase_successors_exact :
    generatorSuccessorState threeGeneratorBaseSystem incidence000 false = 5 ∧
    generatorSuccessorState threeGeneratorBaseSystem incidence000 true = 5 ∧
    generatorSuccessorState threeGeneratorBaseSystem incidence010 false = 4 ∧
    generatorSuccessorState threeGeneratorBaseSystem incidence010 true = 6 ∧
    generatorSuccessorState threeGeneratorBaseSystem incidence110 false = 6 ∧
    generatorSuccessorState threeGeneratorBaseSystem incidence110 true = 4 := by
  decide

/-- Therefore the exact coordinate band `[4,6]` has width `2` and no sound
interval over this feasible class can be narrower. -/
theorem threeGeneratorBase_band_width_two_is_optimal
    (claimedLower claimedUpper : Int)
    (sound : ∀ incidence,
      GeneratorIncidenceFeasible threeGeneratorBaseSystem incidence →
      claimedLower ≤
          generatorSuccessorState threeGeneratorBaseSystem incidence false ∧
        generatorSuccessorState threeGeneratorBaseSystem incidence false ≤
          claimedUpper) :
    2 ≤ claimedUpper - claimedLower := by
  have lowerFeasible :
      GeneratorIncidenceFeasible threeGeneratorBaseSystem incidence010 :=
    (threeGeneratorBase_feasible_iff incidence010).mpr (Or.inr (Or.inl rfl))
  have upperFeasible :
      GeneratorIncidenceFeasible threeGeneratorBaseSystem incidence110 :=
    (threeGeneratorBase_feasible_iff incidence110).mpr (Or.inr (Or.inr rfl))
  have optimal := attained_generator_constraint_band_is_information_optimal
    threeGeneratorBaseSystem false incidence010 incidence110
    lowerFeasible upperFeasible (by decide) (by decide)
    claimedLower claimedUpper sound
  norm_num [threeGeneratorBaseSystem] at optimal ⊢
  exact optimal

/-- Observing only the conserved total `10` aliases feasible successors `(4,6)`
and `(6,4)`, so no total-only decoder can predict the coordinate allocation. -/
theorem conserved_total_does_not_identify_generator_successor :
    ¬ ∃ decoder : Int → (Bool → Int),
      ∀ incidence,
        GeneratorIncidenceFeasible threeGeneratorBaseSystem incidence →
        decoder
            (∑ coordinate,
              generatorSuccessorState threeGeneratorBaseSystem incidence coordinate) =
          generatorSuccessorState threeGeneratorBaseSystem incidence := by
  have leftFeasible :
      GeneratorIncidenceFeasible threeGeneratorBaseSystem incidence010 :=
    (threeGeneratorBase_feasible_iff incidence010).mpr (Or.inr (Or.inl rfl))
  have rightFeasible :
      GeneratorIncidenceFeasible threeGeneratorBaseSystem incidence110 :=
    (threeGeneratorBase_feasible_iff incidence110).mpr (Or.inr (Or.inr rfl))
  apply feasible_generator_observation_alias_blocks_exact_decoder
    threeGeneratorBaseSystem
      (fun incidence =>
        ∑ coordinate,
          generatorSuccessorState threeGeneratorBaseSystem incidence coordinate)
      incidence010 incidence110 leftFeasible rightFeasible
  · decide
  · intro sameSuccessor
    have coordinateEquality := congrFun sameSuccessor false
    have leftCoordinate :
        generatorSuccessorState threeGeneratorBaseSystem incidence010 false = 4 := by
      decide
    have rightCoordinate :
        generatorSuccessorState threeGeneratorBaseSystem incidence110 false = 6 := by
      decide
    rw [leftCoordinate, rightCoordinate] at coordinateEquality
    omega

/-- Tightening the context so generators 0 and 1 are mandatory leaves exactly
one feasible incidence and therefore point-identifies successor `(6,4)`. -/
def threeGeneratorTightSystem :
    GeneratorSuccessorConstraintSystem (Fin 3) Bool Unit :=
  { threeGeneratorBaseSystem with
    mandatory := fun generator =>
      decide (generator = 0 ∨ generator = 1) }

theorem threeGeneratorTight_feasible_iff (incidence : Fin 3 → Bool) :
    GeneratorIncidenceFeasible threeGeneratorTightSystem incidence ↔
      incidence = incidence110 := by
  rw [← generatorIncidenceFeasibleBool_eq_true_iff]
  decide +revert

theorem threeGeneratorTight_point_identifies_successor :
    GeneratorSuccessorPointIdentified threeGeneratorTightSystem :=
  unique_feasible_incidence_point_identifies_successor
    threeGeneratorTightSystem incidence110 threeGeneratorTight_feasible_iff

theorem threeGeneratorTight_successor_exact :
    generatorSuccessorState threeGeneratorTightSystem incidence110 false = 6 ∧
    generatorSuccessorState threeGeneratorTightSystem incidence110 true = 4 := by
  decide

end OCKIndividuationMSpaceComposition
