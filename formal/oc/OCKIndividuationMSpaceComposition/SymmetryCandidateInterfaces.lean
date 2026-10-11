/-!
# Bounded R1/R2/R3 symmetry candidate interfaces

This module is the exact Lean target of
`OC14-G20-P0-S1B-LEAN-FORMALIZATION-0001`.  It formalizes only the interface
and theorem spine admitted by the G19 bounded candidate comparison.

It deliberately selects neither a winning candidate nor a mathematical
formalism.  In particular, the two unresolved R2 source cuts are represented
by singleton typed statuses.  No theorem supplies two-side formulas and no
theorem transports a source-literal invariant.
-/

namespace OCKIndividuationMSpaceComposition

/-- The three comparison tracks.  This is an index, not a winner selection. -/
inductive SymmetryCandidateTrack where
  | r1CanonicalSeparator
  | r2CovectorCoaxisDuality
  | r3C2OrientationTorsor
  deriving DecidableEq, Repr

/--
The complete R2 two-side structure is unavailable in the accepted source cut.
The singleton type makes invention of a second, silently admitted state
impossible inside this interface.
-/
inductive R2TwoSidesStatus where
  | typedUnavailable
  deriving DecidableEq, Repr

/--
R2 invariant records are source-literal only.  No transformation map and no
transport theorem are supplied by this status.
-/
inductive R2InvariantTransportStatus where
  | sourceLiteralOnlyNoTransformationClaim
  deriving DecidableEq, Repr

/--
R1 packages a separator of an already admitted axis.  Compatibility and
canonicality are explicit hypotheses; their truth is not inferred from the
mere existence of a separator.
-/
structure R1CanonicalSeparatorInterface
    (Carrier Axis Boundary Projection : Type _) where
  separator : Carrier → Prop
  axis : Axis
  boundary : Boundary
  projection : Carrier → Projection
  axisBoundaryCompatible : Prop
  axisBoundaryCompatibilityEvidence : axisBoundaryCompatible
  projectionCompatible : Prop
  projectionCompatibilityEvidence : projectionCompatible
  canonicalityCondition : Prop
  canonicalityEvidence : canonicalityCondition

/-- R1 exposes axis/boundary compatibility only when it was supplied. -/
theorem r1_axis_boundary_compatibility
    {Carrier Axis Boundary Projection : Type _}
    (candidate : R1CanonicalSeparatorInterface Carrier Axis Boundary Projection) :
    candidate.axisBoundaryCompatible :=
  candidate.axisBoundaryCompatibilityEvidence

/-- R1 exposes projection compatibility only when it was supplied. -/
theorem r1_projection_compatibility
    {Carrier Axis Boundary Projection : Type _}
    (candidate : R1CanonicalSeparatorInterface Carrier Axis Boundary Projection) :
    candidate.projectionCompatible :=
  candidate.projectionCompatibilityEvidence

/-- R1 canonicality remains an explicit condition rather than a hidden fact. -/
theorem r1_canonicality_condition
    {Carrier Axis Boundary Projection : Type _}
    (candidate : R1CanonicalSeparatorInterface Carrier Axis Boundary Projection) :
    candidate.canonicalityCondition :=
  candidate.canonicalityEvidence

/--
R2 keeps carrier, scalar, coaxis, pairing and induced-axis types separate.
Axis availability is conditional on an admitted pairing.  The two open cuts
are fields with only their fail-closed source states available.
-/
structure R2CovectorCoaxisDualityInterface
    (Carrier Scalar Coaxis Pairing Axis : Type _) where
  covector : Carrier → Scalar
  coaxis : Coaxis
  pairing : Pairing
  inducedAxis : Option Axis
  pairingAdmitted : Prop
  axisAvailable : Prop
  axisRequiresAdmittedPairing : axisAvailable → pairingAdmitted
  dualityBoundary : Prop
  twoSides : R2TwoSidesStatus
  invariantTransport : R2InvariantTransportStatus

/-- An available R2 axis uses the explicit admitted-pairing premise. -/
theorem r2_axis_requires_admitted_pairing
    {Carrier Scalar Coaxis Pairing Axis : Type _}
    (candidate : R2CovectorCoaxisDualityInterface Carrier Scalar Coaxis Pairing Axis)
    (available : candidate.axisAvailable) :
    candidate.pairingAdmitted :=
  candidate.axisRequiresAdmittedPairing available

/-- The accepted source cut cannot silently gain R2 two-side formulas. -/
theorem r2_two_sides_remains_typed_unavailable
    {Carrier Scalar Coaxis Pairing Axis : Type _}
    (candidate : R2CovectorCoaxisDualityInterface Carrier Scalar Coaxis Pairing Axis) :
    candidate.twoSides = R2TwoSidesStatus.typedUnavailable := by
  cases candidate.twoSides
  rfl

/-- The accepted source cut cannot silently gain an invariant transport theorem. -/
theorem r2_invariant_transport_remains_source_literal
    {Carrier Scalar Coaxis Pairing Axis : Type _}
    (candidate : R2CovectorCoaxisDualityInterface Carrier Scalar Coaxis Pairing Axis) :
    candidate.invariantTransport =
      R2InvariantTransportStatus.sourceLiteralOnlyNoTransformationClaim := by
  cases candidate.invariantTransport
  rfl

/--
R3 is a candidate C2-orientation interface.  The reversal is involutive, free
and pair-transitive only when those conditions are supplied.  Orientation,
axis and token identity remain different types.
-/
structure R3C2OrientationTorsorInterface
    (Orientation Axis Identity : Type _) where
  reverse : Orientation → Orientation
  reverseInvolutive : ∀ orientation, reverse (reverse orientation) = orientation
  reverseFree : ∀ orientation, reverse orientation ≠ orientation
  pairTransitive : ∀ first second, second = first ∨ second = reverse first
  axisOf : Orientation → Axis
  identityOf : Orientation → Identity

/-- R3 reversal is involutive under the explicit candidate condition. -/
theorem r3_reverse_involutive
    {Orientation Axis Identity : Type _}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (orientation : Orientation) :
    candidate.reverse (candidate.reverse orientation) = orientation :=
  candidate.reverseInvolutive orientation

/-- R3 freeness is exposed without identifying orientation with object identity. -/
theorem r3_reverse_free
    {Orientation Axis Identity : Type _}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (orientation : Orientation) :
    candidate.reverse orientation ≠ orientation :=
  candidate.reverseFree orientation

/-- R3 transitivity is bounded to the two candidate orientations. -/
theorem r3_pair_transitive
    {Orientation Axis Identity : Type _}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (first second : Orientation) :
    second = first ∨ second = candidate.reverse first :=
  candidate.pairTransitive first second

/--
The observation surface returns an axis and an identity as differently typed
values.  It contains no equality or coercion between them.
-/
def r3_typed_axis_identity_observation
    {Orientation Axis Identity : Type _}
    (candidate : R3C2OrientationTorsorInterface Orientation Axis Identity)
    (orientation : Orientation) : Axis × Identity :=
  (candidate.axisOf orientation, candidate.identityOf orientation)

/--
One comparison bundle retains all three candidate interfaces while enforcing
null winner and null formalism fields.
-/
structure SymmetryCandidateInterfaceBundle
    (R1Carrier R1Axis R1Boundary R1Projection : Type _)
    (R2Carrier R2Scalar R2Coaxis R2Pairing R2Axis : Type _)
    (R3Orientation R3Axis R3Identity : Type _) where
  r1 : R1CanonicalSeparatorInterface R1Carrier R1Axis R1Boundary R1Projection
  r2 : R2CovectorCoaxisDualityInterface R2Carrier R2Scalar R2Coaxis R2Pairing R2Axis
  r3 : R3C2OrientationTorsorInterface R3Orientation R3Axis R3Identity
  winner : Option SymmetryCandidateTrack
  formalism : Option String
  winnerNull : winner = none
  formalismNull : formalism = none

/-- The admitted bundle does not select a candidate winner. -/
theorem symmetry_candidate_winner_remains_null
    {R1Carrier R1Axis R1Boundary R1Projection : Type _}
    {R2Carrier R2Scalar R2Coaxis R2Pairing R2Axis : Type _}
    {R3Orientation R3Axis R3Identity : Type _}
    (bundle : SymmetryCandidateInterfaceBundle
      R1Carrier R1Axis R1Boundary R1Projection
      R2Carrier R2Scalar R2Coaxis R2Pairing R2Axis
      R3Orientation R3Axis R3Identity) :
    bundle.winner = none :=
  bundle.winnerNull

/-- The admitted bundle does not select a mathematical formalism. -/
theorem symmetry_candidate_formalism_remains_null
    {R1Carrier R1Axis R1Boundary R1Projection : Type _}
    {R2Carrier R2Scalar R2Coaxis R2Pairing R2Axis : Type _}
    {R3Orientation R3Axis R3Identity : Type _}
    (bundle : SymmetryCandidateInterfaceBundle
      R1Carrier R1Axis R1Boundary R1Projection
      R2Carrier R2Scalar R2Coaxis R2Pairing R2Axis
      R3Orientation R3Axis R3Identity) :
    bundle.formalism = none :=
  bundle.formalismNull

end OCKIndividuationMSpaceComposition
