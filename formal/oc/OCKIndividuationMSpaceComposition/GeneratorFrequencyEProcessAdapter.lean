import OCKIndividuationMSpaceComposition.DependentInformationBudget
import OCKIndividuationMSpaceComposition.PopulationObservationBounds
import OCKIndividuationMSpaceComposition.SubGaussianEProcess

namespace OCKIndividuationMSpaceComposition

open MeasureTheory ProbabilityTheory
open scoped ENNReal NNReal

/-!
# Generator-incidence frequency and anytime-valid evidence

An observed event may activate several registered generators, so the primitive
observation is a Boolean incidence vector rather than a categorical label.
Each coordinate is embedded in `ℝ`, centred at a candidate incidence
probability, and connected to the already proved sub-Gaussian e-process.

The probability theorem deliberately retains its conditional sub-Gaussian
premise.  Boundedness gives the sharp Hoeffding range width `1`, but conditional
centring and filtration validity are empirical/design obligations and are not
silently inferred from the Boolean type.
-/

/-- Real embedding of one Boolean generator-incidence observation. -/
def generatorIncidenceValue (present : Bool) : ℝ :=
  if present then 1 else 0

/-- Every Boolean incidence observation lies in the unit interval. -/
theorem generatorIncidenceValue_mem_unitInterval (present : Bool) :
    generatorIncidenceValue present ∈ Set.Icc (0 : ℝ) 1 := by
  cases present <;> simp [generatorIncidenceValue]

/-- Centring at an admitted incidence probability gives the exact Hoeffding
range `[-p, 1-p]`. -/
theorem centeredGeneratorIncidence_mem_exactInterval
    (present : Bool) (probability : ℝ) :
    generatorIncidenceValue present - probability ∈
      Set.Icc (-probability) (1 - probability) := by
  cases present <;> simp [generatorIncidenceValue]

/-- The centred Boolean range always has width exactly one, independently of
the candidate frequency. -/
theorem centeredGeneratorIncidence_intervalWidth (probability : ℝ) :
    (1 - probability) - (-probability) = 1 := by
  ring

/-- Centred incidence increment for generator `generator` at event `index`. -/
def generatorIncidenceIncrement
    {Ω Generator : Type*}
    (observation : ℕ → Ω → Generator → Bool)
    (candidateFrequency : Generator → ℝ)
    (generator : Generator) (index : ℕ) (world : Ω) : ℝ :=
  generatorIncidenceValue (observation index world generator) -
    candidateFrequency generator

/-- Exact finite-horizon signed-deviation identity: the cumulative centred
increment is the observed incidence count minus `n * p`. -/
theorem generatorIncidence_cumulativeDeviation_exact
    {Ω Generator : Type*}
    (observation : ℕ → Ω → Generator → Bool)
    (candidateFrequency : Generator → ℝ)
    (generator : Generator) (world : Ω) (horizon : ℕ) :
    (∑ index ∈ Finset.range horizon,
        generatorIncidenceIncrement observation candidateFrequency
          generator index world) =
      (∑ index ∈ Finset.range horizon,
        generatorIncidenceValue (observation index world generator)) -
        horizon * candidateFrequency generator := by
  simp only [generatorIncidenceIncrement, Finset.sum_sub_distrib]
  simp

/-- Constant variance proxy supplied by Hoeffding's width-one bound. -/
noncomputable def generatorIncidenceVarianceProxy : ℕ → ℝ≥0 :=
  fun _ => 1 / 4

/-- Minimum sequential sampling contract for the registered generator family.
The conditional sub-Gaussian field is the precise point where the observation
design must establish conditional centring and dependence control. -/
structure GeneratorIncidenceEProcessContract
    {Ω Generator : Type*}
    {measurableSpace : MeasurableSpace Ω}
    [StandardBorelSpace Ω]
    (filtration : Filtration ℕ measurableSpace)
    (μ : Measure Ω) [IsProbabilityMeasure μ] where
  observation : ℕ → Ω → Generator → Bool
  candidateFrequency : Generator → ℝ
  candidateInUnit : ∀ generator,
    candidateFrequency generator ∈ Set.Icc (0 : ℝ) 1
  incrementMeasurable : ∀ generator index,
    StronglyMeasurable[filtration (index + 1)]
      (generatorIncidenceIncrement observation candidateFrequency
        generator index)
  conditionalSubGaussian : ∀ generator index,
    HasCondSubgaussianMGF (filtration index) (filtration.le index)
      (generatorIncidenceIncrement observation candidateFrequency
        generator index)
      (generatorIncidenceVarianceProxy index) μ

/-- Positive anytime theorem for one registered generator.  At every finite
horizon, crossing the explicit affine signed-deviation boundary has probability
at most `1 / threshold`, with no optional-stopping penalty. -/
theorem generatorIncidence_fixedLambda_anytimeBound
    {Ω Generator : Type*}
    {measurableSpace : MeasurableSpace Ω}
    [StandardBorelSpace Ω]
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    (contract : GeneratorIncidenceEProcessContract filtration μ)
    (generator : Generator)
    {lambda : ℝ} (lambdaPositive : 0 < lambda)
    (threshold : ℝ≥0) (thresholdPositive : 0 < threshold)
    (horizon : ℕ) :
    μ (finiteSubGaussianBoundaryCrossing
      (generatorIncidenceIncrement contract.observation
        contract.candidateFrequency generator)
      generatorIncidenceVarianceProxy lambda threshold horizon) ≤
        ((threshold : ℝ≥0∞)⁻¹) := by
  exact finiteSubGaussianBoundaryCrossing_probability_of_increment_contract
    lambdaPositive (contract.incrementMeasurable generator)
      (contract.conditionalSubGaussian generator)
      threshold thresholdPositive horizon

/-- Familywise union surface for all registered generators. -/
def generatorFamilyBoundaryCrossing
    {Ω Generator : Type*} [Fintype Generator]
    (event : Generator → Set Ω) : Set Ω :=
  ⋃ generator, event generator

/-- Generic finite-family union theorem.  If every coordinate crossing costs
at most `alpha`, the probability that any registered generator crosses is at
most `q * alpha`. -/
theorem generatorFamilyBoundaryCrossing_probability
    {Ω Generator : Type*} [Fintype Generator]
    {measurableSpace : MeasurableSpace Ω}
    (μ : Measure Ω) (event : Generator → Set Ω) (alpha : ℝ≥0∞)
    (perGenerator : ∀ generator, μ (event generator) ≤ alpha) :
    μ (generatorFamilyBoundaryCrossing (Generator := Generator) event) ≤
      (Fintype.card Generator : ℝ≥0∞) * alpha := by
  unfold generatorFamilyBoundaryCrossing
  calc
    μ (⋃ generator, event generator) ≤
        ∑ generator, μ (event generator) :=
      measure_iUnion_fintype_le μ event
    _ ≤ ∑ _generator : Generator, alpha := by
      exact Finset.sum_le_sum fun generator _ => perGenerator generator
    _ = (Fintype.card Generator : ℝ≥0∞) * alpha := by simp

/-- End-to-end familywise anytime bound.  With `q` registered generator
coordinates and the same threshold for each, any coordinate crossing by the
finite horizon costs at most `q / threshold`. -/
theorem generatorIncidence_familywise_fixedLambda_anytimeBound
    {Ω Generator : Type*} [Fintype Generator]
    {measurableSpace : MeasurableSpace Ω}
    [StandardBorelSpace Ω]
    {μ : Measure Ω} [IsProbabilityMeasure μ]
    {filtration : Filtration ℕ measurableSpace}
    (contract : GeneratorIncidenceEProcessContract filtration μ)
    {lambda : ℝ} (lambdaPositive : 0 < lambda)
    (threshold : ℝ≥0) (thresholdPositive : 0 < threshold)
    (horizon : ℕ) :
    μ (generatorFamilyBoundaryCrossing (Generator := Generator) fun generator =>
      finiteSubGaussianBoundaryCrossing
        (generatorIncidenceIncrement contract.observation
          contract.candidateFrequency generator)
        generatorIncidenceVarianceProxy lambda threshold horizon) ≤
      (Fintype.card Generator : ℝ≥0∞) *
        ((threshold : ℝ≥0∞)⁻¹) := by
  apply generatorFamilyBoundaryCrossing_probability
  intro generator
  exact generatorIncidence_fixedLambda_anytimeBound contract generator
    lambdaPositive threshold thresholdPositive horizon

/-- Effective iid-equivalent observations required by the simultaneous
two-sided Hoeffding planning law for `q` generator coordinates. -/
noncomputable def requiredGeneratorFrequencyEffectiveObservations
    (generatorCount epsilon delta : ℝ) : ℝ :=
  requiredRealObservations (2 * generatorCount) delta (2 * epsilon ^ 2)

/-- The generator-frequency budget is exactly the familiar closed form
`log(2q/delta)/(2 epsilon^2)`. -/
theorem requiredGeneratorFrequencyEffectiveObservations_formula
    (generatorCount epsilon delta : ℝ) :
    requiredGeneratorFrequencyEffectiveObservations
        generatorCount epsilon delta =
      Real.log (2 * generatorCount / delta) / (2 * epsilon ^ 2) := by
  rfl

/-- Positive dependence-aware design theorem.  In the declared exchangeable
correlation model, the exact raw-sample threshold supplies the same
simultaneous Hoeffding budget as the iid-equivalent target. -/
theorem exchangeable_generatorFrequency_rawThreshold_guaranteesBudget
    (generatorCount epsilon delta raw correlation : ℝ)
    (generatorCountPositive : 0 < generatorCount)
    (epsilonPositive : 0 < epsilon)
    (deltaPositive : 0 < delta)
    (deltaBelowCompetitors : delta < 2 * generatorCount)
    (correlationNonnegative : 0 ≤ correlation)
    (correlationBelowOne : correlation < 1)
    (belowDependenceCeiling :
      requiredGeneratorFrequencyEffectiveObservations
        generatorCount epsilon delta * correlation < 1)
    (enoughRaw :
      requiredGeneratorFrequencyEffectiveObservations
          generatorCount epsilon delta * (1 - correlation) /
          (1 - requiredGeneratorFrequencyEffectiveObservations
            generatorCount epsilon delta * correlation) ≤ raw) :
    dependentExponentialUnionBudget (2 * generatorCount) raw correlation
        (2 * epsilon ^ 2) ≤ delta := by
  apply exchangeable_raw_threshold_guarantees_budget
    (2 * generatorCount) delta (2 * epsilon ^ 2) raw correlation
  · positivity
  · exact deltaPositive
  · exact deltaBelowCompetitors
  · positivity
  · exact correlationNonnegative
  · exact correlationBelowOne
  · exact belowDependenceCeiling
  · exact enoughRaw

/-- Sharp dependence no-go within the exchangeable model.  If the requested
effective sample reaches the persistent-correlation ceiling `1/rho`, no finite
raw event count can attain the requested iid-equivalent information budget. -/
theorem exchangeable_generatorFrequency_target_unreachable_at_ceiling
    (generatorCount epsilon delta raw correlation : ℝ)
    (rawPositive : 0 < raw)
    (correlationPositive : 0 < correlation)
    (correlationBelowOne : correlation < 1)
    (ceilingBelowTarget :
      1 / correlation ≤
        requiredGeneratorFrequencyEffectiveObservations
          generatorCount epsilon delta) :
    exchangeableEffectiveObservations raw correlation <
      requiredGeneratorFrequencyEffectiveObservations
        generatorCount epsilon delta := by
  exact exchangeable_target_unreachable_at_dependence_ceiling
    raw correlation
      (requiredGeneratorFrequencyEffectiveObservations
        generatorCount epsilon delta)
      rawPositive correlationPositive correlationBelowOne ceilingBelowTarget

/-- A classifier revision can reverse a generator-incidence observation even
when the raw event is unchanged.  Therefore classifier hashes are part of the
observation contract, not object identity or incidental metadata. -/
theorem classifier_change_can_reverse_generatorIncidence :
    (fun event : Bool => event) true ≠
      (fun event : Bool => !event) true := by
  decide

end OCKIndividuationMSpaceComposition
