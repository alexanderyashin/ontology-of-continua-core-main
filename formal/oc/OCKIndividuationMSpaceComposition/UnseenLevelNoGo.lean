import OCKIndividuationMSpaceComposition.SelectionAdjustedBounds

namespace OCKIndividuationMSpaceComposition

/-!
# Unseen-level no-go for a categorical adapter

If a new coordinate level has no lookup entry, a default prediction d in [0,1]
cannot have a uniform absolute-error guarantee below 1/2 when the outcome is
only known to lie in [0,1].  The lower bound is sharp at d = 1/2.
-/

theorem unseenLevel_minimax_half_bound
    {d : ℝ} (hd0 : 0 ≤ d) (hd1 : d ≤ 1) :
    (1 / 2 : ℝ) ≤ max |d - 0| |d - 1| := by
  by_cases hhalf : d ≤ (1 / 2 : ℝ)
  · have hupper : (1 / 2 : ℝ) ≤ 1 - d := by linarith
    calc
      (1 / 2 : ℝ) ≤ 1 - d := hupper
      _ = |d - 1| := by
        rw [abs_of_nonpos (by linarith : d - 1 ≤ 0)]
        linarith
      _ ≤ max |d - 0| |d - 1| := le_max_right _ _
  · have hlower : (1 / 2 : ℝ) ≤ d := by linarith
    calc
      (1 / 2 : ℝ) ≤ d := hlower
      _ = |d - 0| := by
        rw [abs_of_nonneg (by linarith : 0 ≤ d - 0)]
        linarith
      _ ≤ max |d - 0| |d - 1| := le_max_left _ _

theorem unseenLevel_no_uniform_error_lt_half
    {d ε : ℝ} (hd0 : 0 ≤ d) (hd1 : d ≤ 1) (hε : ε < (1 / 2 : ℝ)) :
    ¬ (∀ y : ℝ, 0 ≤ y → y ≤ 1 → |d - y| ≤ ε) := by
  intro hbound
  have hzero : |d - 0| ≤ ε := hbound 0 (by norm_num) (by norm_num)
  have hone : |d - 1| ≤ ε := hbound 1 (by norm_num) (by norm_num)
  have hzero' : d ≤ ε := by
    rw [abs_of_nonneg (by linarith : 0 ≤ d - 0)] at hzero
    linarith
  have hone' : 1 - d ≤ ε := by
    rw [abs_of_nonpos (by linarith : d - 1 ≤ 0)] at hone
    linarith
  linarith

theorem unseenLevel_minimax_half_sharp :
    max |(1 / 2 : ℝ) - 0| |(1 / 2 : ℝ) - 1| = (1 / 2 : ℝ) := by
  norm_num [abs_of_nonneg, abs_of_nonpos]

end OCKIndividuationMSpaceComposition
