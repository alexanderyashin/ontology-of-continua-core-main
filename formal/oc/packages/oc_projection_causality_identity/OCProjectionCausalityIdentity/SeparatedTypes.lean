import Mathlib.Logic.Relation
import Mathlib.Data.Fintype.EquivFin
import Mathlib.Data.Finset.Card

/-!
# Projection causality and persistent identity: separated finite vocabulary

The event-causal relation, continuation evidence, object assembly, evidence
support and classification are deliberately different fields.  In particular,
no quotient or persistent object is postulated by `OperationalSignature`.
-/

namespace OCProjectionCausalityIdentity

universe uOccurrence uContext uObject uCarrier

/-- A typed operational vocabulary before any identity quotient is selected. -/
structure OperationalSignature where
  Occurrence : Type uOccurrence
  Context : Type uContext
  StableObject : Context → Type uObject
  formationSupport : Context → Finset Occurrence → Occurrence → Prop
  causalBefore : Context → Occurrence → Occurrence → Prop
  continuation : Context → Occurrence → Occurrence → Prop
  assemblyMember : (context : Context) → Occurrence → StableObject context → Prop
  evidenceSupports : Context → Occurrence → Occurrence → Prop
  classifiedWith : Context → Occurrence → Occurrence → Prop

/--
A functional assembly is an additional certificate.  It is stronger than a
general membership relation: every occurrence has exactly one object at the
chosen context and the supplied membership relation is exactly that graph.
-/
structure FunctionalAssembly
    (signature : OperationalSignature)
    (context : signature.Context) where
  objectOf : signature.Occurrence → signature.StableObject context
  realizesMembership :
    ∀ occurrence object,
      signature.assemblyMember context occurrence object ↔ objectOf occurrence = object

/-- Existential image of a micro-relation under an assembly map. -/
def MacroEdge
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object)
    (source target : Object) : Prop :=
  ∃ left right,
    micro left right ∧ assemble left = source ∧ assemble right = target

/-- Inter-object macro edge; diagonal/internal evolution is excluded explicitly. -/
def ExternalMacroEdge
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object)
    (source target : Object) : Prop :=
  source ≠ target ∧ MacroEdge micro assemble source target

/-- A micro edge whose endpoints are assembled into the same macro-object. -/
def InternalEvolution
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object)
    (object : Object) : Prop :=
  ∃ left right,
    micro left right ∧ assemble left = object ∧ assemble right = object

/-- Absence of every positive-length directed loop. -/
def NoPositiveCycle {α : Type uCarrier} (relation : α → α → Prop) : Prop :=
  ∀ point, ¬ Relation.TransGen relation point point

/-- Existence of a positive-length directed loop. -/
def HasPositiveCycle {α : Type uCarrier} (relation : α → α → Prop) : Prop :=
  ∃ point, Relation.TransGen relation point point

/-- A natural-valued topological rank strictly increases on every edge. -/
def HasNatTopologicalRank
    {α : Type uCarrier}
    (relation : α → α → Prop) : Prop :=
  ∃ rank : α → Nat, ∀ ⦃left right⦄, relation left right → rank left < rank right

/-- Positive mutual reachability, the non-trivial part of an SCC witness. -/
def PositiveMutualReachability
    {α : Type uCarrier}
    (relation : α → α → Prop)
    (left right : α) : Prop :=
  Relation.TransGen relation left right ∧ Relation.TransGen relation right left

/-- One causal edge followed by an identity-class switch at its target. -/
def StitchedStep
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object)
    (source nextSource : Occurrence) : Prop :=
  ∃ target, micro source target ∧ assemble target = assemble nextSource

/--
A micro-level alternating witness for a macro cycle: zero or more stitched
steps, one final causal edge, and endpoint assembly equality.
-/
def AlternatingCycle
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object) : Prop :=
  ∃ start finalSource finalTarget,
    Relation.ReflTransGen (StitchedStep micro assemble) start finalSource ∧
      micro finalSource finalTarget ∧ assemble finalTarget = assemble start

/-- Reachability obtained from one coherent micro path. -/
def LiftedMicroReachability
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object)
    (source target : Object) : Prop :=
  ∃ left right,
    assemble left = source ∧ assemble right = target ∧
      Relation.TransGen micro left right

/-- Reachability obtained by composing existential macro edges. -/
def MacroReachability
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object) : Object → Object → Prop :=
  Relation.TransGen (MacroEdge micro assemble)

/-- Every macro path has coherent micro endpoints: the stitching defect is zero. -/
def ZeroStitchingDefect
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object) : Prop :=
  ∀ ⦃source target⦄,
    MacroReachability micro assemble source target →
      LiftedMicroReachability micro assemble source target

/-- Strong representative-independence of a relation across assembly fibers. -/
def StrongQuotientCongruence
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object) : Prop :=
  ∀ ⦃left left' right right'⦄,
    assemble left = assemble left' →
      assemble right = assemble right' →
        micro left right → micro left' right'

/-- Convex fibers relative to an explicitly supplied non-strict order. -/
def FiberConvexFor
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (order : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object) : Prop :=
  ∀ ⦃left middle right⦄,
    order left middle → order middle right →
      assemble left = assemble right → assemble middle = assemble left

/-- A positive-length path with its exact number of micro edges. -/
inductive EdgePath
    {α : Type uCarrier}
    (relation : α → α → Prop) : Nat → α → α → Prop
  | single {left right} : relation left right → EdgePath relation 1 left right
  | tail {length left middle right} :
      EdgePath relation length left middle →
      relation middle right →
      EdgePath relation (length + 1) left right

namespace EdgePath

theorem toTransGen
    {α : Type uCarrier}
    {relation : α → α → Prop}
    {length : Nat}
    {left right : α} :
    EdgePath relation length left right → Relation.TransGen relation left right
  | .single edge => .single edge
  | .tail path edge => (toTransGen path).tail edge

end EdgePath

end OCProjectionCausalityIdentity
