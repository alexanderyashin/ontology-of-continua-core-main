import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Finite observation coverage boundary

Tomographic rays and views are useful only relative to a declared region that
must be covered.  This module keeps coverage separate from injectivity: it
records which coordinates have at least one registered observation, transfers
coverage monotonically when support is enlarged, and emits an explicit missing
coordinate when coverage fails.  Agreement of observations yields agreement of
states only on the declared covered region; no global reconstruction or
Nyquist-style claim is inferred.
-/

section CoverageBoundary

variable {Coordinate View : Type*} [DecidableEq Coordinate]

/-- Coordinates sampled by each registered view. -/
def TomographicViewCoverage (covered : View → Finset Coordinate)
    (required : Finset Coordinate) : Prop :=
  ∀ coordinate, coordinate ∈ required → ∃ view, coordinate ∈ covered view

/-- Pointwise inclusion of one registered support family in another. -/
def TomographicCoverageExtension
    (covered extended : View → Finset Coordinate) : Prop :=
  ∀ view, covered view ⊆ extended view

/-- Agreement of two coordinate fields on every registered sample. -/
def TomographicCoveredAgreement
    (covered : View → Finset Coordinate)
    (left right : Coordinate → ℝ) : Prop :=
  ∀ view coordinate, coordinate ∈ covered view → left coordinate = right coordinate

theorem tomographicCoverage_of_extension
    (covered extended : View → Finset Coordinate)
    (required : Finset Coordinate)
    (extension : TomographicCoverageExtension covered extended)
    (coverage : TomographicViewCoverage covered required) :
    TomographicViewCoverage extended required := by
  intro coordinate required_membership
  obtain ⟨view, covered_membership⟩ := coverage coordinate required_membership
  exact ⟨view, extension view covered_membership⟩

theorem tomographicCoverage_of_required_subset
    (covered : View → Finset Coordinate)
    (small large : Finset Coordinate)
    (small_subset_large : small ⊆ large)
    (coverage : TomographicViewCoverage covered large) :
    TomographicViewCoverage covered small := by
  intro coordinate small_membership
  exact coverage coordinate (small_subset_large small_membership)

theorem tomographicCoverage_union_left
    (left right : View → Finset Coordinate)
    (required : Finset Coordinate)
    (coverage : TomographicViewCoverage left required) :
    TomographicViewCoverage (fun view => left view ∪ right view) required := by
  intro coordinate required_membership
  obtain ⟨view, left_membership⟩ := coverage coordinate required_membership
  exact ⟨view, Finset.mem_union_left _ left_membership⟩

theorem tomographicCoverage_agreement_implies_required_equality
    (covered : View → Finset Coordinate)
    (required : Finset Coordinate)
    (left right : Coordinate → ℝ)
    (coverage : TomographicViewCoverage covered required)
    (agreement : TomographicCoveredAgreement covered left right) :
    ∀ coordinate, coordinate ∈ required → left coordinate = right coordinate := by
  intro coordinate required_membership
  obtain ⟨view, covered_membership⟩ := coverage coordinate required_membership
  exact agreement view coordinate covered_membership

theorem tomographicCoverage_missing_witness
    (covered : View → Finset Coordinate)
    (required : Finset Coordinate)
    (not_covered : ¬ TomographicViewCoverage covered required) :
    ∃ coordinate, coordinate ∈ required ∧ ∀ view, coordinate ∉ covered view := by
  classical
  by_contra no_missing
  apply not_covered
  intro coordinate required_membership
  by_contra no_view
  have no_view' : ∀ view, coordinate ∉ covered view := by
    simpa only [not_exists] using no_view
  exact no_missing ⟨coordinate, required_membership, no_view'⟩

section RayCoverage

variable {Ray Sample : Type*}

/-- Every required coordinate occurs in at least one registered ray sample. -/
def TomographicRayCoverage
    (ray : View → Ray → Sample → Coordinate)
    (required : Finset Coordinate) : Prop :=
  ∀ coordinate, coordinate ∈ required →
    ∃ view rayId sample, ray view rayId sample = coordinate

/-- A declared per-view support contains every coordinate sampled by its rays. -/
def TomographicRaySupportWithin
    (covered : View → Finset Coordinate)
    (ray : View → Ray → Sample → Coordinate) : Prop :=
  ∀ view rayId sample, ray view rayId sample ∈ covered view

theorem tomographicRayCoverage_implies_viewCoverage
    (covered : View → Finset Coordinate)
    (ray : View → Ray → Sample → Coordinate)
    (required : Finset Coordinate)
    (support : TomographicRaySupportWithin covered ray)
    (coverage : TomographicRayCoverage ray required) :
    TomographicViewCoverage covered required := by
  intro coordinate required_membership
  obtain ⟨view, rayId, sample, ray_eq⟩ := coverage coordinate required_membership
  refine ⟨view, ?_⟩
  rw [← ray_eq]
  exact support view rayId sample

theorem tomographicRayCoverage_missing_witness
    (ray : View → Ray → Sample → Coordinate)
    (required : Finset Coordinate)
    (not_covered : ¬ TomographicRayCoverage ray required) :
    ∃ coordinate, coordinate ∈ required ∧
      ∀ view rayId sample, ray view rayId sample ≠ coordinate := by
  classical
  by_contra no_missing
  apply not_covered
  intro coordinate required_membership
  by_contra no_sample
  have no_sample' : ∀ view rayId sample, ray view rayId sample ≠ coordinate := by
    simpa only [not_exists] using no_sample
  exact no_missing ⟨coordinate, required_membership, no_sample'⟩

end RayCoverage

end CoverageBoundary

end OCKIndividuationMSpaceComposition
