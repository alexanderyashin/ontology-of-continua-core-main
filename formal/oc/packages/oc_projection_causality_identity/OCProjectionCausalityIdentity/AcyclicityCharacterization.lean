import OCProjectionCausalityIdentity.SeparatedTypes

namespace OCProjectionCausalityIdentity

universe uOccurrence uObject uCarrier

theorem transGen_rank_strict
    {α : Type uCarrier}
    {relation : α → α → Prop}
    {rank : α → Nat}
    (edgeStrict : ∀ ⦃left right⦄, relation left right → rank left < rank right)
    {left right : α}
    (path : Relation.TransGen relation left right) :
    rank left < rank right := by
  induction path with
  | single edge => exact edgeStrict edge
  | tail _ edge inductionHypothesis =>
      exact Nat.lt_trans inductionHypothesis (edgeStrict edge)

theorem natTopologicalRank_implies_noPositiveCycle
    {α : Type uCarrier}
    {relation : α → α → Prop}
    (ranked : HasNatTopologicalRank relation) :
    NoPositiveCycle relation := by
  rcases ranked with ⟨rank, edgeStrict⟩
  intro point loop
  exact (Nat.lt_irrefl (rank point)) (transGen_rank_strict edgeStrict loop)

noncomputable def predecessorFinset
    {α : Type uCarrier}
    [Fintype α]
    (relation : α → α → Prop)
    (point : α) : Finset α := by
  classical
  exact Finset.univ.filter (fun predecessor => Relation.TransGen relation predecessor point)

noncomputable def predecessorRank
    {α : Type uCarrier}
    [Fintype α]
    (relation : α → α → Prop)
    (point : α) : Nat :=
  (predecessorFinset relation point).card

theorem predecessorRank_strict_of_acyclic
    {α : Type uCarrier}
    [Fintype α]
    {relation : α → α → Prop}
    (acyclic : NoPositiveCycle relation)
    {left right : α}
    (edge : relation left right) :
    predecessorRank relation left < predecessorRank relation right := by
  classical
  apply Finset.card_lt_card
  rw [Finset.ssubset_iff_subset_ne]
  constructor
  · intro point membership
    simp only [predecessorFinset, Finset.mem_filter, Finset.mem_univ, true_and] at membership ⊢
    exact membership.tail edge
  · intro finsetsEqual
    have leftPrecedesRight : left ∈ predecessorFinset relation right := by
      simp only [predecessorFinset, Finset.mem_filter, Finset.mem_univ, true_and]
      exact Relation.TransGen.single edge
    have leftPrecedesSelf : left ∈ predecessorFinset relation left := by
      rw [finsetsEqual]
      exact leftPrecedesRight
    have loop : Relation.TransGen relation left left := by
      simpa only [predecessorFinset, Finset.mem_filter, Finset.mem_univ, true_and] using
        leftPrecedesSelf
    exact acyclic left loop

/-- Exact finite rank characterization of a directed acyclic relation. -/
theorem finite_noPositiveCycle_iff_natTopologicalRank
    {α : Type uCarrier}
    [Fintype α]
    (relation : α → α → Prop) :
    NoPositiveCycle relation ↔ HasNatTopologicalRank relation := by
  constructor
  · intro acyclic
    refine ⟨predecessorRank relation, ?_⟩
    intro left right edge
    exact predecessorRank_strict_of_acyclic
      (relation := relation) acyclic edge
  · exact natTopologicalRank_implies_noPositiveCycle

/-- Exact SCC characterization using positive mutual reachability. -/
theorem noPositiveCycle_iff_noPositiveMutualReachability
    {α : Type uCarrier}
    (relation : α → α → Prop) :
    NoPositiveCycle relation ↔
      ∀ left right, ¬ PositiveMutualReachability relation left right := by
  constructor
  · intro acyclic left right mutualReachability
    exact acyclic left
      (Relation.TransGen.trans mutualReachability.1 mutualReachability.2)
  · intro noMutual point loop
    exact noMutual point point ⟨loop, loop⟩

theorem macroPath_has_stitched_lift
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    {source target : Object}
    (path : Relation.TransGen (MacroEdge micro assemble) source target) :
    ∃ start finalSource finalTarget,
      assemble start = source ∧ assemble finalTarget = target ∧
        Relation.ReflTransGen (StitchedStep micro assemble) start finalSource ∧
          micro finalSource finalTarget := by
  induction path with
  | single edge =>
      rcases edge with ⟨left, right, microEdge, leftClass, rightClass⟩
      exact ⟨left, left, right, leftClass, rightClass,
        Relation.ReflTransGen.refl, microEdge⟩
  | tail path edge inductionHypothesis =>
      rcases inductionHypothesis with
        ⟨start, previousSource, previousTarget,
          startClass, previousTargetClass, stitchedPath, previousEdge⟩
      rcases edge with ⟨nextSource, nextTarget, nextEdge, nextSourceClass, nextTargetClass⟩
      have join : StitchedStep micro assemble previousSource nextSource := by
        exact ⟨previousTarget, previousEdge, previousTargetClass.trans nextSourceClass.symm⟩
      exact ⟨start, nextSource, nextTarget,
        startClass, nextTargetClass, stitchedPath.tail join, nextEdge⟩

theorem stitchedPath_then_edge_is_macroPath
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    {start finalSource finalTarget : Occurrence}
    (stitchedPath :
      Relation.ReflTransGen (StitchedStep micro assemble) start finalSource)
    (finalEdge : micro finalSource finalTarget) :
    Relation.TransGen (MacroEdge micro assemble)
      (assemble start) (assemble finalTarget) := by
  induction stitchedPath generalizing finalTarget with
  | refl =>
      exact Relation.TransGen.single ⟨start, finalTarget, finalEdge, rfl, rfl⟩
  | @tail middle finalSource path stitchedStep inductionHypothesis =>
      rcases stitchedStep with ⟨bridgeTarget, bridgeEdge, bridgeClass⟩
      have macroPrefix :
          Relation.TransGen (MacroEdge micro assemble)
            (assemble start) (assemble bridgeTarget) :=
        inductionHypothesis bridgeEdge
      have alignedPrefix :
          Relation.TransGen (MacroEdge micro assemble)
            (assemble start) (assemble finalSource) := by
        simpa only [bridgeClass] using macroPrefix
      exact alignedPrefix.tail
        ⟨finalSource, finalTarget, finalEdge, rfl, rfl⟩

/-- Exact micro alternating-witness characterization of existential macro cycles. -/
theorem macroCycle_iff_alternatingCycle
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object) :
    HasPositiveCycle (MacroEdge micro assemble) ↔ AlternatingCycle micro assemble := by
  constructor
  · rintro ⟨object, cycle⟩
    rcases macroPath_has_stitched_lift cycle with
      ⟨start, finalSource, finalTarget,
        startClass, finalClass, stitchedPath, finalEdge⟩
    exact ⟨start, finalSource, finalTarget, stitchedPath, finalEdge,
      finalClass.trans startClass.symm⟩
  · rintro ⟨start, finalSource, finalTarget, stitchedPath, finalEdge, sameClass⟩
    refine ⟨assemble start, ?_⟩
    have path := stitchedPath_then_edge_is_macroPath stitchedPath finalEdge
    simpa only [sameClass] using path

end OCProjectionCausalityIdentity
