import OCMaturityCompletionCycle.IdentityAssembly
import OCMaturityCompletionCycle.StochasticOpen

/-!
# Experimental-interface refinement and context transport

Experimental contexts index test families and assembly encoders.  They are not
physical reference frames.  Naturality is an additional factor-map certificate;
it is not inferred from reuse of a symbol or object name.
-/

namespace OCMaturityCompletionCycle

universe uHistory uTest uOutcome uContext uOccurrence uState uTarget

/-- Equality of every admitted future-test result in one interface. -/
def PredictiveEquivalent
    {History : Type uHistory}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    (law : History → Test → Outcome)
    (interface : Set Test)
    (left right : History) : Prop :=
  ∀ test, test ∈ interface → law left test = law right test

/-- Refining an interface can split predictive classes but cannot merge them. -/
theorem predictiveEquivalence_antitone
    {History : Type uHistory}
    {Test : Type uTest}
    {Outcome : Type uOutcome}
    (law : History → Test → Outcome)
    {coarse fine : Set Test}
    (refines : coarse ⊆ fine) :
    RelationRefines
      (PredictiveEquivalent law fine)
      (PredictiveEquivalent law coarse) := by
  intro left right equivalent test inCoarse
  exact equivalent test (refines inCoarse)

/-- The used range of an encoder; no claim is made about unused labels. -/
def UsedClass
    {Occurrence : Type uOccurrence}
    {State : Type uState}
    (encode : Occurrence → State) :=
  {state : State // ∃ occurrence, encode occurrence = state}

/-- Exact transport from one assembly encoder to another on the used range. -/
structure UsedContextTransport
    {Occurrence : Type uOccurrence}
    {SourceState : Type uState}
    {TargetState : Type uTarget}
    (source : Occurrence → SourceState)
    (target : Occurrence → TargetState) where
  map : UsedClass source → TargetState
  naturality : ∀ occurrence,
    map ⟨source occurrence, occurrence, rfl⟩ = target occurrence

/--
A context transport exists exactly when the source encoder kernel refines the
target encoder kernel.  This is the used-range factor-map boundary.
-/
theorem usedContextTransport_iff_kernelRefinement
    {Occurrence : Type uOccurrence}
    {SourceState : Type uState}
    {TargetState : Type uTarget}
    (source : Occurrence → SourceState)
    (target : Occurrence → TargetState) :
    Nonempty (UsedContextTransport source target) ↔
      CrossUniverseKernelRefines source target := by
  constructor
  · rintro ⟨transport⟩ left right sameSource
    have leftNaturality := transport.naturality left
    have rightNaturality := transport.naturality right
    have sameUsed :
        (⟨source left, left, rfl⟩ : UsedClass source) =
          ⟨source right, right, rfl⟩ := by
      exact Subtype.ext sameSource
    exact leftNaturality.symm.trans
      ((congrArg transport.map sameUsed).trans rightNaturality)
  · intro refinement
    classical
    let transportMap : UsedClass source → TargetState := fun used =>
      target (Classical.choose used.property)
    refine ⟨{
      map := transportMap
      naturality := ?_
    }⟩
    intro occurrence
    dsimp [transportMap]
    apply refinement
    exact (Classical.choose_spec
      (show ∃ candidate, source candidate = source occurrence from
        ⟨occurrence, rfl⟩))

/-- A concrete obstruction to functorial context transport. -/
def ContextTransportObstruction
    {Occurrence : Type uOccurrence}
    {SourceState : Type uState}
    {TargetState : Type uTarget}
    (source : Occurrence → SourceState)
    (target : Occurrence → TargetState) : Prop :=
  ∃ left right,
    source left = source right ∧ target left ≠ target right

theorem contextTransportObstruction_no_go
    {Occurrence : Type uOccurrence}
    {SourceState : Type uState}
    {TargetState : Type uTarget}
    (source : Occurrence → SourceState)
    (target : Occurrence → TargetState)
    (obstruction : ContextTransportObstruction source target) :
    IsEmpty (UsedContextTransport source target) := by
  refine ⟨?_⟩
  intro transport
  rcases obstruction with ⟨left, right, sameSource, differentTarget⟩
  have refinement :=
    (usedContextTransport_iff_kernelRefinement source target).1 ⟨transport⟩
  exact differentTarget (refinement sameSource)

/-- A context-indexed family of assembly encoders. -/
structure ContextIndexedAssembly
    (Occurrence : Type uOccurrence)
    (Context : Type uContext) where
  State : Context → Type uState
  encode : (context : Context) → Occurrence → State context

/-- One declared refinement arrow. -/
structure ExperimentalContextMorphism (Context : Type uContext) where
  source : Context
  target : Context

/-- Naturality data for one context arrow, restricted to used source classes. -/
structure AssemblyNaturality
    {Occurrence : Type uOccurrence}
    {Context : Type uContext}
    (assembly : ContextIndexedAssembly Occurrence Context)
    (arrow : ExperimentalContextMorphism Context) where
  transport :
    UsedContextTransport (assembly.encode arrow.source)
      (assembly.encode arrow.target)

/-- Used-range naturality composes without inventing values for unused classes. -/
theorem usedContextTransport_composes
    {Occurrence : Type uOccurrence}
    {FirstState : Type uState}
    {MiddleState : Type uTarget}
    {LastState : Type uOutcome}
    (first : Occurrence → FirstState)
    (middle : Occurrence → MiddleState)
    (last : Occurrence → LastState)
    (firstTransport : UsedContextTransport first middle)
    (secondTransport : UsedContextTransport middle last) :
    Nonempty (UsedContextTransport first last) := by
  apply (usedContextTransport_iff_kernelRefinement first last).2
  have firstRefinement :=
    (usedContextTransport_iff_kernelRefinement first middle).1 ⟨firstTransport⟩
  have secondRefinement :=
    (usedContextTransport_iff_kernelRefinement middle last).1 ⟨secondTransport⟩
  intro left right sameFirst
  exact secondRefinement (firstRefinement sameFirst)

/-- The composed certificate has the expected occurrence-level naturality law. -/
theorem context_transport_composes_on_occurrences
    {Occurrence : Type uOccurrence}
    {FirstState : Type uState}
    {MiddleState : Type uTarget}
    {LastState : Type uOutcome}
    (first : Occurrence → FirstState)
    (middle : Occurrence → MiddleState)
    (last : Occurrence → LastState)
    (firstTransport : UsedContextTransport first middle)
    (secondTransport : UsedContextTransport middle last) :
    ∃ composed : UsedContextTransport first last,
      ∀ occurrence,
        composed.map ⟨first occurrence, occurrence, rfl⟩ = last occurrence := by
  rcases usedContextTransport_composes first middle last
    firstTransport secondTransport with ⟨composed⟩
  exact ⟨composed, composed.naturality⟩

/-- The crossing fixture has no strict used-range transport in either direction. -/
theorem crossing_contexts_have_no_strict_transport :
    IsEmpty (UsedContextTransport rowAssembly columnAssembly) ∧
      IsEmpty (UsedContextTransport columnAssembly rowAssembly) := by
  constructor
  · refine ⟨?_⟩
    intro transport
    exact crossing_context_partitions_are_incomparable.1
      ((usedContextTransport_iff_kernelRefinement
        rowAssembly columnAssembly).1 ⟨transport⟩)
  · refine ⟨?_⟩
    intro transport
    exact crossing_context_partitions_are_incomparable.2
      ((usedContextTransport_iff_kernelRefinement
        columnAssembly rowAssembly).1 ⟨transport⟩)

/-! ## Support and law stitching for finite path presentations -/

def PathSupportSurjective
    {FinePath : Type uHistory}
    {MacroPath : Type uTest}
    (project : FinePath → MacroPath) : Prop :=
  Function.Surjective project

def PathLawPushforward
    {FinePath : Type uHistory}
    {MacroPath : Type uTest}
    [Fintype FinePath]
    [DecidableEq MacroPath]
    (fineMass : FinePath → ℚ)
    (project : FinePath → MacroPath)
    (macroPath : MacroPath) : ℚ :=
  ∑ finePath, if project finePath = macroPath then fineMass finePath else 0

def PathLawStitching
    {FinePath : Type uHistory}
    {MacroPath : Type uTest}
    [Fintype FinePath]
    [DecidableEq MacroPath]
    (fineMass : FinePath → ℚ)
    (macroMass : MacroPath → ℚ)
    (project : FinePath → MacroPath) : Prop :=
  ∀ macroPath,
    macroMass macroPath = PathLawPushforward fineMass project macroPath

/-- A right inverse is an explicit coherent lift for every admitted macro path. -/
structure CoherentPathTransport
    (FinePath : Type uHistory)
    (MacroPath : Type uTest) where
  project : FinePath → MacroPath
  lift : MacroPath → FinePath
  project_lift : Function.RightInverse lift project

/-- Coherent support transport plus exact pushed-forward path law. -/
structure CoherentPathLawTransport
    (FinePath : Type uHistory)
    (MacroPath : Type uTest)
    [Fintype FinePath]
    [DecidableEq MacroPath]
    (fineMass : FinePath → ℚ)
    (macroMass : MacroPath → ℚ) extends
      CoherentPathTransport FinePath MacroPath where
  law_stitching : PathLawStitching fineMass macroMass toCoherentPathTransport.project

theorem coherentPathTransport_has_zero_support_defect
    {FinePath : Type uHistory}
    {MacroPath : Type uTest}
    (transport : CoherentPathTransport FinePath MacroPath) :
    PathSupportSurjective transport.project := by
  exact transport.project_lift.surjective

/-- A coherent law transport has both zero support and zero law defect. -/
theorem coherentPathLawTransport_has_zero_support_and_law_defect
    {FinePath : Type uHistory}
    {MacroPath : Type uTest}
    [Fintype FinePath]
    [DecidableEq MacroPath]
    (fineMass : FinePath → ℚ)
    (macroMass : MacroPath → ℚ)
    (transport : CoherentPathLawTransport FinePath MacroPath fineMass macroMass) :
    PathSupportSurjective transport.project ∧
      PathLawStitching fineMass macroMass transport.project := by
  exact ⟨transport.project_lift.surjective, transport.law_stitching⟩

/-- Without path surjectivity there is an explicit unliftable macro path. -/
theorem nonSurjectivePathTransport_has_stitchingObstruction
    {FinePath : Type uHistory}
    {MacroPath : Type uTest}
    (project : FinePath → MacroPath)
    (notSurjective : ¬ PathSupportSurjective project) :
    ∃ macroPath, ∀ finePath, project finePath ≠ macroPath := by
  simpa [PathSupportSurjective, Function.Surjective, not_exists, not_forall]
    using notSurjective

def firstPathLaw : Bool → ℚ
  | false => 1 / 3
  | true => 2 / 3

def secondPathLaw : Bool → ℚ
  | false => 2 / 3
  | true => 1 / 3

theorem sum_bool_mass (mass : Bool → ℚ) :
    (∑ path, mass path) = mass false + mass true := by
  simp [add_comm]

/-- Two path laws can have identical positive support yet different weights. -/
theorem path_support_equality_does_not_determine_law :
    (∀ path, 0 < firstPathLaw path ↔ 0 < secondPathLaw path) ∧
      ¬ PathLawStitching firstPathLaw secondPathLaw id := by
  constructor
  · intro path
    cases path <;> norm_num [firstPathLaw, secondPathLaw]
  · intro stitching
    have falsePath := stitching false
    norm_num [PathLawPushforward, firstPathLaw, secondPathLaw,
      sum_bool_mass] at falsePath

end OCMaturityCompletionCycle
