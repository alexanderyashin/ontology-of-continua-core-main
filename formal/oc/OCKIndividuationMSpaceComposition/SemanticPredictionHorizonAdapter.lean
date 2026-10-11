import OCKIndividuationMSpaceComposition.SemanticPredictionContract
import OCKIndividuationMSpaceComposition.PredictionHorizonCore

namespace OCKIndividuationMSpaceComposition

/-!
# Public semantic adapter for the typed prediction-horizon core

The core horizon contract proves temporal non-overlap.  The public semantic
contract gives a forecast its referent, target, origin and decision context.
This adapter composes them without identifying the two meanings by Lean
equality: the binding carries the explicit coordinate correspondences and
derives input availability from the feature-window boundary.
-/

structure SemanticPredictionHorizonBinding where
  horizon : ForecastHorizonContract
  meaning : PredictionMeaning
  objectMatches : meaning.realityObjectId = horizon.meaning.objectId
  propertyMatches : meaning.targetPropertyId = horizon.meaning.propertyId
  horizonMatches : meaning.horizonId = horizon.meaning.horizonId
  inputs : List OCKIndividuationMSpaceComposition.ForecastInformationItem
  inputsWithinFeatureWindow :
    ∀ item, item ∈ inputs → item.availableAt ≤ horizon.featureWindow.stop

theorem SemanticPredictionHorizonBinding.inputs_available_at_origin
    (binding : SemanticPredictionHorizonBinding) :
    AllInputsAvailableAt binding.horizon.origin binding.inputs := by
  intro item member
  exact Nat.le_trans
    (binding.inputsWithinFeatureWindow item member)
    binding.horizon.featureBeforeOrigin

theorem SemanticPredictionHorizonBinding.core_nonoverlap
    (binding : SemanticPredictionHorizonBinding) :
    binding.horizon.NonOverlapping := by
  exact ForecastHorizonContract.nonoverlap binding.horizon

def SemanticPredictionHorizonBinding.operationalContract
    (binding : SemanticPredictionHorizonBinding) :
    OperationalSemanticForecastContract where
  meaning := binding.meaning
  origin := binding.horizon.origin
  inputs := binding.inputs
  allInputsAvailable := binding.inputs_available_at_origin

theorem SemanticPredictionHorizonBinding.operational_input_available
    (binding : SemanticPredictionHorizonBinding)
    (item : OCKIndividuationMSpaceComposition.ForecastInformationItem)
    (member : item ∈ binding.inputs) :
    item.availableAt ≤ (binding.operationalContract).origin := by
  exact operational_contract_input_available
    binding.operationalContract item member

theorem SemanticPredictionHorizonBinding.target_starts_after_origin
    (binding : SemanticPredictionHorizonBinding) :
    binding.horizon.origin ≤ binding.horizon.targetWindow.start :=
  binding.horizon.originBeforeTarget

end OCKIndividuationMSpaceComposition
