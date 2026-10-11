import OCKIndividuationMSpaceComposition.UniversalDynamics

namespace OCKIndividuationMSpaceComposition

universe uA uB uC uD uE uF uRole

/-!
# Typed relational operators and exact transport

A typed relation is the smallest common operator language used here.  It can
represent deterministic, partial and nondeterministic transitions, has typed
identity and associative composition, and supports exact change-of-context
statements.  It does not retain quantitative weights, and it does not make
operators with incompatible source/target roles interchangeable.

Consequently the result is a minimal common *structural* mechanics, not a
claim that one finite historical glyph list is a complete universal basis.
-/

/-- A typed relational operator from `Source` to `Target`. -/
abbrev RelOperator (Source : Type uA) (Target : Type uB) :=
  Source → Target → Prop

/-- Identity relational operator. -/
def relIdentity {Carrier : Type uA} : RelOperator Carrier Carrier :=
  fun source target => source = target

/-- Typed relational composition, written in execution order: earlier, then later. -/
def relCompose
    {Source : Type uA}
    {Middle : Type uB}
    {Target : Type uC}
    (later : RelOperator Middle Target)
    (earlier : RelOperator Source Middle) :
    RelOperator Source Target :=
  fun source target =>
    ∃ middle, earlier source middle ∧ later middle target

/-- Relational composition is associative. -/
theorem relCompose_assoc
    {A : Type uA}
    {B : Type uB}
    {C : Type uC}
    {D : Type uD}
    (third : RelOperator C D)
    (second : RelOperator B C)
    (first : RelOperator A B) :
    relCompose third (relCompose second first) =
      relCompose (relCompose third second) first := by
  funext source target
  apply propext
  constructor
  · rintro ⟨middleC, ⟨middleB, firstEdge, secondEdge⟩, thirdEdge⟩
    exact ⟨middleB, firstEdge, middleC, secondEdge, thirdEdge⟩
  · rintro ⟨middleB, firstEdge, middleC, secondEdge, thirdEdge⟩
    exact ⟨middleC, ⟨middleB, firstEdge, secondEdge⟩, thirdEdge⟩

/-- Executing identity after an operator changes nothing. -/
theorem relCompose_identity_left
    {Source : Type uA}
    {Target : Type uB}
    (operator : RelOperator Source Target) :
    relCompose relIdentity operator = operator := by
  funext source target
  apply propext
  constructor
  · rintro ⟨middle, edge, equal⟩
    simpa [relIdentity] using equal ▸ edge
  · intro edge
    exact ⟨target, edge, rfl⟩

/-- Executing identity before an operator changes nothing. -/
theorem relCompose_identity_right
    {Source : Type uA}
    {Target : Type uB}
    (operator : RelOperator Source Target) :
    relCompose operator relIdentity = operator := by
  funext source target
  apply propext
  constructor
  · rintro ⟨middle, equal, edge⟩
    simpa [relIdentity] using equal ▸ edge
  · intro edge
    exact ⟨source, rfl, edge⟩

/-!
## Standard operator fragments
-/

/-- Faithful graph embedding of a deterministic operator. -/
def deterministicAsRel
    {Source : Type uA}
    {Target : Type uB}
    (operator : Source → Target) : RelOperator Source Target :=
  deterministicRelation operator

/-- The deterministic graph embedding is injective. -/
theorem deterministicAsRel_injective
    {Source : Type uA}
    {Target : Type uB} :
    Function.Injective (@deterministicAsRel Source Target) :=
  deterministicRelation_injective

/-- Composition of deterministic graphs agrees with function composition. -/
theorem deterministicAsRel_comp
    {A : Type uA}
    {B : Type uB}
    {C : Type uC}
    (later : B → C)
    (earlier : A → B) :
    relCompose (deterministicAsRel later) (deterministicAsRel earlier) =
      deterministicAsRel (later ∘ earlier) := by
  funext source target
  apply propext
  constructor
  · rintro ⟨middle, earlierEdge, laterEdge⟩
    change target = later (earlier source)
    change middle = earlier source at earlierEdge
    change target = later middle at laterEdge
    simpa [earlierEdge] using laterEdge
  · intro edge
    refine ⟨earlier source, ?_, ?_⟩
    · rfl
    · exact edge

/-- A partial deterministic operator returns either a target or no target. -/
abbrev PartialOperator (Source : Type uA) (Target : Type uB) :=
  Source → Option Target

/-- Faithful embedding of a partial operator using `none` as an explicit outcome. -/
def partialAsRel
    {Source : Type uA}
    {Target : Type uB}
    (operator : PartialOperator Source Target) :
    RelOperator Source (Option Target) :=
  deterministicAsRel operator

/-- The explicit-outcome embedding of partial operators is injective. -/
theorem partialAsRel_injective
    {Source : Type uA}
    {Target : Type uB} :
    Function.Injective (@partialAsRel Source Target) :=
  deterministicAsRel_injective

/-- Supported graph of a partial operator, excluding its `none` outcome. -/
def partialSupport
    {Source : Type uA}
    {Target : Type uB}
    (operator : PartialOperator Source Target) :
    RelOperator Source Target :=
  fun source target => operator source = some target

/-- A partial operator has at most one supported target at each source. -/
theorem partialSupport_functional
    {Source : Type uA}
    {Target : Type uB}
    (operator : PartialOperator Source Target)
    {source : Source}
    {first second : Target}
    (firstEdge : partialSupport operator source first)
    (secondEdge : partialSupport operator source second) :
    first = second := by
  change operator source = some first at firstEdge
  change operator source = some second at secondEdge
  rw [firstEdge] at secondEdge
  exact Option.some.inj secondEdge

/-- A nondeterministic operator is a set of possible targets at each source. -/
abbrev NondeterministicOperator
    (Source : Type uA)
    (Target : Type uB) :=
  PowersetStep Source Target

/-- Exact relational embedding of a nondeterministic powerset-valued operator. -/
def nondeterministicAsRel
    {Source : Type uA}
    {Target : Type uB}
    (operator : NondeterministicOperator Source Target) :
    RelOperator Source Target :=
  powersetStepToRelation operator

/-- The nondeterministic relational embedding is faithful. -/
theorem nondeterministicAsRel_injective
    {Source : Type uA}
    {Target : Type uB} :
    Function.Injective (@nondeterministicAsRel Source Target) := by
  intro first second sameRelation
  change powersetStepToRelation first = powersetStepToRelation second at sameRelation
  rw [← relationToPowersetStep_powersetStepToRelation first,
    ← relationToPowersetStep_powersetStepToRelation second, sameRelation]

/-!
## Exact transport and commuting squares
-/

/--
An exact direct-image transport: all target successors of a mapped source are
precisely images of source successors.  This is stronger than forward
simulation and remains meaningful when the right map is non-injective.
-/
structure ExactRelTransport
    {Source : Type uA}
    {Target : Type uB}
    {Source' : Type uC}
    {Target' : Type uD}
    (operator : RelOperator Source Target)
    (operator' : RelOperator Source' Target') where
  sourceMap : Source → Source'
  targetMap : Target → Target'
  exact_image : ∀ source target',
    operator' (sourceMap source) target' ↔
      ∃ target, operator source target ∧ targetMap target = target'

namespace ExactRelTransport

/-- Exact transport includes forward preservation of every operator edge. -/
theorem preserves
    {Source : Type uA}
    {Target : Type uB}
    {Source' : Type uC}
    {Target' : Type uD}
    {operator : RelOperator Source Target}
    {operator' : RelOperator Source' Target'}
    (transport : ExactRelTransport operator operator')
    {source : Source}
    {target : Target}
    (edge : operator source target) :
    operator' (transport.sourceMap source) (transport.targetMap target) :=
  (transport.exact_image source (transport.targetMap target)).2
    ⟨target, edge, rfl⟩

/-- Identity exact transport. -/
def identity
    {Source : Type uA}
    {Target : Type uB}
    (operator : RelOperator Source Target) :
    ExactRelTransport operator operator where
  sourceMap := id
  targetMap := id
  exact_image := by
    intro source target
    constructor
    · intro edge
      exact ⟨target, edge, rfl⟩
    · rintro ⟨middle, edge, rfl⟩
      exact edge

/-- Exact direct-image transports compose. -/
def comp
    {A : Type uA}
    {B : Type uB}
    {C : Type uC}
    {D : Type uD}
    {E : Type uE}
    {F : Type uF}
    {firstOperator : RelOperator A B}
    {secondOperator : RelOperator C D}
    {thirdOperator : RelOperator E F}
    (later : ExactRelTransport secondOperator thirdOperator)
    (earlier : ExactRelTransport firstOperator secondOperator) :
    ExactRelTransport firstOperator thirdOperator where
  sourceMap := later.sourceMap ∘ earlier.sourceMap
  targetMap := later.targetMap ∘ earlier.targetMap
  exact_image := by
    intro source target
    constructor
    · intro thirdEdge
      rcases (later.exact_image (earlier.sourceMap source) target).1 thirdEdge with
        ⟨middleTarget, secondEdge, mapsToTarget⟩
      rcases (earlier.exact_image source middleTarget).1 secondEdge with
        ⟨firstTarget, firstEdge, mapsToMiddle⟩
      refine ⟨firstTarget, firstEdge, ?_⟩
      change later.targetMap (earlier.targetMap firstTarget) = target
      rw [mapsToMiddle]
      exact mapsToTarget
    · rintro ⟨firstTarget, firstEdge, mapsToTarget⟩
      apply (later.exact_image (earlier.sourceMap source) target).2
      refine ⟨earlier.targetMap firstTarget, ?_, mapsToTarget⟩
      exact earlier.preserves firstEdge

end ExactRelTransport

/-- A pointwise commuting square between two typed relational operators. -/
structure RelCommutingSquare
    {Source : Type uA}
    {Target : Type uB}
    {Source' : Type uC}
    {Target' : Type uD}
    (operator : RelOperator Source Target)
    (operator' : RelOperator Source' Target') where
  sourceMap : Source → Source'
  targetMap : Target → Target'
  commutes : ∀ source target,
    operator source target ↔
      operator' (sourceMap source) (targetMap target)

namespace RelCommutingSquare

/-- Pointwise commuting squares compose. -/
def comp
    {A : Type uA}
    {B : Type uB}
    {C : Type uC}
    {D : Type uD}
    {E : Type uE}
    {F : Type uF}
    {firstOperator : RelOperator A B}
    {secondOperator : RelOperator C D}
    {thirdOperator : RelOperator E F}
    (later : RelCommutingSquare secondOperator thirdOperator)
    (earlier : RelCommutingSquare firstOperator secondOperator) :
    RelCommutingSquare firstOperator thirdOperator where
  sourceMap := later.sourceMap ∘ earlier.sourceMap
  targetMap := later.targetMap ∘ earlier.targetMap
  commutes := by
    intro source target
    exact (earlier.commutes source target).trans
      (later.commutes (earlier.sourceMap source) (earlier.targetMap target))

end RelCommutingSquare

/--
An exact direct-image transport with an injective target map induces a
pointwise commuting square.  Injectivity is the exact extra condition needed
to recover a particular preimage edge from equality of transported targets.
-/
def ExactRelTransport.toCommutingSquare
    {Source : Type uA}
    {Target : Type uB}
    {Source' : Type uC}
    {Target' : Type uD}
    {operator : RelOperator Source Target}
    {operator' : RelOperator Source' Target'}
    (transport : ExactRelTransport operator operator')
    (targetInjective : Function.Injective transport.targetMap) :
    RelCommutingSquare operator operator' where
  sourceMap := transport.sourceMap
  targetMap := transport.targetMap
  commutes := by
    intro source target
    constructor
    · exact transport.preserves
    · intro transportedEdge
      rcases (transport.exact_image source (transport.targetMap target)).1
          transportedEdge with
        ⟨preimage, edge, sameImage⟩
      have sameTarget : preimage = target :=
        targetInjective sameImage
      simpa [sameTarget] using edge

/-!
## Objective boundaries of the relational common language
-/

/-- Forgetting quantitative weights to relational support is not faithful. -/
theorem quantitativeSupport_not_faithful :
    ¬ Function.Injective (@weightedSupport Unit Bool) :=
  weightedSupport_not_injective

/-- Source and target types are part of an operator role. -/
structure TypedOperatorRole where
  Source : Type uRole
  Target : Type uRole

/-- Typed roles are compatible only when both endpoint types are equivalent. -/
def TypedOperatorRole.Compatible
    (first second : TypedOperatorRole.{uRole}) : Prop :=
  Nonempty (first.Source ≃ second.Source) ∧
    Nonempty (first.Target ≃ second.Target)

/-- A role from an inhabited source to an empty target. -/
def inhabitedToEmptyRole : TypedOperatorRole where
  Source := Unit
  Target := Empty

/-- The formally reversed role. -/
def emptyToInhabitedRole : TypedOperatorRole where
  Source := Empty
  Target := Unit

/-- Reusing one glyph cannot erase this explicit source/target incompatibility. -/
theorem reversed_roles_are_incompatible :
    ¬ inhabitedToEmptyRole.Compatible emptyToInhabitedRole := by
  rintro ⟨⟨sourceEquivalence⟩, _⟩
  exact Empty.elim (sourceEquivalence ())

/-!
The last theorem does not rule out a finite presentation for a *fixed* typed
theory.  It rules out the stronger type-erasing move needed to treat one bare
glyph as the same universal operator across incompatible roles.  Together
with `quantitativeSupport_not_faithful`, it marks two independent limits:
typing cannot be discarded, and relational support cannot recover weights.
-/

end OCKIndividuationMSpaceComposition
