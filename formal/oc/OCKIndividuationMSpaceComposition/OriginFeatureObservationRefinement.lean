import OCKIndividuationMSpaceComposition.SemanticPredictionContract

namespace OCKIndividuationMSpaceComposition

/-!
# Origin-feature observation refinement

This module is the minimal OC adapter between a typed observation available at
the forecast origin and a mature feature-conditional uncertainty learner.  It
does not re-prove conformal validity.  Instead it states exactly what an
observation refinement and its numerical encoding do, and do not, buy.
-/

/-- `fine` refines `coarse` when the coarse observation can be recovered by an
explicit forgetful map.  Refinement is therefore an information statement,
not a target-accuracy claim. -/
def ObservationRefines
    {World Coarse Fine : Type*}
    (coarse : World → Coarse) (fine : World → Fine) : Prop :=
  ∃ forget : Fine → Coarse, ∀ world, forget (fine world) = coarse world

/-- A predictor using coarse information can always be represented on a
refined observation by first forgetting the extra features. -/
theorem coarse_predictor_lifts_through_refinement
    {World Coarse Fine Outcome : Type*}
    (coarse : World → Coarse) (fine : World → Fine)
    (refines : ObservationRefines coarse fine)
    (predict : Coarse → Outcome) :
    ∃ lifted : Fine → Outcome,
      ∀ world, lifted (fine world) = predict (coarse world) := by
  rcases refines with ⟨forget, recovers⟩
  refine ⟨fun information => predict (forget information), ?_⟩
  intro world
  change predict (forget (fine world)) = predict (coarse world)
  rw [recovers world]

/-- Positive two-world boundary: once the origin observation really separates
two worlds, a deterministic predictor exact on those two worlds exists.  This
is an existence result, not a learning or generalization guarantee. -/
theorem separated_origin_information_supports_two_world_exact_prediction
    {World Information Outcome : Type*}
    [DecidableEq Information]
    (observeAtOrigin : World → Information)
    (target : World → Outcome)
    (first second : World)
    (separates : observeAtOrigin first ≠ observeAtOrigin second) :
    ∃ predict : Information → Outcome,
      predict (observeAtOrigin first) = target first ∧
        predict (observeAtOrigin second) = target second := by
  let predict : Information → Outcome := fun information =>
    if information = observeAtOrigin first then target first else target second
  refine ⟨predict, ?_, ?_⟩
  · simp [predict]
  · simp [predict, Ne.symm separates]

/-- Negative complement: adding features without separating the relevant
worlds leaves the exact-prediction obstruction unchanged. -/
theorem nonseparating_origin_refinement_retains_exact_prediction_no_go
    {World Information Outcome : Type*}
    (refinedObservation : World → Information)
    (target : World → Outcome)
    (first second : World)
    (stillAliased : refinedObservation first = refinedObservation second)
    (differentTargets : target first ≠ target second)
    (predict : Information → Outcome) :
    ¬ (predict (refinedObservation first) = target first ∧
      predict (refinedObservation second) = target second) :=
  aliased_information_cannot_predict_distinct_targets_exactly
    refinedObservation target predict first second stillAliased differentTargets

/-- A lossless correspondence between the typed origin feature and the
covariate consumed by a mature learner. -/
structure LosslessOriginFeatureEncoding (Feature Covariate : Type*) where
  encode : Feature → Covariate
  decode : Covariate → Feature
  decode_encode : ∀ feature, decode (encode feature) = feature

namespace LosslessOriginFeatureEncoding

theorem encode_injective
    {Feature Covariate : Type*}
    (encoding : LosslessOriginFeatureEncoding Feature Covariate) :
    Function.Injective encoding.encode := by
  intro first second encodedEqual
  calc
    first = encoding.decode (encoding.encode first) :=
      (encoding.decode_encode first).symm
    _ = encoding.decode (encoding.encode second) := congrArg encoding.decode encodedEqual
    _ = second := encoding.decode_encode second

/-- A lossless numerical adapter cannot collapse a distinction already present
in the typed origin observation. -/
theorem separation_survives_encoding
    {World Feature Covariate : Type*}
    (encoding : LosslessOriginFeatureEncoding Feature Covariate)
    (observeAtOrigin : World → Feature)
    (first second : World)
    (separates : observeAtOrigin first ≠ observeAtOrigin second) :
    encoding.encode (observeAtOrigin first) ≠
      encoding.encode (observeAtOrigin second) := by
  intro encodedEqual
  exact separates (encoding.encode_injective encodedEqual)

end LosslessOriginFeatureEncoding

/-- If an arbitrary feature encoder aliases two origins with different
targets, no downstream deterministic learner can repair the lost distinction.
This isolates an adapter failure from a model-capacity failure. -/
theorem lossy_origin_encoding_cannot_be_repaired_downstream
    {World Feature Covariate Outcome : Type*}
    (observeAtOrigin : World → Feature)
    (encode : Feature → Covariate)
    (target : World → Outcome)
    (predict : Covariate → Outcome)
    (first second : World)
    (encodedAlias :
      encode (observeAtOrigin first) = encode (observeAtOrigin second))
    (differentTargets : target first ≠ target second) :
    ¬ (predict (encode (observeAtOrigin first)) = target first ∧
      predict (encode (observeAtOrigin second)) = target second) :=
  aliased_information_cannot_predict_distinct_targets_exactly
    (fun world => encode (observeAtOrigin world)) target predict
    first second encodedAlias differentTargets

/-- Pointwise validity of a feature-indexed scalar forecast hull.  A mature
method may supply this premise under its own statistical assumptions. -/
def FeatureHullValid
    {World Feature : Type*}
    (observeAtOrigin : World → Feature)
    (target : World → ℝ)
    (forecast : Feature → ScalarForecastHull) : Prop :=
  ∀ world,
    ScalarForecastHull.Contains (forecast (observeAtOrigin world)) (target world)

/-- Correspondence theorem: a validity premise proved for the mature learner's
encoded covariate is exactly sufficient for validity of the typed OC wrapper.
No exchangeability, coverage or transport premise is manufactured here. -/
theorem encoded_feature_hull_validity_lifts_to_typed_observation
    {World Feature Covariate : Type*}
    (encoding : LosslessOriginFeatureEncoding Feature Covariate)
    (observeAtOrigin : World → Feature)
    (target : World → ℝ)
    (matureForecast : Covariate → ScalarForecastHull)
    (matureValidity :
      ∀ world, ScalarForecastHull.Contains
        (matureForecast (encoding.encode (observeAtOrigin world)))
        (target world)) :
    FeatureHullValid observeAtOrigin target
      (fun feature => matureForecast (encoding.encode feature)) := by
  exact matureValidity

/-- Adding a feature which is deterministically derived from the raw origin
observation does not enlarge the class of deterministic point predictors.  The
same predictor can be written as a function of the raw observation alone. -/
theorem deterministically_derived_feature_adds_no_point_predictive_expressivity
    {World Raw Derived Outcome : Type*}
    (observeRaw : World → Raw)
    (derive : Raw → Derived)
    (predict : Raw × Derived → Outcome) :
    ∃ rawPredict : Raw → Outcome,
      ∀ world,
        rawPredict (observeRaw world) =
          predict (observeRaw world, derive (observeRaw world)) := by
  exact ⟨fun raw => predict (raw, derive raw), by intro world; rfl⟩

/-- No-go complement: if two worlds are already aliased by the raw origin
observation, adjoining any deterministic feature of that observation cannot
repair exact prediction for distinct targets. -/
theorem derived_origin_feature_cannot_break_raw_alias
    {World Raw Derived Outcome : Type*}
    (observeRaw : World → Raw)
    (derive : Raw → Derived)
    (target : World → Outcome)
    (predict : Raw × Derived → Outcome)
    (first second : World)
    (rawAlias : observeRaw first = observeRaw second)
    (differentTargets : target first ≠ target second) :
    ¬ (predict (observeRaw first, derive (observeRaw first)) = target first ∧
      predict (observeRaw second, derive (observeRaw second)) = target second) := by
  apply aliased_information_cannot_predict_distinct_targets_exactly
    (fun world => (observeRaw world, derive (observeRaw world)))
    target predict first second
  · simp [rawAlias]
  · exact differentTargets

/-- Observation refinement alone cannot imply exact target prediction: there
is a refined observation which recovers its coarse observation but still
aliases two different targets. -/
theorem observation_refinement_alone_does_not_imply_exact_prediction :
    ∃ (coarse refined : Bool → Unit),
      ObservationRefines coarse refined ∧
      ∀ predict : Unit → Bool,
        ¬ (predict (refined false) = false ∧
          predict (refined true) = true) := by
  let coarse : Bool → Unit := fun _ => ()
  let refined : Bool → Unit := fun _ => ()
  refine ⟨coarse, refined, ?_, ?_⟩
  · exact ⟨id, by intro world; rfl⟩
  · intro predict
    exact aliased_information_cannot_predict_distinct_targets_exactly
      refined id predict false true rfl (by decide)

end OCKIndividuationMSpaceComposition
