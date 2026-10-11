import OCMinimalObligationSpine.CurrentK
import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionExtension

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine
open OCMinimalObligationSpine.UnifiedEntityProjection

/-!
# From an OC trajectory distinction to its local C₂ axis

`TrajectoryDistinction` is existing OC core evidence: at one finite step and
receiver, two states have unequal effects.  This module proves that such an
observational distinction supplies the primitive relation witness required by
the new symmetry foundation.  The resulting C₂ action is local to the two
witnessed states unless a separate coverage or complement-pairing theorem is
available.
-/

/-- The symmetric, irreflexive effect-difference relation at one frozen step
and receiver. -/
def trajectoryEffectDistinctionRelation
    (K : CurrentK) (step : Nat) (receiver : K.Receiver) :
    K.State → K.State → Prop :=
  fun first second =>
    K.receiverEffect (evolveState K.stateTransition step first) receiver ≠
      K.receiverEffect (evolveState K.stateTransition step second) receiver

theorem trajectoryEffectDistinctionRelation_irreflexive
    (K : CurrentK) (step : Nat) (receiver : K.Receiver) :
    ∀ state : K.State,
      ¬ trajectoryEffectDistinctionRelation K step receiver state state := by
  intro state distinguished
  exact distinguished rfl

theorem trajectoryEffectDistinctionRelation_symmetric
    (K : CurrentK) (step : Nat) (receiver : K.Receiver) :
    Symmetric (trajectoryEffectDistinctionRelation K step receiver) := by
  intro first second distinguished
  exact Ne.symm distinguished

/-- Existing trajectory evidence becomes a relation-level primitive
distinction without adding a symmetry operation. -/
def trajectoryDistinctionWitness (K : CurrentK)
    (distinction : TrajectoryDistinction K) :
    IrreflexiveDistinctionWitness K.State where
  relation := trajectoryEffectDistinctionRelation K
    distinction.step distinction.receiver
  irreflexive := trajectoryEffectDistinctionRelation_irreflexive K
    distinction.step distinction.receiver
  first := distinction.left
  second := distinction.right
  witnessed := distinction.effect_ne

/-- A finite-step receiver-effect distinction therefore separates the two
states themselves. -/
theorem trajectoryDistinction_states_ne (K : CurrentK)
    (distinction : TrajectoryDistinction K) :
    distinction.left ≠ distinction.right :=
  (trajectoryDistinctionWitness K distinction).endpoints_ne

/-- Forget the observational provenance only after extracting the proved
primitive distinction. -/
def trajectoryDistinctionToPrimitive (K : CurrentK)
    (distinction : TrajectoryDistinction K) : PrimitiveDistinction K.State :=
  (trajectoryDistinctionWitness K distinction).toPrimitiveDistinction

/-- The generated local axis of the two states distinguished by the receiver. -/
abbrev TrajectoryDistinctionAxis (K : CurrentK)
    (distinction : TrajectoryDistinction K) :=
  (trajectoryDistinctionToPrimitive K distinction).Axis

/-- Every OC trajectory distinction produces a local R3 C₂ torsor on its
generated two-state axis. -/
noncomputable def trajectoryDistinctionToLocalR3 (K : CurrentK)
    (distinction : TrajectoryDistinction K) :
    R3C2OrientationTorsorInterface
      (TrajectoryDistinctionAxis K distinction) Unit Unit :=
  (trajectoryDistinctionToPrimitive K distinction).toR3Torsor

/-- The admissible automorphism algebra of that local axis is C₂. -/
noncomputable def trajectoryDistinctionAutomorphismsEquivBool (K : CurrentK)
    (distinction : TrajectoryDistinction K) :
    R3AdmissibleEndomorphism
        (trajectoryDistinctionToLocalR3 K distinction) ≃ Bool :=
  PrimitiveDistinction.generatedAdmissibleAutomorphismsEquivBool
    (trajectoryDistinctionToPrimitive K distinction)

/-- Exact global boundary for the canonical pair swap on the state carrier. -/
theorem trajectoryDistinction_globalPairSwap_free_iff_stateCoverage
    (K : CurrentK) (distinction : TrajectoryDistinction K) :
    (∀ state : K.State,
        (trajectoryDistinctionToPrimitive K distinction).pairSwap state ≠ state) ↔
      ∀ state : K.State,
        state = distinction.left ∨ state = distinction.right := by
  exact PrimitiveDistinction.pairSwap_fixedPointFree_iff_coversCarrier
    (trajectoryDistinctionToPrimitive K distinction)

/-- The underlying effect-difference relation does not privilege an ordering:
the reverse evidence follows directly.  This is relation symmetry, not yet a
global carrier automorphism. -/
theorem trajectoryDistinction_reverse_effect_ne (K : CurrentK)
    (distinction : TrajectoryDistinction K) :
    trajectoryEffectDistinctionRelation K distinction.step distinction.receiver
      distinction.right distinction.left :=
  trajectoryEffectDistinctionRelation_symmetric K
    distinction.step distinction.receiver distinction.effect_ne

end OCKIndividuationMSpaceComposition
