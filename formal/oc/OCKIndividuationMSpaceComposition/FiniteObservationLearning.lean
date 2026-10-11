import OCKIndividuationMSpaceComposition.UniversalPredictiveDynamics
import Mathlib.Analysis.SpecialFunctions.Exp
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum

namespace OCKIndividuationMSpaceComposition

/-!
# Finite observation and learnability

This module separates three resources: observational sufficiency, finite design
coverage, and statistical concentration.  More rows cannot repair an
insufficient observation map; a sufficient map still needs coverage or a
distributional generalization argument.
-/

universe uWorld uObservation uOutcome uCoarse uFine uHypothesis

structure ObservationExperiment where
  World : Type uWorld
  Observation : Type uObservation
  Outcome : Type uOutcome
  observe : World → Observation
  outcome : World → Outcome

/-- The complete task-relative bounded behavior of an initial state. -/
def BoundedFutureSignature (system : PredictiveSystem) (horizon : Nat) :
    system.State → (system.State → Prop) :=
  fun initial target => TargetFuture system initial horizon target

/-- A horizon-monotone signature records every bounded prediction question up
to the horizon, rather than only the union of reachable states. -/
def CumulativeFutureSignature (system : PredictiveSystem) (horizon : Nat) :
    system.State → (Nat × system.State → Prop) :=
  fun initial point => point.1 ≤ horizon ∧
    TargetFuture system initial point.1 point.2

theorem longer_cumulative_horizon_refines_shorter
    (system : PredictiveSystem) {short long : Nat} (bounded : short ≤ long)
    (left right : system.State)
    (sameLong : CumulativeFutureSignature system long left =
      CumulativeFutureSignature system long right) :
    CumulativeFutureSignature system short left =
      CumulativeFutureSignature system short right := by
  funext point
  apply propext
  constructor
  · intro leftShort
    have leftLong : CumulativeFutureSignature system long left point :=
      ⟨le_trans leftShort.1 bounded, leftShort.2⟩
    have rightLong : CumulativeFutureSignature system long right point := by
      rw [← sameLong]
      exact leftLong
    exact ⟨leftShort.1, rightLong.2⟩
  · intro rightShort
    have rightLong : CumulativeFutureSignature system long right point :=
      ⟨le_trans rightShort.1 bounded, rightShort.2⟩
    have leftLong : CumulativeFutureSignature system long left point := by
      rw [sameLong]
      exact rightLong
    exact ⟨rightShort.1, leftLong.2⟩

/-- An observation is sufficient for a target exactly when the target is
constant on every observation fiber. -/
def ObservationSufficient (experiment : ObservationExperiment) : Prop :=
  ∀ left right,
    experiment.observe left = experiment.observe right →
    experiment.outcome left = experiment.outcome right

def ExactObservationPredictor (experiment : ObservationExperiment)
    (predictor : experiment.Observation → experiment.Outcome) : Prop :=
  ∀ world, predictor (experiment.observe world) = experiment.outcome world

theorem exact_predictor_implies_observation_sufficient
    (experiment : ObservationExperiment)
    (predictor : experiment.Observation → experiment.Outcome)
    (exact : ExactObservationPredictor experiment predictor) :
    ObservationSufficient experiment := by
  intro left right sameObservation
  calc
    experiment.outcome left = predictor (experiment.observe left) := (exact left).symm
    _ = predictor (experiment.observe right) := congrArg predictor sameObservation
    _ = experiment.outcome right := exact right

noncomputable def sufficientObservationPredictor
    (experiment : ObservationExperiment) [Inhabited experiment.Outcome] :
    experiment.Observation → experiment.Outcome := by
  classical
  exact fun observation =>
    if existsWorld : ∃ world, experiment.observe world = observation then
      experiment.outcome (Classical.choose existsWorld)
    else
      default

theorem observation_sufficient_implies_exact_predictor
    (experiment : ObservationExperiment) [Inhabited experiment.Outcome]
    (sufficient : ObservationSufficient experiment) :
    ExactObservationPredictor experiment
      (sufficientObservationPredictor experiment) := by
  intro world
  let existsWorld : ∃ candidate,
      experiment.observe candidate = experiment.observe world := ⟨world, rfl⟩
  simp only [sufficientObservationPredictor, dif_pos existsWorld]
  exact sufficient (Classical.choose existsWorld) world
    (Classical.choose_spec existsWorld)

/-- Equality under the fine observation implies equality under the coarse one. -/
def IsObservationRefinement
    {World : Type uWorld} {Coarse : Type uCoarse} {Fine : Type uFine}
    (coarse : World → Coarse) (fine : World → Fine) : Prop :=
  ∀ left right, fine left = fine right → coarse left = coarse right

/-- The task-relative behavior signature is itself a sufficient observation. -/
theorem target_signature_is_observation_sufficient
    {World : Type uWorld} {Signature : Type uOutcome}
    (signature : World → Signature) :
    ∀ left right, signature left = signature right →
      signature left = signature right := by
  intro left right sameSignature
  exact sameSignature

/-- Every sufficient representation refines the partition induced by the
target behavior signature.  Hence that partition is the coarsest exact
task-relative state representation, up to renaming of cells. -/
theorem every_sufficient_observation_refines_target_signature
    {World : Type uWorld} {Observation : Type uObservation}
    {Signature : Type uOutcome}
    (observe : World → Observation) (signature : World → Signature)
    (sufficient : ∀ left right,
      observe left = observe right → signature left = signature right) :
    IsObservationRefinement signature observe :=
  sufficient

theorem sufficiency_is_monotone_under_refinement
    {World : Type uWorld} {Coarse : Type uCoarse} {Fine : Type uFine}
    {Outcome : Type uOutcome}
    (coarse : World → Coarse) (fine : World → Fine) (outcome : World → Outcome)
    (refines : IsObservationRefinement coarse fine)
    (coarseSufficient : ∀ left right,
      coarse left = coarse right → outcome left = outcome right) :
    ∀ left right, fine left = fine right → outcome left = outcome right := by
  intro left right sameFine
  exact coarseSufficient left right (refines left right sameFine)

theorem sufficient_refinement_must_split_every_outcome_collision
    {World : Type uWorld} {Coarse : Type uCoarse} {Fine : Type uFine}
    {Outcome : Type uOutcome}
    (coarse : World → Coarse) (fine : World → Fine) (outcome : World → Outcome)
    (fineSufficient : ∀ left right,
      fine left = fine right → outcome left = outcome right)
    (left right : World)
    (_sameCoarse : coarse left = coarse right)
    (differentOutcome : outcome left ≠ outcome right) :
    fine left ≠ fine right := by
  intro sameFine
  exact differentOutcome (fineSufficient left right sameFine)

/-- A finite design covers every behaviorally relevant observation fiber. -/
def ObservationDesignCovers
    {World : Type uWorld} {Observation : Type uObservation}
    {sampleSize : Nat}
    (observe : World → Observation) (sample : Fin sampleSize → World) : Prop :=
  ∀ world, ∃ index, observe (sample index) = observe world

noncomputable def coveredSamplePredictor
    {World : Type uWorld} {Observation : Type uObservation}
    {Outcome : Type uOutcome} [Inhabited Outcome] {sampleSize : Nat}
    (observe : World → Observation) (outcome : World → Outcome)
    (sample : Fin sampleSize → World) : Observation → Outcome := by
  classical
  exact fun observation =>
    if existsIndex : ∃ index, observe (sample index) = observation then
      outcome (sample (Classical.choose existsIndex))
    else
      default

theorem covered_sufficient_sample_predictor_is_exact
    {World : Type uWorld} {Observation : Type uObservation}
    {Outcome : Type uOutcome} [Inhabited Outcome] {sampleSize : Nat}
    (observe : World → Observation) (outcome : World → Outcome)
    (sample : Fin sampleSize → World)
    (covers : ObservationDesignCovers observe sample)
    (sufficient : ∀ left right,
      observe left = observe right → outcome left = outcome right) :
    ∀ world,
      coveredSamplePredictor observe outcome sample (observe world) = outcome world := by
  intro world
  rcases covers world with ⟨index, sameObservation⟩
  let existsIndex : ∃ candidate,
      observe (sample candidate) = observe world := ⟨index, sameObservation⟩
  simp only [coveredSamplePredictor, dif_pos existsIndex]
  exact sufficient (sample (Classical.choose existsIndex)) world
    (Classical.choose_spec existsIndex)

/-- Without coverage, two outcome laws can agree on every sampled world and
disagree at one unseen world. -/
def hiddenFlip {World : Type uWorld} [DecidableEq World]
    (hidden : World) : World → Bool :=
  fun world => decide (world = hidden)

theorem unseen_world_supports_indistinguishable_outcome_laws
    {World : Type uWorld} [DecidableEq World] {sampleSize : Nat}
    (sample : Fin sampleSize → World) (hidden : World)
    (unseen : ∀ index, sample index ≠ hidden) :
    (∀ index, (fun _ : World => false) (sample index) =
      hiddenFlip hidden (sample index)) ∧
    (fun _ : World => false) hidden ≠ hiddenFlip hidden hidden := by
  constructor
  · intro index
    simp [hiddenFlip, unseen index]
  · simp [hiddenFlip]

/-- Finite-hypothesis uniform concentration certificate.  A concentration
theorem or a validated sampling design must establish this numerical premise. -/
def UniformConcentrationCertificate
    (sampleSize hypothesisCount : Nat) (epsilon delta : ℝ) : Prop :=
  0 < epsilon ∧ 0 < delta ∧
    2 * (hypothesisCount : ℝ) * Real.exp (-2 * (sampleSize : ℝ) * epsilon ^ 2) ≤ delta

theorem concentration_bound_meets_declared_confidence
    (sampleSize hypothesisCount : Nat) (epsilon delta failureProbability : ℝ)
    (bound : failureProbability ≤
      2 * (hypothesisCount : ℝ) * Real.exp (-2 * (sampleSize : ℝ) * epsilon ^ 2))
    (certificate : UniformConcentrationCertificate
      sampleSize hypothesisCount epsilon delta) :
    failureProbability ≤ delta :=
  le_trans bound certificate.2.2

/-- On the uniform-deviation event, empirical risk minimization has at most
`2 epsilon` excess true risk relative to the chosen comparator. -/
theorem uniform_deviation_erm_excess_risk
    {Hypothesis : Type uHypothesis}
    (trueRisk empiricalRisk : Hypothesis → ℝ)
    (chosen comparator : Hypothesis) (epsilon : ℝ)
    (uniformDeviation : ∀ hypothesis,
      |empiricalRisk hypothesis - trueRisk hypothesis| ≤ epsilon)
    (empiricalOptimal : empiricalRisk chosen ≤ empiricalRisk comparator) :
    trueRisk chosen ≤ trueRisk comparator + 2 * epsilon := by
  have chosenLower := (abs_le.mp (uniformDeviation chosen)).1
  have comparatorUpper := (abs_le.mp (uniformDeviation comparator)).2
  linarith

/-- If each transition contributes at most `epsilon` additional error, the
worst-case horizon error grows at most linearly.  Sharper contractive or mixing
bounds require stronger domain assumptions. -/
theorem additive_transition_error_accumulates_at_most_linearly
    (error : Nat → ℝ) (epsilon : ℝ)
    (initial : error 0 ≤ 0)
    (step : ∀ horizon, error (horizon + 1) ≤ error horizon + epsilon) :
    ∀ horizon, error horizon ≤ (horizon : ℝ) * epsilon := by
  intro horizon
  induction horizon with
  | zero => simpa using initial
  | succ horizon inductionHypothesis =>
      have nextStep := step horizon
      norm_num [Nat.cast_add, Nat.cast_one]
      linarith

end OCKIndividuationMSpaceComposition
