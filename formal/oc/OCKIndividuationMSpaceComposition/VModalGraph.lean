import OCKIndividuationMSpaceComposition.PathDependentContinuation

namespace OCKIndividuationMSpaceComposition

namespace VModalGraph

universe uNode uSemantic uView uValue uExtra

/-!
# Formal semantics of the V-modal research graph adapter

This is a derived research-programme layer, not a theorem identifying V-cells
with OC K-levels and not an execution or release admission.  It isolates the
minimal propositions needed to prevent a decomposition graph, its projections,
and its profiles from manufacturing scientific closure.
-/

/-- A directed decomposition step.  It records the local parent whose question
is refined and the local child that must eventually be composed back. -/
structure Split (Node : Type uNode) where
  parent : Node
  child : Node
deriving DecidableEq

/-- An explicit return obligation for one split.  `result` is local to the
split; `returnsTo` makes the intended parent checkable rather than inferred by
transitive reachability. -/
structure JoinObligation (Node : Type uNode) where
  split : Split Node
  result : Node
  returnsTo : Node
deriving DecidableEq

/-- Every registered split has a registered local result returning to its own
parent.  The definition deliberately does not accept an arbitrary reachable
result elsewhere in the graph. -/
def NoSplitWithoutJoin {Node : Type uNode}
    (splits : List (Split Node))
    (joins : List (JoinObligation Node)) : Prop :=
  ∀ split, split ∈ splits →
    ∃ join, join ∈ joins ∧ join.split = split ∧
      join.returnsTo = split.parent

theorem registered_split_has_local_return
    {Node : Type uNode}
    {splits : List (Split Node)}
    {joins : List (JoinObligation Node)}
    (h : NoSplitWithoutJoin splits joins)
    {split : Split Node}
    (hs : split ∈ splits) :
    ∃ join, join ∈ joins ∧ join.split = split ∧
      join.returnsTo = split.parent :=
  h split hs

/-- A concrete no-go instance: recording a split without a join does not
satisfy the invariant. -/
theorem split_registration_alone_does_not_supply_join :
    ∃ splits : List (Split Bool),
      ¬ NoSplitWithoutJoin splits [] := by
  let split : Split Bool := ⟨false, true⟩
  refine ⟨[split], ?_⟩
  intro h
  obtain ⟨join, hj, _⟩ := h split (by simp)
  simp at hj

/-- Parent closure has four independent inputs.  A child status is therefore
not silently promoted into accepted composition, interface compatibility, or
evidence sufficiency. -/
structure ClosureConditions where
  childrenClosed : Prop
  compositionAccepted : Prop
  interfacesAccepted : Prop
  evidenceAccepted : Prop

def ParentClosed (conditions : ClosureConditions) : Prop :=
  conditions.childrenClosed ∧
    conditions.compositionAccepted ∧
    conditions.interfacesAccepted ∧
    conditions.evidenceAccepted

theorem parent_closure_requires_composition
    {conditions : ClosureConditions}
    (h : ParentClosed conditions) :
    conditions.compositionAccepted :=
  h.2.1

theorem parent_closure_requires_interface_acceptance
    {conditions : ClosureConditions}
    (h : ParentClosed conditions) :
    conditions.interfacesAccepted :=
  h.2.2.1

theorem parent_closure_requires_evidence_acceptance
    {conditions : ClosureConditions}
    (h : ParentClosed conditions) :
    conditions.evidenceAccepted :=
  h.2.2.2

/-- No Boolean computed from child closure alone can encode the missing
composition facts: two worlds may have the same closed children and opposite
parent-closure truth values. -/
theorem child_closure_is_not_sufficient_for_parent_closure :
    ∃ accepted rejected : ClosureConditions,
      accepted.childrenClosed ∧ rejected.childrenClosed ∧
      ParentClosed accepted ∧ ¬ ParentClosed rejected := by
  let accepted : ClosureConditions := ⟨True, True, True, True⟩
  let rejected : ClosureConditions := ⟨True, False, True, True⟩
  refine ⟨accepted, rejected, ?_⟩
  simp [accepted, rejected, ParentClosed]

/-- A view contains an explicitly retained semantic source.  Rendering may
change the view value, but the constructor cannot rewrite the source. -/
structure Projection (Semantic : Type uSemantic) (View : Type uView) where
  semantic : Semantic
  rendered : View

def render {Semantic : Type uSemantic} {View : Type uView}
    (semantic : Semantic) (renderer : Semantic → View) :
    Projection Semantic View :=
  ⟨semantic, renderer semantic⟩

theorem rendering_preserves_semantic_source
    {Semantic : Type uSemantic} {View : Type uView}
    (semantic : Semantic) (renderer : Semantic → View) :
    (render semantic renderer).semantic = semantic := by
  rfl

/-- Equal rendered views do not justify equal semantic objects.  This is the
formal anti-shortcut behind projection purity. -/
theorem equal_view_does_not_imply_equal_semantic_source :
    ∃ left right : Projection Bool Unit,
      left.rendered = right.rendered ∧
      left.semantic ≠ right.semantic := by
  refine ⟨⟨false, ()⟩, ⟨true, ()⟩, rfl, ?_⟩
  decide

/-- Reopening creates a new generation and preserves the previous occurrence
in history.  It does not mutate the old occurrence in place. -/
structure VersionedRecord (Value : Type uValue) where
  generation : Nat
  current : Value
  history : List (Nat × Value)

def reopen {Value : Type uValue}
    (record : VersionedRecord Value) (next : Value) :
    VersionedRecord Value :=
  { generation := record.generation + 1
    current := next
    history := (record.generation, record.current) :: record.history }

theorem reopen_advances_generation
    {Value : Type uValue}
    (record : VersionedRecord Value) (next : Value) :
    (reopen record next).generation = record.generation + 1 := by
  rfl

theorem reopen_preserves_previous_occurrence
    {Value : Type uValue}
    (record : VersionedRecord Value) (next : Value) :
    ((record.generation, record.current) ∈ (reopen record next).history) := by
  simp [reopen]

theorem reopen_is_not_in_place_at_generation
    {Value : Type uValue}
    (record : VersionedRecord Value) (next : Value) :
    (reopen record next).generation ≠ record.generation := by
  simp [reopen]

/-- A profile extension retains a typed core and adds profile-specific data.
The forgetful map is the conservative boundary. -/
structure ProfileExtension (Core : Type uSemantic) (Extra : Type uExtra) where
  core : Core
  extra : Extra

def extendProfile {Core : Type uSemantic} {Extra : Type uExtra}
    (core : Core) (extra : Extra) : ProfileExtension Core Extra :=
  ⟨core, extra⟩

def forgetProfile {Core : Type uSemantic} {Extra : Type uExtra}
    (profile : ProfileExtension Core Extra) : Core :=
  profile.core

theorem profile_extension_is_conservative
    {Core : Type uSemantic} {Extra : Type uExtra}
    (core : Core) (extra : Extra) :
    forgetProfile (extendProfile core extra) = core := by
  rfl

/-- A profile is admissible only through a separately supplied conservativity
witness.  Merely attaching extra fields is not that witness. -/
structure AdmittedProfile
    (Core : Type uSemantic) (Extra : Type uExtra)
    (semanticInvariant : Core → Prop) where
  extension : ProfileExtension Core Extra
  conservative : semanticInvariant extension.core

theorem admitted_profile_preserves_declared_invariant
    {Core : Type uSemantic} {Extra : Type uExtra}
    {semanticInvariant : Core → Prop}
    (profile : AdmittedProfile Core Extra semanticInvariant) :
    semanticInvariant (forgetProfile profile.extension) :=
  profile.conservative

end VModalGraph

end OCKIndividuationMSpaceComposition
