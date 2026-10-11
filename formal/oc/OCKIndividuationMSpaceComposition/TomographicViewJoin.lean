import OCKIndividuationMSpaceComposition.TomographicTaskReconstruction
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

universe uWorld uView uSignature

/-!
# Tomographic view-family join

This is the explicit bridge from a family of heterogeneous projections to a
single multidimensional fused image.  It reuses the existing multi-task join
kernel: no claim is made that the fused image is a physical object, a causal
state, or a minimal representation for every task.  It is the typed common
refinement required when several projections must be kept available together.
-/

/-- A typed family of projections, one codomain per view. -/
def TomographicProjectionFamily
    (World : Type uWorld)
    (View : Type uView)
    (Signature : View → Type uSignature) : Type _ :=
  ∀ view, World → Signature view

/-- The multidimensional image obtained by retaining every registered view. -/
def tomographicViewFamilyFusedImage
    {World : Type uWorld} {View : Type uView}
    (Signature : View → Type uSignature)
    (projection : TomographicProjectionFamily World View Signature) :
    World → (∀ view, Signature view) :=
  tomographicFusedImage projection

/-- The fused image is sufficient for every projection in the family. -/
theorem tomographic_fused_image_sufficient_for_every_projection
    {World : Type uWorld} {View : Type uView}
    (Signature : View → Type uSignature)
    (projection : TomographicProjectionFamily World View Signature) :
    MultiTaskSufficient Signature projection
      (tomographicViewFamilyFusedImage Signature projection) := by
  exact multiTaskSignature_is_sufficient_for_every_task Signature projection

/-- Any observation that preserves all registered projections refines the
fused image; dropping a coordinate is therefore an explicit loss of a view. -/
theorem every_common_tomographic_observation_refines_fused_image
    {World : Type uWorld} {View : Type uView}
    (Signature : View → Type uSignature)
    (projection : TomographicProjectionFamily World View Signature)
    {Observation : Type*}
    (observe : World → Observation)
    (sufficient : MultiTaskSufficient Signature projection observe) :
    IsObservationRefinement
      (tomographicViewFamilyFusedImage Signature projection) observe := by
  exact every_common_sufficient_observation_refines_multiTaskSignature
    Signature projection observe sufficient

/-- A fused-image coordinate is definitionally the corresponding registered
projection value, so downstream task adapters can address a view by its index. -/
theorem tomographic_fused_image_recovers_projection
    {World : Type uWorld} {View : Type uView}
    (Signature : View → Type uSignature)
    (projection : TomographicProjectionFamily World View Signature)
    (view : View) (world : World) :
    tomographicViewFamilyFusedImage Signature projection world view =
      projection view world :=
  rfl

end OCKIndividuationMSpaceComposition