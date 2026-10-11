import OCProjectionCausalityIdentity.FiniteQuotientCycles

namespace OCProjectionCausalityIdentity

universe uOccurrence uObject uCarrier

theorem transGen_collapses_of_transitive
    {α : Type uCarrier}
    {relation : α → α → Prop}
    (transitive : Transitive relation)
    {left right : α}
    (path : Relation.TransGen relation left right) :
    relation left right := by
  induction path with
  | single edge => exact edge
  | tail _ edge inductionHypothesis => exact transitive inductionHypothesis edge

theorem transitive_irreflexive_is_acyclic
    {α : Type uCarrier}
    {relation : α → α → Prop}
    (transitive : Transitive relation)
    (irreflexive : Irreflexive relation) :
    NoPositiveCycle relation := by
  intro point loop
  exact irreflexive point (transGen_collapses_of_transitive transitive loop)

theorem convex_externalMacro_uniform_direction
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    [LinearOrder Occurrence]
    {assemble : Occurrence → Object}
    (convex : FiberConvexFor (· ≤ ·) assemble)
    {objectA objectB : Object}
    (macroEdge : ExternalMacroEdge (· < ·) assemble objectA objectB)
    {left right : Occurrence}
    (leftClass : assemble left = objectA)
    (rightClass : assemble right = objectB) :
    left < right := by
  rcases macroEdge with
    ⟨differentObjects, ⟨aWitness, bWitness, witnessEdge, aClass, bClass⟩⟩
  have left_lt_bWitness : left < bWitness := by
    by_contra notLess
    have bWitness_le_left : bWitness ≤ left := le_of_not_gt notLess
    have bWitnessInA : assemble bWitness = assemble aWitness :=
      convex (le_of_lt witnessEdge) bWitness_le_left (aClass.trans leftClass.symm)
    apply differentObjects
    calc
      objectA = assemble aWitness := aClass.symm
      _ = assemble bWitness := bWitnessInA.symm
      _ = objectB := bClass
  by_contra notLess
  have right_le_left : right ≤ left := le_of_not_gt notLess
  have leftInB : assemble left = assemble right :=
    convex right_le_left (le_of_lt left_lt_bWitness) (rightClass.trans bClass.symm)
  apply differentObjects
  calc
    objectA = assemble left := leftClass.symm
    _ = assemble right := leftInB
    _ = objectB := rightClass

theorem convex_externalMacro_transitive
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    [LinearOrder Occurrence]
    {assemble : Occurrence → Object}
    (convex : FiberConvexFor (· ≤ ·) assemble) :
    Transitive (ExternalMacroEdge (· < ·) assemble) := by
  intro objectA objectB objectC aToB bToC
  rcases aToB.2 with
    ⟨aWitness, bWitness, aToBEdge, aClass, bClass⟩
  rcases bToC.2 with
    ⟨bWitness', cWitness, bToCEdge, bClass', cClass⟩
  have a_lt_bWitness' : aWitness < bWitness' :=
    convex_externalMacro_uniform_direction convex aToB aClass bClass'
  have a_lt_c : aWitness < cWitness := lt_trans a_lt_bWitness' bToCEdge
  have differentEndpoints : objectA ≠ objectC := by
    intro sameEndpointClass
    have middleInA : assemble bWitness' = assemble aWitness :=
      convex (le_of_lt a_lt_bWitness') (le_of_lt bToCEdge)
        (aClass.trans (sameEndpointClass.trans cClass.symm))
    apply aToB.1
    calc
      objectA = assemble aWitness := aClass.symm
      _ = assemble bWitness' := middleInA.symm
      _ = objectB := bClass'
  exact ⟨differentEndpoints,
    ⟨aWitness, cWitness, a_lt_c, aClass, cClass⟩⟩

theorem externalMacro_irreflexive
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object) :
    Irreflexive (ExternalMacroEdge micro assemble) := by
  intro object loop
  exact loop.1 rfl

/-- Convex fibers of a total order force the external quotient graph to be acyclic. -/
theorem totalOrder_convexFibers_imply_externalMacro_acyclic
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    [LinearOrder Occurrence]
    {assemble : Occurrence → Object}
    (convex : FiberConvexFor (· ≤ ·) assemble) :
    NoPositiveCycle (ExternalMacroEdge (· < ·) assemble) :=
  transitive_irreflexive_is_acyclic
    (convex_externalMacro_transitive convex)
    (externalMacro_irreflexive (· < ·) assemble)

/-- For a total order, external quotient acyclicity also forces fiber convexity. -/
theorem totalOrder_externalMacro_acyclic_implies_convexFibers
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    [LinearOrder Occurrence]
    {assemble : Occurrence → Object}
    (acyclic : NoPositiveCycle (ExternalMacroEdge (· < ·) assemble)) :
    FiberConvexFor (· ≤ ·) assemble := by
  intro left middle right left_le_middle middle_le_right sameEndpoints
  by_contra middleNotInFiber
  have left_ne_middle : left ≠ middle := by
    intro same
    apply middleNotInFiber
    simpa only [same]
  have middle_ne_right : middle ≠ right := by
    intro same
    apply middleNotInFiber
    calc
      assemble middle = assemble right := congrArg assemble same
      _ = assemble left := sameEndpoints.symm
  have left_lt_middle : left < middle := lt_of_le_of_ne left_le_middle left_ne_middle
  have middle_lt_right : middle < right := lt_of_le_of_ne middle_le_right middle_ne_right
  have leftToMiddle :
      ExternalMacroEdge (· < ·) assemble (assemble left) (assemble middle) := by
    exact ⟨fun same => middleNotInFiber same.symm,
      ⟨left, middle, left_lt_middle, rfl, rfl⟩⟩
  have middleToLeft :
      ExternalMacroEdge (· < ·) assemble (assemble middle) (assemble left) := by
    exact ⟨middleNotInFiber,
      ⟨middle, right, middle_lt_right, rfl, sameEndpoints.symm⟩⟩
  exact acyclic (assemble left)
    ((Relation.TransGen.single leftToMiddle).tail middleToLeft)

/-- Exact total-order characterization. -/
theorem totalOrder_convexFibers_iff_externalMacro_acyclic
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    [LinearOrder Occurrence]
    (assemble : Occurrence → Object) :
    FiberConvexFor (· ≤ ·) assemble ↔
      NoPositiveCycle (ExternalMacroEdge (· < ·) assemble) := by
  constructor
  · exact totalOrder_convexFibers_imply_externalMacro_acyclic
  · exact totalOrder_externalMacro_acyclic_implies_convexFibers

/-- Four points forming two disconnected two-element chains. -/
inductive TwoChainPoint
  | a0
  | b0
  | b1
  | a1
  deriving DecidableEq, Fintype, Repr

def twoChainLE : TwoChainPoint → TwoChainPoint → Prop
  | left, right =>
      left = right ∨
        (left = .a0 ∧ right = .b0) ∨
        (left = .b1 ∧ right = .a1)

def twoChainLT : TwoChainPoint → TwoChainPoint → Prop
  | .a0, .b0 => True
  | .b1, .a1 => True
  | _, _ => False

def twoChainAssembly : TwoChainPoint → TwoObject
  | .a0 => .a
  | .a1 => .a
  | .b0 => .b
  | .b1 => .b

def IsPartialOrderRelation
    {α : Type uCarrier}
    (order : α → α → Prop) : Prop :=
  (∀ point, order point point) ∧
    (∀ left right, order left right → order right left → left = right) ∧
    (∀ left middle right, order left middle → order middle right → order left right)

theorem twoChainLE_is_partial_order_relation : IsPartialOrderRelation twoChainLE := by
  constructor
  · intro point
    cases point <;> simp [twoChainLE]
  constructor
  · intro left right leftToRight rightToLeft
    cases left <;> cases right <;>
      simp_all [twoChainLE]
  · intro left middle right leftToMiddle middleToRight
    cases left <;> cases middle <;> cases right <;>
      simp_all [twoChainLE]

theorem twoChainAssembly_fibers_are_convex :
    FiberConvexFor twoChainLE twoChainAssembly := by
  intro left middle right leftToMiddle middleToRight sameEndpoints
  cases left <;> cases middle <;> cases right <;>
    simp_all [twoChainLE, twoChainAssembly]

theorem partialOrder_convex_fibers_can_have_reciprocal_quotient :
    FiberConvexFor twoChainLE twoChainAssembly ∧
      IsPartialOrderRelation twoChainLE ∧
      HasPositiveCycle (ExternalMacroEdge twoChainLT twoChainAssembly) := by
  refine ⟨twoChainAssembly_fibers_are_convex,
    twoChainLE_is_partial_order_relation, ?_⟩
  have aToB : ExternalMacroEdge twoChainLT twoChainAssembly .a .b := by
    exact ⟨by decide, ⟨.a0, .b0, trivial, rfl, rfl⟩⟩
  have bToA : ExternalMacroEdge twoChainLT twoChainAssembly .b .a := by
    exact ⟨by decide, ⟨.b1, .a1, trivial, rfl, rfl⟩⟩
  exact ⟨.a, (Relation.TransGen.single aToB).tail bToA⟩

theorem strongCongruence_reflects_macroCycle
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    (congruence : StrongQuotientCongruence micro assemble)
    (macroCycle : HasPositiveCycle (MacroEdge micro assemble)) :
    HasPositiveCycle micro := by
  rcases (macroCycle_iff_alternatingCycle micro assemble).1 macroCycle with
    ⟨start, finalSource, finalTarget, stitchedPath, finalEdge, sameClass⟩
  have stitchedStepReflects :
      ∀ ⦃left right⦄, StitchedStep micro assemble left right → micro left right := by
    rintro left right ⟨target, edge, targetClass⟩
    exact congruence rfl targetClass edge
  have microPrefix : Relation.ReflTransGen micro start finalSource := by
    exact stitchedPath.mono
      (fun _ _ stitchedStep => stitchedStepReflects stitchedStep)
  have closingEdge : micro finalSource start := congruence rfl sameClass finalEdge
  exact ⟨start, Relation.TransGen.tail' microPrefix closingEdge⟩

/-- Strong representative congruence is sufficient for acyclicity preservation. -/
theorem strongCongruence_preserves_acyclicity
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    (microAcyclic : NoPositiveCycle micro)
    (congruence : StrongQuotientCongruence micro assemble) :
    NoPositiveCycle (MacroEdge micro assemble) := by
  intro object macroLoop
  rcases strongCongruence_reflects_macroCycle congruence ⟨object, macroLoop⟩ with
    ⟨point, microLoop⟩
  exact microAcyclic point microLoop

def oneCrossEdge : TwoChainPoint → TwoChainPoint → Prop
  | .a0, .b0 => True
  | _, _ => False

def twoObjectRank : TwoObject → Nat
  | .a => 0
  | .b => 1

theorem oneCrossEdge_iff
    {source target : TwoChainPoint} :
    oneCrossEdge source target ↔ source = .a0 ∧ target = .b0 := by
  cases source <;> cases target <;> simp [oneCrossEdge]

theorem oneCrossMacro_rank_strict :
    ∀ ⦃left right⦄,
      MacroEdge oneCrossEdge twoChainAssembly left right →
        twoObjectRank left < twoObjectRank right := by
  intro left right edge
  rcases edge with ⟨source, target, microEdge, sourceClass, targetClass⟩
  rcases oneCrossEdge_iff.mp microEdge with ⟨rfl, rfl⟩
  have leftIsA : left = .a := sourceClass.symm
  have rightIsB : right = .b := targetClass.symm
  subst left
  subst right
  decide

theorem oneCrossMacro_acyclic :
    NoPositiveCycle (MacroEdge oneCrossEdge twoChainAssembly) :=
  natTopologicalRank_implies_noPositiveCycle
    ⟨twoObjectRank, oneCrossMacro_rank_strict⟩

theorem oneCrossEdge_not_strongCongruence :
    ¬ StrongQuotientCongruence oneCrossEdge twoChainAssembly := by
  intro congruence
  have forced : oneCrossEdge .a1 .b1 :=
    congruence (left := .a0) (left' := .a1) (right := .b0) (right' := .b1)
      rfl rfl trivial
  exact forced

/-- Strong congruence is sufficient but not necessary for quotient acyclicity. -/
theorem strongCongruence_is_not_necessary_for_macro_acyclicity :
    NoPositiveCycle (MacroEdge oneCrossEdge twoChainAssembly) ∧
      ¬ StrongQuotientCongruence oneCrossEdge twoChainAssembly :=
  ⟨oneCrossMacro_acyclic, oneCrossEdge_not_strongCongruence⟩

end OCProjectionCausalityIdentity
