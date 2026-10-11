import OCKIndividuationMSpaceComposition.StrongestUniversalization

namespace OCKIndividuationMSpaceComposition

universe uSource uTarget uState uObservable uMicro uMacro uNode uEdge

/-!
# Universal dynamics: a minimal relative spine

This module isolates structural facts shared by deterministic, relational and
open descriptions of dynamics.  Its completeness claims are relative: a
binary transition relation is represented exactly by its powerset-valued step,
and a typed diagram symmetry is represented exactly by commuting equivalences.
Nothing here asserts absolute semantic completeness, a largest scientific
language, or recovery of hidden observables from a non-injective projection.
-/

/-!
## Relations and powerset-valued steps
-/

/-- A powerset-valued transition step, represented by a predicate on targets. -/
abbrev PowersetStep (Source : Type uSource) (Target : Type uTarget) :=
  Source → Set Target

/-- Encode a binary relation as the set of targets available at each source. -/
def relationToPowersetStep
    {Source : Type uSource}
    {Target : Type uTarget}
    (relation : Source → Target → Prop) : PowersetStep Source Target :=
  fun source => {target | relation source target}

/-- Decode a powerset-valued step into its membership relation. -/
def powersetStepToRelation
    {Source : Type uSource}
    {Target : Type uTarget}
    (step : PowersetStep Source Target) : Source → Target → Prop :=
  fun source target => target ∈ step source

/-- Relation-to-step-to-relation is exact, not merely sound. -/
theorem powersetStepToRelation_relationToPowersetStep
    {Source : Type uSource}
    {Target : Type uTarget}
    (relation : Source → Target → Prop) :
    powersetStepToRelation (relationToPowersetStep relation) = relation := by
  rfl

/-- Step-to-relation-to-step is exact extensionally. -/
theorem relationToPowersetStep_powersetStepToRelation
    {Source : Type uSource}
    {Target : Type uTarget}
    (step : PowersetStep Source Target) :
    relationToPowersetStep (powersetStepToRelation step) = step := by
  rfl

/-!
## Deterministic dynamics as a faithful relational fragment
-/

/-- The graph relation of a deterministic transition. -/
def deterministicRelation
    {Source : Type uSource}
    {Target : Type uTarget}
    (step : Source → Target) : Source → Target → Prop :=
  fun source target => target = step source

/-- Deterministic transitions embed injectively into binary relations. -/
theorem deterministicRelation_injective
    {Source : Type uSource}
    {Target : Type uTarget} :
    Function.Injective
      (@deterministicRelation Source Target) := by
  intro first second sameRelation
  funext source
  have graphMember :
      deterministicRelation first source (first source) := rfl
  rw [sameRelation] at graphMember
  exact graphMember

/-!
## Independent observable extensions

Adding an independent observable coordinate gives a bounded signature-level
extension.  Its forgetful map can lose distinctions whenever the base is
inhabited and the observable type has two distinct values.  This does not by
itself prove behavioral conservativity; that would require an additional
lifting theorem for base transitions.  Nor does it say that every such
extension is empirically relevant.
-/

/-- Extend base dynamics with an independently specified observable dynamics. -/
def independentObservableExtension
    {State : Type uState}
    {Observable : Type uObservable}
    (stateStep : State → State → Prop)
    (observableStep : Observable → Observable → Prop) :
    (State × Observable) → (State × Observable) → Prop :=
  fun current next =>
    stateStep current.1 next.1 ∧ observableStep current.2 next.2

/-- Every extended transition projects to its base transition. -/
theorem independentObservableExtension_projects
    {State : Type uState}
    {Observable : Type uObservable}
    {stateStep : State → State → Prop}
    {observableStep : Observable → Observable → Prop}
    {current next : State × Observable}
    (extended :
      independentObservableExtension stateStep observableStep current next) :
    stateStep current.1 next.1 :=
  extended.1

/-- Distinct observable values make the forgetful state map non-injective. -/
theorem forgetIndependentObservable_not_injective
    {State : Type uState}
    {Observable : Type uObservable}
    (state : State)
    {first second : Observable}
    (different : first ≠ second) :
    ¬ Function.Injective (@Prod.fst State Observable) := by
  intro injective
  apply different
  exact congrArg Prod.snd
    (injective (show (state, first).1 = (state, second).1 from rfl))

/-- A concrete hidden Boolean coordinate already defeats injectivity. -/
theorem boolObservable_forget_not_injective
    {State : Type uState}
    (state : State) :
    ¬ Function.Injective (@Prod.fst State Bool) :=
  forgetIndependentObservable_not_injective state
    (first := false) (second := true) (by decide)

/-!
## Symmetry of a projection arrow

An arrow symmetry is relative to a specified projection `q`.  It is a pair of
micro- and macro-equivalences whose square commutes.  This is structural
equivariance, not a claim that the projection captures all semantics.
-/

/-- An automorphism of the source and target of `q` preserving the arrow. -/
structure ArrowSymmetry
    {Micro : Type uMicro}
    {Macro : Type uMacro}
    (q : Micro → Macro) where
  micro : Micro ≃ Micro
  macroEquiv : Macro ≃ Macro
  commutes : ∀ point, q (micro point) = macroEquiv (q point)

/-- For a surjective projection, the macro action is fixed by the micro action. -/
theorem arrowSymmetry_macro_unique_of_surjective
    {Micro : Type uMicro}
    {Macro : Type uMacro}
    {q : Micro → Macro}
    (surjective : Function.Surjective q)
    (first second : ArrowSymmetry q)
    (sameMicro : first.micro = second.micro) :
    first.macroEquiv = second.macroEquiv := by
  apply Equiv.ext
  intro macroPoint
  rcases surjective macroPoint with ⟨microPoint, rfl⟩
  rw [← first.commutes microPoint, ← second.commutes microPoint,
    sameMicro]

/-- A micro fixed point is transported to a macro fixed point along `q`. -/
theorem ArrowSymmetry.transport_fixed_point
    {Micro : Type uMicro}
    {Macro : Type uMacro}
    {q : Micro → Macro}
    (symmetry : ArrowSymmetry q)
    {point : Micro}
    (fixed : symmetry.micro point = point) :
    symmetry.macroEquiv (q point) = q point := by
  rw [← symmetry.commutes point, fixed]

/-!
## Compatible symmetry of a typed hierarchy or diagram
-/

/-- A typed directed diagram of local state maps. -/
structure TypedDynamicsDiagram where
  Node : Type uNode
  State : Node → Type uState
  Edge : Type uEdge
  source : Edge → Node
  target : Edge → Node
  map : ∀ edge, State (source edge) → State (target edge)

/-- A compatible family of local equivalences across every typed edge. -/
structure DiagramSymmetry (diagram : TypedDynamicsDiagram) where
  nodeEquiv : ∀ node, diagram.State node ≃ diagram.State node
  compatible : ∀ edge point,
    diagram.map edge (nodeEquiv (diagram.source edge) point) =
      nodeEquiv (diagram.target edge) (diagram.map edge point)

/-- Stabilizers propagate along every compatible diagram edge. -/
theorem DiagramSymmetry.transport_fixed_point
    {diagram : TypedDynamicsDiagram}
    (symmetry : DiagramSymmetry diagram)
    (edge : diagram.Edge)
    {point : diagram.State (diagram.source edge)}
    (fixed : symmetry.nodeEquiv (diagram.source edge) point = point) :
    symmetry.nodeEquiv (diagram.target edge) (diagram.map edge point) =
      diagram.map edge point := by
  rw [← symmetry.compatible edge point, fixed]

/-!
## Explicit descent obstruction

Swapping visible and hidden Boolean coordinates does not descend through
`Prod.fst`.  The countermodel identifies the exact boundary of arrow symmetry:
equal macro views can acquire unequal macro views after the micro transform.
-/

/-- Swap the visible and hidden Boolean coordinates. -/
def swapBoolCoordinates : Bool × Bool → Bool × Bool :=
  fun point => (point.2, point.1)

/-- Coordinate swap fails the fiber-preservation condition for `Prod.fst`. -/
theorem swapBoolCoordinates_fails_fst_fiber_preservation :
    ¬ ∀ {left right : Bool × Bool},
      left.1 = right.1 →
        (swapBoolCoordinates left).1 = (swapBoolCoordinates right).1 := by
  intro preserves
  have impossible := preserves
    (left := (false, false)) (right := (false, true)) rfl
  simp [swapBoolCoordinates] at impossible

/-- No macro function makes coordinate swap commute with `Prod.fst`. -/
theorem swapBoolCoordinates_has_no_fst_descent :
    ¬ ∃ induced : Bool → Bool,
      ∀ point : Bool × Bool,
        induced point.1 = (swapBoolCoordinates point).1 := by
  rintro ⟨induced, commutes⟩
  have first := commutes (false, false)
  have second := commutes (false, true)
  simp [swapBoolCoordinates] at first second
  rw [first] at second
  contradiction

/-- Consequently coordinate swap cannot be an arrow symmetry of `Prod.fst`. -/
theorem swapBoolCoordinates_is_not_fst_arrowSymmetry :
    ¬ ∃ macroEquiv : Bool ≃ Bool,
      ∀ point : Bool × Bool,
        (@Prod.fst Bool Bool) (swapBoolCoordinates point) =
          macroEquiv ((@Prod.fst Bool Bool) point) := by
  rintro ⟨macroEquiv, commutes⟩
  apply swapBoolCoordinates_has_no_fst_descent
  exact ⟨macroEquiv, by
    intro point
    exact (commutes point).symm⟩

/-!
## Lift existence and uniqueness are independent

The next two finite models separate two questions that a commuting square can
otherwise hide.  Unequal fibers can obstruct existence of a micro lift of a
macro symmetry.  Equal nontrivial fibers can instead support several lifts of
one macro symmetry.  Thus neither lift existence nor lift uniqueness follows
from the macro transformation alone.
-/

/-- A finite projection with a two-point `false` fiber and one-point `true` fiber. -/
def unequalBoolFiberProjection : BareThree → Bool
  | .first => false
  | .second => false
  | .third => true

/-- Boolean negation has no equivariant lift through the unequal fibers. -/
theorem boolSwap_has_no_lift_through_unequalBoolFibers :
    ¬ ∃ microEquiv : BareThree ≃ BareThree,
      ∀ point,
        unequalBoolFiberProjection (microEquiv point) =
          !(unequalBoolFiberProjection point) := by
  rintro ⟨microEquiv, commutes⟩
  have firstMapsTrue :
      unequalBoolFiberProjection (microEquiv BareThree.first) = true := by
    simpa [unequalBoolFiberProjection] using commutes BareThree.first
  have secondMapsTrue :
      unequalBoolFiberProjection (microEquiv BareThree.second) = true := by
    simpa [unequalBoolFiberProjection] using commutes BareThree.second
  have trueFiberIsThird : ∀ point,
      unequalBoolFiberProjection point = true →
        point = BareThree.third := by
    intro point inTrueFiber
    cases point <;> simp [unequalBoolFiberProjection] at inTrueFiber ⊢
  have firstImage : microEquiv BareThree.first = BareThree.third := by
    exact trueFiberIsThird _ firstMapsTrue
  have secondImage : microEquiv BareThree.second = BareThree.third := by
    exact trueFiberIsThird _ secondMapsTrue
  have equalSources : BareThree.first = BareThree.second :=
    microEquiv.injective (firstImage.trans secondImage.symm)
  cases equalSources

/-- Flip only the hidden Boolean coordinate while preserving `Prod.fst`. -/
def hiddenBoolCoordinateSwap : Bool × Bool → Bool × Bool :=
  fun point => (point.1, !point.2)

/-- Hidden-coordinate flip as a self-equivalence. -/
def hiddenBoolCoordinateSwapEquiv : (Bool × Bool) ≃ (Bool × Bool) where
  toFun := hiddenBoolCoordinateSwap
  invFun := hiddenBoolCoordinateSwap
  left_inv := by
    intro point
    cases point with
    | mk visible hidden =>
        cases visible <;> cases hidden <;> rfl
  right_inv := by
    intro point
    cases point with
    | mk visible hidden =>
        cases visible <;> cases hidden <;> rfl

/-- The completely trivial lift of macro identity through `Prod.fst`. -/
def fstIdentityArrowSymmetry : ArrowSymmetry (@Prod.fst Bool Bool) where
  micro := Equiv.refl (Bool × Bool)
  macroEquiv := Equiv.refl Bool
  commutes := by intro point; rfl

/-- A nontrivial hidden or gauge lift of the same macro identity. -/
def fstHiddenSwapArrowSymmetry : ArrowSymmetry (@Prod.fst Bool Bool) where
  micro := hiddenBoolCoordinateSwapEquiv
  macroEquiv := Equiv.refl Bool
  commutes := by intro point; rfl

/-- Identity and hidden-coordinate flip are genuinely different micro lifts. -/
theorem fstIdentity_and_hiddenSwap_have_distinct_micro_actions :
    fstIdentityArrowSymmetry.micro ≠
      fstHiddenSwapArrowSymmetry.micro := by
  intro sameEquiv
  have sameAtPoint := DFunLike.congr_fun sameEquiv (false, false)
  simp [fstIdentityArrowSymmetry, fstHiddenSwapArrowSymmetry,
    hiddenBoolCoordinateSwapEquiv, hiddenBoolCoordinateSwap] at sameAtPoint

/-- `Prod.fst` admits at least two distinct lifts of macro identity. -/
theorem fst_macroIdentity_has_multiple_micro_lifts :
    ∃ first second : ArrowSymmetry (@Prod.fst Bool Bool),
      first.macroEquiv = Equiv.refl Bool ∧
      second.macroEquiv = Equiv.refl Bool ∧
      first.micro ≠ second.micro := by
  exact ⟨fstIdentityArrowSymmetry, fstHiddenSwapArrowSymmetry,
    rfl, rfl, fstIdentity_and_hiddenSwap_have_distinct_micro_actions⟩

/-!
## Support forgets weights

The following finite countermodel is intentionally weaker than probability:
it concerns nonnegative natural weights.  It is enough to prove that support
semantics is not faithful once quantitative weights are introduced.
-/

/-- Forget quantitative transition weights while retaining positive support. -/
def weightedSupport
    {Source : Type uSource}
    {Target : Type uTarget}
    (weight : Source → Target → Nat) : Source → Target → Prop :=
  fun source target => weight source target ≠ 0

/-- First full-support Boolean weighting. -/
def firstBoolWeight : Unit → Bool → Nat :=
  fun _ _ => 1

/-- A distinct weighting with the same Boolean support. -/
def secondBoolWeight : Unit → Bool → Nat :=
  fun _ target => if target then 2 else 1

theorem boolWeights_are_distinct :
    firstBoolWeight ≠ secondBoolWeight := by
  intro equalWeights
  have pointwise := congrFun (congrFun equalWeights ()) true
  simp [firstBoolWeight, secondBoolWeight] at pointwise

theorem boolWeights_have_equal_support :
    weightedSupport firstBoolWeight = weightedSupport secondBoolWeight := by
  funext source target
  apply propext
  cases target <;> simp [weightedSupport, firstBoolWeight, secondBoolWeight]

/-- Support is non-injective on weighted dynamics. -/
theorem weightedSupport_not_injective :
    ¬ Function.Injective
      (@weightedSupport Unit Bool) := by
  intro injective
  exact boolWeights_are_distinct
    (injective boolWeights_have_equal_support)

end OCKIndividuationMSpaceComposition
