import OCMinimalObligationSpine.MSpace
import Mathlib.Data.Nat.Find

namespace OCMinimalObligationSpine

universe uLiftCarrier uLiftCandidate uArgmin

/--
A finite declaration of the exact M-space fiber under consideration.  Every
listed value is already a checked fiber member, while `complete` says that the
list omits no member of this declared fiber.  Duplicates are harmless; no
uniqueness claim is built into the declaration.
-/
structure FiniteDeclaredMSpace
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K) where
  members : List (MSpaceFiber search d)
  complete : forall member : MSpaceFiber search d, member ∈ members

/-- A discrete, auditable transition ranking; lower natural numbers are better. -/
abbrev TransitionRank
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K) :=
  search.Candidate -> Nat

/--
The result of minimizing a natural-number rank over one finite declared
M-space.  Minimality is only relative to that declared, complete fiber.
-/
structure FiniteMSpaceArgmin
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {d : TrajectoryDistinction K}
    (declared : FiniteDeclaredMSpace search d)
    (rank : TransitionRank search) where
  minimizer : MSpaceFiber search d
  listed : minimizer ∈ declared.members
  minimalWithinDeclaredFiber : forall other : MSpaceFiber search d,
    rank minimizer.1 ≤ rank other.1

/--
An argmin for the complete M-space fiber under a natural-number rank.

Unlike `FiniteMSpaceArgmin`, this structure does not require an enumeration or
a finiteness assumption.  The well-ordering of `Nat` is sufficient once the
fiber is constructively inhabited.
-/
structure NatRankedMSpaceArgmin
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K)
    (rank : TransitionRank search) where
  minimizer : MSpaceFiber search d
  minimalWithinFiber : forall other : MSpaceFiber search d,
    rank minimizer.1 ≤ rank other.1

/--
General F07 theorem for the declared search class.  Every inhabited M-space
fiber has a globally minimal member for any natural-number transition rank.

The result is constructive up to Lean's choice of the least attainable
natural rank.  It handles infinite candidate classes and ties.  The empty-fiber
case remains correctly unavailable because `AvailableLiftWithin` is required.
-/
theorem natRanked_mSpace_argmin_exists
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K)
    (rank : TransitionRank search)
    (available : AvailableLiftWithin search d) :
    Nonempty (NatRankedMSpaceArgmin search d rank) := by
  classical
  let attainable : Nat -> Prop :=
    fun value =>
      Exists fun member : MSpaceFiber search d =>
        rank member.1 = value
  have attainableExists : Exists attainable := by
    obtain ⟨member⟩ := available
    exact ⟨rank member.1, member, rfl⟩
  let leastRank : Nat := Nat.find attainableExists
  have leastRankAttained : attainable leastRank := by
    exact Nat.find_spec attainableExists
  obtain ⟨minimizer, minimizerRank⟩ := leastRankAttained
  refine ⟨{
    minimizer := minimizer
    minimalWithinFiber := ?_
  }⟩
  intro other
  rw [minimizerRank]
  exact Nat.find_min' attainableExists ⟨other, rfl⟩

/-- Every nonempty finite list has a member of least natural-number rank. -/
private theorem list_argmin_exists
    {alpha : Type uArgmin}
    (rank : alpha -> Nat) :
    forall (head : alpha) (tail : List alpha),
      Exists fun chosen : alpha =>
        chosen ∈ head :: tail /\
          forall other : alpha,
            other ∈ head :: tail -> rank chosen ≤ rank other := by
  intro head tail
  induction tail generalizing head with
  | nil =>
      refine ⟨head, ?_, ?_⟩
      · simp
      · intro other otherMem
        simp at otherMem
        subst other
        exact Nat.le_refl _
  | cons next rest ih =>
      obtain ⟨tailBest, tailBestMem, tailBestMinimal⟩ := ih next
      rcases Nat.le_total (rank head) (rank tailBest) with headLe | tailBestLe
      · refine ⟨head, ?_, ?_⟩
        · simp
        · intro other otherMem
          rcases List.mem_cons.mp otherMem with otherEq | otherInTail
          · subst other
            exact Nat.le_refl _
          · exact Nat.le_trans headLe (tailBestMinimal other otherInTail)
      · refine ⟨tailBest, ?_, ?_⟩
        · exact List.mem_cons.mpr (Or.inr tailBestMem)
        · intro other otherMem
          rcases List.mem_cons.mp otherMem with otherEq | otherInTail
          · subst other
            exact tailBestLe
          · exact tailBestMinimal other otherInTail

/--
Constructive finite F07 theorem.  Availability supplies non-emptiness;
finiteness and completeness come from `declared`; recursive comparison of
natural ranks constructs an argmin.  No minimizer is assumed.
-/
theorem finite_declared_mSpace_argmin_exists
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (d : TrajectoryDistinction K)
    (declared : FiniteDeclaredMSpace search d)
    (rank : TransitionRank search)
    (available : AvailableLiftWithin search d) :
    Nonempty (FiniteMSpaceArgmin declared rank) := by
  obtain ⟨seed⟩ := available
  have seedListed : seed ∈ declared.members := declared.complete seed
  cases membersEq : declared.members with
  | nil =>
      simp [membersEq] at seedListed
  | cons head tail =>
      obtain ⟨chosen, chosenListed, chosenMinimalInList⟩ :=
        list_argmin_exists
          (fun member : MSpaceFiber search d => rank member.1)
          head tail
      refine ⟨{
        minimizer := chosen
        listed := ?_
        minimalWithinDeclaredFiber := ?_
      }⟩
      · simpa [membersEq] using chosenListed
      · intro other
        exact chosenMinimalInList other (by
          simpa [membersEq] using declared.complete other)

/-- The selected argmin, projected as an explicit M-space fiber member. -/
def finiteArgmin_mSpace_member
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {d : TrajectoryDistinction K}
    {declared : FiniteDeclaredMSpace search d}
    {rank : TransitionRank search}
    (argmin : FiniteMSpaceArgmin declared rank) :
    MSpaceFiber search d :=
  argmin.minimizer

/-- The selected M-space member occurs in the declared finite enumeration. -/
theorem finiteArgmin_listed
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {d : TrajectoryDistinction K}
    {declared : FiniteDeclaredMSpace search d}
    {rank : TransitionRank search}
    (argmin : FiniteMSpaceArgmin declared rank) :
    argmin.minimizer ∈ declared.members :=
  argmin.listed

/-- The selected argmin satisfies every declared F06 admissibility constraint. -/
theorem finiteArgmin_constraints
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {d : TrajectoryDistinction K}
    {declared : FiniteDeclaredMSpace search d}
    {rank : TransitionRank search}
    (argmin : FiniteMSpaceArgmin declared rank) :
    search.constraints argmin.minimizer.1 :=
  mSpaceMember_constraints argmin.minimizer

/-- The selected argmin resolves the demanded trajectory distinction. -/
theorem finiteArgmin_resolves
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {d : TrajectoryDistinction K}
    {declared : FiniteDeclaredMSpace search d}
    {rank : TransitionRank search}
    (argmin : FiniteMSpaceArgmin declared rank) :
    LiftResolves (search.lift argmin.minimizer.1) d :=
  mSpaceMember_resolves argmin.minimizer

/-- The selected rank is no greater than that of any member of the fiber. -/
theorem finiteArgmin_rank_le
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {d : TrajectoryDistinction K}
    {declared : FiniteDeclaredMSpace search d}
    {rank : TransitionRank search}
    (argmin : FiniteMSpaceArgmin declared rank)
    (other : MSpaceFiber search d) :
    rank argmin.minimizer.1 ≤ rank other.1 :=
  argmin.minimalWithinDeclaredFiber other

end OCMinimalObligationSpine
