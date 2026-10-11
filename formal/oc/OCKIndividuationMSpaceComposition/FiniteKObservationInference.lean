import OCKIndividuationMSpaceComposition.KAxisAndCurrentKBridge
import Mathlib.Data.Real.Basic
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uState

/-!
# Finite observation contracts for K-profile inference

The K construction is a quotient of declared distinction profiles.  A finite
experiment sees only the pairs selected by its observation frame.  This module
makes the resulting bridge explicit: exact recovery needs a coverage contract;
an omitted pair is a genuine alias, not a defect that an estimator can repair.

The scalar `coverageFailureUpperBound` is deliberately only an algebraic
budget.  Its probability meaning requires a domain adapter that justifies a
per-trial miss probability and the dependence assumptions behind repeated
trials.
-/

/-- Restrict a distinction profile to pairs actually interrogated by a finite
observation frame. -/
def observedDistinctionProfile
    {State : Type uState}
    (tested : State → State → Prop)
    (profile : DistinctionProfile State) : DistinctionProfile State :=
  fun left right => tested left right ∧ profile left right

/-- A frame is complete for a profile if every true distinction is tested. -/
def ObservationFrameComplete
    {State : Type uState}
    (tested : State → State → Prop)
    (profile : DistinctionProfile State) : Prop :=
  ∀ ⦃left right⦄, profile left right → tested left right

/-- Under an explicit coverage contract, finite observation recovers exactly
the declared distinction profile. -/
theorem observedDistinctionProfile_eq_of_complete
    {State : Type uState}
    (tested : State → State → Prop)
    (profile : DistinctionProfile State)
    (complete : ObservationFrameComplete tested profile) :
    observedDistinctionProfile tested profile = profile := by
  funext left right
  apply propext
  constructor
  · intro observed
    exact observed.2
  · intro distinguished
    exact ⟨complete distinguished, distinguished⟩

/-- If the same observation frame is complete for two profiles, equality of
their observed profiles is sufficient to identify the declared profiles. -/
theorem profile_eq_of_observed_eq_and_complete
    {State : Type uState}
    (tested : State → State → Prop)
    (first second : DistinctionProfile State)
    (firstComplete : ObservationFrameComplete tested first)
    (secondComplete : ObservationFrameComplete tested second)
    (observedEq : observedDistinctionProfile tested first =
      observedDistinctionProfile tested second) :
    first = second := by
  calc
    first = observedDistinctionProfile tested first :=
      (observedDistinctionProfile_eq_of_complete tested first firstComplete).symm
    _ = observedDistinctionProfile tested second := observedEq
    _ = second := observedDistinctionProfile_eq_of_complete tested second secondComplete

/-- A missed tested coordinate admits two different profiles with identical
finite observations.  No downstream learner can distinguish this pair from
that observation alone. -/
theorem omitted_test_pair_creates_observational_alias
    {State : Type uState}
    (tested : State → State → Prop)
    (source target : State)
    (omitted : ¬ tested source target) :
    observedDistinctionProfile tested (fun _ _ => False) =
      observedDistinctionProfile tested
        (fun left right => left = source ∧ right = target) ∧
    (fun _ _ : State => False) ≠
      (fun left right => left = source ∧ right = target) := by
  constructor
  · funext left right
    apply propext
    constructor
    · intro impossible
      exact False.elim impossible.2
    · intro observed
      exact False.elim (omitted (by simpa [observed.2.1, observed.2.2] using observed.1))
  · intro profilesEqual
    have atMissedPair := congrFun (congrFun profilesEqual source) target
    exact (atMissedPair.mpr ⟨rfl, rfl⟩).elim

/-- The union-bound-shaped risk budget for `pairCount` distinguishable
coordinates, per-trial miss factor `q`, and `repeats` independent-equivalent
attempts.  Probability semantics are supplied by a domain adapter. -/
def coverageFailureUpperBound
    (pairCount repeats : Nat)
    (q : ℝ) : ℝ :=
  (pairCount : ℝ) * q ^ repeats

/-- With a nonnegative miss factor at most one, an additional repeat cannot
increase the algebraic coverage-failure budget. -/
theorem coverageFailureUpperBound_antitone_repeats
    (pairCount repeats : Nat)
    {q : ℝ}
    (nonnegative : 0 ≤ q)
    (atMostOne : q ≤ 1) :
    coverageFailureUpperBound pairCount (repeats + 1) q ≤
      coverageFailureUpperBound pairCount repeats q := by
  unfold coverageFailureUpperBound
  rw [pow_succ]
  have countNonnegative : 0 ≤ (pairCount : ℝ) := by positivity
  have powerNonnegative : 0 ≤ q ^ repeats := pow_nonneg nonnegative _
  calc
    (pairCount : ℝ) * (q ^ repeats * q) ≤
        (pairCount : ℝ) * (q ^ repeats * 1) := by gcongr
    _ = (pairCount : ℝ) * q ^ repeats := by ring

/-- If every individual attempt misses with factor one, repeats provide no
coverage improvement: the bound remains the full pair count. -/
theorem coverageFailureUpperBound_one_is_unimproved
    (pairCount repeats : Nat) :
    coverageFailureUpperBound pairCount repeats 1 = pairCount := by
  simp [coverageFailureUpperBound]

/-- A concrete design calculation: 100 coordinates, miss factor 0.1 and five
independent-equivalent attempts give the algebraic upper bound 0.001. -/
theorem hundred_coordinates_five_repeats_point_one_bound :
    coverageFailureUpperBound 100 5 (1 / 10 : ℝ) = 1 / 1000 := by
  norm_num [coverageFailureUpperBound]

end OCKIndividuationMSpaceComposition
