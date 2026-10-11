import OCKIndividuationMSpaceComposition.UnseenLevelNoGo

namespace OCKIndividuationMSpaceComposition

/-!
# Explicit affine numeric adapter

The affine adapter is a contract, not a free extrapolation rule.  The theorems
below prove exactness at the calibration points and uniqueness among affine
functions; empirical validation must still establish whether the contract is
appropriate for a domain/outcome branch.
-/

noncomputable def affinePredict (a b x : ℝ) : ℝ := a + b * x

noncomputable def affineThrough (x₀ y₀ x₁ y₁ x : ℝ) : ℝ :=
  y₀ + (y₁ - y₀) / (x₁ - x₀) * (x - x₀)

theorem affineThrough_left
    {x₀ y₀ x₁ y₁ : ℝ} (hneq : x₁ ≠ x₀) :
    affineThrough x₀ y₀ x₁ y₁ x₀ = y₀ := by
  dsimp [affineThrough]
  ring

theorem affineThrough_right
    {x₀ y₀ x₁ y₁ : ℝ} (hneq : x₁ ≠ x₀) :
    affineThrough x₀ y₀ x₁ y₁ x₁ = y₁ := by
  have hden : x₁ - x₀ ≠ 0 := sub_ne_zero.mpr hneq
  dsimp [affineThrough]
  field_simp [hden]
  ring

theorem affineThrough_unique
    {x₀ y₀ x₁ y₁ a b : ℝ} (hneq : x₁ ≠ x₀)
    (h₀ : affinePredict a b x₀ = y₀)
    (h₁ : affinePredict a b x₁ = y₁) :
    ∀ x, affinePredict a b x = affineThrough x₀ y₀ x₁ y₁ x := by
  intro x
  have hden : x₁ - x₀ ≠ 0 := sub_ne_zero.mpr hneq
  have hrel : b * (x₁ - x₀) = y₁ - y₀ := by
    dsimp [affinePredict] at h₀ h₁
    linarith
  dsimp [affinePredict] at h₀ h₁
  have hb : b = (y₁ - y₀) / (x₁ - x₀) := by
    apply (eq_div_iff hden).2
    exact hrel
  have ha : a = y₀ - b * x₀ := by
    linarith [h₀]
  rw [ha, hb]
  dsimp [affinePredict, affineThrough]
  field_simp [hden]
  ring

theorem affine_contract_error_bound
    {a b x y ε : ℝ}
    (hcontract : |y - affinePredict a b x| ≤ ε) :
    |affinePredict a b x - y| ≤ ε := by
  simpa [abs_sub_comm] using hcontract

end OCKIndividuationMSpaceComposition
