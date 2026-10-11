import Mathlib.Data.Rat.Defs
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

/-!
# Observation-resource scaling calculus

This module separates an observation-error law from the protocol that supplies
its resources.  The resulting exponent is a consequence of both components.
The DRT cubic law is the instance p = q = s = 1, r = 2.
-/

/-- Total resolution degree after closing exposure by a resolution power. -/
def closureDegree (resolutionPower exposurePower closurePower : Nat) : Nat :=
  resolutionPower + closurePower * exposurePower

/--
A monomial observation law plus an explicit resource closure yields an exact
polynomial balance.  No root operation or asymptotic notation is required.
-/
theorem monomial_resource_closure_balance
    {signal flux exposure resolution : ℚ}
    {fluxPower exposurePower resolutionPower closurePower : Nat}
    (denominatorNonzero : flux^fluxPower * exposure^exposurePower ≠ 0)
    (observationLaw :
      resolution^resolutionPower =
        signal / (flux^fluxPower * exposure^exposurePower))
    (resourceClosure : exposure = resolution^closurePower) :
    flux^fluxPower *
        resolution^(closureDegree resolutionPower exposurePower closurePower) =
      signal := by
  have multiplied :
      resolution^resolutionPower *
          (flux^fluxPower * exposure^exposurePower) = signal :=
    (eq_div_iff denominatorNonzero).mp observationLaw
  rw [resourceClosure] at multiplied
  calc
    flux^fluxPower *
        resolution^(closureDegree resolutionPower exposurePower closurePower) =
        resolution^resolutionPower *
          (flux^fluxPower * (resolution^closurePower)^exposurePower) := by
            simp only [closureDegree, pow_add, pow_mul]
            ring
    _ = signal := multiplied

/--
If exposure remains independently controlled, it remains in the invariant and
there is no justified closure-induced exponent.
-/
theorem independent_resource_balance
    {signal flux exposure resolution : ℚ}
    {fluxPower exposurePower resolutionPower : Nat}
    (denominatorNonzero : flux^fluxPower * exposure^exposurePower ≠ 0)
    (observationLaw :
      resolution^resolutionPower =
        signal / (flux^fluxPower * exposure^exposurePower)) :
    flux^fluxPower * exposure^exposurePower *
        resolution^resolutionPower = signal := by
  have multiplied :
      resolution^resolutionPower *
          (flux^fluxPower * exposure^exposurePower) = signal :=
    (eq_div_iff denominatorNonzero).mp observationLaw
  calc
    flux^fluxPower * exposure^exposurePower *
        resolution^resolutionPower =
        resolution^resolutionPower *
          (flux^fluxPower * exposure^exposurePower) := by ring
    _ = signal := multiplied

/-- Fixed model parameters preserve the resource-resolution monomial. -/
theorem closed_resource_invariant
    {flux₁ flux₂ resolution₁ resolution₂ signal : ℚ}
    {fluxPower totalDegree : Nat}
    (balance₁ : flux₁^fluxPower * resolution₁^totalDegree = signal)
    (balance₂ : flux₂^fluxPower * resolution₂^totalDegree = signal) :
    flux₁^fluxPower * resolution₁^totalDegree =
      flux₂^fluxPower * resolution₂^totalDegree :=
  balance₁.trans balance₂.symm

/--
Flux and resolution measurements identify only the combined closure degree,
not its decomposition into estimator, exposure, and protocol exponents.
-/
theorem equal_closure_degree_gives_equal_scaling_surface
    {resolutionPower₁ exposurePower₁ closurePower₁
      resolutionPower₂ exposurePower₂ closurePower₂ : Nat}
    (sameDegree :
      closureDegree resolutionPower₁ exposurePower₁ closurePower₁ =
        closureDegree resolutionPower₂ exposurePower₂ closurePower₂)
    (flux resolution : ℚ) (fluxPower : Nat) :
    flux^fluxPower *
        resolution^(closureDegree resolutionPower₁ exposurePower₁ closurePower₁) =
      flux^fluxPower *
        resolution^(closureDegree resolutionPower₂ exposurePower₂ closurePower₂) := by
  rw [sameDegree]

/--
Concrete non-identifiability: a square-error law with linear closure and a
linear-error law with quadratic closure are distinct mechanisms but both have
total degree three.
-/
theorem cubic_flux_slope_does_not_identify_mechanism :
    closureDegree 2 1 1 = closureDegree 1 1 2 ∧
      (2, 1, 1) ≠ (1, 1, 2) := by
  norm_num [closureDegree]

/--
Rate alone cannot fix resolution when exposure is independently variable:
both designs satisfy the same unit-signal law at the same unit flux.
-/
theorem flux_alone_does_not_determine_resolution :
    (1 : ℚ) * 1 * 1^2 = 1 ∧
      (1 : ℚ) * 4 * (1 / 2)^2 = 1 ∧
      (1 : ℚ) ≠ 1 / 2 := by
  norm_num

/-- Fourfold resource and halved resolution obey a square invariant. -/
theorem fourfold_resource_halves_square_resolution :
    (1 : ℚ) * 1^2 = 4 * (1 / 2)^2 := by
  norm_num

/-- Eightfold resource and halved resolution obey a cubic invariant. -/
theorem eightfold_resource_halves_cubic_resolution :
    (1 : ℚ) * 1^3 = 8 * (1 / 2)^3 := by
  norm_num

end OCKIndividuationMSpaceComposition
