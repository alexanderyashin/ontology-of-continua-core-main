import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite frequency-response boundary

This module records the smallest algebraic analogue of a frequency-domain
transfer response: a declared multiplier on a finite frequency index.  It is
useful for MTF/OTF-inspired bookkeeping, but it does not define a Fourier
transform, physical frequency units, diffraction, or a calibrated optical
system.  Those interpretations require separate source-bound evidence.
-/

section FrequencyResponse

variable {Frequency : Type*} [Fintype Frequency]

/-- A declared finite transfer response acting pointwise on a spectrum. -/
def tomographicFrequencyTransfer
    (response spectrum : Frequency → ℝ) : Frequency → ℝ :=
  fun frequency => response frequency * spectrum frequency

theorem tomographicFrequencyTransfer_zero_spectrum
    (response : Frequency → ℝ) :
    tomographicFrequencyTransfer response (0 : Frequency → ℝ) = 0 := by
  funext frequency
  simp [tomographicFrequencyTransfer]

theorem tomographicFrequencyTransfer_zero_response
    (spectrum : Frequency → ℝ) :
    tomographicFrequencyTransfer (0 : Frequency → ℝ) spectrum = 0 := by
  funext frequency
  simp [tomographicFrequencyTransfer]

theorem tomographicFrequencyTransfer_add
    (response : Frequency → ℝ)
    (left right : Frequency → ℝ) :
    tomographicFrequencyTransfer response (fun frequency =>
      left frequency + right frequency) =
      fun frequency => tomographicFrequencyTransfer response left frequency +
        tomographicFrequencyTransfer response right frequency := by
  funext frequency
  simp [tomographicFrequencyTransfer, mul_add]

theorem tomographicFrequencyTransfer_smul
    (response : Frequency → ℝ)
    (scalar : ℝ) (spectrum : Frequency → ℝ) :
    tomographicFrequencyTransfer response (fun frequency =>
      scalar * spectrum frequency) =
      fun frequency => scalar * tomographicFrequencyTransfer response spectrum frequency := by
  funext frequency
  simp [tomographicFrequencyTransfer]
  ring

theorem tomographicFrequencyTransfer_composition
    (first second spectrum : Frequency → ℝ) :
    tomographicFrequencyTransfer first
        (tomographicFrequencyTransfer second spectrum) =
      tomographicFrequencyTransfer (fun frequency =>
        first frequency * second frequency) spectrum := by
  funext frequency
  simp [tomographicFrequencyTransfer, mul_assoc]

theorem tomographicFrequencyTransfer_abs_bound
    (response spectrum : Frequency → ℝ)
    (bound : ℝ)
    (spectrum_bound : ∀ frequency, |spectrum frequency| ≤ bound) :
    ∀ frequency,
      |tomographicFrequencyTransfer response spectrum frequency| ≤
      |response frequency| * bound := by
  intro frequency
  rw [tomographicFrequencyTransfer, abs_mul]
  exact mul_le_mul_of_nonneg_left (spectrum_bound frequency) (abs_nonneg _)

theorem tomographicFrequencyTransfer_uniform_abs_bound
    (response spectrum : Frequency → ℝ)
    (response_gain spectrum_gain : ℝ)
    (spectrum_gain_nonnegative : 0 ≤ spectrum_gain)
    (response_bound : ∀ frequency, |response frequency| ≤ response_gain)
    (spectrum_bound : ∀ frequency, |spectrum frequency| ≤ spectrum_gain) :
    ∀ frequency,
      |tomographicFrequencyTransfer response spectrum frequency| ≤
        response_gain * spectrum_gain := by
  intro frequency
  calc
    |tomographicFrequencyTransfer response spectrum frequency| ≤
        |response frequency| * spectrum_gain :=
      tomographicFrequencyTransfer_abs_bound response spectrum spectrum_gain
        spectrum_bound frequency
    _ ≤ response_gain * spectrum_gain :=
        mul_le_mul_of_nonneg_right (response_bound frequency)
          spectrum_gain_nonnegative

theorem tomographicFrequencyTransfer_composition_uniform_abs_bound
    (first second spectrum : Frequency → ℝ)
    (first_gain second_gain spectrum_gain : ℝ)
    (second_gain_nonnegative : 0 ≤ second_gain)
    (spectrum_gain_nonnegative : 0 ≤ spectrum_gain)
    (first_bound : ∀ frequency, |first frequency| ≤ first_gain)
    (second_bound : ∀ frequency, |second frequency| ≤ second_gain)
    (spectrum_bound : ∀ frequency, |spectrum frequency| ≤ spectrum_gain) :
    ∀ frequency,
      |tomographicFrequencyTransfer first
          (tomographicFrequencyTransfer second spectrum) frequency| ≤
        first_gain * second_gain * spectrum_gain := by
  intro frequency
  have inner_bound : ∀ frequency,
      |tomographicFrequencyTransfer second spectrum frequency| ≤
        second_gain * spectrum_gain :=
    tomographicFrequencyTransfer_uniform_abs_bound second spectrum
      second_gain spectrum_gain spectrum_gain_nonnegative second_bound
        spectrum_bound
  calc
    |tomographicFrequencyTransfer first
        (tomographicFrequencyTransfer second spectrum) frequency| ≤
        first_gain * (second_gain * spectrum_gain) :=
      tomographicFrequencyTransfer_uniform_abs_bound first
        (tomographicFrequencyTransfer second spectrum) first_gain
        (second_gain * spectrum_gain)
        (mul_nonneg second_gain_nonnegative spectrum_gain_nonnegative)
        first_bound inner_bound frequency
    _ = first_gain * second_gain * spectrum_gain := by ring

/-! A response is invertible only on a declared band and only with a supplied
    inverse certificate.  This is the finite analogue of a calibrated
    deconvolution/MTF passband; it makes no claim about frequencies outside
    the band. -/
structure TomographicFrequencyBandInverseCertificate
    (response : Frequency → ℝ) where
  band : Set Frequency
  inverse : Frequency → ℝ
  left_inverse_on_band : ∀ frequency, frequency ∈ band →
    inverse frequency * response frequency = 1
  inverse_gain : ℝ
  inverse_gain_nonnegative : 0 ≤ inverse_gain
  inverse_gain_bound : ∀ frequency, frequency ∈ band →
    |inverse frequency| ≤ inverse_gain

noncomputable def tomographicFrequencyApplyInverseOnBand
    {response : Frequency → ℝ}
    (certificate : TomographicFrequencyBandInverseCertificate response)
    (observed : Frequency → ℝ) : Frequency → ℝ :=
  by
    classical
    exact fun frequency => if frequency ∈ certificate.band then
      certificate.inverse frequency * observed frequency
    else 0

theorem tomographicFrequencyApplyInverseOnBand_exact_on_transfer
    {response : Frequency → ℝ}
    (certificate : TomographicFrequencyBandInverseCertificate response)
    (spectrum : Frequency → ℝ) :
    ∀ frequency, frequency ∈ certificate.band →
      tomographicFrequencyApplyInverseOnBand certificate
        (tomographicFrequencyTransfer response spectrum) frequency =
        spectrum frequency := by
  intro frequency in_band
  simp [tomographicFrequencyApplyInverseOnBand, in_band,
    tomographicFrequencyTransfer]
  rw [← mul_assoc, certificate.left_inverse_on_band frequency in_band]
  simp

theorem tomographicFrequencyApplyInverseOnBand_exact_of_band_limited
    {response : Frequency → ℝ}
    (certificate : TomographicFrequencyBandInverseCertificate response)
    (spectrum : Frequency → ℝ)
    (zero_off_band : ∀ frequency, frequency ∉ certificate.band →
      spectrum frequency = 0) :
    tomographicFrequencyApplyInverseOnBand certificate
        (tomographicFrequencyTransfer response spectrum) =
      spectrum := by
  funext frequency
  by_cases in_band : frequency ∈ certificate.band
  · exact tomographicFrequencyApplyInverseOnBand_exact_on_transfer
      certificate spectrum frequency in_band
  · simp [tomographicFrequencyApplyInverseOnBand, in_band,
      zero_off_band frequency in_band, tomographicFrequencyTransfer]

theorem tomographicFrequencyApplyInverseOnBand_noise_bound
    {response : Frequency → ℝ}
    (certificate : TomographicFrequencyBandInverseCertificate response)
    (first second : Frequency → ℝ)
    (bound : ℝ)
    (difference_bound : ∀ frequency, frequency ∈ certificate.band →
      |first frequency - second frequency| ≤ bound) :
    ∀ frequency, frequency ∈ certificate.band →
      |tomographicFrequencyApplyInverseOnBand certificate first frequency -
        tomographicFrequencyApplyInverseOnBand certificate second frequency| ≤
        certificate.inverse_gain * bound := by
  intro frequency in_band
  simp only [tomographicFrequencyApplyInverseOnBand, if_pos in_band]
  rw [← mul_sub, abs_mul]
  calc
    |certificate.inverse frequency| * |first frequency - second frequency| ≤
        |certificate.inverse frequency| * bound :=
      mul_le_mul_of_nonneg_left (difference_bound frequency in_band)
        (abs_nonneg _)
    _ ≤ certificate.inverse_gain * bound :=
      mul_le_mul_of_nonneg_right
        (certificate.inverse_gain_bound frequency in_band)
        (le_trans (abs_nonneg _) (difference_bound frequency in_band))

theorem tomographicFrequencyApplyInverseOnBand_noise_bound_global
    {response : Frequency → ℝ}
    (certificate : TomographicFrequencyBandInverseCertificate response)
    (first second : Frequency → ℝ)
    (bound : ℝ)
    (bound_nonnegative : 0 ≤ bound)
    (difference_bound : ∀ frequency, frequency ∈ certificate.band →
      |first frequency - second frequency| ≤ bound) :
    ∀ frequency,
      |tomographicFrequencyApplyInverseOnBand certificate first frequency -
        tomographicFrequencyApplyInverseOnBand certificate second frequency| ≤
        certificate.inverse_gain * bound := by
  intro frequency
  by_cases in_band : frequency ∈ certificate.band
  · exact tomographicFrequencyApplyInverseOnBand_noise_bound certificate
      first second bound difference_bound frequency in_band
  · simp [tomographicFrequencyApplyInverseOnBand, in_band]
    exact mul_nonneg certificate.inverse_gain_nonnegative bound_nonnegative

end FrequencyResponse

end OCKIndividuationMSpaceComposition
