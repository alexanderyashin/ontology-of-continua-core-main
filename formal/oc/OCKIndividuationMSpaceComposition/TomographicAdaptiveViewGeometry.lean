import OCKIndividuationMSpaceComposition.AdaptiveLocalOpticGeometry
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Real.Basic
open scoped BigOperators

namespace OCKIndividuationMSpaceComposition

/-!
# Tomographic adapter for existing adaptive optic geometry

The adaptive-view layer reuses the current OC local-modulus and finite-cover
contracts.  These names are only a domain adapter: no second Lipschitz or grid
theory is introduced.  A bound is available only for a declared risk modulus,
cover and catalogue minimiser; it is not a global optimum or a claim about
semantic identification.
-/

def TomographicViewRiskModulus
    {Optic : Type*} [PseudoMetricSpace Optic]
    (risk : Optic → ℝ) (modulus : Optic → ℝ) : Prop :=
  PointwiseMetricRiskModulus risk modulus

def TomographicViewGridCover
    {Optic : Type*} [PseudoMetricSpace Optic]
    (grid : Finset Optic) (targetSet : Set Optic)
    (radius : Optic → ℝ) : Prop :=
  AdaptiveMetricGridCover grid targetSet radius

theorem tomographicAdaptiveView_grid_minimizer_regret_bound
    {Optic : Type*} [PseudoMetricSpace Optic]
    (risk : Optic → ℝ)
    (grid : Finset Optic)
    (targetSet : Set Optic)
    (modulus radius : Optic → ℝ)
    (chosen : Optic)
    (regularity : TomographicViewRiskModulus risk modulus)
    (chosen_minimal : ∀ candidate, candidate ∈ grid → risk chosen ≤ risk candidate)
    (cover : TomographicViewGridCover grid targetSet radius) :
    ∀ target, target ∈ targetSet →
      risk chosen ≤ risk target + modulus target * radius target := by
  exact adaptive_local_grid_minimizer_regret_bound risk grid targetSet modulus radius
    chosen regularity chosen_minimal cover

theorem tomographicAdaptiveView_excess_refutes_declared_contract
    {Optic : Type*} [PseudoMetricSpace Optic]
    (risk : Optic → ℝ)
    (modulus radius : Optic → ℝ)
    (target chosen : Optic)
    (contract_bound : risk chosen ≤ risk target + modulus target * radius target)
    (observed_excess : risk target + modulus target * radius target < risk chosen) :
    False := by
  exact observed_local_regret_excess_refutes_adaptive_contract risk modulus radius
    target chosen contract_bound observed_excess

end OCKIndividuationMSpaceComposition