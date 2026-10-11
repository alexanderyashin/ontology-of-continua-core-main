import OCKIndividuationMSpaceComposition.ResidualAlignmentContextAdmission

namespace OCKIndividuationMSpaceComposition

/-!
# Support-conditioned correction transport

The baseline continuation forecast is the current state.  A learned path or
context model contributes a correction.  This module states the exact boundary
between a correction that transports through a change in regime mixture and
one that was admitted only by an aggregate calibration accident.

The algebra is standard squared-loss and robust-decision theory (`REUSE`).  The
OC contribution is the adapter: contexts are explicit strata, continuation is
the safe zero-correction action, and unsupported context transport is forbidden
unless a separate invariance contract supplies the missing premise (`ADAPT`).
-/

/-- Squared-risk improvement of a correction in one context stratum. -/
def StratumCorrectionGain
    (alignment energy weight : ℝ) : ℝ :=
  2 * weight * alignment - weight ^ 2 * energy

/-- Gain after the target population mixes the declared context strata. -/
def MixtureCorrectionGain {Context : Type*} [Fintype Context]
    (mass alignment energy : Context → ℝ) (weight : ℝ) : ℝ :=
  ∑ context, mass context *
    StratumCorrectionGain (alignment context) (energy context) weight

/-- Exact local admission condition implies nonnegative gain in that stratum. -/
theorem stratumCorrectionGain_nonnegative
    (alignment energy weight : ℝ)
    (weightNonnegative : 0 ≤ weight)
    (localAdmission : weight * energy ≤ 2 * alignment) :
    0 ≤ StratumCorrectionGain alignment energy weight := by
  unfold StratumCorrectionGain
  nlinarith [mul_nonneg weightNonnegative
    (sub_nonneg.mpr localAdmission)]

/-- Positive transport theorem: if the correction passes the exact admission
condition separately in every target stratum, it cannot become harmful under
any nonnegative change of regime mixture. -/
theorem perStratumAdmission_transports_to_every_mixture
    {Context : Type*} [Fintype Context]
    (mass alignment energy : Context → ℝ) (weight : ℝ)
    (massNonnegative : ∀ context, 0 ≤ mass context)
    (weightNonnegative : 0 ≤ weight)
    (perStratumAdmission : ∀ context,
      weight * energy context ≤ 2 * alignment context) :
    0 ≤ MixtureCorrectionGain mass alignment energy weight := by
  unfold MixtureCorrectionGain
  exact Finset.sum_nonneg fun context _ =>
    mul_nonneg (massNonnegative context)
      (stratumCorrectionGain_nonnegative
        (alignment context) (energy context) weight weightNonnegative
        (perStratumAdmission context))

/-- A target population concentrated in one stratum exposes exactly that
stratum's correction gain. -/
theorem concentratedMixtureGain
    {Context : Type*} [Fintype Context] [DecidableEq Context]
    (selected : Context) (alignment energy : Context → ℝ) (weight : ℝ) :
    MixtureCorrectionGain
        (fun context => if context = selected then 1 else 0)
        alignment energy weight =
      StratumCorrectionGain (alignment selected) (energy selected) weight := by
  simp [MixtureCorrectionGain]

/-- No-go theorem: one harmful stratum is enough to defeat a uniform transport
claim, because an admissible target mixture may concentrate on that stratum. -/
theorem harmfulStratum_refutes_uniform_mixture_transport
    {Context : Type*} [Fintype Context] [DecidableEq Context]
    (selected : Context) (alignment energy : Context → ℝ) (weight : ℝ)
    (harmful : StratumCorrectionGain
      (alignment selected) (energy selected) weight < 0) :
    ∃ mass : Context → ℝ,
      (∀ context, 0 ≤ mass context) ∧
      (∑ context, mass context) = 1 ∧
      MixtureCorrectionGain mass alignment energy weight < 0 := by
  refine ⟨fun context => if context = selected then 1 else 0, ?_, ?_, ?_⟩
  · intro context
    by_cases contextEq : context = selected <;> simp [contextEq]
  · simp
  · simpa [concentratedMixtureGain] using harmful

/-- The zero mechanism is an observationally compatible completion of every
finite support. -/
def ZeroContextMechanism {Context : Type*} : Context → ℝ := fun _ => 0

/-- A second completion agrees with zero away from one unsupported context. -/
def UnsupportedSpikeMechanism {Context : Type*} [DecidableEq Context]
    (target : Context) : Context → ℝ :=
  fun context => if context = target then 1 else 0

/-- Observations outside the target cannot distinguish the zero and spike
mechanisms. -/
theorem zeroAndSpike_agree_on_observed_support
    {Context : Type*} [DecidableEq Context]
    (observed : Finset Context) (target : Context)
    (unsupported : target ∉ observed) :
    ∀ context ∈ observed,
      ZeroContextMechanism context = UnsupportedSpikeMechanism target context := by
  intro context contextObserved
  have contextNe : context ≠ target := by
    intro contextEq
    apply unsupported
    simpa [contextEq] using contextObserved
  simp [ZeroContextMechanism, UnsupportedSpikeMechanism, contextNe]

/-- The same two mechanisms disagree at the unsupported target context. -/
theorem zeroAndSpike_disagree_at_unsupported_target
    {Context : Type*} [DecidableEq Context] (target : Context) :
    ZeroContextMechanism target ≠ UnsupportedSpikeMechanism target target := by
  simp [ZeroContextMechanism, UnsupportedSpikeMechanism]

/-- Identification no-go: if the target context is outside observed support,
two mechanisms fit every observed context exactly and predict different target
corrections. -/
theorem unsupportedContext_correction_not_identified
    {Context : Type*} [DecidableEq Context]
    (observed : Finset Context) (target : Context)
    (unsupported : target ∉ observed) :
    ∃ first second : Context → ℝ,
      (∀ context ∈ observed, first context = second context) ∧
      first target ≠ second target := by
  exact ⟨ZeroContextMechanism, UnsupportedSpikeMechanism target,
    zeroAndSpike_agree_on_observed_support observed target unsupported,
    zeroAndSpike_disagree_at_unsupported_target target⟩

/-- Squared loss after applying a scalar correction to an unknown increment. -/
def ScalarCorrectionLoss (increment correction : ℝ) : ℝ :=
  (increment - correction) ^ 2

/-- Worst loss over the two endpoints of a symmetric uncertainty interval. -/
def SymmetricEndpointWorstLoss (radius correction : ℝ) : ℝ :=
  max (ScalarCorrectionLoss radius correction)
    (ScalarCorrectionLoss (-radius) correction)

/-- Positive robust theorem: zero correction has worst endpoint loss exactly
equal to the squared uncertainty radius. -/
theorem zeroCorrection_exact_worst_loss (radius : ℝ) :
    SymmetricEndpointWorstLoss radius 0 = radius ^ 2 := by
  simp [SymmetricEndpointWorstLoss, ScalarCorrectionLoss]

/-- Minimax theorem: without directional information about an increment in a
symmetric uncertainty set, no correction improves on continuation. -/
theorem zeroCorrection_minimax
    (radius correction : ℝ) (radiusNonnegative : 0 ≤ radius) :
    radius ^ 2 ≤ SymmetricEndpointWorstLoss radius correction := by
  by_cases correctionNonnegative : 0 ≤ correction
  · have endpointBound :
        radius ^ 2 ≤ ScalarCorrectionLoss (-radius) correction := by
      unfold ScalarCorrectionLoss
      nlinarith [mul_nonneg radiusNonnegative correctionNonnegative]
    exact endpointBound.trans (le_max_right _ _)
  · have correctionNonpositive : correction ≤ 0 := le_of_not_ge correctionNonnegative
    have endpointBound :
        radius ^ 2 ≤ ScalarCorrectionLoss radius correction := by
      unfold ScalarCorrectionLoss
      nlinarith [mul_nonpos_of_nonneg_of_nonpos radiusNonnegative correctionNonpositive]
    exact endpointBound.trans (le_max_left _ _)

/-- Strict minimax boundary: with positive uncertainty radius, every nonzero
unsupported correction is strictly worse in at least one compatible world. -/
theorem nonzeroUnsupportedCorrection_strictly_worse
    (radius correction : ℝ) (radiusPositive : 0 < radius)
    (correctionNonzero : correction ≠ 0) :
    radius ^ 2 < SymmetricEndpointWorstLoss radius correction := by
  rcases lt_or_gt_of_ne correctionNonzero with correctionNegative | correctionPositive
  · have endpointStrict :
        radius ^ 2 < ScalarCorrectionLoss radius correction := by
      unfold ScalarCorrectionLoss
      nlinarith [mul_neg_of_pos_of_neg radiusPositive correctionNegative]
    exact endpointStrict.trans_le (le_max_left _ _)
  · have endpointStrict :
        radius ^ 2 < ScalarCorrectionLoss (-radius) correction := by
      unfold ScalarCorrectionLoss
      nlinarith [mul_pos radiusPositive correctionPositive]
    exact endpointStrict.trans_le (le_max_right _ _)

end OCKIndividuationMSpaceComposition
