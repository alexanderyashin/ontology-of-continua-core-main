import OCKIndividuationMSpaceComposition.DynamicQuotientDefectBound

namespace OCKIndividuationMSpaceComposition

/-!
# Structural quotient defect → transition perturbation → horizon error

`DynamicQuotientDefectBound` is a valid transition-perturbation theorem.  It
does not, by itself, define an observation-fibre defect.  This module supplies
the missing typed bridge for a scalar observable: a declared observation map,
a representative section of its reachable values, and a reference abstract
update induce an observed transition.  A structural fibre-residual bound then
implies the `UniformTransitionDefect` premise, after which the existing
geometric horizon envelope applies.

The section/surjectivity premise is explicit.  Without it the bridge is only
defined on the reachable observation range, exactly as required by the empty
world boundary.
-/

/-- Operational structural quotient residual for a scalar observation. -/
def StructuralQuotientTransitionDefect
    {World : Type*}
    (observe : World → ℚ)
    (next : World → World)
    (reference : ℚ → ℚ)
    (defect : ℚ) : Prop :=
  ∀ world, |observe (next world) - reference (observe world)| ≤ defect

/-- Observed transition induced by a declared representative section. -/
def sectionInducedObservedTransition
    {World : Type*}
    (observe : World → ℚ)
    (next : World → World)
    (representative : ℚ → World) : ℚ → ℚ :=
  fun coordinate => observe (next (representative coordinate))

/-- A section turns the structural quotient residual into the uniform
transition perturbation premise used by the horizon theorem. -/
theorem structuralQuotientDefect_implies_uniformTransitionDefect
    {World : Type*}
    (observe : World → ℚ)
    (next : World → World)
    (reference : ℚ → ℚ)
    (representative : ℚ → World)
    (sectionLaw : ∀ coordinate,
      observe (representative coordinate) = coordinate)
    (defect : ℚ)
    (structural : StructuralQuotientTransitionDefect observe next reference defect) :
    UniformTransitionDefect reference
      (sectionInducedObservedTransition observe next representative) defect := by
  intro coordinate
  simpa [sectionInducedObservedTransition, sectionLaw coordinate] using
    structural (representative coordinate)

/-- Structural quotient residuals therefore receive the finite-horizon
geometric forecast envelope, under the same explicit contraction premise. -/
theorem structuralQuotientDefect_horizon_error_bound
    {World : Type*}
    (observe : World → ℚ)
    (next : World → World)
    (reference : ℚ → ℚ)
    (representative : ℚ → World)
    (sectionLaw : ∀ coordinate,
      observe (representative coordinate) = coordinate)
    (rho defect : ℚ)
    (rhoNonnegative : 0 ≤ rho)
    (contractive : IsContraction rho reference)
    (structural : StructuralQuotientTransitionDefect observe next reference defect)
    (horizon : ℕ)
    (initial : ℚ) :
    |iterateState (sectionInducedObservedTransition observe next representative)
        horizon initial - iterateState reference horizon initial| ≤
      robustErrorEnvelope rho defect 0 horizon := by
  exact approximate_transition_error_bound reference
    (sectionInducedObservedTransition observe next representative) rho defect
    rhoNonnegative contractive
    (structuralQuotientDefect_implies_uniformTransitionDefect observe next reference
      representative sectionLaw defect structural)
    horizon initial

end OCKIndividuationMSpaceComposition
