import Mathlib.Data.Finset.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

section OverlapConsistency

variable {Coordinate View : Type*} [DecidableEq Coordinate]

/-!
# Overlap consistency for projection gluing

Coverage only says that a coordinate is present.  Before several views are
glued, readings on their shared support must also agree.  This finite relation
is deliberately weaker than injectivity or reconstruction: it is a local
compatibility gate for registered projections.
-/

def TomographicOverlapAgreement
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ) : Prop :=
  ∀ left right coordinate,
    coordinate ∈ support left ∩ support right →
      reading left coordinate = reading right coordinate

def TomographicPairwiseConsistency
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ) : Prop :=
  ∀ left right coordinate,
    coordinate ∈ support left → coordinate ∈ support right →
      reading left coordinate = reading right coordinate

def TomographicOverlapBoundedAgreement
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (bound : ℝ) : Prop :=
  0 ≤ bound ∧
    ∀ left right coordinate,
      coordinate ∈ support left ∩ support right →
        |reading left coordinate - reading right coordinate| ≤ bound

def TomographicOverlapStep
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (coordinate : Coordinate) (left right : View) : Prop :=
    coordinate ∈ support left ∩ support right ∧
    reading left coordinate = reading right coordinate

def TomographicGluedReading
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (coordinate : Coordinate)
    (value : ℝ) : Prop :=
  ∃ view, coordinate ∈ support view ∧ reading view coordinate = value

def TomographicGluedReadingInterval
    (anchor : ℝ) (bound : ℝ) (value : ℝ) : Prop :=
  anchor - bound ≤ value ∧ value ≤ anchor + bound

inductive TomographicOverlapReachable
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (coordinate : Coordinate) : View → View → Prop
  | refl (view : View) : TomographicOverlapReachable support reading coordinate view view
  | tail {left middle right : View} :
      TomographicOverlapReachable support reading coordinate left middle →
      TomographicOverlapStep support reading coordinate middle right →
      TomographicOverlapReachable support reading coordinate left right

inductive TomographicOverlapBoundedPath
    (support : View → Finset Coordinate)
    (coordinate : Coordinate) : View → View → ℕ → Prop
  | refl (view : View) :
      TomographicOverlapBoundedPath support coordinate view view 0
  | tail {left middle right : View} {length : ℕ} :
      TomographicOverlapBoundedPath support coordinate left middle length →
      coordinate ∈ support middle ∩ support right →
      TomographicOverlapBoundedPath support coordinate left right (length + 1)

theorem tomographicOverlapAgreement_iff_pairwiseConsistency
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ) :
    TomographicOverlapAgreement support reading ↔
      TomographicPairwiseConsistency support reading := by
  constructor
  · intro agreement left right coordinate left_membership right_membership
    exact agreement left right coordinate
      (Finset.mem_inter.mpr ⟨left_membership, right_membership⟩)
  · intro consistency left right coordinate overlap_membership
    exact consistency left right coordinate
      (Finset.mem_inter.mp overlap_membership).1
      (Finset.mem_inter.mp overlap_membership).2

theorem tomographicOverlapReachable_agreement
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (coordinate : Coordinate) (left right : View)
    (reachable : TomographicOverlapReachable support reading coordinate left right) :
    reading left coordinate = reading right coordinate := by
  induction reachable with
  | refl => rfl
  | tail reachable step ih => exact ih.trans step.2

theorem tomographicGluedReading_unique
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (agreement : TomographicOverlapAgreement support reading)
    {coordinate : Coordinate} {value₁ value₂ : ℝ}
    (left : TomographicGluedReading support reading coordinate value₁)
    (right : TomographicGluedReading support reading coordinate value₂) :
    value₁ = value₂ := by
  rcases left with ⟨leftView, leftSupport, leftValue⟩
  rcases right with ⟨rightView, rightSupport, rightValue⟩
  calc
    value₁ = reading leftView coordinate := leftValue.symm
    _ = reading rightView coordinate := agreement leftView rightView coordinate
      (Finset.mem_inter.mpr ⟨leftSupport, rightSupport⟩)
    _ = value₂ := rightValue

theorem tomographicGluedReading_exists_of_coverage
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (required : Finset Coordinate)
    (coverage : ∀ coordinate, coordinate ∈ required →
      ∃ view, coordinate ∈ support view) :
    ∀ coordinate, coordinate ∈ required →
      ∃ value, TomographicGluedReading support reading coordinate value := by
  intro coordinate required_membership
  obtain ⟨view, view_support⟩ := coverage coordinate required_membership
  exact ⟨reading view coordinate, ⟨view, view_support, rfl⟩⟩

noncomputable def tomographicCanonicalGluedField
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (required : Finset Coordinate)
    (coverage : ∀ coordinate, coordinate ∈ required →
      ∃ view, coordinate ∈ support view) :
    {coordinate : Coordinate // coordinate ∈ required} → ℝ :=
  fun coordinate =>
    Classical.choose
      (tomographicGluedReading_exists_of_coverage support reading required
        coverage coordinate.1 coordinate.property)

theorem tomographicGluedReading_existsUnique_of_coverage
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (required : Finset Coordinate)
    (coverage : ∀ coordinate, coordinate ∈ required →
      ∃ view, coordinate ∈ support view)
    (agreement : TomographicOverlapAgreement support reading) :
    ∀ coordinate, coordinate ∈ required →
      ∃! value, TomographicGluedReading support reading coordinate value := by
  intro coordinate required_membership
  obtain ⟨view, view_support⟩ := coverage coordinate required_membership
  refine ⟨reading view coordinate, ⟨view, view_support, rfl⟩, ?_⟩
  intro value right
  exact (tomographicGluedReading_unique support reading agreement
    ⟨view, view_support, rfl⟩ right).symm

theorem tomographicGluedReading_bounded_spread
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    {bound : ℝ}
    (bounded : TomographicOverlapBoundedAgreement support reading bound)
    {coordinate : Coordinate} {value₁ value₂ : ℝ}
    (left : TomographicGluedReading support reading coordinate value₁)
    (right : TomographicGluedReading support reading coordinate value₂) :
    |value₁ - value₂| ≤ bound := by
  rcases left with ⟨leftView, leftSupport, leftValue⟩
  rcases right with ⟨rightView, rightSupport, rightValue⟩
  rw [← leftValue, ← rightValue]
  exact bounded.2 leftView rightView coordinate
    (Finset.mem_inter.mpr ⟨leftSupport, rightSupport⟩)

theorem tomographicOverlapBoundedAgreement_chain_two_step
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    {bound : ℝ}
    (bounded : TomographicOverlapBoundedAgreement support reading bound)
    (left middle right : View) (coordinate : Coordinate)
    (left_middle : coordinate ∈ support left ∩ support middle)
    (middle_right : coordinate ∈ support middle ∩ support right) :
    |reading left coordinate - reading right coordinate| ≤ 2 * bound := by
  calc
    |reading left coordinate - reading right coordinate| ≤
        |reading left coordinate - reading middle coordinate| +
          |reading middle coordinate - reading right coordinate| :=
      abs_sub_le _ _ _
    _ ≤ bound + bound := add_le_add
      (bounded.2 left middle coordinate left_middle)
      (bounded.2 middle right coordinate middle_right)
    _ = 2 * bound := by simp [two_mul]

theorem tomographicOverlapBoundedAgreement_path_error
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    {bound : ℝ}
    (bounded : TomographicOverlapBoundedAgreement support reading bound)
    {coordinate : Coordinate} {left right : View} {length : ℕ}
    (path : TomographicOverlapBoundedPath support coordinate left right length) :
    |reading left coordinate - reading right coordinate| ≤ length * bound := by
  induction path with
  | refl => simp
  | @tail middle right length path overlap ih =>
      calc
        |reading left coordinate - reading right coordinate| ≤
            |reading left coordinate - reading middle coordinate| +
              |reading middle coordinate - reading right coordinate| :=
          abs_sub_le _ _ _
        _ ≤ length * bound + bound := add_le_add ih
          (bounded.2 middle right coordinate overlap)
        _ ≤ (length + 1) * bound := by
          rw [add_mul, one_mul]
        _ = (↑(length + 1) : ℝ) * bound := by
          rw [Nat.cast_add, Nat.cast_one]

theorem tomographicGluedReading_bounded_path_error_to_anchor
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    {bound : ℝ}
    (bounded : TomographicOverlapBoundedAgreement support reading bound)
    {coordinate : Coordinate} (anchor : View) {value : ℝ}
    (path_to_view : ∀ view, ∃ length,
      TomographicOverlapBoundedPath support coordinate anchor view length)
    (candidate : TomographicGluedReading support reading coordinate value) :
    ∃ length, |reading anchor coordinate - value| ≤ length * bound := by
  rcases candidate with ⟨view, view_support, view_value⟩
  obtain ⟨length, path⟩ := path_to_view view
  refine ⟨length, ?_⟩
  rw [← view_value]
  exact tomographicOverlapBoundedAgreement_path_error support reading bounded path

theorem tomographicOverlapBoundedAgreement_path_exact_of_zero
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (bounded : TomographicOverlapBoundedAgreement support reading 0)
    {coordinate : Coordinate} {left right : View} {length : ℕ}
    (path : TomographicOverlapBoundedPath support coordinate left right length) :
    reading left coordinate = reading right coordinate := by
  have error_bound := tomographicOverlapBoundedAgreement_path_error
    support reading bounded path
  have error_zero :
      |reading left coordinate - reading right coordinate| = 0 := by
    apply le_antisymm
    · simpa using error_bound
    · exact abs_nonneg _
  exact sub_eq_zero.mp (abs_eq_zero.mp error_zero)

theorem tomographicGluedReading_mem_anchor_interval
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    {bound : ℝ}
    (bounded : TomographicOverlapBoundedAgreement support reading bound)
    (anchor : View) {coordinate : Coordinate}
    (anchor_support : coordinate ∈ support anchor)
    {value : ℝ}
    (candidate : TomographicGluedReading support reading coordinate value) :
    TomographicGluedReadingInterval (reading anchor coordinate) bound value := by
  unfold TomographicGluedReadingInterval
  have spread := tomographicGluedReading_bounded_spread support reading bounded
    ⟨anchor, anchor_support, rfl⟩ candidate
  have lower := (abs_le.mp spread).1
  have upper := (abs_le.mp spread).2
  constructor <;> linarith

theorem tomographicCanonicalGluedField_spec
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (required : Finset Coordinate)
    (coverage : ∀ coordinate, coordinate ∈ required →
      ∃ view, coordinate ∈ support view)
    (coordinate : {coordinate : Coordinate // coordinate ∈ required}) :
    TomographicGluedReading support reading coordinate.1
      (tomographicCanonicalGluedField support reading required coverage coordinate) := by
  exact Classical.choose_spec
    (tomographicGluedReading_exists_of_coverage support reading required
      coverage coordinate.1 coordinate.property)

theorem tomographicCanonicalGluedField_agreement
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (required : Finset Coordinate)
    (coverage : ∀ coordinate, coordinate ∈ required →
      ∃ view, coordinate ∈ support view)
    (agreement : TomographicOverlapAgreement support reading)
    (coordinate : {coordinate : Coordinate // coordinate ∈ required})
    {value : ℝ}
    (candidate : TomographicGluedReading support reading coordinate.1 value) :
    value = tomographicCanonicalGluedField support reading required coverage coordinate := by
  exact tomographicGluedReading_unique support reading agreement candidate
    (tomographicCanonicalGluedField_spec support reading required coverage coordinate)

theorem tomographicCanonicalGluedField_coverage_independent
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (required : Finset Coordinate)
    (coverage₁ coverage₂ : ∀ coordinate, coordinate ∈ required →
      ∃ view, coordinate ∈ support view)
    (agreement : TomographicOverlapAgreement support reading)
    (coordinate : {coordinate : Coordinate // coordinate ∈ required}) :
    tomographicCanonicalGluedField support reading required coverage₁ coordinate =
      tomographicCanonicalGluedField support reading required coverage₂ coordinate := by
  exact tomographicGluedReading_unique support reading agreement
    (tomographicCanonicalGluedField_spec support reading required coverage₁ coordinate)
    (tomographicCanonicalGluedField_spec support reading required coverage₂ coordinate)

theorem tomographicCanonicalGluedField_recovers_view
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (required : Finset Coordinate)
    (coverage : ∀ coordinate, coordinate ∈ required →
      ∃ view, coordinate ∈ support view)
    (agreement : TomographicOverlapAgreement support reading)
    (coordinate : {coordinate : Coordinate // coordinate ∈ required})
    (view : View)
    (view_support : coordinate.1 ∈ support view) :
    tomographicCanonicalGluedField support reading required coverage coordinate =
      reading view coordinate.1 := by
  exact (tomographicCanonicalGluedField_agreement support reading required coverage
    agreement coordinate ⟨view, view_support, rfl⟩).symm

theorem tomographicCanonicalGluedField_mem_anchor_interval
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    {bound : ℝ}
    (bounded : TomographicOverlapBoundedAgreement support reading bound)
    (required : Finset Coordinate)
    (coverage : ∀ coordinate, coordinate ∈ required →
      ∃ view, coordinate ∈ support view)
    (anchor : View)
    (coordinate : {coordinate : Coordinate // coordinate ∈ required})
    (anchor_support : coordinate.1 ∈ support anchor) :
    TomographicGluedReadingInterval (reading anchor coordinate.1) bound
      (tomographicCanonicalGluedField support reading required coverage coordinate) := by
  exact tomographicGluedReading_mem_anchor_interval support reading bounded anchor
    anchor_support
    (tomographicCanonicalGluedField_spec support reading required coverage coordinate)

theorem tomographicGluedReading_existsUnique_of_zero_bound_coverage
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (required : Finset Coordinate)
    (coverage : ∀ coordinate, coordinate ∈ required →
      ∃ view, coordinate ∈ support view)
    (bounded : TomographicOverlapBoundedAgreement support reading 0) :
    ∀ coordinate, coordinate ∈ required →
      ∃! value, TomographicGluedReading support reading coordinate value := by
  apply tomographicGluedReading_existsUnique_of_coverage support reading required
    coverage
  intro left right coordinate overlap_membership
  have bounded' := bounded.2 left right coordinate overlap_membership
  have absolute_zero :
      |reading left coordinate - reading right coordinate| = 0 :=
    le_antisymm bounded' (abs_nonneg _)
  exact sub_eq_zero.mp (abs_eq_zero.mp absolute_zero)

theorem tomographicOverlapAgreement_symmetric
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (agreement : TomographicOverlapAgreement support reading) :
    ∀ left right coordinate,
      coordinate ∈ support right ∩ support left →
        reading left coordinate = reading right coordinate := by
  intro left right coordinate overlap_membership
  exact (agreement right left coordinate
    (Finset.mem_inter.mpr ⟨
      (Finset.mem_inter.mp overlap_membership).1,
      (Finset.mem_inter.mp overlap_membership).2⟩)).symm

theorem tomographicOverlapAgreement_on_shared_subset
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (agreement : TomographicOverlapAgreement support reading)
    (left right : View)
    (shared : Finset Coordinate)
    (shared_subset : shared ⊆ support left ∩ support right) :
    ∀ coordinate, coordinate ∈ shared →
      reading left coordinate = reading right coordinate := by
  intro coordinate shared_membership
  exact agreement left right coordinate
    (shared_subset shared_membership)

theorem tomographicOverlapAgreement_restrict
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (agreement : TomographicOverlapAgreement support reading)
    (reduced : View → Finset Coordinate)
    (reduced_subset : ∀ view, reduced view ⊆ support view) :
    TomographicOverlapAgreement reduced reading := by
  intro left right coordinate overlap_membership
  apply agreement left right coordinate
  refine Finset.mem_inter.mpr ⟨?_, ?_⟩
  · exact reduced_subset left (Finset.mem_inter.mp overlap_membership).1
  · exact reduced_subset right (Finset.mem_inter.mp overlap_membership).2

theorem tomographicOverlapAgreement_implies_bounded
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (agreement : TomographicOverlapAgreement support reading)
    (bound : ℝ)
    (bound_nonnegative : 0 ≤ bound) :
    TomographicOverlapBoundedAgreement support reading bound := by
  refine ⟨bound_nonnegative, ?_⟩
  intro left right coordinate overlap_membership
  rw [agreement left right coordinate overlap_membership]
  simp
  exact bound_nonnegative

theorem tomographicOverlapBoundedAgreement_zero_implies_exact
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (agreement : TomographicOverlapBoundedAgreement support reading 0) :
    TomographicOverlapAgreement support reading := by
  intro left right coordinate overlap_membership
  have bounded := agreement.2 left right coordinate overlap_membership
  have absolute_zero :
      |reading left coordinate - reading right coordinate| = 0 :=
    le_antisymm bounded (abs_nonneg _)
  exact sub_eq_zero.mp (abs_eq_zero.mp absolute_zero)

theorem tomographicOverlapBoundedAgreement_mono
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    {small large : ℝ}
    (agreement : TomographicOverlapBoundedAgreement support reading small)
    (bounds : small ≤ large) :
    TomographicOverlapBoundedAgreement support reading large := by
  refine ⟨le_trans agreement.1 bounds, ?_⟩
  intro left right coordinate overlap_membership
  exact le_trans (agreement.2 left right coordinate overlap_membership) bounds

theorem tomographicOverlapBoundedAgreement_failure_witness
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (bound : ℝ)
    (bound_nonnegative : 0 ≤ bound)
    (not_agreement : ¬ TomographicOverlapBoundedAgreement support reading bound) :
    ∃ left right coordinate,
      coordinate ∈ support left ∩ support right ∧
        |reading left coordinate - reading right coordinate| > bound := by
  classical
  by_contra no_witness
  apply not_agreement
  refine ⟨bound_nonnegative, ?_⟩
  intro left right coordinate overlap_membership
  by_contra not_le
  exact no_witness ⟨left, right, coordinate, overlap_membership,
    lt_of_not_ge not_le⟩

theorem tomographicOverlapAgreement_failure_witness
    (support : View → Finset Coordinate)
    (reading : View → Coordinate → ℝ)
    (not_agreement : ¬ TomographicOverlapAgreement support reading) :
    ∃ left right coordinate,
      coordinate ∈ support left ∩ support right ∧
        reading left coordinate ≠ reading right coordinate := by
  classical
  by_contra no_witness
  apply not_agreement
  intro left right coordinate overlap_membership
  by_contra unequal
  exact no_witness ⟨left, right, coordinate, overlap_membership, unequal⟩

end OverlapConsistency

end OCKIndividuationMSpaceComposition
