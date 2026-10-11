import OCKIndividuationMSpaceComposition.SequentialGeneratorReachability
import OCKIndividuationMSpaceComposition.TypedTransportComparativeBoundary

namespace OCKIndividuationMSpaceComposition

open OCMaturityCompletionCycle

universe
  uModel uOutcome uExecution uCausalContext uInvariant
  uState uInput uEvidence uTask uProjection uBoundary uConstraint uScope uFrame

/-!
# OC continuation-aware predictive admissibility kernel

This bundled public surface composes mature partial-identification,
set-valued-prediction, reachability, causal-transport and robust-execution
mathematics with OC's typed context and continuation contract.  An `Outcome`
may itself be a state, path, distribution or set, so the outer deterministic
candidate map does not exclude stochastic or set-valued inner semantics.
-/

/-- The domain-generic flagship object.  All scientific carrier types are
bundled so a kernel value fixes one registered information class. -/
structure ContinuationAwarePredictiveAdmissibilityKernel where
  State : Type uState
  Input : Type uInput
  Evidence : Type uEvidence
  Task : Type uTask
  Projection : Type uProjection
  Boundary : Type uBoundary
  Constraint : Type uConstraint
  Scope : Type uScope
  Frame : Type uFrame
  Model : Type uModel
  Outcome : Type uOutcome
  Execution : Type uExecution
  CausalContext : Type uCausalContext
  causalContextFintype : Fintype CausalContext
  sourceContext :
    ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame
  targetContext :
    ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame
  admissibleModel : Model → Prop
  predictedOutcome : Model → Outcome
  modelExists : ∃ model, admissibleModel model
  admissibleExecution : Execution → Prop
  executionOutcome : Execution → Outcome

/-- Union of outcomes over every registered admissible model. -/
def KernelPossibleFuture
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (outcome : kernel.Outcome) : Prop :=
  ∃ model, kernel.admissibleModel model ∧
    kernel.predictedOutcome model = outcome

/-- Intersection of outcomes over every registered admissible model. -/
def KernelNecessaryFuture
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (outcome : kernel.Outcome) : Prop :=
  ∀ model, kernel.admissibleModel model →
    kernel.predictedOutcome model = outcome

/-- A same-information predictor is sound exactly when it contains every
admissible model's outcome. -/
def KernelSoundPredictor
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (predictor : kernel.Outcome → Prop) : Prop :=
  ∀ model, kernel.admissibleModel model → predictor (kernel.predictedOutcome model)

/-- Mandatory abstention from a point prediction. -/
def KernelAbstains
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel) : Prop :=
  ∃ first second,
    KernelPossibleFuture kernel first ∧
    KernelPossibleFuture kernel second ∧ first ≠ second

/-- Exact typed transport permission. -/
def KernelTransportAllowed
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel) : Prop := by
  letI := kernel.causalContextFintype
  exact Nonempty (TypedExactCausalContinuationTransport
    kernel.sourceContext kernel.targetContext kernel.CausalContext)

/-- Availability of the mature causal component alone. -/
def KernelCausalTransportAvailable
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel) : Prop := by
  letI := kernel.causalContextFintype
  exact Nonempty (StaticEffectTransportContract kernel.CausalContext)

/-- Robustness over the registered execution envelope. -/
def KernelRobustOutcome
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (outcome : kernel.Outcome) : Prop :=
  ∀ execution, kernel.admissibleExecution execution →
    kernel.executionOutcome execution = outcome

/-- Explicit failure witness for robustness. -/
def KernelCounterprofile
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (outcome : kernel.Outcome) : Prop :=
  ∃ execution, kernel.admissibleExecution execution ∧
    kernel.executionOutcome execution ≠ outcome

/-- Formal soundness. -/
theorem admissible_model_outcome_is_possible
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (model : kernel.Model) (admissible : kernel.admissibleModel model) :
    KernelPossibleFuture kernel (kernel.predictedOutcome model) := by
  exact ⟨model, admissible, rfl⟩

/-- Exactness: nonemptiness makes necessity equivalent to a singleton possible
set. -/
theorem necessary_future_iff_possible_singleton
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (outcome : kernel.Outcome) :
    KernelNecessaryFuture kernel outcome ↔
      ∀ candidate, KernelPossibleFuture kernel candidate ↔ candidate = outcome := by
  constructor
  · intro necessary candidate
    constructor
    · rintro ⟨model, admissible, predicted⟩
      exact predicted.symm.trans (necessary model admissible)
    · intro equal
      subst candidate
      rcases kernel.modelExists with ⟨model, admissible⟩
      exact ⟨model, admissible, necessary model admissible⟩
  · intro singleton model admissible
    exact (singleton (kernel.predictedOutcome model)).mp
      (admissible_model_outcome_is_possible kernel model admissible)

/-- Pointwise information sharpness relative to the registered information
class. -/
theorem possible_future_is_minimal_sound_predictor
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (predictor : kernel.Outcome → Prop)
    (sound : KernelSoundPredictor kernel predictor)
    (outcome : kernel.Outcome) (possible : KernelPossibleFuture kernel outcome) :
    predictor outcome := by
  rcases possible with ⟨model, admissible, predicted⟩
  rw [← predicted]
  exact sound model admissible

/-- Sharp no-go: excluding one possible future makes a same-information
predictor unsound. -/
theorem excluding_possible_future_is_unsound
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (predictor : kernel.Outcome → Prop) (outcome : kernel.Outcome)
    (possible : KernelPossibleFuture kernel outcome)
    (excluded : ¬ predictor outcome) :
    ¬ KernelSoundPredictor kernel predictor := by
  intro sound
  exact excluded (possible_future_is_minimal_sound_predictor
    kernel predictor sound outcome possible)

/-- Ambiguity rules out every exact necessary point. -/
theorem abstention_blocks_every_exact_point
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (ambiguous : KernelAbstains kernel) :
    ¬ ∃ outcome, KernelNecessaryFuture kernel outcome := by
  rintro ⟨outcome, necessary⟩
  rcases ambiguous with ⟨first, second, firstPossible, secondPossible, distinct⟩
  have singleton := (necessary_future_iff_possible_singleton kernel outcome).mp necessary
  have firstEqual := (singleton first).mp firstPossible
  have secondEqual := (singleton second).mp secondPossible
  exact distinct (firstEqual.trans secondEqual.symm)

/-- Conversely, if no two possible outcomes differ, a necessary point exists. -/
theorem no_abstention_implies_exact_point
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (unambiguous : ¬ KernelAbstains kernel) :
    ∃ outcome, KernelNecessaryFuture kernel outcome := by
  rcases kernel.modelExists with ⟨selected, selectedAdmissible⟩
  refine ⟨kernel.predictedOutcome selected, ?_⟩
  intro model admissible
  by_contra distinct
  exact unambiguous ⟨kernel.predictedOutcome selected,
    kernel.predictedOutcome model,
    admissible_model_outcome_is_possible kernel selected selectedAdmissible,
    admissible_model_outcome_is_possible kernel model admissible,
    (fun equal => distinct equal.symm)⟩

/-- Robustness gives the outcome for each admitted execution. -/
theorem robust_outcome_holds_for_admissible_execution
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (outcome : kernel.Outcome) (robust : KernelRobustOutcome kernel outcome)
    (execution : kernel.Execution)
    (admissible : kernel.admissibleExecution execution) :
    kernel.executionOutcome execution = outcome :=
  robust execution admissible

/-- The robustness boundary is sharp. -/
theorem not_robust_iff_counterprofile
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (outcome : kernel.Outcome) :
    ¬ KernelRobustOutcome kernel outcome ↔ KernelCounterprofile kernel outcome := by
  classical
  constructor
  · intro notRobust
    by_contra noCounterprofile
    apply notRobust
    intro execution admissible
    by_contra violates
    exact noCounterprofile ⟨execution, admissible, violates⟩
  · rintro ⟨execution, admissible, violates⟩ robust
    exact violates (robust execution admissible)

/-- Typed transport contains exactly the mature causal component and OC
context compatibility. -/
theorem kernel_transport_allowed_iff_components
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel) :
    KernelTransportAllowed kernel ↔
      Nonempty (ContextCompatibility kernel.sourceContext kernel.targetContext) ∧
      KernelCausalTransportAvailable kernel := by
  letI := kernel.causalContextFintype
  exact typed_exact_transport_exists_iff_components_exist

/-- A frame mismatch blocks the typed flag although causal transport exists. -/
theorem causal_transport_without_frame_continuity_is_not_kernel_transport
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (causalAvailable : KernelCausalTransportAvailable kernel)
    (frameMismatch : kernel.sourceContext.frame ≠ kernel.targetContext.frame) :
    KernelCausalTransportAvailable kernel ∧ ¬ KernelTransportAllowed kernel := by
  letI := kernel.causalContextFintype
  rcases causalAvailable with ⟨causal⟩
  exact causal_transport_alone_is_strictly_weaker_at_frame_mismatch
    causal frameMismatch

/-- The v88 generator-successor system is an exact flagship instance. -/
def generatorSuccessorPredictiveKernel
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {Generator : Type uModel} {Coordinate : Type uOutcome}
    {Invariant : Type uInvariant} {CausalContext : Type uCausalContext}
    [Fintype Generator] [Fintype Coordinate] [Fintype Invariant]
    [Fintype CausalContext]
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (nonempty : ∃ incidence, GeneratorIncidenceFeasible system incidence) :
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
  Model := Generator → Bool
  Outcome := Coordinate → Int
  Execution := Generator → Bool
  CausalContext := CausalContext
  causalContextFintype := inferInstance
  sourceContext := source
  targetContext := target
  admissibleModel := GeneratorIncidenceFeasible system
  predictedOutcome := generatorSuccessorState system
  modelExists := nonempty
  admissibleExecution := GeneratorIncidenceFeasible system
  executionOutcome := generatorSuccessorState system

theorem generator_successor_possible_iff_feasible_image
    {State : Type uState} {Input : Type uInput} {Evidence : Type uEvidence}
    {Task : Type uTask} {Projection : Type uProjection}
    {Boundary : Type uBoundary} {Constraint : Type uConstraint}
    {Scope : Type uScope} {Frame : Type uFrame}
    {Generator : Type uModel} {Coordinate : Type uOutcome}
    {Invariant : Type uInvariant} {CausalContext : Type uCausalContext}
    [Fintype Generator] [Fintype Coordinate] [Fintype Invariant]
    [Fintype CausalContext]
    (source target :
      ContinuationContext State Input Evidence Task Projection Boundary Constraint Scope Frame)
    (system : GeneratorSuccessorConstraintSystem Generator Coordinate Invariant)
    (nonempty : ∃ incidence, GeneratorIncidenceFeasible system incidence)
    (outcome : Coordinate → Int) :
    KernelPossibleFuture
        (generatorSuccessorPredictiveKernel (CausalContext := CausalContext)
          source target system nonempty) outcome ↔
      ∃ incidence, GeneratorIncidenceFeasible system incidence ∧
        generatorSuccessorState system incidence = outcome := by
  rfl

/-- One theorem exposing the four domain-generic flagship guarantees. -/
theorem continuation_aware_predictive_kernel_guarantees
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel) :
    (∀ model, kernel.admissibleModel model →
      KernelPossibleFuture kernel (kernel.predictedOutcome model)) ∧
    (∀ outcome, KernelNecessaryFuture kernel outcome ↔
      ∀ candidate, KernelPossibleFuture kernel candidate ↔ candidate = outcome) ∧
    (∀ predictor, KernelSoundPredictor kernel predictor →
      ∀ outcome, KernelPossibleFuture kernel outcome → predictor outcome) ∧
    (∀ outcome execution, KernelRobustOutcome kernel outcome →
      kernel.admissibleExecution execution →
      kernel.executionOutcome execution = outcome) := by
  exact ⟨admissible_model_outcome_is_possible kernel,
    necessary_future_iff_possible_singleton kernel,
    possible_future_is_minimal_sound_predictor kernel,
    (fun outcome execution robust admissible =>
      robust_outcome_holds_for_admissible_execution
        kernel outcome robust execution admissible)⟩

/-- Provenance-only and endpoint-only strict separations in one public result. -/
theorem flagship_provenance_and_endpoint_strict_separation :
    (LineageGenerated
        (fun source target => ∃ input, bridgeTransition source input target)
        .initial .terminal ∧
      ¬ Continues (bridgeContext false false) .initial .terminal) ∧
    (GeneratorIncidenceFeasible (twoGeneratorEndpointSystem 0 1)
        bothGeneratorsPresent ∧
      ¬ SequentiallyGeneratorReachable (twoGeneratorEndpointSystem 0 1)
        twoGeneratorEnumeration alwaysDynamicallyEnabled bothGeneratorsPresent) := by
  exact ⟨provenance_lineage_projection_has_no_general_continuation_converse,
    endpoint_feasibility_does_not_imply_sequential_reachability⟩

end OCKIndividuationMSpaceComposition
