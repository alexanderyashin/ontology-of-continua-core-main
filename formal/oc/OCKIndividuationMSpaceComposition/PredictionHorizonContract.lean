import OCKIndividuationMSpaceComposition.SemanticPredictionContract

namespace OCKIndividuationMSpaceComposition

/-!
# Typed prediction horizons

The same numerical target can support different scientific claims depending on
the forecast origin and target window.  This module gives the smallest typed
contract needed to keep profile-to-future prediction, within-cycle forecasting,
and measurement reconstruction distinct.  It also exposes the exact leakage
boundary: a feature window ending after the target begins cannot be admitted as
a non-overlapping forecast.
-/

structure TypedHorizonWindow where
  start : ℕ
  stop : ℕ
  start_lt_stop : start < stop

def TypedWindowBefore (feature target : TypedHorizonWindow) : Prop :=
  feature.stop ≤ target.start

structure TypedPredictionHorizon where
  meaning : PredictionMeaning
  origin : ℕ
  featureWindow : TypedHorizonWindow
  targetWindow : TypedHorizonWindow
  featureBeforeOrigin : featureWindow.stop ≤ origin
  originBeforeTarget : origin ≤ targetWindow.start
  inputs : List ForecastInformationItem
  allInputsAvailable : AllInputsAvailableAt origin inputs

namespace PredictionMeaning

theorem ne_of_horizonId_ne
    {first second : PredictionMeaning}
    (different : first.horizonId ≠ second.horizonId) :
    first ≠ second := by
  intro equal
  apply different
  simpa [equal]

end PredictionMeaning

namespace TypedPredictionHorizon

def NonOverlapping (contract : TypedPredictionHorizon) : Prop :=
  TypedWindowBefore contract.featureWindow contract.targetWindow

theorem feature_target_nonoverlap
    (contract : TypedPredictionHorizon) :
    NonOverlapping contract := by
  unfold NonOverlapping TypedWindowBefore
  exact Nat.le_trans contract.featureBeforeOrigin contract.originBeforeTarget

theorem no_shared_sample_of_nonoverlap
    (contract : TypedPredictionHorizon)
    (nonoverlap : NonOverlapping contract) :
    ¬ ∃ time : ℕ,
      contract.featureWindow.start ≤ time ∧
      time < contract.featureWindow.stop ∧
      contract.targetWindow.start ≤ time ∧
      time < contract.targetWindow.stop := by
  intro shared
  rcases shared with ⟨time, featureStart, featureStop, targetStart, targetStop⟩
  unfold NonOverlapping TypedWindowBefore at nonoverlap
  omega

theorem overlap_blocks_nonoverlap
    (feature target : TypedHorizonWindow)
    (overlap : ∃ time : ℕ,
      feature.start ≤ time ∧ time < feature.stop ∧
      target.start ≤ time ∧ time < target.stop) :
    ¬ TypedWindowBefore feature target := by
  intro before
  rcases overlap with ⟨time, featureStart, featureStop, targetStart, targetStop⟩
  unfold TypedWindowBefore at before
  omega

theorem input_available_at_origin
    (contract : TypedPredictionHorizon)
    (item : ForecastInformationItem)
    (member : item ∈ contract.inputs) :
    item.availableAt ≤ contract.origin := by
  exact contract.allInputsAvailable item member

end TypedPredictionHorizon

/-! ## Two-block selector stability -/

def CandidateNoWorseOnBlocks
    {Block : Type*}
    (baseline candidate : Block → ℝ)
    (blocks : List Block) : Prop :=
  ∀ block, block ∈ blocks → candidate block ≤ baseline block

theorem candidate_no_worse_preserves_block_safety
    {Block : Type*}
    (baseline candidate : Block → ℝ)
    (blocks : List Block)
    (stable : CandidateNoWorseOnBlocks baseline candidate blocks) :
    ∀ block, block ∈ blocks → candidate block ≤ baseline block := by
  exact stable

theorem candidate_failure_on_untouched_tail_is_not_repaired_by_selection_stability
    {Block : Type*}
    (baseline candidate : Block → ℝ)
    (selectionBlocks : List Block)
    (stable : CandidateNoWorseOnBlocks baseline candidate selectionBlocks)
    (untouched : Block)
    (tailFailure : baseline untouched < candidate untouched) :
    ¬ (candidate untouched ≤ baseline untouched) := by
  exact not_le_of_gt tailFailure

end OCKIndividuationMSpaceComposition
