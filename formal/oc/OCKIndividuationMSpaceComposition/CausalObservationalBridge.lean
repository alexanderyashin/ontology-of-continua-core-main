import OCKIndividuationMSpaceComposition.ConstraintGeneratedObject

namespace OCKIndividuationMSpaceComposition

universe uCausal uPresentation uObservation uProvenance

/-!
# Derived causal--observational correspondence

This module replaces an assumed exact-image field by local, independently
checkable graph laws.  A presentation graph represents a root-relative causal
graph when it preserves the root, maps every presentation edge to a causal
edge, and locally lifts every causal edge leaving a represented node.

Those three laws imply an exact correspondence between the two reachable
carriers.  Quotienting reachable presentations by equality of their realized
causal node then gives a bijection with the causal carrier.

The quotient below is a *presentation equivalence*.  It is deliberately not a
token-identity or provenance relation.  A final countermodel makes that
separation explicit.
-/

/-- Finite root-relative reachability in an arbitrary directed graph. -/
inductive ReachableFrom
    {Node : Type uCausal}
    (edge : Node → Node → Prop)
    (root : Node) : Node → Prop
  | root : ReachableFrom edge root root
  | step {current next} :
      ReachableFrom edge root current →
      edge current next →
      ReachableFrom edge root next

/-- Root preservation and forward edge soundness, without path lifting. -/
structure SoundRootedPresentation
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    (causalEdge : Causal → Causal → Prop)
    (presentationEdge : Presentation → Presentation → Prop)
    (causalRoot : Causal)
    (presentationRoot : Presentation) where
  realize : Presentation → Causal
  root_preserved : realize presentationRoot = causalRoot
  edge_sound : ∀ ⦃current next⦄,
    presentationEdge current next →
      causalEdge (realize current) (realize next)

/-- Every causal successor of a represented node has a one-edge presentation lift. -/
def LocalPathLifting
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (sound : SoundRootedPresentation causalEdge presentationEdge
      causalRoot presentationRoot) : Prop :=
  ∀ ⦃current nextCausal⦄,
    causalEdge (sound.realize current) nextCausal →
      ∃ nextPresentation,
        presentationEdge current nextPresentation ∧
          sound.realize nextPresentation = nextCausal

/-- The local laws used to derive the global reachable-carrier bridge. -/
structure CausalObservationalBridge
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    (causalEdge : Causal → Causal → Prop)
    (presentationEdge : Presentation → Presentation → Prop)
    (causalRoot : Causal)
    (presentationRoot : Presentation)
    extends SoundRootedPresentation causalEdge presentationEdge
      causalRoot presentationRoot where
  local_path_lifting : LocalPathLifting toSoundRootedPresentation

/-- Edge soundness extends from one edge to every finite presentation path. -/
theorem CausalObservationalBridge.presentationReachable_implies_causalReachable
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot)
    {presentation : Presentation}
    (reachable : ReachableFrom presentationEdge presentationRoot presentation) :
    ReachableFrom causalEdge causalRoot (bridge.realize presentation) := by
  induction reachable with
  | root =>
      rw [bridge.root_preserved]
      exact .root
  | step previous edge inductionHypothesis =>
      exact .step inductionHypothesis (bridge.edge_sound edge)

/-- Local path lifting extends from one edge to every finite causal path. -/
theorem CausalObservationalBridge.causalReachable_has_presentation
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot)
    {causal : Causal}
    (reachable : ReachableFrom causalEdge causalRoot causal) :
    ∃ presentation,
      ReachableFrom presentationEdge presentationRoot presentation ∧
        bridge.realize presentation = causal := by
  induction reachable with
  | root =>
      exact ⟨presentationRoot, .root, bridge.root_preserved⟩
  | @step current next previous edge inductionHypothesis =>
      rcases inductionHypothesis with ⟨presentation, presentationReachable,
        realizesCurrent⟩
      have liftedEdge : causalEdge (bridge.realize presentation) next := by
        simpa [realizesCurrent] using edge
      rcases bridge.local_path_lifting liftedEdge with
        ⟨nextPresentation, presentationEdgeProof, realizesNext⟩
      exact ⟨nextPresentation, .step presentationReachable presentationEdgeProof,
        realizesNext⟩

/--
The exact reachable-image theorem is derived from the three local laws; it is
not a field of `CausalObservationalBridge`.
-/
theorem CausalObservationalBridge.exact_reachable_image
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot)
    (causal : Causal) :
    ReachableFrom causalEdge causalRoot causal ↔
      ∃ presentation,
        ReachableFrom presentationEdge presentationRoot presentation ∧
          bridge.realize presentation = causal := by
  constructor
  · exact bridge.causalReachable_has_presentation
  · rintro ⟨presentation, presentationReachable, realizes⟩
    rw [← realizes]
    exact bridge.presentationReachable_implies_causalReachable
      presentationReachable

/-- Root-relative causal carrier generated by the causal edge relation. -/
abbrev ReachableCausalCarrier
    {Causal : Type uCausal}
    (causalEdge : Causal → Causal → Prop)
    (causalRoot : Causal) :=
  {causal : Causal // ReachableFrom causalEdge causalRoot causal}

/-- Root-relative carrier of presentation occurrences. -/
abbrev ReachablePresentationCarrier
    {Presentation : Type uPresentation}
    (presentationEdge : Presentation → Presentation → Prop)
    (presentationRoot : Presentation) :=
  {presentation : Presentation //
    ReachableFrom presentationEdge presentationRoot presentation}

/-- The realization map restricted to the two reachable carriers. -/
def CausalObservationalBridge.toCausalCarrier
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot) :
    ReachablePresentationCarrier presentationEdge presentationRoot →
      ReachableCausalCarrier causalEdge causalRoot :=
  fun presentation =>
    ⟨bridge.realize presentation.1,
      bridge.presentationReachable_implies_causalReachable presentation.2⟩

/-- Exact reachable image is surjectivity of the restricted realization map. -/
theorem CausalObservationalBridge.toCausalCarrier_surjective
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot) :
    Function.Surjective bridge.toCausalCarrier := by
  rintro ⟨causal, causalReachable⟩
  rcases bridge.causalReachable_has_presentation causalReachable with
    ⟨presentation, presentationReachable, realizes⟩
  refine ⟨⟨presentation, presentationReachable⟩, ?_⟩
  apply Subtype.ext
  exact realizes

/--
Presentation-kernel equivalence identifies exactly those reachable
presentations that realize the same causal node.
-/
def realizationKernelSetoid
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot) :
    Setoid (ReachablePresentationCarrier presentationEdge presentationRoot) where
  r := fun left right =>
    bridge.realize left.1 = bridge.realize right.1
  iseqv := ⟨
    by intro presentation; rfl,
    by intro left right related; exact related.symm,
    by
      intro first second third firstSecond secondThird
      exact firstSecond.trans secondThird⟩

/-- Reachable presentations modulo realization-kernel equivalence. -/
abbrev ReachablePresentationQuotient
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot) :=
  Quotient (realizationKernelSetoid bridge)

/-- Realization descends to the presentation-kernel quotient. -/
def CausalObservationalBridge.quotientToCausalCarrier
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot) :
    ReachablePresentationQuotient bridge →
      ReachableCausalCarrier causalEdge causalRoot :=
  Quotient.lift bridge.toCausalCarrier (by
    intro left right related
    apply Subtype.ext
    exact related)

theorem CausalObservationalBridge.quotientToCausalCarrier_mk
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot)
    (presentation :
      ReachablePresentationCarrier presentationEdge presentationRoot) :
    bridge.quotientToCausalCarrier
        (Quotient.mk (realizationKernelSetoid bridge) presentation) =
      bridge.toCausalCarrier presentation :=
  rfl

/-- Quotienting removes exactly, and only, realization-map non-injectivity. -/
theorem CausalObservationalBridge.quotientToCausalCarrier_injective
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot) :
    Function.Injective bridge.quotientToCausalCarrier := by
  intro left right
  induction left using Quotient.inductionOn with
  | _ leftRepresentative =>
      induction right using Quotient.inductionOn with
      | _ rightRepresentative =>
          intro equalImages
          apply Quotient.sound
          exact congrArg Subtype.val equalImages

/-- The derived quotient-to-carrier map is a bijection. -/
theorem CausalObservationalBridge.quotientToCausalCarrier_bijective
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot) :
    Function.Bijective bridge.quotientToCausalCarrier := by
  constructor
  · exact bridge.quotientToCausalCarrier_injective
  · rintro ⟨causal, causalReachable⟩
    rcases bridge.causalReachable_has_presentation causalReachable with
      ⟨presentation, presentationReachable, realizes⟩
    refine ⟨Quotient.mk (realizationKernelSetoid bridge)
      ⟨presentation, presentationReachable⟩, ?_⟩
    apply Subtype.ext
    exact realizes

/-!
## Relation to the independently generated causal kernel
-/

/-- `GeneratedKernel` is exactly generic reachability under internal dependency. -/
theorem reachableFrom_internalDependency_iff_generatedKernel
    {Mechanism : Type uCausal}
    {Intervention Outcome : Type*}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {root mechanism : Mechanism} :
    ReachableFrom (InternalDependency model) root mechanism ↔
      GeneratedKernel model root mechanism := by
  constructor
  · intro reachable
    induction reachable with
    | root => exact .ofRoot
    | step previous edge inductionHypothesis =>
        exact .ofInternalDependency inductionHypothesis edge
  · intro generated
    induction generated with
    | ofRoot => exact .root
    | ofInternalDependency previous edge inductionHypothesis =>
        exact .step inductionHypothesis edge

/--
For the OC intensional dependency graph, the local bridge laws derive the
exact image of the independently generated kernel.
-/
theorem CausalObservationalBridge.exact_generatedKernel_image
    {Mechanism : Type uCausal}
    {Intervention Outcome : Type*}
    {Presentation : Type uPresentation}
    {model : ActiveConstraintModel Mechanism Intervention Outcome}
    {presentationEdge : Presentation → Presentation → Prop}
    {root : Mechanism}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge (InternalDependency model)
      presentationEdge root presentationRoot)
    (mechanism : Mechanism) :
    GeneratedKernel model root mechanism ↔
      ∃ presentation,
        ReachableFrom presentationEdge presentationRoot presentation ∧
          bridge.realize presentation = mechanism := by
  rw [← reachableFrom_internalDependency_iff_generatedKernel]
  exact bridge.exact_reachable_image mechanism

/-!
## Observation descent and its exact limitation

An observation quotient can carry a well-defined causal realization only if
observation equality separates realized causal nodes on the reachable carrier.
This is an extra empirical/measurement assumption, not a consequence of path
lifting.
-/

def reachableObservationalSetoid
    {Presentation : Type uPresentation}
    {Observation : Type uObservation}
    {presentationEdge : Presentation → Presentation → Prop}
    {presentationRoot : Presentation}
    (observe : Presentation → Observation) :
    Setoid (ReachablePresentationCarrier presentationEdge presentationRoot) where
  r := fun left right => observe left.1 = observe right.1
  iseqv := ⟨
    by intro presentation; rfl,
    by intro left right related; exact related.symm,
    by
      intro first second third firstSecond secondThird
      exact firstSecond.trans secondThird⟩

abbrev ReachableObservationQuotient
    {Presentation : Type uPresentation}
    {Observation : Type uObservation}
    {presentationEdge : Presentation → Presentation → Prop}
    {presentationRoot : Presentation}
    (observe : Presentation → Observation) :=
  Quotient (reachableObservationalSetoid
    (presentationEdge := presentationEdge)
    (presentationRoot := presentationRoot) observe)

def ObservationSeparatesRealization
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {Observation : Type uObservation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot)
    (observe : Presentation → Observation) : Prop :=
  ∀ left right :
      ReachablePresentationCarrier presentationEdge presentationRoot,
    observe left.1 = observe right.1 →
      bridge.realize left.1 = bridge.realize right.1

/-- A claimed descent of observational classes to causal carrier nodes. -/
structure ObservationCausalDescent
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {Observation : Type uObservation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot)
    (observe : Presentation → Observation) where
  descend : ReachableObservationQuotient
      (presentationEdge := presentationEdge)
      (presentationRoot := presentationRoot) observe →
    ReachableCausalCarrier causalEdge causalRoot
  commutes : ∀ presentation :
      ReachablePresentationCarrier presentationEdge presentationRoot,
    descend (Quotient.mk
      (reachableObservationalSetoid
        (presentationEdge := presentationEdge)
        (presentationRoot := presentationRoot) observe)
      presentation) = bridge.toCausalCarrier presentation

/-- Observation separation is sufficient to construct causal descent. -/
def observationCausalDescent_of_separation
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {Observation : Type uObservation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    (bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot)
    (observe : Presentation → Observation)
    (separates : ObservationSeparatesRealization bridge observe) :
    ObservationCausalDescent bridge observe where
  descend := Quotient.lift bridge.toCausalCarrier (by
    intro left right observationallyEqual
    apply Subtype.ext
    exact separates left right observationallyEqual)
  commutes := by intro presentation; rfl

/-- Observation separation is also necessary for any commuting causal descent. -/
theorem observationCausalDescent_implies_separation
    {Causal : Type uCausal}
    {Presentation : Type uPresentation}
    {Observation : Type uObservation}
    {causalEdge : Causal → Causal → Prop}
    {presentationEdge : Presentation → Presentation → Prop}
    {causalRoot : Causal}
    {presentationRoot : Presentation}
    {bridge : CausalObservationalBridge causalEdge presentationEdge
      causalRoot presentationRoot}
    {observe : Presentation → Observation}
    (descent : ObservationCausalDescent bridge observe) :
    ObservationSeparatesRealization bridge observe := by
  intro left right observationallyEqual
  have quotientEqual :
      Quotient.mk
          (reachableObservationalSetoid
            (presentationEdge := presentationEdge)
            (presentationRoot := presentationRoot) observe) left =
        Quotient.mk
          (reachableObservationalSetoid
            (presentationEdge := presentationEdge)
            (presentationRoot := presentationRoot) observe) right :=
    Quotient.sound observationallyEqual
  have descendedEqual := congrArg descent.descend quotientEqual
  rw [descent.commutes left, descent.commutes right] at descendedEqual
  exact congrArg Subtype.val descendedEqual

/-!
## Sharp countermodels
-/

def pathLiftingCounterexampleCausalEdge : Bool → Bool → Prop :=
  fun current next => current = false ∧ next = true

def pathLiftingCounterexamplePresentationEdge : Unit → Unit → Prop :=
  fun _ _ => False

def pathLiftingCounterexampleSound :
    SoundRootedPresentation pathLiftingCounterexampleCausalEdge
      pathLiftingCounterexamplePresentationEdge false () where
  realize := fun _ => false
  root_preserved := rfl
  edge_sound := by intro current next impossible; exact False.elim impossible

theorem pathLiftingCounterexample_has_unrepresented_reachable_node :
    ReachableFrom pathLiftingCounterexampleCausalEdge false true ∧
      ¬ ∃ presentation,
        ReachableFrom pathLiftingCounterexamplePresentationEdge () presentation ∧
          pathLiftingCounterexampleSound.realize presentation = true := by
  constructor
  · exact .step .root ⟨rfl, rfl⟩
  · rintro ⟨presentation, _, realizesTrue⟩
    cases presentation
    simp [pathLiftingCounterexampleSound] at realizesTrue

theorem pathLiftingCounterexample_has_no_local_path_lifting :
    ¬ LocalPathLifting pathLiftingCounterexampleSound := by
  intro lifting
  rcases lifting (current := ()) (nextCausal := true) ⟨rfl, rfl⟩ with
    ⟨nextPresentation, presentationEdge, _⟩
  exact presentationEdge

theorem pathLiftingCounterexample_refutes_exact_reachable_image :
    ¬ ∀ causal,
      ReachableFrom pathLiftingCounterexampleCausalEdge false causal ↔
        ∃ presentation,
          ReachableFrom pathLiftingCounterexamplePresentationEdge () presentation ∧
            pathLiftingCounterexampleSound.realize presentation = causal := by
  intro exactImage
  exact pathLiftingCounterexample_has_unrepresented_reachable_node.2
    ((exactImage true).mp
      pathLiftingCounterexample_has_unrepresented_reachable_node.1)

def separationCounterexampleEdge : Bool → Bool → Prop :=
  fun current next => current = false ∧ next = true

def separationCounterexampleBridge :
    CausalObservationalBridge separationCounterexampleEdge
      separationCounterexampleEdge false false where
  realize := id
  root_preserved := rfl
  edge_sound := by intro current next edge; exact edge
  local_path_lifting := by
    intro current next edge
    exact ⟨next, edge, rfl⟩

def separationCounterexampleObserve : Bool → Unit := fun _ => ()

theorem separationCounterexample_observation_does_not_separate :
    ¬ ObservationSeparatesRealization separationCounterexampleBridge
      separationCounterexampleObserve := by
  intro separates
  let left : ReachablePresentationCarrier separationCounterexampleEdge false :=
    ⟨false, .root⟩
  let right : ReachablePresentationCarrier separationCounterexampleEdge false :=
    ⟨true, .step .root ⟨rfl, rfl⟩⟩
  have realizedEqual := separates left right rfl
  exact Bool.false_ne_true realizedEqual

theorem separationCounterexample_has_no_observation_causal_descent :
    ¬ Nonempty (ObservationCausalDescent separationCounterexampleBridge
      separationCounterexampleObserve) := by
  rintro ⟨descent⟩
  exact separationCounterexample_observation_does_not_separate
    (observationCausalDescent_implies_separation descent)

/-!
## Presentation equivalence is not token or provenance identity
-/

structure ProvenancedPresentation
    (Presentation : Type uPresentation)
    (Provenance : Type uProvenance) where
  presentation : Presentation
  provenance : Provenance

def PresentationRealizationEquivalent
    {Presentation : Type uPresentation}
    {Provenance : Type uProvenance}
    {Causal : Type uCausal}
    (realize : Presentation → Causal) :
    ProvenancedPresentation Presentation Provenance →
      ProvenancedPresentation Presentation Provenance → Prop :=
  fun left right => realize left.presentation = realize right.presentation

/-- Equal realization is compatible with distinct provenance tokens. -/
theorem presentation_equivalence_does_not_imply_provenance_identity :
    ∃ left right : ProvenancedPresentation Unit Bool,
      PresentationRealizationEquivalent (fun _ : Unit => ()) left right ∧
        left.provenance ≠ right.provenance := by
  exact ⟨⟨(), false⟩, ⟨(), true⟩, rfl, Bool.false_ne_true⟩

end OCKIndividuationMSpaceComposition
