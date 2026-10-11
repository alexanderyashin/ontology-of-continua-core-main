import OCMaturityCompletionCycle.DerivedAbstractionDefects
import Mathlib.Algebra.Order.Ring.Abs
import Mathlib.Tactic.Ring

/-!
# Concrete finite total-variation composition lemmas
-/

namespace OCMaturityCompletionCycle

universe uFine uCoarse uLeft uRight uState uAction

/-- Total variation obeys the triangle inequality on finite probabilities. -/
theorem finiteTotalVariation_triangle
    {Outcome : Type uFine}
    [Fintype Outcome]
    (first middle last : FiniteProbabilityMass Outcome) :
    finiteTotalVariation first last ≤
      finiteTotalVariation first middle + finiteTotalVariation middle last := by
  simp only [finiteTotalVariation]
  rw [← add_div]
  apply div_le_div_of_nonneg_right _ (by norm_num : (0 : ℚ) ≤ 2)
  rw [← Finset.sum_add_distrib]
  exact Finset.sum_le_sum fun outcome _ =>
    abs_sub_le (first.mass outcome) (middle.mass outcome) (last.mass outcome)

/-- Deterministic finite pushforward cannot increase total variation. -/
theorem pushforwardFiniteProbability_nonexpansive
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    [Fintype Fine]
    [Fintype Coarse]
    [DecidableEq Coarse]
    (encode : Fine → Coarse)
    (left right : FiniteProbabilityMass Fine) :
    finiteTotalVariation
        (pushforwardFiniteProbability encode left)
        (pushforwardFiniteProbability encode right) ≤
      finiteTotalVariation left right := by
  classical
  simp only [finiteTotalVariation, pushforwardFiniteProbability]
  apply div_le_div_of_nonneg_right _ (by norm_num : (0 : ℚ) ≤ 2)
  calc
    (∑ target : Coarse,
      |(∑ source : Fine, if encode source = target then left.mass source else 0) -
        ∑ source : Fine, if encode source = target then right.mass source else 0|) =
      ∑ target : Coarse,
        |∑ source : Fine,
          if encode source = target then
            left.mass source - right.mass source else 0| := by
          apply Finset.sum_congr rfl
          intro target _
          congr 1
          rw [← Finset.sum_sub_distrib]
          apply Finset.sum_congr rfl
          intro source _
          split <;> simp_all
    _ ≤ ∑ target : Coarse,
        ∑ source : Fine,
          |if encode source = target then
            left.mass source - right.mass source else 0| := by
      exact Finset.sum_le_sum fun target _ => Finset.abs_sum_le_sum_abs _ _
    _ = ∑ source : Fine, |left.mass source - right.mass source| := by
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro source _
      simpa only [abs_ite, abs_zero, eq_comm, Finset.mem_univ, if_true] using
        (Finset.sum_ite_eq' Finset.univ (encode source)
          (fun _ : Coarse => |left.mass source - right.mass source|))

/-- Independent product of two finite probability masses. -/
def independentProductProbability
    {Left : Type uLeft}
    {Right : Type uRight}
    [Fintype Left]
    [Fintype Right]
    (left : FiniteProbabilityMass Left)
    (right : FiniteProbabilityMass Right) :
    FiniteProbabilityMass (Left × Right) where
  mass outcome := left.mass outcome.1 * right.mass outcome.2
  nonnegative outcome :=
    mul_nonneg (left.nonnegative outcome.1) (right.nonnegative outcome.2)
  normalized := by
    rw [Fintype.sum_prod_type]
    calc
      (∑ leftOutcome : Left,
        ∑ rightOutcome : Right,
          left.mass leftOutcome * right.mass rightOutcome) =
        (∑ leftOutcome : Left, left.mass leftOutcome) *
          ∑ rightOutcome : Right, right.mass rightOutcome := by
            rw [Finset.sum_mul]
            apply Finset.sum_congr rfl
            intro leftOutcome _
            rw [Finset.mul_sum]
      _ = 1 := by rw [left.normalized, right.normalized]; norm_num

/-- Holding the right independent factor fixed preserves finite TV exactly. -/
theorem independentProductProbability_tv_left
    {Left : Type uLeft}
    {Right : Type uRight}
    [Fintype Left]
    [Fintype Right]
    (first second : FiniteProbabilityMass Left)
    (right : FiniteProbabilityMass Right) :
    finiteTotalVariation
        (independentProductProbability first right)
        (independentProductProbability second right) =
      finiteTotalVariation first second := by
  simp only [finiteTotalVariation, independentProductProbability]
  rw [Fintype.sum_prod_type]
  congr 1
  calc
    (∑ leftOutcome : Left,
      ∑ rightOutcome : Right,
        |first.mass leftOutcome * right.mass rightOutcome -
          second.mass leftOutcome * right.mass rightOutcome|) =
      ∑ leftOutcome : Left,
        |first.mass leftOutcome - second.mass leftOutcome| *
          ∑ rightOutcome : Right, right.mass rightOutcome := by
      apply Finset.sum_congr rfl
      intro leftOutcome _
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro rightOutcome _
      rw [← sub_mul, abs_mul, abs_of_nonneg (right.nonnegative rightOutcome)]
    _ = ∑ leftOutcome : Left,
        |first.mass leftOutcome - second.mass leftOutcome| := by
      rw [right.normalized]
      simp

/-- Holding the left independent factor fixed preserves finite TV exactly. -/
theorem independentProductProbability_tv_right
    {Left : Type uLeft}
    {Right : Type uRight}
    [Fintype Left]
    [Fintype Right]
    (left : FiniteProbabilityMass Left)
    (first second : FiniteProbabilityMass Right) :
    finiteTotalVariation
        (independentProductProbability left first)
        (independentProductProbability left second) =
      finiteTotalVariation first second := by
  simp only [finiteTotalVariation, independentProductProbability]
  rw [Fintype.sum_prod_type]
  congr 1
  calc
    (∑ leftOutcome : Left,
      ∑ rightOutcome : Right,
        |left.mass leftOutcome * first.mass rightOutcome -
          left.mass leftOutcome * second.mass rightOutcome|) =
      ∑ leftOutcome : Left,
        left.mass leftOutcome *
          ∑ rightOutcome : Right,
            |first.mass rightOutcome - second.mass rightOutcome| := by
      apply Finset.sum_congr rfl
      intro leftOutcome _
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro rightOutcome _
      rw [← mul_sub, abs_mul, abs_of_nonneg (left.nonnegative leftOutcome)]
    _ = ∑ rightOutcome : Right,
        |first.mass rightOutcome - second.mass rightOutcome| := by
      rw [← Finset.sum_mul, left.normalized]
      simp

/-- Genuine TV product bound for independently factored laws. -/
theorem independentProductProbability_tv_le_sum
    {Left : Type uLeft}
    {Right : Type uRight}
    [Fintype Left]
    [Fintype Right]
    (leftFirst leftSecond : FiniteProbabilityMass Left)
    (rightFirst rightSecond : FiniteProbabilityMass Right) :
    finiteTotalVariation
        (independentProductProbability leftFirst rightFirst)
        (independentProductProbability leftSecond rightSecond) ≤
      finiteTotalVariation leftFirst leftSecond +
        finiteTotalVariation rightFirst rightSecond := by
  calc
    finiteTotalVariation
        (independentProductProbability leftFirst rightFirst)
        (independentProductProbability leftSecond rightSecond) ≤
      finiteTotalVariation
          (independentProductProbability leftFirst rightFirst)
          (independentProductProbability leftSecond rightFirst) +
        finiteTotalVariation
          (independentProductProbability leftSecond rightFirst)
          (independentProductProbability leftSecond rightSecond) :=
      finiteTotalVariation_triangle _ _ _
    _ = finiteTotalVariation leftFirst leftSecond +
        finiteTotalVariation rightFirst rightSecond := by
      rw [independentProductProbability_tv_left,
        independentProductProbability_tv_right]

/-- Evolve a probability mass through one normalized finite kernel row family. -/
def evolveFiniteProbability
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (action : Action)
    (initial : FiniteProbabilityMass State) : FiniteProbabilityMass State where
  mass target := ∑ source, initial.mass source * kernel.mass source action target
  nonnegative target := Finset.sum_nonneg fun source _ =>
    mul_nonneg (initial.nonnegative source)
      (kernel.nonnegative source action target)
  normalized := by
    rw [Finset.sum_comm]
    calc
      (∑ source : State,
        ∑ target : State,
          initial.mass source * kernel.mass source action target) =
        ∑ source : State,
          initial.mass source *
            ∑ target : State, kernel.mass source action target := by
          apply Finset.sum_congr rfl
          intro source _
          rw [Finset.mul_sum]
      _ = ∑ source : State, initial.mass source := by
        apply Finset.sum_congr rfl
        intro source _
        rw [kernel.normalized]
        simp
      _ = 1 := initial.normalized

/-- A common normalized finite kernel is nonexpansive in total variation. -/
theorem evolveFiniteProbability_nonexpansive
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (kernel : FiniteControlledKernel State Action)
    (action : Action)
    (left right : FiniteProbabilityMass State) :
    finiteTotalVariation
        (evolveFiniteProbability kernel action left)
        (evolveFiniteProbability kernel action right) ≤
      finiteTotalVariation left right := by
  simp only [finiteTotalVariation, evolveFiniteProbability]
  apply div_le_div_of_nonneg_right _ (by norm_num : (0 : ℚ) ≤ 2)
  calc
    (∑ target : State,
      |(∑ source : State, left.mass source * kernel.mass source action target) -
        ∑ source : State, right.mass source * kernel.mass source action target|) =
      ∑ target : State,
        |∑ source : State,
          (left.mass source - right.mass source) *
            kernel.mass source action target| := by
        apply Finset.sum_congr rfl
        intro target _
        congr 1
        rw [← Finset.sum_sub_distrib]
        apply Finset.sum_congr rfl
        intro source _
        ring
    _ ≤ ∑ target : State,
        ∑ source : State,
          |(left.mass source - right.mass source) *
            kernel.mass source action target| := by
      exact Finset.sum_le_sum fun target _ => Finset.abs_sum_le_sum_abs _ _
    _ = ∑ source : State, |left.mass source - right.mass source| := by
      rw [Finset.sum_comm]
      apply Finset.sum_congr rfl
      intro source _
      simp_rw [abs_mul, abs_of_nonneg (kernel.nonnegative source action _)]
      rw [← Finset.mul_sum, kernel.normalized]
      simp

/--
One sequential step is bounded by the previous TV plus a declared same-input
kernel-row perturbation bound.  The latter remains an independently checkable
finite quantity, not a hidden composition assumption.
-/
theorem sequentialKernelPerturbation_le_previous_add_rowBound
    {State : Type uState}
    {Action : Type uAction}
    [Fintype State]
    (firstKernel secondKernel : FiniteControlledKernel State Action)
    (action : Action)
    (left right : FiniteProbabilityMass State)
    (epsilon : ℚ)
    (rowMixtureBound :
      finiteTotalVariation
        (evolveFiniteProbability firstKernel action right)
        (evolveFiniteProbability secondKernel action right) ≤ epsilon) :
    finiteTotalVariation
        (evolveFiniteProbability firstKernel action left)
        (evolveFiniteProbability secondKernel action right) ≤
      finiteTotalVariation left right + epsilon := by
  calc
    finiteTotalVariation
        (evolveFiniteProbability firstKernel action left)
        (evolveFiniteProbability secondKernel action right) ≤
      finiteTotalVariation
          (evolveFiniteProbability firstKernel action left)
          (evolveFiniteProbability firstKernel action right) +
        finiteTotalVariation
          (evolveFiniteProbability firstKernel action right)
          (evolveFiniteProbability secondKernel action right) :=
      finiteTotalVariation_triangle _ _ _
    _ ≤ finiteTotalVariation left right + epsilon :=
      add_le_add
        (evolveFiniteProbability_nonexpansive firstKernel action left right)
        rowMixtureBound

end OCMaturityCompletionCycle
