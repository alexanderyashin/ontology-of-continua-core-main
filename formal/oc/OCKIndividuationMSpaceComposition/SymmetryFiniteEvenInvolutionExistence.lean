import OCKIndividuationMSpaceComposition.SymmetryFiniteFreeInvolutionOrbitRank
import Mathlib.Algebra.Ring.Parity
import Mathlib.Data.Fintype.EquivFin
import Mathlib.Logic.Equiv.Fin.Basic

namespace OCKIndividuationMSpaceComposition

universe uCarrier

/-!
# The exact finite existence boundary for a free two-sided symmetry

`SymmetryFiniteFreeInvolutionOrbitRank` proves the forward implication:
a fixed-point-free involution forces an even finite carrier.  This file proves
the converse as a pure existence theorem.  If the finite carrier has cardinal
`k + k`, transport the component exchange on `Fin k ⊕ Fin k` across any finite
enumeration of the carrier.  The result is a free involution, hence a local
`C₂` action.

The construction is intentionally non-canonical: the cardinal witness and the
enumeration are choices.  Therefore the theorem closes the existence question
without claiming that a bare finite distinction selects a preferred global
axis or a preferred involution.
-/

namespace FixedPointFreeInvolution

variable {Carrier : Type uCarrier}

/-! ## The model exchange on an explicitly doubled finite type -/

private def finSwap (k : ℕ) : Fin (k + k) ≃ Fin (k + k) :=
  finSumFinEquiv.symm.trans
    ((Equiv.sumComm (Fin k) (Fin k)).trans finSumFinEquiv)

private theorem finSwap_involutive (k : ℕ) (i : Fin (k + k)) :
    finSwap k (finSwap k i) = i := by
  obtain ⟨j, rfl⟩ := finSumFinEquiv.surjective i
  cases j with
  | inl j =>
      dsimp [finSwap]
      simp only [Equiv.trans_apply, Equiv.symm_apply_apply,
        Equiv.apply_symm_apply]
      rw [Sum.swap_swap]
      exact finSumFinEquiv.apply_symm_apply _
  | inr j =>
      dsimp [finSwap]
      simp only [Equiv.trans_apply, Equiv.symm_apply_apply,
        Equiv.apply_symm_apply]
      rw [Sum.swap_swap]
      exact finSumFinEquiv.apply_symm_apply _

private theorem finSwap_fixedPointFree (k : ℕ) (i : Fin (k + k)) :
    finSwap k i ≠ i := by
  intro equality
  obtain ⟨j, rfl⟩ := finSumFinEquiv.surjective i
  cases j with
  | inl j =>
      have transformed := congrArg finSumFinEquiv.symm equality
      dsimp [finSwap] at transformed
      simp only [Equiv.trans_apply, Equiv.symm_apply_apply,
        Equiv.apply_symm_apply] at transformed
      simpa [finSumFinEquiv_symm_apply_castAdd] using transformed
  | inr j =>
      have transformed := congrArg finSumFinEquiv.symm equality
      dsimp [finSwap] at transformed
      simp only [Equiv.trans_apply, Equiv.symm_apply_apply,
        Equiv.apply_symm_apply] at transformed
      change (finSumFinEquiv.symm (Fin.natAdd k j)).swap =
        finSumFinEquiv.symm (Fin.natAdd k j) at transformed
      rw [finSumFinEquiv_symm_apply_natAdd] at transformed
      cases transformed

/-! ## Transport to an arbitrary finite carrier -/

noncomputable def evenCardInvolution [Fintype Carrier] {k : ℕ}
    (hcard : Fintype.card Carrier = k + k) :
    FixedPointFreeInvolution Carrier := by
  let enumeration : Carrier ≃ Fin (k + k) :=
    Fintype.equivFinOfCardEq hcard
  let transported : Carrier ≃ Carrier :=
    enumeration.trans ((finSwap k).trans enumeration.symm)
  refine { action := transported, involutive := ?_, fixedPointFree := ?_ }
  · intro x
    dsimp [transported]
    simp only [Equiv.trans_apply, Equiv.apply_symm_apply]
    rw [finSwap_involutive]
    exact enumeration.symm_apply_apply x
  · intro x equality
    apply finSwap_fixedPointFree k (enumeration x)
    have mapped := congrArg enumeration equality
    simpa [transported] using mapped

theorem exists_fixedPointFreeInvolution_of_even_card
    [Fintype Carrier] (even : Even (Fintype.card Carrier)) :
    Nonempty (FixedPointFreeInvolution Carrier) := by
  rcases even with ⟨k, hcard⟩
  exact ⟨evenCardInvolution hcard⟩

/-! ## Exact equivalence, with non-canonicity kept explicit -/

theorem even_card_iff_nonempty_fixedPointFreeInvolution
    [Fintype Carrier] :
    Even (Fintype.card Carrier) ↔
      Nonempty (FixedPointFreeInvolution Carrier) := by
  constructor
  · exact exists_fixedPointFreeInvolution_of_even_card
  · intro existence
    classical
    rcases existence with ⟨symmetry⟩
    exact even_carrier_card symmetry

end FixedPointFreeInvolution

end OCKIndividuationMSpaceComposition
