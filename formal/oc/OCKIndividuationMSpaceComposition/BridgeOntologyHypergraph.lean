import Mathlib.Data.Set.Lattice
import Mathlib.Data.Finset.Basic
import Mathlib.Logic.Relation

namespace OCKIndividuationMSpaceComposition

universe uFamily uVertex uEdge uBridge uA uB uC uD uObs uTask uEvent uNode

/-!
Typed bridge-ontology and integrated-hypergraph kernel.

The construction is deliberately a tagged disjoint union plus admitted bridge
hyperedges.  It never quotients ontology-local vertices into one identity.
-/

/-- A family of ontology-local hypergraphs sharing only an index type. -/
structure OntologyFamilyGraph (Family : Type uFamily) where
  Vertex : Family → Type uVertex
  Edge : Family → Type uEdge
  incident : (family : Family) → Edge family → Vertex family → Prop

/-- Canonical tagged vertex of the disjoint ontology union. -/
abbrev TaggedVertex {Family : Type uFamily} (graph : OntologyFamilyGraph Family) :=
  Sigma graph.Vertex

/-- Canonical tagged local edge of the disjoint ontology union. -/
abbrev TaggedLocalEdge {Family : Type uFamily} (graph : OntologyFamilyGraph Family) :=
  Sigma graph.Edge

/-- A typed candidate bridge retains both endpoint families and values. -/
structure BridgeCandidate {Family : Type uFamily} (graph : OntologyFamilyGraph Family) where
  sourceFamily : Family
  source : graph.Vertex sourceFamily
  targetFamily : Family
  target : graph.Vertex targetFamily
  ruleGeneration : Nat
  mappingGeneration : Nat

def vertexTag {Family : Type uFamily} (graph : OntologyFamilyGraph Family)
    (family : Family) : graph.Vertex family → TaggedVertex graph :=
  fun vertex => ⟨family, vertex⟩

def bridgeSourceVertex {Family : Type uFamily} {graph : OntologyFamilyGraph Family}
    (bridge : BridgeCandidate graph) : TaggedVertex graph :=
  ⟨bridge.sourceFamily, bridge.source⟩

def bridgeTargetVertex {Family : Type uFamily} {graph : OntologyFamilyGraph Family}
    (bridge : BridgeCandidate graph) : TaggedVertex graph :=
  ⟨bridge.targetFamily, bridge.target⟩

/-- Local incidence after tagging; different family tags cannot be incident. -/
def taggedLocalIncident {Family : Type uFamily} (graph : OntologyFamilyGraph Family)
    (edge : TaggedLocalEdge graph) (vertex : TaggedVertex graph) : Prop :=
  ∃ sameFamily : vertex.1 = edge.1,
    graph.incident edge.1 edge.2 (sameFamily ▸ vertex.2)

/-- Minimal typed hypergraph surface used by the bridge assembly theorem. -/
structure IntegratedHypergraph where
  Vertex : Type uVertex
  LocalEdge : Type uEdge
  BridgeEdge : Type uBridge
  localIncident : LocalEdge → Vertex → Prop
  bridgeIncident : BridgeEdge → Vertex → Prop

/--
The static assembly operator.  `admit` is the complete bridge-rule admission
predicate for one frozen context/evidence cut.
-/
def assembleIntegratedHypergraph {Family : Type uFamily}
    (graph : OntologyFamilyGraph Family)
    (admit : BridgeCandidate graph → Prop) : IntegratedHypergraph where
  Vertex := TaggedVertex graph
  LocalEdge := TaggedLocalEdge graph
  BridgeEdge := {bridge : BridgeCandidate graph // admit bridge}
  localIncident := taggedLocalIncident graph
  bridgeIncident := fun bridge vertex =>
    vertex = bridgeSourceVertex bridge.1 ∨ vertex = bridgeTargetVertex bridge.1

/-- Every ontology-local vertex injection into the assembly is injective. -/
theorem vertexTag_injective {Family : Type uFamily}
    (graph : OntologyFamilyGraph Family) (family : Family) :
    Function.Injective (vertexTag graph family) := by
  intro left right equal
  cases equal
  rfl

/-- Different ontology tags have disjoint images, independent of payload equality. -/
theorem distinct_family_tags_ne {Family : Type uFamily}
    (graph : OntologyFamilyGraph Family) {leftFamily rightFamily : Family}
    (different : leftFamily ≠ rightFamily)
    (left : graph.Vertex leftFamily) (right : graph.Vertex rightFamily) :
    vertexTag graph leftFamily left ≠ vertexTag graph rightFamily right := by
  intro equal
  apply different
  exact congrArg Sigma.fst equal

/-- Tagging preserves every ontology-local incidence exactly. -/
theorem assembled_local_incidence_iff {Family : Type uFamily}
    (graph : OntologyFamilyGraph Family)
    (admit : BridgeCandidate graph → Prop)
    (family : Family) (edge : graph.Edge family) (vertex : graph.Vertex family) :
    (assembleIntegratedHypergraph graph admit).localIncident
        ⟨family, edge⟩ ⟨family, vertex⟩ ↔ graph.incident family edge vertex := by
  simp [assembleIntegratedHypergraph, taggedLocalIncident]

/-- Every admitted bridge is incident to its source endpoint. -/
theorem admitted_bridge_incident_source {Family : Type uFamily}
    (graph : OntologyFamilyGraph Family)
    (admit : BridgeCandidate graph → Prop)
    (bridge : {candidate : BridgeCandidate graph // admit candidate}) :
    (assembleIntegratedHypergraph graph admit).bridgeIncident
      bridge (bridgeSourceVertex bridge.1) := by
  exact Or.inl rfl

/-- Every admitted bridge is incident to its target endpoint. -/
theorem admitted_bridge_incident_target {Family : Type uFamily}
    (graph : OntologyFamilyGraph Family)
    (admit : BridgeCandidate graph → Prop)
    (bridge : {candidate : BridgeCandidate graph // admit candidate}) :
    (assembleIntegratedHypergraph graph admit).bridgeIncident
      bridge (bridgeTargetVertex bridge.1) := by
  exact Or.inr rfl

/-- The assembled vertex carrier is definitionally the tagged disjoint union. -/
theorem integrated_hypergraph_vertex_carrier {Family : Type uFamily}
    (graph : OntologyFamilyGraph Family)
    (admit : BridgeCandidate graph → Prop) :
    (assembleIntegratedHypergraph graph admit).Vertex = TaggedVertex graph := rfl

/-! ### Bridge-path algebra -/

/-- Left-to-right relational composition. -/
def BridgeRelComp (left : α → β → Prop) (right : β → γ → Prop) : α → γ → Prop :=
  fun source target => ∃ middle, left source middle ∧ right middle target

/-- Typed relational bridge composition is associative. -/
theorem bridgeRelComp_assoc
    (first : α → β → Prop) (second : β → γ → Prop) (third : γ → δ → Prop) :
    BridgeRelComp (BridgeRelComp first second) third =
      BridgeRelComp first (BridgeRelComp second third) := by
  funext source target
  apply propext
  constructor
  · rintro ⟨middle₂, ⟨middle₁, hFirst, hSecond⟩, hThird⟩
    exact ⟨middle₁, hFirst, middle₂, hSecond, hThird⟩
  · rintro ⟨middle₁, hFirst, middle₂, hSecond, hThird⟩
    exact ⟨middle₂, ⟨middle₁, hFirst, hSecond⟩, hThird⟩

/--
An ordered bridge path carries semantic information that is not present in its
two endpoints: rule generation, witness and loss account are part of the path.
-/
structure BridgePathRecord (Source : Type uA) (Target : Type uB)
    (Witness : Type uC) (Loss : Type uD) where
  source : Source
  target : Target
  ruleGeneration : Nat
  witness : Witness
  loss : Loss

def bridgePathEndpoints
    (path : BridgePathRecord α β γ δ) : α × β :=
  (path.source, path.target)

/--
Even with fixed endpoints and loss payload, endpoint projection is not
injective: two paths can carry different witnesses. Hence endpoints alone
cannot identify a bridge path.
-/
theorem endpoints_do_not_identify_path
    (source : α) (target : β) (loss : δ) :
    ¬ Function.Injective
      (bridgePathEndpoints : BridgePathRecord α β Bool δ → α × β) := by
  intro injective
  let left : BridgePathRecord α β Bool δ :=
    { source := source
      target := target
      ruleGeneration := 0
      witness := false
      loss := loss }
  let right : BridgePathRecord α β Bool δ :=
    { source := source
      target := target
      ruleGeneration := 0
      witness := true
      loss := loss }
  have sameEndpoints : bridgePathEndpoints left = bridgePathEndpoints right := rfl
  have samePath : left = right := injective sameEndpoints
  have sameWitness : false = true :=
    congrArg (fun path : BridgePathRecord α β Bool δ => path.witness) samePath
  simp at sameWitness

/-- A deterministic map has an exact source round trip precisely via a left inverse. -/
def HasExactSourceRoundTrip (forward : α → β) : Prop :=
  ∃ reverse : β → α, Function.LeftInverse reverse forward

/-- Canonical embedding of a source into the verified image of a map. -/
def forwardIntoVerifiedImage (forward : α → β) (source : α) : Set.range forward :=
  ⟨forward source, ⟨source, rfl⟩⟩

/-- A reverse map exists on the verified image; it deliberately uses choice. -/
noncomputable def reverseFromVerifiedImage
    (forward : α → β) : Set.range forward → α :=
  fun target => Classical.choose target.property

theorem reverseFromVerifiedImage_spec
    (forward : α → β) (target : Set.range forward) :
    forward (reverseFromVerifiedImage forward target) = target.1 :=
  Classical.choose_spec target.property

/--
Every faithful embedding has exact source recovery on its verified image. This
does not define a reverse outside that image and therefore does not overstate a
partial correspondence as a total lens.
-/
theorem faithful_embedding_round_trip_on_verified_image
    (forward : α → β) (faithful : Function.Injective forward) :
    Function.LeftInverse (reverseFromVerifiedImage forward)
      (forwardIntoVerifiedImage forward) := by
  intro source
  apply faithful
  exact reverseFromVerifiedImage_spec forward (forwardIntoVerifiedImage forward source)

theorem faithful_embedding_has_exact_image_round_trip
    (forward : α → β) (faithful : Function.Injective forward) :
    HasExactSourceRoundTrip (forwardIntoVerifiedImage forward) :=
  ⟨reverseFromVerifiedImage forward,
    faithful_embedding_round_trip_on_verified_image forward faithful⟩

theorem exact_source_round_trip_implies_injective
    {forward : α → β} (roundTrip : HasExactSourceRoundTrip forward) :
    Function.Injective forward := by
  rcases roundTrip with ⟨reverse, leftInverse⟩
  exact leftInverse.injective

/--
Finite or infinite aliasing is already enough to forbid an exact deterministic
target-only inverse.  No cardinality or probability assumption is needed.
-/
theorem aliasing_blocks_exact_source_round_trip
    (forward : α → β) {left right : α}
    (distinct : left ≠ right) (aliased : forward left = forward right) :
    ¬ HasExactSourceRoundTrip forward := by
  intro roundTrip
  exact distinct ((exact_source_round_trip_implies_injective roundTrip) aliased)

/-! ### Task sufficiency and View no-go boundary -/

def ExactTaskRecoverable (observe : α → β) (task : α → γ) : Prop :=
  ∃ decode : β → γ, ∀ state, decode (observe state) = task state

def ExactTaskSufficientFor (observe : α → β) (task : α → γ) : Prop :=
  ∀ left right, observe left = observe right → task left = task right

theorem exactTaskRecoverable_implies_sufficient
    {observe : α → β} {task : α → γ}
    (recoverable : ExactTaskRecoverable observe task) :
    ExactTaskSufficientFor observe task := by
  rcases recoverable with ⟨decode, recovers⟩
  intro left right sameObservation
  rw [← recovers left, ← recovers right, sameObservation]

/-- A View that aliases task-distinct states cannot answer the task exactly. -/
theorem task_distinguishing_alias_blocks_exact_recovery
    (observe : α → β) (task : α → γ) {left right : α}
    (sameObservation : observe left = observe right)
    (differentTask : task left ≠ task right) :
    ¬ ExactTaskRecoverable observe task := by
  intro recoverable
  exact differentTask
    ((exactTaskRecoverable_implies_sufficient recoverable) left right sameObservation)

/-! ### Information-loss accounting -/

/-- Conservative loss composition: every forgotten distinction remains lost. -/
def ComposedLoss (first second : Set α) : Set α := first ∪ second

/-- Transport a typed distinction set across an explicit vocabulary adapter. -/
def TransportLoss (transport : α → β) (loss : Set α) : Set β :=
  transport '' loss

theorem transportLoss_union
    (transport : α → β) (first second : Set α) :
    TransportLoss transport (ComposedLoss first second) =
      ComposedLoss (TransportLoss transport first) (TransportLoss transport second) := by
  ext distinction
  constructor
  · rintro ⟨source, sourceLost, rfl⟩
    rcases sourceLost with leftLost | rightLost
    · exact Or.inl ⟨source, leftLost, rfl⟩
    · exact Or.inr ⟨source, rightLost, rfl⟩
  · rintro (⟨source, sourceLost, rfl⟩ | ⟨source, sourceLost, rfl⟩)
    · exact ⟨source, Or.inl sourceLost, rfl⟩
    · exact ⟨source, Or.inr sourceLost, rfl⟩

theorem transportLoss_comp
    (first : α → β) (second : β → γ) (loss : Set α) :
    TransportLoss second (TransportLoss first loss) =
      TransportLoss (second ∘ first) loss := by
  ext distinction
  simp [TransportLoss]

theorem first_loss_mono (first second : Set α) :
    first ⊆ ComposedLoss first second := by
  intro distinction lost
  exact Or.inl lost

theorem second_loss_mono (first second : Set α) :
    second ⊆ ComposedLoss first second := by
  intro distinction lost
  exact Or.inr lost

theorem composedLoss_assoc (first second third : Set α) :
    ComposedLoss (ComposedLoss first second) third =
      ComposedLoss first (ComposedLoss second third) := by
  ext distinction
  simp [ComposedLoss, or_assoc]

/-! ### Dynamic event fold -/

structure AssemblyEvent (EventId : Type uEvent) (Node : Type uNode) where
  eventId : EventId
  addedNodes : Set Node

structure AssemblyState (EventId : Type uEvent) (Node : Type uNode) where
  processed : Finset EventId
  nodes : Set Node

/-- At-least-once delivery becomes exactly-once state effect by event-id dedupe. -/
def applyAssemblyEvent {EventId : Type uEvent} {Node : Type uNode}
    [DecidableEq EventId]
    (state : AssemblyState EventId Node) (event : AssemblyEvent EventId Node) :
    AssemblyState EventId Node :=
  if event.eventId ∈ state.processed then state
  else
    { processed := insert event.eventId state.processed
      nodes := state.nodes ∪ event.addedNodes }

/-- Replaying the same event has no second state effect. -/
theorem applyAssemblyEvent_replay_idempotent
    {EventId : Type uEvent} {Node : Type uNode} [DecidableEq EventId]
    (state : AssemblyState EventId Node) (event : AssemblyEvent EventId Node) :
    applyAssemblyEvent (applyAssemblyEvent state event) event =
      applyAssemblyEvent state event := by
  by_cases seen : event.eventId ∈ state.processed
  · simp [applyAssemblyEvent, seen]
  · simp [applyAssemblyEvent, seen]

/-- Two previously unseen distinct additive events commute. -/
theorem distinct_unseen_additive_events_commute
    {EventId : Type uEvent} {Node : Type uNode} [DecidableEq EventId]
    (state : AssemblyState EventId Node)
    (left right : AssemblyEvent EventId Node)
    (leftFresh : left.eventId ∉ state.processed)
    (rightFresh : right.eventId ∉ state.processed)
    (distinct : left.eventId ≠ right.eventId) :
    applyAssemblyEvent (applyAssemblyEvent state left) right =
      applyAssemblyEvent (applyAssemblyEvent state right) left := by
  simp [applyAssemblyEvent, leftFresh, rightFresh, distinct, Ne.symm distinct,
    Finset.insert_comm, Set.union_comm, Set.union_left_comm]

/-- Minimal currentness state: any dependency-generation mismatch fails closed. -/
structure BridgeDependencyGeneration where
  source : Nat
  target : Nat
  rule : Nat
  context : Nat
  evidence : Nat
deriving DecidableEq

structure BridgeCurrentState where
  qualifiedAgainst : BridgeDependencyGeneration
  current : Bool

def recheckBridgeCurrent
    (observed : BridgeDependencyGeneration) (state : BridgeCurrentState) :
    BridgeCurrentState :=
  if observed = state.qualifiedAgainst then state
  else { qualifiedAgainst := observed, current := false }

theorem changed_dependency_invalidates
    (observed : BridgeDependencyGeneration) (state : BridgeCurrentState)
    (changed : observed ≠ state.qualifiedAgainst) :
    (recheckBridgeCurrent observed state).current = false := by
  simp [recheckBridgeCurrent, changed]

end OCKIndividuationMSpaceComposition
