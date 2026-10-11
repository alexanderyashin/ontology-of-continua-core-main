import OCMinimalObligationSpine.FirstPrincipleContinuationTrichotomy
import OCMinimalObligationSpine.UniversalLift

namespace OCScientificExtensions.FirstPrincipleBoolWitness

open OCMinimalObligationSpine
open UnifiedEntityProjection

/-!
# A jointly inhabited positive first-principle route

This separate extension gives actual data for the scoped exact-refinement
branch.  The substrate and receiver effect are Bool, the old carrier and
receiver are Unit, and both old transitions are identities.  The old decoder
always returns false.  Its encoded dynamics are compatible, but its declared
receiver semantics lose the true state.

The repair scope contains EVERY same-carrier candidate for this CurrentK;
architecture preservation and admissibility are explicitly True.  It is
nonempty, yet the Unit carrier prevents every candidate from separating the
certified Bool distinction.  The lift scope is the inherited singleton
full-state lift, with carrier Unit × Bool and True admission constraints.
Here its declared decoder and dynamics are exact.

Rank is the constant natural number zero.  This is a stipulated mathematical
rank, with no physical unit, resource measurement, performance, or empirical
interpretation.  Its argmin and exact strict-successor certificate are given
directly; the witness does not need classical Nat.find selection.  Instantiating
the inherited general trichotomy still uses that theorem's proof foundations.

Qualification is recorded in the separate dated extension register and receipt;
source text alone supplies no compiled-proof or release acceptance claim.
This file does not extend or modify the frozen inherited 992-module corpus.
No physical realization, observation access, affordability, or empirical
validation is asserted.
-/

/-- An identity-dynamics declaration with a lossy Unit representation. -/
def current : CurrentK where
  State := Bool
  Receiver := Unit
  Effect := Bool
  Carrier := Unit
  stateTransition := fun state => state
  receiverEffect := fun state _ => state
  encode := fun _ => ()
  carrierTransition := fun carrier => carrier
  decodeReceiverEffect := fun _ _ => false

/-- The two receiver effects already differ at step zero. -/
def distinction : TrajectoryDistinction current where
  left := false
  right := true
  step := 0
  receiver := ()
  effect_ne := by
    change false ≠ true
    intro impossible
    cases impossible

/-- Every certified distinction is demanded in this stipulated example. -/
def demand : ActiveDemand current := fun _ => True

theorem distinction_is_active : demand distinction := True.intro

theorem current_does_not_express : Not (Expresses current distinction) := by
  intro separation
  exact separation rfl

theorem current_is_not_exact : Not (HasExactDeclaredSemantics current) :=
  unexpressed_distinction_refutes_exact_declared_semantics
    current distinction current_does_not_express

/-- A concrete member of the full same-carrier repair scope. -/
def identityRepair : SameCarrierRepairCandidate current where
  repairedEncode := current.encode
  repairedCarrierTransition := current.carrierTransition
  repairedDecoder := current.decodeReceiverEffect

/-- This scope includes all repair records retaining the old Unit carrier. -/
def repairSearch : RepairSearchClass current where
  Candidate := SameCarrierRepairCandidate current
  repair := fun candidate => candidate
  architecturePreserving := fun _ => True
  admissible := fun _ => True

theorem repair_scope_is_inhabited :
    Exists fun candidate : repairSearch.Candidate =>
      repairSearch.architecturePreserving candidate ∧
        repairSearch.admissible candidate := by
  exact ⟨identityRepair, True.intro, True.intro⟩

/-- Changing the Unit encoder, transition, or decoder cannot split two states. -/
theorem every_same_carrier_repair_fails
    (candidate : SameCarrierRepairCandidate current) :
    Not (Resolves candidate distinction) := by
  intro separation
  have collision : candidate.repairedEncode distinction.left =
      candidate.repairedEncode distinction.right :=
    @Subsingleton.elim Unit inferInstance _ _
  exact (resolves_iff_repaired_encoder_separates candidate distinction).mp
    separation collision

theorem repair_scope_is_exhausted :
    Not (RepairableWithin repairSearch distinction) := by
  exact exhaustive_scoped_no_repair repairSearch distinction
    (fun candidate _ _ => every_same_carrier_repair_fails candidate)

theorem pressure_is_inhabited :
    IrreduciblePressureWithin repairSearch demand distinction :=
  irreduciblePressureWithin_intro repairSearch demand distinction
    distinction_is_active current_does_not_express repair_scope_is_exhausted

/-- The inherited construction keeps the old Unit component and adjoins Bool. -/
def fullStateLift : LiftCandidate current := universalStateLift current

/-- Exactness is proved for this declaration, not inferred from resolution. -/
theorem full_state_lift_is_exact :
    HasExactDeclaredSemantics fullStateLift.toCurrentK := by
  constructor
  · intro state receiver
    rfl
  · intro state
    rfl

/-- One explicitly admitted candidate, using the inherited full-state search. -/
def liftSearch : LiftSearchClass current := universalStateLiftSearch current

theorem every_admitted_lift_is_exact :
    forall candidate, liftSearch.constraints candidate ->
      HasExactDeclaredSemantics (liftSearch.lift candidate).toCurrentK := by
  intro candidate admitted
  exact full_state_lift_is_exact

/-- A checked member, including admission and resolution proofs. -/
def member : MSpaceFiber liftSearch distinction :=
  mSpaceWitness liftSearch distinction () True.intro
    (universalStateLift_resolves distinction)

theorem lift_scope_is_available : AvailableLiftWithin liftSearch distinction :=
  ⟨member⟩

/-- Zero is an arbitrary declared rank; no physical dimension is represented. -/
def rank : TransitionRank liftSearch := fun _ => 0

/-- An actual minimizer with a proof against every member of the whole fiber. -/
def argmin : NatRankedMSpaceArgmin liftSearch distinction rank where
  minimizer := member
  minimalWithinFiber := fun _ => Nat.le_refl 0

/-- The selected lift has both a separated old collision and exact semantics. -/
def exactCertificate :
    ExactStrictSuccessorCertificate current
      (liftSearch.lift argmin.minimizer.1) where
  strictSuccessor := {
    projection := fullStateLift.encoderProjection
    transitionFactorsOnEncoded := fullStateLift.projectTransitionOnEncoded
    strictWitness := {
      left := distinction.left
      right := distinction.right
      oldCollision := rfl
      newSeparation :=
        (liftResolves_iff_encoder_separates fullStateLift distinction).mp
          (universalStateLift_resolves distinction)
    }
  }
  exactSemantics := full_state_lift_is_exact

/-- The positive branch is witnessed directly, independently of route selection. -/
theorem exact_ranked_refinement_branch_is_inhabited :
    Exists fun selected : NatRankedMSpaceArgmin liftSearch distinction rank =>
      Nonempty (ExactStrictSuccessorCertificate current
        (liftSearch.lift selected.minimizer.1)) := by
  exact ⟨argmin, ⟨exactCertificate⟩⟩

/-- All substantive positive-route obligations hold for the same concrete data. -/
theorem joint_positive_witness :
    (Exists fun candidate : repairSearch.Candidate =>
      repairSearch.architecturePreserving candidate ∧
        repairSearch.admissible candidate) ∧
    IrreduciblePressureWithin repairSearch demand distinction ∧
    (forall candidate, liftSearch.constraints candidate ->
      HasExactDeclaredSemantics (liftSearch.lift candidate).toCurrentK) ∧
    (Exists fun selected : NatRankedMSpaceArgmin liftSearch distinction rank =>
      Nonempty (ExactStrictSuccessorCertificate current
        (liftSearch.lift selected.minimizer.1))) := by
  exact ⟨repair_scope_is_inhabited, pressure_is_inhabited,
    every_admitted_lift_is_exact, exact_ranked_refinement_branch_is_inhabited⟩

/-- The inherited primary theorem applies with all formal-instance premises proved. -/
theorem primary_trichotomy_is_instantiated :
    ScopedExactContinuationTrichotomy repairSearch distinction liftSearch rank :=
  scoped_first_principle_exact_continuation_trichotomy
    repairSearch demand distinction distinction_is_active current_does_not_express
    liftSearch rank every_admitted_lift_is_exact

/-- Strict kernel refinement and shift stability hold for this actual selection. -/
theorem selected_refinement_and_shift_stability :
    EncoderKernelStrictlyRefines
        (liftSearch.lift argmin.minimizer.1).encode current.encode ∧
      (currentKTrajectoryProjectionFamily
        (liftSearch.lift argmin.minimizer.1).toCurrentK).DynamicsCommute
        (liftSearch.lift argmin.minimizer.1).toCurrentK.stateTransition
        shiftCausalTrajectory :=
  first_principle_refinement_branch_properties argmin exactCertificate

theorem bounded_collapse_is_excluded :
    Not (BoundedRepresentationalCollapseWithin
      repairSearch liftSearch distinction) := by
  intro collapse
  exact collapse (Or.inr lift_scope_is_available)

end OCScientificExtensions.FirstPrincipleBoolWitness
