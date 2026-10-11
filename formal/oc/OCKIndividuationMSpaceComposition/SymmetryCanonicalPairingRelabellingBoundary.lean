import OCKIndividuationMSpaceComposition.SymmetryFoundationsCore
import Mathlib.Logic.Equiv.Basic

namespace OCKIndividuationMSpaceComposition

universe uCarrier

/-!
# The canonicality boundary for a global pairing

An even finite carrier admits some fixed-point-free involution (M42), but that
existence proof transports a chosen pairing across a chosen enumeration.  It
does not provide a relabelling-independent choice.  This module isolates the
missing premise precisely.

`RelabellingInvariant` says that a selected action is unchanged by conjugation
with every carrier equivalence.  If the action has a third point outside the
orbit of one endpoint, swapping that third point with the endpoint's partner
changes the conjugate action at the endpoint.  Therefore no selected action
can satisfy this strongest label-independence condition.

The theorem is a boundary result, not a claim that no global free involution
can be supplied.  A model may still choose one by extra structure (an order,
enumeration, pairing, or naturality datum); the extra structure is exactly the
part not supplied by a bare distinction or by cardinal parity.
-/

namespace FixedPointFreeInvolution

variable {Carrier : Type uCarrier}

/-- A chosen action is fixed under conjugation by every carrier relabelling. -/
def RelabellingInvariant (symmetry : FixedPointFreeInvolution Carrier) : Prop :=
  ∀ relabel : Carrier ≃ Carrier,
    relabel.trans (symmetry.action.trans relabel.symm) = symmetry.action

/-- A point `z` witnesses that the orbit of `x` does not cover the carrier. -/
def HasThirdPoint (symmetry : FixedPointFreeInvolution Carrier) : Prop :=
  ∃ x z : Carrier, z ≠ x ∧ z ≠ symmetry.action x

theorem no_relabelling_invariant_of_third_point
    (symmetry : FixedPointFreeInvolution Carrier)
    (third : HasThirdPoint symmetry) :
    ¬ RelabellingInvariant symmetry := by
  rintro invariant
  classical
  rcases third with ⟨x, z, z_ne_x, z_ne_partner⟩
  let relabel : Carrier ≃ Carrier := Equiv.swap (symmetry.action x) z
  have invariantAt :=
    congrArg (fun map : Carrier ≃ Carrier => map x) (invariant relabel)
  change (relabel.trans (symmetry.action.trans relabel.symm)) x =
    symmetry.action x at invariantAt
  have x_ne_partner : x ≠ symmetry.action x :=
    Ne.symm (symmetry.fixedPointFree x)
  have x_ne_z : x ≠ z := Ne.symm z_ne_x
  have conjugate_value :
      (relabel.trans (symmetry.action.trans relabel.symm)) x = z := by
    simp [relabel, Equiv.trans_apply, Equiv.swap_apply_left,
      Equiv.swap_apply_of_ne_of_ne x_ne_partner x_ne_z]
  rw [conjugate_value] at invariantAt
  exact z_ne_partner invariantAt

end FixedPointFreeInvolution

end OCKIndividuationMSpaceComposition
