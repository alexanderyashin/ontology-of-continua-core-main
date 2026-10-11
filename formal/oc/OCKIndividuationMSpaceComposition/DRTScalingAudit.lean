import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

/-!
Exact separation of two models that had previously been conflated:

* the published time-distinguishability preprint closes the acquisition window
  with the resolution being tested and therefore has a cubic flux-time law;
* the current DRT appendix minimizes a different localization-variance
  objective and therefore has a quadratic stationary balance.

The theorems below concern exact algebraic consequences of the displayed
models.  They do not assert that either observation model is empirically true.
-/

/--
The temporal-variance expression in the published photon-limited model after
identifying the acquisition window with the resolution being tested.
-/
def publishedTemporalVariance
    (kappa width4 D Phi resolution : ℚ) : ℚ :=
  kappa * width4 / (4 * D^2 * Phi * resolution)

/--
The published self-consistency condition forces a cubic balance.  This is the
positive algebraic origin of the `Phi^(-1/3)` law.
-/
theorem published_self_consistency_implies_cubic_balance
    {kappa width4 D Phi resolution : ℚ}
    (denominatorNonzero : 4 * D^2 * Phi * resolution ≠ 0)
    (selfConsistent :
      resolution^2 =
        publishedTemporalVariance kappa width4 D Phi resolution) :
    4 * D^2 * Phi * resolution^3 = kappa * width4 := by
  have multiplied :
      resolution^2 * (4 * D^2 * Phi * resolution) = kappa * width4 :=
    (eq_div_iff denominatorNonzero).mp (by
      simpa [publishedTemporalVariance] using selfConsistent)
  calc
    4 * D^2 * Phi * resolution^3 =
        resolution^2 * (4 * D^2 * Phi * resolution) := by ring
    _ = kappa * width4 := multiplied

/--
When the acquisition duration is an independently fixed parameter, the same
variance law yields a square-resolution balance.  A cubic law requires the
additional closure `acquisition = resolution`; it is not a consequence of
Poisson statistics alone.
-/
theorem independent_exposure_implies_square_resolution_balance
    {kappa width4 D Phi acquisition resolution : ℚ}
    (denominatorNonzero : 4 * D^2 * Phi * acquisition ≠ 0)
    (selfConsistent :
      resolution^2 =
        kappa * width4 / (4 * D^2 * Phi * acquisition)) :
    4 * D^2 * Phi * acquisition * resolution^2 = kappa * width4 := by
  have multiplied :
      resolution^2 * (4 * D^2 * Phi * acquisition) = kappa * width4 :=
    (eq_div_iff denominatorNonzero).mp selfConsistent
  calc
    4 * D^2 * Phi * acquisition * resolution^2 =
        resolution^2 * (4 * D^2 * Phi * acquisition) := by ring
    _ = kappa * width4 := multiplied

/-- Fixed physical and statistical parameters preserve `Phi * resolution^3`. -/
theorem published_cubic_flux_time_invariant
    {kappa width4 D Phi₁ Phi₂ resolution₁ resolution₂ : ℚ}
    (nonzeroD : D ≠ 0)
    (balance₁ :
      4 * D^2 * Phi₁ * resolution₁^3 = kappa * width4)
    (balance₂ :
      4 * D^2 * Phi₂ * resolution₂^3 = kappa * width4) :
    Phi₁ * resolution₁^3 = Phi₂ * resolution₂^3 := by
  have h :
      4 * D^2 * (Phi₁ * resolution₁^3) =
        4 * D^2 * (Phi₂ * resolution₂^3) := by
    calc
      4 * D^2 * (Phi₁ * resolution₁^3) = kappa * width4 := by
        simpa [mul_assoc] using balance₁
      _ = 4 * D^2 * (Phi₂ * resolution₂^3) := by
        simpa [mul_assoc] using balance₂.symm
  exact mul_left_cancel₀ (by norm_num [nonzeroD] : 4 * D^2 ≠ 0) h

/-- An eightfold flux increase and a halved resolution obey the cubic invariant. -/
theorem one_third_pair_satisfies_published_cubic_invariant :
    (1 : ℚ) * 1^3 = 8 * (1 / 2)^3 := by
  norm_num

/-- A fourfold flux increase and a halved duration obey the stationary square invariant. -/
theorem one_half_pair_satisfies_stationary_square_invariant :
    (1 : ℚ) * 1^2 = 4 * (1 / 2)^2 := by
  norm_num

/-- The fourfold/half-time stationary pair violates the published cubic closure. -/
theorem drt_one_half_scaling_fails_published_cubic_invariant :
    (1 : ℚ) * 1^3 ≠ 4 * (1 / 2)^3 := by
  norm_num

/-- Derivative of the displayed objective `2 D t + sigma2 / (Phi t)`. -/
def drtDisplayedDerivative (D sigma2 Phi t : ℚ) : ℚ :=
  2 * D - sigma2 / (Phi * t^2)

/-- A zero derivative forces a quadratic, not cubic, flux-time balance. -/
theorem drt_displayed_stationarity_implies_quadratic_balance
    {D sigma2 Phi t : ℚ}
    (denominatorNonzero : Phi * t^2 ≠ 0)
    (stationary : drtDisplayedDerivative D sigma2 Phi t = 0) :
    2 * D * Phi * t^2 = sigma2 := by
  have ratioEq : sigma2 / (Phi * t^2) = 2 * D := by
    simp only [drtDisplayedDerivative] at stationary
    linarith
  have multiplied : sigma2 = 2 * D * (Phi * t^2) :=
    (div_eq_iff denominatorNonzero).mp ratioEq
  rw [multiplied]
  ring

/-- Two stationary experiments with fixed `D` and `sigma2` preserve `Phi * t^2`. -/
theorem drt_stationary_flux_time_square_invariant
    {D sigma2 Phi₁ Phi₂ t₁ t₂ : ℚ}
    (nonzeroD : D ≠ 0)
    (denom₁ : Phi₁ * t₁^2 ≠ 0)
    (denom₂ : Phi₂ * t₂^2 ≠ 0)
    (stationary₁ : drtDisplayedDerivative D sigma2 Phi₁ t₁ = 0)
    (stationary₂ : drtDisplayedDerivative D sigma2 Phi₂ t₂ = 0) :
    Phi₁ * t₁^2 = Phi₂ * t₂^2 := by
  have h₁ := drt_displayed_stationarity_implies_quadratic_balance denom₁ stationary₁
  have h₂ := drt_displayed_stationarity_implies_quadratic_balance denom₂ stationary₂
  have h : 2 * D * (Phi₁ * t₁^2) = 2 * D * (Phi₂ * t₂^2) := by
    calc
      2 * D * (Phi₁ * t₁^2) = sigma2 := by simpa [mul_assoc] using h₁
      _ = 2 * D * (Phi₂ * t₂^2) := by simpa [mul_assoc] using h₂.symm
  exact mul_left_cancel₀ (by norm_num [nonzeroD] : 2 * D ≠ 0) h

/--
Concrete incompatibility: with the displayed objective, increasing flux from
`1` to `8` cannot move a stationary time from `1` to `1/2`, even though that
pair has the claimed `Phi^(-1/3)` ratio.
-/
theorem drt_one_third_scaling_fails_displayed_stationarity :
    drtDisplayedDerivative 1 2 1 1 = 0 ∧
      drtDisplayedDerivative 1 2 8 (1 / 2) ≠ 0 := by
  norm_num [drtDisplayedDerivative]

end OCKIndividuationMSpaceComposition
