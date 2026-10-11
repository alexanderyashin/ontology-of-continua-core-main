import OCKIndividuationMSpaceComposition.NestedPredictiveInformationRisk
import OCKIndividuationMSpaceComposition.OriginFeatureObservationRefinement

namespace OCKIndividuationMSpaceComposition

/-!
# Strong raw-baseline discriminator

This module separates two scientifically different ways in which an OC optic
may improve a fitted prediction.

* A feature computed deterministically from the same origin-time raw history
  cannot add oracle predictive expressivity.  A fitted gain can still arise
  from inductive bias, regularisation, optimization or sample efficiency.
* An independently observed OC coordinate can add information only when it
  separates task-relevant worlds that the raw history aliases.

The distinction is the formal interpretation contract for the strong raw
baseline experiment.  It prevents an empirical representation gain from
being promoted into a claim that OC supplied new information about the world.
-/

/-- World-level deterministic predictors which factor through an observation. -/
def ObservationPredictorClass
    {World Observation Outcome : Type*}
    (observe : World → Observation) : Set (World → Outcome) :=
  {predictWorld | ∃ predictObservation : Observation → Outcome,
    ∀ world, predictWorld world = predictObservation (observe world)}

/-- A feature computed from a raw observation cannot create a predictor that
was unavailable to the unrestricted raw-observation class. -/
theorem derived_predictor_class_subset_raw
    {World Raw Derived Outcome : Type*}
    (observeRaw : World → Raw) (derive : Raw → Derived) :
    ObservationPredictorClass (fun world => derive (observeRaw world)) ⊆
      ObservationPredictorClass (Outcome := Outcome) observeRaw := by
  intro predictWorld member
  rcases member with ⟨predictDerived, realizes⟩
  exact ⟨fun raw => predictDerived (derive raw), realizes⟩

/-- Giving an unrestricted raw predictor a deterministic feature alongside
the raw observation leaves its predictor class exactly unchanged. -/
theorem raw_plus_derived_predictor_class_eq_raw
    {World Raw Derived Outcome : Type*}
    (observeRaw : World → Raw) (derive : Raw → Derived) :
    ObservationPredictorClass
        (fun world => (observeRaw world, derive (observeRaw world))) =
      ObservationPredictorClass (Outcome := Outcome) observeRaw := by
  apply Set.ext
  intro predictWorld
  constructor
  · intro member
    rcases member with ⟨predictJoint, realizes⟩
    exact ⟨fun raw => predictJoint (raw, derive raw), realizes⟩
  · intro member
    rcases member with ⟨predictRaw, realizes⟩
    refine ⟨fun joint => predictRaw joint.1, ?_⟩
    intro world
    exact realizes world

/-- Equal model classes have equal attained oracle risk. -/
theorem optimal_risk_equal_of_model_classes_equal
    {Model : Type*}
    (risk : Model → ℝ) (firstClass secondClass : Set Model)
    (classesEqual : firstClass = secondClass)
    (firstOptimal : OptimalRiskWitness risk firstClass)
    (secondOptimal : OptimalRiskWitness risk secondClass) :
    firstOptimal.value = secondOptimal.value := by
  apply le_antisymm
  · exact firstOptimal.optimal secondOptimal.predictor
      (by simpa [classesEqual] using secondOptimal.predictor_admissible)
  · exact secondOptimal.optimal firstOptimal.predictor
      (by simpa [classesEqual] using firstOptimal.predictor_admissible)

/-- **Strong-raw no-go theorem.** If the OC coordinate is a deterministic
function of the same origin-time raw observation and the raw learner ranges
over all observation-measurable deterministic predictors, adjoining that
coordinate cannot improve attained oracle risk. -/
theorem deterministic_oc_feature_has_zero_unrestricted_oracle_gain
    {World Raw OCFeature Outcome : Type*}
    (observeRaw : World → Raw) (deriveOC : Raw → OCFeature)
    (risk : (World → Outcome) → ℝ)
    (rawOptimal : OptimalRiskWitness risk
      (ObservationPredictorClass observeRaw))
    (jointOptimal : OptimalRiskWitness risk
      (ObservationPredictorClass
        (fun world => (observeRaw world, deriveOC (observeRaw world))))) :
    rawOptimal.value - jointOptimal.value = 0 := by
  have classesEqual := raw_plus_derived_predictor_class_eq_raw
    (Outcome := Outcome) observeRaw deriveOC
  have valuesEqual : jointOptimal.value = rawOptimal.value :=
    optimal_risk_equal_of_model_classes_equal risk _ _ classesEqual
      jointOptimal rawOptimal
  linarith

/-- A raw oracle cannot be worse than an oracle restricted to a derived-only
OC representation, because every derived predictor factors through raw. -/
theorem unrestricted_raw_oracle_no_worse_than_derived_oracle
    {World Raw OCFeature Outcome : Type*}
    (observeRaw : World → Raw) (deriveOC : Raw → OCFeature)
    (risk : (World → Outcome) → ℝ)
    (rawOptimal : OptimalRiskWitness risk
      (ObservationPredictorClass observeRaw))
    (derivedOptimal : OptimalRiskWitness risk
      (ObservationPredictorClass
        (fun world => deriveOC (observeRaw world)))) :
    rawOptimal.value ≤ derivedOptimal.value := by
  exact rawOptimal.optimal derivedOptimal.predictor
    (derived_predictor_class_subset_raw
      (Outcome := Outcome) observeRaw deriveOC
      derivedOptimal.predictor_admissible)

/-- Excess risk of a fitted predictor over an attained oracle for its class. -/
def FittedOraclePenalty
    {Model : Type*} {risk : Model → ℝ} {admissible : Set Model}
    (oracle : OptimalRiskWitness risk admissible) (fitted : Model) : ℝ :=
  risk fitted - oracle.value

/-- Oracle gain of the OC information/model class over the raw class. -/
def OCOracleGain
    {Model : Type*} {risk : Model → ℝ}
    {rawClass ocClass : Set Model}
    (rawOracle : OptimalRiskWitness risk rawClass)
    (ocOracle : OptimalRiskWitness risk ocClass) : ℝ :=
  rawOracle.value - ocOracle.value

/-- Observed fitted gain, positive when the OC fitted predictor has less risk. -/
def ObservedOCGain
    {Model : Type*} (risk : Model → ℝ)
    (rawFitted ocFitted : Model) : ℝ :=
  risk rawFitted - risk ocFitted

/-- Exact decomposition of an observed OC gain into oracle information/model
gain and the difference between fitted penalties. -/
theorem observed_oc_gain_decomposition
    {Model : Type*} (risk : Model → ℝ)
    (rawClass ocClass : Set Model)
    (rawOracle : OptimalRiskWitness risk rawClass)
    (ocOracle : OptimalRiskWitness risk ocClass)
    (rawFitted ocFitted : Model) :
    ObservedOCGain risk rawFitted ocFitted =
      OCOracleGain rawOracle ocOracle +
        FittedOraclePenalty rawOracle rawFitted -
        FittedOraclePenalty ocOracle ocFitted := by
  simp [ObservedOCGain, OCOracleGain, FittedOraclePenalty]

/-- When raw and raw-plus-derived OC have the same oracle value, every fitted
OC gain is exactly a penalty difference.  It may be useful, but it is evidence
for inductive bias/regularisation/sample efficiency rather than new origin
information. -/
theorem observed_gain_from_deterministic_feature_is_penalty_difference
    {Model : Type*} (risk : Model → ℝ)
    (rawClass ocClass : Set Model)
    (rawOracle : OptimalRiskWitness risk rawClass)
    (ocOracle : OptimalRiskWitness risk ocClass)
    (rawFitted ocFitted : Model)
    (equalOracleValue : rawOracle.value = ocOracle.value) :
    ObservedOCGain risk rawFitted ocFitted =
      FittedOraclePenalty rawOracle rawFitted -
        FittedOraclePenalty ocOracle ocFitted := by
  simp only [ObservedOCGain, FittedOraclePenalty]
  rw [equalOracleValue]
  ring

/-- A task-relevant incremental observation witness: raw aliases two worlds,
the OC observation separates them, and their task targets differ. -/
structure IncrementalTaskInformationWitness
    {World Raw OCObservation Outcome : Type*}
    (observeRaw : World → Raw)
    (observeOC : World → OCObservation)
    (target : World → Outcome) where
  first : World
  second : World
  rawAlias : observeRaw first = observeRaw second
  ocSeparates : observeOC first ≠ observeOC second
  targetDiffers : target first ≠ target second

/-- A witnessed OC distinction cannot be a deterministic function of the raw
observation.  This is the formal admission condition for an information-gain
interpretation rather than an inductive-bias interpretation. -/
theorem incremental_task_information_not_raw_derived
    {World Raw OCObservation Outcome : Type*}
    (observeRaw : World → Raw)
    (observeOC : World → OCObservation)
    (target : World → Outcome)
    (witness : IncrementalTaskInformationWitness observeRaw observeOC target) :
    ¬ ∃ derive : Raw → OCObservation,
      ∀ world, observeOC world = derive (observeRaw world) := by
  intro derived
  rcases derived with ⟨derive, realizes⟩
  apply witness.ocSeparates
  calc
    observeOC witness.first = derive (observeRaw witness.first) :=
      realizes witness.first
    _ = derive (observeRaw witness.second) := by rw [witness.rawAlias]
    _ = observeOC witness.second := (realizes witness.second).symm

/-- Positive counterpart: on the witnessed pair, the OC observation supports
an exact deterministic task predictor. -/
theorem incremental_task_information_supports_pairwise_exact_prediction
    {World Raw OCObservation Outcome : Type*}
    [DecidableEq OCObservation]
    (observeRaw : World → Raw)
    (observeOC : World → OCObservation)
    (target : World → Outcome)
    (witness : IncrementalTaskInformationWitness observeRaw observeOC target) :
    ∃ predict : OCObservation → Outcome,
      predict (observeOC witness.first) = target witness.first ∧
        predict (observeOC witness.second) = target witness.second :=
  separated_origin_information_supports_two_world_exact_prediction
    observeOC target witness.first witness.second witness.ocSeparates

/-- Any deterministic raw predictor must fail on at least one member of a
task-relevant raw-alias pair.  This is the negative half of the Track-B
discriminator and does not assume a particular learner. -/
theorem raw_alias_forces_pairwise_prediction_failure
    {World Raw OCObservation Outcome : Type*}
    (observeRaw : World → Raw)
    (observeOC : World → OCObservation)
    (target : World → Outcome)
    (witness : IncrementalTaskInformationWitness observeRaw observeOC target)
    (predictRaw : Raw → Outcome) :
    predictRaw (observeRaw witness.first) ≠ target witness.first ∨
      predictRaw (observeRaw witness.second) ≠ target witness.second := by
  by_contra bothCorrect
  push_neg at bothCorrect
  apply witness.targetDiffers
  calc
    target witness.first = predictRaw (observeRaw witness.first) :=
      bothCorrect.1.symm
    _ = predictRaw (observeRaw witness.second) := by rw [witness.rawAlias]
    _ = target witness.second := bothCorrect.2

/-- Zero-one loss used by the exact two-world numerical witness. -/
def BoolZeroOneLoss (predicted actual : Bool) : ℝ :=
  if predicted = actual then 0 else 1

/-- With two equiprobable task-relevant worlds collapsed to the same raw
observation, every deterministic raw predictor has risk exactly `1/2`. -/
theorem uniform_two_world_raw_alias_risk (predictRaw : Unit → Bool) :
    (BoolZeroOneLoss (predictRaw ()) false +
      BoolZeroOneLoss (predictRaw ()) true) / 2 = (1 : ℝ) / 2 := by
  cases value : predictRaw () <;> norm_num [BoolZeroOneLoss, value]

/-- An independently observed Boolean coordinate that distinguishes the two
worlds permits zero risk by the identity predictor. -/
theorem uniform_two_world_incremental_observation_risk :
    (BoolZeroOneLoss false false + BoolZeroOneLoss true true) / 2 = 0 := by
  norm_num [BoolZeroOneLoss]

/-- **Exact numerical positive theorem.** On the uniform two-world witness,
incremental origin information reduces deterministic zero-one Bayes risk by
exactly `1/2`, from `1/2` to `0`. -/
theorem uniform_two_world_incremental_information_strict_gain
    (predictRaw : Unit → Bool) :
    (BoolZeroOneLoss (predictRaw ()) false +
        BoolZeroOneLoss (predictRaw ()) true) / 2 -
      (BoolZeroOneLoss false false + BoolZeroOneLoss true true) / 2 =
        (1 : ℝ) / 2 := by
  rw [uniform_two_world_raw_alias_risk]
  norm_num [BoolZeroOneLoss]

/-! ## Decision rules for the paired held-out discriminator -/

/-- A simultaneous interval with radius `radius` covers a true paired risk
difference when the estimation error is at most that radius. -/
def PairedDifferenceCovered
    (estimate truth radius : ℝ) : Prop :=
  |estimate - truth| ≤ radius

/-- If the entire simultaneous interval is below the negative practical
margin, the true OC-minus-raw risk difference is beneficial beyond margin. -/
theorem upper_bound_below_negative_margin_certifies_oc_benefit
    (estimate truth radius margin : ℝ)
    (covered : PairedDifferenceCovered estimate truth radius)
    (upperBelow : estimate + radius < -margin) :
    truth < -margin := by
  have bounds := (abs_le.mp covered).1
  linarith

/-- If the entire simultaneous interval is above the practical margin, the
true OC-minus-raw risk difference is harmful beyond margin. -/
theorem lower_bound_above_margin_certifies_raw_benefit
    (estimate truth radius margin : ℝ)
    (covered : PairedDifferenceCovered estimate truth radius)
    (lowerAbove : margin < estimate - radius) :
    margin < truth := by
  have bounds := (abs_le.mp covered).2
  linarith

/-- If the simultaneous interval lies inside the practical-equivalence band,
the covered true difference also lies inside that band. -/
theorem interval_inside_margin_certifies_practical_equivalence
    (estimate truth radius margin : ℝ)
    (covered : PairedDifferenceCovered estimate truth radius)
    (lowerInside : -margin ≤ estimate - radius)
    (upperInside : estimate + radius ≤ margin) :
    |truth| ≤ margin := by
  apply abs_le.mpr
  have bounds := abs_le.mp covered
  constructor <;> linarith

/-- Overlap with both signs is genuinely non-identifying: one estimate and
radius can cover opposite true effects. -/
theorem overlapping_interval_cannot_identify_effect_direction :
    PairedDifferenceCovered 0 (-1) 1 ∧
      PairedDifferenceCovered 0 1 1 := by
  norm_num [PairedDifferenceCovered]

end OCKIndividuationMSpaceComposition
