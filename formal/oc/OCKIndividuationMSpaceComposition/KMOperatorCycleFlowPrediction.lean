import OCKIndividuationMSpaceComposition.KMContextContinuationCoherence
import OCKIndividuationMSpaceComposition.OpenDiscreteDynamics

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe uLiftCarrier uLiftCandidate uRepairCandidate

/-!
# Operator, cycle and flow constraints on K/M predictive model classes

This layer turns existing exact OC stock-flow mechanics into model-class
predictions.  Uniform increment bounds generate finite-horizon state bands and
threshold-crossing certificates; positive drift excludes return cycles;
nonpositive drift below threshold excludes crossing.  The final theorems lift
these mechanics over every rank-tied K/M candidate.
-/

/-- A lower bound on every increment generates a computable lower state band. -/
theorem OpenDiscreteDynamics.state_lower_bound_of_increment_lower
    (model : OpenDiscreteDynamics) (lower : ℚ)
    (incrementLower : ∀ t, lower ≤ model.increment t)
    (horizon : ℕ) :
    model.initial + (horizon : ℚ) * lower ≤ model.state horizon := by
  induction horizon with
  | zero => simp
  | succ horizon inductionHypothesis =>
      rw [model.state_succ]
      have nextLower := incrementLower horizon
      push_cast
      linarith

/-- Dually, an upper increment bound generates the upper state band. -/
theorem OpenDiscreteDynamics.state_upper_bound_of_increment_upper
    (model : OpenDiscreteDynamics) (upper : ℚ)
    (incrementUpper : ∀ t, model.increment t ≤ upper)
    (horizon : ℕ) :
    model.state horizon ≤ model.initial + (horizon : ℚ) * upper := by
  induction horizon with
  | zero => simp
  | succ horizon inductionHypothesis =>
      rw [model.state_succ]
      have nextUpper := incrementUpper horizon
      push_cast
      linarith

/-- Exact finite-horizon forecast band from per-step flow bounds. -/
theorem OpenDiscreteDynamics.state_interval_of_increment_interval
    (model : OpenDiscreteDynamics) (lower upper : ℚ)
    (incrementLower : ∀ t, lower ≤ model.increment t)
    (incrementUpper : ∀ t, model.increment t ≤ upper)
    (horizon : ℕ) :
    model.initial + (horizon : ℚ) * lower ≤ model.state horizon ∧
      model.state horizon ≤ model.initial + (horizon : ℚ) * upper :=
  ⟨model.state_lower_bound_of_increment_lower lower incrementLower horizon,
    model.state_upper_bound_of_increment_upper upper incrementUpper horizon⟩

/-- The width of the generated state band is exactly horizon times the
per-step uncertainty width. -/
theorem increment_interval_induces_exact_band_width
    (initial lower upper : ℚ) (horizon : ℕ) :
    (initial + (horizon : ℚ) * upper) -
        (initial + (horizon : ℚ) * lower) =
      (horizon : ℚ) * (upper - lower) := by
  ring

/-- If a threshold has been reached by a horizon, its unique first crossing is
not later than that horizon. -/
theorem OpenDiscreteDynamics.first_crossing_exists_within_of_reaches
    (model : OpenDiscreteDynamics) (threshold : ℚ) (horizon : ℕ)
    (reaches : threshold ≤ model.state horizon) :
    ∃ first, first ≤ horizon ∧ model.CrossesAt threshold first := by
  obtain ⟨first, firstCrossing⟩ :=
    model.first_crossing_exists_of_reaches threshold horizon reaches
  refine ⟨first, ?_, firstCrossing⟩
  by_contra notWithin
  have horizonBefore : horizon < first := Nat.lt_of_not_ge notWithin
  have below := firstCrossing.2 horizon horizonBefore
  linarith

/-- A positive lower-flow certificate whose algebraic lower band reaches the
threshold gives a finite, witnessed first-crossing prediction. -/
theorem OpenDiscreteDynamics.lower_flow_forces_crossing_by
    (model : OpenDiscreteDynamics) (threshold lower : ℚ) (horizon : ℕ)
    (incrementLower : ∀ t, lower ≤ model.increment t)
    (algebraicReach :
      threshold ≤ model.initial + (horizon : ℚ) * lower) :
    ∃ first, first ≤ horizon ∧ model.CrossesAt threshold first := by
  apply model.first_crossing_exists_within_of_reaches threshold horizon
  exact algebraicReach.trans
    (model.state_lower_bound_of_increment_lower lower incrementLower horizon)

/-- Window-flow counterpart of the state lower bound. -/
theorem OpenDiscreteDynamics.windowFlow_lower_bound
    (model : OpenDiscreteDynamics) (lower : ℚ)
    (incrementLower : ∀ t, lower ≤ model.increment t)
    (start period : ℕ) :
    (period : ℚ) * lower ≤ model.windowFlow start period := by
  induction period with
  | zero => simp [OpenDiscreteDynamics.windowFlow]
  | succ period inductionHypothesis =>
      have recurrence :
          model.windowFlow start (period + 1) =
            model.windowFlow start period + model.increment (start + period) := by
        simp [OpenDiscreteDynamics.windowFlow, Finset.sum_range_succ]
      rw [recurrence]
      have nextLower := incrementLower (start + period)
      push_cast
      linarith

/-- Strictly positive flow excludes every positive-period return cycle. -/
theorem OpenDiscreteDynamics.positive_lower_flow_excludes_cycle
    (model : OpenDiscreteDynamics) (lower : ℚ)
    (positiveLower : 0 < lower)
    (incrementLower : ∀ t, lower ≤ model.increment t)
    (start period : ℕ) (positivePeriod : 0 < period) :
    model.state (start + period) ≠ model.state start := by
  intro returns
  have zeroFlow := model.cycle_implies_zero_windowFlow start period returns
  have periodPositive : (0 : ℚ) < (period : ℚ) := by exact_mod_cast positivePeriod
  have positiveProduct : 0 < (period : ℚ) * lower :=
    mul_pos periodPositive positiveLower
  have flowLower := model.windowFlow_lower_bound lower incrementLower start period
  linarith

/-- Below threshold, globally nonpositive flow forbids every finite crossing. -/
theorem OpenDiscreteDynamics.nonpositive_increment_never_crosses
    (model : OpenDiscreteDynamics) (threshold : ℚ)
    (initialBelow : model.initial < threshold)
    (nonpositive : ∀ t, model.increment t ≤ 0) :
    ∀ t, ¬ model.CrossesAt threshold t := by
  intro t crossing
  have upper := model.state_upper_bound_of_increment_upper 0 nonpositive t
  have reached := crossing.1
  simp at upper
  linarith

/-- Common K/M adapter to scalar open dynamics and one declared threshold
question. -/
structure KMOpenFlowInterpretation
    {K : CurrentK}
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K) where
  dynamicsOf : liftSearch.Candidate → OpenDiscreteDynamics
  threshold : ℚ
  horizon : ℕ

/-- Candidate-relative event: the declared threshold has a first crossing by
the declared horizon. -/
def KMOpenFlowInterpretation.crossesBy
    {K : CurrentK}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    (interpretation : KMOpenFlowInterpretation liftSearch)
    (candidate : liftSearch.Candidate) : Prop :=
  ∃ first, first ≤ interpretation.horizon ∧
    (interpretation.dynamicsOf candidate).CrossesAt interpretation.threshold first

/-- Inspectable generative contract: every tied structural minimum has a
positive certified drift whose lower band reaches the common threshold by the
common horizon. -/
structure KMTiedPositiveFlowContract
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMOpenFlowInterpretation liftSearch) where
  lower : liftSearch.Candidate → ℚ
  positive : ∀ candidate, KMTiedResolvingCandidate resolution candidate →
    0 < lower candidate
  incrementLower : ∀ candidate, KMTiedResolvingCandidate resolution candidate →
    ∀ t, lower candidate ≤ (interpretation.dynamicsOf candidate).increment t
  algebraicReach : ∀ candidate, KMTiedResolvingCandidate resolution candidate →
    interpretation.threshold ≤
      (interpretation.dynamicsOf candidate).initial +
        (interpretation.horizon : ℚ) * lower candidate

/-- Generative K/M prediction: the flow contract forces threshold crossing to
be a necessary future of the entire tied model class. -/
theorem km_positive_flow_contract_forces_necessary_crossing
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMOpenFlowInterpretation liftSearch)
    (contract : KMTiedPositiveFlowContract resolution interpretation) :
    KMNecessaryFuture resolution
      (fun candidate (_ : Unit) => interpretation.crossesBy candidate) () := by
  intro candidate tied
  exact (interpretation.dynamicsOf candidate).lower_flow_forces_crossing_by
    interpretation.threshold (contract.lower candidate) interpretation.horizon
    (contract.incrementLower candidate tied)
    (contract.algebraicReach candidate tied)

/-- No-go at the model-class level: a tied positive-flow candidate and a tied
nonpositive-flow candidate below threshold disagree on crossing, so the future
cannot be point identified without further OC constraints or evidence. -/
theorem tied_opposite_flow_regimes_block_crossing_point_identification
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    {pressure : IrreduciblePressureWithin repairSearch activeDemand d}
    {liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {rank : TransitionRank liftSearch}
    (resolution : SelectedPressureResolution pressure liftSearch rank)
    (interpretation : KMOpenFlowInterpretation liftSearch)
    (positiveCandidate nonpositiveCandidate : liftSearch.Candidate)
    (positiveTied : KMTiedResolvingCandidate resolution positiveCandidate)
    (nonpositiveTied : KMTiedResolvingCandidate resolution nonpositiveCandidate)
    (lower : ℚ)
    (positiveIncrementLower : ∀ t,
      lower ≤ (interpretation.dynamicsOf positiveCandidate).increment t)
    (positiveAlgebraicReach : interpretation.threshold ≤
      (interpretation.dynamicsOf positiveCandidate).initial +
        (interpretation.horizon : ℚ) * lower)
    (nonpositiveInitialBelow :
      (interpretation.dynamicsOf nonpositiveCandidate).initial < interpretation.threshold)
    (nonpositiveIncrement : ∀ t,
      (interpretation.dynamicsOf nonpositiveCandidate).increment t ≤ 0) :
    ¬ KMPointIdentified resolution
      (fun candidate (_ : Unit) => interpretation.crossesBy candidate) := by
  apply tied_behavioral_disagreement_blocks_point_identification
    resolution (fun candidate (_ : Unit) => interpretation.crossesBy candidate)
      positiveCandidate nonpositiveCandidate () positiveTied nonpositiveTied
  · exact (interpretation.dynamicsOf positiveCandidate).lower_flow_forces_crossing_by
      interpretation.threshold lower interpretation.horizon
      positiveIncrementLower positiveAlgebraicReach
  · rintro ⟨first, within, crossing⟩
    exact (interpretation.dynamicsOf nonpositiveCandidate).nonpositive_increment_never_crosses
      interpretation.threshold nonpositiveInitialBelow nonpositiveIncrement first crossing

end OCKIndividuationMSpaceComposition
