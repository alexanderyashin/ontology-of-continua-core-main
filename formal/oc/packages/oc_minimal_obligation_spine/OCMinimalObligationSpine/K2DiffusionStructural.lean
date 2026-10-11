import OCMinimalObligationSpine.MinimalTransition
import OCMinimalObligationSpine.StrictSuccessor

namespace OCMinimalObligationSpine.K2DiffusionStructural

/-!
# A bounded K2 diffusion instantiation of the structural OC chain

Scientific scope: `STRUCTURAL_LAW_LEVEL_K2_INSTANTIATION`.

The source model is the single-snapshot variance signature

    s(t, D, b) = 2 * D * t + b.

This file proves, for one explicit two-state parameter domain, that two distinct
timestamps collide in the old scalar signature; no deterministic
postprocessing of that scalar can split the collision; a declared two-member
lift class contains resolving exact representations; a declared natural-number
cost selects a minimum; and the selected lift is a strict successor preserving
the old signature as a projection.

The result is deliberately not a Gaussian-measure theorem, real-data
validation, a five-sigma result, or a proof of universal physical OC.  It also
does not use the erroneous inference that the Moore--Penrose pseudoinverse of a
rank-deficient joint Fisher matrix supplies a finite marginal CRLB for an
unidentifiable timestamp.  A pseudoinverse controls estimable directions only
after the estimability conditions are stated.  Here the non-identifiability
claim is established directly by an exact signature collision.
-/

/-- Machine-readable boundary label for downstream evidence accounting. -/
def scientificScope : String := "STRUCTURAL_LAW_LEVEL_K2_INSTANTIATION"

/-- The bounded parameter domain used by this structural witness. -/
inductive DiffusionState where
  | earlyFast
  | lateSlow
deriving DecidableEq, Repr

def timestamp : DiffusionState -> Nat
  | .earlyFast => 1
  | .lateSlow => 2

def diffusivity : DiffusionState -> Nat
  | .earlyFast => 2
  | .lateSlow => 1

def varianceFloor : DiffusionState -> Nat
  | .earlyFast => 0
  | .lateSlow => 0

/-- The exact arithmetic signature `s = 2Dt + b` used by the old K. -/
def varianceSignature (state : DiffusionState) : Nat :=
  2 * diffusivity state * timestamp state + varianceFloor state

/--
The old K exposes only the scalar variance signature while the receiver asks
for timestamp.  Its decoder is intentionally declared but not assumed exact.
-/
def diffusionVarianceK : CurrentK where
  State := DiffusionState
  Receiver := Unit
  Effect := Nat
  Carrier := Nat
  stateTransition := id
  receiverEffect := fun state _ => timestamp state
  encode := varianceSignature
  carrierTransition := id
  decodeReceiverEffect := fun signature _ => signature

/-- `(t,D,b)=(1,2,0)` and `(2,1,0)` have the same signature `s=4`. -/
theorem variance_signature_collision :
    diffusionVarianceK.encode .earlyFast =
      diffusionVarianceK.encode .lateSlow := by
  rfl

/-- The same two states demand different timestamp effects. -/
def timestampDistinction : TrajectoryDistinction diffusionVarianceK where
  left := .earlyFast
  right := .lateSlow
  step := 0
  receiver := ()
  effect_ne := by
    change (1 : Nat) ≠ 2
    decide

theorem old_k_does_not_express_timestamp :
    Not (Expresses diffusionVarianceK timestampDistinction) := by
  intro separation
  exact separation variance_signature_collision

/-- The scoped same-K repair class contains only postprocessings of old `s`. -/
def postprocessingRepairSearch : RepairSearchClass diffusionVarianceK where
  Candidate := Nat -> Nat
  repair := fun postprocess =>
    SameCarrierRepairCandidate.postcomposeEncoder
      diffusionVarianceK postprocess
  architecturePreserving := fun _ => True
  admissible := fun _ => True

/-- No deterministic postprocessing of `s` can split the existing collision. -/
theorem no_postprocessing_repair :
    Not (RepairableWithin postprocessingRepairSearch timestampDistinction) := by
  apply exhaustive_scoped_no_repair
  intro postprocess _ _
  exact postcomposition_cannot_resolve_collision
    diffusionVarianceK postprocess timestampDistinction
    variance_signature_collision

/-- Timestamp separation is the explicit active demand in this instantiation. -/
def timestampDemand : ActiveDemand diffusionVarianceK :=
  fun distinction =>
    timestamp distinction.left ≠ timestamp distinction.right

theorem timestamp_demand_is_active :
    timestampDemand timestampDistinction := by
  change (1 : Nat) ≠ 2
  decide

/-- Scoped pressure: active timestamp demand, old collision, no postprocess repair. -/
theorem postprocessing_irreducible_pressure :
    IrreduciblePressureWithin
      postprocessingRepairSearch timestampDemand timestampDistinction := by
  exact ⟨timestamp_demand_is_active,
    old_k_does_not_express_timestamp,
    no_postprocessing_repair⟩

/-- Two explicit candidate channels in the declared lift search. -/
inductive LiftKind where
  | timestampChannel
  | diffusivityCalibration
deriving DecidableEq, Repr

/-- A finite calibration table on the bounded two-state domain. -/
def calibratedTimestamp : Nat -> Nat
  | 2 => 1
  | 1 => 2
  | _ => 0

/--
Both candidates retain old `s` in the first component.  One adds timestamp
directly; the other adds calibrated diffusivity and recovers timestamp using the
declared finite calibration table.  This table is not a real instrument model.
-/
def diffusionLift : LiftKind -> LiftCandidate diffusionVarianceK
  | .timestampChannel => {
      Carrier := Nat × Nat
      encode := fun state => (varianceSignature state, timestamp state)
      carrierTransition := id
      decodeReceiverEffect := fun carrier _ => carrier.2
      project := Prod.fst
      projectEncode := by intro state; rfl
      projectTransitionOnEncoded := by intro state; rfl
    }
  | .diffusivityCalibration => {
      Carrier := Nat × Nat
      encode := fun state => (varianceSignature state, diffusivity state)
      carrierTransition := id
      decodeReceiverEffect := fun carrier _ => calibratedTimestamp carrier.2
      project := Prod.fst
      projectEncode := by intro state; rfl
      projectTransitionOnEncoded := by intro state; rfl
    }

theorem timestamp_lift_has_exact_declared_semantics :
    HasExactDeclaredSemantics
      (diffusionLift .timestampChannel).toCurrentK := by
  constructor
  · intro state receiver
    cases state <;> cases receiver <;> rfl
  · intro state
    cases state <;> rfl

theorem calibration_lift_has_exact_declared_semantics :
    HasExactDeclaredSemantics
      (diffusionLift .diffusivityCalibration).toCurrentK := by
  constructor
  · intro state receiver
    cases state <;> cases receiver <;> rfl
  · intro state
    cases state <;> rfl

/-- The declared M-search admits exactly the two exact candidates above. -/
def diffusionLiftSearch : LiftSearchClass diffusionVarianceK where
  Candidate := LiftKind
  lift := diffusionLift
  constraints := fun candidate =>
    HasExactDeclaredSemantics (diffusionLift candidate).toCurrentK

theorem timestamp_lift_resolves :
    LiftResolves (diffusionLift .timestampChannel) timestampDistinction := by
  apply (liftResolves_iff_encoder_separates
    (diffusionLift .timestampChannel) timestampDistinction).2
  change ((4, 1) : Nat × Nat) ≠ (4, 2)
  decide

theorem calibration_lift_resolves :
    LiftResolves
      (diffusionLift .diffusivityCalibration) timestampDistinction := by
  apply (liftResolves_iff_encoder_separates
    (diffusionLift .diffusivityCalibration) timestampDistinction).2
  change ((4, 2) : Nat × Nat) ≠ (4, 1)
  decide

def timestampMember :
    MSpaceFiber diffusionLiftSearch timestampDistinction :=
  mSpaceWitness diffusionLiftSearch timestampDistinction
    .timestampChannel
    timestamp_lift_has_exact_declared_semantics
    timestamp_lift_resolves

def calibrationMember :
    MSpaceFiber diffusionLiftSearch timestampDistinction :=
  mSpaceWitness diffusionLiftSearch timestampDistinction
    .diffusivityCalibration
    calibration_lift_has_exact_declared_semantics
    calibration_lift_resolves

theorem declared_mSpace_is_available :
    AvailableLiftWithin diffusionLiftSearch timestampDistinction := by
  exact ⟨timestampMember⟩

/-- Complete enumeration of this declared two-member M-fiber. -/
def finiteDiffusionMSpace :
    FiniteDeclaredMSpace diffusionLiftSearch timestampDistinction where
  members := [timestampMember, calibrationMember]
  complete := by
    intro member
    rcases member with ⟨candidate, conditions⟩
    cases candidate with
    | timestampChannel =>
        have same :
            (⟨.timestampChannel, conditions⟩ :
              MSpaceFiber diffusionLiftSearch timestampDistinction) =
              timestampMember := by
          apply Subtype.ext
          rfl
        simp [same]
    | diffusivityCalibration =>
        have same :
            (⟨.diffusivityCalibration, conditions⟩ :
              MSpaceFiber diffusionLiftSearch timestampDistinction) =
              calibrationMember := by
          apply Subtype.ext
          rfl
        simp [same]

/-- A declared structural cost only; it has no empirical resource units. -/
def transitionCost : TransitionRank diffusionLiftSearch
  | .timestampChannel => 1
  | .diffusivityCalibration => 2

/-- Explicit argmin witness: the timestamp channel has declared cost `1`. -/
def timestampArgmin :
    FiniteMSpaceArgmin finiteDiffusionMSpace transitionCost where
  minimizer := timestampMember
  listed := by simp [finiteDiffusionMSpace]
  minimalWithinDeclaredFiber := by
    intro other
    rcases other with ⟨candidate, conditions⟩
    cases candidate with
    | timestampChannel =>
        change 1 ≤ 1
        exact Nat.le_refl 1
    | diffusivityCalibration =>
        change 1 ≤ 2
        decide

/-- The generic finite-M-space theorem independently reconstructs existence. -/
theorem generic_argmin_exists :
    Nonempty
      (FiniteMSpaceArgmin finiteDiffusionMSpace transitionCost) :=
  finite_declared_mSpace_argmin_exists
    diffusionLiftSearch timestampDistinction finiteDiffusionMSpace
    transitionCost declared_mSpace_is_available

/--
The selected finite-argmin member receives the shared F09 strict-successor
certificate.  This is conditional on the explicit member and the scoped
postprocessing pressure proof.  It does not exclude richer same-carrier
encoders outside `postprocessingRepairSearch`, and it carries no physical or
empirical improvement claim.  The dynamics are identity dynamics and the cost
is the arbitrary declared natural-number ranking above.
-/
theorem argminStrictSuccessor :
    Nonempty
      (StrictSuccessorCertificate diffusionVarianceK
        (diffusionLiftSearch.lift timestampArgmin.minimizer.1)) := by
  exact strictSuccessorCertificate_of_pressure_mSpaceMember
    postprocessing_irreducible_pressure diffusionLiftSearch
    timestampArgmin.minimizer

theorem argmin_successor_preserves_old_signature
    (state : DiffusionState) :
  (diffusionLiftSearch.lift timestampArgmin.minimizer.1).project
        ((diffusionLiftSearch.lift timestampArgmin.minimizer.1).encode state) =
      diffusionVarianceK.encode state := by
  exact
    (diffusionLiftSearch.lift
      timestampArgmin.minimizer.1).projectEncode state

theorem argmin_successor_preserves_old_transition_on_encoded
    (state : DiffusionState) :
  (diffusionLiftSearch.lift timestampArgmin.minimizer.1).project
        ((diffusionLiftSearch.lift timestampArgmin.minimizer.1).carrierTransition
          ((diffusionLiftSearch.lift timestampArgmin.minimizer.1).encode state)) =
      diffusionVarianceK.carrierTransition
        (diffusionVarianceK.encode state) := by
  exact
    (diffusionLiftSearch.lift
      timestampArgmin.minimizer.1).projectTransitionOnEncoded state

theorem argmin_successor_separates_collision :
    (diffusionLiftSearch.lift timestampArgmin.minimizer.1).encode
        .earlyFast ≠
      (diffusionLiftSearch.lift timestampArgmin.minimizer.1).encode
        .lateSlow := by
  exact (liftResolves_iff_encoder_separates
    (diffusionLiftSearch.lift timestampArgmin.minimizer.1)
    timestampDistinction).mp
      (finiteArgmin_resolves timestampArgmin)

theorem argmin_successor_not_reverse_projection :
    Not
      (Nonempty
        (EncoderProjection
          (diffusionLiftSearch.lift timestampArgmin.minimizer.1).encode
          diffusionVarianceK.encode)) := by
  rcases argminStrictSuccessor with ⟨certificate⟩
  exact certificate.not_reverse_projection

theorem argmin_successor_not_carrier_relabeling :
    Not
      (Nonempty
        (EncoderRelabeling
          diffusionVarianceK.encode
          (diffusionLiftSearch.lift timestampArgmin.minimizer.1).encode)) := by
  rcases argminStrictSuccessor with ⟨certificate⟩
  exact certificate.not_relabeling

/--
Publication-facing K2 Fisher-comparator package.

The deterministic Fisher replay is allowed to support the K2 structural story
only when it is tied to the exact Lean facts that make the comparator useful:
the old scalar variance signature collides, timestamp recovery is not expressed
by the old K, postprocessing cannot repair that collision inside the scoped
same-K class, and the finite M-space successor separates the collision while
preserving the old signature as a projection.
-/
structure K2FisherComparatorPublicationPackage : Prop where
  old_variance_signature_collides :
    diffusionVarianceK.encode .earlyFast =
      diffusionVarianceK.encode .lateSlow
  old_k_timestamp_not_expressed :
    Not (Expresses diffusionVarianceK timestampDistinction)
  no_scoped_postprocessing_repair :
    Not (RepairableWithin postprocessingRepairSearch timestampDistinction)
  strict_successor_available :
    Nonempty
      (StrictSuccessorCertificate diffusionVarianceK
        (diffusionLiftSearch.lift timestampArgmin.minimizer.1))
  strict_successor_separates_collision :
    (diffusionLiftSearch.lift timestampArgmin.minimizer.1).encode
        .earlyFast ≠
      (diffusionLiftSearch.lift timestampArgmin.minimizer.1).encode
        .lateSlow
  strict_successor_preserves_old_signature :
    ∀ state : DiffusionState,
      (diffusionLiftSearch.lift timestampArgmin.minimizer.1).project
          ((diffusionLiftSearch.lift timestampArgmin.minimizer.1).encode state) =
        diffusionVarianceK.encode state

/--
The K2 Fisher-comparator obligation is closed as a structural publication
artifact: it may be published as a deterministic method/comparator witness for
why a scalar variance snapshot is insufficient and why a K2 lift is required.
-/
theorem k2_fisher_comparator_publication_package_closed :
    K2FisherComparatorPublicationPackage := by
  exact {
    old_variance_signature_collides := variance_signature_collision
    old_k_timestamp_not_expressed := old_k_does_not_express_timestamp
    no_scoped_postprocessing_repair := no_postprocessing_repair
    strict_successor_available := argminStrictSuccessor
    strict_successor_separates_collision := argmin_successor_separates_collision
    strict_successor_preserves_old_signature := argmin_successor_preserves_old_signature
  }

end OCMinimalObligationSpine.K2DiffusionStructural
