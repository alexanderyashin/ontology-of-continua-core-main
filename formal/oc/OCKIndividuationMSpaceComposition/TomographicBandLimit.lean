import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite band-limit boundary for tomographic spectral coordinates

This module does not define a Fourier transform or import a Nyquist theorem.
It records the smaller contract that a finite spectral representation can
actually support: coefficients outside a declared band are absent, the energy
inside that band is nonnegative, and two band-limited coefficient fields that
agree on the band agree everywhere.  Fourier geometry, aliasing rates and
physical frequency interpretation remain separate obligations.
-/

section BandLimit

variable {Frequency : Type*} [DecidableEq Frequency]

/-- Every coefficient outside `band` is declared absent. -/
def TomographicBandLimited
    (band : Finset Frequency)
    (coefficients : Frequency → ℝ) : Prop :=
  ∀ frequency, frequency ∉ band → coefficients frequency = 0

/-- Squared coefficient energy retained by a finite spectral band. -/
def tomographicBandEnergy
    (band : Finset Frequency)
    (coefficients : Frequency → ℝ) : ℝ :=
  ∑ frequency ∈ band, (coefficients frequency) ^ 2

/-- The finite spectral projector keeps exactly the declared band and
    discards every coefficient outside it.  It is a representation operator,
    not a claim that the band came from a Fourier transform. -/
def tomographicBandProjection
    (band : Finset Frequency)
    (coefficients : Frequency → ℝ) : Frequency → ℝ :=
  fun frequency => if frequency ∈ band then coefficients frequency else 0

/-- Squared truncation error measured on a declared finite frequency universeSet. -/
def tomographicBandProjectionResidual
    (universeSet band : Finset Frequency)
    (coefficients : Frequency → ℝ) : ℝ :=
  ∑ frequency ∈ universeSet,
    (coefficients frequency - tomographicBandProjection band coefficients frequency) ^ 2

theorem tomographicBandProjection_on_band
    (band : Finset Frequency)
    (coefficients : Frequency → ℝ) :
    ∀ frequency, frequency ∈ band →
      tomographicBandProjection band coefficients frequency = coefficients frequency := by
  intro frequency membership
  simp [tomographicBandProjection, membership]

theorem tomographicBandProjection_is_band_limited
    (band : Finset Frequency)
    (coefficients : Frequency → ℝ) :
    TomographicBandLimited band (tomographicBandProjection band coefficients) := by
  intro frequency not_membership
  simp [tomographicBandProjection, not_membership]

theorem tomographicBandProjection_idempotent
    (band : Finset Frequency)
    (coefficients : Frequency → ℝ) :
    tomographicBandProjection band (tomographicBandProjection band coefficients) =
      tomographicBandProjection band coefficients := by
  funext frequency
  by_cases membership : frequency ∈ band <;>
    simp [tomographicBandProjection, membership]

theorem tomographicBandProjection_add
    (band : Finset Frequency)
    (first second : Frequency → ℝ) :
    tomographicBandProjection band (fun frequency =>
      first frequency + second frequency) =
      fun frequency => tomographicBandProjection band first frequency +
        tomographicBandProjection band second frequency := by
  funext frequency
  by_cases membership : frequency ∈ band <;>
    simp [tomographicBandProjection, membership]

theorem tomographicBandProjection_smul
    (band : Finset Frequency)
    (scalar : ℝ)
    (coefficients : Frequency → ℝ) :
    tomographicBandProjection band (fun frequency => scalar * coefficients frequency) =
      fun frequency => scalar * tomographicBandProjection band coefficients frequency := by
  funext frequency
  by_cases membership : frequency ∈ band <;>
    simp [tomographicBandProjection, membership]

theorem tomographicBandProjection_compose_of_subset
    (small large : Finset Frequency)
    (coefficients : Frequency → ℝ)
    (nested : small ⊆ large) :
    tomographicBandProjection small
        (tomographicBandProjection large coefficients) =
      tomographicBandProjection small coefficients := by
  funext frequency
  by_cases in_small : frequency ∈ small
  · have in_large : frequency ∈ large := nested in_small
    simp [tomographicBandProjection, in_small, in_large]
  · simp [tomographicBandProjection, in_small]

theorem tomographicBandProjection_eq_self_of_band_limited
    (band : Finset Frequency)
    (coefficients : Frequency → ℝ)
    (band_limited : TomographicBandLimited band coefficients) :
    tomographicBandProjection band coefficients = coefficients := by
  funext frequency
  by_cases membership : frequency ∈ band
  · simp [tomographicBandProjection, membership]
  · simp [tomographicBandProjection, membership, band_limited frequency membership]

theorem tomographicBandProjectionResidual_nonnegative
    (universeSet band : Finset Frequency)
    (coefficients : Frequency → ℝ) :
    0 ≤ tomographicBandProjectionResidual universeSet band coefficients := by
  unfold tomographicBandProjectionResidual
  exact Finset.sum_nonneg (fun frequency _ => sq_nonneg _)

theorem tomographicBandProjectionResidual_zero_of_band_limited
    (universeSet band : Finset Frequency)
    (coefficients : Frequency → ℝ)
    (band_limited : TomographicBandLimited band coefficients) :
    tomographicBandProjectionResidual universeSet band coefficients = 0 := by
  unfold tomographicBandProjectionResidual
  apply Finset.sum_eq_zero
  intro frequency membership
  by_cases in_band : frequency ∈ band
  · simp [tomographicBandProjection, in_band]
  · simp [tomographicBandProjection, in_band, band_limited frequency in_band]

/-! Enlarging the declared band cannot increase the finite truncation
residual. This is a multiresolution statement about the explicit projection,
not a frequency-domain or signal-recovery theorem. -/

theorem tomographicBandProjectionResidual_mono_of_subset
    (universeSet small large : Finset Frequency)
    (coefficients : Frequency → ℝ)
    (small_subset_large : small ⊆ large) :
    tomographicBandProjectionResidual universeSet large coefficients ≤
      tomographicBandProjectionResidual universeSet small coefficients := by
  unfold tomographicBandProjectionResidual
  apply Finset.sum_le_sum
  intro frequency frequency_in_universe
  by_cases in_small : frequency ∈ small
  · have in_large : frequency ∈ large := small_subset_large in_small
    simp [tomographicBandProjection, in_small, in_large]
  · by_cases in_large : frequency ∈ large
    · simpa [tomographicBandProjection, in_small, in_large] using
        (sq_nonneg (coefficients frequency))
    · simp [tomographicBandProjection, in_small, in_large]

theorem tomographicBandEnergy_nonnegative
    (band : Finset Frequency)
    (coefficients : Frequency → ℝ) :
    0 ≤ tomographicBandEnergy band coefficients := by
  unfold tomographicBandEnergy
  exact Finset.sum_nonneg (fun frequency _ => sq_nonneg _)

theorem tomographicBandEnergy_zero_of_on_band_zero
    (band : Finset Frequency)
    (coefficients : Frequency → ℝ)
    (zero_on_band : ∀ frequency, frequency ∈ band → coefficients frequency = 0) :
    tomographicBandEnergy band coefficients = 0 := by
  unfold tomographicBandEnergy
  apply Finset.sum_eq_zero
  intro frequency membership
  simp [zero_on_band frequency membership]

theorem tomographicBandLimited_extensional
    (band : Finset Frequency)
    (first second : Frequency → ℝ)
    (first_band_limited : TomographicBandLimited band first)
    (second_band_limited : TomographicBandLimited band second)
    (agree_on_band : ∀ frequency, frequency ∈ band →
      first frequency = second frequency) :
    first = second := by
  funext frequency
  by_cases membership : frequency ∈ band
  · exact agree_on_band frequency membership
  · rw [first_band_limited frequency membership,
    second_band_limited frequency membership]

end BandLimit

end OCKIndividuationMSpaceComposition