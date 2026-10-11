import OCMaturityCompletionCycle.BernoulliPredictiveDefect
import OCMaturityCompletionCycle.AbstractionDefect
import Mathlib.Tactic.Positivity

/-!
# Explicit abstraction cost and Pareto frontier

All five declared defects plus state, memory, and compute cost are kept as
separate coordinates.  The costs are declared operational inputs; this module
does not claim they have been measured.  It intentionally provides no universal
scalar selector.
-/

namespace OCMaturityCompletionCycle

/-- Exact nonnegative defect/cost coordinates for one abstraction candidate. -/
structure AbstractionCostProfile where
  predictiveDefect : ℚ
  lumpabilityDefect : ℚ
  boundaryDefect : ℚ
  contextDefect : ℚ
  stitchingDefect : ℚ
  stateCost : ℚ
  memoryCost : ℚ
  computeCost : ℚ
  predictive_nonnegative : 0 ≤ predictiveDefect
  lumpability_nonnegative : 0 ≤ lumpabilityDefect
  boundary_nonnegative : 0 ≤ boundaryDefect
  context_nonnegative : 0 ≤ contextDefect
  stitching_nonnegative : 0 ≤ stitchingDefect
  state_nonnegative : 0 ≤ stateCost
  memory_nonnegative : 0 ≤ memoryCost
  compute_nonnegative : 0 ≤ computeCost

/-- Use the defect's own declared representation costs in the Pareto profile. -/
def AbstractionDefect.toCostProfile
    (defect : AbstractionDefect)
    (predictionNonnegative : 0 ≤ defect.prediction)
    (lumpabilityNonnegative : 0 ≤ defect.lumpability)
    (boundaryNonnegative : 0 ≤ defect.boundary)
    (contextNonnegative : 0 ≤ defect.context)
    (stitchingNonnegative : 0 ≤ defect.stitching) : AbstractionCostProfile where
  predictiveDefect := defect.prediction
  lumpabilityDefect := defect.lumpability
  boundaryDefect := defect.boundary
  contextDefect := defect.context
  stitchingDefect := defect.stitching
  stateCost := defect.stateCost
  memoryCost := defect.memoryCost
  computeCost := defect.resourceCost
  predictive_nonnegative := predictionNonnegative
  lumpability_nonnegative := lumpabilityNonnegative
  boundary_nonnegative := boundaryNonnegative
  context_nonnegative := contextNonnegative
  stitching_nonnegative := stitchingNonnegative
  state_nonnegative := by positivity
  memory_nonnegative := by positivity
  compute_nonnegative := by positivity

/-- Coordinatewise no-worse relation; every coordinate is minimized. -/
def AbstractionCostProfile.NoWorse
    (left right : AbstractionCostProfile) : Prop :=
  left.predictiveDefect ≤ right.predictiveDefect ∧
  left.lumpabilityDefect ≤ right.lumpabilityDefect ∧
  left.boundaryDefect ≤ right.boundaryDefect ∧
  left.contextDefect ≤ right.contextDefect ∧
  left.stitchingDefect ≤ right.stitchingDefect ∧
  left.stateCost ≤ right.stateCost ∧
  left.memoryCost ≤ right.memoryCost ∧
  left.computeCost ≤ right.computeCost

/-- Pareto domination requires no-worse coordinates and one strict gain. -/
def AbstractionCostProfile.Dominates
    (left right : AbstractionCostProfile) : Prop :=
  left.NoWorse right ∧ ¬ right.NoWorse left

/-- Candidate is Pareto efficient inside one frozen finite comparison set. -/
def ParetoEfficient
    {Candidate : Type*}
    (population : Finset Candidate)
    (profile : Candidate → AbstractionCostProfile)
    (candidate : Candidate) : Prop :=
  candidate ∈ population ∧
    ¬ ∃ alternative ∈ population,
      (profile alternative).Dominates (profile candidate)

/-- Profile with lower prediction defect but higher memory cost. -/
def accurateExpensiveProfile : AbstractionCostProfile where
  predictiveDefect := 0
  lumpabilityDefect := 0
  boundaryDefect := 0
  contextDefect := 0
  stitchingDefect := 0
  stateCost := 1
  memoryCost := 1
  computeCost := 1
  predictive_nonnegative := by norm_num
  lumpability_nonnegative := by norm_num
  boundary_nonnegative := by norm_num
  context_nonnegative := by norm_num
  stitching_nonnegative := by norm_num
  state_nonnegative := by norm_num
  memory_nonnegative := by norm_num
  compute_nonnegative := by norm_num

/-- Profile with higher prediction defect but lower resource costs. -/
def lossyCheapProfile : AbstractionCostProfile where
  predictiveDefect := 1
  lumpabilityDefect := 1
  boundaryDefect := 0
  contextDefect := 0
  stitchingDefect := 0
  stateCost := 0
  memoryCost := 0
  computeCost := 0
  predictive_nonnegative := by norm_num
  lumpability_nonnegative := by norm_num
  boundary_nonnegative := by norm_num
  context_nonnegative := by norm_num
  stitching_nonnegative := by norm_num
  state_nonnegative := by norm_num
  memory_nonnegative := by norm_num
  compute_nonnegative := by norm_num

/-- Accuracy/resource tradeoff gives a concrete Pareto incomparability. -/
theorem accurateExpensive_and_lossyCheap_are_pareto_incomparable :
    ¬ accurateExpensiveProfile.Dominates lossyCheapProfile ∧
      ¬ lossyCheapProfile.Dominates accurateExpensiveProfile := by
  constructor <;>
    simp [AbstractionCostProfile.Dominates, AbstractionCostProfile.NoWorse,
      accurateExpensiveProfile, lossyCheapProfile]

end OCMaturityCompletionCycle
