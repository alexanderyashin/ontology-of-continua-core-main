import OCKIndividuationMSpaceComposition.KMRecursivePredictiveState
import OCKIndividuationMSpaceComposition.FiniteObservationRefinementBudget
import OCKIndividuationMSpaceComposition.DynamicObservationQuotient

namespace OCKIndividuationMSpaceComposition

universe uEvent uModel uOutcome uCoarseProbe uFineProbe uHistory uTarget

/-!
# K/M probe refinement: predictive monotonicity and dynamic nonmonotonicity

The F9 known-truth wave separated two notions which must not be conflated.
A larger suffix battery refines the available predictive information, so the
task-relevant collision budget cannot increase.  Dynamic closure of the
resulting quotient is different: a refinement can expose successor
distinctions before it separates their sources, making closure fail
temporarily.  Exact residual state restores closure by right congruence.
-/

/-- Inclusion of every coarse suffix in a fine battery is an observation
refinement of the corresponding complete K/M probe signatures. -/
theorem km_probe_family_refinement_induces_observation_refinement
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    {CoarseProbe : Type uCoarseProbe} {FineProbe : Type uFineProbe}
    (coarse : CoarseProbe → List Event)
    (fine : FineProbe → List Event)
    (refines : KMProbeFamilyRefines coarse fine)
    (forecast : Model → List Event → Outcome) :
    ObservationRefines
      (KMProbeForecastSignature coarse forecast)
      (KMProbeForecastSignature fine forecast) := by
  rcases refines with ⟨embed, included⟩
  refine ⟨fun fineSignature model query => fineSignature model (embed query), ?_⟩
  intro history
  funext model query
  simp [KMProbeForecastSignature, included query]

/-- Numerical positive theorem specialized to the laboratory metric: adding
registered suffix probes cannot increase the number of task-relevant history
collisions under a fixed finite universe and target. -/
theorem km_probe_collision_budget_monotone_under_family_refinement
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    {CoarseProbe : Type uCoarseProbe} {FineProbe : Type uFineProbe}
    {RegisteredHistory : Type uHistory} {Target : Type uTarget}
    [Fintype RegisteredHistory] [DecidableEq RegisteredHistory]
    [Fintype Model] [DecidableEq Model]
    [Fintype CoarseProbe] [DecidableEq CoarseProbe]
    [Fintype FineProbe] [DecidableEq FineProbe]
    [DecidableEq Outcome] [DecidableEq Target]
    (historyOf : RegisteredHistory → List Event)
    (coarse : CoarseProbe → List Event)
    (fine : FineProbe → List Event)
    (refines : KMProbeFamilyRefines coarse fine)
    (forecast : Model → List Event → Outcome)
    (target : RegisteredHistory → Target) :
    observationCollisionPairCount
        (fun history => KMProbeForecastSignature fine forecast (historyOf history))
        target ≤
      observationCollisionPairCount
        (fun history => KMProbeForecastSignature coarse forecast (historyOf history))
        target := by
  apply collision_pair_budget_monotone_under_refinement
  rcases km_probe_family_refinement_induces_observation_refinement
      coarse fine refines forecast with ⟨forget, recovers⟩
  exact ⟨forget, fun history => recovers (historyOf history)⟩

/-- The exact residual forecast is dynamically closed under appending any
common event.  This is the terminal closure condition observed at exact probe
depth in the finite wave. -/
theorem km_residual_forecast_dynamic_closure
    {Event : Type uEvent} {Model : Type uModel} {Outcome : Type uOutcome}
    (forecast : Model → List Event → Outcome) (event : Event) :
    DynamicClosure
      (KMResidualForecast forecast)
      (fun history => history ++ [event]) := by
  intro left right sameResidual
  exact km_future_behavior_equivalence_right_congruent
    forecast sameResidual event

/-! ## Finite countermodel: dynamic closure may fail in the middle -/

/-- Four registered worlds with two source worlds whose successors separate. -/
def probeUpdateCounterNext (world : Fin 4) : Fin 4 :=
  if world = 0 then 2 else if world = 1 then 3 else world

/-- The coarsest observation has one cell and is vacuously update-closed. -/
def probeUpdateCounterCoarse (_world : Fin 4) : Unit := ()

/-- The middle observation separates world 3 only.  Worlds 0 and 1 remain
aliased, but their successors 2 and 3 are distinguished. -/
def probeUpdateCounterMiddle (world : Fin 4) : Bool := world = 3

/-- The exact observation separates every registered world. -/
def probeUpdateCounterExact (world : Fin 4) : Fin 4 := world

theorem probe_update_counter_coarse_refines_to_middle :
    ObservationRefines probeUpdateCounterCoarse probeUpdateCounterMiddle := by
  exact ⟨fun _ => (), by intro world; rfl⟩

theorem probe_update_counter_middle_refines_to_exact :
    ObservationRefines probeUpdateCounterMiddle probeUpdateCounterExact := by
  exact ⟨probeUpdateCounterMiddle, by intro world; rfl⟩

theorem probe_update_counter_coarse_is_closed :
    DynamicClosure probeUpdateCounterCoarse probeUpdateCounterNext := by
  intro left right _
  rfl

theorem probe_update_counter_middle_is_not_closed :
    ¬ DynamicClosure probeUpdateCounterMiddle probeUpdateCounterNext := by
  intro closure
  have contradiction : (2 : Fin 4) = 3 := by
    simpa [probeUpdateCounterMiddle, probeUpdateCounterNext] using
      closure (0 : Fin 4) (1 : Fin 4) (by decide)
  have impossible : (2 : Nat) = 3 := congrArg Fin.val contradiction
  omega

theorem probe_update_counter_exact_is_closed :
    DynamicClosure probeUpdateCounterExact probeUpdateCounterNext := by
  intro left right same
  exact congrArg probeUpdateCounterNext same

/-- No-go theorem matching the v1 negative result: even along a two-step
observation-refinement chain, dynamic update closure can follow the pattern
`true → false → true`.  Therefore raw update defect is not a monotone
calibration objective. -/
theorem dynamic_closure_is_not_monotone_under_observation_refinement :
    ObservationRefines probeUpdateCounterCoarse probeUpdateCounterMiddle ∧
      ObservationRefines probeUpdateCounterMiddle probeUpdateCounterExact ∧
      DynamicClosure probeUpdateCounterCoarse probeUpdateCounterNext ∧
      ¬ DynamicClosure probeUpdateCounterMiddle probeUpdateCounterNext ∧
      DynamicClosure probeUpdateCounterExact probeUpdateCounterNext := by
  exact ⟨probe_update_counter_coarse_refines_to_middle,
    probe_update_counter_middle_refines_to_exact,
    probe_update_counter_coarse_is_closed,
    probe_update_counter_middle_is_not_closed,
    probe_update_counter_exact_is_closed⟩

end OCKIndividuationMSpaceComposition
