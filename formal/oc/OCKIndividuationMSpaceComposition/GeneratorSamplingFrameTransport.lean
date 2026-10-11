import OCKIndividuationMSpaceComposition.GeneratorFrequencyEProcessAdapter
import OCKIndividuationMSpaceComposition.InterventionalContrastIdentification
import Mathlib.Algebra.Order.BigOperators.Group.Finset

namespace OCKIndividuationMSpaceComposition

open scoped BigOperators

universe uCell uGenerator

/-!
# Sampling-frame transport for generator frequencies

The sequential generator-frequency law is a law of the registered observation
stream.  It becomes a target-population law only through an explicit sampling
frame.  The inverse-inclusion identity below is the finite-population
Horvitz--Thompson algebra specialised to OC generator incidence.  The OC-specific
content is the typed frame contract: target weights, inclusion probabilities and
the frozen generator classifier must refer to the same cells and context.

This file also makes selection bias operational.  Its exact numerator is a
weighted cross-deviation between inclusion and incidence.  Positive inclusion
removes that bias by inverse weighting.  A zero-coverage cell supports two
observationally indistinguishable worlds with different target frequencies, so
no decoder can repair the missing frame from selected events alone.
-/

/-- Target mass of a cell-level quantity. -/
def samplingTargetMass
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight quantity : Cell → ℚ) : ℚ :=
  ∑ cell, targetWeight cell * quantity cell

/-- Total target-population weight. -/
def samplingTargetWeight
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight : Cell → ℚ) : ℚ :=
  ∑ cell, targetWeight cell

/-- Expected selected mass before inverse-inclusion correction. -/
def samplingSelectedMass
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight inclusion quantity : Cell → ℚ) : ℚ :=
  ∑ cell, targetWeight cell * inclusion cell * quantity cell

/-- Expected total selected weight. -/
def samplingSelectedWeight
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight inclusion : Cell → ℚ) : ℚ :=
  ∑ cell, targetWeight cell * inclusion cell

/-- Target-population generator frequency. -/
def samplingTargetFrequency
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight incidence : Cell → ℚ) : ℚ :=
  samplingTargetMass targetWeight incidence /
    samplingTargetWeight targetWeight

/-- Frequency in the selected stream before frame correction. -/
def samplingSelectedFrequency
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight inclusion incidence : Cell → ℚ) : ℚ :=
  samplingSelectedMass targetWeight inclusion incidence /
    samplingSelectedWeight targetWeight inclusion

/-- Expected inverse-inclusion mass, written so the selection expectation is
visible as the leading inclusion factor. -/
def inverseInclusionExpectedMass
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight inclusion quantity : Cell → ℚ) : ℚ :=
  ∑ cell,
    inclusion cell *
      (targetWeight cell * quantity cell / inclusion cell)

/-- Expected inverse-inclusion frequency when the target total weight is known. -/
def inverseInclusionExpectedFrequency
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight inclusion incidence : Cell → ℚ) : ℚ :=
  inverseInclusionExpectedMass targetWeight inclusion incidence /
    samplingTargetWeight targetWeight

/-- Typed OC sampling frame.  The classifier version and context binding are
carried by the `Generator` and `Cell` indices chosen by the application; the
numeric fields state the minimum population-transport contract. -/
structure GeneratorSamplingFrame
    (Cell : Type uCell) [Fintype Cell]
    (Generator : Type uGenerator) where
  targetWeight : Cell → ℚ
  inclusionProbability : Cell → ℚ
  incidenceProbability : Cell → Generator → ℚ
  targetWeight_nonnegative : ∀ cell, 0 ≤ targetWeight cell
  targetWeight_normalized : samplingTargetWeight targetWeight = 1
  inclusion_positive : ∀ cell, 0 < inclusionProbability cell
  inclusion_at_most_one : ∀ cell, inclusionProbability cell ≤ 1
  incidence_mem_unit : ∀ cell generator,
    incidenceProbability cell generator ∈ Set.Icc (0 : ℚ) 1

/-- Positive theorem: known nonzero inclusion probabilities recover the exact
target mass in expectation. -/
theorem inverse_inclusion_identifies_target_mass
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight inclusion quantity : Cell → ℚ)
    (inclusionNonzero : ∀ cell, inclusion cell ≠ 0) :
    inverseInclusionExpectedMass targetWeight inclusion quantity =
      samplingTargetMass targetWeight quantity := by
  unfold inverseInclusionExpectedMass samplingTargetMass
  apply Finset.sum_congr rfl
  intro cell _
  field_simp [inclusionNonzero cell]

/-- The corresponding target generator frequency is exactly identified when
the target population has nonzero total weight. -/
theorem inverse_inclusion_identifies_target_frequency
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight inclusion incidence : Cell → ℚ)
    (inclusionNonzero : ∀ cell, inclusion cell ≠ 0)
    (_targetWeightNonzero : samplingTargetWeight targetWeight ≠ 0) :
    inverseInclusionExpectedFrequency targetWeight inclusion incidence =
      samplingTargetFrequency targetWeight incidence := by
  unfold inverseInclusionExpectedFrequency samplingTargetFrequency
  rw [inverse_inclusion_identifies_target_mass _ _ _ inclusionNonzero]

/-- Unnormalised weighted covariance numerator controlling selection bias. -/
def samplingSelectionBiasNumerator
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight inclusion incidence : Cell → ℚ) : ℚ :=
  samplingSelectedMass targetWeight inclusion incidence *
      samplingTargetWeight targetWeight -
    samplingSelectedWeight targetWeight inclusion *
      samplingTargetMass targetWeight incidence

/-- Exact operational selection-bias law.  No asymptotics or independence
approximation is used. -/
theorem selected_frequency_bias_exact
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight inclusion incidence : Cell → ℚ)
    (targetWeightNonzero : samplingTargetWeight targetWeight ≠ 0)
    (selectedWeightNonzero :
      samplingSelectedWeight targetWeight inclusion ≠ 0) :
    samplingSelectedFrequency targetWeight inclusion incidence -
        samplingTargetFrequency targetWeight incidence =
      samplingSelectionBiasNumerator targetWeight inclusion incidence /
        (samplingSelectedWeight targetWeight inclusion *
          samplingTargetWeight targetWeight) := by
  unfold samplingSelectedFrequency samplingTargetFrequency
    samplingSelectionBiasNumerator
  field_simp [targetWeightNonzero, selectedWeightNonzero]

/-- Under nonzero target and selected mass, the naive selected frequency is
transportable exactly iff the registered selection-bias numerator vanishes. -/
theorem selected_frequency_eq_target_iff_zero_bias
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight inclusion incidence : Cell → ℚ)
    (targetWeightNonzero : samplingTargetWeight targetWeight ≠ 0)
    (selectedWeightNonzero :
      samplingSelectedWeight targetWeight inclusion ≠ 0) :
    samplingSelectedFrequency targetWeight inclusion incidence =
        samplingTargetFrequency targetWeight incidence ↔
      samplingSelectionBiasNumerator targetWeight inclusion incidence = 0 := by
  rw [← sub_eq_zero]
  rw [selected_frequency_bias_exact _ _ _ targetWeightNonzero
    selectedWeightNonzero]
  have denominatorNonzero :
      samplingSelectedWeight targetWeight inclusion *
          samplingTargetWeight targetWeight ≠ 0 :=
    mul_ne_zero selectedWeightNonzero targetWeightNonzero
  constructor
  · intro quotientZero
    rcases div_eq_zero_iff.mp quotientZero with numeratorZero | denominatorZero
    · exact numeratorZero
    · exact False.elim (denominatorNonzero denominatorZero)
  · intro numeratorZero
    simp [numeratorZero]

/-- Equal-probability selection is a sufficient special case: the selected and
target frequencies coincide. -/
theorem constant_inclusion_preserves_frequency
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight incidence : Cell → ℚ) (probability : ℚ)
    (probabilityNonzero : probability ≠ 0)
    (targetWeightNonzero : samplingTargetWeight targetWeight ≠ 0) :
    samplingSelectedFrequency targetWeight (fun _ => probability) incidence =
      samplingTargetFrequency targetWeight incidence := by
  have selectedMassFactor :
      samplingSelectedMass targetWeight (fun _ => probability) incidence =
        probability * samplingTargetMass targetWeight incidence := by
    unfold samplingSelectedMass samplingTargetMass
    rw [Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro cell _
    ring
  have selectedWeightFactor :
      samplingSelectedWeight targetWeight (fun _ => probability) =
        probability * samplingTargetWeight targetWeight := by
    unfold samplingSelectedWeight samplingTargetWeight
    rw [Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro cell _
    ring
  unfold samplingSelectedFrequency samplingTargetFrequency
  rw [selectedMassFactor, selectedWeightFactor]
  field_simp [probabilityNonzero, targetWeightNonzero]

/-- Expected inverse weighting with a misspecified inclusion model. -/
def misspecifiedInverseInclusionExpectedMass
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight trueInclusion assumedInclusion quantity : Cell → ℚ) : ℚ :=
  ∑ cell,
    trueInclusion cell *
      (targetWeight cell * quantity cell / assumedInclusion cell)

/-- Expected target frequency when the inverse weights use an assumed sampling
model while selection follows the true one. -/
def misspecifiedInverseInclusionExpectedFrequency
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight trueInclusion assumedInclusion incidence : Cell → ℚ) : ℚ :=
  misspecifiedInverseInclusionExpectedMass targetWeight trueInclusion
      assumedInclusion incidence /
    samplingTargetWeight targetWeight

/-- Exact error law for an assumed rather than true inclusion probability. -/
theorem misspecified_inclusion_error_exact
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight trueInclusion assumedInclusion quantity : Cell → ℚ)
    (assumedNonzero : ∀ cell, assumedInclusion cell ≠ 0) :
    misspecifiedInverseInclusionExpectedMass targetWeight trueInclusion
          assumedInclusion quantity -
        samplingTargetMass targetWeight quantity =
      ∑ cell,
        targetWeight cell * quantity cell *
          (trueInclusion cell - assumedInclusion cell) /
            assumedInclusion cell := by
  unfold misspecifiedInverseInclusionExpectedMass samplingTargetMass
  rw [← Finset.sum_sub_distrib]
  apply Finset.sum_congr rfl
  intro cell _
  field_simp [assumedNonzero cell]

/-- Exact target-frequency error induced by a misspecified inclusion model. -/
theorem misspecified_inclusion_frequency_error_exact
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight trueInclusion assumedInclusion incidence : Cell → ℚ)
    (assumedNonzero : ∀ cell, assumedInclusion cell ≠ 0) :
    misspecifiedInverseInclusionExpectedFrequency targetWeight trueInclusion
          assumedInclusion incidence -
        samplingTargetFrequency targetWeight incidence =
      (∑ cell,
        targetWeight cell * incidence cell *
          (trueInclusion cell - assumedInclusion cell) /
            assumedInclusion cell) /
        samplingTargetWeight targetWeight := by
  unfold misspecifiedInverseInclusionExpectedFrequency samplingTargetFrequency
  rw [← sub_div]
  rw [misspecified_inclusion_error_exact _ _ _ _ assumedNonzero]

/-- A registered per-cell inclusion-model error budget propagates additively to
the target-mass error.  Applications may instantiate the cell budgets from a
positivity floor and calibrated propensity error. -/
theorem misspecified_inclusion_error_bounded_by_cell_budgets
    {Cell : Type uCell} [Fintype Cell]
    (targetWeight trueInclusion assumedInclusion quantity cellBudget : Cell → ℚ)
    (assumedNonzero : ∀ cell, assumedInclusion cell ≠ 0)
    (cellBound : ∀ cell,
      |targetWeight cell * quantity cell *
          (trueInclusion cell - assumedInclusion cell) /
            assumedInclusion cell| ≤ cellBudget cell) :
    |misspecifiedInverseInclusionExpectedMass targetWeight trueInclusion
          assumedInclusion quantity -
        samplingTargetMass targetWeight quantity| ≤
      ∑ cell, cellBudget cell := by
  rw [misspecified_inclusion_error_exact _ _ _ _ assumedNonzero]
  calc
    |∑ cell,
        targetWeight cell * quantity cell *
          (trueInclusion cell - assumedInclusion cell) /
            assumedInclusion cell| ≤
      ∑ cell,
        |targetWeight cell * quantity cell *
          (trueInclusion cell - assumedInclusion cell) /
            assumedInclusion cell| :=
      Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ cell, cellBudget cell := by
      apply Finset.sum_le_sum
      intro cell _
      exact cellBound cell

/-! ## Sharp two-cell falsifiers -/

def twoCellTargetWeight (_cell : Bool) : ℚ := 1

def differentialTwoCellInclusion (cell : Bool) : ℚ :=
  if cell then 1 / 3 else 1

def firstCellIncidence (cell : Bool) : ℚ :=
  if cell then 0 else 1

def secondCellIncidence (cell : Bool) : ℚ :=
  if cell then 1 else 0

def misspecifiedTwoCellInclusion (cell : Bool) : ℚ :=
  if cell then 1 / 2 else 1

/-- Concrete numerical prediction: differential inclusion changes a true
frequency `1/2` into a naive selected frequency `3/4`, an upward bias `1/4`;
inverse inclusion restores `1/2`. -/
theorem differential_selection_has_exact_quarter_bias :
    samplingTargetFrequency twoCellTargetWeight firstCellIncidence = 1 / 2 ∧
    samplingSelectedFrequency twoCellTargetWeight differentialTwoCellInclusion
        firstCellIncidence = 3 / 4 ∧
    samplingSelectedFrequency twoCellTargetWeight differentialTwoCellInclusion
          firstCellIncidence -
        samplingTargetFrequency twoCellTargetWeight firstCellIncidence = 1 / 4 ∧
    inverseInclusionExpectedFrequency twoCellTargetWeight
        differentialTwoCellInclusion firstCellIncidence = 1 / 2 := by
  norm_num [samplingTargetFrequency, samplingSelectedFrequency,
    inverseInclusionExpectedFrequency, inverseInclusionExpectedMass,
    samplingTargetMass, samplingTargetWeight, samplingSelectedMass,
    samplingSelectedWeight, twoCellTargetWeight, differentialTwoCellInclusion,
    firstCellIncidence]

/-- Concrete inclusion-model falsifier: replacing true `1/3` by assumed `1/2`
in the incident cell yields frequency `1/3` instead of `1/2`, error `-1/6`. -/
theorem misspecified_selection_has_exact_sixth_error :
    samplingTargetFrequency twoCellTargetWeight secondCellIncidence = 1 / 2 ∧
    misspecifiedInverseInclusionExpectedFrequency twoCellTargetWeight
        differentialTwoCellInclusion misspecifiedTwoCellInclusion
          secondCellIncidence = 1 / 3 ∧
    misspecifiedInverseInclusionExpectedFrequency twoCellTargetWeight
          differentialTwoCellInclusion misspecifiedTwoCellInclusion
            secondCellIncidence -
        samplingTargetFrequency twoCellTargetWeight secondCellIncidence =
      -(1 / 6) := by
  norm_num [samplingTargetFrequency,
    misspecifiedInverseInclusionExpectedFrequency,
    misspecifiedInverseInclusionExpectedMass, samplingTargetMass,
    samplingTargetWeight, twoCellTargetWeight, differentialTwoCellInclusion,
    misspecifiedTwoCellInclusion, secondCellIncidence]

def zeroCoverageTwoCellInclusion (cell : Bool) : ℚ :=
  if cell then 0 else 1

def hiddenIncidenceWorldA (_cell : Bool) : ℚ := 0

def hiddenIncidenceWorldB (cell : Bool) : ℚ :=
  if cell then 1 else 0

/-- Cellwise selected contribution, the complete observation supplied to the
countermodel decoder. -/
def selectedCellContribution
    {Cell : Type uCell}
    (targetWeight inclusion quantity : Cell → ℚ) (cell : Cell) : ℚ :=
  targetWeight cell * inclusion cell * quantity cell

/-- A zero-inclusion cell makes the two worlds observationally identical. -/
theorem zero_coverage_worlds_have_equal_selected_contributions :
    selectedCellContribution twoCellTargetWeight zeroCoverageTwoCellInclusion
        hiddenIncidenceWorldA =
      selectedCellContribution twoCellTargetWeight zeroCoverageTwoCellInclusion
        hiddenIncidenceWorldB := by
  funext cell
  cases cell <;>
    norm_num [selectedCellContribution, twoCellTargetWeight,
      zeroCoverageTwoCellInclusion, hiddenIncidenceWorldA,
      hiddenIncidenceWorldB]

/-- The same observationally equal worlds have target frequencies `0` and
`1/2`. -/
theorem zero_coverage_worlds_have_distinct_target_frequencies :
    samplingTargetFrequency twoCellTargetWeight hiddenIncidenceWorldA = 0 ∧
    samplingTargetFrequency twoCellTargetWeight hiddenIncidenceWorldB = 1 / 2 := by
  norm_num [samplingTargetFrequency, samplingTargetMass, samplingTargetWeight,
    twoCellTargetWeight, hiddenIncidenceWorldA, hiddenIncidenceWorldB]

/-- Sharp no-go: when a target cell has zero inclusion, no function of all
selected cell contributions can be correct in both compatible worlds. -/
theorem zero_coverage_blocks_universal_target_frequency_decoder
    (decoder : (Bool → ℚ) → ℚ) :
    ¬ (decoder
          (selectedCellContribution twoCellTargetWeight
            zeroCoverageTwoCellInclusion hiddenIncidenceWorldA) =
          samplingTargetFrequency twoCellTargetWeight hiddenIncidenceWorldA ∧
        decoder
          (selectedCellContribution twoCellTargetWeight
            zeroCoverageTwoCellInclusion hiddenIncidenceWorldB) =
          samplingTargetFrequency twoCellTargetWeight hiddenIncidenceWorldB) := by
  intro bothCorrect
  have sameObservation :=
    zero_coverage_worlds_have_equal_selected_contributions
  have sameDecoded := congrArg decoder sameObservation
  have targetEqual :
      samplingTargetFrequency twoCellTargetWeight hiddenIncidenceWorldA =
        samplingTargetFrequency twoCellTargetWeight hiddenIncidenceWorldB := by
    calc
      samplingTargetFrequency twoCellTargetWeight hiddenIncidenceWorldA =
          decoder
            (selectedCellContribution twoCellTargetWeight
              zeroCoverageTwoCellInclusion hiddenIncidenceWorldA) :=
        bothCorrect.1.symm
      _ = decoder
            (selectedCellContribution twoCellTargetWeight
              zeroCoverageTwoCellInclusion hiddenIncidenceWorldB) := sameDecoded
      _ = samplingTargetFrequency twoCellTargetWeight hiddenIncidenceWorldB :=
        bothCorrect.2
  norm_num [samplingTargetFrequency, samplingTargetMass, samplingTargetWeight,
    twoCellTargetWeight, hiddenIncidenceWorldA, hiddenIncidenceWorldB] at targetEqual

end OCKIndividuationMSpaceComposition
