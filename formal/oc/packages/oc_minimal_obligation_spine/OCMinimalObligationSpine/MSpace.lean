import OCMinimalObligationSpine.IrreduciblePressure

namespace OCMinimalObligationSpine

universe uLiftCarrier uLiftCandidate uRepairCandidate

/--
A representational lift of `K`.  It keeps the substrate state, receiver, effect,
and state-transition types fixed, but may use a richer carrier.  `project`
exhibits the old carrier as a lossful view of the candidate carrier.  This is a
structural interface only: it contains no physical-space or axis-existence
claim.
-/
structure LiftCandidate (K : CurrentK) where
  Carrier : Type uLiftCarrier
  encode : K.State -> Carrier
  carrierTransition : Carrier -> Carrier
  decodeReceiverEffect : Carrier -> K.Receiver -> K.Effect
  project : Carrier -> K.Carrier
  projectEncode : forall state, project (encode state) = K.encode state
  projectTransitionOnEncoded : forall state,
    project (carrierTransition (encode state)) =
      K.carrierTransition (K.encode state)

/-- The current-K interface induced by a candidate lift. -/
def LiftCandidate.toCurrentK
    {K : CurrentK} (candidate : LiftCandidate.{uLiftCarrier} K) : CurrentK where
  State := K.State
  Receiver := K.Receiver
  Effect := K.Effect
  Carrier := candidate.Carrier
  stateTransition := K.stateTransition
  receiverEffect := K.receiverEffect
  encode := candidate.encode
  carrierTransition := candidate.carrierTransition
  decodeReceiverEffect := candidate.decodeReceiverEffect

/-- The same certified trajectory distinction, viewed in the lifted carrier. -/
def LiftCandidate.rebaseDistinction
    {K : CurrentK}
    (candidate : LiftCandidate.{uLiftCarrier} K)
    (d : TrajectoryDistinction K) :
    TrajectoryDistinction candidate.toCurrentK where
  left := d.left
  right := d.right
  step := d.step
  receiver := d.receiver
  effect_ne := d.effect_ne

/-- A lift resolves `d` when its encoder separates the distinguished states. -/
def LiftResolves
    {K : CurrentK}
    (candidate : LiftCandidate.{uLiftCarrier} K)
    (d : TrajectoryDistinction K) : Prop :=
  Expresses candidate.toCurrentK (candidate.rebaseDistinction d)

theorem liftResolves_iff_encoder_separates
    {K : CurrentK}
    (candidate : LiftCandidate.{uLiftCarrier} K)
    (d : TrajectoryDistinction K) :
    LiftResolves candidate d <->
      Not (candidate.encode d.left = candidate.encode d.right) := by
  rfl

/-- Every candidate lift refines the old encoder kernel. -/
theorem lift_collision_implies_current_collision
    {K : CurrentK}
    (candidate : LiftCandidate.{uLiftCarrier} K)
    {left right : K.State}
    (collision : candidate.encode left = candidate.encode right) :
    K.encode left = K.encode right := by
  calc
    K.encode left = candidate.project (candidate.encode left) :=
      (candidate.projectEncode left).symm
    _ = candidate.project (candidate.encode right) := by rw [collision]
    _ = K.encode right := candidate.projectEncode right

/--
A frozen, auditable class of lift candidates.  `constraints` may encode formal
resource, conservation, causal, or domain restrictions, but those restrictions
must be supplied and proved by the caller; this structure does not manufacture
them.
-/
structure LiftSearchClass (K : CurrentK) where
  Candidate : Type uLiftCandidate
  lift : Candidate -> LiftCandidate.{uLiftCarrier} K
  constraints : Candidate -> Prop

/-- The exact dependent M-fiber over a current K and one demanded distinction. -/
def MSpaceFiber
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K) :=
  {candidate : search.Candidate //
    search.constraints candidate /\ LiftResolves (search.lift candidate) d}

/-- Availability is constructive non-emptiness inside the declared lift class. -/
def AvailableLiftWithin
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K) : Prop :=
  Nonempty (MSpaceFiber search d)

/-- A checked candidate constructs a positive M-space membership witness. -/
def mSpaceWitness
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K)
    (candidate : search.Candidate)
    (constraintsHold : search.constraints candidate)
    (resolves : LiftResolves (search.lift candidate) d) :
    MSpaceFiber search d :=
  ⟨candidate, constraintsHold, resolves⟩

theorem availableLiftWithin_of_witness
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K)
    (candidate : search.Candidate)
    (constraintsHold : search.constraints candidate)
    (resolves : LiftResolves (search.lift candidate) d) :
    AvailableLiftWithin search d := by
  exact ⟨mSpaceWitness search d candidate constraintsHold resolves⟩

theorem mSpaceMember_constraints
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {d : TrajectoryDistinction K}
    (member : MSpaceFiber search d) :
    search.constraints member.1 :=
  member.2.1

theorem mSpaceMember_resolves
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {d : TrajectoryDistinction K}
    (member : MSpaceFiber search d) :
    LiftResolves (search.lift member.1) d :=
  member.2.2

/--
Scoped exhaustive negative result.  It says only that the declared class has no
admissible resolving lift; it says nothing about candidates outside that class,
physical space, or collapse.
-/
theorem exhaustive_scoped_no_lift
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K)
    (everyCandidateFails : forall candidate,
      search.constraints candidate ->
        Not (LiftResolves (search.lift candidate) d)) :
    Not (AvailableLiftWithin search d) := by
  intro available
  obtain ⟨member⟩ := available
  exact everyCandidateFails member.1 member.2.1 member.2.2

theorem not_availableLiftWithin_iff_every_scoped_candidate_fails
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K) :
    Not (AvailableLiftWithin search d) <->
      forall candidate,
        search.constraints candidate ->
          Not (LiftResolves (search.lift candidate) d) := by
  constructor
  · intro unavailable candidate constraintsHold resolves
    exact unavailable
      ⟨mSpaceWitness search d candidate constraintsHold resolves⟩
  · exact exhaustive_scoped_no_lift search d

/--
After scoped irreducible pressure, an M-fiber member supplies a strict local
representational witness for `d`: old K does not express `d`, while the lift
does.  This still does not imply physical axis birth.
-/
theorem mSpace_member_strictly_resolves_pressure_distinction
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (member : MSpaceFiber liftSearch d) :
    Not (Expresses K d) /\
      LiftResolves (liftSearch.lift member.1) d := by
  exact ⟨pressure.2.1, member.2.2⟩

/-- A valid same-K repair contradicts the pressure premise, not the M-fiber. -/
theorem repair_witness_blocks_pressure_before_mSpace_routing
    {K : CurrentK}
    (repairSearch : RepairSearchClass.{uRepairCandidate} K)
    (activeDemand : ActiveDemand K)
    (d : TrajectoryDistinction K)
    (repairable : RepairableWithin repairSearch d) :
    Not (IrreduciblePressureWithin repairSearch activeDemand d) :=
  repairable_blocks_pressure repairSearch activeDemand d repairable

end OCMinimalObligationSpine
