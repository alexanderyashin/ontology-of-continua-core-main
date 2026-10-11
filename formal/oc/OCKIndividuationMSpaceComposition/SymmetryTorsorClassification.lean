import OCKIndividuationMSpaceComposition.SymmetryCandidateResolution

namespace OCKIndividuationMSpaceComposition

universe uOrientation uAxis uIdentity

/-!
# Classification of a pointed C₂ torsor

An R3 carrier is a free transitive C₂-set.  Once one orientation is selected
as a basepoint, it is explicitly equivalent to `Bool`: the basepoint is
`false`, its reversed partner is `true`, and reversal is Boolean negation.
Changing the basepoint to its partner negates the coordinate everywhere.

This proves both completeness of the two-side description and its precise
non-canonicity: the unpointed torsor is canonical, while its sign coordinate
is defined only up to the unique non-trivial automorphism of `Bool`.
-/

/-- The explicit coordinate equivalence of a pointed R3 torsor with `Bool`. -/
noncomputable def r3OrientationEquivBool
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base : Orientation) : Orientation ≃ Bool := by
  classical
  refine
    { toFun := fun orientation => if orientation = base then false else true
      invFun := fun sign => if sign then candidate.reverse base else base
      left_inv := ?_
      right_inv := ?_ }
  · intro orientation
    rcases candidate.pairTransitive base orientation with same | partner
    · subst orientation
      simp
    · subst orientation
      simp [candidate.reverseFree base]
  · intro sign
    cases sign <;> simp [candidate.reverseFree base]

@[simp] theorem r3OrientationEquivBool_base
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base : Orientation) :
    r3OrientationEquivBool candidate base base = false := by
  simp [r3OrientationEquivBool]

@[simp] theorem r3OrientationEquivBool_partner
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base : Orientation) :
    r3OrientationEquivBool candidate base (candidate.reverse base) = true := by
  simp [r3OrientationEquivBool, candidate.reverseFree base]

/-- Reversal of an orientation is exactly Boolean negation in the pointed
coordinate. -/
theorem r3OrientationEquivBool_reverse
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base orientation : Orientation) :
    r3OrientationEquivBool candidate base (candidate.reverse orientation) =
      Bool.not (r3OrientationEquivBool candidate base orientation) := by
  classical
  rcases candidate.pairTransitive base orientation with same | partner
  · subst orientation
    simp [r3OrientationEquivBool, candidate.reverseFree base]
  · subst orientation
    simp [r3OrientationEquivBool, candidate.reverseInvolutive,
      candidate.reverseFree base]

/-- The false fiber is exactly the selected basepoint. -/
theorem r3OrientationEquivBool_false_iff
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base orientation : Orientation) :
    r3OrientationEquivBool candidate base orientation = false ↔
      orientation = base := by
  simp [r3OrientationEquivBool]

/-- The true fiber is exactly the reversed partner of the basepoint. -/
theorem r3OrientationEquivBool_true_iff
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base orientation : Orientation) :
    r3OrientationEquivBool candidate base orientation = true ↔
      orientation = candidate.reverse base := by
  constructor
  · intro positive
    rcases candidate.pairTransitive base orientation with same | partner
    · subst orientation
      simp at positive
    · exact partner
  · intro partner
    subst orientation
    exact r3OrientationEquivBool_partner candidate base

/-- Changing the chosen endpoint to its partner reverses the sign coordinate
at every orientation. -/
theorem r3OrientationEquivBool_change_base
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base orientation : Orientation) :
    r3OrientationEquivBool candidate (candidate.reverse base) orientation =
      Bool.not (r3OrientationEquivBool candidate base orientation) := by
  classical
  rcases candidate.pairTransitive base orientation with same | partner
  · subst orientation
    simp [r3OrientationEquivBool, Ne.symm (candidate.reverseFree base)]
  · subst orientation
    simp only [r3OrientationEquivBool_base, r3OrientationEquivBool_partner,
      Bool.not_true]

end OCKIndividuationMSpaceComposition
