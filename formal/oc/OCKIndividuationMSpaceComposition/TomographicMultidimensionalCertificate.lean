import OCKIndividuationMSpaceComposition.TomographicMultidimensionalFusion
import OCKIndividuationMSpaceComposition.TomographicFusionCertificate
import OCKIndividuationMSpaceComposition.TomographicFilteredBackprojection
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

section MultidimensionalCertificate

variable {Coordinate Modality View Ray Sample Answer : Type*}
  [Fintype Coordinate] [Fintype Modality] [Fintype View]
  [Fintype Ray] [Fintype Sample]

/-!
# Reconstruction transport for the multidimensional stack

The existing finite `TomographicFusionCertificate` is the authoritative
left-inverse contract.  This module only transports it across the exact
modality × view × ray-to-multiplicity-row equality; it does not infer a
reconstructor from coverage, energy, or the number of rays.
-/

theorem tomographicMultidimensionalRay_exact_reconstruction_of_fusion_certificate
    [DecidableEq Coordinate]
    (rayMap : Modality → View → Ray → Sample → Coordinate)
    (certificate :
      TomographicFusionCertificate (tomographicMultidimensionalRayRow rayMap))
    (state : Coordinate → ℝ) :
    certificate.reconstruct
        (tomographicMultidimensionalRayProjection rayMap state) = state := by
  rw [tomographicMultidimensionalRayProjection_eq_projection rayMap state]
  exact certificate.exact_on_model state

theorem tomographicMultidimensionalRay_target_decoder_of_fusion_certificate
    [DecidableEq Coordinate]
    (rayMap : Modality → View → Ray → Sample → Coordinate)
    (certificate :
      TomographicFusionCertificate (tomographicMultidimensionalRayRow rayMap))
    (target : (Coordinate → ℝ) → Answer) :
    ∃ decode : (Modality × (View × Ray) → ℝ) → Answer,
      ∀ state,
        decode (tomographicMultidimensionalRayProjection rayMap state) =
          target state := by
  refine ⟨fun data => target (certificate.reconstruct data), ?_⟩
  intro state
  exact congrArg target
    (tomographicMultidimensionalRay_exact_reconstruction_of_fusion_certificate
      rayMap certificate state)

theorem tomographicMultidimensionalRay_unique_reconstruction
    [DecidableEq Coordinate]
    (rayMap : Modality → View → Ray → Sample → Coordinate)
    (first second :
      (Modality × (View × Ray) → ℝ) → Coordinate → ℝ)
    (first_exact second_exact : ∀ state,
      first (tomographicMultidimensionalRayProjection rayMap state) = state ∧
      second (tomographicMultidimensionalRayProjection rayMap state) = state)
    (state : Coordinate → ℝ) :
    first (tomographicMultidimensionalRayProjection rayMap state) =
      second (tomographicMultidimensionalRayProjection rayMap state) := by
  have first_eq := (first_exact state).1
  have second_eq := (second_exact state).2
  exact first_eq.trans second_eq.symm

theorem tomographicMultidimensionalRay_exact_reconstruction_of_filtered_backprojection_certificate
    [DecidableEq Coordinate]
    (rayMap : Modality → View → Ray → Sample → Coordinate)
    (certificate :
      TomographicFilteredBackprojectionCertificate
        (tomographicMultidimensionalRayRow rayMap))
    (state : Coordinate → ℝ) :
    tomographicFilteredBackprojection
        (tomographicMultidimensionalRayRow rayMap)
        certificate.filter
        (tomographicMultidimensionalRayProjection rayMap state) = state := by
  rw [tomographicMultidimensionalRayProjection_eq_projection rayMap state]
  exact certificate.exact_reconstruction state

theorem tomographicMultidimensionalRay_target_decoder_of_filtered_backprojection_certificate
    [DecidableEq Coordinate]
    (rayMap : Modality → View → Ray → Sample → Coordinate)
    (certificate :
      TomographicFilteredBackprojectionCertificate
        (tomographicMultidimensionalRayRow rayMap))
    (target : (Coordinate → ℝ) → Answer) :
    ∃ decode : (Modality × (View × Ray) → ℝ) → Answer,
      ∀ state,
        decode (tomographicMultidimensionalRayProjection rayMap state) =
          target state := by
  refine ⟨fun data => target (tomographicFilteredBackprojection
    (tomographicMultidimensionalRayRow rayMap) certificate.filter data), ?_⟩
  intro state
  exact congrArg target
    (tomographicMultidimensionalRay_exact_reconstruction_of_filtered_backprojection_certificate
      rayMap certificate state)

end MultidimensionalCertificate

end OCKIndividuationMSpaceComposition
