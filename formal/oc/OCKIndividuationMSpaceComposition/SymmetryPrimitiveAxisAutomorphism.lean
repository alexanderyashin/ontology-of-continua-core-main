import OCKIndividuationMSpaceComposition.SymmetryPrimitiveSwapUniqueness
import Mathlib.GroupTheory.Perm.Support

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# The automorphism algebra of a primitive axis

The generated axis of a primitive distinction has exactly two points.  This
file classifies *arbitrary* bijective self-maps of that axis; the candidate
automorphism is not given any compatibility, involution, transitivity or
group-law field.  Evaluation at one displayed endpoint separates the two
possibilities, so the full automorphism algebra is derived as a two-element
Boolean algebra.

The result is deliberately local.  The ambient carrier may contain further
points, in which case the pair-swap is not globally fixed-point-free.  Thus
this theorem derives `C₂` for the generated two-point axis, while preserving
the exact boundary against a global symmetry claim.
-/

/-- An automorphism of the generated axis sends the displayed first endpoint
to one of the two generated endpoints. -/
theorem axisAutomorphism_maps_first_cases
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (transform : Equiv.Perm distinction.Axis) :
    transform distinction.axisFirst = distinction.axisFirst ∨
      transform distinction.axisFirst = distinction.axisSecond := by
  exact distinction.axis_cases (transform distinction.axisFirst)

/-- If an axis automorphism fixes one endpoint, injectivity forces it to fix
the other endpoint as well, hence it is the identity. -/
theorem axisAutomorphism_eq_identity_of_fixed_first
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (transform : Equiv.Perm distinction.Axis)
    (fixed : transform distinction.axisFirst = distinction.axisFirst) :
    transform = Equiv.refl distinction.Axis := by
  apply Equiv.ext
  intro point
  rcases distinction.axis_cases point with pointFirst | pointSecond
  · subst point
    simpa using fixed
  · subst point
    rcases distinction.axis_cases (transform distinction.axisSecond) with
      imageFirst | imageSecond
    · have equalImages :
          transform distinction.axisSecond = transform distinction.axisFirst :=
        imageFirst.trans fixed.symm
      have impossible : distinction.axisSecond = distinction.axisFirst :=
        transform.injective equalImages
      exact (distinction.axisFirst_ne_axisSecond impossible.symm).elim
    · simpa using imageSecond

/-/ If an axis automorphism sends the first endpoint to the second, injectivity
forces the opposite endpoint exchange, hence it is the canonical swap. -/
theorem axisAutomorphism_eq_swap_of_maps_second
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (transform : Equiv.Perm distinction.Axis)
    (maps : transform distinction.axisFirst = distinction.axisSecond) :
    transform = distinction.axisSwapEquiv := by
  apply Equiv.ext
  intro point
  rcases distinction.axis_cases point with pointFirst | pointSecond
  · subst point
    change transform distinction.axisFirst = distinction.axisSwap distinction.axisFirst
    rw [distinction.axisSwap_first]
    exact maps
  · subst point
    rcases distinction.axis_cases (transform distinction.axisSecond) with
      imageFirst | imageSecond
    · simpa [axisSwapEquiv] using imageFirst
    · have equalImages :
          transform distinction.axisSecond = transform distinction.axisFirst :=
        imageSecond.trans maps.symm
      have impossible : distinction.axisSecond = distinction.axisFirst :=
        transform.injective equalImages
      exact (distinction.axisFirst_ne_axisSecond impossible.symm).elim

/-/ Every automorphism of the generated axis is exactly identity or the
canonical endpoint swap.  No R3 interface is used as a premise. -/
theorem axisAutomorphism_eq_identity_or_swap
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (transform : Equiv.Perm distinction.Axis) :
    transform = Equiv.refl distinction.Axis ∨
      transform = distinction.axisSwapEquiv := by
  rcases distinction.axisAutomorphism_maps_first_cases transform with
    fixed | swapped
  · exact Or.inl (distinction.axisAutomorphism_eq_identity_of_fixed_first
      transform fixed)
  · exact Or.inr (distinction.axisAutomorphism_eq_swap_of_maps_second
      transform swapped)

/-/ The parity of an axis automorphism is its image of the displayed base
endpoint: `false` means fixed and `true` means exchanged.  The base is only a
coordinate choice; the underlying axis and swap are already canonical. -/
noncomputable def axisAutomorphismParity
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (transform : Equiv.Perm distinction.Axis) : Bool :=
  by
    classical
    exact if transform distinction.axisFirst = distinction.axisFirst then false else true

@[simp] theorem axisAutomorphismParity_identity
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.axisAutomorphismParity (Equiv.refl distinction.Axis) = false := by
  simp [axisAutomorphismParity]

@[simp] theorem axisAutomorphismParity_swap
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    distinction.axisAutomorphismParity distinction.axisSwapEquiv = true := by
  classical
  unfold axisAutomorphismParity
  change (if distinction.axisSwap distinction.axisFirst = distinction.axisFirst
    then false else true) = true
  rw [distinction.axisSwap_first]
  simp [Ne.symm distinction.axisFirst_ne_axisSecond]

/-/ Evaluation parity is a complete equivalence between the generated-axis
automorphism type and `Bool`. -/
noncomputable def axisAutomorphismEquivBool
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier) :
    Equiv.Perm distinction.Axis ≃ Bool where
  toFun := distinction.axisAutomorphismParity
  invFun := fun parity =>
    if parity then distinction.axisSwapEquiv else Equiv.refl distinction.Axis
  left_inv := by
    intro transform
    rcases distinction.axisAutomorphism_eq_identity_or_swap transform with
      identity | swap
    · subst transform
      simp
    · subst transform
      simp
  right_inv := by
    intro parity
    cases parity <;> simp

/-/ Under the derived parity coordinate, composition of arbitrary axis
automorphisms is Boolean XOR.  This is the multiplication law of the
two-element symmetry algebra, proved after classification rather than hidden
in an interface definition. -/
theorem axisAutomorphismParity_mul
    {Carrier : Type uCarrier}
    (distinction : PrimitiveDistinction Carrier)
    (first second : Equiv.Perm distinction.Axis) :
    distinction.axisAutomorphismParity (first * second) =
      Bool.xor (distinction.axisAutomorphismParity first)
        (distinction.axisAutomorphismParity second) := by
  rcases distinction.axisAutomorphism_eq_identity_or_swap first with
    firstIdentity | firstSwap
  · subst first
    rcases distinction.axisAutomorphism_eq_identity_or_swap second with
      secondIdentity | secondSwap
    · subst second
      simp [axisAutomorphismParity]
    · subst second
      simp [axisAutomorphismParity, axisSwapEquiv]
  · subst first
    rcases distinction.axisAutomorphism_eq_identity_or_swap second with
      secondIdentity | secondSwap
    · subst second
      simp [axisAutomorphismParity, axisSwapEquiv]
    · subst second
      simp [axisAutomorphismParity, axisSwapEquiv]

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
