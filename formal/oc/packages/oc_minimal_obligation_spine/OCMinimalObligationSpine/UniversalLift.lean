import OCMinimalObligationSpine.MSpace

namespace OCMinimalObligationSpine

universe u

/-!
This module is a machine-checked adapter for the existing ESTRA No-Go/STOP
boundary, not a claim of a new standalone No-Go family.  ESTRA already treats
STOP and transformation impossibility as relative to an explicitly constrained
admissible continuation space.  The lemma below supplies the missing formal
counterpoint: once those constraints are removed, a structural lift can always
be constructed by adjoining state.  Hence any no-lift or collapse result must
name the constraints that exclude this witness.
-/

/--
The unrestricted structural lift always exists: retain the old carrier and
adjoin the full substrate state.  This construction is mathematical only.  It
does not assert that the added state is observable, finite, affordable, or
physically admissible.
-/
def universalStateLift
    (K : CurrentK.{u, u, u, u}) :
    LiftCandidate.{u} K where
  Carrier := K.Carrier × K.State
  encode state := (K.encode state, state)
  carrierTransition carrierState :=
    (K.carrierTransition carrierState.1, K.stateTransition carrierState.2)
  decodeReceiverEffect carrierState receiver :=
    K.receiverEffect carrierState.2 receiver
  project carrierState := carrierState.1
  projectEncode _ := rfl
  projectTransitionOnEncoded _ := rfl

/-- A certified trajectory distinction necessarily uses distinct states. -/
theorem trajectoryDistinction_states_ne
    {K : CurrentK.{u, u, u, u}}
    (d : TrajectoryDistinction K) :
    d.left ≠ d.right := by
  intro statesEqual
  apply d.effect_ne
  rw [statesEqual]

/-- The unrestricted state-adjoining lift resolves every certified distinction. -/
theorem universalStateLift_resolves
    {K : CurrentK.{u, u, u, u}}
    (d : TrajectoryDistinction K) :
    LiftResolves (universalStateLift K) d := by
  intro encodedEqual
  exact trajectoryDistinction_states_ne d (congrArg Prod.snd encodedEqual)

/-- A one-candidate frozen search class exposing the unrestricted lift. -/
def universalStateLiftSearch
    (K : CurrentK.{u, u, u, u}) :
    LiftSearchClass.{u, 0} K where
  Candidate := Unit
  lift _ := universalStateLift K
  constraints _ := True

/--
Every certified distinction has a constructive member in the unrestricted
state-adjoining search class.
-/
theorem universalStateLift_available
    (K : CurrentK.{u, u, u, u})
    (d : TrajectoryDistinction K) :
    AvailableLiftWithin (universalStateLiftSearch K) d := by
  exact availableLiftWithin_of_witness
    (universalStateLiftSearch K) d Unit.unit trivial
    (universalStateLift_resolves d)

/--
Therefore scoped no-lift, and hence bounded collapse, cannot be inferred from
representation failure alone when this unrestricted candidate is admitted.
-/
theorem unrestricted_structural_no_lift_is_impossible
    (K : CurrentK.{u, u, u, u})
    (d : TrajectoryDistinction K) :
    ¬ (¬ AvailableLiftWithin (universalStateLiftSearch K) d) := by
  intro noLift
  exact noLift (universalStateLift_available K d)

end OCMinimalObligationSpine
