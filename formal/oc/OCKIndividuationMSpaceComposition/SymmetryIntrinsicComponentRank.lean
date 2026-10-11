import OCKIndividuationMSpaceComposition.ConstraintGeneratedObject
import OCKIndividuationMSpaceComposition.SymmetryIntrinsicDimensionBoundary
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

namespace IntrinsicComponentRank

open OCMaturityCompletionCycle

/-!
# The exact rank supplied by equivalence generation

OC already uses `EquivalenceGenerated` as the least equivalence closure of typed
binary evidence.  This module asks exactly what notion of intrinsic dimension
that existing construction supports, without importing vectors, coordinates,
bases, matroids or `finrank`.

The answer has two parts.

* Positive: the number of generated equivalence classes represented by a
  finite family is an intrinsic rank.  Adding a token raises it by one exactly
  when that token is outside the generated closure.
* Boundary: this is a component rank, not yet a general compositional
  dimension.  Equivalence closure is singleton-generated and therefore cannot
  express genuinely joint generation.  A finite exchange closure with a
  three-element circuit supplies an exact counterexample.

Thus binary equivalence supplies an intrinsic component-count rank relative to
the chosen evidence, not general dimension.  To derive dimension of
independent directions, OC still needs a scientifically grounded finitary
composition law whose closure admits exchange (or an equivalent rank
principle), followed by a separate equivariance theorem.
-/

universe uToken

abbrev GeneratedEquivalence {Token : Type uToken}
    (evidence : Token → Token → Prop) : Token → Token → Prop :=
  EquivalenceGenerated evidence

def generatedSetoid {Token : Type uToken}
    (evidence : Token → Token → Prop) : Setoid Token where
  r := GeneratedEquivalence evidence
  iseqv := ⟨
    by intro token; exact EquivalenceGenerated.refl token,
    by intro first second related; exact EquivalenceGenerated.symm related,
    by intro first second third firstSecond secondThird
       exact EquivalenceGenerated.trans firstSecond secondThird⟩

abbrev Component {Token : Type uToken}
    (evidence : Token → Token → Prop) :=
  Quotient (generatedSetoid evidence)

def componentOf {Token : Type uToken}
    (evidence : Token → Token → Prop) (token : Token) : Component evidence :=
  Quotient.mk _ token

/-- Closure of a finite family under the already existing OC equivalence
generation.  Membership remains a proposition; no ambient finite universe is
assumed. -/
def componentClosure {Token : Type uToken}
    [DecidableEq Token]
    (evidence : Token → Token → Prop) (seed : Finset Token) (token : Token) : Prop :=
  ∃ root ∈ seed, GeneratedEquivalence evidence root token

/-- Intrinsic component rank: number of generated equivalence classes met by
the finite family. -/
noncomputable def componentRank {Token : Type uToken}
    [DecidableEq Token]
    (evidence : Token → Token → Prop) (seed : Finset Token) : Nat := by
  classical
  exact (seed.image (componentOf evidence)).card

theorem componentClosure_extensive
    {Token : Type uToken}
    [DecidableEq Token]
    (evidence : Token → Token → Prop) (seed : Finset Token) :
    ∀ ⦃token⦄, token ∈ seed → componentClosure evidence seed token := by
  intro token tokenMember
  exact ⟨token, tokenMember, EquivalenceGenerated.refl token⟩

theorem componentClosure_monotone
    {Token : Type uToken}
    [DecidableEq Token]
    (evidence : Token → Token → Prop) {first second : Finset Token}
    (subset : first ⊆ second) :
    ∀ ⦃token⦄,
      componentClosure evidence first token →
        componentClosure evidence second token := by
  rintro token ⟨root, rootMember, generated⟩
  exact ⟨root, subset rootMember, generated⟩

/-- Equivalence closure is already closed under a second closure step. -/
theorem componentClosure_idempotent
    {Token : Type uToken}
    [DecidableEq Token]
    (evidence : Token → Token → Prop) (seed : Finset Token) (token : Token) :
    (∃ middle,
        componentClosure evidence seed middle ∧
        GeneratedEquivalence evidence middle token) ↔
      componentClosure evidence seed token := by
  constructor
  · rintro ⟨middle, ⟨root, rootMember, rootMiddle⟩, middleToken⟩
    exact ⟨root, rootMember, EquivalenceGenerated.trans rootMiddle middleToken⟩
  · rintro ⟨root, rootMember, rootToken⟩
    exact ⟨root, ⟨root, rootMember, EquivalenceGenerated.refl root⟩, rootToken⟩

/-- The existing equivalence closure satisfies Steinitz exchange. -/
theorem componentClosure_exchange
    {Token : Type uToken}
    [DecidableEq Token]
    (evidence : Token → Token → Prop) (seed : Finset Token)
    {first second : Token}
    (firstGenerated : componentClosure evidence (insert second seed) first)
    (firstNew : ¬ componentClosure evidence seed first) :
    componentClosure evidence (insert first seed) second := by
  rcases firstGenerated with ⟨root, rootMember, rootFirst⟩
  have rootIsSecond : root = second := by
    rcases Finset.mem_insert.mp rootMember with rootIsSecond | rootInSeed
    · exact rootIsSecond
    · exact False.elim (firstNew ⟨root, rootInSeed, rootFirst⟩)
  subst root
  exact ⟨first, Finset.mem_insert_self _ _,
    EquivalenceGenerated.symm rootFirst⟩

/-- Exact rank-growth theorem for the intrinsic component construction. -/
theorem componentRank_insert_eq_add_one_of_not_generated
    {Token : Type uToken}
    [DecidableEq Token]
    (evidence : Token → Token → Prop) (seed : Finset Token) (token : Token)
    (newComponent : ¬ componentClosure evidence seed token) :
    componentRank evidence (insert token seed) = componentRank evidence seed + 1 := by
  classical
  rw [componentRank, componentRank, Finset.image_insert]
  apply Finset.card_insert_of_notMem
  intro classMember
  rcases Finset.mem_image.mp classMember with ⟨root, rootMember, classesEqual⟩
  apply newComponent
  exact ⟨root, rootMember,
    (show generatedSetoid evidence root token from Quotient.exact classesEqual)⟩

/-- Generated additions do not change component rank. -/
theorem componentRank_insert_eq_of_generated
    {Token : Type uToken}
    [DecidableEq Token]
    (evidence : Token → Token → Prop) (seed : Finset Token) (token : Token)
    (generated : componentClosure evidence seed token) :
    componentRank evidence (insert token seed) = componentRank evidence seed := by
  classical
  rw [componentRank, componentRank, Finset.image_insert]
  apply Finset.card_insert_of_mem
  rcases generated with ⟨root, rootMember, rootToken⟩
  exact Finset.mem_image.mpr
    ⟨root, rootMember,
      Quotient.sound (show generatedSetoid evidence root token from rootToken)⟩

/-- Strong iff form: a new component and a one-step rank increase are the
same event. -/
theorem componentRank_insert_eq_add_one_iff
    {Token : Type uToken}
    [DecidableEq Token]
    (evidence : Token → Token → Prop) (seed : Finset Token) (token : Token) :
    componentRank evidence (insert token seed) = componentRank evidence seed + 1 ↔
      ¬ componentClosure evidence seed token := by
  constructor
  · intro rankIncrease generated
    rw [componentRank_insert_eq_of_generated evidence seed token generated] at rankIncrease
    omega
  · exact componentRank_insert_eq_add_one_of_not_generated evidence seed token

/-- Critical classification theorem: equivalence closure has no genuinely
joint generators.  Every generated token is already generated by one seed
token. -/
theorem componentClosure_is_singleton_generated
    {Token : Type uToken}
    [DecidableEq Token]
    (evidence : Token → Token → Prop) (seed : Finset Token) (token : Token) :
    componentClosure evidence seed token ↔
      ∃ root ∈ seed, componentClosure evidence {root} token := by
  constructor
  · rintro ⟨root, rootMember, generated⟩
    exact ⟨root, rootMember, root, by simp, generated⟩
  · rintro ⟨root, rootMember, witness, witnessMember, generated⟩
    have witnessEq : witness = root := by simpa using witnessMember
    subst witness
    exact ⟨root, rootMember, generated⟩

/-! ## Exact boundary: exchange can support joint generation -/

abbrev TriangleToken := Fin 3

/-- The rank-two three-point circuit closure: any two distinctions jointly
generate the third, while no singleton does. -/
def triangleClosure (seed : Finset TriangleToken) : Finset TriangleToken :=
  if 2 ≤ seed.card then Finset.univ else seed

theorem triangleClosure_extensive :
    IntrinsicDimensionBoundary.ClosureExtensive triangleClosure := by
  intro seed
  by_cases large : 2 ≤ seed.card
  · simp [triangleClosure, large]
  · simpa [triangleClosure, large]

theorem triangleClosure_monotone :
    IntrinsicDimensionBoundary.ClosureMonotone triangleClosure := by
  intro first second subset
  by_cases firstLarge : 2 ≤ first.card
  · have secondLarge : 2 ≤ second.card :=
      firstLarge.trans (Finset.card_le_card subset)
    simp [triangleClosure, firstLarge, secondLarge]
  · by_cases secondLarge : 2 ≤ second.card
    · simp [triangleClosure, firstLarge, secondLarge]
    · simpa [triangleClosure, firstLarge, secondLarge] using subset

theorem triangleClosure_idempotent :
    IntrinsicDimensionBoundary.ClosureIdempotent triangleClosure := by
  intro seed
  by_cases large : 2 ≤ seed.card
  · simp [triangleClosure, large]
  · simp [triangleClosure, large]

theorem triangleClosure_exchange :
    IntrinsicDimensionBoundary.ClosureExchange triangleClosure := by
  intro seed first second firstGenerated firstNew
  by_cases seedLarge : 2 ≤ seed.card
  · exact False.elim (firstNew (by simp [triangleClosure, seedLarge]))
  · have firstNotSeed : first ∉ seed := by
      intro firstMember
      apply firstNew
      simpa [triangleClosure, seedLarge] using firstMember
    by_cases secondMember : second ∈ seed
    · apply False.elim
      apply firstNew
      simpa [Finset.insert_eq_of_mem secondMember] using firstGenerated
    · have secondInsertCard : (insert second seed).card = seed.card + 1 :=
        Finset.card_insert_of_notMem secondMember
      by_cases seedEmpty : seed.card = 0
      · have secondInsertSmall : ¬ 2 ≤ (insert second seed).card := by
          rw [secondInsertCard, seedEmpty]
          omega
        have firstInInsert : first ∈ insert second seed := by
          simpa [triangleClosure, secondInsertSmall] using firstGenerated
        have firstEqSecond : first = second :=
          (Finset.mem_insert.mp firstInInsert).resolve_right firstNotSeed
        subst first
        exact triangleClosure_extensive (insert second seed)
          (Finset.mem_insert_self second seed)
      · have seedCardOne : seed.card = 1 := by omega
        have firstInsertCard : (insert first seed).card = 2 := by
          rw [Finset.card_insert_of_notMem firstNotSeed, seedCardOne]
        simp [triangleClosure, firstInsertCard]

theorem triangleClosure_has_joint_generation :
    (2 : TriangleToken) ∈ triangleClosure {0, 1} ∧
    (2 : TriangleToken) ∉ triangleClosure {0} ∧
    (2 : TriangleToken) ∉ triangleClosure {1} := by
  decide

/-- No binary equivalence evidence can represent the triangle closure.  This
is the exact obstruction to treating component rank as the full OC notion of
dimension. -/
theorem triangleClosure_not_equivalence_component_closure :
    ¬ ∃ evidence : TriangleToken → TriangleToken → Prop,
      ∀ seed token,
        token ∈ triangleClosure seed ↔
          componentClosure evidence seed token := by
  rintro ⟨evidence, represents⟩
  have generated : componentClosure evidence {0, 1} (2 : TriangleToken) :=
    (represents {0, 1} 2).mp triangleClosure_has_joint_generation.1
  rcases (componentClosure_is_singleton_generated evidence {0, 1} 2).mp generated with
    ⟨root, rootMember, singletonGenerated⟩
  have triangleSingleton : (2 : TriangleToken) ∈ triangleClosure {root} :=
    (represents {root} 2).mpr singletonGenerated
  have rootZeroOrOne : root = 0 ∨ root = 1 := by
    simpa using rootMember
  rcases rootZeroOrOne with rfl | rfl
  · exact triangleClosure_has_joint_generation.2.1 triangleSingleton
  · exact triangleClosure_has_joint_generation.2.2 triangleSingleton

end IntrinsicComponentRank

end OCKIndividuationMSpaceComposition
