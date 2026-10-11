import OCKIndividuationMSpaceComposition.FiniteObservationLearning
import OCKIndividuationMSpaceComposition.OpenDiscreteDynamics
import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.NormNum

namespace OCKIndividuationMSpaceComposition

/-!
An operational bridge from observation-fiber sufficiency to conservative frame
extension, plus the explicit adapter required to interpret an observable
threshold crossing as a physical phase transition.
-/

/-- A task-relevant outcome collision hidden inside one observation fiber. -/
structure OutcomeCollision (experiment : ObservationExperiment) where
  left : experiment.World
  right : experiment.World
  sameObservation : experiment.observe left = experiment.observe right
  differentOutcome : experiment.outcome left ≠ experiment.outcome right

/-- A predictive frame is insufficient exactly when it contains such a collision. -/
def FrameInsufficient (experiment : ObservationExperiment) : Prop :=
  Nonempty (OutcomeCollision experiment)

theorem frameInsufficient_iff_not_observationSufficient
    (experiment : ObservationExperiment) :
    FrameInsufficient experiment ↔ ¬ ObservationSufficient experiment := by
  constructor
  · rintro ⟨collision⟩ sufficient
    exact collision.differentOutcome
      (sufficient collision.left collision.right collision.sameObservation)
  · intro notSufficient
    by_contra noCollision
    apply notSufficient
    intro left right sameObservation
    by_contra differentOutcome
    exact noCollision ⟨{
      left := left
      right := right
      sameObservation := sameObservation
      differentOutcome := differentOutcome
    }⟩

/-- A conservative observation-frame extension that resolves the target. -/
structure ResolvingFrameExtension
    (experiment : ObservationExperiment) (Fine : Type*) where
  fine : experiment.World → Fine
  refines : IsObservationRefinement experiment.observe fine
  sufficient : ∀ left right,
    fine left = fine right → experiment.outcome left = experiment.outcome right

def ResolvingFrameExtension.refinedExperiment
    {experiment : ObservationExperiment} {Fine : Type*}
    (extension : ResolvingFrameExtension experiment Fine) : ObservationExperiment where
  World := experiment.World
  Observation := Fine
  Outcome := experiment.Outcome
  observe := extension.fine
  outcome := experiment.outcome

/-- Every resolving extension must split every outcome collision. -/
theorem ResolvingFrameExtension.splits_collision
    {experiment : ObservationExperiment} {Fine : Type*}
    (extension : ResolvingFrameExtension experiment Fine)
    (collision : OutcomeCollision experiment) :
    extension.fine collision.left ≠ extension.fine collision.right :=
  sufficient_refinement_must_split_every_outcome_collision
    experiment.observe extension.fine experiment.outcome extension.sufficient
    collision.left collision.right collision.sameObservation
    collision.differentOutcome

/-- A resolving extension restores an exact predictor on the declared world. -/
theorem ResolvingFrameExtension.has_exact_predictor
    {experiment : ObservationExperiment} {Fine : Type*}
    [Inhabited experiment.Outcome]
    (extension : ResolvingFrameExtension experiment Fine) :
    ∃ predictor : Fine → experiment.Outcome,
      ExactObservationPredictor extension.refinedExperiment predictor := by
  let outcomeInhabited : Inhabited extension.refinedExperiment.Outcome := by
    simpa [ResolvingFrameExtension.refinedExperiment] using
      (inferInstance : Inhabited experiment.Outcome)
  letI := outcomeInhabited
  exact ⟨sufficientObservationPredictor extension.refinedExperiment,
    observation_sufficient_implies_exact_predictor
      extension.refinedExperiment extension.sufficient⟩

/-- Universe-polymorphic binary score for a frame-local point prediction. -/
def FrameZeroOneCorrect {Outcome : Type*} [DecidableEq Outcome]
    (predicted actual : Outcome) : Nat :=
  if predicted = actual then 1 else 0

/-- The unresolved coarse collision imposes a one-half accuracy ceiling. -/
theorem OutcomeCollision.pair_correct_count_le_one
    {experiment : ObservationExperiment} [DecidableEq experiment.Outcome]
    (collision : OutcomeCollision experiment)
    (predictor : experiment.Observation → experiment.Outcome) :
    FrameZeroOneCorrect (predictor (experiment.observe collision.left))
        (experiment.outcome collision.left) +
      FrameZeroOneCorrect (predictor (experiment.observe collision.right))
        (experiment.outcome collision.right) ≤ 1 :=
  by
    rw [collision.sameObservation]
    by_cases predictsLeft :
        predictor (experiment.observe collision.right) =
          experiment.outcome collision.left
    · have notRight :
          predictor (experiment.observe collision.right) ≠
            experiment.outcome collision.right := by
        intro predictsRight
        exact collision.differentOutcome (predictsLeft.symm.trans predictsRight)
      unfold FrameZeroOneCorrect
      rw [if_pos predictsLeft, if_neg notRight]
    · unfold FrameZeroOneCorrect
      rw [if_neg predictsLeft]
      split <;> simp

/-- A qualified repair records why one observed collision is not a post-hoc anomaly. -/
structure QualifiedFrameRepair
    (experiment : ObservationExperiment) (Fine : Type*) where
  collision : OutcomeCollision experiment
  extension : ResolvingFrameExtension experiment Fine
  replicated : Prop
  replicationEvidence : replicated
  interventionRelevant : Prop
  interventionEvidence : interventionRelevant

theorem QualifiedFrameRepair.old_frame_fails
    {experiment : ObservationExperiment} {Fine : Type*}
    (repair : QualifiedFrameRepair experiment Fine) :
    ¬ ObservationSufficient experiment :=
  (frameInsufficient_iff_not_observationSufficient experiment).mp
    ⟨repair.collision⟩

theorem QualifiedFrameRepair.extension_strictly_resolves_trigger
    {experiment : ObservationExperiment} {Fine : Type*}
    (repair : QualifiedFrameRepair experiment Fine) :
    repair.extension.fine repair.collision.left ≠
      repair.extension.fine repair.collision.right :=
  repair.extension.splits_collision repair.collision

/-- Observable crossing of an explicitly declared scalar order parameter. -/
def ObservableThresholdCrossing
    {State : Type*} (orderParameter : State → ℚ) (threshold : ℚ)
    (before after : State) : Prop :=
  orderParameter before < threshold ∧ threshold ≤ orderParameter after

/--
A physical phase label is licensed only by an adapter whose crossing semantics,
finite-size/scaling evidence and intervention evidence are separately typed.
-/
structure ValidatedPhaseAdapter (State : Type*) where
  orderParameter : State → ℚ
  threshold : ℚ
  phaseChange : State → State → Prop
  sound : ∀ before after,
    ObservableThresholdCrossing orderParameter threshold before after →
      phaseChange before after
  complete : ∀ before after,
    phaseChange before after →
      ObservableThresholdCrossing orderParameter threshold before after
  scalingValidated : Prop
  scalingEvidence : scalingValidated
  interventionValidated : Prop
  interventionEvidence : interventionValidated

theorem ValidatedPhaseAdapter.phaseChange_iff_crossing
    {State : Type*} (adapter : ValidatedPhaseAdapter State)
    (before after : State) :
    adapter.phaseChange before after ↔
      ObservableThresholdCrossing adapter.orderParameter adapter.threshold
        before after :=
  ⟨adapter.complete before after, adapter.sound before after⟩

def booleanOrderParameter : Bool → ℚ
  | false => 0
  | true => 1

theorem boolean_half_threshold_crosses :
    ObservableThresholdCrossing booleanOrderParameter (1 / 2) false true := by
  norm_num [ObservableThresholdCrossing, booleanOrderParameter]

/--
No-go: identical order-parameter data and the same threshold crossing support
opposite phase labels when no validated phase adapter is supplied.
-/
theorem threshold_data_alone_does_not_determine_phase_label :
    ∃ phaseLabelA phaseLabelB : Bool → Bool → Prop,
      ObservableThresholdCrossing booleanOrderParameter (1 / 2) false true ∧
      phaseLabelA false true ∧ ¬ phaseLabelB false true := by
  refine ⟨fun _ _ => True, fun _ _ => False,
    boolean_half_threshold_crosses, trivial, ?_⟩
  simp

end OCKIndividuationMSpaceComposition
