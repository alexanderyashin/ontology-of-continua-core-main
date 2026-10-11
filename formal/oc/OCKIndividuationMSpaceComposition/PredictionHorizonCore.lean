import OCKIndividuationMSpaceComposition.SemanticPredictionContract

namespace OCKIndividuationMSpaceComposition

/-!
# Dependency-free typed prediction-horizon kernel

This is the local kernel behind the package-facing horizon surface. A
forecast binds a referent, target property and horizon identifier before its
temporal windows can be compared. The contract records which inputs existed
at the origin and proves the non-overlap boundary used by later adapters.
-/

structure HorizonMeaning where
  objectId : String
  propertyId : String
  horizonId : String
  deriving DecidableEq

theorem horizonMeaning_ne_of_horizonId_ne
    {first second : HorizonMeaning}
    (different : first.horizonId ≠ second.horizonId) :
    first ≠ second := by
  intro equal
  apply different
  simpa [equal]

structure HorizonWindow where
  start : ℕ
  stop : ℕ
  start_lt_stop : start < stop

def WindowBefore (feature target : HorizonWindow) : Prop :=
  feature.stop ≤ target.start

structure ForecastHorizonContract where
  meaning : HorizonMeaning
  origin : ℕ
  featureWindow : HorizonWindow
  targetWindow : HorizonWindow
  featureBeforeOrigin : featureWindow.stop ≤ origin
  originBeforeTarget : origin ≤ targetWindow.start

namespace ForecastHorizonContract

def NonOverlapping (contract : ForecastHorizonContract) : Prop :=
  WindowBefore contract.featureWindow contract.targetWindow

theorem nonoverlap (contract : ForecastHorizonContract) :
    contract.NonOverlapping := by
  unfold NonOverlapping WindowBefore
  exact Nat.le_trans contract.featureBeforeOrigin contract.originBeforeTarget

end ForecastHorizonContract

theorem no_shared_sample_of_nonoverlap
    (contract : ForecastHorizonContract)
    (nonoverlap : contract.NonOverlapping) :
    ¬ ∃ time : ℕ,
      contract.featureWindow.start ≤ time ∧
      time < contract.featureWindow.stop ∧
      contract.targetWindow.start ≤ time ∧
      time < contract.targetWindow.stop := by
  intro shared
  rcases shared with ⟨time, featureStart, featureStop, targetStart, targetStop⟩
  unfold ForecastHorizonContract.NonOverlapping WindowBefore at nonoverlap
  omega

theorem overlap_blocks_nonoverlap
    (feature target : HorizonWindow)
    (overlap : ∃ time : ℕ,
      feature.start ≤ time ∧ time < feature.stop ∧
      target.start ≤ time ∧ time < target.stop) :
    ¬ WindowBefore feature target := by
  intro before
  rcases overlap with ⟨time, featureStart, featureStop, targetStart, targetStop⟩
  unfold WindowBefore at before
  omega

theorem admitted_input_is_available
    (origin : ℕ)
    (inputs : List ForecastInformationItem)
    (admitted : AllInputsAvailableAt origin inputs)
    (item : ForecastInformationItem)
    (member : item ∈ inputs) :
    item.availableAt ≤ origin :=
  admitted item member

def SelectorNoWorseOnBlocks
    {Block : Type*}
    (baseline candidate : Block → ℝ)
    (blocks : List Block) : Prop :=
  ∀ block, block ∈ blocks → candidate block ≤ baseline block

theorem stable_selector_preserves_nonloss
    {Block : Type*}
    (baseline candidate : Block → ℝ)
    (blocks : List Block)
    (stable : SelectorNoWorseOnBlocks baseline candidate blocks) :
    ∀ block, block ∈ blocks → candidate block ≤ baseline block :=
  stable

theorem untouched_tail_failure_is_not_repaired
    {Block : Type*}
    (baseline candidate : Block → ℝ)
    (selectionBlocks : List Block)
    (_stable : SelectorNoWorseOnBlocks baseline candidate selectionBlocks)
    (untouched : Block)
    (tailFailure : baseline untouched < candidate untouched) :
    ¬ candidate untouched ≤ baseline untouched := by
  exact not_le_of_gt tailFailure

end OCKIndividuationMSpaceComposition
