import OCMaturityCompletionCycle.AbstractionDefect
import Mathlib.Tactic.Ring

/-!
# Scoped quantitative composition bounds

These theorems expose every assumption that prevents an invalid composition
claim.  In particular, the parallel theorem takes independent-product
subadditivity as a premise, recurrent feedback takes a strict contraction, and
context transport takes an explicit nonnegative Lipschitz constant.
-/

namespace OCMaturityCompletionCycle

/-- Accumulated local error over a finite horizon. -/
def accumulatedLocalError (localError : Nat → ℚ) : Nat → ℚ
  | 0 => 0
  | horizon + 1 => accumulatedLocalError localError horizon + localError horizon

/-- A uniform local bound gives the finite telescoping `n * epsilon` bound. -/
theorem accumulatedLocalError_le_horizon_mul
    (localError : Nat → ℚ)
    (epsilon : ℚ)
    (localBound : ∀ step, localError step ≤ epsilon) :
    ∀ horizon,
      accumulatedLocalError localError horizon ≤ (horizon : ℚ) * epsilon := by
  intro horizon
  induction horizon with
  | zero => simp [accumulatedLocalError]
  | succ prior inductionHypothesis =>
      calc
        accumulatedLocalError localError (prior + 1) =
            accumulatedLocalError localError prior + localError prior := rfl
        _ ≤ (prior : ℚ) * epsilon + epsilon :=
          add_le_add inductionHypothesis (localBound prior)
        _ = ((prior + 1 : Nat) : ℚ) * epsilon := by
          norm_num [Nat.cast_add, add_mul]

/-- Probability-metric clipping adds the independent unit upper bound. -/
theorem sequentialError_le_min_one_horizon_mul
    (localError : Nat → ℚ)
    (epsilon observed : ℚ)
    (horizon : Nat)
    (localBound : ∀ step, localError step ≤ epsilon)
    (observedBelowAccumulation :
      observed ≤ accumulatedLocalError localError horizon)
    (observedAtMostOne : observed ≤ 1) :
    observed ≤ min 1 ((horizon : ℚ) * epsilon) := by
  apply le_min observedAtMostOne
  exact observedBelowAccumulation.trans
    (accumulatedLocalError_le_horizon_mul localError epsilon localBound horizon)

/--
Independent-product parallel error is subadditive only after the joint law has
been proved to obey the declared product subadditivity inequality.
-/
theorem independentParallelError_le_sum
    (firstError secondError jointError epsilonFirst epsilonSecond : ℚ)
    (firstBound : firstError ≤ epsilonFirst)
    (secondBound : secondError ≤ epsilonSecond)
    (independentProductSubadditivity : jointError ≤ firstError + secondError) :
    jointError ≤ epsilonFirst + epsilonSecond :=
  independentProductSubadditivity.trans (add_le_add firstBound secondBound)

/-- Finite feedback unrolling has the same telescoping bound as any finite loop. -/
theorem finiteFeedbackError_le_horizon_mul
    (loopError : Nat → ℚ)
    (epsilon : ℚ)
    (loopBound : ∀ iteration, loopError iteration ≤ epsilon)
    (horizon : Nat) :
    accumulatedLocalError loopError horizon ≤ (horizon : ℚ) * epsilon :=
  accumulatedLocalError_le_horizon_mul loopError epsilon loopBound horizon

/--
A recurrent self-consistency inequality yields the geometric scale only under
the explicit strict contraction `alpha < 1`.
-/
theorem recurrentFeedbackError_le_geometricScale
    (error epsilon alpha : ℚ)
    (alphaBelowOne : alpha < 1)
    (selfConsistency : error ≤ alpha * error + epsilon) :
    error ≤ epsilon / (1 - alpha) := by
  have denominatorPositive : 0 < 1 - alpha := sub_pos.mpr alphaBelowOne
  apply (le_div_iff₀ denominatorPositive).2
  calc
    error * (1 - alpha) = error - alpha * error := by ring
    _ ≤ epsilon := by
      apply (sub_le_iff_le_add).2
      simpa [add_comm] using selfConsistency

/-- Context error transport needs an explicit nonnegative Lipschitz factor. -/
theorem contextTransportError_le_lipschitzScale
    (before after epsilon lipschitz : ℚ)
    (lipschitzNonnegative : 0 ≤ lipschitz)
    (beforeBound : before ≤ epsilon)
    (transportLipschitz : after ≤ lipschitz * before) :
    after ≤ lipschitz * epsilon :=
  transportLipschitz.trans
    (mul_le_mul_of_nonneg_left beforeBound lipschitzNonnegative)

/-- Nonexpansive transport is the `L = 1` specialization. -/
theorem contextTransportError_nonexpansive
    (before after epsilon : ℚ)
    (beforeBound : before ≤ epsilon)
    (transportNonexpansive : after ≤ before) :
    after ≤ epsilon :=
  transportNonexpansive.trans beforeBound

end OCMaturityCompletionCycle
