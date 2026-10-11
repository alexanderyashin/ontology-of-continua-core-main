import OCKIndividuationMSpaceComposition.NestedPredictiveInformationRisk

namespace OCKIndividuationMSpaceComposition

/-!
# Context typing refinement

Domain event types are not transported by renaming.  A fine observation
refines a coarse one only when the coarse observation factors through an
explicit collapse map.  This gives compositional laws, monotone
distinguishability and inclusion of all predictors that factor through the
coarse observation.  Finite fitted estimators remain subject to the penalty
versus information-gain boundary proved in `NestedPredictiveInformationRisk`.
-/

section

variable {State Coarse Middle Fine Prediction : Type*}

/-- `fineObserve` refines `coarseObserve` when an explicit collapse recovers
the coarse observation from the fine one on every state. -/
structure ContextObservationRefinement
    (coarseObserve : State → Coarse) (fineObserve : State → Fine) where
  collapse : Fine → Coarse
  factor : ∀ state, coarseObserve state = collapse (fineObserve state)

/-- Every observation refines itself. -/
def ContextObservationRefinement.refl (observe : State → Coarse) :
    ContextObservationRefinement observe observe where
  collapse := id
  factor := by intro state; rfl

/-- Observation refinement composes across domain-adapter layers. -/
def ContextObservationRefinement.trans
    {coarseObserve : State → Coarse} {middleObserve : State → Middle}
    {fineObserve : State → Fine}
    (coarseMiddle : ContextObservationRefinement coarseObserve middleObserve)
    (middleFine : ContextObservationRefinement middleObserve fineObserve) :
    ContextObservationRefinement coarseObserve fineObserve where
  collapse := coarseMiddle.collapse ∘ middleFine.collapse
  factor := by
    intro state
    rw [coarseMiddle.factor state, middleFine.factor state]
    rfl

/-- A collision in the fine observation necessarily remains a collision after
collapse to the coarse observation. -/
theorem ContextObservationRefinement.coarse_collision_of_fine_collision
    {coarseObserve : State → Coarse} {fineObserve : State → Fine}
    (refinement : ContextObservationRefinement coarseObserve fineObserve)
    {left right : State} (fineCollision : fineObserve left = fineObserve right) :
    coarseObserve left = coarseObserve right := by
  rw [refinement.factor left, refinement.factor right, fineCollision]

/-- Equivalently, every distinction visible to the coarse observation is also
visible to the fine observation. -/
theorem ContextObservationRefinement.fine_distinguishes_of_coarse_distinguishes
    {coarseObserve : State → Coarse} {fineObserve : State → Fine}
    (refinement : ContextObservationRefinement coarseObserve fineObserve)
    {left right : State} (coarseDistinct : coarseObserve left ≠ coarseObserve right) :
    fineObserve left ≠ fineObserve right := by
  intro fineCollision
  exact coarseDistinct
    (refinement.coarse_collision_of_fine_collision fineCollision)

/-- A state-level predictor factors through an observation if its output is a
function only of that observation. -/
def FactorsThrough
    (observe : State → Coarse) (predictor : State → Prediction) : Prop :=
  ∃ decode : Coarse → Prediction, ∀ state, predictor state = decode (observe state)

/-- Every predictor available from a coarse observation can be lifted to a
refining observation by precomposing with the explicit collapse. -/
theorem ContextObservationRefinement.factorsThrough_mono
    {coarseObserve : State → Coarse} {fineObserve : State → Fine}
    (refinement : ContextObservationRefinement coarseObserve fineObserve) :
    {predictor : State → Prediction | FactorsThrough coarseObserve predictor} ⊆
      {predictor : State → Prediction | FactorsThrough fineObserve predictor} := by
  intro predictor coarseFactor
  obtain ⟨decode, factor⟩ := coarseFactor
  refine ⟨fun fine => decode (refinement.collapse fine), ?_⟩
  intro state
  rw [factor state, refinement.factor state]

/-- Positive risk theorem for domain typing: under explicit observation
refinement, attained optimal risk over all factoring predictors cannot grow. -/
theorem optimal_risk_antitone_under_observation_refinement
    {coarseObserve : State → Coarse} {fineObserve : State → Fine}
    (refinement : ContextObservationRefinement coarseObserve fineObserve)
    (risk : (State → Prediction) → ℝ)
    (coarseOptimal : OptimalRiskWitness risk
      {predictor | FactorsThrough coarseObserve predictor})
    (fineOptimal : OptimalRiskWitness risk
      {predictor | FactorsThrough fineObserve predictor}) :
    fineOptimal.value ≤ coarseOptimal.value := by
  exact optimal_risk_antitone_under_model_refinement
    risk _ _ refinement.factorsThrough_mono coarseOptimal fineOptimal

/-- No decoder can recover a distinction erased by its observation. -/
theorem factoring_predictor_equal_on_observation_collision
    {observe : State → Coarse} (predictor : State → Prediction)
    (factor : FactorsThrough observe predictor)
    {left right : State} (collision : observe left = observe right) :
    predictor left = predictor right := by
  obtain ⟨decode, predictorFactor⟩ := factor
  rw [predictorFactor left, predictorFactor right, collision]

end

end OCKIndividuationMSpaceComposition
