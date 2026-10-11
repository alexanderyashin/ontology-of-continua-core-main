import Mathlib.Analysis.SpecialFunctions.Log.Basic

/-!
OC Core 1.4 minimal obligation spine: analytic Q073/Q012 logarithmic-diffusion
obstructions.

This file proves only real-analysis implications.  It does not prove a weak
central-limit theorem, a moment asymptotic, or any other statement about a
particular Lorentz gas.

The release-authorized interface is the eventual positive logarithmic lower
bound below.  It is strictly weaker than an eventual equality and is sufficient
to rule out a finite ordinary diffusion coefficient.

The exact `D0 * log (t / t0)` definitions and lemmas are retained only as
conditional analytic utilities for symbolic examples.  They are not a
source theorem and must not authorize scientific closure.
-/

namespace OCMinimalObligationSpine

open Filter

noncomputable def q073_q012_logarithmic_diffusion_coefficient
    (D0 t0 t : ℝ) : ℝ :=
  D0 * Real.log (t / t0)

theorem q073_q012_logarithmic_diffusion_diverges_atTop
    {D0 t0 : ℝ}
    (hD0 : 0 < D0)
    (ht0 : 0 < t0) :
    Tendsto
      (q073_q012_logarithmic_diffusion_coefficient D0 t0)
      atTop
      atTop := by
  have hRatio :
      Tendsto (fun t : ℝ => t / t0) atTop atTop :=
    Tendsto.atTop_div_const ht0 tendsto_id
  have hLog :
      Tendsto (fun t : ℝ => Real.log (t / t0)) atTop atTop :=
    Real.tendsto_log_atTop.comp hRatio
  exact Tendsto.const_mul_atTop hD0 hLog

theorem q073_q012_logarithmic_diffusion_incompatible_with_finite_limit
    {D0 t0 : ℝ}
    (hD0 : 0 < D0)
    (ht0 : 0 < t0)
    (finiteCoefficient : ℝ) :
    ¬ Tendsto
      (q073_q012_logarithmic_diffusion_coefficient D0 t0)
      atTop
      (nhds finiteCoefficient) := by
  exact not_tendsto_nhds_of_tendsto_atTop
    (q073_q012_logarithmic_diffusion_diverges_atTop hD0 ht0)
    finiteCoefficient

theorem q073_q012_logarithmic_diffusion_has_no_finite_ordinary_coefficient
    {D0 t0 : ℝ}
    (hD0 : 0 < D0)
    (ht0 : 0 < t0) :
    ¬ ∃ finiteCoefficient : ℝ,
      Tendsto
        (q073_q012_logarithmic_diffusion_coefficient D0 t0)
        atTop
        (nhds finiteCoefficient) := by
  rintro ⟨finiteCoefficient, hFinite⟩
  exact
    (q073_q012_logarithmic_diffusion_incompatible_with_finite_limit
      hD0 ht0 finiteCoefficient) hFinite

theorem q073_q012_eventually_logarithmic_diffusion_diverges_atTop
    {effectiveCoefficient : ℝ → ℝ}
    {D0 t0 : ℝ}
    (hD0 : 0 < D0)
    (ht0 : 0 < t0)
    (hRegime :
      effectiveCoefficient =ᶠ[atTop]
        q073_q012_logarithmic_diffusion_coefficient D0 t0) :
    Tendsto effectiveCoefficient atTop atTop := by
  exact
    (q073_q012_logarithmic_diffusion_diverges_atTop hD0 ht0).congr'
      hRegime.symm

theorem
    q073_q012_eventually_logarithmic_diffusion_has_no_finite_ordinary_coefficient
    {effectiveCoefficient : ℝ → ℝ}
    {D0 t0 : ℝ}
    (hD0 : 0 < D0)
    (ht0 : 0 < t0)
    (hRegime :
      effectiveCoefficient =ᶠ[atTop]
        q073_q012_logarithmic_diffusion_coefficient D0 t0) :
    ¬ ∃ finiteCoefficient : ℝ,
      Tendsto effectiveCoefficient atTop (nhds finiteCoefficient) := by
  rintro ⟨finiteCoefficient, hFinite⟩
  exact
    (not_tendsto_nhds_of_tendsto_atTop
      (q073_q012_eventually_logarithmic_diffusion_diverges_atTop
        hD0 ht0 hRegime)
      finiteCoefficient) hFinite

/-!
The honest C4 analytic bridge.  Positive time is recorded in the eventual
premise because the physical observable is only interpreted for `t > 0`.
The `atTop` filter makes the claim asymptotic; no finite-time equality is
assumed.
-/

theorem q073_q012_eventual_positive_log_lower_bound_diverges_atTop
    {effectiveCoefficient : ℝ → ℝ}
    {c : ℝ}
    (hc : 0 < c)
    (hLowerBound :
      ∀ᶠ t : ℝ in atTop,
        0 < t ∧ c * Real.log t ≤ effectiveCoefficient t) :
    Tendsto effectiveCoefficient atTop atTop := by
  have hLog :
      Tendsto (fun t : ℝ => Real.log t) atTop atTop :=
    Real.tendsto_log_atTop
  have hScaled :
      Tendsto (fun t : ℝ => c * Real.log t) atTop atTop :=
    Tendsto.const_mul_atTop hc hLog
  refine Filter.tendsto_atTop.2 ?_
  intro lowerTarget
  filter_upwards
    [Filter.tendsto_atTop.1 hScaled lowerTarget, hLowerBound]
    with t hScaledLower hPhysicalLower
  exact hScaledLower.trans hPhysicalLower.2

theorem
    q073_q012_eventual_positive_log_lower_bound_incompatible_with_finite_limit
    {effectiveCoefficient : ℝ → ℝ}
    {c : ℝ}
    (hc : 0 < c)
    (hLowerBound :
      ∀ᶠ t : ℝ in atTop,
        0 < t ∧ c * Real.log t ≤ effectiveCoefficient t)
    (finiteCoefficient : ℝ) :
    ¬ Tendsto effectiveCoefficient atTop (nhds finiteCoefficient) := by
  exact not_tendsto_nhds_of_tendsto_atTop
    (q073_q012_eventual_positive_log_lower_bound_diverges_atTop
      hc hLowerBound)
    finiteCoefficient

theorem
    q073_q012_eventual_positive_log_lower_bound_has_no_finite_ordinary_coefficient
    {effectiveCoefficient : ℝ → ℝ}
    {c : ℝ}
    (hc : 0 < c)
    (hLowerBound :
      ∀ᶠ t : ℝ in atTop,
        0 < t ∧ c * Real.log t ≤ effectiveCoefficient t) :
    ¬ ∃ finiteCoefficient : ℝ,
      Tendsto effectiveCoefficient atTop (nhds finiteCoefficient) := by
  rintro ⟨finiteCoefficient, hFinite⟩
  exact
    (q073_q012_eventual_positive_log_lower_bound_incompatible_with_finite_limit
      hc hLowerBound finiteCoefficient) hFinite

end OCMinimalObligationSpine
