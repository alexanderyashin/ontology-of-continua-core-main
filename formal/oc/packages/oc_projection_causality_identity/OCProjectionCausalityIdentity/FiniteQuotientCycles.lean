import OCProjectionCausalityIdentity.AcyclicityCharacterization
import Mathlib.Tactic.DeriveFintype

namespace OCProjectionCausalityIdentity

universe uOccurrence uObject

/-- The smallest path-shaped witness for a reciprocal two-object macro cycle. -/
inductive ThreeToken
  | a0
  | b
  | a1
  deriving DecidableEq, Fintype, Repr

inductive TwoObject
  | a
  | b
  deriving DecidableEq, Fintype, Repr

def threeTokenCausal : ThreeToken → ThreeToken → Prop
  | .a0, .b => True
  | .b, .a1 => True
  | _, _ => False

def threeTokenAssembly : ThreeToken → TwoObject
  | .a0 => .a
  | .b => .b
  | .a1 => .a

def threeTokenRank : ThreeToken → Nat
  | .a0 => 0
  | .b => 1
  | .a1 => 2

theorem threeTokenCausal_rank_strict :
    ∀ ⦃left right⦄,
      threeTokenCausal left right → threeTokenRank left < threeTokenRank right := by
  intro left right edge
  cases left <;> cases right <;> simp_all [threeTokenCausal, threeTokenRank]

theorem threeTokenCausal_acyclic : NoPositiveCycle threeTokenCausal :=
  natTopologicalRank_implies_noPositiveCycle
    ⟨threeTokenRank, threeTokenCausal_rank_strict⟩

theorem threeToken_macro_a_to_b :
    MacroEdge threeTokenCausal threeTokenAssembly .a .b := by
  exact ⟨.a0, .b, trivial, rfl, rfl⟩

theorem threeToken_macro_b_to_a :
    MacroEdge threeTokenCausal threeTokenAssembly .b .a := by
  exact ⟨.b, .a1, trivial, rfl, rfl⟩

theorem threeToken_quotient_has_reciprocal_cycle :
    HasPositiveCycle (MacroEdge threeTokenCausal threeTokenAssembly) := by
  exact ⟨.a,
    (Relation.TransGen.single threeToken_macro_a_to_b).tail threeToken_macro_b_to_a⟩

/-- Macro reciprocity is compatible with a micro DAG and hence does not imply a micro loop. -/
theorem macro_reciprocity_does_not_imply_micro_cycle :
    MacroEdge threeTokenCausal threeTokenAssembly .a .b ∧
      MacroEdge threeTokenCausal threeTokenAssembly .b .a ∧
      NoPositiveCycle threeTokenCausal := by
  exact ⟨threeToken_macro_a_to_b, threeToken_macro_b_to_a,
    threeTokenCausal_acyclic⟩

/-- A diagonal macro edge is exactly an internal micro evolution witness. -/
theorem macro_self_loop_iff_internalEvolution
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object)
    (object : Object) :
    MacroEdge micro assemble object object ↔ InternalEvolution micro assemble object := by
  rfl

/-- Three selected values are pairwise different. -/
def PairwiseDistinct3 {α : Type uOccurrence} (first second third : α) : Prop :=
  first ≠ second ∧ first ≠ third ∧ second ≠ third

/--
Any reciprocal cycle between two distinct macro-objects over an acyclic micro
relation requires at least three distinct micro occurrences.
-/
theorem reciprocal_macro_edges_require_three_micro_occurrences
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    {objectA objectB : Object}
    (differentObjects : objectA ≠ objectB)
    (aToB : MacroEdge micro assemble objectA objectB)
    (bToA : MacroEdge micro assemble objectB objectA)
    (microAcyclic : NoPositiveCycle micro) :
    ∃ (first second third : Occurrence),
      PairwiseDistinct3 first second third := by
  rcases aToB with
    ⟨aSource, bTarget, aToBEdge, aSourceClass, bTargetClass⟩
  rcases bToA with
    ⟨bSource, aTarget, bToAEdge, bSourceClass, aTargetClass⟩
  have aSource_ne_bTarget : aSource ≠ bTarget := by
    intro same
    apply differentObjects
    calc
      objectA = assemble aSource := aSourceClass.symm
      _ = assemble bTarget := congrArg assemble same
      _ = objectB := bTargetClass
  have aSource_ne_bSource : aSource ≠ bSource := by
    intro same
    apply differentObjects
    calc
      objectA = assemble aSource := aSourceClass.symm
      _ = assemble bSource := congrArg assemble same
      _ = objectB := bSourceClass
  have bTarget_ne_aTarget : bTarget ≠ aTarget := by
    intro same
    apply differentObjects
    calc
      objectA = assemble aTarget := aTargetClass.symm
      _ = assemble bTarget := (congrArg assemble same).symm
      _ = objectB := bTargetClass
  by_cases bSourcesDiffer : bSource ≠ bTarget
  · refine ⟨aSource, bTarget, bSource, ?_⟩
    exact ⟨aSource_ne_bTarget, aSource_ne_bSource,
      fun same => bSourcesDiffer same.symm⟩
  · have bSource_eq_bTarget : bSource = bTarget := not_ne_iff.mp bSourcesDiffer
    by_cases aTargetsDiffer : aTarget ≠ aSource
    · refine ⟨aSource, bTarget, aTarget, ?_⟩
      exact ⟨aSource_ne_bTarget,
        fun same => aTargetsDiffer same.symm,
        bTarget_ne_aTarget⟩
    · have aTarget_eq_aSource : aTarget = aSource := not_ne_iff.mp aTargetsDiffer
      subst bSource
      subst aTarget
      have microLoop : Relation.TransGen micro aSource aSource :=
        (Relation.TransGen.single aToBEdge).tail bToAEdge
      exact (microAcyclic aSource microLoop).elim

theorem transGen_maps_to_macro
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    {left right : Occurrence}
    (path : Relation.TransGen micro left right) :
    Relation.TransGen (MacroEdge micro assemble) (assemble left) (assemble right) := by
  exact path.lift assemble
    (fun left right edge => ⟨left, right, edge, rfl, rfl⟩)

/-- Mapping a length-indexed micro path preserves its exact edge count. -/
theorem edgePath_maps_to_macro
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    {length : Nat}
    {left right : Occurrence}
    (path : EdgePath micro length left right) :
    EdgePath (MacroEdge micro assemble) length (assemble left) (assemble right) := by
  induction path with
  | single edge =>
      exact EdgePath.single ⟨_, _, edge, rfl, rfl⟩
  | tail path edge inductionHypothesis =>
      exact EdgePath.tail inductionHypothesis ⟨_, _, edge, rfl, rfl⟩

/-- Any positive micro path becomes a macro cycle when its endpoints are assembled together. -/
theorem collapsed_micro_path_creates_macro_cycle
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    {left right : Occurrence}
    (path : Relation.TransGen micro left right)
    (sameObject : assemble left = assemble right) :
    HasPositiveCycle (MacroEdge micro assemble) := by
  refine ⟨assemble left, ?_⟩
  have macroPath := transGen_maps_to_macro (assemble := assemble) path
  simpa only [sameObject] using macroPath

/-- Length-indexed form of the endpoint-collapse construction. -/
theorem n_edge_path_endpoint_collapse_creates_macro_cycle
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    {length : Nat}
    {left right : Occurrence}
    (path : EdgePath micro length left right)
    (sameObject : assemble left = assemble right) :
    HasPositiveCycle (MacroEdge micro assemble) :=
  collapsed_micro_path_creates_macro_cycle path.toTransGen sameObject

/--
Exact-length form of the construction: endpoint collapse turns an `n`-edge
micro path into an `n`-edge closed macro walk.  Distinctness of intermediate
macro objects is intentionally not inferred.
-/
theorem n_edge_path_endpoint_collapse_creates_n_edge_macro_closedWalk
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    {length : Nat}
    {left right : Occurrence}
    (path : EdgePath micro length left right)
    (sameObject : assemble left = assemble right) :
    EdgePath (MacroEdge micro assemble) length (assemble left) (assemble left) := by
  have macroPath := edgePath_maps_to_macro (assemble := assemble) path
  simpa only [sameObject] using macroPath

theorem injective_assembly_reflects_macro_cycle
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    (injectiveAssembly : Function.Injective assemble)
    (macroCycle : HasPositiveCycle (MacroEdge micro assemble)) :
    HasPositiveCycle micro := by
  rcases (macroCycle_iff_alternatingCycle micro assemble).1 macroCycle with
    ⟨start, finalSource, finalTarget, stitchedPath, finalEdge, sameClass⟩
  have stitchedStepReflects :
      ∀ ⦃left right⦄, StitchedStep micro assemble left right → micro left right := by
    rintro left right ⟨target, edge, targetClass⟩
    exact injectiveAssembly targetClass ▸ edge
  have microPrefix : Relation.ReflTransGen micro start finalSource := by
    exact stitchedPath.mono
      (fun _ _ stitchedStep => stitchedStepReflects stitchedStep)
  have endpointEquality : finalTarget = start := injectiveAssembly sameClass
  subst finalTarget
  exact ⟨start, Relation.TransGen.tail' microPrefix finalEdge⟩

/-- A cyclic quotient of an acyclic micro relation must identify two occurrences. -/
theorem acyclic_micro_cyclic_macro_forces_noninjective_assembly
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    (microAcyclic : NoPositiveCycle micro)
    (macroCycle : HasPositiveCycle (MacroEdge micro assemble)) :
    ¬ Function.Injective assemble := by
  intro injectiveAssembly
  rcases injective_assembly_reflects_macro_cycle injectiveAssembly macroCycle with
    ⟨point, microLoop⟩
  exact microAcyclic point microLoop

/--
Finite cardinal minimality: a surjective cyclic quotient of an acyclic micro
relation has strictly more occurrences than macro-objects.
-/
theorem cyclic_quotient_requires_more_occurrences_than_objects
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    [Fintype Occurrence]
    [Fintype Object]
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    (surjectiveAssembly : Function.Surjective assemble)
    (microAcyclic : NoPositiveCycle micro)
    (macroCycle : HasPositiveCycle (MacroEdge micro assemble)) :
    Fintype.card Object < Fintype.card Occurrence := by
  exact Fintype.card_lt_of_surjective_not_injective assemble surjectiveAssembly
    (acyclic_micro_cyclic_macro_forces_noninjective_assembly microAcyclic macroCycle)

end OCProjectionCausalityIdentity
