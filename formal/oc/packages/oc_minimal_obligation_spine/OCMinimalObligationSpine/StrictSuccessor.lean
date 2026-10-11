import OCMinimalObligationSpine.MinimalTransition
import OCMinimalObligationSpine.UnifiedEntityProjection

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

universe uState uOldCarrier uNewCarrier uLiftCarrier uLiftCandidate uRepairCandidate

/--
`EncoderProjection oldEncode newEncode` is an explicit new-to-old
factorization: projecting the new representation recovers the old encoding.
It is a representational statement only; it carries no physical-axis claim.
-/
structure EncoderProjection
    {State : Type uState}
    {OldCarrier : Type uOldCarrier}
    {NewCarrier : Type uNewCarrier}
    (oldEncode : State -> OldCarrier)
    (newEncode : State -> NewCarrier) where
  project : NewCarrier -> OldCarrier
  factorEncode : forall state, project (newEncode state) = oldEncode state

/-- New collisions imply old collisions, so the new kernel refines the old one. -/
theorem EncoderProjection.new_collision_implies_old_collision
    {State : Type uState}
    {OldCarrier : Type uOldCarrier}
    {NewCarrier : Type uNewCarrier}
    {oldEncode : State -> OldCarrier}
    {newEncode : State -> NewCarrier}
    (projection : EncoderProjection oldEncode newEncode)
    {left right : State}
    (newCollision : newEncode left = newEncode right) :
    oldEncode left = oldEncode right := by
  calc
    oldEncode left = projection.project (newEncode left) :=
      (projection.factorEncode left).symm
    _ = projection.project (newEncode right) := by rw [newCollision]
    _ = oldEncode right := projection.factorEncode right

/-- Every distinction already visible to the old encoder remains visible. -/
theorem EncoderProjection.preserves_old_separation
    {State : Type uState}
    {OldCarrier : Type uOldCarrier}
    {NewCarrier : Type uNewCarrier}
    {oldEncode : State -> OldCarrier}
    {newEncode : State -> NewCarrier}
    (projection : EncoderProjection oldEncode newEncode)
    {left right : State}
    (oldSeparation : oldEncode left ≠ oldEncode right) :
    newEncode left ≠ newEncode right := by
  intro newCollision
  exact oldSeparation
    (projection.new_collision_implies_old_collision newCollision)

/-- The factorization already carried by every declared lift candidate. -/
def LiftCandidate.encoderProjection
    {K : CurrentK}
    (candidate : LiftCandidate.{uLiftCarrier} K) :
    EncoderProjection K.encode candidate.encode where
  project := candidate.project
  factorEncode := candidate.projectEncode

/--
A strict-kernel witness is one old collision that the new encoder separates.
It proves strictness of the kernel refinement, not existence of the encoder.
-/
structure StrictKernelWitness
    {State : Type uState}
    {OldCarrier : Type uOldCarrier}
    {NewCarrier : Type uNewCarrier}
    (oldEncode : State -> OldCarrier)
    (newEncode : State -> NewCarrier) where
  left : State
  right : State
  oldCollision : oldEncode left = oldEncode right
  newSeparation : newEncode left ≠ newEncode right

/-- A strict witness rules out refinement in the reverse kernel direction. -/
theorem StrictKernelWitness.not_reverse_kernel_refinement
    {State : Type uState}
    {OldCarrier : Type uOldCarrier}
    {NewCarrier : Type uNewCarrier}
    {oldEncode : State -> OldCarrier}
    {newEncode : State -> NewCarrier}
    (witness : StrictKernelWitness oldEncode newEncode) :
    Not (forall {left right : State},
      oldEncode left = oldEncode right ->
        newEncode left = newEncode right) := by
  intro reverseRefinement
  exact witness.newSeparation
    (reverseRefinement witness.oldCollision)

/-- A strict witness therefore excludes an explicit old-to-new factorization. -/
theorem StrictKernelWitness.not_reverse_projection
    {State : Type uState}
    {OldCarrier : Type uOldCarrier}
    {NewCarrier : Type uNewCarrier}
    {oldEncode : State -> OldCarrier}
    {newEncode : State -> NewCarrier}
    (witness : StrictKernelWitness oldEncode newEncode) :
    Not (Nonempty (EncoderProjection newEncode oldEncode)) := by
  intro ⟨reverseProjection⟩
  exact witness.newSeparation
    (reverseProjection.new_collision_implies_old_collision
      witness.oldCollision)

/--
A carrier relabeling is stronger than mutual kernel refinement: one carrier
equivalence must commute with both encoders.
-/
structure EncoderRelabeling
    {State : Type uState}
    {OldCarrier : Type uOldCarrier}
    {NewCarrier : Type uNewCarrier}
    (oldEncode : State -> OldCarrier)
    (newEncode : State -> NewCarrier) where
  toOld : NewCarrier -> OldCarrier
  toNew : OldCarrier -> NewCarrier
  toNew_toOld : forall carrier, toNew (toOld carrier) = carrier
  toOld_toNew : forall carrier, toOld (toNew carrier) = carrier
  factorEncode : forall state,
    toOld (newEncode state) = oldEncode state

/-- A separated old collision cannot be explained by carrier relabeling. -/
theorem StrictKernelWitness.not_relabeling
    {State : Type uState}
    {OldCarrier : Type uOldCarrier}
    {NewCarrier : Type uNewCarrier}
    {oldEncode : State -> OldCarrier}
    {newEncode : State -> NewCarrier}
    (witness : StrictKernelWitness oldEncode newEncode) :
    Not (Nonempty (EncoderRelabeling oldEncode newEncode)) := by
  intro ⟨relabeling⟩
  apply witness.newSeparation
  calc
    newEncode witness.left =
        relabeling.toNew (relabeling.toOld (newEncode witness.left)) :=
      (relabeling.toNew_toOld (newEncode witness.left)).symm
    _ = relabeling.toNew (oldEncode witness.left) := by
      rw [relabeling.factorEncode witness.left]
    _ = relabeling.toNew (oldEncode witness.right) := by
      rw [witness.oldCollision]
    _ = relabeling.toNew (relabeling.toOld (newEncode witness.right)) := by
      rw [relabeling.factorEncode witness.right]
    _ = newEncode witness.right :=
      relabeling.toNew_toOld (newEncode witness.right)

/--
A strict successor certificate for one concrete lift candidate.  The projection
also commutes with one encoded transition step.  This is not a construction of
a lift member, physical axis, or empirical improvement.
-/
structure StrictSuccessorCertificate
    (K : CurrentK)
    (candidate : LiftCandidate.{uLiftCarrier} K) where
  projection : EncoderProjection K.encode candidate.encode
  transitionFactorsOnEncoded : forall state,
    projection.project
        (candidate.carrierTransition (candidate.encode state)) =
      K.carrierTransition (K.encode state)
  strictWitness : StrictKernelWitness K.encode candidate.encode

theorem StrictSuccessorCertificate.kernel_refines_current
    {K : CurrentK}
    {candidate : LiftCandidate.{uLiftCarrier} K}
    (certificate : StrictSuccessorCertificate K candidate)
    {left right : K.State}
    (newCollision : candidate.encode left = candidate.encode right) :
    K.encode left = K.encode right :=
  certificate.projection.new_collision_implies_old_collision newCollision

theorem StrictSuccessorCertificate.preserves_current_separation
    {K : CurrentK}
    {candidate : LiftCandidate.{uLiftCarrier} K}
    (certificate : StrictSuccessorCertificate K candidate)
    {left right : K.State}
    (oldSeparation : K.encode left ≠ K.encode right) :
    candidate.encode left ≠ candidate.encode right :=
  certificate.projection.preserves_old_separation oldSeparation

theorem StrictSuccessorCertificate.not_reverse_projection
    {K : CurrentK}
    {candidate : LiftCandidate.{uLiftCarrier} K}
    (certificate : StrictSuccessorCertificate K candidate) :
    Not (Nonempty (EncoderProjection candidate.encode K.encode)) :=
  certificate.strictWitness.not_reverse_projection

theorem StrictSuccessorCertificate.not_relabeling
    {K : CurrentK}
    {candidate : LiftCandidate.{uLiftCarrier} K}
    (certificate : StrictSuccessorCertificate K candidate) :
    Not (Nonempty (EncoderRelabeling K.encode candidate.encode)) :=
  certificate.strictWitness.not_relabeling

/--
Every strict-successor certificate is a strict edge in the kernel-refinement
order used by the K hierarchy.
-/
theorem StrictSuccessorCertificate.kernel_strictly_refines_current
    {K : CurrentK}
    {candidate : LiftCandidate.{uLiftCarrier} K}
    (certificate : StrictSuccessorCertificate K candidate) :
    EncoderKernelStrictlyRefines candidate.encode K.encode := by
  constructor
  · intro left right newCollision
    exact certificate.kernel_refines_current newCollision
  · exact certificate.strictWitness.not_reverse_kernel_refinement

/--
Given scoped irreducible pressure and an actual member of the declared M-fiber,
construct the strict successor certificate for that member's lift candidate.
No uninhabited M-fiber is turned into an existence result.
-/
theorem strictSuccessorCertificate_of_pressure_mSpaceMember
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (member : MSpaceFiber liftSearch d) :
    Nonempty (StrictSuccessorCertificate K (liftSearch.lift member.1)) := by
  classical
  have strictResolution :=
    mSpace_member_strictly_resolves_pressure_distinction
      pressure liftSearch member
  have oldCollision : K.encode d.left = K.encode d.right := by
    apply Classical.byContradiction
    intro oldSeparation
    exact strictResolution.1 oldSeparation
  have newSeparation :
      (liftSearch.lift member.1).encode d.left ≠
        (liftSearch.lift member.1).encode d.right :=
    (liftResolves_iff_encoder_separates
      (liftSearch.lift member.1) d).mp strictResolution.2
  exact ⟨{
    projection := (liftSearch.lift member.1).encoderProjection
    transitionFactorsOnEncoded :=
      (liftSearch.lift member.1).projectTransitionOnEncoded
    strictWitness := {
      left := d.left
      right := d.right
      oldCollision := oldCollision
      newSeparation := newSeparation
    }
  }⟩

/--
The finite F07 argmin feeds the same F09 certificate without a second
selection step.  Minimality is inherited only from the declared finite fiber;
strictness is inherited from pressure plus M-space membership.
-/
theorem strictSuccessorCertificate_of_pressure_finiteArgmin
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    {declared : FiniteDeclaredMSpace liftSearch d}
    {rank : TransitionRank liftSearch}
    (argmin : FiniteMSpaceArgmin declared rank) :
    Nonempty
      (StrictSuccessorCertificate K
        (liftSearch.lift argmin.minimizer.1)) :=
  strictSuccessorCertificate_of_pressure_mSpaceMember
    pressure liftSearch argmin.minimizer

/--
The general natural-rank F07 argmin feeds the F09 strict-successor certificate
without a finiteness or enumeration premise.
-/
theorem strictSuccessorCertificate_of_pressure_natRankedArgmin
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    {rank : TransitionRank liftSearch}
    (argmin : NatRankedMSpaceArgmin liftSearch d rank) :
    Nonempty
      (StrictSuccessorCertificate K
        (liftSearch.lift argmin.minimizer.1)) :=
  strictSuccessorCertificate_of_pressure_mSpaceMember
    pressure liftSearch argmin.minimizer

end OCMinimalObligationSpine
