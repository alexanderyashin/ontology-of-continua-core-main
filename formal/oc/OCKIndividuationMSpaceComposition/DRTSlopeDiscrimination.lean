import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

/-!
# Finite-error discrimination of DRT scaling closures

The DRT scaling audit proves conditional cubic and quadratic laws.  This file
adds the small decision-theoretic bridge needed by the physical protocol: a
bounded slope estimate selects its nearer registered mechanism exactly when
the model separation exceeds twice the error envelope.  The midpoint result is
the sharp obstruction; no amount of rhetorical confidence can select a model
from an estimate in that overlap region.
-/

/-- A bounded slope error selects the true registered slope when the two
candidate slopes are separated by more than twice that error. -/
theorem bounded_slope_error_selects_nearer_model
    {trueSlope alternativeSlope estimate error : ℝ}
    (boundedError : |estimate - trueSlope| ≤ error)
    (separated : 2 * error < |alternativeSlope - trueSlope|) :
    |estimate - trueSlope| < |estimate - alternativeSlope| := by
  by_contra notNearer
  have alternativeLe :
      |estimate - alternativeSlope| ≤ |estimate - trueSlope| :=
    le_of_not_gt notNearer
  have triangle :
      |alternativeSlope - trueSlope| ≤
        |estimate - alternativeSlope| + |estimate - trueSlope| := by
    calc
      |alternativeSlope - trueSlope| =
          |(alternativeSlope - estimate) + (estimate - trueSlope)| := by
            congr 1 <;> ring
      _ ≤ |alternativeSlope - estimate| + |estimate - trueSlope| :=
        abs_add_le _ _
      _ = |estimate - alternativeSlope| + |estimate - trueSlope| := by
        rw [abs_sub_comm alternativeSlope estimate]
  linarith

/-- The two DRT closures have an exact slope gap of one sixth. -/
theorem drt_cubic_quadratic_slope_gap :
    |(-1 / 2 : ℝ) - (-1 / 3 : ℝ)| = 1 / 6 := by
  norm_num

/-- Consequently, an absolute slope-error envelope below one twelfth selects
the cubic closure over the quadratic closure. -/
theorem drt_error_below_one_twelfth_selects_cubic
    {estimate error : ℝ}
    (boundedError : |estimate - (-1 / 3 : ℝ)| ≤ error)
    (smallError : error < 1 / 12) :
    |estimate - (-1 / 3 : ℝ)| < |estimate - (-1 / 2 : ℝ)| := by
  apply bounded_slope_error_selects_nearer_model boundedError
  rw [drt_cubic_quadratic_slope_gap]
  linarith

/-- The same finite-error envelope symmetrically selects the quadratic closure. -/
theorem drt_error_below_one_twelfth_selects_quadratic
    {estimate error : ℝ}
    (boundedError : |estimate - (-1 / 2 : ℝ)| ≤ error)
    (smallError : error < 1 / 12) :
    |estimate - (-1 / 2 : ℝ)| < |estimate - (-1 / 3 : ℝ)| := by
  apply bounded_slope_error_selects_nearer_model boundedError
  rw [abs_sub_comm]
  rw [drt_cubic_quadratic_slope_gap]
  linarith

/-- Sharp no-go: at the midpoint of two slope values both models are equally
near.  Without a stricter error envelope there is no unique nearest-model
decision. -/
theorem midpoint_slope_is_not_a_unique_model_selection
    (cubicSlope quadraticSlope : ℝ) :
    ¬ |((cubicSlope + quadraticSlope) / 2) - cubicSlope| <
        |((cubicSlope + quadraticSlope) / 2) - quadraticSlope| := by
  have midpointEquality :
      |((cubicSlope + quadraticSlope) / 2) - cubicSlope| =
        |((cubicSlope + quadraticSlope) / 2) - quadraticSlope| := by
    rw [show (cubicSlope + quadraticSlope) / 2 - cubicSlope =
        (quadraticSlope - cubicSlope) / 2 by ring]
    rw [show (cubicSlope + quadraticSlope) / 2 - quadraticSlope =
        -((quadraticSlope - cubicSlope) / 2) by ring]
    exact (abs_neg _).symm
  rw [midpointEquality]
  exact lt_irrefl _

end OCKIndividuationMSpaceComposition
