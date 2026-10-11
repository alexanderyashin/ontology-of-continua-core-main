import OCMinimalObligationSpine.StrictSuccessor

namespace OCMinimalObligationSpine

universe
  uCandidate uObservation
  uLiftCarrier uLiftCandidate uRepairCandidate

/--
A transition rank that factors through a declared candidate observation.

The scientific declaration is split into two auditable maps:

* `observe` measures a candidate without receiving a demanded distinction,
  M-space membership proof, argmin result, or successor certificate;
* `score` maps that observation to a natural-number burden.

Lean cannot prove that a declaration was frozen before seeing domain results.
That temporal/provenance obligation belongs to the domain replay.  This type
does ensure that downstream selection consumes only the declared observation
surface.
-/
structure ObservableTransitionRanking
    (Candidate : Type uCandidate)
    (Observation : Type uObservation) where
  observe : Candidate -> Observation
  score : Observation -> Nat

/-- The natural rank induced by the declared observation and score maps. -/
def ObservableTransitionRanking.rank
    {Candidate : Type uCandidate}
    {Observation : Type uObservation}
    (ranking : ObservableTransitionRanking Candidate Observation) :
    Candidate -> Nat :=
  fun candidate => ranking.score (ranking.observe candidate)

/-- Candidates with equal declared observations receive equal ranks. -/
theorem ObservableTransitionRanking.rank_eq_of_observation_eq
    {Candidate : Type uCandidate}
    {Observation : Type uObservation}
    (ranking : ObservableTransitionRanking Candidate Observation)
    {left right : Candidate}
    (sameObservation : ranking.observe left = ranking.observe right) :
    ranking.rank left = ranking.rank right := by
  simp only [ObservableTransitionRanking.rank, sameObservation]

/-- Interpret an observable ranking as the existing F07 transition rank. -/
def ObservableTransitionRanking.toTransitionRank
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {Observation : Type uObservation}
    (ranking :
      ObservableTransitionRanking search.Candidate Observation) :
    TransitionRank search :=
  ranking.rank

/--
A two-stage bounded cost for replay-friendly lexicographic selection.

The primary burden has absolute precedence.  The secondary burden is required
to lie in `[0, secondaryBound]`, making the positional natural-number encoding
order-preserving for the declared lexicographic comparison.
-/
structure BoundedLexicographicCost
    (Observation : Type uObservation) where
  primaryBurden : Observation -> Nat
  secondaryBurden : Observation -> Nat
  secondaryBound : Nat
  secondary_le_bound :
    forall observation, secondaryBurden observation <= secondaryBound

/-- Positional encoding of the declared bounded lexicographic cost. -/
def BoundedLexicographicCost.score
    {Observation : Type uObservation}
    (cost : BoundedLexicographicCost Observation)
    (observation : Observation) : Nat :=
  cost.primaryBurden observation * (cost.secondaryBound + 1) +
    cost.secondaryBurden observation

/-- Strict two-stage lexicographic improvement. -/
def BoundedLexicographicCost.Better
    {Observation : Type uObservation}
    (cost : BoundedLexicographicCost Observation)
    (left right : Observation) : Prop :=
  cost.primaryBurden left < cost.primaryBurden right \/
    (cost.primaryBurden left = cost.primaryBurden right /\
      cost.secondaryBurden left < cost.secondaryBurden right)

/--
The positional natural score respects the declared bounded lexicographic
order.  Consequently the ordinary F07 Nat argmin can implement this two-stage
policy without a hidden tie-breaking oracle.
-/
theorem BoundedLexicographicCost.score_lt_of_better
    {Observation : Type uObservation}
    (cost : BoundedLexicographicCost Observation)
    {left right : Observation}
    (better : cost.Better left right) :
    cost.score left < cost.score right := by
  rcases better with primaryBetter | ⟨primaryEqual, secondaryBetter⟩
  · have secondaryBelowWidth :
        cost.secondaryBurden left < cost.secondaryBound + 1 :=
      Nat.lt_succ_iff.mpr (cost.secondary_le_bound left)
    have belowNextPrimary :
        cost.primaryBurden left * (cost.secondaryBound + 1) +
            cost.secondaryBurden left <
          cost.primaryBurden left * (cost.secondaryBound + 1) +
            (cost.secondaryBound + 1) :=
      Nat.add_lt_add_left secondaryBelowWidth _
    have nextPrimaryLe :
        cost.primaryBurden left + 1 <= cost.primaryBurden right :=
      Nat.succ_le_iff.mpr primaryBetter
    calc
      cost.score left <
          (cost.primaryBurden left + 1) *
            (cost.secondaryBound + 1) := by
              simpa
                [BoundedLexicographicCost.score, Nat.add_mul]
                using belowNextPrimary
      _ <= cost.primaryBurden right * (cost.secondaryBound + 1) :=
        Nat.mul_le_mul_right (cost.secondaryBound + 1) nextPrimaryLe
      _ <= cost.primaryBurden right * (cost.secondaryBound + 1) +
          cost.secondaryBurden right :=
        Nat.le_add_right _ _
      _ = cost.score right := by
        rfl
  · simp only [BoundedLexicographicCost.score]
    rw [primaryEqual]
    exact Nat.add_lt_add_left secondaryBetter _

/-- Build an observable transition ranking from a bounded lexicographic cost. -/
def ObservableTransitionRanking.ofBoundedLexicographic
    {Candidate : Type uCandidate}
    {Observation : Type uObservation}
    (observe : Candidate -> Observation)
    (cost : BoundedLexicographicCost Observation) :
    ObservableTransitionRanking Candidate Observation where
  observe := observe
  score := cost.score

/--
One constructive, observation-bound candidate certificate.

The observation is recorded explicitly so a domain replay can bind it to
units, source data, uncertainty, and a provenance hash.  The two proof fields
are exactly the requirements for membership in the declared M-space fiber.
-/
structure ObservableMSpaceWitness
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K)
    {Observation : Type uObservation}
    (ranking :
      ObservableTransitionRanking search.Candidate Observation) where
  candidate : search.Candidate
  observation : Observation
  observation_matches :
    ranking.observe candidate = observation
  constraintsHold : search.constraints candidate
  resolves : LiftResolves (search.lift candidate) d

/-- The candidate certificate is an explicit member of the M-space fiber. -/
def ObservableMSpaceWitness.toMSpaceMember
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {d : TrajectoryDistinction K}
    {Observation : Type uObservation}
    {ranking :
      ObservableTransitionRanking search.Candidate Observation}
    (witness : ObservableMSpaceWitness search d ranking) :
    MSpaceFiber search d :=
  mSpaceWitness
    search d witness.candidate witness.constraintsHold witness.resolves

/--
An explicit observation-bound candidate constructively proves non-emptiness of
the declared M-space fiber.
-/
theorem availableLiftWithin_of_observable_witness
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {d : TrajectoryDistinction K}
    {Observation : Type uObservation}
    {ranking :
      ObservableTransitionRanking search.Candidate Observation}
    (witness : ObservableMSpaceWitness search d ranking) :
    AvailableLiftWithin search d := by
  exact ⟨witness.toMSpaceMember⟩

/--
General observable-selection theorem.  A single constructive M-space witness
is enough for the well-ordering of `Nat` to provide a globally minimal
candidate under the declared observation-derived rank.

For infinite candidate classes this is a mathematical existence theorem, not
an executable enumeration claim.
-/
theorem observable_natRanked_mSpace_argmin_exists_of_witness
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K)
    {Observation : Type uObservation}
    (ranking :
      ObservableTransitionRanking search.Candidate Observation)
    (witness : ObservableMSpaceWitness search d ranking) :
    Nonempty
      (NatRankedMSpaceArgmin search d ranking.toTransitionRank) :=
  natRanked_mSpace_argmin_exists
    search d ranking.toTransitionRank
    (availableLiftWithin_of_observable_witness witness)

/--
Executable finite form.  The complete finite M-space declaration supplies the
search boundary, while the explicit witness supplies non-emptiness.  The
existing recursive F07 selector then returns a least observation-derived
natural rank.
-/
theorem finite_observable_mSpace_argmin_exists_of_witness
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K)
    {Observation : Type uObservation}
    (ranking :
      ObservableTransitionRanking search.Candidate Observation)
    (declared : FiniteDeclaredMSpace search d)
    (witness : ObservableMSpaceWitness search d ranking) :
    Nonempty
      (FiniteMSpaceArgmin declared ranking.toTransitionRank) :=
  finite_declared_mSpace_argmin_exists
    search d declared ranking.toTransitionRank
    (availableLiftWithin_of_observable_witness witness)

/--
End-to-end formal-calculus bridge: scoped pressure plus one observable M-space
witness yields a rank-minimal member and a strict representational successor
certificate for that selected member.

This still proves no physical axis, no empirical improvement, and no domain
realization of K0--K12.
-/
theorem observable_ranked_strict_successor_exists
    {K : CurrentK}
    {repairSearch : RepairSearchClass.{uRepairCandidate} K}
    {activeDemand : ActiveDemand K}
    {d : TrajectoryDistinction K}
    (pressure : IrreduciblePressureWithin repairSearch activeDemand d)
    (liftSearch : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    {Observation : Type uObservation}
    (ranking :
      ObservableTransitionRanking liftSearch.Candidate Observation)
    (witness : ObservableMSpaceWitness liftSearch d ranking) :
    Exists fun argmin :
        NatRankedMSpaceArgmin
          liftSearch d ranking.toTransitionRank =>
      Nonempty
        (StrictSuccessorCertificate K
          (liftSearch.lift argmin.minimizer.1)) := by
  obtain ⟨argmin⟩ :=
    observable_natRanked_mSpace_argmin_exists_of_witness
      liftSearch d ranking witness
  exact ⟨argmin,
    strictSuccessorCertificate_of_pressure_natRankedArgmin
      pressure liftSearch argmin⟩

end OCMinimalObligationSpine
