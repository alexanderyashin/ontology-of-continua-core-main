import OCKIndividuationMSpaceComposition.PredictionHorizonCore
import OCKIndividuationMSpaceComposition.SemanticPredictionContract

namespace OCKIndividuationMSpaceComposition

/-!
# Discrete event-prefix horizon refinement

The BPI replay uses the first half of an event trace as the observed context
and the second half as the target horizon.  This module makes that split
explicit and proves the two relevant boundaries: the prefix is invariant under
future suffix extension, while identical prefixes cannot determine distinct
suffix outcomes without an additional stochastic/structural premise.
-/

structure EventPrefixHorizon (Event : Type*) where
  trace : List Event
  split : Nat
  splitPositive : 0 < split
  splitBeforeEnd : split < trace.length

def EventPrefixHorizon.prefix
    {Event : Type*} (horizon : EventPrefixHorizon Event) : List Event :=
  horizon.trace.take horizon.split

def EventPrefixHorizon.suffix
    {Event : Type*} (horizon : EventPrefixHorizon Event) : List Event :=
  horizon.trace.drop horizon.split

theorem EventPrefixHorizon.prefix_length
    {Event : Type*} (horizon : EventPrefixHorizon Event) :
    horizon.prefix.length = horizon.split := by
  exact List.length_take_of_le (Nat.le_of_lt horizon.splitBeforeEnd)

theorem EventPrefixHorizon.prefix_is_origin_information
    {Event Information : Type*}
    (observe : List Event → Information)
    (horizon : EventPrefixHorizon Event) :
    observe horizon.prefix = observe horizon.prefix := by
  rfl

theorem EventPrefixHorizon.prefix_ignores_appended_future
    {Event : Type*}
    (pre post : List Event)
    (split : Nat)
    (splitLe : split ≤ pre.length) :
    (pre ++ post).take split = pre.take split := by
  induction pre generalizing split with
  | nil =>
      have splitZero : split = 0 := Nat.eq_zero_of_le_zero (by simpa using splitLe)
      simp [splitZero]
  | cons head tail ih =>
      cases split with
      | zero => simp
      | succ split =>
          have tailLe : split ≤ tail.length := by
            exact Nat.le_of_succ_le_succ (by simpa using splitLe)
          simpa using ih split tailLe

theorem EventPrefixHorizon.to_core_contract
    {Event : Type*} (horizon : EventPrefixHorizon Event) :
    ∃ contract : ForecastHorizonContract,
      contract.origin = horizon.split ∧
      contract.featureWindow.stop = horizon.split ∧
      contract.targetWindow.start = horizon.split ∧
      contract.targetWindow.stop = horizon.trace.length := by
  let featureWindow : HorizonWindow := {
    start := 0
    stop := horizon.split
    start_lt_stop := horizon.splitPositive
  }
  let targetWindow : HorizonWindow := {
    start := horizon.split
    stop := horizon.trace.length
    start_lt_stop := horizon.splitBeforeEnd
  }
  let meaning : HorizonMeaning := {
    objectId := "event-trace"
    propertyId := "suffix-outcome"
    horizonId := "prefix-to-suffix"
  }
  let contract : ForecastHorizonContract := {
    meaning := meaning
    origin := horizon.split
    featureWindow := featureWindow
    targetWindow := targetWindow
    featureBeforeOrigin := le_rfl
    originBeforeTarget := le_rfl
  }
  refine ⟨contract, rfl, ?_, ?_, ?_⟩
  · rfl
  · rfl
  · rfl

/-- Prefix-only deterministic prediction has the same aliasing no-go as any
other observation channel. -/
theorem identical_event_prefix_cannot_force_distinct_suffix_outcomes
    {Event Outcome : Type*}
    (prefixObserve : List Event → List Event)
    (target : List Event → Outcome)
    (predict : List Event → Outcome)
    (first second : List Event)
    (samePrefix : prefixObserve first = prefixObserve second)
    (differentSuffixOutcome : target first ≠ target second) :
    ¬ (predict (prefixObserve first) = target first ∧
      predict (prefixObserve second) = target second) := by
  exact aliased_information_cannot_predict_distinct_targets_exactly
    prefixObserve target predict first second samePrefix differentSuffixOutcome

/-! The finite BPI vocabulary is a representation-level refinement of the
prefix context.  Counts are normalized by the observed prefix length; the
definition therefore has no access to the suffix. -/

def eventCount [DecidableEq Event] (event : Event) : List Event → Nat
  | [] => 0
  | head :: tail => (if head = event then 1 else 0) + eventCount event tail

def eventPrefixFeature [DecidableEq Event]
    (event : Event) (trace : List Event) (split : Nat) (splitPositive : 0 < split) : ℚ :=
  (eventCount event (trace.take split) : ℚ) / (split : ℚ)

def finiteEventPrefixFeatureVector [DecidableEq Event]
    {m : Nat} (vocab : Fin m → Event) (trace : List Event)
    (split : Nat) (splitPositive : 0 < split) : Fin m → ℚ :=
  fun index => eventPrefixFeature (vocab index) trace split splitPositive

theorem eventPrefixFeature_append_eq [DecidableEq Event]
    (event : Event) (pre post : List Event) (split : Nat)
    (splitPositive : 0 < split) (splitLe : split ≤ pre.length) :
    eventPrefixFeature event (pre ++ post) split splitPositive =
      eventPrefixFeature event pre split splitPositive := by
  unfold eventPrefixFeature
  rw [EventPrefixHorizon.prefix_ignores_appended_future pre post split splitLe]

theorem finiteEventPrefixFeatureVector_append_eq [DecidableEq Event]
    {m : Nat} (vocab : Fin m → Event) (pre post : List Event) (split : Nat)
    (splitPositive : 0 < split) (splitLe : split ≤ pre.length) :
    finiteEventPrefixFeatureVector vocab (pre ++ post) split splitPositive =
      finiteEventPrefixFeatureVector vocab pre split splitPositive := by
  funext index
  exact eventPrefixFeature_append_eq (vocab index) pre post split splitPositive splitLe

end OCKIndividuationMSpaceComposition
