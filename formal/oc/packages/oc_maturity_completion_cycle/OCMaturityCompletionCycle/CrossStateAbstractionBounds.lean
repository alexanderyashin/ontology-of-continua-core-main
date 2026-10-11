import OCMaturityCompletionCycle.ProcessTVBounds

/-!
# Cross-state abstraction error propagation

These lemmas compare a fine evolution transported through `stateMap` with an
abstract evolution on a genuinely different state type.  The local premise is
the TV defect between each transported fine row and its corresponding
abstract row; policy transport is explicit through `actionMap`.
-/

namespace OCMaturityCompletionCycle

universe uFineState uAbstractState uFineAction uAbstractAction

/-- A normalized mixture of finite laws with a normalized finite weight. -/
def finiteProbabilityMixture
    {Index : Type*}
    {Outcome : Type*}
    [Fintype Index]
    [Fintype Outcome]
    (weight : FiniteProbabilityMass Index)
    (law : Index → FiniteProbabilityMass Outcome) :
    FiniteProbabilityMass Outcome where
  mass outcome := ∑ index, weight.mass index * (law index).mass outcome
  nonnegative outcome := by
    apply Finset.sum_nonneg
    intro index _
    exact mul_nonneg (weight.nonnegative index) ((law index).nonnegative outcome)
  normalized := by
    rw [Finset.sum_comm]
    calc
      (∑ index, ∑ outcome, weight.mass index * (law index).mass outcome) =
          ∑ index, weight.mass index *
            (∑ outcome, (law index).mass outcome) := by
        apply Finset.sum_congr rfl
        intro index _
        rw [Finset.mul_sum]
      _ = ∑ index, weight.mass index := by
        apply Finset.sum_congr rfl
        intro index _
        rw [(law index).normalized]
        simp
      _ = 1 := weight.normalized

/-- TV of two mixtures with common weights is bounded by weighted row TV. -/
theorem finiteProbabilityMixture_tv_le_weighted_row_tv
    {Index : Type*}
    {Outcome : Type*}
    [Fintype Index]
    [Fintype Outcome]
    (weight : FiniteProbabilityMass Index)
    (left right : Index → FiniteProbabilityMass Outcome) :
    finiteTotalVariation
        (finiteProbabilityMixture weight left)
        (finiteProbabilityMixture weight right) ≤
      ∑ index, weight.mass index * finiteTotalVariation (left index) (right index) := by
  simp only [finiteTotalVariation, finiteProbabilityMixture]
  calc
    (∑ outcome,
      |∑ index, weight.mass index * (left index).mass outcome -
        ∑ index, weight.mass index * (right index).mass outcome|) / 2 ≤
        (∑ index, weight.mass index *
          ∑ outcome,
            |(left index).mass outcome - (right index).mass outcome|) / 2 := by
      apply div_le_div_of_nonneg_right _ (by norm_num : (0 : ℚ) ≤ 2)
      calc
        (∑ outcome,
          |∑ index, weight.mass index * (left index).mass outcome -
            ∑ index, weight.mass index * (right index).mass outcome|) =
            ∑ outcome,
              |∑ index, weight.mass index *
                ((left index).mass outcome - (right index).mass outcome)| := by
          apply Finset.sum_congr rfl
          intro outcome _
          congr 1
          rw [← Finset.sum_sub_distrib]
          apply Finset.sum_congr rfl
          intro index _
          ring
        _ ≤ ∑ outcome,
            ∑ index,
              |weight.mass index *
                ((left index).mass outcome - (right index).mass outcome)| := by
          exact Finset.sum_le_sum fun outcome _ => Finset.abs_sum_le_sum_abs _ _
        _ = ∑ index, weight.mass index *
            ∑ outcome,
              |(left index).mass outcome - (right index).mass outcome| := by
          rw [Finset.sum_comm]
          apply Finset.sum_congr rfl
          intro index _
          rw [Finset.mul_sum]
          apply Finset.sum_congr rfl
          intro outcome _
          rw [abs_mul, abs_of_nonneg (weight.nonnegative index)]
    _ = ∑ index, weight.mass index *
        ((∑ outcome,
          |(left index).mass outcome - (right index).mass outcome|) / 2) := by
      rw [div_eq_mul_inv, Finset.sum_mul]
      apply Finset.sum_congr rfl
      intro index _
      ring

/-- Uniform row error bounds the corresponding common-weight mixtures. -/
theorem finiteProbabilityMixture_tv_le_uniform_row_tv
    {Index : Type*}
    {Outcome : Type*}
    [Fintype Index]
    [Fintype Outcome]
    (weight : FiniteProbabilityMass Index)
    (left right : Index → FiniteProbabilityMass Outcome)
    (epsilon : ℚ)
    (uniform : ∀ index, finiteTotalVariation (left index) (right index) ≤ epsilon) :
    finiteTotalVariation
        (finiteProbabilityMixture weight left)
        (finiteProbabilityMixture weight right) ≤ epsilon := by
  calc
    finiteTotalVariation
        (finiteProbabilityMixture weight left)
        (finiteProbabilityMixture weight right) ≤
      ∑ index, weight.mass index * finiteTotalVariation (left index) (right index) :=
        finiteProbabilityMixture_tv_le_weighted_row_tv weight left right
    _ ≤ ∑ index, weight.mass index * epsilon := by
      apply Finset.sum_le_sum
      intro index _
      exact mul_le_mul_of_nonneg_left (uniform index) (weight.nonnegative index)
    _ = epsilon := by
      rw [← Finset.sum_mul, weight.normalized]
      simp

/-- TV defect of every transported fine row against the mapped abstract row. -/
def TransportedKernelRowTVBound
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : FiniteControlledKernel FineState FineAction)
    (abstract : FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (action : FineAction)
    (epsilon : ℚ) : Prop :=
  ∀ state,
    finiteTotalVariation
      (pushforwardFiniteProbability stateMap
        (kernelRowProbability fine state action))
      (kernelRowProbability abstract (stateMap state) (actionMap action)) ≤ epsilon

/-- Pushforward of one fine evolution is the mixture of transported fine rows. -/
theorem pushforward_evolve_mass_eq_transportedRowMixture
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : FiniteControlledKernel FineState FineAction)
    (stateMap : FineState → AbstractState)
    (action : FineAction)
    (initial : FiniteProbabilityMass FineState) :
    (pushforwardFiniteProbability stateMap
      (evolveFiniteProbability fine action initial)).mass =
    (finiteProbabilityMixture initial fun state =>
      pushforwardFiniteProbability stateMap
        (kernelRowProbability fine state action)).mass := by
  funext target
  simp only [pushforwardFiniteProbability, evolveFiniteProbability,
    finiteProbabilityMixture, kernelRowProbability]
  calc
    (∑ fineTarget,
      if stateMap fineTarget = target then
        ∑ source, initial.mass source * fine.mass source action fineTarget
      else 0) =
        ∑ fineTarget, ∑ source,
          if stateMap fineTarget = target then
            initial.mass source * fine.mass source action fineTarget
          else 0 := by
      apply Finset.sum_congr rfl
      intro fineTarget _
      by_cases mapped : stateMap fineTarget = target <;> simp [mapped]
    _ = ∑ source, ∑ fineTarget,
          if stateMap fineTarget = target then
            initial.mass source * fine.mass source action fineTarget
          else 0 := Finset.sum_comm
    _ = ∑ source, initial.mass source *
          ∑ fineTarget,
            if stateMap fineTarget = target then
              fine.mass source action fineTarget
            else 0 := by
      apply Finset.sum_congr rfl
      intro source _
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro fineTarget _
      by_cases mapped : stateMap fineTarget = target <;> simp [mapped]

/-- Abstract evolution of a pushed law is the mixture of mapped abstract rows. -/
theorem evolve_pushforward_mass_eq_mappedAbstractRowMixture
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (abstract : FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (action : AbstractAction)
    (initial : FiniteProbabilityMass FineState) :
    (evolveFiniteProbability abstract action
      (pushforwardFiniteProbability stateMap initial)).mass =
    (finiteProbabilityMixture initial fun state =>
      kernelRowProbability abstract (stateMap state) action).mass := by
  funext target
  simp only [evolveFiniteProbability, pushforwardFiniteProbability,
    finiteProbabilityMixture, kernelRowProbability]
  calc
    (∑ abstractSource,
      (∑ source,
        if stateMap source = abstractSource then initial.mass source else 0) *
        abstract.mass abstractSource action target) =
      ∑ abstractSource, ∑ source,
        (if stateMap source = abstractSource then initial.mass source else 0) *
          abstract.mass abstractSource action target := by
        apply Finset.sum_congr rfl
        intro abstractSource _
        rw [Finset.sum_mul]
    _ = ∑ source, ∑ abstractSource,
        (if stateMap source = abstractSource then initial.mass source else 0) *
          abstract.mass abstractSource action target := Finset.sum_comm
    _ = ∑ source,
        initial.mass source * abstract.mass (stateMap source) action target := by
      apply Finset.sum_congr rfl
      intro source _
      simpa only [ite_mul, zero_mul, eq_comm, Finset.mem_univ, if_true] using
        (Finset.sum_ite_eq' Finset.univ (stateMap source)
          (fun abstractSource =>
            initial.mass source * abstract.mass abstractSource action target))

/-- One-step abstraction error with explicit initial and row defects. -/
theorem transportedEvolve_tv_le_initial_add_rowError
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : FiniteControlledKernel FineState FineAction)
    (abstract : FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (action : FineAction)
    (fineInitial : FiniteProbabilityMass FineState)
    (abstractInitial : FiniteProbabilityMass AbstractState)
    (epsilon : ℚ)
    (uniform : TransportedKernelRowTVBound fine abstract stateMap actionMap
      action epsilon) :
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveFiniteProbability fine action fineInitial))
        (evolveFiniteProbability abstract (actionMap action) abstractInitial) ≤
      finiteTotalVariation
          (pushforwardFiniteProbability stateMap fineInitial) abstractInitial + epsilon := by
  let transportedInitial := pushforwardFiniteProbability stateMap fineInitial
  calc
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveFiniteProbability fine action fineInitial))
        (evolveFiniteProbability abstract (actionMap action) abstractInitial) ≤
      finiteTotalVariation
          (pushforwardFiniteProbability stateMap
            (evolveFiniteProbability fine action fineInitial))
          (evolveFiniteProbability abstract (actionMap action) transportedInitial) +
        finiteTotalVariation
          (evolveFiniteProbability abstract (actionMap action) transportedInitial)
          (evolveFiniteProbability abstract (actionMap action) abstractInitial) :=
      finiteTotalVariation_triangle _ _ _
    _ ≤ epsilon + finiteTotalVariation transportedInitial abstractInitial := by
      apply add_le_add
      · simp only [finiteTotalVariation]
        rw [pushforward_evolve_mass_eq_transportedRowMixture,
          evolve_pushforward_mass_eq_mappedAbstractRowMixture]
        exact finiteProbabilityMixture_tv_le_uniform_row_tv fineInitial _ _ epsilon
          uniform
      · exact evolveFiniteProbability_nonexpansive abstract
          (actionMap action) transportedInitial abstractInitial
    _ = finiteTotalVariation transportedInitial abstractInitial + epsilon := by ring

/-- Sequential cross-state abstraction bound under a mapped action schedule. -/
theorem transportedEvolveMany_tv_le_initial_add_sum_rowError
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : Nat → FiniteControlledKernel FineState FineAction)
    (abstract : Nat → FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (actions : Nat → FineAction)
    (fineInitial : FiniteProbabilityMass FineState)
    (abstractInitial : FiniteProbabilityMass AbstractState)
    (rowError : Nat → ℚ)
    (uniform : ∀ step,
      TransportedKernelRowTVBound (fine step) (abstract step) stateMap actionMap
        (actions step) (rowError step)) :
    ∀ horizon,
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveMany fine actions horizon fineInitial))
        (evolveMany abstract (fun step => actionMap (actions step)) horizon
          abstractInitial) ≤
      finiteTotalVariation
          (pushforwardFiniteProbability stateMap fineInitial) abstractInitial +
        ∑ step ∈ Finset.range horizon, rowError step := by
  intro horizon
  induction horizon with
  | zero => simp [evolveMany]
  | succ prior inductionHypothesis =>
      calc
        finiteTotalVariation
            (pushforwardFiniteProbability stateMap
              (evolveMany fine actions (prior + 1) fineInitial))
            (evolveMany abstract (fun step => actionMap (actions step))
              (prior + 1) abstractInitial) ≤
          finiteTotalVariation
              (pushforwardFiniteProbability stateMap
                (evolveMany fine actions prior fineInitial))
              (evolveMany abstract (fun step => actionMap (actions step)) prior
                abstractInitial) + rowError prior := by
            exact transportedEvolve_tv_le_initial_add_rowError
              (fine prior) (abstract prior) stateMap actionMap (actions prior)
              (evolveMany fine actions prior fineInitial)
              (evolveMany abstract (fun step => actionMap (actions step)) prior
                abstractInitial)
              (rowError prior) (uniform prior)
        _ ≤ (finiteTotalVariation
              (pushforwardFiniteProbability stateMap fineInitial) abstractInitial +
            ∑ step ∈ Finset.range prior, rowError step) + rowError prior :=
          by
            simpa [add_comm] using
              (add_le_add_right inductionHypothesis (rowError prior))
        _ = finiteTotalVariation
              (pushforwardFiniteProbability stateMap fineInitial) abstractInitial +
            ∑ step ∈ Finset.range (prior + 1), rowError step := by
          rw [Finset.sum_range_succ]
          ring

/--
The cross-state abstraction error is also clipped by the probability-law
diameter.  This is the abstraction-specific `min 1` statement; it is not the
same-state perturbation lemma from `ProcessTVBounds`.
-/
theorem transportedEvolveMany_tv_le_min_one_initial_add_sum_rowError
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : Nat → FiniteControlledKernel FineState FineAction)
    (abstract : Nat → FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (actions : Nat → FineAction)
    (fineInitial : FiniteProbabilityMass FineState)
    (abstractInitial : FiniteProbabilityMass AbstractState)
    (rowError : Nat → ℚ)
    (uniform : ∀ step,
      TransportedKernelRowTVBound (fine step) (abstract step) stateMap actionMap
        (actions step) (rowError step))
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveMany fine actions horizon fineInitial))
        (evolveMany abstract (fun step => actionMap (actions step)) horizon
          abstractInitial) ≤
      min 1 (finiteTotalVariation
          (pushforwardFiniteProbability stateMap fineInitial) abstractInitial +
        ∑ step ∈ Finset.range horizon, rowError step) := by
  apply le_min
  · exact finiteTotalVariation_le_one _ _
  · exact transportedEvolveMany_tv_le_initial_add_sum_rowError fine abstract
      stateMap actionMap actions fineInitial abstractInitial rowError uniform horizon

/-- Uniform transported-row error gives the cross-state `n * epsilon` bound. -/
theorem transportedEvolveMany_tv_le_min_one_initial_add_horizon_mul
    {FineState : Type uFineState}
    {AbstractState : Type uAbstractState}
    {FineAction : Type uFineAction}
    {AbstractAction : Type uAbstractAction}
    [Fintype FineState]
    [Fintype AbstractState]
    [DecidableEq AbstractState]
    (fine : Nat → FiniteControlledKernel FineState FineAction)
    (abstract : Nat → FiniteControlledKernel AbstractState AbstractAction)
    (stateMap : FineState → AbstractState)
    (actionMap : FineAction → AbstractAction)
    (actions : Nat → FineAction)
    (fineInitial : FiniteProbabilityMass FineState)
    (abstractInitial : FiniteProbabilityMass AbstractState)
    (epsilon : ℚ)
    (uniform : ∀ step,
      TransportedKernelRowTVBound (fine step) (abstract step) stateMap actionMap
        (actions step) epsilon)
    (horizon : Nat) :
    finiteTotalVariation
        (pushforwardFiniteProbability stateMap
          (evolveMany fine actions horizon fineInitial))
        (evolveMany abstract (fun step => actionMap (actions step)) horizon
          abstractInitial) ≤
      min 1 (finiteTotalVariation
          (pushforwardFiniteProbability stateMap fineInitial) abstractInitial +
        (horizon : ℚ) * epsilon) := by
  simpa using
    (transportedEvolveMany_tv_le_min_one_initial_add_sum_rowError fine abstract
      stateMap actionMap actions fineInitial abstractInitial (fun _ => epsilon)
      uniform horizon)

end OCMaturityCompletionCycle
