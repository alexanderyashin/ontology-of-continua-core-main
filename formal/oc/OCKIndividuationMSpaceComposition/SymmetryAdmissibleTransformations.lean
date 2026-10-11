import OCKIndividuationMSpaceComposition.SymmetryLayerSynthesis

namespace OCKIndividuationMSpaceComposition

universe uOrientation uAxis uIdentity uObservable

/-!
# Admissible transformations of the R3 C₂ torsor

An internal transformation is admissible when it commutes with the primitive
reversal.  Pair transitivity makes this condition rigid: every admissible
endomorphism is either the identity or reversal everywhere.  Thus the
admissible transformation monoid is already the two-element symmetry group.

Both transformations act trivially on the orbit quotient, while no
orientation is fixed by all admissible transformations.  Observables invariant
under every admissible transformation are exactly the globally constant ones.
-/

/-- An R3 carrier transformation is admissible when it commutes with the
primitive reversal. -/
def R3AdmissibleTransformation
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (transform : Orientation → Orientation) : Prop :=
  ∀ orientation,
    transform (candidate.reverse orientation) =
      candidate.reverse (transform orientation)

/-- Identity is admissible. -/
theorem r3_identity_admissible
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity) :
    R3AdmissibleTransformation candidate id := by
  intro orientation
  rfl

/-- Reversal itself is admissible. -/
theorem r3_reversal_admissible
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity) :
    R3AdmissibleTransformation candidate candidate.reverse := by
  intro orientation
  rfl

/-- Every admissible transformation is globally identity or globally
reversal. -/
theorem r3_admissible_transformation_classification
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base : Orientation) (transform : Orientation → Orientation)
    (admissible : R3AdmissibleTransformation candidate transform) :
    (∀ orientation, transform orientation = orientation) ∨
      (∀ orientation,
        transform orientation = candidate.reverse orientation) := by
  rcases candidate.pairTransitive base (transform base) with fixed | reversed
  · left
    intro orientation
    rcases candidate.pairTransitive base orientation with same | partner
    · subst orientation
      exact fixed
    · subst orientation
      calc
        transform (candidate.reverse base) =
            candidate.reverse (transform base) := admissible base
        _ = candidate.reverse base := congrArg candidate.reverse fixed
  · right
    intro orientation
    rcases candidate.pairTransitive base orientation with same | partner
    · subst orientation
      exact reversed
    · subst orientation
      calc
        transform (candidate.reverse base) =
            candidate.reverse (transform base) := admissible base
        _ = candidate.reverse (candidate.reverse base) :=
          congrArg candidate.reverse reversed

/-- The two classified transformations are genuinely different. -/
theorem r3_identity_ne_reversal
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base : Orientation) :
    ¬ (∀ orientation, id orientation = candidate.reverse orientation) := by
  intro equality
  exact candidate.reverseFree base (equality base).symm

/-- Every admissible transformation is injective. -/
theorem r3_admissible_transformation_injective
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base : Orientation) (transform : Orientation → Orientation)
    (admissible : R3AdmissibleTransformation candidate transform) :
    Function.Injective transform := by
  rcases r3_admissible_transformation_classification candidate base transform
      admissible with fixed | reversed
  · intro left right equality
    simpa [fixed left, fixed right] using equality
  · intro left right equality
    have reversedEquality :
        candidate.reverse left = candidate.reverse right := by
      simpa [reversed left, reversed right] using equality
    have restored := congrArg candidate.reverse reversedEquality
    simpa [candidate.reverseInvolutive] using restored

/-- Every admissible transformation is surjective. -/
theorem r3_admissible_transformation_surjective
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base : Orientation) (transform : Orientation → Orientation)
    (admissible : R3AdmissibleTransformation candidate transform) :
    Function.Surjective transform := by
  rcases r3_admissible_transformation_classification candidate base transform
      admissible with fixed | reversed
  · intro orientation
    exact ⟨orientation, fixed orientation⟩
  · intro orientation
    refine ⟨candidate.reverse orientation, ?_⟩
    rw [reversed, candidate.reverseInvolutive]

/-- Every admissible transformation acts trivially on the invariant orbit
quotient. -/
theorem r3_admissible_transformation_preserves_boundary
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base : Orientation) (transform : Orientation → Orientation)
    (admissible : R3AdmissibleTransformation candidate transform)
    (orientation : Orientation) :
    axisClass (r3FixedPointFreeInvolution candidate)
        (transform orientation) =
      axisClass (r3FixedPointFreeInvolution candidate) orientation := by
  rcases r3_admissible_transformation_classification candidate base transform
      admissible with fixed | reversed
  · rw [fixed]
  · rw [reversed]
    exact action_preserves_axis_class
      (r3FixedPointFreeInvolution candidate) orientation

/-- There is no orientation which is fixed by every admissible
transformation; an equivariantly canonical sign choice is impossible. -/
theorem r3_no_orientation_fixed_by_all_admissible_transformations
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity) :
    ¬ ∃ orientation, ∀ transform,
      R3AdmissibleTransformation candidate transform →
        transform orientation = orientation := by
  rintro ⟨orientation, universal⟩
  exact candidate.reverseFree orientation
    (universal candidate.reverse (r3_reversal_admissible candidate))

/-- An observable is invariant under every admissible transformation exactly
when it is globally constant on the R3 torsor. -/
theorem r3_all_admissible_invariant_iff_constant
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity} {Observable : Type uObservable}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (observable : Orientation → Observable) :
    (∀ transform, R3AdmissibleTransformation candidate transform →
        ∀ orientation, observable (transform orientation) = observable orientation) ↔
      ∀ left right, observable left = observable right := by
  constructor
  · intro invariant left right
    rcases candidate.pairTransitive left right with same | reversed
    · subst right
      rfl
    · subst right
      exact (invariant candidate.reverse
        (r3_reversal_admissible candidate) left).symm
  · intro constant transform _ orientation
    exact constant (transform orientation) orientation

end OCKIndividuationMSpaceComposition
