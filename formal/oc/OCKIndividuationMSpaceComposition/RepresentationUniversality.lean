import Mathlib.Data.Fin.Basic
import Mathlib.Logic.Function.Basic

/-!
# Universe-relative representation universality and its exact limit

The universal claim needed by the OC synthesis has two parts which must not be
confused.

* A fixed, finite incidence vocabulary can losslessly carry every particular
  small finitary set-based extensional relational model.  The schema, elements,
  facts, and argument incidences are data in the encoding.
* No fixed scientific payload determines every future independent predicate.
  Allowing a genuinely new probe therefore always permits two extensions with
  the same old reduct and different new facts.

The first statement is representation universality, relative to the Lean
universes in which the source model lives.  The second is an
extension-relative no-maximum theorem.  Neither theorem supplies intended
meaning, empirical truth, admissible morphisms, or causal force: those remain
typed data and domain obligations in the surrounding OC theory.
-/

namespace OCKIndividuationMSpaceComposition

universe uSort uRel uCarrier uNode uOld uProbe

/-- A many-sorted relational signature whose relation symbols have finite arity. -/
structure FinitaryRelSignature where
  SortCode : Type uSort
  Relation : Type uRel
  arity : Relation → Nat
  slotSort : (r : Relation) → Fin (arity r) → SortCode

/-- The dependent tuple type selected by a relation symbol. -/
abbrev FinitaryTuple
    (signature : FinitaryRelSignature)
    (Carrier : signature.SortCode → Type uCarrier)
    (relation : signature.Relation) : Type uCarrier :=
  (slot : Fin (signature.arity relation)) →
    Carrier (signature.slotSort relation slot)

/-- A small set-based extensional model of a finitary relational signature. -/
structure FinitaryRelModel (signature : FinitaryRelSignature) where
  Carrier : signature.SortCode → Type uCarrier
  holds : (relation : signature.Relation) →
    FinitaryTuple signature Carrier relation → Prop

/--
The fixed generic incidence vocabulary.  It has five unary node tags, four
binary typing/ownership relations, and one ternary argument-incidence relation.
All model-specific schema and facts are payload, not new vocabulary.
-/
structure GenericIncidenceStructure where
  Node : Type uNode
  isSort : Node → Prop
  isRelation : Node → Prop
  isSlot : Node → Prop
  isElement : Node → Prop
  isFact : Node → Prop
  typedBy : Node → Node → Prop
  slotOf : Node → Node → Prop
  slotType : Node → Node → Prop
  factOf : Node → Node → Prop
  argumentAt : Node → Node → Node → Prop

namespace FinitaryRelModel

variable {signature : FinitaryRelSignature}
variable (model : FinitaryRelModel signature)

/-- A slot payload records a relation symbol and one of its finite positions. -/
abbrev SlotPayload := Σ relation, Fin (signature.arity relation)

/-- An element payload records its sort together with the carrier element. -/
abbrev ElementPayload := Σ sort, model.Carrier sort

/-- A fact payload contains an exact tuple and evidence that the relation holds. -/
abbrev FactPayload :=
  Σ relation, { tuple : FinitaryTuple signature model.Carrier relation //
    model.holds relation tuple }

/--
Nodes in the canonical encoding.  The constructors are the five node tags of
the generic incidence vocabulary; no source-specific constructor is added.
-/
inductive IncidenceNode where
  | sort (value : signature.SortCode)
  | relation (value : signature.Relation)
  | slot (relation : signature.Relation)
      (index : Fin (signature.arity relation))
  | element (sort : signature.SortCode) (value : model.Carrier sort)
  | fact (relation : signature.Relation)
      (tuple : FinitaryTuple signature model.Carrier relation)
      (evidence : model.holds relation tuple)

/-- The disjoint source payload represented by an incidence node. -/
abbrev IncidencePayload :=
  Sum signature.SortCode
    (Sum signature.Relation
      (Sum (SlotPayload (signature := signature))
        (Sum model.ElementPayload (FactPayload (model := model)))))

/-- Encode one source payload as a node of the fixed generic vocabulary. -/
def encodePayload : model.IncidencePayload → model.IncidenceNode
  | Sum.inl sort => .sort sort
  | Sum.inr (Sum.inl relation) => .relation relation
  | Sum.inr (Sum.inr (Sum.inl ⟨relation, index⟩)) =>
      .slot relation index
  | Sum.inr (Sum.inr (Sum.inr (Sum.inl ⟨sort, value⟩))) =>
      .element sort value
  | Sum.inr (Sum.inr (Sum.inr (Sum.inr ⟨relation, tuple, evidence⟩))) =>
      .fact relation tuple evidence

/-- Decode a canonical incidence node back to its exact source payload. -/
def decodeNode : model.IncidenceNode → model.IncidencePayload
  | .sort sort => Sum.inl sort
  | .relation relation => Sum.inr (Sum.inl relation)
  | .slot relation index =>
      Sum.inr (Sum.inr (Sum.inl ⟨relation, index⟩))
  | .element sort value =>
      Sum.inr (Sum.inr (Sum.inr (Sum.inl ⟨sort, value⟩)))
  | .fact relation tuple evidence =>
      Sum.inr (Sum.inr (Sum.inr (Sum.inr ⟨relation, tuple, evidence⟩)))

theorem decode_encode_payload :
    Function.LeftInverse model.decodeNode model.encodePayload := by
  intro payload
  rcases payload with sort | payload
  · rfl
  rcases payload with relation | payload
  · rfl
  rcases payload with slot | payload
  · rcases slot with ⟨relation, index⟩
    rfl
  rcases payload with element | fact
  · rcases element with ⟨sort, value⟩
    rfl
  · rcases fact with ⟨relation, tuple, evidence⟩
    rfl

theorem encode_decode_node :
    Function.RightInverse model.decodeNode model.encodePayload := by
  intro node
  cases node <;> rfl

theorem encodePayload_bijective : Function.Bijective model.encodePayload :=
  ⟨model.decode_encode_payload.injective,
    model.encode_decode_node.surjective⟩

/-- The five canonical node tags. -/
def IsSort : model.IncidenceNode → Prop
  | .sort _ => True
  | _ => False

def IsRelation : model.IncidenceNode → Prop
  | .relation _ => True
  | _ => False

def IsSlot : model.IncidenceNode → Prop
  | .slot _ _ => True
  | _ => False

def IsElement : model.IncidenceNode → Prop
  | .element _ _ => True
  | _ => False

def IsFact : model.IncidenceNode → Prop
  | .fact _ _ _ => True
  | _ => False

/-- An element node is typed by exactly its encoded sort node. -/
def TypedBy : model.IncidenceNode → model.IncidenceNode → Prop
  | .element sourceSort _, .sort targetSort => sourceSort = targetSort
  | _, _ => False

/-- A slot node belongs to exactly its encoded relation node. -/
def SlotOf : model.IncidenceNode → model.IncidenceNode → Prop
  | .slot sourceRelation _, .relation targetRelation =>
      sourceRelation = targetRelation
  | _, _ => False

/-- A slot node is typed by the sort declared at its encoded position. -/
def SlotType : model.IncidenceNode → model.IncidenceNode → Prop
  | .slot relation index, .sort sort =>
      signature.slotSort relation index = sort
  | _, _ => False

/-- A fact node instantiates exactly its encoded relation symbol. -/
def FactOf : model.IncidenceNode → model.IncidenceNode → Prop
  | .fact sourceRelation _ _, .relation targetRelation =>
      sourceRelation = targetRelation
  | _, _ => False

/--
The ternary incidence connecting a fact, a relation slot, and the element at
that slot.  The existential form keeps the dependency between slot sort and
element type explicit.
-/
def ArgumentAt
    (fact slot element : model.IncidenceNode) : Prop :=
  ∃ (relation : signature.Relation)
      (tuple : FinitaryTuple signature model.Carrier relation)
      (evidence : model.holds relation tuple)
      (index : Fin (signature.arity relation)),
    fact = .fact relation tuple evidence ∧
    slot = .slot relation index ∧
    element = .element (signature.slotSort relation index) (tuple index)

/-- Package the canonical encoding in the one fixed generic vocabulary. -/
def incidenceEncoding : GenericIncidenceStructure where
  Node := model.IncidenceNode
  isSort := model.IsSort
  isRelation := model.IsRelation
  isSlot := model.IsSlot
  isElement := model.IsElement
  isFact := model.IsFact
  typedBy := model.TypedBy
  slotOf := model.SlotOf
  slotType := model.SlotType
  factOf := model.FactOf
  argumentAt := model.ArgumentAt

theorem encoded_element_has_exact_type
    (sort : signature.SortCode) (value : model.Carrier sort) :
    model.TypedBy (.element sort value) (.sort sort) := rfl

theorem encoded_slot_has_exact_owner_and_type
    (relation : signature.Relation)
    (index : Fin (signature.arity relation)) :
    model.SlotOf (.slot relation index) (.relation relation) ∧
      model.SlotType (.slot relation index)
        (.sort (signature.slotSort relation index)) := by
  exact ⟨rfl, rfl⟩

theorem encoded_fact_has_exact_relation
    (relation : signature.Relation)
    (tuple : FinitaryTuple signature model.Carrier relation)
    (evidence : model.holds relation tuple) :
    model.FactOf (.fact relation tuple evidence) (.relation relation) := rfl

theorem encoded_fact_has_exact_argument
    (relation : signature.Relation)
    (tuple : FinitaryTuple signature model.Carrier relation)
    (evidence : model.holds relation tuple)
    (index : Fin (signature.arity relation)) :
    model.ArgumentAt
      (.fact relation tuple evidence)
      (.slot relation index)
      (.element (signature.slotSort relation index) (tuple index)) := by
  exact ⟨relation, tuple, evidence, index, rfl, rfl, rfl⟩

/-- Every held source tuple is represented by one exact fact-incidence star. -/
theorem held_tuple_is_reified
    (relation : signature.Relation)
    (tuple : FinitaryTuple signature model.Carrier relation)
    (evidence : model.holds relation tuple) :
    ∃ fact : model.IncidenceNode,
      model.IsFact fact ∧
      model.FactOf fact (.relation relation) ∧
      ∀ index : Fin (signature.arity relation),
        model.ArgumentAt fact (.slot relation index)
          (.element (signature.slotSort relation index) (tuple index)) := by
  refine ⟨.fact relation tuple evidence, trivial, rfl, ?_⟩
  intro index
  exact model.encoded_fact_has_exact_argument relation tuple evidence index

/-- Conversely, the canonical encoding contains no fact node without a source fact. -/
theorem fact_node_reflects_held_tuple
    (fact : model.IncidenceNode)
    (isFact : model.IsFact fact) :
    ∃ (relation : signature.Relation)
        (tuple : FinitaryTuple signature model.Carrier relation)
        (evidence : model.holds relation tuple),
      fact = .fact relation tuple evidence := by
  cases fact with
  | sort sort => simp [IsFact] at isFact
  | relation relation => simp [IsFact] at isFact
  | slot relation index => simp [IsFact] at isFact
  | element sort value => simp [IsFact] at isFact
  | fact relation tuple evidence =>
      exact ⟨relation, tuple, evidence, rfl⟩

/-- The complete carrier/fact serialization result, with both exact round trips. -/
theorem universe_relative_incidence_representation_is_lossless :
    Function.LeftInverse model.decodeNode model.encodePayload ∧
    Function.RightInverse model.decodeNode model.encodePayload ∧
    (∀ (relation : signature.Relation)
        (tuple : FinitaryTuple signature model.Carrier relation),
      model.holds relation tuple →
        ∃ fact : model.IncidenceNode,
          model.IsFact fact ∧
          model.FactOf fact (.relation relation) ∧
          ∀ index : Fin (signature.arity relation),
            model.ArgumentAt fact (.slot relation index)
              (.element (signature.slotSort relation index) (tuple index))) ∧
    (∀ fact : model.IncidenceNode,
      model.IsFact fact →
        ∃ (relation : signature.Relation)
            (tuple : FinitaryTuple signature model.Carrier relation)
            (evidence : model.holds relation tuple),
          fact = .fact relation tuple evidence) := by
  refine ⟨model.decode_encode_payload, model.encode_decode_node, ?_, ?_⟩
  · intro relation tuple evidence
    exact model.held_tuple_is_reified relation tuple evidence
  · intro fact isFact
    exact model.fact_node_reflects_held_tuple fact isFact

end FinitaryRelModel

/-! ## The exact extension-relative boundary -/

/-- A scientific payload extended by one new unary probe. -/
structure UnaryPredicateExtension (Old : Type uOld) (Probe : Type uProbe) where
  old : Old
  newPredicate : Probe → Prop

def emptyPredicateExtension
    {Old : Type uOld} {Probe : Type uProbe} (old : Old) :
    UnaryPredicateExtension Old Probe where
  old := old
  newPredicate := fun _ => False

def fullPredicateExtension
    {Old : Type uOld} {Probe : Type uProbe} (old : Old) :
    UnaryPredicateExtension Old Probe where
  old := old
  newPredicate := fun _ => True

theorem empty_full_extensions_have_same_reduct
    {Old : Type uOld} {Probe : Type uProbe} (old : Old) :
    (emptyPredicateExtension (Probe := Probe) old).old =
      (fullPredicateExtension (Probe := Probe) old).old := rfl

theorem empty_full_extensions_are_distinct
    {Old : Type uOld} {Probe : Type uProbe} [Nonempty Probe]
    (old : Old) :
    emptyPredicateExtension (Probe := Probe) old ≠
      fullPredicateExtension (Probe := Probe) old := by
  intro equalExtensions
  let probe : Probe := Classical.choice (inferInstance : Nonempty Probe)
  have equalPredicates := congrArg UnaryPredicateExtension.newPredicate equalExtensions
  have equalAtProbe := congrFun equalPredicates probe
  exact Eq.mpr equalAtProbe trivial

/--
No function of the old payload alone can recover both possible independent
extensions.  This is the precise no-maximum result; it is relative to allowing
a new probe and does not deny completeness inside a fixed language.
-/
theorem no_old_payload_recovers_all_independent_extensions
    {Old : Type uOld} {Probe : Type uProbe} [Nonempty Probe]
    (old : Old) (recover : Old → Probe → Prop) :
    recover old ≠ (fun _ => False) ∨
      recover old ≠ (fun _ => True) := by
  let probe : Probe := Classical.choice (inferInstance : Nonempty Probe)
  by_cases observed : recover old probe
  · left
    intro equalEmpty
    have equalAtProbe := congrFun equalEmpty probe
    exact Eq.mp equalAtProbe observed
  · right
    intro equalFull
    have equalAtProbe := congrFun equalFull probe
    exact observed (Eq.mpr equalAtProbe trivial)

/-- Every old payload has at least two distinct extensions with the same reduct. -/
theorem extension_relative_no_maximum
    {Old : Type uOld} {Probe : Type uProbe} [Nonempty Probe]
    (old : Old) :
    ∃ first second : UnaryPredicateExtension Old Probe,
      first.old = old ∧ second.old = old ∧ first ≠ second := by
  exact ⟨emptyPredicateExtension old, fullPredicateExtension old,
    rfl, rfl, empty_full_extensions_are_distinct old⟩

end OCKIndividuationMSpaceComposition
