import OCKIndividuationMSpaceComposition.TaskConditionedOptics
import OCKIndividuationMSpaceComposition.KMObservationAcquisitionValue
import OCKIndividuationMSpaceComposition.PhysicalEpistemicMSpace

namespace OCKIndividuationMSpaceComposition

universe uWorld uModel uValue

/-!
# Task-optic to model-class dynamics

This module closes the missing formal bridge between task-conditioned optics
and the OC/KM predictive model class.  An optic observation filters a prior
model class by observational compatibility with the actual world.  A refined
optic therefore contracts the admitted class and cannot widen its sharp
prediction band.  The converse strictness claim is false: a refinement may add
distinctions which are absent from the current prior class.

Model-class revision is a different operation.  Even with the optic and the
actual observation fixed, adding an observationally aliased model can reopen
an epistemic prediction which the smaller class excluded.  This is the finite
positive mechanism requested by the physical/epistemic M-space programme; it
does not assert that the new model is physically sound.
-/

/-- Models admitted by a prior class and observationally compatible with the
actual world under the declared optic. -/
def OpticPosteriorAdmits
    {World : Type uWorld} {Model : Type uModel}
    (optic : TaskConditionedOptic World)
    (modelWorld : Model → World)
    (priorAdmits : Model → Prop)
    (actual : World)
    (model : Model) : Prop :=
  priorAdmits model ∧ optic.observe (modelWorld model) = optic.observe actual

/-- A refined optic can only contract the observationally compatible part of
the same prior model class. -/
theorem optic_refinement_contracts_admitted_model_class
    {World : Type uWorld} {Model : Type uModel}
    {coarse fine : TaskConditionedOptic World}
    (refinement : OpticRefinement coarse fine)
    (modelWorld : Model → World)
    (priorAdmits : Model → Prop)
    (actual : World) :
    ∀ model,
      OpticPosteriorAdmits fine modelWorld priorAdmits actual model →
        OpticPosteriorAdmits coarse modelWorld priorAdmits actual model := by
  intro model admitted
  refine ⟨admitted.1, ?_⟩
  calc
    coarse.observe (modelWorld model) =
        refinement.coarsen (fine.observe (modelWorld model)) :=
      refinement.commutes (modelWorld model)
    _ = refinement.coarsen (fine.observe actual) :=
      congrArg refinement.coarsen admitted.2
    _ = coarse.observe actual := (refinement.commutes actual).symm

/-- The task-optic bridge to an operational numerical prediction: when both
posterior classes have sharp bands, optic refinement cannot widen the band. -/
theorem optic_refinement_narrows_sharp_prediction_band
    {World : Type uWorld} {Model : Type uModel}
    {coarse fine : TaskConditionedOptic World}
    (refinement : OpticRefinement coarse fine)
    (modelWorld : Model → World)
    (priorAdmits : Model → Prop)
    (actual : World)
    (value : Model → ℚ)
    (coarseBand : ObservationSharpPredictionBand
      (OpticPosteriorAdmits coarse modelWorld priorAdmits actual) value)
    (fineBand : ObservationSharpPredictionBand
      (OpticPosteriorAdmits fine modelWorld priorAdmits actual) value) :
    fineBand.width ≤ coarseBand.width := by
  exact ObservationSharpPredictionBand.refinement_narrows
    (optic_refinement_contracts_admitted_model_class refinement
      modelWorld priorAdmits actual)
    coarseBand fineBand

/-- Equivalently, the structural acquisition value of a refined task optic is
nonnegative whenever the sharp posterior bands exist. -/
theorem task_optic_refinement_has_nonnegative_acquisition_value
    {World : Type uWorld} {Model : Type uModel}
    {coarse fine : TaskConditionedOptic World}
    (refinement : OpticRefinement coarse fine)
    (modelWorld : Model → World)
    (priorAdmits : Model → Prop)
    (actual : World)
    (value : Model → ℚ)
    (coarseBand : ObservationSharpPredictionBand
      (OpticPosteriorAdmits coarse modelWorld priorAdmits actual) value)
    (fineBand : ObservationSharpPredictionBand
      (OpticPosteriorAdmits fine modelWorld priorAdmits actual) value) :
    0 ≤ ObservationSharpPredictionBand.acquisitionValue coarseBand fineBand := by
  exact ObservationSharpPredictionBand.acquisitionValue_nonnegative_of_refinement
    (optic_refinement_contracts_admitted_model_class refinement
      modelWorld priorAdmits actual)
    coarseBand fineBand

/-! ## Exact empty-refinement obstruction -/

private def bridgeCoarseBoolOptic : TaskConditionedOptic Bool where
  Observation := Unit
  Vocabulary := Unit
  Context := Unit
  Operation := Unit
  Evidence := Unit
  observe := fun _ => ()
  represent := id
  context := fun _ => ()
  horizon := 1
  admissibleOperation := fun _ => True
  provenance := ()

private def bridgeFineBoolOptic : TaskConditionedOptic Bool where
  Observation := Bool
  Vocabulary := Bool
  Context := Unit
  Operation := Unit
  Evidence := Unit
  observe := id
  represent := id
  context := fun _ => ()
  horizon := 1
  admissibleOperation := fun _ => True
  provenance := ()

private def bridgeBoolRefinement :
    OpticRefinement bridgeCoarseBoolOptic bridgeFineBoolOptic where
  coarsen := fun _ => ()
  commutes := by intro world; rfl

/-- No-go to strictness: the fine optic distinguishes the two worlds, but if
the prior class admits only the actual world, coarse and fine posterior model
classes are exactly equal. -/
theorem strict_optic_refinement_need_not_strictly_contract_model_class :
    (bridgeFineBoolOptic.observe false ≠ bridgeFineBoolOptic.observe true) ∧
    (∀ model : Bool,
      OpticPosteriorAdmits bridgeCoarseBoolOptic id (fun candidate => candidate = false)
          false model ↔
        OpticPosteriorAdmits bridgeFineBoolOptic id (fun candidate => candidate = false)
          false model) := by
  constructor
  · show false ≠ true
    decide
  · intro model
    simp [OpticPosteriorAdmits, bridgeCoarseBoolOptic, bridgeFineBoolOptic]

/-! ## Fixed-optic model-class reopening -/

/-- Prediction values supported by an admitted model class. -/
def ModelPredictionSet
    {Model : Type uModel} {Value : Type uValue}
    (admitted : Model → Prop) (value : Model → Value) : Set Value :=
  {predicted | ∃ model, admitted model ∧ value model = predicted}

/-- With the optic and observation fixed, extending the model class can reopen
both the posterior model set and its prediction set.  The new candidate is
observationally aliased but predicts a previously excluded value. -/
theorem fixed_optic_model_extension_reopens_epistemic_predictions :
    let smallPrior : Bool → Prop := fun model => model = false
    let largePrior : Bool → Prop := fun _ => True
    let smallPosterior := OpticPosteriorAdmits bridgeCoarseBoolOptic id
      smallPrior false
    let largePosterior := OpticPosteriorAdmits bridgeCoarseBoolOptic id
      largePrior false
    StrictSubset {model | smallPosterior model} {model | largePosterior model} ∧
      StrictSubset
        (ModelPredictionSet smallPosterior id)
        (ModelPredictionSet largePosterior id) := by
  dsimp
  constructor
  · constructor
    · intro model admitted
      exact ⟨trivial, rfl⟩
    · refine ⟨true, ?_, ?_⟩
      · exact ⟨trivial, rfl⟩
      · intro impossible
        exact Bool.noConfusion impossible.1
  · constructor
    · intro predicted supported
      rcases supported with ⟨model, admitted, valueEq⟩
      exact ⟨model, ⟨trivial, rfl⟩, valueEq⟩
    · refine ⟨true, ?_, ?_⟩
      · exact ⟨true, ⟨trivial, rfl⟩, rfl⟩
      · rintro ⟨model, admitted, valueEq⟩
        have modelFalse : model = false := admitted.1
        subst model
        exact Bool.noConfusion valueEq

end OCKIndividuationMSpaceComposition
