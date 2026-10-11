import OCKIndividuationMSpaceComposition.SymmetryCandidateInterfaces
import OCKIndividuationMSpaceComposition.SymmetryAxisCoaxis
import OCKIndividuationMSpaceComposition.SymmetryInvariantQuotient

namespace OCKIndividuationMSpaceComposition

universe u

/-!
# A non-vacuous R1 canonical separator

The historical R1 interface separated its predicates from their evidence, but
did not itself construct those predicates.  Here the proved symmetry kernel
provides a concrete instance.

For a chosen endpoint `x`, the separator is the positive coaxis side, the axis
is its two-point orbit, the boundary is the orbit class, and the projection is
the quotient map.  Replacing `x` by its partner reverses the separator while
leaving the axis and boundary class unchanged.  This is the exact canonicality
available without making a global orientation choice.
-/

/-- The carrier-level relative separator selected by the endpoint `x`. -/
def relativeAxisSeparator {Carrier : Type u}
    (x : Carrier) : Carrier → Prop :=
  fun y => y = x

/-- Orbit membership is exactly equality of the canonical quotient boundary
class. -/
theorem axis_membership_iff_boundary_class
    {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x y : Carrier) :
    y ∈ axis symmetry x ↔
      axisClass symmetry y = axisClass symmetry x := by
  constructor
  · intro membership
    exact (axisClass_eq_iff_sameAxis symmetry y x).2
      (sameAxis_symm symmetry membership)
  · intro equality
    exact sameAxis_symm symmetry
      ((axisClass_eq_iff_sameAxis symmetry y x).1 equality)

/-- The quotient projection itself is invariant under the primitive action. -/
theorem axisClass_projection_invariant
    {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) :
    InvariantObservable symmetry (axisClass symmetry) :=
  action_preserves_axis_class symmetry

/-- A concrete R1 package whose compatibility and canonicality propositions
state the actual orbit/quotient equations. -/
def coreR1CanonicalSeparator
    {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    R1CanonicalSeparatorInterface Carrier (Set Carrier)
      (AxisQuotient symmetry) (AxisQuotient symmetry) where
  separator := relativeAxisSeparator x
  axis := axis symmetry x
  boundary := axisClass symmetry x
  projection := axisClass symmetry
  axisBoundaryCompatible :=
    ∀ y, y ∈ axis symmetry x ↔
      axisClass symmetry y = axisClass symmetry x
  axisBoundaryCompatibilityEvidence :=
    axis_membership_iff_boundary_class symmetry x
  projectionCompatible :=
    InvariantObservable symmetry (axisClass symmetry)
  projectionCompatibilityEvidence :=
    axisClass_projection_invariant symmetry
  canonicalityCondition :=
    ∀ y, axis symmetry y = axis symmetry x ↔
      axisClass symmetry y = axisClass symmetry x
  canonicalityEvidence := by
    intro y
    rw [axis_eq_iff_sameAxis, axisClass_eq_iff_sameAxis]

/-- The concrete R1 separator restricted to its axis is exactly the positive
side of the base coaxis. -/
theorem coreR1_separator_is_positive_side
    {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier)
    (y : axis symmetry x) :
    (coreR1CanonicalSeparator symmetry x).separator y.1 ↔
      y ∈ axisPositiveSide symmetry x :=
  Iff.rfl

/-- Acting on an axis point flips the concrete R1 separator. -/
theorem coreR1_separator_flips
    {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier)
    (y : axis symmetry x) :
    (coreR1CanonicalSeparator symmetry x).separator
        (symmetry.action y.1) ↔
      ¬ (coreR1CanonicalSeparator symmetry x).separator y.1 := by
  exact (axisSwap_positive_iff_negative symmetry x y).trans
    (axis_negative_iff_not_positive symmetry x y)

/-- Reversing the seed leaves the canonical axis unchanged. -/
theorem coreR1_seed_reversal_preserves_axis
    {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    (coreR1CanonicalSeparator symmetry (symmetry.action x)).axis =
      (coreR1CanonicalSeparator symmetry x).axis :=
  axis_invariant symmetry x

/-- Reversing the seed leaves the quotient boundary class unchanged. -/
theorem coreR1_seed_reversal_preserves_boundary
    {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier) :
    (coreR1CanonicalSeparator symmetry (symmetry.action x)).boundary =
      (coreR1CanonicalSeparator symmetry x).boundary :=
  action_preserves_axis_class symmetry x

/-- Relative to the original axis, choosing the partner as seed complements
the separator. -/
theorem coreR1_seed_reversal_complements_separator
    {Carrier : Type u}
    (symmetry : FixedPointFreeInvolution Carrier) (x : Carrier)
    (y : axis symmetry x) :
    (coreR1CanonicalSeparator symmetry (symmetry.action x)).separator y.1 ↔
      ¬ (coreR1CanonicalSeparator symmetry x).separator y.1 :=
  axis_negative_iff_not_positive symmetry x y

end OCKIndividuationMSpaceComposition
