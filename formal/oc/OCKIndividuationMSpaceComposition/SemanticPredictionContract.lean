import OCKIndividuationMSpaceComposition.ExperimentalEpistemology

namespace OCKIndividuationMSpaceComposition

/-!
# Semantic prediction contracts

The numerical codomain does not determine what a prediction means.  This
module types the referent, target, origin, horizon and decision, then isolates
the information-at-origin condition required by an operational forecast.
-/

/-- Stable target classes reused by the machine-readable profile. -/
inductive PredictionTargetKind where
  | realityState
  | measurementResult
  | derivedMeasurementResult
  | event
  | decisionUtility
  | setValuedState
  deriving DecidableEq

/-- Semantic coordinates which remain distinct even when two runners emit the
same numeric value. -/
structure PredictionMeaning where
  realityObjectId : String
  targetPropertyId : String
  targetKind : PredictionTargetKind
  forecastOriginId : String
  horizonId : String
  decisionContextId : String
  deriving DecidableEq

namespace PredictionMeaning

theorem ne_of_targetPropertyId_ne
    {first second : PredictionMeaning}
    (different : first.targetPropertyId ≠ second.targetPropertyId) :
    first ≠ second := by
  intro equal
  apply different
  simpa [equal]

theorem ne_of_decisionContextId_ne
    {first second : PredictionMeaning}
    (different : first.decisionContextId ≠ second.decisionContextId) :
    first ≠ second := by
  intro equal
  apply different
  simpa [equal]

end PredictionMeaning

/-- An experiment cell with an explicit semantic prediction binding.  This is
additive and does not change the identity of historical unbound cells. -/
structure SemanticallyBoundExperimentCell where
  cell : ScientificExperimentCell
  meaning : PredictionMeaning
  semanticContractId : String
  deriving DecidableEq

namespace SemanticallyBoundExperimentCell

theorem ne_of_targetPropertyId_ne
    {first second : SemanticallyBoundExperimentCell}
    (different : first.meaning.targetPropertyId ≠
      second.meaning.targetPropertyId) :
    first ≠ second := by
  intro equal
  apply different
  simpa [equal]

end SemanticallyBoundExperimentCell

/-- A model input and the first discrete time at which it is available. -/
structure ForecastInformationItem where
  itemId : String
  availableAt : ℕ
  deriving DecidableEq

/-- Every model input must be available no later than the forecast origin. -/
def AllInputsAvailableAt
    (origin : ℕ) (inputs : List ForecastInformationItem) : Prop :=
  ∀ item, item ∈ inputs → item.availableAt ≤ origin

/-- The mathematical core of an operational semantic forecast contract. -/
structure OperationalSemanticForecastContract where
  meaning : PredictionMeaning
  origin : ℕ
  inputs : List ForecastInformationItem
  allInputsAvailable : AllInputsAvailableAt origin inputs

/-- Positive theorem: an admitted contract provides an availability proof for
every declared model input. -/
theorem operational_contract_input_available
    (contract : OperationalSemanticForecastContract)
    (item : ForecastInformationItem)
    (member : item ∈ contract.inputs) :
    item.availableAt ≤ contract.origin :=
  contract.allInputsAvailable item member

/-- A post-origin model input is not available at the origin. -/
theorem postOrigin_input_not_available
    (origin : ℕ) (item : ForecastInformationItem)
    (postOrigin : origin < item.availableAt) :
    ¬ item.availableAt ≤ origin :=
  Nat.not_le_of_gt postOrigin

/-- No operational admission can coexist with a declared post-origin member. -/
theorem postOrigin_member_blocks_operational_contract
    (origin : ℕ) (inputs : List ForecastInformationItem)
    (item : ForecastInformationItem)
    (member : item ∈ inputs)
    (postOrigin : origin < item.availableAt) :
    ¬ AllInputsAvailableAt origin inputs := by
  intro admitted
  exact postOrigin_input_not_available origin item postOrigin
    (admitted item member)

/-! ## Information and measurement no-go boundaries -/

/-- If two possible worlds have the same origin information but distinct
targets, no deterministic predictor of that information is exact in both. -/
theorem aliased_information_cannot_predict_distinct_targets_exactly
    {World Information Outcome : Type*}
    (observeAtOrigin : World → Information)
    (target : World → Outcome)
    (predict : Information → Outcome)
    (first second : World)
    (sameInformation : observeAtOrigin first = observeAtOrigin second)
    (differentTargets : target first ≠ target second) :
    ¬ (predict (observeAtOrigin first) = target first ∧
      predict (observeAtOrigin second) = target second) := by
  intro exactBoth
  apply differentTargets
  calc
    target first = predict (observeAtOrigin first) := exactBoth.1.symm
    _ = predict (observeAtOrigin second) := by rw [sameInformation]
    _ = target second := exactBoth.2

/-- Coverage semantics for a set-valued forecast represented by a finite list.
It makes uncertainty about an unavailable destination explicit instead of
inventing a point identity. -/
def SetValuedForecastCoversAt
    {World Information Outcome : Type*}
    (observeAtOrigin : World → Information)
    (target : World → Outcome)
    (forecast : Information → List Outcome)
    (world : World) : Prop :=
  target world ∈ forecast (observeAtOrigin world)

/-- Positive counterpart to the point-prediction aliasing no-go.  When two
worlds share origin information, the explicit pair of possible outcomes covers
both worlds.  This does not choose between them; it preserves the unresolved
destination coordinate. -/
theorem aliased_pair_is_covered_by_explicit_set_forecast
    {World Information Outcome : Type*}
    [DecidableEq Information] [DecidableEq Outcome]
    (observeAtOrigin : World → Information)
    (target : World → Outcome)
    (first second : World)
    (sameInformation : observeAtOrigin first = observeAtOrigin second) :
    let forecast : Information → List Outcome := fun information =>
      if information = observeAtOrigin first
      then [target first, target second]
      else []
    SetValuedForecastCoversAt observeAtOrigin target forecast first ∧
      SetValuedForecastCoversAt observeAtOrigin target forecast second := by
  dsimp [SetValuedForecastCoversAt]
  constructor
  · rw [if_pos rfl]
    exact List.mem_cons_self
  · rw [sameInformation, if_pos rfl]
    exact List.mem_cons_of_mem _ List.mem_cons_self

/-! ## Exact-key successor binding and transport -/

/-- A minimal exact-key successor adapter.  An unseen key falls back to the
current state; a seen key returns the current state together with the recorded
successors. -/
def ExactKeySuccessorForecast
    {Key State : Type*}
    (successors : Key → List State)
    (key : Key)
    (current : State) : List State :=
  match successors key with
  | [] => [current]
  | head :: tail => current :: head :: tail

/-- Positive theorem: every recorded successor is covered by the exact-key
adapter. -/
theorem recorded_exact_key_successor_is_covered
    {Key State : Type*}
    [DecidableEq State]
    (successors : Key → List State)
    (key : Key)
    (current actual : State)
    (recorded : actual ∈ successors key) :
    actual ∈ ExactKeySuccessorForecast successors key current := by
  cases successorCases : successors key with
  | nil =>
      rw [successorCases] at recorded
      exact (List.not_mem_nil recorded).elim
  | cons head tail =>
      rw [successorCases] at recorded
      rw [ExactKeySuccessorForecast, successorCases]
      exact List.mem_cons_of_mem current recorded

/-- No-go theorem: when the exact predecessor key was unseen, persistence
fallback cannot cover a genuinely changed destination.  More model capacity
downstream cannot repair this missing binding premise. -/
theorem unseen_exact_key_persistence_cannot_cover_changed_destination
    {Key State : Type*}
    [DecidableEq State]
    (successors : Key → List State)
    (key : Key)
    (current actual : State)
    (unseen : successors key = [])
    (changed : actual ≠ current) :
    actual ∉ ExactKeySuccessorForecast successors key current := by
  rw [ExactKeySuccessorForecast, unseen]
  intro member
  rcases List.mem_cons.mp member with equal | impossible
  · exact changed equal
  · exact (List.not_mem_nil impossible).elim

/-- Positive transport fact for a backoff hierarchy: once a destination is
covered, any explicitly proved list expansion preserves coverage. -/
theorem successor_coverage_is_monotone_under_explicit_backoff
    {State : Type*}
    (narrow broad : List State)
    (expands : ∀ state, state ∈ narrow → state ∈ broad)
    (actual : State)
    (covered : actual ∈ narrow) :
    actual ∈ broad :=
  expands actual covered

/-- Mapping a finite destination forecast through a conditional response model
contains the oracle conditional response whenever the actual destination is in
the destination forecast.  This is response containment, not target accuracy. -/
theorem mapped_destination_forecast_contains_oracle_response
    {Destination Response : Type*}
    (predict : Destination → Response)
    (candidates : List Destination)
    (actual : Destination)
    (covered : actual ∈ candidates) :
    predict actual ∈ candidates.map predict := by
  exact List.mem_map.mpr ⟨actual, covered, rfl⟩

/-- Explicit no-go countermodel: coverage of the realized destination does not
by itself make the conditional response model exact for the realized physical
target.  A residual/dynamics premise remains necessary. -/
theorem destination_coverage_does_not_imply_response_exactness :
    ∃ candidates : List Bool, ∃ actual : Bool,
      actual ∈ candidates ∧
      (fun _destination : Bool => false) actual ≠ true := by
  exact ⟨[false], false, by decide, by decide⟩

/-- A scalar response hull used to distinguish a mechanism envelope from a
governance/action envelope. -/
structure ScalarForecastHull where
  lower : ℝ
  upper : ℝ

namespace ScalarForecastHull

/-- A response is contained in a scalar forecast hull. -/
def Contains (hull : ScalarForecastHull) (response : ℝ) : Prop :=
  hull.lower ≤ response ∧ response ≤ hull.upper

/-- Symmetric residual hull around a conditional point forecast. -/
def symmetric (center radius : ℝ) : ScalarForecastHull where
  lower := center - radius
  upper := center + radius

/-- Expand both sides of a forecast hull by an explicit residual radius. -/
def inflate (hull : ScalarForecastHull) (radius : ℝ) : ScalarForecastHull where
  lower := hull.lower - radius
  upper := hull.upper + radius

/-- The narrow hull is explicitly nested inside the broad hull. -/
def Refines (narrow broad : ScalarForecastHull) : Prop :=
  broad.lower ≤ narrow.lower ∧ narrow.upper ≤ broad.upper

/-- Positive theorem: explicit hull refinement cannot increase scalar width. -/
theorem width_le_of_refines
    (narrow broad : ScalarForecastHull)
    (refines : Refines narrow broad) :
    narrow.upper - narrow.lower ≤ broad.upper - broad.lower := by
  linarith [refines.1, refines.2]

/-- Any response contained in a refined hull is also contained in the broad
hull. -/
theorem broad_contains_of_refined_contains
    (narrow broad : ScalarForecastHull)
    (refines : Refines narrow broad)
    (response : ℝ)
    (contained : narrow.lower ≤ response ∧ response ≤ narrow.upper) :
    broad.lower ≤ response ∧ response ≤ broad.upper := by
  constructor
  · exact le_trans refines.1 contained.1
  · exact le_trans contained.2 refines.2

/-- Exact accounting identity: symmetric inflation adds twice the radius to
the interval width.  Coverage therefore cannot be optimized without charging
for width. -/
theorem inflate_width
    (hull : ScalarForecastHull)
    (radius : ℝ) :
    (inflate hull radius).upper - (inflate hull radius).lower =
      (hull.upper - hull.lower) + 2 * radius := by
  simp [inflate]
  ring

/-- Positive monotonicity theorem: increasing the residual radius gives a
broader hull containing the smaller-radius hull. -/
theorem inflate_refines_of_radius_le
    (hull : ScalarForecastHull)
    (small large : ℝ)
    (radiusLe : small ≤ large) :
    Refines (inflate hull small) (inflate hull large) := by
  constructor <;> simp [inflate] <;> linarith

/-- A two-sided absolute residual certificate is sufficient for containment in
the corresponding symmetric forecast hull. -/
theorem symmetric_contains_of_abs_sub_le
    (center radius response : ℝ)
    (bound : |response - center| ≤ radius) :
    Contains (symmetric center radius) response := by
  have sides := (abs_le.mp bound)
  constructor <;> simp [symmetric] <;> linarith [sides.1, sides.2]

/-- The pointwise maximum is safe for either of two regime-specific residual
contracts when the regime is not observed. -/
theorem max_regime_radius_is_safe
    (nontransition transition : ℝ) :
    nontransition ≤ max nontransition transition ∧
      transition ≤ max nontransition transition := by
  exact ⟨le_max_left _ _, le_max_right _ _⟩

/-- The unknown-regime union radius is pointwise minimal: every radius which
dominates both regime-specific requirements must dominate their maximum. -/
theorem max_regime_radius_is_minimal
    (nontransition transition candidate : ℝ)
    (safeNontransition : nontransition ≤ candidate)
    (safeTransition : transition ≤ candidate) :
    max nontransition transition ≤ candidate := by
  exact max_le safeNontransition safeTransition

/-- No-go complement: a radius strictly below the unknown-regime union fails
at least one of the two regime-specific lower-bound contracts. -/
theorem below_max_regime_radius_violates_a_contract
    (nontransition transition candidate : ℝ)
    (tooSmall : candidate < max nontransition transition) :
    candidate < nontransition ∨ candidate < transition := by
  exact (lt_max_iff).mp tooSmall

/-- A source residual bound alone does not transport to a different target
environment.  Some invariance theorem or explicit transport margin is needed. -/
theorem source_residual_bound_does_not_imply_target_bound :
    ∃ sourceResidual targetResidual radius : ℝ,
      |sourceResidual| ≤ radius ∧ ¬ |targetResidual| ≤ radius := by
  refine ⟨0, 2, 1, ?_, ?_⟩
  · norm_num
  · norm_num

/-- Positive repair: once a source radius and an explicit environment-transport
margin jointly bound the target residual, their sum yields target containment. -/
theorem additive_transport_margin_yields_containment
    (center sourceRadius transportMargin target : ℝ)
    (transportBound :
      |target - center| ≤ sourceRadius + transportMargin) :
    Contains (symmetric center (sourceRadius + transportMargin)) target := by
  exact symmetric_contains_of_abs_sub_le
    center (sourceRadius + transportMargin) target transportBound

end ScalarForecastHull

/-- A toy measurement channel which erases the underlying Boolean state. -/
def constantBooleanMeasurement (_state : Bool) : Bool := false

/-- Explicit countermodel: equality of measurement results does not imply
equality of the reality states which generated them. -/
theorem same_measurement_result_does_not_imply_same_reality_state :
    constantBooleanMeasurement false = constantBooleanMeasurement true ∧
      false ≠ true := by
  decide

/-- Stronger no-go: no decoder of the constant measurement is exact for every
underlying state.  A measurement-to-state adapter needs an identifiability
premise; estimator capacity cannot recover information erased upstream. -/
theorem constant_measurement_has_no_exact_state_decoder :
    ¬ ∃ decode : Bool → Bool,
      ∀ state, decode (constantBooleanMeasurement state) = state := by
  intro decoderExists
  obtain ⟨decode, exact⟩ := decoderExists
  have falseExact := exact false
  have trueExact := exact true
  have impossible : false = true := by
    calc
      false = decode false := falseExact.symm
      _ = true := trueExact
  cases impossible

/-- Same target property and numeric codomain do not make two predictions the
same scientific object when their supported decisions differ. -/
def diagnosticMeaning : PredictionMeaning where
  realityObjectId := "rig"
  targetPropertyId := "next-sensor-change"
  targetKind := .derivedMeasurementResult
  forecastOriginId := "after-cycle-i"
  horizonId := "one-cycle"
  decisionContextId := "scientific-family-selection"

def maintenanceMeaning : PredictionMeaning where
  realityObjectId := "rig"
  targetPropertyId := "next-sensor-change"
  targetKind := .derivedMeasurementResult
  forecastOriginId := "after-cycle-i"
  horizonId := "one-cycle"
  decisionContextId := "maintenance-action"

theorem same_target_different_decision_is_different_prediction_meaning :
    diagnosticMeaning.targetPropertyId = maintenanceMeaning.targetPropertyId ∧
      diagnosticMeaning ≠ maintenanceMeaning := by
  constructor
  · rfl
  · exact PredictionMeaning.ne_of_decisionContextId_ne (by decide)

end OCKIndividuationMSpaceComposition
