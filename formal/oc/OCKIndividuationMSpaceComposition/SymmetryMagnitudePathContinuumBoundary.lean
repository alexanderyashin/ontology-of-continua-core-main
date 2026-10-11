import OCKIndividuationMSpaceComposition.SymmetryMagnitudeBetweennessBoundary
import OCKIndividuationMSpaceComposition.SymmetryDistinctionEmbeddedInterval

namespace OCKIndividuationMSpaceComposition

universe uCarrier uScalar

namespace PrimitiveDistinction

/-!
# The path and continuum boundary of a bounded distinction model

The finite magnitude/betweenness slices establish only local quantitative and
strictness facts.  This module makes the next boundary explicit.  A density
law is an additional relation-level premise; it is not forced by a symmetric
Nat magnitude, and it is not supplied by the existence of a third point.

The `Fin 3` models are concrete finite countermodels: they satisfy the
bounded magnitude and minimal strictness interfaces, while even a witnessed
middle fails the density law.  Thus these interfaces do not by themselves
produce a path, an order, a topology, completeness, or a continuum.

The positive results below keep their extra structure visible.  A linearly
ordered field supplies algebraic midpoint density.  A real topological-vector
space supplies a straight path, and a Hausdorff realization upgrades its
injective range to a copy of the real unit interval.  These are sufficient
realization results, not consequences of bare OC distinction.
-/

/-! ## Density is a separate relation-level premise -/

/-/ A relation is dense between every distinct pair, with orientation left
    free.  No order, transitivity, topology, or completeness is included. -/
def StrictBetweenDensityLaw {Point : Type uCarrier}
    (Between : Point → Point → Point → Prop) : Prop :=
  ∀ {left right}, left ≠ right → ∃ middle, Between left middle right

/-! ## Finite/discrete countermodels -/

theorem finThree_finite_carrier : Finite (Fin 3) := by
  infer_instance

theorem finThreeEmptyBetween_not_dense :
    ¬ StrictBetweenDensityLaw finThreeEmptyBetween := by
  intro dense
  obtain ⟨middle, between⟩ :=
    dense (left := (0 : Fin 3)) (right := (2 : Fin 3)) (by decide)
  change False at between
  exact between.elim

theorem finThreeWitnessedBetween_not_dense :
    ¬ StrictBetweenDensityLaw finThreeWitnessedBetween := by
  intro dense
  obtain ⟨middle, between⟩ :=
    dense (left := (0 : Fin 3)) (right := (1 : Fin 3)) (by decide)
  change (0 : Fin 3) = 0 ∧ middle = 1 ∧ (1 : Fin 3) = 2 at between
  exact (by decide : (1 : Fin 3) ≠ 2) between.2.2

/-/ Both concrete finite models retain their bounded quantitative and
    strictness evidence while failing density.  This is a countermodel to the
    implication "magnitude + minimal betweenness ⇒ path/continuum". -/
theorem finThree_bounded_models_are_not_dense :
    Finite (Fin 3) ∧
      NatMagnitudeStrictBetweenModel finThreeDiscreteMagnitude
        finThreeEmptyBetween ∧
      NatMagnitudeStrictBetweenModel finThreeDiscreteMagnitude
        finThreeWitnessedBetween ∧
      ¬ StrictBetweenDensityLaw finThreeEmptyBetween ∧
      ¬ StrictBetweenDensityLaw finThreeWitnessedBetween := by
  exact ⟨finThree_finite_carrier,
    finThreeDiscreteMagnitude_empty_model,
    finThreeDiscreteMagnitude_witnessed_model,
    finThreeEmptyBetween_not_dense,
    finThreeWitnessedBetween_not_dense⟩

/-! ## An ordered-field sufficient condition for density -/

section OrderedFieldDensity

variable {K : Type uScalar}
  [Field K] [LinearOrder K] [IsStrictOrderedRing K]

/-/ A linearly ordered field supplies an intermediate parameter for every
    distinct pair by choosing the algebraic midpoint.  Completeness and a
    topology are intentionally absent from this theorem. -/
theorem orderedField_parameter_density {left right : K}
    (different : left ≠ right) :
    ∃ middle, StrictParameterBetween left middle right := by
  by_cases ordered : left < right
  · exact ⟨interpolateParameter left right,
      Or.inl (interpolateParameter_strictBetween ordered)⟩
  · have reverse : right < left :=
      lt_of_le_of_ne (le_of_not_gt ordered) (Ne.symm different)
    exact ⟨interpolateParameter right left,
      Or.inr (interpolateParameter_strictBetween reverse)⟩

end OrderedFieldDensity

/-! ## Explicit sufficient premises for a real path / interval realization -/

section RealPathSufficiency

open Set
open scoped unitInterval

variable {V : Type uCarrier} [AddCommGroup V] [Module ℝ V]
  [TopologicalSpace V] [ContinuousAdd V] [ContinuousSMul ℝ V]

/-/ A supplied real topological-vector-space realization is sufficient for a
    genuine injective path with connected range.  The conclusion reuses the
    existing straight-segment construction; no topology is inferred from the
    distinction. -/
theorem real_topological_realization_suffices_for_path
    (distinction : PrimitiveDistinction V) :
    ∃ path : Path distinction.first distinction.second,
      Function.Injective path ∧ IsConnected (Set.range path) := by
  refine ⟨distinction.distinctionPath, ?_ , ?_⟩
  · exact distinction.distinctionPath_injective
  · exact distinction.distinctionPath_range_connected

variable [T2Space V]

/-/ Adding Hausdorff separation is sufficient to identify the path range with
    the real unit interval.  This is an explicit realization bridge, not a
    definition of "continuum" and not a theorem about arbitrary OC carriers. -/
theorem real_T2_realization_suffices_for_interval_copy
    (distinction : PrimitiveDistinction V) :
    Nonempty (unitInterval ≃ₜ Set.range distinction.distinctionPath) :=
  ⟨distinction.distinctionPath_homeomorphUnitInterval⟩

end RealPathSufficiency

section CompleteRealPathSufficiency

open Set

variable {V : Type uCarrier} [AddCommGroup V] [Module ℝ V]
  [UniformSpace V] [T2Space V] [ContinuousAdd V] [ContinuousSMul ℝ V]

/-/ A separated uniform realization is additionally sufficient for completeness
    of the embedded range; completeness is an extra premise/result layer and
    is not supplied by the finite countermodel interfaces. -/
theorem separated_uniform_realization_suffices_for_complete_range
    (distinction : PrimitiveDistinction V) :
    IsComplete (Set.range distinction.distinctionPath) :=
  distinction.distinctionPath_range_complete

end CompleteRealPathSufficiency

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
