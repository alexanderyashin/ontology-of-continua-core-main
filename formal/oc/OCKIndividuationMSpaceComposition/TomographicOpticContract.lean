import OCKIndividuationMSpaceComposition.TomographicTaskReconstruction
import OCKIndividuationMSpaceComposition.TomographicResolutionMargin
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

universe uWorld uView uParameter

/-!
# Typed optic contract for task-relative focusing

The contract keeps four quantities separate: a focus score, a declared
resolution margin, a calibration budget and a distortion budget.  The score
has no physical interpretation by itself.  Task focus adequacy is a stronger,
source-supplied separation certificate that charges both error budgets before
claiming that a task is identifiable.
-/

section OpticContract

variable {World : Type uWorld} {View : Type uView} {Parameter : Type uParameter}

/-- Minimal typed optic metadata and observation family. -/
structure TomographicOpticContract where
  observe : Parameter → View → World → ℝ
  focusMeasure : Parameter → ℝ
  resolution : Parameter → ℝ
  calibration : Parameter → ℝ
  distortion : Parameter → ℝ
  resolution_nonnegative : ∀ parameter, 0 ≤ resolution parameter
  calibration_nonnegative : ∀ parameter, 0 ≤ calibration parameter
  distortion_nonnegative : ∀ parameter, 0 ≤ distortion parameter

/-- The full view-indexed observation at one optic setting. -/
def tomographicOpticObservation
    (optic : TomographicOpticContract (World := World) (View := View)
      (Parameter := Parameter)) (parameter : Parameter) (world : World) :
    View → ℝ :=
  fun view => optic.observe parameter view world

/-- Resolution left after paying the declared calibration and distortion
budgets.  Positivity is a contract, not an inferred property of a score. -/
def tomographicEffectiveResolution
    (optic : TomographicOpticContract (World := World) (View := View)
      (Parameter := Parameter)) (parameter : Parameter) : ℝ :=
  optic.resolution parameter -
    2 * (optic.calibration parameter + optic.distortion parameter)

/-- Task-relative focus adequacy: the setting has positive usable resolution
and every pair with different task answers is separated by a registered view
after the complete calibration/distortion budget is charged. -/
def TomographicFocusAdequacy
    (optic : TomographicOpticContract (World := World) (View := View)
      (Parameter := Parameter)) (parameter : Parameter)
    (target : World → ℝ) : Prop :=
  2 * (optic.calibration parameter + optic.distortion parameter) <
      optic.resolution parameter ∧
    ∀ left right, target left ≠ target right →
      ∃ view,
        2 * (optic.calibration parameter + optic.distortion parameter) <
            |optic.observe parameter view left -
              optic.observe parameter view right|

theorem tomographicFocusAdequacy_implies_positive_effectiveResolution
    (optic : TomographicOpticContract (World := World) (View := View)
      (Parameter := Parameter)) (parameter : Parameter)
    (target : World → ℝ)
    (adequate : TomographicFocusAdequacy optic parameter target) :
    0 < tomographicEffectiveResolution optic parameter := by
  unfold tomographicEffectiveResolution
  exact sub_pos.mpr adequate.1

/-- A non-positive usable resolution is a hard impossibility boundary for
    task-relative focus.  The observer must repair calibration/distortion or
    acquire a better optic; it may not promote the setting by score alone. -/
theorem tomographicFocusAdequacy_impossible_of_nonpositive_effectiveResolution
    (optic : TomographicOpticContract (World := World) (View := View)
      (Parameter := Parameter)) (parameter : Parameter)
    (target : World → ℝ)
    (nonpositive : tomographicEffectiveResolution optic parameter ≤ 0) :
    ¬ TomographicFocusAdequacy optic parameter target := by
  intro adequate
  exact (not_lt_of_ge nonpositive)
    (tomographicFocusAdequacy_implies_positive_effectiveResolution
      optic parameter target adequate)

/-- A task-disagreeing pair that no registered view separates beyond the full
    calibration/distortion budget makes focus unattainable at this setting.
    This is a witness-level insufficiency result, not a claim that every
    failed focus attempt has found the globally worst pair. -/
theorem tomographicFocusAdequacy_impossible_of_unseparated_pair
    (optic : TomographicOpticContract (World := World) (View := View)
      (Parameter := Parameter)) (parameter : Parameter)
    (target : World → ℝ) (left right : World)
    (task_different : target left ≠ target right)
    (unseparated : ∀ view,
      |optic.observe parameter view left -
        optic.observe parameter view right| ≤
        2 * (optic.calibration parameter + optic.distortion parameter)) :
    ¬ TomographicFocusAdequacy optic parameter target := by
  intro adequate
  obtain ⟨view, separated⟩ := adequate.2 left right task_different
  exact (not_lt_of_ge (unseparated view)) separated

theorem tomographicFocusAdequacy_implies_taskIdentifiable
    (optic : TomographicOpticContract (World := World) (View := View)
      (Parameter := Parameter)) (parameter : Parameter)
    (target : World → ℝ)
    (adequate : TomographicFocusAdequacy optic parameter target) :
    TomographicTaskIdentifiable
      (fun view => optic.observe parameter view) target := by
  intro left right same
  by_contra different
  obtain ⟨view, separation⟩ := adequate.2 left right different
  have zero :
      |optic.observe parameter view left -
        optic.observe parameter view right| = 0 := by
    have pointwise : optic.observe parameter view left =
        optic.observe parameter view right := by
      simpa [MultiTaskSignature] using congrFun same view
    rw [pointwise]
    simp
  have nonnegative_budget :
      0 ≤ 2 * (optic.calibration parameter + optic.distortion parameter) := by
    nlinarith [optic.calibration_nonnegative parameter,
      optic.distortion_nonnegative parameter]
  have impossible :
      2 * (optic.calibration parameter + optic.distortion parameter) < 0 := by
    simpa [zero] using separation
  exact (not_lt_of_ge nonnegative_budget impossible).elim

theorem tomographicFocusAdequacy_implies_noisy_taskIdentifiable
    (optic : TomographicOpticContract (World := World) (View := View)
      (Parameter := Parameter)) (parameter : Parameter)
    (target : World → ℝ) (noise : View → World → ℝ)
    (adequate : TomographicFocusAdequacy optic parameter target)
    (noise_bound : ∀ view world,
      |noise view world| ≤
        optic.calibration parameter + optic.distortion parameter) :
    TomographicTaskIdentifiable
      (fun view world => optic.observe parameter view world + noise view world)
      target := by
  intro left right same
  by_contra different
  obtain ⟨view, separation⟩ := adequate.2 left right different
  have nonnegative_budget :
      0 ≤ 2 * (optic.calibration parameter + optic.distortion parameter) := by
    nlinarith [optic.calibration_nonnegative parameter,
      optic.distortion_nonnegative parameter]
  have margin_positive :
      0 < |optic.observe parameter view left -
        optic.observe parameter view right| := by
    linarith
  let certificate : TomographicPairResolutionCertificate
      (fun selected world => optic.observe parameter selected world) left right :=
    { view := view
      margin := |optic.observe parameter view left -
        optic.observe parameter view right|
      margin_positive := margin_positive
      lower_bound := le_rfl }
  have budget : |noise certificate.view left| + |noise certificate.view right| <
      certificate.margin := by
    dsimp [certificate]
    have left_bound := noise_bound view left
    have right_bound := noise_bound view right
    linarith
  have unequal := tomographicPairResolutionCertificate_robust_to_bounded_error
    (fun selected world => optic.observe parameter selected world) left right
    certificate (noise certificate.view left) (noise certificate.view right)
    budget
  exact unequal (congrFun same certificate.view)

theorem tomographicFocusAdequacy_implies_observation_task_boundary
    (optic : TomographicOpticContract (World := World) (View := View)
      (Parameter := Parameter)) (parameter : Parameter)
    (target : World → ℝ)
    (adequate : TomographicFocusAdequacy optic parameter target) :
    ∀ left right,
      tomographicOpticObservation optic parameter left =
        tomographicOpticObservation optic parameter right →
      target left = target right := by
  intro left right same
  exact tomographicFocusAdequacy_implies_taskIdentifiable
    optic parameter target adequate left right (by
      simpa [tomographicOpticObservation] using same)

end OpticContract

end OCKIndividuationMSpaceComposition
