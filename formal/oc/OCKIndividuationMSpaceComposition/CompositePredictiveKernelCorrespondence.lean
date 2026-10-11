import OCKIndividuationMSpaceComposition.ContinuationAwarePredictiveKernel

namespace OCKIndividuationMSpaceComposition

universe uModel uOutcome uExecution

/-!
# Correspondence with a mature composite predictive surface

The outer possible/necessary/set-valued and robust semantics of the v91 OC
kernel are mature constructions.  This module forgets the internal OC context
types while preserving their already-computed transport flag.  It proves the
exact extensional correspondence and localizes any possible predictive gain to
a difference in the admitted model class or outcome map, rather than to a new
name for the same set-valued surface.
-/

/-- The strongest fair outer composite needed for the correspondence.  Its
components may be implemented by partial identification/reachability,
calibrated set prediction, robust control and a supplied transport decision. -/
structure MatureCompositePredictiveKernel where
  Model : Type uModel
  Outcome : Type uOutcome
  Execution : Type uExecution
  admissibleModel : Model → Prop
  predictedOutcome : Model → Outcome
  modelExists : ∃ model, admissibleModel model
  admissibleExecution : Execution → Prop
  executionOutcome : Execution → Outcome
  transportAllowed : Prop

def CompositePossibleFuture
    (kernel : MatureCompositePredictiveKernel)
    (outcome : kernel.Outcome) : Prop :=
  ∃ model, kernel.admissibleModel model ∧
    kernel.predictedOutcome model = outcome

def CompositeNecessaryFuture
    (kernel : MatureCompositePredictiveKernel)
    (outcome : kernel.Outcome) : Prop :=
  ∀ model, kernel.admissibleModel model →
    kernel.predictedOutcome model = outcome

def CompositeSoundPredictor
    (kernel : MatureCompositePredictiveKernel)
    (predictor : kernel.Outcome → Prop) : Prop :=
  ∀ model, kernel.admissibleModel model →
    predictor (kernel.predictedOutcome model)

def CompositeRobustOutcome
    (kernel : MatureCompositePredictiveKernel)
    (outcome : kernel.Outcome) : Prop :=
  ∀ execution, kernel.admissibleExecution execution →
    kernel.executionOutcome execution = outcome

/-- Forget the internal OC context carriers after they have determined the
typed transport permission. -/
def ContinuationAwarePredictiveAdmissibilityKernel.toMatureComposite
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel) :
    MatureCompositePredictiveKernel where
  Model := kernel.Model
  Outcome := kernel.Outcome
  Execution := kernel.Execution
  admissibleModel := kernel.admissibleModel
  predictedOutcome := kernel.predictedOutcome
  modelExists := kernel.modelExists
  admissibleExecution := kernel.admissibleExecution
  executionOutcome := kernel.executionOutcome
  transportAllowed := KernelTransportAllowed kernel

theorem mature_composite_preserves_possible_future
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (outcome : kernel.Outcome) :
    CompositePossibleFuture kernel.toMatureComposite outcome ↔
      KernelPossibleFuture kernel outcome := by
  rfl

theorem mature_composite_preserves_necessary_future
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (outcome : kernel.Outcome) :
    CompositeNecessaryFuture kernel.toMatureComposite outcome ↔
      KernelNecessaryFuture kernel outcome := by
  rfl

theorem mature_composite_preserves_sound_predictor
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (predictor : kernel.Outcome → Prop) :
    CompositeSoundPredictor kernel.toMatureComposite predictor ↔
      KernelSoundPredictor kernel predictor := by
  rfl

theorem mature_composite_preserves_robust_outcome
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel)
    (outcome : kernel.Outcome) :
    CompositeRobustOutcome kernel.toMatureComposite outcome ↔
      KernelRobustOutcome kernel outcome := by
  rfl

theorem mature_composite_transport_residual_is_oc_compatibility
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel) :
    kernel.toMatureComposite.transportAllowed ↔
      Nonempty (ContextCompatibility kernel.sourceContext kernel.targetContext) ∧
      KernelCausalTransportAvailable kernel := by
  exact kernel_transport_allowed_iff_components kernel

/-- Exact forgetting leaves no strict possible-future difference. -/
theorem no_strict_possible_future_gain_over_exact_mature_composite
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel) :
    ¬ ∃ outcome, KernelPossibleFuture kernel outcome ∧
      ¬ CompositePossibleFuture kernel.toMatureComposite outcome := by
  rintro ⟨outcome, possible, excluded⟩
  exact excluded ((mature_composite_preserves_possible_future kernel outcome).mpr possible)

/-- A strict possible-set difference between two same-carrier profiles must
come from a difference in model admission or in the outcome map. -/
theorem strict_possible_difference_requires_contract_difference
    {Model : Type uModel} {Outcome : Type uOutcome}
    (firstAdmissible secondAdmissible : Model → Prop)
    (firstOutcome secondOutcome : Model → Outcome)
    (strict : ∃ outcome,
      (∃ model, firstAdmissible model ∧ firstOutcome model = outcome) ∧
      ¬ (∃ model, secondAdmissible model ∧ secondOutcome model = outcome)) :
    (∃ model, firstAdmissible model ∧ ¬ secondAdmissible model) ∨
      ∃ model, firstAdmissible model ∧ firstOutcome model ≠ secondOutcome model := by
  classical
  rcases strict with ⟨outcome, ⟨model, firstAdmitted, firstPredicted⟩, excluded⟩
  by_cases secondAdmitted : secondAdmissible model
  · right
    refine ⟨model, firstAdmitted, ?_⟩
    intro samePrediction
    apply excluded
    exact ⟨model, secondAdmitted, samePrediction.symm.trans firstPredicted⟩
  · left
    exact ⟨model, firstAdmitted, secondAdmitted⟩

/-- The complete correspondence result: the outer predictive and robust
surface is conservative; the typed compatibility contract is the explicit
OC-specific residual at this abstraction level. -/
theorem continuation_aware_kernel_mature_composite_correspondence
    (kernel : ContinuationAwarePredictiveAdmissibilityKernel) :
    (∀ outcome, CompositePossibleFuture kernel.toMatureComposite outcome ↔
      KernelPossibleFuture kernel outcome) ∧
    (∀ outcome, CompositeNecessaryFuture kernel.toMatureComposite outcome ↔
      KernelNecessaryFuture kernel outcome) ∧
    (∀ predictor, CompositeSoundPredictor kernel.toMatureComposite predictor ↔
      KernelSoundPredictor kernel predictor) ∧
    (∀ outcome, CompositeRobustOutcome kernel.toMatureComposite outcome ↔
      KernelRobustOutcome kernel outcome) ∧
    (kernel.toMatureComposite.transportAllowed ↔
      Nonempty (ContextCompatibility kernel.sourceContext kernel.targetContext) ∧
      KernelCausalTransportAvailable kernel) := by
  exact ⟨mature_composite_preserves_possible_future kernel,
    mature_composite_preserves_necessary_future kernel,
    mature_composite_preserves_sound_predictor kernel,
    mature_composite_preserves_robust_outcome kernel,
    mature_composite_transport_residual_is_oc_compatibility kernel⟩

end OCKIndividuationMSpaceComposition
