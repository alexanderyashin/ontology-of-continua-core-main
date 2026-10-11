import Mathlib.Data.Fin.Basic
import Mathlib.Data.Real.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite sampling adequacy

This module formalizes the part of sampling theory that transfers without a
band-limit metaphor: a non-surjective sampling map cannot identify an
arbitrary finite signal, while a surjective map is enough for injectivity of
the sampling operator. Any Nyquist-style frequency constant needs additional
structure and is intentionally not asserted here.
-/

def tomographicSample
    {Sample Signal : Type*} (signal : Signal → ℝ)
    (sample : Sample → Signal) : Sample → ℝ :=
  signal ∘ sample

theorem tomographicSampling_injective_of_surjective
    {Sample Signal : Type*}
    (sample : Sample → Signal)
    (surjective : Function.Surjective sample) :
    Function.Injective (fun signal : Signal → ℝ => tomographicSample signal sample) := by
  intro first second equal
  funext signal
  obtain ⟨source, source_maps⟩ := surjective signal
  have sampled_equal := congrFun equal source
  simpa [tomographicSample, source_maps] using sampled_equal

theorem tomographicSampling_noninjective_of_not_surjective
    {Sample Signal : Type*} [DecidableEq Signal]
    (sample : Sample → Signal)
    (not_surjective : ¬ Function.Surjective sample) :
    ∃ first second : Signal → ℝ,
      first ≠ second ∧ tomographicSample first sample = tomographicSample second sample := by
  classical
  have exists_hidden : ∃ hidden : Signal, ∀ source, sample source ≠ hidden := by
    by_contra no_hidden
    apply not_surjective
    intro signal
    by_contra no_source
    apply no_hidden
    refine ⟨signal, ?_⟩
    intro source
    intro source_maps
    apply no_source
    exact ⟨source, source_maps⟩
  obtain ⟨hidden, hidden_absent⟩ := exists_hidden
  let first : Signal → ℝ := fun _ => 0
  let second : Signal → ℝ := fun signal => if signal = hidden then 1 else 0
  have different : first ≠ second := by
    intro equal
    have values_equal := congrFun equal hidden
    have impossible : (0 : ℝ) = 1 := by
      simpa [first, second] using values_equal
    exact zero_ne_one impossible
  have sampled_equal : tomographicSample first sample = tomographicSample second sample := by
    funext source
    simp [tomographicSample, first, second, hidden_absent source]
  exact ⟨first, second, different, sampled_equal⟩

end OCKIndividuationMSpaceComposition