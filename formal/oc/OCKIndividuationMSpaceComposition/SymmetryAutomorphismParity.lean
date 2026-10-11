import OCKIndividuationMSpaceComposition.SymmetryAdmissibleTransformations

namespace OCKIndividuationMSpaceComposition

universe uOrientation uAxis uIdentity

/-!
# The intrinsic C₂ algebra of admissible transformations

The classification theorem says that an admissible endomorphism is identity
or reversal.  Here those maps are packaged as a type and given an intrinsic
parity coordinate.  Evaluation at one base orientation yields an equivalence
with `Bool`; under that equivalence, composition is Boolean xor.

Thus the two-element symmetry algebra is recovered from admissibility and
torsor transitivity rather than postulated as an unrelated external label.
-/

/-- An endomorphism carrying its proof of compatibility with the R3
reversal. -/
structure R3AdmissibleEndomorphism
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity) where
  toFun : Orientation → Orientation
  admissible : R3AdmissibleTransformation candidate toFun

instance
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    {candidate : R3C2OrientationTorsorInterface Orientation Axis Identity} :
    CoeFun (R3AdmissibleEndomorphism candidate)
      (fun _ => Orientation → Orientation) :=
  ⟨R3AdmissibleEndomorphism.toFun⟩

/-- Identity as an admissible endomorphism. -/
def r3AdmissibleIdentity
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity) :
    R3AdmissibleEndomorphism candidate where
  toFun := id
  admissible := r3_identity_admissible candidate

/-- Reversal as an admissible endomorphism. -/
def r3AdmissibleReversal
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity) :
    R3AdmissibleEndomorphism candidate where
  toFun := candidate.reverse
  admissible := r3_reversal_admissible candidate

/-- Composition remains admissible. -/
def r3AdmissibleComposition
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    {candidate : R3C2OrientationTorsorInterface Orientation Axis Identity}
    (first second : R3AdmissibleEndomorphism candidate) :
    R3AdmissibleEndomorphism candidate where
  toFun := fun orientation => first (second orientation)
  admissible := by
    intro orientation
    change first.toFun (second.toFun (candidate.reverse orientation)) =
      candidate.reverse (first.toFun (second.toFun orientation))
    rw [second.admissible orientation,
      first.admissible (second.toFun orientation)]

/-- Two admissible endomorphisms agreeing at one base orientation agree
everywhere. -/
theorem r3AdmissibleEndomorphism_ext_at_base
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    {candidate : R3C2OrientationTorsorInterface Orientation Axis Identity}
    (base : Orientation)
    (first second : R3AdmissibleEndomorphism candidate)
    (atBase : first base = second base) :
    first = second := by
  cases first with
  | mk first firstAdmissible =>
      cases second with
      | mk second secondAdmissible =>
          congr
          funext orientation
          rcases candidate.pairTransitive base orientation with same | partner
          · subst orientation
            exact atBase
          · subst orientation
            calc
              first (candidate.reverse base) =
                  candidate.reverse (first base) := firstAdmissible base
              _ = candidate.reverse (second base) :=
                congrArg candidate.reverse atBase
              _ = second (candidate.reverse base) :=
                (secondAdmissible base).symm

/-- The parity of an admissible transformation is where it sends the chosen
basepoint in the pointed Bool coordinate. -/
noncomputable def r3AdmissibleParity
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    {candidate : R3C2OrientationTorsorInterface Orientation Axis Identity}
    (base : Orientation) (transform : R3AdmissibleEndomorphism candidate) : Bool :=
  r3OrientationEquivBool candidate base (transform base)

@[simp] theorem r3AdmissibleParity_identity
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base : Orientation) :
    r3AdmissibleParity base (r3AdmissibleIdentity candidate) = false :=
  r3OrientationEquivBool_base candidate base

@[simp] theorem r3AdmissibleParity_reversal
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base : Orientation) :
    r3AdmissibleParity base (r3AdmissibleReversal candidate) = true :=
  r3OrientationEquivBool_partner candidate base

/-- Every admissible endomorphism is exactly the identity package or exactly
the reversal package. -/
theorem r3AdmissibleEndomorphism_eq_identity_or_reversal
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    {candidate : R3C2OrientationTorsorInterface Orientation Axis Identity}
    (base : Orientation) (transform : R3AdmissibleEndomorphism candidate) :
    transform = r3AdmissibleIdentity candidate ∨
      transform = r3AdmissibleReversal candidate := by
  rcases r3_admissible_transformation_classification candidate base
      transform.toFun transform.admissible with fixed | reversed
  · left
    exact r3AdmissibleEndomorphism_ext_at_base base transform
      (r3AdmissibleIdentity candidate) (fixed base)
  · right
    exact r3AdmissibleEndomorphism_ext_at_base base transform
      (r3AdmissibleReversal candidate) (reversed base)

/-- Evaluation parity is a complete two-element classification of admissible
endomorphisms. -/
noncomputable def r3AdmissibleEndomorphismEquivBool
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (base : Orientation) :
    R3AdmissibleEndomorphism candidate ≃ Bool where
  toFun := r3AdmissibleParity base
  invFun := fun parity =>
    if parity then r3AdmissibleReversal candidate
    else r3AdmissibleIdentity candidate
  left_inv := by
    intro transform
    rcases r3AdmissibleEndomorphism_eq_identity_or_reversal base transform with
      identity | reversal
    · subst transform
      simp
    · subst transform
      simp
  right_inv := by
    intro parity
    cases parity <;> simp

/-- Composition of admissible transformations is xor of their parities. -/
theorem r3AdmissibleParity_composition
    {Orientation : Type uOrientation} {Axis : Type uAxis}
    {Identity : Type uIdentity}
    {candidate : R3C2OrientationTorsorInterface Orientation Axis Identity}
    (base : Orientation)
    (first second : R3AdmissibleEndomorphism candidate) :
    r3AdmissibleParity base (r3AdmissibleComposition first second) =
      Bool.xor (r3AdmissibleParity base first)
        (r3AdmissibleParity base second) := by
  rcases r3AdmissibleEndomorphism_eq_identity_or_reversal base first with
    firstIdentity | firstReversal
  · subst first
    rcases r3AdmissibleEndomorphism_eq_identity_or_reversal base second with
      secondIdentity | secondReversal
    · subst second
      simp [r3AdmissibleParity, r3AdmissibleComposition,
        r3AdmissibleIdentity]
    · subst second
      simp [r3AdmissibleParity, r3AdmissibleComposition,
        r3AdmissibleIdentity, r3AdmissibleReversal]
  · subst first
    rcases r3AdmissibleEndomorphism_eq_identity_or_reversal base second with
      secondIdentity | secondReversal
    · subst second
      simp [r3AdmissibleParity, r3AdmissibleComposition,
        r3AdmissibleIdentity, r3AdmissibleReversal]
    · subst second
      simp [r3AdmissibleParity, r3AdmissibleComposition,
        r3AdmissibleReversal, candidate.reverseInvolutive]

end OCKIndividuationMSpaceComposition
