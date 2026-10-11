import OCKIndividuationMSpaceComposition.MultiTaskOpticJoin
import OCKIndividuationMSpaceComposition.SymmetryGluingV2
import Mathlib.Tactic.Linarith
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Task-relative reconstruction from heterogeneous projections

Static candidate, not yet elaborated. Reuses the existing joint signature and
Cech presentation. All views concern ONE declared World, coordinate registration
and observation cut. These premises do not follow from similarity of records.
-/

section JointTask

variable {World View Answer : Type*} {Reading : View → Type*}

/-- A target is constant on every fibre of the full joint observation. -/
def TomographicTaskIdentifiable
    (project : ∀ view, World → Reading view) (target : World → Answer) : Prop :=
  ∀ x z, MultiTaskSignature Reading project x =
    MultiTaskSignature Reading project z → target x = target z

/-- A decoder exists exactly when the target is constant on observation fibres.
The nonempty output type permits arbitrary values OUTSIDE the observation image;
the theorem makes no claim about those values. Choice is not a reconstruction
algorithm or a complexity guarantee. -/
theorem tomographic_task_decoder_iff [Nonempty Answer]
    (project : ∀ view, World → Reading view) (target : World → Answer) :
    (∃ decode : (∀ view, Reading view) → Answer,
      ∀ x, decode (MultiTaskSignature Reading project x) = target x) ↔
      TomographicTaskIdentifiable project target := by
  classical
  constructor
  · rintro ⟨decode, correct⟩ x z same
    rw [← correct x, ← correct z, same]
  · intro identifiable
    let decode : (∀ view, Reading view) → Answer := fun data =>
      if h : ∃ x, MultiTaskSignature Reading project x = data then
        target (Classical.choose h)
      else Classical.choice (inferInstance : Nonempty Answer)
    refine ⟨decode, ?_⟩
    intro x
    have hx : ∃ z, MultiTaskSignature Reading project z =
        MultiTaskSignature Reading project x := ⟨x, rfl⟩
    dsimp [decode]
    rw [dif_pos hx]
    exact identifiable _ x (Classical.choose_spec hx)

/-- An observed collision for this task cannot be cured by postprocessing. -/
theorem tomographic_task_collision_blocks_postprocessing
    (project : ∀ view, World → Reading view) (target : World → Answer)
    (x z : World)
    (same : ∀ view, project view x = project view z)
    (different : target x ≠ target z) :
    ¬ ∃ decode : (∀ view, Reading view) → Answer,
      ∀ w, decode (MultiTaskSignature Reading project w) = target w := by
  rintro ⟨decode, correct⟩
  apply different
  have joint : MultiTaskSignature Reading project x =
      MultiTaskSignature Reading project z := funext same
  rw [← correct x, ← correct z, joint]

/-- A jointly injective observation recovers every target; the converse is not
required for a particular target. -/
theorem jointly_injective_projections_identify_task
    (project : ∀ view, World → Reading view) (target : World → Answer)
    (separates : Function.Injective (MultiTaskSignature Reading project)) :
    TomographicTaskIdentifiable project target := by
  intro x z same
  exact congrArg target (separates same)

end JointTask

section Fusion

variable {World View Answer : Type*} {Reading : View → Type*}

/-! A view family separates worlds when some registered projection detects every
non-identical pair.  This is a view-level condition, not an inferred semantic
identity claim. -/
def TomographicViewSeparation
    (project : ∀ view, World → Reading view) : Prop :=
  ∀ ⦃left right : World⦄, left ≠ right →
    ∃ view, project view left ≠ project view right

/-! The fused image is exactly the existing heterogeneous joint signature. -/
def tomographicFusedImage
    (project : ∀ view, World → Reading view) :
    World → (∀ view, Reading view) :=
  MultiTaskSignature Reading project

@[simp] theorem tomographic_fused_image_coordinate
    (project : ∀ view, World → Reading view) (world : World) (view : View) :
    tomographicFusedImage project world view = project view world := rfl

theorem tomographic_fused_image_eq_iff
    (project : ∀ view, World → Reading view) (left right : World) :
    tomographicFusedImage project left = tomographicFusedImage project right ↔
      ∀ view, project view left = project view right := by
  constructor
  · intro same view
    exact congrFun same view
  · intro same
    funext view
    exact same view

theorem tomographic_fused_image_injective_of_view_separation
    (project : ∀ view, World → Reading view)
    (separation : TomographicViewSeparation project) :
    Function.Injective (tomographicFusedImage project) := by
  intro left right same
  by_cases equal : left = right
  · exact equal
  · obtain ⟨view, witness⟩ := separation equal
    exact False.elim (witness (congrFun same view))

theorem tomographic_fused_image_injective_iff_view_separation
    (project : ∀ view, World → Reading view) :
    Function.Injective (tomographicFusedImage project) ↔
      TomographicViewSeparation project := by
  constructor
  · intro injective left right different
    by_contra no_separating_view
    apply different
    apply injective
    apply (tomographic_fused_image_eq_iff project left right).2
    intro view
    by_contra unequal
    exact no_separating_view ⟨view, unequal⟩
  · exact tomographic_fused_image_injective_of_view_separation project

theorem tomographic_fused_image_identifies_task_of_view_separation
    (project : ∀ view, World → Reading view) (target : World → Answer)
    (separation : TomographicViewSeparation project) :
    TomographicTaskIdentifiable project target := by
  apply jointly_injective_projections_identify_task project target
  simpa [tomographicFusedImage] using
    (tomographic_fused_image_injective_of_view_separation project separation)

end Fusion

section Descent

variable {Patch : Type*} [Fintype Patch] {cover : FiniteCechCover Patch}

/-- The existing descent/separation contracts give actual unique global
realization, not merely pairwise agreement of local readings. -/
theorem tomographic_cech_unique_reconstruction
    (presentation : FiniteCechGlobalPresentation cover)
    (descent : FiniteCechDescent presentation)
    (separated : FiniteCechSeparated presentation)
    (data : FiniteCechMatchingFamily cover) :
    ∃! world, finiteCechRestrictGlobal presentation world = data := by
  obtain ⟨world, realizes⟩ := descent data
  refine ⟨world, realizes, ?_⟩
  intro other otherRealizes
  exact separated (otherRealizes.trans realizes.symm)

/-- A violated overlap equation rules out every realization in this model.
It does not by itself locate the faulty sensor, timestamp, model or registration. -/
theorem tomographic_overlap_conflict_no_realization
    (presentation : FiniteCechGlobalPresentation cover)
    (data : ∀ patch, cover.LocalState patch)
    (conflict : ¬ cover.IsMatching data) :
    ¬ ∃ world, ∀ patch, presentation.restrict patch world = data patch := by
  rintro ⟨world, realizes⟩
  apply conflict
  have same : (fun patch => presentation.restrict patch world) = data :=
    funext realizes
  rw [← same]
  exact presentation.restrictions_match world

end Descent

/-! ## Small discrete tomography: margins do not identify interaction

Two nonnegative 2x2 images have identical row/column projections but different
internal structure. One diagonal projection removes this particular ambiguity.
This is NOT a theorem that one extra view always reconstructs an enterprise.
-/

abbrev TomographicImage2 := Bool → Bool → ℝ

def tomographicMargins2 (x : TomographicImage2) : (ℝ × ℝ) × (ℝ × ℝ) :=
  ((x false false + x false true, x true false + x true true),
   (x false false + x true false, x false true + x true true))

def tomographicDiagonal2 (x : TomographicImage2) : ℝ :=
  x false false + x true true

def tomographicUniform2 : TomographicImage2 := fun _ _ => 1
def tomographicChecker2 : TomographicImage2 := fun i j => if i = j then 2 else 0

theorem tomographic_nonnegative_margin_collision :
    (∀ i j, 0 ≤ tomographicUniform2 i j) ∧
    (∀ i j, 0 ≤ tomographicChecker2 i j) ∧
    tomographicMargins2 tomographicUniform2 =
      tomographicMargins2 tomographicChecker2 ∧
    tomographicUniform2 ≠ tomographicChecker2 := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · intro i j
    norm_num [tomographicUniform2]
  · intro i j
    by_cases h : i = j <;> simp [tomographicChecker2, h]
  · norm_num [tomographicMargins2, tomographicUniform2, tomographicChecker2]
  · intro same
    have corner := congrFun (congrFun same false) false
    norm_num [tomographicUniform2, tomographicChecker2] at corner

/-- Additional projection geometry, rather than another copy of the margins,
identifies all four coordinates in this small example. -/
theorem tomographic_margins_and_diagonal_injective :
    Function.Injective (fun x : TomographicImage2 =>
      (tomographicMargins2 x, tomographicDiagonal2 x)) := by
  intro x z same
  have rows0 := congrArg (fun data => data.1.1.1) same
  have rows1 := congrArg (fun data => data.1.1.2) same
  have cols0 := congrArg (fun data => data.1.2.1) same
  have diagonal := congrArg Prod.snd same
  change x false false + x false true = z false false + z false true at rows0
  change x true false + x true true = z true false + z true true at rows1
  change x false false + x true false = z false false + z true false at cols0
  change x false false + x true true = z false false + z true true at diagonal
  funext i j
  cases i <;> cases j <;> linarith

end OCKIndividuationMSpaceComposition