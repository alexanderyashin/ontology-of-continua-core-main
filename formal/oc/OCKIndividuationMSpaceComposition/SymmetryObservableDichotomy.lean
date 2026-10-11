import OCKIndividuationMSpaceComposition.SymmetryAutomorphismParity

namespace OCKIndividuationMSpaceComposition

universe uOrientation uAxis uIdentity uObservable

/-!
# Observable dichotomy on the R3 torsor

An arbitrary observable on a two-orientation torsor has at most two values.
There is no intermediate pattern: it is either globally constant (and hence
invariant) or it distinguishes every orientation from its reversal.  In the
breaking regime, the two value fibers are exactly the two orientations.

This is a mathematical discriminator.  A concrete measurement still has to
provide a typed observable and an observed occurrence separately.
-/

/-- Every observable value is one of its values at a selected orientation and
its reversed partner. -/
theorem r3_observable_range_two_values
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity} {Observable : Type uObservable}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (observable : Orientation → Observable)
    (base orientation : Orientation) :
    observable orientation = observable base ∨
      observable orientation = observable (candidate.reverse base) := by
  rcases candidate.pairTransitive base orientation with same | partner
  · left
    subst orientation
    rfl
  · right
    subst orientation
    rfl

/-- On an R3 torsor, invariance under reversal is equivalent to global
constancy. -/
theorem r3_invariant_observable_iff_constant
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity} {Observable : Type uObservable}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (observable : Orientation → Observable) :
    InvariantObservable (r3FixedPointFreeInvolution candidate) observable ↔
      ∀ left right, observable left = observable right := by
  constructor
  · intro invariant left right
    exact r3_invariant_observable_constant candidate observable invariant
      right left
  · intro constant orientation
    exact constant (candidate.reverse orientation) orientation

/-- Every observable is globally constant or breaks reversal at every
orientation. -/
theorem r3_observable_constant_or_breaks_everywhere
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity} {Observable : Type uObservable}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (observable : Orientation → Observable) (base : Orientation) :
    (∀ left right, observable left = observable right) ∨
      (∀ orientation,
        SymmetryBreakingWitness (r3FixedPointFreeInvolution candidate)
          observable orientation) := by
  by_cases sameBase :
      observable (candidate.reverse base) = observable base
  · left
    have valueAtBase : ∀ orientation, observable orientation = observable base := by
      intro orientation
      rcases candidate.pairTransitive base orientation with same | partner
      · subst orientation
        rfl
      · subst orientation
        exact sameBase
    intro left right
    exact (valueAtBase left).trans (valueAtBase right).symm
  · right
    intro orientation
    rcases candidate.pairTransitive base orientation with same | partner
    · subst orientation
      exact sameBase
    · subst orientation
      change observable (candidate.reverse (candidate.reverse base)) ≠
        observable (candidate.reverse base)
      rw [candidate.reverseInvolutive]
      exact Ne.symm sameBase

/-- One symmetry-breaking witness propagates to every orientation. -/
theorem r3_breaking_witness_propagates_everywhere
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity} {Observable : Type uObservable}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (observable : Orientation → Observable) (base : Orientation)
    (breaking : SymmetryBreakingWitness
      (r3FixedPointFreeInvolution candidate) observable base) :
    ∀ orientation,
      SymmetryBreakingWitness (r3FixedPointFreeInvolution candidate)
        observable orientation := by
  rcases r3_observable_constant_or_breaks_everywhere candidate observable base with
    constant | globalBreaking
  · exact (breaking (constant (candidate.reverse base) base)).elim
  · exact globalBreaking

/-- Nonconstancy is equivalent to breaking reversal everywhere, not merely at
one witness. -/
theorem r3_observable_nonconstant_iff_breaks_everywhere
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity} {Observable : Type uObservable}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (observable : Orientation → Observable) (base : Orientation) :
    (∃ left right, observable left ≠ observable right) ↔
      ∀ orientation,
        SymmetryBreakingWitness (r3FixedPointFreeInvolution candidate)
          observable orientation := by
  constructor
  · rintro ⟨left, right, nonconstant⟩
    rcases r3_observable_constant_or_breaks_everywhere candidate observable base with
      constant | globalBreaking
    · exact (nonconstant (constant left right)).elim
    · exact globalBreaking
  · intro globalBreaking
    exact ⟨candidate.reverse base, base, globalBreaking base⟩

/-- In the breaking regime, the base-value fiber is exactly the base
orientation. -/
theorem r3_breaking_base_fiber
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity} {Observable : Type uObservable}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (observable : Orientation → Observable) (base orientation : Orientation)
    (breaking : observable (candidate.reverse base) ≠ observable base) :
    observable orientation = observable base ↔ orientation = base := by
  constructor
  · intro equality
    rcases candidate.pairTransitive base orientation with same | partner
    · exact same
    · subst orientation
      exact (breaking equality).elim
  · intro same
    subst orientation
    rfl

/-- In the breaking regime, the partner-value fiber is exactly the reversed
orientation. -/
theorem r3_breaking_partner_fiber
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity} {Observable : Type uObservable}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (observable : Orientation → Observable) (base orientation : Orientation)
    (breaking : observable (candidate.reverse base) ≠ observable base) :
    observable orientation = observable (candidate.reverse base) ↔
      orientation = candidate.reverse base := by
  constructor
  · intro equality
    rcases candidate.pairTransitive base orientation with same | partner
    · subst orientation
      exact (breaking equality.symm).elim
    · exact partner
  · intro partner
    subst orientation
    rfl

end OCKIndividuationMSpaceComposition
