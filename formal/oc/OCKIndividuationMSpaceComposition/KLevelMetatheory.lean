import Mathlib.Order.Basic

namespace OCKIndividuationMSpaceComposition

/-!
# Task-relative K-level metatheory

K-depth is the length of a witnessed decomposition chain in an explicitly
declared context.  This makes the ontic relation, the observational boundary,
and the analyst's task separate inputs instead of silently identifying them.
-/

universe u v

structure HierarchyContext where
  Entity : Type u
  child : Entity → Entity → Prop

inductive ChainFrom (context : HierarchyContext) :
    context.Entity → Nat → Prop where
  | nil (root : context.Entity) : ChainFrom context root 0
  | cons {root child : context.Entity} {depth : Nat} :
      context.child child root →
      ChainFrom context child depth →
      ChainFrom context root (depth + 1)

def HasKDepth (context : HierarchyContext) (root : context.Entity)
    (depth : Nat) : Prop :=
  ChainFrom context root depth

def ExactKHeight (context : HierarchyContext) (root : context.Entity)
    (height : Nat) : Prop :=
  HasKDepth context root height ∧ ¬ HasKDepth context root (height + 1)

theorem chain_of_le {context : HierarchyContext} {root : context.Entity}
    {large : Nat} (chain : ChainFrom context root large) :
    ∀ small, small ≤ large → ChainFrom context root small := by
  induction chain with
  | nil root =>
      intro small bounded
      have equal : small = 0 := Nat.eq_zero_of_le_zero bounded
      subst small
      exact ChainFrom.nil root
  | @cons root child depth edge tail inductionHypothesis =>
      intro small bounded
      cases small with
      | zero => exact ChainFrom.nil root
      | succ small =>
          exact ChainFrom.cons edge
            (inductionHypothesis small (Nat.succ_le_succ_iff.mp bounded))

theorem chain_prefix {context : HierarchyContext} {root : context.Entity}
    {depth : Nat} (chain : ChainFrom context root (depth + 1)) :
    ChainFrom context root depth :=
  chain_of_le chain depth (Nat.le_succ depth)

theorem exact_k_height_unique {context : HierarchyContext}
    {root : context.Entity} {left right : Nat}
    (leftExact : ExactKHeight context root left)
    (rightExact : ExactKHeight context root right) :
    left = right := by
  rcases Nat.lt_trichotomy left right with leftLt | equal | rightLt
  · exfalso
    exact leftExact.2 (chain_of_le rightExact.1 (left + 1) leftLt)
  · exact equal
  · exfalso
    exact rightExact.2 (chain_of_le leftExact.1 (right + 1) rightLt)

abbrev LinearHierarchy : HierarchyContext where
  Entity := Nat
  child := fun child parent => child = parent + 1

theorem linear_hierarchy_has_every_finite_depth (root depth : Nat) :
    HasKDepth LinearHierarchy root depth := by
  induction depth generalizing root with
  | zero =>
      show ChainFrom LinearHierarchy root 0
      exact @ChainFrom.nil LinearHierarchy root
  | succ depth inductionHypothesis =>
      exact @ChainFrom.cons LinearHierarchy root (root + 1) depth rfl
        (inductionHypothesis (root + 1))

theorem no_finite_universal_k_ceiling :
    ¬ ∃ ceiling : Nat, ∀ root : Nat,
      ¬ HasKDepth LinearHierarchy root (ceiling + 1) := by
  intro claimed
  rcases claimed with ⟨ceiling, bound⟩
  exact bound 0 (linear_hierarchy_has_every_finite_depth 0 (ceiling + 1))

structure HierarchyEmbedding (source : HierarchyContext)
    (target : HierarchyContext) where
  map : source.Entity → target.Entity
  preservesChild : ∀ {child parent}, source.child child parent →
    target.child (map child) (map parent)

theorem HierarchyEmbedding.maps_chain
    {source : HierarchyContext} {target : HierarchyContext}
    (embedding : HierarchyEmbedding source target)
    {root : source.Entity} {depth : Nat}
    (chain : ChainFrom source root depth) :
    ChainFrom target (embedding.map root) depth := by
  induction chain with
  | nil root => exact ChainFrom.nil (embedding.map root)
  | cons edge tail inductionHypothesis =>
      exact ChainFrom.cons (embedding.preservesChild edge) inductionHypothesis

theorem embedding_cannot_reduce_witnessed_depth
    {source : HierarchyContext} {target : HierarchyContext}
    (embedding : HierarchyEmbedding source target)
    {root : source.Entity} {depth : Nat}
    (witness : HasKDepth source root depth) :
    HasKDepth target (embedding.map root) depth :=
  embedding.maps_chain witness

/-! A task does not create the underlying child relation, but it selects which
entities and edges count as observable and relevant for the stated prediction.
-/
structure KObservation (context : HierarchyContext) where
  visible : context.Entity → Prop
  relevantEdge : ∀ {child parent}, context.child child parent → Prop

def ObservedHierarchy (context : HierarchyContext)
    (observation : KObservation context) : HierarchyContext where
  Entity := {entity : context.Entity // observation.visible entity}
  child := fun child parent =>
    ∃ edge : context.child child.1 parent.1, observation.relevantEdge edge

theorem observed_chain_has_underlying_chain
    (context : HierarchyContext) (observation : KObservation context)
    {root : (ObservedHierarchy context observation).Entity} {depth : Nat}
    (observed : ChainFrom (ObservedHierarchy context observation) root depth) :
    ChainFrom context root.1 depth := by
  induction observed with
  | nil root => exact ChainFrom.nil root.1
  | cons edge tail inductionHypothesis =>
      rcases edge with ⟨underlying, _⟩
      exact ChainFrom.cons underlying inductionHypothesis

theorem observation_cannot_invent_underlying_depth
    (context : HierarchyContext) (observation : KObservation context)
    {root : (ObservedHierarchy context observation).Entity} {depth : Nat}
    (observed : HasKDepth (ObservedHierarchy context observation) root depth) :
    HasKDepth context root.1 depth :=
  observed_chain_has_underlying_chain context observation observed

end OCKIndividuationMSpaceComposition
