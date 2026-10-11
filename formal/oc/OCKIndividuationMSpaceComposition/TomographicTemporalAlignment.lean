import OCKIndividuationMSpaceComposition.TimeVaryingCoupledPropagation
import OCKIndividuationMSpaceComposition.TomographicLinearVisibility
import Mathlib.Tactic.Abel
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Temporal registration for tomographic projections

Projections collected at different times are not a single static image.  This
module reuses the current time-varying propagation source and gives a minimal
alignment contract.  It deliberately does not infer that a path, branch or
repository is stationary, nor that an endpoint identifies its schedule.
-/

section TemporalReadout

variable {State : Type*} [AddCommGroup State]

/-- One additive measurement row per time and its readout from a propagated
initial state. -/
def temporalProjectionReadout
    (operator : ℕ → State →+ State) (forcing : ℕ → State)
    (row : ℕ → State →+ ℚ) (initial : State) : ℕ → ℚ :=
  fun time => row time
    (timeVaryingCoupledTrajectory operator forcing initial time)

/-- Difference of equal-forcing temporal readouts is the row applied to the
chronologically propagated intervention difference. -/
theorem temporalProjectionReadout_difference
    (operator : ℕ → State →+ State) (forcing : ℕ → State)
    (row : ℕ → State →+ ℚ) (first second : State) (time : ℕ) :
    temporalProjectionReadout operator forcing row first time -
        temporalProjectionReadout operator forcing row second time =
      row time (timeOrderedPropagation operator time (first - second)) := by
  unfold temporalProjectionReadout
  rw [← map_sub]
  rw [timeVaryingCoupledTrajectory_initial_difference_eq_product]

def TemporalProjectionInvisible
    (operator : ℕ → State →+ State) (row : ℕ → State →+ ℚ)
    (difference : State) : Prop :=
  ∀ time, row time (timeOrderedPropagation operator time difference) = 0

theorem temporalProjectionReadout_equal_iff_invisible
    (operator : ℕ → State →+ State) (forcing : ℕ → State)
    (row : ℕ → State →+ ℚ) (first second : State) :
    (∀ time, temporalProjectionReadout operator forcing row first time =
      temporalProjectionReadout operator forcing row second time) ↔
      TemporalProjectionInvisible operator row (first - second) := by
  constructor
  · intro same time
    have difference := temporalProjectionReadout_difference operator forcing row
      first second time
    rw [same time] at difference
    have zero : (0 : ℚ) = row time
        (timeOrderedPropagation operator time (first - second)) := by
      simpa using difference
    exact zero.symm
  · intro invisible time
    have difference := temporalProjectionReadout_difference operator forcing row
      first second time
    rw [invisible time] at difference
    exact sub_eq_zero.mp difference

/-- A temporal row family separates initial states when every nonzero initial
difference reaches at least one visible propagated direction. -/
def TemporallySeparatesInitialState
    (operator : ℕ → State →+ State) (row : ℕ → State →+ ℚ) : Prop :=
  ∀ difference, difference ≠ 0 →
    ∃ time, row time (timeOrderedPropagation operator time difference) ≠ 0

theorem temporally_separating_rows_injective
    (operator : ℕ → State →+ State) (forcing : ℕ → State)
    (row : ℕ → State →+ ℚ)
    (separates : TemporallySeparatesInitialState operator row) :
    Function.Injective (temporalProjectionReadout operator forcing row) := by
  intro first second same
  by_contra distinct
  obtain ⟨time, visible⟩ := separates (first - second) (sub_ne_zero.mpr distinct)
  have equal :=
    (temporalProjectionReadout_equal_iff_invisible operator forcing row
      first second).mp (fun t => congrFun same t)
  exact visible (equal time)

/-- If a nonzero propagated difference is invisible at every time, no temporal
row-action decoder can distinguish the two initial states. -/
theorem temporal_invisible_difference_blocks_initial_injectivity
    (operator : ℕ → State →+ State) (forcing : ℕ → State)
    (row : ℕ → State →+ ℚ) (initialDifference : State)
    (nonzero : initialDifference ≠ 0)
    (invisible : TemporalProjectionInvisible operator row initialDifference) :
    ¬ Function.Injective (temporalProjectionReadout operator forcing row) := by
  intro injective
  apply nonzero
  apply injective
  funext time
  exact (temporalProjectionReadout_equal_iff_invisible operator forcing row
    initialDifference 0).mpr (by simpa only [sub_zero] using invisible) time

end TemporalReadout

section Alignment

variable {State : Type*} [AddCommGroup State]

/-- A registration family maps each propagated state back to the reference
state. The left-inverse law is the explicit calibration/transport obligation.
It is not inferred from timestamps or endpoint equality. -/
structure TemporalRegistration
    (operator : ℕ → State →+ State) where
  pullback : ℕ → State →+ State
  leftInverse : ∀ time state,
    pullback time (timeOrderedPropagation operator time state) = state

def alignedTemporalReadout
    (operator : ℕ → State →+ State) (forcing : ℕ → State)
    (registration : TemporalRegistration operator)
    (row : ℕ → State →+ ℚ) (initial : State) : ℕ → ℚ :=
  fun time => row time (registration.pullback time
    (timeVaryingCoupledTrajectory operator forcing initial time))

theorem alignedTemporalReadout_difference
    (operator : ℕ → State →+ State) (forcing : ℕ → State)
    (registration : TemporalRegistration operator)
    (row : ℕ → State →+ ℚ) (first second : State) (time : ℕ) :
    alignedTemporalReadout operator forcing registration row first time -
        alignedTemporalReadout operator forcing registration row second time =
      row time (first - second) := by
  unfold alignedTemporalReadout
  rw [← map_sub]
  rw [← map_sub]
  rw [timeVaryingCoupledTrajectory_initial_difference_eq_product]
  rw [registration.leftInverse]

theorem aligned_readout_separates_when_rows_separate
    (operator : ℕ → State →+ State) (forcing : ℕ → State)
    (registration : TemporalRegistration operator)
    (row : ℕ → State →+ ℚ)
    (separates : ∀ difference, difference ≠ 0 →
      ∃ time, row time difference ≠ 0) :
    Function.Injective (alignedTemporalReadout operator forcing registration row) := by
  intro first second same
  by_contra distinct
  obtain ⟨time, visible⟩ := separates (first - second)
    (sub_ne_zero.mpr distinct)
  apply visible
  calc
    row time (first - second) =
        alignedTemporalReadout operator forcing registration row first time -
          alignedTemporalReadout operator forcing registration row second time :=
      (alignedTemporalReadout_difference operator forcing registration row first second time).symm
    _ = 0 := by rw [congrFun same time, sub_self]

/-- Reversing the chronological product is not a valid registration shortcut:
the current corpus's concrete noncommutative schedule witness is reused here.
-/
theorem temporal_endpoint_agreement_does_not_license_registration :
    timeVaryingCoupledTrajectory earlyAmplificationSchedule (fun _ => 0) 1 2 =
      timeVaryingCoupledTrajectory lateAmplificationSchedule (fun _ => 0) 1 2 ∧
    timeVaryingCoupledTrajectory earlyAmplificationSchedule (fun _ => 0) 1 1 ≠
      timeVaryingCoupledTrajectory lateAmplificationSchedule (fun _ => 0) 1 1 := by
  exact (endpoint_product_does_not_identify_operator_schedule).2

end Alignment

end OCKIndividuationMSpaceComposition
