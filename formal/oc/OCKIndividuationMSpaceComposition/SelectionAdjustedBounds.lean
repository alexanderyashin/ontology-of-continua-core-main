import OCKIndividuationMSpaceComposition.InterventionalContrastIdentification

namespace OCKIndividuationMSpaceComposition

/-!
# Selection-adjusted identified-set bounds

This module is deliberately narrower than a causal-identification theorem.  It
formalises the exact finite-population fallback when an observed outcome is a
selected mixture and the selection rate is known but the unobserved component
is only bounded in `[0,1]`.  The bounds are sound and sharp; the zero-rate
lemma records the corresponding no-go for point identification.
-/

def populationMean (π μs μu : ℝ) : ℝ :=
  π * μs + (1 - π) * μu

def observedSelectedContribution (π μs : ℝ) : ℝ :=
  π * μs

theorem selection_mean_interval_sound
    {π μs μu : ℝ}
    (hπ0 : 0 ≤ π) (hπ1 : π ≤ 1)
    (hμs0 : 0 ≤ μs) (hμs1 : μs ≤ 1)
    (hμu0 : 0 ≤ μu) (hμu1 : μu ≤ 1) :
    π * μs ≤ populationMean π μs μu ∧
      populationMean π μs μu ≤ π * μs + (1 - π) := by
  have hweight0 : 0 ≤ 1 - π := by linarith
  have hterm0 : 0 ≤ (1 - π) * μu := mul_nonneg hweight0 hμu0
  have hterm1 : (1 - π) * μu ≤ (1 - π) := by
    simpa using (mul_le_mul_of_nonneg_left hμu1 hweight0)
  dsimp [populationMean]
  constructor <;> linarith

theorem selection_interval_lower_sharp
    {π μs : ℝ} :
    populationMean π μs 0 = π * μs := by
  simp [populationMean]

theorem selection_interval_upper_sharp
    {π μs : ℝ} :
    populationMean π μs 1 = π * μs + (1 - π) := by
  dsimp [populationMean]
  ring

def contrastLower (πa μa πb μb : ℝ) : ℝ :=
  πa * μa - (πb * μb + (1 - πb))

def contrastUpper (πa μa πb μb : ℝ) : ℝ :=
  (πa * μa + (1 - πa)) - πb * μb

theorem selection_contrast_interval_sound
    {πa μa μua πb μb μub : ℝ}
    (hπa0 : 0 ≤ πa) (hπa1 : πa ≤ 1)
    (hμa0 : 0 ≤ μa) (hμa1 : μa ≤ 1)
    (hμua0 : 0 ≤ μua) (hμua1 : μua ≤ 1)
    (hπb0 : 0 ≤ πb) (hπb1 : πb ≤ 1)
    (hμb0 : 0 ≤ μb) (hμb1 : μb ≤ 1)
    (hμub0 : 0 ≤ μub) (hμub1 : μub ≤ 1) :
    contrastLower πa μa πb μb ≤
        populationMean πa μa μua - populationMean πb μb μub ∧
      populationMean πa μa μua - populationMean πb μb μub ≤
        contrastUpper πa μa πb μb := by
  rcases selection_mean_interval_sound hπa0 hπa1 hμa0 hμa1 hμua0 hμua1 with
    ⟨haLower, haUpper⟩
  rcases selection_mean_interval_sound hπb0 hπb1 hμb0 hμb1 hμub0 hμub1 with
    ⟨hbLower, hbUpper⟩
  dsimp [contrastLower, contrastUpper]
  constructor <;> linarith

theorem zero_selection_rate_observation_independent
    {μs μu₁ μu₂ : ℝ}
    (hlatent : μu₁ < μu₂) :
    observedSelectedContribution 0 μs = observedSelectedContribution 0 μs ∧
      populationMean 0 μs μu₁ ≠ populationMean 0 μs μu₂ := by
  constructor
  · rfl
  · simp [populationMean]
    linarith

theorem selection_rate_transport_no_go_at_zero_selected_mean
    {π₁ π₂ : ℝ}
    (hπ : π₁ ≠ π₂) :
    populationMean π₁ 0 1 ≠ populationMean π₂ 0 1 := by
  intro h
  dsimp [populationMean] at h
  apply hπ
  linarith

theorem selection_mean_interval_rate_uncertainty_sound
    {πL πU π μs μu : ℝ}
    (hπL0 : 0 ≤ πL) (hπL1 : πL ≤ 1)
    (hπU0 : 0 ≤ πU) (hπU1 : πU ≤ 1)
    (hπLleU : πL ≤ πU)
    (hπgeL : πL ≤ π) (hπleU : π ≤ πU)
    (hμs0 : 0 ≤ μs) (hμs1 : μs ≤ 1)
    (hμu0 : 0 ≤ μu) (hμu1 : μu ≤ 1) :
    πL * μs ≤ populationMean π μs μu ∧
      populationMean π μs μu ≤ πL * μs + (1 - πL) := by
  have hweight0 : 0 ≤ 1 - π := by linarith
  have hterm0 : 0 ≤ (1 - π) * μu := mul_nonneg hweight0 hμu0
  have hterm1 : (1 - π) * μu ≤ (1 - π) := by
    simpa using (mul_le_mul_of_nonneg_left hμu1 hweight0)
  have hlower : πL * μs ≤ π * μs :=
    mul_le_mul_of_nonneg_right hπgeL hμs0
  have hfactor0 : 0 ≤ 1 - μs := by linarith
  have hprod : πL * (1 - μs) ≤ π * (1 - μs) :=
    mul_le_mul_of_nonneg_right hπgeL hfactor0
  have hupperBase : π * μs + (1 - π) ≤ πL * μs + (1 - πL) := by
    calc
      π * μs + (1 - π) = 1 - π * (1 - μs) := by ring
      _ ≤ 1 - πL * (1 - μs) := by linarith
      _ = πL * μs + (1 - πL) := by ring
  dsimp [populationMean]
  constructor
  · linarith
  · linarith

end OCKIndividuationMSpaceComposition
