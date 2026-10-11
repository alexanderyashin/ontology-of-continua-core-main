import OCKIndividuationMSpaceComposition.FiniteHistoryMarkovization
import OCKIndividuationMSpaceComposition.KMPredictiveModelConstraint

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe uEvent uModel uOutcome uProbe uSummary
  uLiftCarrier uLiftCandidate uRepairCandidate

/-!
# Canonical recursive predictive state for a K/M model class

K/M selection constrains a model class, but a class of models is not yet an
online state representation.  The canonical task-conditioned state of a
history is its residual forecast: every admitted model's prediction after
every possible future suffix.  This is the exact Myhill--Nerode/predictive-
state object needed for lossless recursive compression.
-/

/-- The abstract `Model` parameter below is instantiated in OC by exactly the
K/M-tied resolving candidates, not by an arbitrary post-hoc model family. -/
abbrev KMTiedPredictiveModel
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank) :=
  {candidate : liftSearch.Candidate //
    KMTiedResolvingCandidate resolution candidate}

/-- K/M selection guarantees that the OC predictive model class is inhabited. -/
def selectedKMTiedPredictiveModel
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank) :
    KMTiedPredictiveModel resolution :=
  ⟨resolution.selection.minimizer.1,
    selected_is_km_tied_resolving resolution⟩

/-- Residual future behaviour of every candidate model after a history. -/
def KMResidualForecast
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    (forecast : Model → List Event → Outcome) (history : List Event) :
    Model → List Event → Outcome :=
  fun model suffix => forecast model (history ++ suffix)

/-- Two histories are predictively equivalent precisely when no admitted
model and no future suffix can distinguish them. -/
def KMFutureBehaviorEquivalent
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    (forecast : Model → List Event → Outcome)
    (left right : List Event) : Prop :=
  KMResidualForecast forecast left = KMResidualForecast forecast right

theorem km_future_behavior_equivalent_iff
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    (forecast : Model → List Event → Outcome)
    (left right : List Event) :
    KMFutureBehaviorEquivalent forecast left right ↔
      ∀ model suffix,
        forecast model (left ++ suffix) =
          forecast model (right ++ suffix) := by
  constructor
  · intro equivalent model suffix
    exact congrFun (congrFun equivalent model) suffix
  · intro pointwise
    funext model suffix
    exact pointwise model suffix

/-- Predictive equivalence is stable under a common next event.  This is the
right-congruence property required by deterministic online updating. -/
theorem km_future_behavior_equivalence_right_congruent
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    (forecast : Model → List Event → Outcome)
    {left right : List Event}
    (equivalent : KMFutureBehaviorEquivalent forecast left right)
    (event : Event) :
    KMFutureBehaviorEquivalent forecast (left ++ [event]) (right ++ [event]) := by
  rw [km_future_behavior_equivalent_iff] at equivalent ⊢
  intro model suffix
  simpa [List.append_assoc] using equivalent model (event :: suffix)

/-- Canonical residual state updates by pre-pending the new event to every
queried suffix. -/
def kmResidualRecursiveSummary
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    (forecast : Model → List Event → Outcome) :
    RecursiveHistorySummary Event (Model → List Event → Outcome) where
  initial := fun model suffix => forecast model suffix
  update := fun state event model suffix => state model (event :: suffix)

/-- The recursively folded canonical state is exactly the residual forecast
of the observed history. -/
theorem km_residual_recursive_summary_exact
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    (forecast : Model → List Event → Outcome) (history : List Event) :
    (kmResidualRecursiveSummary forecast).summarize history =
      KMResidualForecast forecast history := by
  induction history using List.reverseRecOn with
  | nil =>
      funext model suffix
      rfl
  | append_singleton history event inductionHypothesis =>
      rw [RecursiveHistorySummary.summarize_append_event,
        inductionHypothesis]
      funext model suffix
      simp [kmResidualRecursiveSummary, KMResidualForecast,
        List.append_assoc]

/-- Universal positive theorem: the K/M residual state is an exact recursive
sufficient statistic for the entire future-behaviour surface. -/
theorem km_residual_state_is_exactly_sufficient
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    (forecast : Model → List Event → Outcome) :
    ExactDecisionSufficient
      (kmResidualRecursiveSummary forecast).summarize
      (KMResidualForecast forecast) := by
  refine ⟨id, ?_⟩
  intro history
  exact km_residual_recursive_summary_exact forecast history

/-- Current predictions are the empty-suffix projection of the residual. -/
def KMCurrentForecastSignature
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    (forecast : Model → List Event → Outcome) (history : List Event) :
    Model → Outcome :=
  fun model => forecast model history

theorem km_current_signature_factors_through_residual
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    (forecast : Model → List Event → Outcome) (history : List Event) :
    KMCurrentForecastSignature forecast history =
      fun model => KMResidualForecast forecast history model [] := by
  funext model
  simp [KMCurrentForecastSignature, KMResidualForecast]

/-- Any exact compressed state must identify only future-equivalent histories. -/
theorem exact_km_predictive_summary_collision_implies_future_equivalence
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    {Summary : Type uSummary}
    (forecast : Model → List Event → Outcome)
    (summary : List Event → Summary)
    (sufficient : ExactDecisionSufficient summary
      (KMResidualForecast forecast))
    {left right : List Event}
    (sameSummary : summary left = summary right) :
    KMFutureBehaviorEquivalent forecast left right := by
  rcases sufficient with ⟨decode, recovers⟩
  rw [KMFutureBehaviorEquivalent]
  rw [← recovers left, ← recovers right, sameSummary]

/-! ## Exact minimality on a finite registered history universe -/

/-- Every exact summary must contain at least as many states as there are
distinct reached target values.  Applied to residual forecasts, this is the
exact finite Myhill--Nerode lower bound. -/
theorem exact_summary_reached_target_cardinality_lower_bound
    {History : Type*} [Finite History]
    {Summary : Type uSummary} [Finite Summary]
    {Target : Type*}
    (summary : History → Summary) (target : History → Target)
    (sufficient : ExactDecisionSufficient summary target) :
    Nat.card (Set.range target) ≤ Nat.card Summary := by
  classical
  rcases sufficient with ⟨decode, recovers⟩
  choose representative representativeSpec using
    fun reached : Set.range target => reached.property
  apply Nat.card_le_card_of_injective
    (fun reached : Set.range target => summary (representative reached))
  intro left right sameSummary
  apply Subtype.ext
  calc
    left.1 = target (representative left) := (representativeSpec left).symm
    _ = decode (summary (representative left)) :=
      (recovers (representative left)).symm
    _ = decode (summary (representative right)) :=
      congrArg decode sameSummary
    _ = target (representative right) := recovers (representative right)
    _ = right.1 := representativeSpec right

/-- The reached-target image itself attains the lower bound: store the reached
target value and decode by subtype projection. -/
theorem reached_target_image_summary_is_exact
    {History : Type*} {Target : Type*} (target : History → Target) :
    ∃ summary : History → Set.range target,
      ExactDecisionSufficient summary target := by
  let summary : History → Set.range target :=
    fun history => ⟨target history, ⟨history, rfl⟩⟩
  refine ⟨summary, ⟨Subtype.val, ?_⟩⟩
  intro history
  rfl

/-- OC specialization: on any finite registered history universe, the number
of distinct K/M residual behaviours is a sharp lower bound for every exact
compressed predictive state. -/
theorem exact_km_summary_requires_reached_residual_cardinality
    {RegisteredHistory : Type*} [Finite RegisteredHistory]
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    {Summary : Type uSummary} [Finite Summary]
    (historyOf : RegisteredHistory → List Event)
    (forecast : Model → List Event → Outcome)
    (summary : RegisteredHistory → Summary)
    (sufficient : ExactDecisionSufficient summary
      (fun history => KMResidualForecast forecast (historyOf history))) :
    Nat.card (Set.range
      (fun history => KMResidualForecast forecast (historyOf history))) ≤
      Nat.card Summary :=
  exact_summary_reached_target_cardinality_lower_bound summary _ sufficient

/-- No-go theorem: equality of present predictions is insufficient whenever a
future suffix separates the histories.  In that case no exact decoder from
the current K/M signature to the residual predictive state can exist. -/
theorem current_km_signature_collision_blocks_exact_recursive_state
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    (forecast : Model → List Event → Outcome)
    (left right : List Event)
    (sameCurrent : KMCurrentForecastSignature forecast left =
      KMCurrentForecastSignature forecast right)
    (model : Model) (suffix : List Event)
    (futureDiffers : forecast model (left ++ suffix) ≠
      forecast model (right ++ suffix)) :
    ¬ ExactDecisionSufficient
      (KMCurrentForecastSignature forecast)
      (KMResidualForecast forecast) := by
  intro sufficient
  have equivalent :=
    exact_km_predictive_summary_collision_implies_future_equivalence
      forecast (KMCurrentForecastSignature forecast) sufficient sameCurrent
  rw [km_future_behavior_equivalent_iff] at equivalent
  exact futureDiffers (equivalent model suffix)

/-! ## Explicit current-signature countermodel -/

/-- A one-model Boolean forecast whose present outputs agree at two histories,
while the suffix `[true]` separates their future behaviour. -/
def delayedBooleanCounterForecast (_model : Unit) (history : List Bool) : Bool :=
  history == [true]

theorem delayed_boolean_counter_has_same_current_but_different_future :
    KMCurrentForecastSignature delayedBooleanCounterForecast [] =
        KMCurrentForecastSignature delayedBooleanCounterForecast [false] ∧
      delayedBooleanCounterForecast () ([] ++ [true]) ≠
        delayedBooleanCounterForecast () ([false] ++ [true]) := by
  decide

/-- Concrete refutation of the universal shortcut “the current K/M forecast
vector is always a sufficient recursive state”. -/
theorem current_km_forecast_signature_is_not_universally_sufficient :
    ¬ ExactDecisionSufficient
      (KMCurrentForecastSignature delayedBooleanCounterForecast)
      (KMResidualForecast delayedBooleanCounterForecast) := by
  rcases delayed_boolean_counter_has_same_current_but_different_future with
    ⟨sameCurrent, futureDiffers⟩
  exact current_km_signature_collision_blocks_exact_recursive_state
    delayedBooleanCounterForecast [] [false] sameCurrent () [true]
    futureDiffers

/-- A finite registered suffix battery gives the executable K/M signature
used by the experimental adapter. -/
def KMProbeForecastSignature
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    {Probe : Type uProbe}
    (probe : Probe → List Event)
    (forecast : Model → List Event → Outcome)
    (history : List Event) : Model → Probe → Outcome :=
  fun model query => forecast model (history ++ probe query)

/-- A refined probe family contains every coarse suffix query, possibly with
additional queries. -/
def KMProbeFamilyRefines
    {Event : Type uEvent} {CoarseProbe : Type*} {FineProbe : Type*}
    (coarse : CoarseProbe → List Event)
    (fine : FineProbe → List Event) : Prop :=
  ∃ embed : CoarseProbe → FineProbe,
    ∀ query, fine (embed query) = coarse query

/-- Monotonicity theorem for adaptive optics: equality under a refined probe
battery implies equality under every coarser battery it contains. -/
theorem refined_probe_signature_equality_implies_coarse_equality
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    {CoarseProbe FineProbe : Type*}
    (coarse : CoarseProbe → List Event)
    (fine : FineProbe → List Event)
    (refines : KMProbeFamilyRefines coarse fine)
    (forecast : Model → List Event → Outcome)
    (left right : List Event)
    (sameFine : KMProbeForecastSignature fine forecast left =
      KMProbeForecastSignature fine forecast right) :
    KMProbeForecastSignature coarse forecast left =
      KMProbeForecastSignature coarse forecast right := by
  rcases refines with ⟨embed, included⟩
  funext model query
  have equalAtFine := congrFun (congrFun sameFine model) (embed query)
  simpa [KMProbeForecastSignature, included query] using equalAtFine

/-- If a registered probe is a separating suffix, that finite battery
necessarily resolves the history collision. -/
theorem included_separating_suffix_distinguishes_probe_signatures
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    {Probe : Type uProbe}
    (probe : Probe → List Event)
    (forecast : Model → List Event → Outcome)
    (left right : List Event)
    (model : Model) (query : Probe)
    (separates : forecast model (left ++ probe query) ≠
      forecast model (right ++ probe query)) :
    KMProbeForecastSignature probe forecast left ≠
      KMProbeForecastSignature probe forecast right := by
  intro same
  exact separates (congrFun (congrFun same model) query)

/-- Exact size of the ambient finite probe-signature state space.  With `m`
models, `p` registered suffix probes and `r` outcomes, it has `r^(m*p)`
states.  The actually reached image may be smaller and is an empirical
quantity. -/
theorem km_probe_signature_state_space_cardinality
    (Model : Type uModel) [Fintype Model] [DecidableEq Model]
    (Probe : Type uProbe) [Fintype Probe] [DecidableEq Probe]
    (Outcome : Type uOutcome) [Fintype Outcome] :
    Fintype.card (Model → Probe → Outcome) =
      Fintype.card Outcome ^
        (Fintype.card Model * Fintype.card Probe) := by
  simp only [Fintype.card_fun]
  rw [← pow_mul, Nat.mul_comm]

/-- Concrete capacity calculation: five tied models, eight suffix probes and
binary outcomes produce exactly `2^40` possible registered signatures. -/
theorem five_models_eight_probes_binary_signature_has_2_pow_40_states :
    Fintype.card (Fin 5 → Fin 8 → Bool) = 2 ^ 40 := by
  simpa using km_probe_signature_state_space_cardinality
    (Fin 5) (Fin 8) Bool

end OCKIndividuationMSpaceComposition
