import OCMinimalObligationSpine.CurrentK

namespace OCMinimalObligationSpine

universe uCandidate

/--
A proposed repair that keeps the state, receiver, effect, and carrier types of
`K`, together with its source-level transition and receiver-effect semantics.

This record is only a candidate.  In particular, merely using the same carrier
type does not prove that a proposal preserves the architecture or the already
accepted semantics of `K`; those obligations are explicit in
`RepairSearchClass`.
-/
structure SameCarrierRepairCandidate (K : CurrentK) where
  repairedEncode : K.State -> K.Carrier
  repairedCarrierTransition : K.Carrier -> K.Carrier
  repairedDecoder : K.Carrier -> K.Receiver -> K.Effect

/-- Interpret a same-carrier candidate as a current-K declaration. -/
def SameCarrierRepairCandidate.toCurrentK
    {K : CurrentK}
    (candidate : SameCarrierRepairCandidate K) : CurrentK where
  State := K.State
  Receiver := K.Receiver
  Effect := K.Effect
  Carrier := K.Carrier
  stateTransition := K.stateTransition
  receiverEffect := K.receiverEffect
  encode := candidate.repairedEncode
  carrierTransition := candidate.repairedCarrierTransition
  decodeReceiverEffect := candidate.repairedDecoder

/--
The same concrete distinction, viewed under a candidate whose source-level
dynamics and receiver effects are definitionally unchanged.
-/
def SameCarrierRepairCandidate.rebaseDistinction
    {K : CurrentK}
    (candidate : SameCarrierRepairCandidate K)
    (d : TrajectoryDistinction K) :
    TrajectoryDistinction candidate.toCurrentK where
  left := d.left
  right := d.right
  step := d.step
  receiver := d.receiver
  effect_ne := d.effect_ne

/-- A candidate resolves `d` exactly when its repaired encoder separates it. -/
def Resolves
    {K : CurrentK}
    (candidate : SameCarrierRepairCandidate K)
    (d : TrajectoryDistinction K) : Prop :=
  Expresses candidate.toCurrentK (candidate.rebaseDistinction d)

theorem resolves_iff_repaired_encoder_separates
    {K : CurrentK}
    (candidate : SameCarrierRepairCandidate K)
    (d : TrajectoryDistinction K) :
    Resolves candidate d <->
      Not (candidate.repairedEncode d.left = candidate.repairedEncode d.right) := by
  rfl

/--
A declared and therefore auditable scope of repairs.  The two predicates are
kept separate: architecture preservation says that this is still a repair of
the same K, while admissibility can enforce preservation of prior commitments,
hard constraints, held-out validation, or any other frozen scientific policy.
-/
structure RepairSearchClass (K : CurrentK) where
  Candidate : Type uCandidate
  repair : Candidate -> SameCarrierRepairCandidate K
  architecturePreserving : Candidate -> Prop
  admissible : Candidate -> Prop

/--
Repairability is existential only within the explicitly declared search class.
It is not an assertion about every imaginable representation change.
-/
def RepairableWithin
    {K : CurrentK}
    (search : RepairSearchClass.{uCandidate} K)
    (d : TrajectoryDistinction K) : Prop :=
  exists candidate,
    search.architecturePreserving candidate /\
      search.admissible candidate /\
        Resolves (search.repair candidate) d

/-- A concrete checked witness constructively establishes scoped repairability. -/
theorem repairableWithin_of_constructive_witness
    {K : CurrentK}
    (search : RepairSearchClass.{uCandidate} K)
    (d : TrajectoryDistinction K)
    (candidate : search.Candidate)
    (preservesArchitecture : search.architecturePreserving candidate)
    (isAdmissible : search.admissible candidate)
    (resolves : Resolves (search.repair candidate) d) :
    RepairableWithin search d := by
  exact ⟨candidate, preservesArchitecture, isAdmissible, resolves⟩

/--
If every architecture-preserving and admissible member of the declared class
fails, then there is no repair within that class.
-/
theorem exhaustive_scoped_no_repair
    {K : CurrentK}
    (search : RepairSearchClass.{uCandidate} K)
    (d : TrajectoryDistinction K)
    (everyCandidateFails :
      forall candidate,
        search.architecturePreserving candidate ->
          search.admissible candidate ->
            Not (Resolves (search.repair candidate) d)) :
    Not (RepairableWithin search d) := by
  intro repairable
  obtain ⟨candidate, preservesArchitecture, isAdmissible, resolves⟩ := repairable
  exact everyCandidateFails candidate preservesArchitecture isAdmissible resolves

theorem not_repairableWithin_iff_every_scoped_candidate_fails
    {K : CurrentK}
    (search : RepairSearchClass.{uCandidate} K)
    (d : TrajectoryDistinction K) :
    Not (RepairableWithin search d) <->
      forall candidate,
        search.architecturePreserving candidate ->
          search.admissible candidate ->
            Not (Resolves (search.repair candidate) d) := by
  constructor
  · intro noRepair candidate preservesArchitecture isAdmissible resolves
    exact noRepair ⟨candidate, preservesArchitecture, isAdmissible, resolves⟩
  · intro everyCandidateFails
    exact exhaustive_scoped_no_repair search d everyCandidateFails

/--
The special candidate obtained by postcomposing the old encoder with a carrier
endomorphism.  No admissibility or exactness claim is attached to it.
-/
def SameCarrierRepairCandidate.postcomposeEncoder
    (K : CurrentK)
    (postprocess : K.Carrier -> K.Carrier) :
    SameCarrierRepairCandidate K where
  repairedEncode := fun state => postprocess (K.encode state)
  repairedCarrierTransition := K.carrierTransition
  repairedDecoder := K.decodeReceiverEffect

/-- A carrier postcomposition cannot split a collision already made by `K`. -/
theorem postcomposition_preserves_encoding_collision
    (K : CurrentK)
    (postprocess : K.Carrier -> K.Carrier)
    {left right : K.State}
    (collision : K.encode left = K.encode right) :
    postprocess (K.encode left) = postprocess (K.encode right) := by
  exact congrArg postprocess collision

theorem postcomposition_cannot_resolve_collision
    (K : CurrentK)
    (postprocess : K.Carrier -> K.Carrier)
    (d : TrajectoryDistinction K)
    (collision : K.encode d.left = K.encode d.right) :
    Not (Resolves (SameCarrierRepairCandidate.postcomposeEncoder K postprocess) d) := by
  intro resolves
  exact resolves (postcomposition_preserves_encoding_collision K postprocess collision)

/--
Constructive variant: even without converting `not (a != b)` into `a = b`, an
unexpressed distinction cannot be resolved by postcomposition alone.
-/
theorem postcomposition_cannot_resolve_unexpressed
    (K : CurrentK)
    (postprocess : K.Carrier -> K.Carrier)
    (d : TrajectoryDistinction K)
    (notExpressed : Not (Expresses K d)) :
    Not (Resolves (SameCarrierRepairCandidate.postcomposeEncoder K postprocess) d) := by
  intro resolves
  apply notExpressed
  intro collision
  exact resolves (postcomposition_preserves_encoding_collision K postprocess collision)

end OCMinimalObligationSpine
