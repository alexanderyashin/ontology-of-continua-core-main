import OCKIndividuationMSpaceComposition.SymmetryDistinctionContinuousPath
import Mathlib.Topology.Homeomorph.Lemmas
import Mathlib.Topology.UniformSpace.Cauchy

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# The embedded interval and its exact continuum boundary

The previous layer constructs an injective continuous segment in a supplied
real topological vector space.  A Hausdorff carrier now turns that compact
injective image into an embedding, hence into a subspace homeomorphic to the
unit interval.  If the carrier topology is induced by a separated uniform
structure, compactness also makes the image complete as a subspace.

This identifies the origin of the continuum-like layer precisely: not from
the primitive distinction alone, but from the real unit interval together
with continuous scalar action and separation.  The distinction selects the
nondegenerate image; the ambient topological structure transports the interval
properties.
-/

section HausdorffRealTopologicalRealization

open Set
open scoped unitInterval

variable {V : Type uCarrier} [AddCommGroup V] [Module ℝ V]
  [TopologicalSpace V] [ContinuousAdd V] [ContinuousSMul ℝ V] [T2Space V]

/-- The straight distinction path has compact range. -/
theorem distinctionPath_range_compact
    (distinction : PrimitiveDistinction V) :
    IsCompact (Set.range distinction.distinctionPath) := by
  simpa only [Set.image_univ] using
    isCompact_univ.image distinction.distinctionPath.continuous

/-- Compactness plus Hausdorff separation makes the path range closed. -/
theorem distinctionPath_range_closed
    (distinction : PrimitiveDistinction V) :
    IsClosed (Set.range distinction.distinctionPath) :=
  distinction.distinctionPath_range_compact.isClosed

/-- The continuous injective path from the compact unit interval is a closed
embedding into every Hausdorff realization. -/
theorem distinctionPath_isClosedEmbedding
    (distinction : PrimitiveDistinction V) :
    Topology.IsClosedEmbedding distinction.distinctionPath :=
  distinction.distinctionPath.continuous.isClosedEmbedding
    distinction.distinctionPath_injective

/-- The path range is not merely connected: it is homeomorphic to the real
unit interval. -/
noncomputable def distinctionPath_homeomorphUnitInterval
    (distinction : PrimitiveDistinction V) :
    unitInterval ≃ₜ Set.range distinction.distinctionPath :=
  distinction.distinctionPath_isClosedEmbedding.isEmbedding.toHomeomorph

/-- The embedded interval is nondegenerate because its endpoints remain
distinct. -/
theorem distinctionPath_range_nontrivial
    (distinction : PrimitiveDistinction V) :
    ∃ firstPoint secondPoint : Set.range distinction.distinctionPath,
      firstPoint ≠ secondPoint := by
  let firstPoint : Set.range distinction.distinctionPath :=
    ⟨distinction.first, ⟨0, by simp [distinctionPath]⟩⟩
  let secondPoint : Set.range distinction.distinctionPath :=
    ⟨distinction.second, ⟨1, by simp [distinctionPath]⟩⟩
  refine ⟨firstPoint, secondPoint, ?_⟩
  intro equality
  apply distinction.separated
  exact congrArg Subtype.val equality

/-- Exact topological package inherited by the image of the real unit
interval.  This states the properties directly instead of defining the word
"continuum" to make them true. -/
theorem distinctionPath_range_compact_connected_nontrivial
    (distinction : PrimitiveDistinction V) :
    IsCompact (Set.range distinction.distinctionPath) ∧
      IsConnected (Set.range distinction.distinctionPath) ∧
      ∃ firstPoint secondPoint : Set.range distinction.distinctionPath,
        firstPoint ≠ secondPoint :=
  ⟨distinction.distinctionPath_range_compact,
    distinction.distinctionPath_range_connected,
    distinction.distinctionPath_range_nontrivial⟩

end HausdorffRealTopologicalRealization

section UniformRealization

open Set
open scoped unitInterval

variable {V : Type uCarrier} [AddCommGroup V] [Module ℝ V]
  [UniformSpace V] [T2Space V] [ContinuousAdd V] [ContinuousSMul ℝ V]

/-- Under a separated uniform realization, compactness makes the embedded
interval complete even without assuming the whole carrier complete. -/
theorem distinctionPath_range_complete
    (distinction : PrimitiveDistinction V) :
    IsComplete (Set.range distinction.distinctionPath) :=
  distinction.distinctionPath_range_compact.isComplete

/-- The range subtype therefore carries a complete-space instance. -/
noncomputable def distinctionPathRangeCompleteSpace
    (distinction : PrimitiveDistinction V) :
    CompleteSpace (Set.range distinction.distinctionPath) :=
  distinction.distinctionPath_range_complete.completeSpace_coe

end UniformRealization

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
