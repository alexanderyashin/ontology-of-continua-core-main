import OCKIndividuationMSpaceComposition.SymmetryAxisCoaxis
import OCKIndividuationMSpaceComposition.SymmetryInvariantQuotient

namespace OCKIndividuationMSpaceComposition

universe u

/-!
# The coaxis as the sign representation of C₂

On a generated two-point axis the canonical swap is itself a free
involution.  A sign pairing is an equivariant map from that axis to `Bool`,
where the non-trivial group element acts by Boolean negation.  This is a
precise local realization of the covector/coaxis intuition which needs no
metric and no global choice of orientation.

Such pairings exist after choosing one endpoint, are determined by the sign
at that endpoint, and any two differ by at most simultaneous sign reversal.
Because the pairing is odd rather than invariant, it cannot factor through
the orbit quotient.
-/

/-- The canonical swap, packaged as a fixed-point-free involution on one
generated axis. -/
def axisSwapInvolution {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    FixedPointFreeInvolution (axis symmetry x) where
  action := axisSwap symmetry x
  involutive := axisSwap_involutive symmetry x
  fixedPointFree := axisSwap_fixedPointFree symmetry x

/-- A Boolean sign which transforms by the non-trivial character of C₂. -/
structure AxisSignPairing {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) where
  sign : axis symmetry x → Bool
  equivariant : ∀ y,
    sign (axisSwap symmetry x y) = Bool.not (sign y)

/-- Choosing the seed as `false` and its partner as `true` gives a sign
pairing. -/
noncomputable def baseAxisSignPairing {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    AxisSignPairing symmetry x := by
  classical
  refine
    { sign := fun y => if y.1 = x then false else true
      equivariant := ?_ }
  intro y
  rcases y with ⟨y, membership⟩
  change (if symmetry.action y = x then false else true) =
    Bool.not (if y = x then false else true)
  rcases membership with same | partner
  · subst y
    simp [symmetry.fixedPointFree x]
  · subst y
    simp [symmetry.involutive x, symmetry.fixedPointFree x]

@[simp] theorem baseAxisSignPairing_seed
    {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    (baseAxisSignPairing symmetry x).sign
      ⟨x, axis_mem_left symmetry x⟩ = false := by
  simp [baseAxisSignPairing]

@[simp] theorem baseAxisSignPairing_partner
    {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    (baseAxisSignPairing symmetry x).sign
      ⟨symmetry.action x, axis_mem_right symmetry x⟩ = true := by
  simp [baseAxisSignPairing, symmetry.fixedPointFree x]

/-- Simultaneous Boolean negation reverses a sign pairing. -/
def reverseAxisSignPairing {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (pairing : AxisSignPairing symmetry x) : AxisSignPairing symmetry x where
  sign := fun y => Bool.not (pairing.sign y)
  equivariant := by
    intro y
    rw [pairing.equivariant]

/-- An equivariant sign pairing is determined by its value at the seed. -/
theorem axisSignPairing_determined_by_seed
    {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (first second : AxisSignPairing symmetry x)
    (seedAgreement :
      first.sign ⟨x, axis_mem_left symmetry x⟩ =
        second.sign ⟨x, axis_mem_left symmetry x⟩) :
    ∀ y, first.sign y = second.sign y := by
  intro y
  rcases y with ⟨y, membership⟩
  rcases membership with same | partner
  · subst y
    exact seedAgreement
  · subst y
    let seed : axis symmetry x := ⟨x, axis_mem_left symmetry x⟩
    have swapped :
        axisSwap symmetry x seed =
          (⟨symmetry.action x, axis_mem_right symmetry x⟩ :
            axis symmetry x) :=
      axisSwap_exchanges_endpoints_left symmetry x
    calc
      first.sign ⟨symmetry.action x, axis_mem_right symmetry x⟩ =
          first.sign (axisSwap symmetry x seed) :=
        congrArg first.sign swapped.symm
      _ = Bool.not (first.sign seed) := first.equivariant seed
      _ = Bool.not (second.sign seed) := congrArg Bool.not seedAgreement
      _ = second.sign (axisSwap symmetry x seed) :=
        (second.equivariant seed).symm
      _ = second.sign
          ⟨symmetry.action x, axis_mem_right symmetry x⟩ :=
        congrArg second.sign swapped

/-- Any two local sign pairings are equal pointwise or differ pointwise by
global sign reversal. -/
theorem axisSignPairing_equal_or_reversed
    {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (first second : AxisSignPairing symmetry x) :
    (∀ y, second.sign y = first.sign y) ∨
      (∀ y, second.sign y = Bool.not (first.sign y)) := by
  let seed : axis symmetry x := ⟨x, axis_mem_left symmetry x⟩
  by_cases sameSeed : second.sign seed = first.sign seed
  · left
    exact axisSignPairing_determined_by_seed second first sameSeed
  · right
    have reversedSeed :
        second.sign seed = (reverseAxisSignPairing first).sign seed := by
      change second.sign seed = Bool.not (first.sign seed)
      cases firstValue : first.sign seed <;>
          cases secondValue : second.sign seed
      · exfalso
        apply sameSeed
        rw [secondValue, firstValue]
      · rfl
      · rfl
      · exfalso
        apply sameSeed
        rw [secondValue, firstValue]
    intro y
    exact axisSignPairing_determined_by_seed second
      (reverseAxisSignPairing first) reversedSeed y

/-- The sign representation distinguishes every point from its swapped
partner. -/
theorem axisSignPairing_breaks_everywhere
    {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (pairing : AxisSignPairing symmetry x) (y : axis symmetry x) :
    SymmetryBreakingWitness (axisSwapInvolution symmetry x) pairing.sign y := by
  change pairing.sign (axisSwap symmetry x y) ≠ pairing.sign y
  rw [pairing.equivariant]
  cases pairing.sign y <;> decide

/-- Consequently an odd sign pairing cannot factor through the invariant
orbit quotient of the axis swap. -/
theorem axisSignPairing_forbids_quotient_factor
    {Carrier : Type u}
    {symmetry : FixedPointFreeInvolution Carrier} {x : Carrier}
    (pairing : AxisSignPairing symmetry x) (y : axis symmetry x) :
    ¬ ∃ factor : AxisQuotient (axisSwapInvolution symmetry x) → Bool,
        ∀ point,
          factor (axisClass (axisSwapInvolution symmetry x) point) =
            pairing.sign point :=
  symmetry_breaking_forbids_axis_quotient_factor
    (axisSwapInvolution symmetry x) pairing.sign y
      (axisSignPairing_breaks_everywhere pairing y)

end OCKIndividuationMSpaceComposition
