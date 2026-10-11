import OCKIndividuationMSpaceComposition.GeneratorSuccessorConstraintMechanics

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe uGenerator uCoordinate uInvariant uFrame uObservation

/-!
# Binding observed OC structure to generator successor mechanics

This module closes the formal half of the field-binding boundary left by the
finite successor mechanics.  A binding observation records which inputs come
from the K layer, the M-space projection, the operator family, the active
context and the continuation invariants.  Its translation to a successor
system is definitional and therefore replayable.

The empirical question whether a concrete extractor measured those fields
correctly remains separate.  The theorems here establish what follows once a
versioned observation satisfies that contract, how constraint refinement
changes predictive power, and why a frame omitted from the observation can
destroy identification.
-/

/-- Minimum typed observation surface from which every field of the finite
generator mechanics is computed. -/
structure OCGeneratorMechanicsObservation
    (Generator : Type uGenerator) [Fintype Generator]
    (Coordinate : Type uCoordinate) [Fintype Coordinate]
    (Invariant : Type uInvariant) [Fintype Invariant]
    (Frame : Type uFrame) where
  kLevel : Generator → Nat
  kEnabled : Generator → Bool
  mProjection : Coordinate → Int
  operatorEffect : Generator → Coordinate → Int
  contextLowerBound : Coordinate → Int
  contextUpperBound : Coordinate → Int
  continuationCoefficient : Invariant → Coordinate → Int
  continuationTarget : Invariant → Int
  contextMandatory : Generator → Bool
  contextRequires : Generator → Generator → Bool
  contextExcludes : Generator → Generator → Bool
  frame : Frame

/-- The field-by-field OC adapter.  No optimization or fitting occurs here:
the mechanics is the exact image of the frozen observation. -/
def OCGeneratorMechanicsObservation.toConstraintSystem
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {Frame : Type uFrame}
    (observation :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame) :
    GeneratorSuccessorConstraintSystem Generator Coordinate Invariant where
  current := observation.mProjection
  generatorEffect := observation.operatorEffect
  lowerBound := observation.contextLowerBound
  upperBound := observation.contextUpperBound
  invariantCoefficient := observation.continuationCoefficient
  invariantTarget := observation.continuationTarget
  enabled := observation.kEnabled
  mandatory := observation.contextMandatory
  requires := observation.contextRequires
  excludes := observation.contextExcludes

/-- The complete observation is a sufficient statistic for the mechanics:
equal frozen observations cannot silently produce different systems. -/
theorem equal_complete_observation_gives_equal_constraint_system
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {Frame : Type uFrame}
    {left right :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame}
    (same : left = right) :
    left.toConstraintSystem = right.toConstraintSystem := by
  subst right
  rfl

/-- A tight observation refines a loose one when it keeps the state equation
and invariant semantics fixed while disabling more generators, requiring or
excluding more combinations, and narrowing coordinate bounds.  K levels and
frame are fixed: changing either is transport, not refinement. -/
structure OCGeneratorMechanicsRefines
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {Frame : Type uFrame}
    (tight loose :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame) :
    Prop where
  sameKLevel : tight.kLevel = loose.kLevel
  sameFrame : tight.frame = loose.frame
  sameCurrent : tight.mProjection = loose.mProjection
  sameEffect : tight.operatorEffect = loose.operatorEffect
  enabled : ∀ generator,
    tight.kEnabled generator = true → loose.kEnabled generator = true
  mandatory : ∀ generator,
    loose.contextMandatory generator = true →
      tight.contextMandatory generator = true
  requires : ∀ source target,
    loose.contextRequires source target = true →
      tight.contextRequires source target = true
  excludes : ∀ left right,
    tight.contextExcludes left right = false →
      loose.contextExcludes left right = false
  lowerNarrowed : ∀ coordinate,
    loose.contextLowerBound coordinate ≤ tight.contextLowerBound coordinate
  upperNarrowed : ∀ coordinate,
    tight.contextUpperBound coordinate ≤ loose.contextUpperBound coordinate
  sameInvariantCoefficient :
    tight.continuationCoefficient = loose.continuationCoefficient
  sameInvariantTarget : tight.continuationTarget = loose.continuationTarget

theorem successor_state_eq_of_observation_refinement
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {Frame : Type uFrame}
    {tight loose :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame}
    (refines : OCGeneratorMechanicsRefines tight loose)
    (incidence : Generator → Bool) :
    generatorSuccessorState tight.toConstraintSystem incidence =
      generatorSuccessorState loose.toConstraintSystem incidence := by
  funext coordinate
  simp only [generatorSuccessorState, OCGeneratorMechanicsObservation.toConstraintSystem]
  rw [refines.sameCurrent, refines.sameEffect]

/-- Positive monotonicity theorem: with a stable K/frame/state/effect/invariant
contract, stronger OC constraints can only remove feasible incidences. -/
theorem observation_refinement_shrinks_feasible_class
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {Frame : Type uFrame}
    {tight loose :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame}
    (refines : OCGeneratorMechanicsRefines tight loose)
    (incidence : Generator → Bool)
    (tightFeasible :
      GeneratorIncidenceFeasible tight.toConstraintSystem incidence) :
    GeneratorIncidenceFeasible loose.toConstraintSystem incidence := by
  let successorEquality :=
    successor_state_eq_of_observation_refinement refines incidence
  constructor
  · intro generator present
    exact refines.enabled generator (tightFeasible.enabled generator present)
  · intro generator mandatory
    exact tightFeasible.mandatory generator
      (refines.mandatory generator mandatory)
  · intro source target sourcePresent required
    exact tightFeasible.required source target sourcePresent
      (refines.requires source target required)
  · intro left right leftPresent rightPresent
    exact refines.excludes left right
      (tightFeasible.excluded left right leftPresent rightPresent)
  · intro coordinate
    have tightLower := tightFeasible.lowerBounded coordinate
    have narrowed := refines.lowerNarrowed coordinate
    change loose.contextLowerBound coordinate ≤
      generatorSuccessorState loose.toConstraintSystem incidence coordinate
    rw [← congrFun successorEquality coordinate]
    exact narrowed.trans tightLower
  · intro coordinate
    have tightUpper := tightFeasible.upperBounded coordinate
    have narrowed := refines.upperNarrowed coordinate
    change generatorSuccessorState loose.toConstraintSystem incidence coordinate ≤
      loose.contextUpperBound coordinate
    rw [← congrFun successorEquality coordinate]
    exact tightUpper.trans narrowed
  · intro invariant
    have preserved := tightFeasible.invariantPreserved invariant
    change (∑ coordinate,
      loose.continuationCoefficient invariant coordinate *
        generatorSuccessorState loose.toConstraintSystem incidence coordinate) =
      loose.continuationTarget invariant
    rw [← refines.sameInvariantCoefficient, ← refines.sameInvariantTarget,
      ← successorEquality]
    exact preserved

/-- Exact finite enumeration inherits the same subset law. -/
theorem observation_refinement_feasibleEnumeration_subset
    {Generator : Type uGenerator} [Fintype Generator] [DecidableEq Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
      [DecidableEq Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant] [DecidableEq Invariant]
    {Frame : Type uFrame}
    {tight loose :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame}
    (refines : OCGeneratorMechanicsRefines tight loose) :
    feasibleGeneratorIncidences tight.toConstraintSystem ⊆
      feasibleGeneratorIncidences loose.toConstraintSystem := by
  intro incidence member
  rw [incidence_mem_feasibleEnumeration_iff] at member ⊢
  exact observation_refinement_shrinks_feasible_class refines incidence member

/-- Once a loose model is point-identified, a nonempty refinement with the
same state equation preserves that exact successor. -/
theorem point_identification_survives_nonempty_refinement
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {Frame : Type uFrame}
    {tight loose :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame}
    (refines : OCGeneratorMechanicsRefines tight loose)
    (looseIdentified :
      GeneratorSuccessorPointIdentified loose.toConstraintSystem)
    (tightNonempty : ∃ incidence,
      GeneratorIncidenceFeasible tight.toConstraintSystem incidence) :
    GeneratorSuccessorPointIdentified tight.toConstraintSystem := by
  refine ⟨tightNonempty, ?_⟩
  intro left right leftTight rightTight
  have leftLoose :=
    observation_refinement_shrinks_feasible_class refines left leftTight
  have rightLoose :=
    observation_refinement_shrinks_feasible_class refines right rightTight
  rw [successor_state_eq_of_observation_refinement refines left,
    successor_state_eq_of_observation_refinement refines right]
  exact looseIdentified.2 left right leftLoose rightLoose

/-! ## Continuation and M-space bridge -/

/-- The mechanics induces an evidence-qualified continuation context whose
one-step transitions are exactly feasible generator successors. -/
def OCGeneratorMechanicsObservation.continuationContext
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {Frame : Type uFrame}
    (observation :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame) :
    ContinuationContext
      (Coordinate → Int) (Generator → Bool) Unit Unit (Coordinate → Int)
        Unit Unit Unit Frame where
  task := ()
  projection := observation.mProjection
  boundary := ()
  activeConstraint := fun _ => True
  scope := ()
  frame := observation.frame
  transition := fun source incidence target =>
    source = observation.mProjection ∧
      GeneratorIncidenceFeasible observation.toConstraintSystem incidence ∧
      target = generatorSuccessorState observation.toConstraintSystem incidence
  edgeAdmissible := fun _ _ _ _ => True
  evidenceSufficient := fun _ => True
  invariant := fun state => ∀ invariant,
    (∑ coordinate,
      observation.continuationCoefficient invariant coordinate *
        state coordinate) = observation.continuationTarget invariant
  transitionPreservesInvariant := by
    intro current next incidence currentInvariant transition
    rw [transition.2.2]
    simpa [OCGeneratorMechanicsObservation.toConstraintSystem] using
      transition.2.1.invariantPreserved

/-- The qualified one-step transition is equivalent to mechanics feasibility
and the exact state equation. -/
theorem mechanics_qualifiedStep_iff_feasible_successor
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {Frame : Type uFrame}
    (observation :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame)
    (incidence : Generator → Bool)
    (target : Coordinate → Int) :
    EvidenceQualifiedStep observation.continuationContext
        observation.mProjection incidence target ↔
      GeneratorIncidenceFeasible observation.toConstraintSystem incidence ∧
        target = generatorSuccessorState observation.toConstraintSystem incidence := by
  simp [EvidenceQualifiedStep,
    OCGeneratorMechanicsObservation.continuationContext]

/-- Every feasible incidence with an admissible initial M-projection produces
an explicit one-edge path-dependent continuation witness. -/
def feasibleIncidence.toContinuationWitness
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {Frame : Type uFrame}
    (observation :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame)
    (incidence : Generator → Bool)
    (feasible :
      GeneratorIncidenceFeasible observation.toConstraintSystem incidence)
    (initialInvariant : ∀ invariant,
      (∑ coordinate,
        observation.continuationCoefficient invariant coordinate *
          observation.mProjection coordinate) =
        observation.continuationTarget invariant) :
    ContinuationWitness observation.continuationContext observation.mProjection
      (generatorSuccessorState observation.toConstraintSystem incidence) := by
  let edge : observation.continuationContext.transition observation.mProjection
      incidence (generatorSuccessorState observation.toConstraintSystem incidence) :=
    ⟨rfl, feasible, rfl⟩
  let history : OpenHistory observation.continuationContext.transition
      observation.mProjection
      (generatorSuccessorState observation.toConstraintSystem incidence) :=
    .extend .start incidence edge
  let evidence : HistoryEvidence observation.continuationContext history :=
    .extend .start incidence edge () trivial trivial
  exact ⟨history, evidence, initialInvariant⟩

/-! ## Frame-omission no-go -/

/-- Any observation map that aliases two feasible worlds with different
successors cannot support a universally exact successor decoder. -/
theorem oc_observation_alias_blocks_exact_successor_decoder
    {Generator : Type uGenerator} [Fintype Generator]
    {Coordinate : Type uCoordinate} [Fintype Coordinate]
    {Invariant : Type uInvariant} [Fintype Invariant]
    {Frame : Type uFrame}
    {Observation : Type uObservation}
    (observe :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame →
        Observation)
    (left right :
      OCGeneratorMechanicsObservation Generator Coordinate Invariant Frame)
    (incidence : Generator → Bool)
    (leftFeasible :
      GeneratorIncidenceFeasible left.toConstraintSystem incidence)
    (rightFeasible :
      GeneratorIncidenceFeasible right.toConstraintSystem incidence)
    (sameObservation : observe left = observe right)
    (differentSuccessor :
      generatorSuccessorState left.toConstraintSystem incidence ≠
        generatorSuccessorState right.toConstraintSystem incidence) :
    ¬ ∃ decoder : Observation → (Generator → Bool) → (Coordinate → Int),
      ∀ world candidate,
        GeneratorIncidenceFeasible world.toConstraintSystem candidate →
        decoder (observe world) candidate =
          generatorSuccessorState world.toConstraintSystem candidate := by
  rintro ⟨decoder, exactDecoder⟩
  have sameDecoded := congrArg (fun observation => decoder observation incidence)
    sameObservation
  change decoder (observe left) incidence =
    decoder (observe right) incidence at sameDecoded
  rw [exactDecoder left incidence leftFeasible,
    exactDecoder right incidence rightFeasible] at sameDecoded
  exact differentSuccessor sameDecoded

def oneGeneratorFrameWorld (frame : Bool) :
    OCGeneratorMechanicsObservation (Fin 1) (Fin 1) Unit Bool where
  kLevel := fun _ => 0
  kEnabled := fun _ => true
  mProjection := fun _ => 0
  operatorEffect := fun _ _ => if frame then 2 else 1
  contextLowerBound := fun _ => 0
  contextUpperBound := fun _ => 2
  continuationCoefficient := fun _ _ => 0
  continuationTarget := fun _ => 0
  contextMandatory := fun _ => true
  contextRequires := fun _ _ => false
  contextExcludes := fun _ _ => false
  frame := frame

def oneGeneratorPresent (_ : Fin 1) : Bool := true

/-- K-level and current M-projection agree across the two worlds, while the
omitted frame changes the operator effect. -/
theorem frame_worlds_have_same_k_and_m_projection :
    (oneGeneratorFrameWorld false).kLevel =
        (oneGeneratorFrameWorld true).kLevel ∧
      (oneGeneratorFrameWorld false).mProjection =
        (oneGeneratorFrameWorld true).mProjection := by
  decide

theorem oneGeneratorPresent_feasible_in_both_frames :
    GeneratorIncidenceFeasible
        (oneGeneratorFrameWorld false).toConstraintSystem oneGeneratorPresent ∧
      GeneratorIncidenceFeasible
        (oneGeneratorFrameWorld true).toConstraintSystem oneGeneratorPresent := by
  constructor
  · apply (generatorIncidenceFeasibleBool_eq_true_iff
      (oneGeneratorFrameWorld false).toConstraintSystem
      oneGeneratorPresent).mp
    decide
  · apply (generatorIncidenceFeasibleBool_eq_true_iff
      (oneGeneratorFrameWorld true).toConstraintSystem
      oneGeneratorPresent).mp
    decide

theorem frame_shift_changes_exact_successor :
    generatorSuccessorState
        (oneGeneratorFrameWorld false).toConstraintSystem oneGeneratorPresent 0 = 1 ∧
      generatorSuccessorState
        (oneGeneratorFrameWorld true).toConstraintSystem oneGeneratorPresent 0 = 2 := by
  decide

/-- Concrete no-go: K-level plus current M-projection cannot be a universally
exact predictor when frame-dependent operator effects are possible. -/
theorem k_and_m_projection_without_frame_do_not_identify_successor :
    ¬ ∃ decoder : ((Fin 1 → Nat) × (Fin 1 → Int)) →
          (Fin 1 → Bool) → (Fin 1 → Int),
      ∀ world : OCGeneratorMechanicsObservation (Fin 1) (Fin 1) Unit Bool,
        ∀ incidence,
          GeneratorIncidenceFeasible world.toConstraintSystem incidence →
          decoder (world.kLevel, world.mProjection) incidence =
            generatorSuccessorState world.toConstraintSystem incidence := by
  apply oc_observation_alias_blocks_exact_successor_decoder
    (fun world => (world.kLevel, world.mProjection))
    (oneGeneratorFrameWorld false) (oneGeneratorFrameWorld true)
    oneGeneratorPresent
    oneGeneratorPresent_feasible_in_both_frames.1
    oneGeneratorPresent_feasible_in_both_frames.2
  · exact congrArg₂ Prod.mk frame_worlds_have_same_k_and_m_projection.1
      frame_worlds_have_same_k_and_m_projection.2
  · intro equalSuccessor
    have coordinateEquality := congrFun equalSuccessor 0
    rw [frame_shift_changes_exact_successor.1,
      frame_shift_changes_exact_successor.2] at coordinateEquality
    omega

end OCKIndividuationMSpaceComposition
