import OCKIndividuationMSpaceComposition.CoupledAffinePropagation
import OCKIndividuationMSpaceComposition.TimeVaryingCoupledPropagation

namespace OCKIndividuationMSpaceComposition

variable {X : Type*} [AddCommGroup X]

/-- A single declared operator change at `cut`: `before` then `after`. -/
def twoRegimeOperator
    (before after : X →+ X) (cut : ℕ) : ℕ → X →+ X :=
  fun t => if t < cut then before else after

/-- Before or at the cut, the ordered product contains only the first regime. -/
theorem timeOrderedPropagation_twoRegime_before_or_at
    (before after : X →+ X) (cut horizon : ℕ) (within : horizon ≤ cut) :
    timeOrderedPropagation (twoRegimeOperator before after cut) horizon =
      couplingPower before horizon := by
  induction horizon with
  | zero => rfl
  | succ horizon ih =>
      have beforeCut : horizon < cut := Nat.lt_of_succ_le within
      have prefixWithin : horizon ≤ cut := Nat.le_of_lt beforeCut
      simp [timeOrderedPropagation, couplingPower, twoRegimeOperator, beforeCut,
        ih prefixWithin]

/--
Exact split law after a change point: `B^k A^cut`, with chronological order
preserved even when the two operators do not commute.
-/
theorem timeOrderedPropagation_twoRegime_at_cut_add
    (before after : X →+ X) (cut afterSteps : ℕ) :
    timeOrderedPropagation (twoRegimeOperator before after cut)
        (cut + afterSteps) =
      (couplingPower after afterSteps).comp (couplingPower before cut) := by
  induction afterSteps with
  | zero =>
      simp [timeOrderedPropagation_twoRegime_before_or_at before after cut cut
        (Nat.le_refl cut), couplingPower]
  | succ afterSteps ih =>
      have notBefore : ¬ cut + afterSteps < cut :=
        Nat.not_lt_of_ge (Nat.le_add_right cut afterSteps)
      rw [Nat.add_succ]
      simp only [timeOrderedPropagation, couplingPower]
      rw [ih]
      simp [twoRegimeOperator, notBefore, AddMonoidHom.comp_assoc]

/-- If both regimes are the same, the alleged cut disappears extensionally. -/
theorem twoRegimeOperator_same
    (operator : X →+ X) (cut : ℕ) :
    twoRegimeOperator operator operator cut = fun _ => operator := by
  funext t
  simp [twoRegimeOperator]

/--
No-go: when the before/after operators are identical, every proposed change
point generates the same complete trajectory.  No estimator can recover a cut
that leaves no observational contrast in the declared state.
-/
theorem identical_regimes_make_change_point_unidentifiable
    (operator : X →+ X) (firstCut secondCut : ℕ)
    (forcing : ℕ → X) (x0 : X) :
    ∀ horizon,
      timeVaryingCoupledTrajectory
          (twoRegimeOperator operator operator firstCut) forcing x0 horizon =
        timeVaryingCoupledTrajectory
          (twoRegimeOperator operator operator secondCut) forcing x0 horizon := by
  rw [twoRegimeOperator_same, twoRegimeOperator_same]
  intro horizon
  rfl

/-- A probe exposes a regime change exactly when the two one-step actions differ. -/
def RegimeSeparatedAtProbe
    (before after : X →+ X) (probe : X) : Prop :=
  before probe ≠ after probe

/-- Positive repair: a separating probe remains separating under common forcing. -/
theorem separating_probe_detects_one_step_regime_change
    (before after : X →+ X) (probe forcing : X)
    (separated : RegimeSeparatedAtProbe before after probe) :
    before probe + forcing ≠ after probe + forcing := by
  intro equalOutputs
  apply separated
  exact add_right_cancel equalOutputs

/-- Agreement on all registered probes makes one-step regime labels observationally equal there. -/
theorem probe_agreement_blocks_registered_one_step_detection
    (probes : Set X) (before after : X →+ X)
    (agreement : CouplingProbeAgreement probes before after)
    (probe : X) (registered : probe ∈ probes) (forcing : X) :
    before probe + forcing = after probe + forcing := by
  rw [agreement probe registered]

end OCKIndividuationMSpaceComposition
