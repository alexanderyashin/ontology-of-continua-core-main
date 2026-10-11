import OCMinimalObligationSpine.MSpace

namespace OCScientificExtensions

open OCMinimalObligationSpine

universe uLiftCarrier uLiftCandidate

/-!
# Exact semantics, constraint admission and scoped lift availability

This is a separate scientific extension outside the inherited frozen 992-file
corpus. Its compilation and axiom qualification require a separate receipt.
The inherited first-principle theorem does not need this derived bridge to be
valid; the bridge makes the meaning of its uniform exactness premise explicit.

Admission here means satisfaction of the supplied mathematical lift constraints.
The equivalence is relative to one declared search class and one certified
trajectory distinction. It introduces no rank, physical unit, empirical law,
algorithm-performance claim or authority to admit a real-world operation.

Exactness uses the declared decoder and encoded transition of the selected lift.
Resolving a distinction alone is weaker. The concrete Bool/Unit counterexample
below has an admitted structural lift but no resolving fibre, showing why the
uniform exactness premise cannot simply be omitted.
-/

/--
An exact lift expresses the same certified distinction rebased to its CurrentK.
This reuses the inherited exactness-to-expression theorem; no new observation,
candidate selection or assumption about physical realizability is introduced.
-/
theorem exact_lift_resolves_certified_distinction
    {K : CurrentK}
    (candidate : LiftCandidate.{uLiftCarrier} K)
    (d : TrajectoryDistinction K)
    (exactSemantics : HasExactDeclaredSemantics candidate.toCurrentK) :
    LiftResolves candidate d := by
  exact exact_declared_semantics_expresses
    candidate.toCurrentK exactSemantics (candidate.rebaseDistinction d)

/--
With exactness uniform over constraint-admitted candidates, availability is
equivalent to existence of an admitted candidate. The forward implication only
projects fibre membership; the reverse implication additionally uses exactness
to supply resolution of the certified distinction. No finiteness is required.
-/
theorem available_lift_iff_admitted_candidate_of_uniform_exactness
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K)
    (exactOfConstraints :
      forall candidate,
        search.constraints candidate ->
          HasExactDeclaredSemantics (search.lift candidate).toCurrentK) :
    AvailableLiftWithin search d ↔
      (Exists fun candidate : search.Candidate => search.constraints candidate) := by
  constructor
  · intro available
    obtain ⟨member⟩ := available
    exact ⟨member.1, member.2.1⟩
  · intro admitted
    obtain ⟨candidate, constraintsHold⟩ := admitted
    exact availableLiftWithin_of_witness
      search d candidate constraintsHold
      (exact_lift_resolves_certified_distinction
        (search.lift candidate) d (exactOfConstraints candidate constraintsHold))

/--
The negative form of the same scoped equivalence. Under the uniform exactness
contract, no available lift means that no candidate satisfies these constraints;
it does not assert absence of candidates outside the declared search class.
Both implications use negation introduction and the preceding equivalence.
-/
theorem no_available_lift_iff_no_admitted_candidate_of_uniform_exactness
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K)
    (exactOfConstraints :
      forall candidate,
        search.constraints candidate ->
          HasExactDeclaredSemantics (search.lift candidate).toCurrentK) :
    Not (AvailableLiftWithin search d) ↔
      Not (Exists fun candidate : search.Candidate => search.constraints candidate) := by
  constructor
  · intro noAvailable admitted
    exact noAvailable
      ((available_lift_iff_admitted_candidate_of_uniform_exactness
        search d exactOfConstraints).mpr admitted)
  · intro noAdmitted available
    exact noAdmitted
      ((available_lift_iff_admitted_candidate_of_uniform_exactness
        search d exactOfConstraints).mp available)

/-! ## Concrete counterexample when uniform exactness is omitted -/

/--
A Bool source with identity dynamics and a Unit carrier. The receiver effect is
the source Bool, while the decoder always returns false. Thus encoded dynamics
can be exact even though the declared receiver decoder loses information.
All fields are mathematical declarations, not empirical measurements.
-/
def lossyUnitCurrentK : CurrentK where
  State := Bool
  Receiver := Unit
  Effect := Bool
  Carrier := Unit
  stateTransition := fun state => state
  receiverEffect := fun state _ => state
  encode := fun _ => ()
  carrierTransition := fun carrier => carrier
  decodeReceiverEffect := fun _ _ => false

/-- A concrete receiver distinction at step zero, before any state transition. -/
def lossyUnitDistinction : TrajectoryDistinction lossyUnitCurrentK where
  left := false
  right := true
  step := 0
  receiver := ()
  effect_ne := by
    change false ≠ true
    intro impossible
    cases impossible

/--
A real structural lift that retains the Unit carrier and its identity transition
and projection. Both required factorization laws hold by reflexivity. This
candidate has no additional distinction-resolving information.
-/
def lossyUnitIdentityLift : LiftCandidate lossyUnitCurrentK where
  Carrier := Unit
  encode := fun _ => ()
  carrierTransition := fun carrier => carrier
  decodeReceiverEffect := fun _ _ => false
  project := fun carrier => carrier
  projectEncode := fun _ => rfl
  projectTransitionOnEncoded := fun _ => rfl

/-- A nonempty candidate class whose sole candidate is constraint-admitted. -/
def lossyUnitLiftSearch : LiftSearchClass lossyUnitCurrentK where
  Candidate := Unit
  lift := fun _ => lossyUnitIdentityLift
  constraints := fun _ => True

/-- The constant Unit encoder cannot separate the certified Bool distinction. -/
theorem lossy_unit_identity_lift_does_not_resolve :
    Not (LiftResolves lossyUnitIdentityLift lossyUnitDistinction) := by
  intro resolves
  exact resolves rfl

/-- Admission is genuinely inhabited, rather than obtained from an empty class. -/
theorem lossy_unit_search_admits_candidate :
    Exists fun candidate : lossyUnitLiftSearch.Candidate =>
      lossyUnitLiftSearch.constraints candidate := by
  exact ⟨(), True.intro⟩

/-- Every putative fibre member would contradict the explicit failure to resolve. -/
theorem lossy_unit_search_has_no_available_lift :
    Not (AvailableLiftWithin lossyUnitLiftSearch lossyUnitDistinction) := by
  intro available
  obtain ⟨member⟩ := available
  exact lossy_unit_identity_lift_does_not_resolve member.2.2

/-- Exact semantics is excluded by the inherited exactness-to-expression law. -/
theorem lossy_unit_identity_lift_not_exact :
    Not (HasExactDeclaredSemantics lossyUnitIdentityLift.toCurrentK) := by
  intro exactSemantics
  exact lossy_unit_identity_lift_does_not_resolve
    (exact_lift_resolves_certified_distinction
      lossyUnitIdentityLift lossyUnitDistinction exactSemantics)

/-- The admitted candidate prevents the uniform exactness contract from holding. -/
theorem lossy_unit_search_not_uniformly_exact :
    Not (forall candidate : lossyUnitLiftSearch.Candidate,
      lossyUnitLiftSearch.constraints candidate ->
        HasExactDeclaredSemantics (lossyUnitLiftSearch.lift candidate).toCurrentK) := by
  intro exactOfConstraints
  exact lossy_unit_identity_lift_not_exact (exactOfConstraints () True.intro)

/--
Concrete failure of admission implying availability without uniform exactness:
the candidate class is nonempty, its constraints are True, its actual structural
lift cannot resolve the distinction, and its uniform exactness contract fails.
This is a logical counterexample, not a physical no-lift or collapse result.
-/
theorem admitted_candidate_without_uniform_exactness_need_not_supply_available_lift :
    (Exists fun candidate : lossyUnitLiftSearch.Candidate =>
      lossyUnitLiftSearch.constraints candidate) ∧
    Not (AvailableLiftWithin lossyUnitLiftSearch lossyUnitDistinction) ∧
    Not (forall candidate : lossyUnitLiftSearch.Candidate,
      lossyUnitLiftSearch.constraints candidate ->
        HasExactDeclaredSemantics (lossyUnitLiftSearch.lift candidate).toCurrentK) := by
  exact ⟨lossy_unit_search_admits_candidate,
    lossy_unit_search_has_no_available_lift,
    lossy_unit_search_not_uniformly_exact⟩

end OCScientificExtensions
