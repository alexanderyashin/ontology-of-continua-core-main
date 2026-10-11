import OCKIndividuationMSpaceComposition.KMFlagshipPredictiveChain

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe uModel uLiftCarrier uLiftCandidate uRepairCandidate

/-!
# K/M observation acquisition value

Blackwell comparison, value-of-information and active-learning theory already
provide mature ways to compare experiments and acquisition policies.  This
module does not replace them.  It supplies the missing OC adapter: an
origin-time observation refines the rank-tied K/M class, and its structural
value is the reduction of the sharp prediction band warranted by that class.

The decision formula is deliberately pre-outcome and auditable.  Acquisition
is justified exactly when the priced reduction in structural ambiguity pays
its incremental acquisition cost.  A strict filter refinement need not reduce
the sharp band: removing only interior models has zero structural value.
-/

/-- A sharp numerical band over any explicitly admitted model class. -/
structure ObservationSharpPredictionBand
    {Model : Type uModel}
    (admitted : Model → Prop) (value : Model → ℚ) where
  lower : ℚ
  upper : ℚ
  valid : ∀ model, admitted model → lower ≤ value model ∧ value model ≤ upper
  lowerAttained : ∃ model, admitted model ∧ value model = lower
  upperAttained : ∃ model, admitted model ∧ value model = upper

namespace ObservationSharpPredictionBand

def width
    {Model : Type uModel} {admitted : Model → Prop} {value : Model → ℚ}
    (band : ObservationSharpPredictionBand admitted value) : ℚ :=
  band.upper - band.lower

theorem width_nonnegative
    {Model : Type uModel} {admitted : Model → Prop} {value : Model → ℚ}
    (band : ObservationSharpPredictionBand admitted value) :
    0 ≤ band.width := by
  obtain ⟨model, admittedModel, atLower⟩ := band.lowerAttained
  have bounds := band.valid model admittedModel
  rw [atLower] at bounds
  exact sub_nonneg.mpr bounds.2

/-- Every sound interval over the same admitted class contains the sharp
endpoints. -/
theorem information_optimal
    {Model : Type uModel} {admitted : Model → Prop} {value : Model → ℚ}
    (band : ObservationSharpPredictionBand admitted value)
    (otherLower otherUpper : ℚ)
    (otherValid : ∀ model, admitted model →
      otherLower ≤ value model ∧ value model ≤ otherUpper) :
    otherLower ≤ band.lower ∧ band.upper ≤ otherUpper := by
  obtain ⟨lowerModel, lowerAdmitted, lowerAt⟩ := band.lowerAttained
  obtain ⟨upperModel, upperAdmitted, upperAt⟩ := band.upperAttained
  constructor
  · simpa [lowerAt] using (otherValid lowerModel lowerAdmitted).1
  · simpa [upperAt] using (otherValid upperModel upperAdmitted).2

/-- A genuine observation refinement can only narrow the sharp structural
band, provided both bands are computed over nonempty admitted classes. -/
theorem refinement_narrows
    {Model : Type uModel} {coarse fine : Model → Prop} {value : Model → ℚ}
    (fineRefines : ∀ model, fine model → coarse model)
    (coarseBand : ObservationSharpPredictionBand coarse value)
    (fineBand : ObservationSharpPredictionBand fine value) :
    fineBand.width ≤ coarseBand.width := by
  obtain ⟨fineLowerModel, fineLowerAdmitted, fineLowerAt⟩ :=
    fineBand.lowerAttained
  obtain ⟨fineUpperModel, fineUpperAdmitted, fineUpperAt⟩ :=
    fineBand.upperAttained
  have lowerBounds := coarseBand.valid fineLowerModel
    (fineRefines fineLowerModel fineLowerAdmitted)
  have upperBounds := coarseBand.valid fineUpperModel
    (fineRefines fineUpperModel fineUpperAdmitted)
  rw [fineLowerAt] at lowerBounds
  rw [fineUpperAt] at upperBounds
  dsimp [width]
  linarith

/-- Structural value of an observation: exact reduction of the sharp band at
the common declared forecast target. -/
def acquisitionValue
    {Model : Type uModel} {coarse fine : Model → Prop} {value : Model → ℚ}
    (coarseBand : ObservationSharpPredictionBand coarse value)
    (fineBand : ObservationSharpPredictionBand fine value) : ℚ :=
  coarseBand.width - fineBand.width

theorem acquisitionValue_nonnegative_of_refinement
    {Model : Type uModel} {coarse fine : Model → Prop} {value : Model → ℚ}
    (fineRefines : ∀ model, fine model → coarse model)
    (coarseBand : ObservationSharpPredictionBand coarse value)
    (fineBand : ObservationSharpPredictionBand fine value) :
    0 ≤ acquisitionValue coarseBand fineBand := by
  dsimp [acquisitionValue]
  exact sub_nonneg.mpr (refinement_narrows fineRefines coarseBand fineBand)

/-- Ambiguity-priced decision loss.  `ambiguityPrice` has units of decision
loss per unit of forecast-band width; `acquisitionCost` has decision-loss
units. -/
def acquisitionAdjustedLoss
    {Model : Type uModel} {admitted : Model → Prop} {value : Model → ℚ}
    (ambiguityPrice acquisitionCost : ℚ)
    (band : ObservationSharpPredictionBand admitted value) : ℚ :=
  ambiguityPrice * band.width + acquisitionCost

/-- Exact operational rule.  A refined observation is preferred precisely
when priced structural ambiguity reduction covers incremental acquisition
cost. -/
theorem refined_observation_preferred_iff_value_covers_cost
    {Model : Type uModel} {coarse fine : Model → Prop} {value : Model → ℚ}
    (coarseBand : ObservationSharpPredictionBand coarse value)
    (fineBand : ObservationSharpPredictionBand fine value)
    (ambiguityPrice coarseCost fineCost : ℚ) :
    acquisitionAdjustedLoss ambiguityPrice fineCost fineBand ≤
        acquisitionAdjustedLoss ambiguityPrice coarseCost coarseBand ↔
      ambiguityPrice * acquisitionValue coarseBand fineBand ≥
        fineCost - coarseCost := by
  simp only [acquisitionAdjustedLoss, acquisitionValue, width]
  constructor <;> intro comparison <;> nlinarith

/-- No-go: when a refinement leaves the sharp band unchanged, any strictly
positive incremental acquisition cost makes acquisition decision-inferior. -/
theorem no_acquisition_with_zero_value_and_positive_incremental_cost
    {Model : Type uModel} {coarse fine : Model → Prop} {value : Model → ℚ}
    (coarseBand : ObservationSharpPredictionBand coarse value)
    (fineBand : ObservationSharpPredictionBand fine value)
    (ambiguityPrice coarseCost fineCost : ℚ)
    (zeroValue : acquisitionValue coarseBand fineBand = 0)
    (positiveIncrement : coarseCost < fineCost) :
    ¬ acquisitionAdjustedLoss ambiguityPrice fineCost fineBand ≤
      acquisitionAdjustedLoss ambiguityPrice coarseCost coarseBand := by
  rw [refined_observation_preferred_iff_value_covers_cost]
  rw [zeroValue]
  norm_num
  linarith

end ObservationSharpPredictionBand

/-! ## Exact K/M specialization -/

/-- The observed flagship band is not over an arbitrary model list: admission
is exactly rank-tied K/M resolution intersected with the forecast-origin
observation filter. -/
abbrev KMObservedSharpPredictionBand
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (originAdmits : liftSearch.Candidate → Prop)
    (value : liftSearch.Candidate → ℚ) :=
  ObservationSharpPredictionBand
    (ObservedKMTiedCandidate resolution originAdmits) value

/-- Positive OC bridge: refining the origin observation predicate narrows the
sharp K/M forecast band and therefore has nonnegative structural value. -/
theorem km_origin_observation_refinement_has_nonnegative_value
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    {resolution : SelectedPressureResolution pressure liftSearch rank}
    {coarse fine : liftSearch.Candidate → Prop}
    {value : liftSearch.Candidate → ℚ}
    (fineRefines : ∀ candidate, fine candidate → coarse candidate)
    (coarseBand : KMObservedSharpPredictionBand resolution coarse value)
    (fineBand : KMObservedSharpPredictionBand resolution fine value) :
    0 ≤ ObservationSharpPredictionBand.acquisitionValue coarseBand fineBand := by
  apply ObservationSharpPredictionBand.acquisitionValue_nonnegative_of_refinement
  intro candidate fineAdmitted
  exact ⟨fineAdmitted.1, fineRefines candidate fineAdmitted.2⟩

/-! ## Sharp finite obstruction -/

def threeModelValue (model : Fin 3) : ℚ :=
  if model = 0 then 0 else if model = 1 then (1 : ℚ) / 2 else 1

def allThreeModels (_model : Fin 3) : Prop := True

def endpointModelsOnly (model : Fin 3) : Prop := model = 0 ∨ model = 2

instance allThreeModelsDecidable : DecidablePred allThreeModels :=
  fun _ => isTrue trivial

instance endpointModelsOnlyDecidable : DecidablePred endpointModelsOnly :=
  fun model =>
    if h0 : model = 0 then isTrue (Or.inl h0)
    else if h2 : model = 2 then isTrue (Or.inr h2)
    else isFalse (by
      intro admitted
      rcases admitted with atZero | atTwo
      · exact h0 atZero
      · exact h2 atTwo)

def allThreeModelsBand :
    ObservationSharpPredictionBand allThreeModels threeModelValue where
  lower := 0
  upper := 1
  valid := by
    intro model _
    fin_cases model <;> norm_num [threeModelValue, Fin.ext_iff]
  lowerAttained := ⟨0, trivial, by norm_num [threeModelValue, Fin.ext_iff]⟩
  upperAttained := ⟨2, trivial, by norm_num [threeModelValue, Fin.ext_iff]⟩

def endpointModelsBand :
    ObservationSharpPredictionBand endpointModelsOnly threeModelValue where
  lower := 0
  upper := 1
  valid := by
    intro model admitted
    rcases admitted with atZero | atTwo
    · subst model
      norm_num [threeModelValue, Fin.ext_iff]
    · subst model
      norm_num [threeModelValue, Fin.ext_iff]
  lowerAttained := ⟨0, Or.inl rfl, by norm_num [threeModelValue, Fin.ext_iff]⟩
  upperAttained := ⟨2, Or.inr rfl, by norm_num [threeModelValue, Fin.ext_iff]⟩

/-- Strictly removing a model need not improve the prediction band.  The
removed model may be interior while both endpoint models remain; acquisition
value is then exactly zero. -/
theorem strict_refinement_can_have_zero_acquisition_value :
    (∀ model, endpointModelsOnly model → allThreeModels model) ∧
    (∃ model, allThreeModels model ∧ ¬ endpointModelsOnly model) ∧
    ObservationSharpPredictionBand.acquisitionValue
      allThreeModelsBand endpointModelsBand = 0 := by
  constructor
  · intro model _
    trivial
  constructor
  · refine ⟨1, trivial, ?_⟩
    norm_num [endpointModelsOnly, Fin.ext_iff]
  · norm_num [ObservationSharpPredictionBand.acquisitionValue,
      ObservationSharpPredictionBand.width, allThreeModelsBand,
      endpointModelsBand]

end OCKIndividuationMSpaceComposition
