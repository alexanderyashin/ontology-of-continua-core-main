import OCKIndividuationMSpaceComposition.OperatorTransport

namespace OCKIndividuationMSpaceComposition

universe uState uObservable uEvidence uContext
universe uState' uObservable' uEvidence'

/-!
# Context-indexed symmetry and the limit of global invariance

The mechanics in this module are deliberately indexed by a declared context.
A local symmetry is an automorphism that stabilizes four typed surfaces at
once: transition, observation, evidence and admissibility.  Exact equivalences
between contexts conjugate such stabilizers.  Identity, composition and inverse
give the corresponding groupoid-shaped transport schema.

The result is a universal *form* for differently realized local mechanics, not
one context-free global symmetry group.  A two-state countermodel proves the
boundary: Boolean negation stabilizes equality dynamics under a coarse
observation, but ceases to be admissible once the observation separates the
states.  Thus extra observational resolution can only remove candidate
symmetries; it cannot create them.
-/

/-!
## Local mechanics and its stabilizer
-/

/--
The surfaces relative to which a state transformation can count as a symmetry.
`Evidence` is an explicitly typed evidence label, not an assertion that the
label is empirically adequate or complete.
-/
structure LocalMechanics
    (State : Type uState)
    (Observable : Type uObservable)
    (Evidence : Type uEvidence) where
  transition : State → State → Prop
  observation : State → Observable
  evidence : State → Evidence
  admissible : State → Prop

/--
A local symmetry is a state automorphism preserving every declared mechanics
surface.  The definition is context-relative because changing any surface can
change the stabilizer.
-/
structure LocalSymmetry
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    (mechanics : LocalMechanics State Observable Evidence) where
  stateEquiv : State ≃ State
  transition_iff : ∀ source target,
    mechanics.transition (stateEquiv source) (stateEquiv target) ↔
      mechanics.transition source target
  observation_eq : ∀ state,
    mechanics.observation (stateEquiv state) = mechanics.observation state
  evidence_eq : ∀ state,
    mechanics.evidence (stateEquiv state) = mechanics.evidence state
  admissible_iff : ∀ state,
    mechanics.admissible (stateEquiv state) ↔ mechanics.admissible state

namespace LocalSymmetry

/-- Equality of local symmetries is equality of their underlying state actions. -/
theorem ext
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    {first second : LocalSymmetry mechanics}
    (sameAction : first.stateEquiv = second.stateEquiv) :
    first = second := by
  cases first
  cases second
  cases sameAction
  rfl

/-- Identity belongs to every local stabilizer. -/
def identity
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    (mechanics : LocalMechanics State Observable Evidence) :
    LocalSymmetry mechanics where
  stateEquiv := Equiv.refl State
  transition_iff := by intro source target; rfl
  observation_eq := by intro state; rfl
  evidence_eq := by intro state; rfl
  admissible_iff := by intro state; rfl

/-- Stabilizer composition, in execution order: `first`, then `second`. -/
def comp
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (second first : LocalSymmetry mechanics) :
    LocalSymmetry mechanics where
  stateEquiv := first.stateEquiv.trans second.stateEquiv
  transition_iff := by
    intro source target
    exact (second.transition_iff
      (first.stateEquiv source) (first.stateEquiv target)).trans
        (first.transition_iff source target)
  observation_eq := by
    intro state
    calc
      mechanics.observation
          (second.stateEquiv (first.stateEquiv state)) =
          mechanics.observation (first.stateEquiv state) :=
        second.observation_eq (first.stateEquiv state)
      _ = mechanics.observation state := first.observation_eq state
  evidence_eq := by
    intro state
    calc
      mechanics.evidence
          (second.stateEquiv (first.stateEquiv state)) =
          mechanics.evidence (first.stateEquiv state) :=
        second.evidence_eq (first.stateEquiv state)
      _ = mechanics.evidence state := first.evidence_eq state
  admissible_iff := by
    intro state
    exact (second.admissible_iff (first.stateEquiv state)).trans
      (first.admissible_iff state)

/-- Every local symmetry has a local inverse. -/
def inverse
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : LocalSymmetry mechanics) :
    LocalSymmetry mechanics where
  stateEquiv := symmetry.stateEquiv.symm
  transition_iff := by
    intro source target
    simpa using
      (symmetry.transition_iff
        (symmetry.stateEquiv.symm source)
        (symmetry.stateEquiv.symm target)).symm
  observation_eq := by
    intro state
    simpa using
      (symmetry.observation_eq (symmetry.stateEquiv.symm state)).symm
  evidence_eq := by
    intro state
    simpa using
      (symmetry.evidence_eq (symmetry.stateEquiv.symm state)).symm
  admissible_iff := by
    intro state
    simpa using
      (symmetry.admissible_iff (symmetry.stateEquiv.symm state)).symm

/-- Composition acts pointwise as ordinary function composition. -/
theorem comp_apply
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (second first : LocalSymmetry mechanics)
    (state : State) :
    (comp second first).stateEquiv state =
      second.stateEquiv (first.stateEquiv state) := by
  rfl

/-- A symmetry followed by its inverse fixes every state. -/
theorem inverse_comp_apply
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : LocalSymmetry mechanics)
    (state : State) :
    (comp (inverse symmetry) symmetry).stateEquiv state = state := by
  simp [comp, inverse]

/-- Its inverse followed by the symmetry also fixes every state. -/
theorem comp_inverse_apply
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : LocalSymmetry mechanics)
    (state : State) :
    (comp symmetry (inverse symmetry)).stateEquiv state = state := by
  simp [comp, inverse]

/-- Identity acts neutrally on the left. -/
theorem identity_comp
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : LocalSymmetry mechanics) :
    comp (identity mechanics) symmetry = symmetry := by
  apply ext
  apply Equiv.ext
  intro state
  rfl

/-- Identity acts neutrally on the right. -/
theorem comp_identity
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : LocalSymmetry mechanics) :
    comp symmetry (identity mechanics) = symmetry := by
  apply ext
  apply Equiv.ext
  intro state
  rfl

/-- Local symmetry composition is associative. -/
theorem comp_assoc
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (third second first : LocalSymmetry mechanics) :
    comp third (comp second first) = comp (comp third second) first := by
  apply ext
  apply Equiv.ext
  intro state
  rfl

/-- The inverse is a left inverse in the local stabilizer. -/
theorem inverse_comp
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : LocalSymmetry mechanics) :
    comp (inverse symmetry) symmetry = identity mechanics := by
  apply ext
  apply Equiv.ext
  exact inverse_comp_apply symmetry

/-- The inverse is a right inverse in the local stabilizer. -/
theorem comp_inverse
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : LocalSymmetry mechanics) :
    comp symmetry (inverse symmetry) = identity mechanics := by
  apply ext
  apply Equiv.ext
  exact comp_inverse_apply symmetry

end LocalSymmetry

/-!
## Exact equivalence of contexts
-/

/--
An exact typed change of context.  It preserves the full local-mechanics
signature, while allowing the state, observable and evidence carriers to
change by equivalence.
-/
structure ExactContextEquivalence
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {State' : Type uState'}
    {Observable' : Type uObservable'}
    {Evidence' : Type uEvidence'}
    (source : LocalMechanics State Observable Evidence)
    (target : LocalMechanics State' Observable' Evidence') where
  stateEquiv : State ≃ State'
  observableEquiv : Observable ≃ Observable'
  evidenceEquiv : Evidence ≃ Evidence'
  transition_iff : ∀ left right,
    target.transition (stateEquiv left) (stateEquiv right) ↔
      source.transition left right
  observation_commutes : ∀ state,
    target.observation (stateEquiv state) =
      observableEquiv (source.observation state)
  evidence_commutes : ∀ state,
    target.evidence (stateEquiv state) =
      evidenceEquiv (source.evidence state)
  admissible_iff : ∀ state,
    target.admissible (stateEquiv state) ↔ source.admissible state

namespace ExactContextEquivalence

/-- Exact context equivalences are determined by their three carrier actions. -/
theorem ext
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {State' : Type uState'}
    {Observable' : Type uObservable'}
    {Evidence' : Type uEvidence'}
    {source : LocalMechanics State Observable Evidence}
    {target : LocalMechanics State' Observable' Evidence'}
    {first second : ExactContextEquivalence source target}
    (sameState : first.stateEquiv = second.stateEquiv)
    (sameObservable : first.observableEquiv = second.observableEquiv)
    (sameEvidence : first.evidenceEquiv = second.evidenceEquiv) :
    first = second := by
  cases first
  cases second
  cases sameState
  cases sameObservable
  cases sameEvidence
  rfl

/-- Identity exact context equivalence. -/
def identity
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    (mechanics : LocalMechanics State Observable Evidence) :
    ExactContextEquivalence mechanics mechanics where
  stateEquiv := Equiv.refl State
  observableEquiv := Equiv.refl Observable
  evidenceEquiv := Equiv.refl Evidence
  transition_iff := by intro left right; rfl
  observation_commutes := by intro state; rfl
  evidence_commutes := by intro state; rfl
  admissible_iff := by intro state; rfl

/-- Reverse an exact context equivalence. -/
def inverse
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {State' : Type uState'}
    {Observable' : Type uObservable'}
    {Evidence' : Type uEvidence'}
    {source : LocalMechanics State Observable Evidence}
    {target : LocalMechanics State' Observable' Evidence'}
    (transport : ExactContextEquivalence source target) :
    ExactContextEquivalence target source where
  stateEquiv := transport.stateEquiv.symm
  observableEquiv := transport.observableEquiv.symm
  evidenceEquiv := transport.evidenceEquiv.symm
  transition_iff := by
    intro left right
    simpa using
      (transport.transition_iff
        (transport.stateEquiv.symm left)
        (transport.stateEquiv.symm right)).symm
  observation_commutes := by
    intro state
    have mapped := congrArg transport.observableEquiv.symm
      (transport.observation_commutes (transport.stateEquiv.symm state))
    simpa using mapped.symm
  evidence_commutes := by
    intro state
    have mapped := congrArg transport.evidenceEquiv.symm
      (transport.evidence_commutes (transport.stateEquiv.symm state))
    simpa using mapped.symm
  admissible_iff := by
    intro state
    simpa using
      (transport.admissible_iff (transport.stateEquiv.symm state)).symm

/-- Exact context equivalences compose. -/
def comp
    {State₁ : Type uState}
    {Observable₁ : Type uObservable}
    {Evidence₁ : Type uEvidence}
    {State₂ : Type uState'}
    {Observable₂ : Type uObservable'}
    {Evidence₂ : Type uEvidence'}
    {State₃ : Type*}
    {Observable₃ : Type*}
    {Evidence₃ : Type*}
    {firstMechanics : LocalMechanics State₁ Observable₁ Evidence₁}
    {secondMechanics : LocalMechanics State₂ Observable₂ Evidence₂}
    {thirdMechanics : LocalMechanics State₃ Observable₃ Evidence₃}
    (later : ExactContextEquivalence secondMechanics thirdMechanics)
    (earlier : ExactContextEquivalence firstMechanics secondMechanics) :
    ExactContextEquivalence firstMechanics thirdMechanics where
  stateEquiv := earlier.stateEquiv.trans later.stateEquiv
  observableEquiv := earlier.observableEquiv.trans later.observableEquiv
  evidenceEquiv := earlier.evidenceEquiv.trans later.evidenceEquiv
  transition_iff := by
    intro left right
    exact (later.transition_iff
      (earlier.stateEquiv left) (earlier.stateEquiv right)).trans
        (earlier.transition_iff left right)
  observation_commutes := by
    intro state
    calc
      thirdMechanics.observation
          (later.stateEquiv (earlier.stateEquiv state)) =
          later.observableEquiv
            (secondMechanics.observation (earlier.stateEquiv state)) :=
        later.observation_commutes (earlier.stateEquiv state)
      _ = later.observableEquiv
          (earlier.observableEquiv
            (firstMechanics.observation state)) :=
        congrArg later.observableEquiv
          (earlier.observation_commutes state)
      _ = (earlier.observableEquiv.trans later.observableEquiv)
          (firstMechanics.observation state) := rfl
  evidence_commutes := by
    intro state
    calc
      thirdMechanics.evidence
          (later.stateEquiv (earlier.stateEquiv state)) =
          later.evidenceEquiv
            (secondMechanics.evidence (earlier.stateEquiv state)) :=
        later.evidence_commutes (earlier.stateEquiv state)
      _ = later.evidenceEquiv
          (earlier.evidenceEquiv (firstMechanics.evidence state)) :=
        congrArg later.evidenceEquiv (earlier.evidence_commutes state)
      _ = (earlier.evidenceEquiv.trans later.evidenceEquiv)
          (firstMechanics.evidence state) := rfl
  admissible_iff := by
    intro state
    exact (later.admissible_iff (earlier.stateEquiv state)).trans
      (earlier.admissible_iff state)

/-!
## Conjugation of stabilizers
-/

/-- Exact change of context conjugates a source symmetry into a target symmetry. -/
def conjugate
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {State' : Type uState'}
    {Observable' : Type uObservable'}
    {Evidence' : Type uEvidence'}
    {source : LocalMechanics State Observable Evidence}
    {target : LocalMechanics State' Observable' Evidence'}
    (transport : ExactContextEquivalence source target)
    (symmetry : LocalSymmetry source) :
    LocalSymmetry target where
  stateEquiv := transport.stateEquiv.symm.trans
    (symmetry.stateEquiv.trans transport.stateEquiv)
  transition_iff := by
    intro left right
    calc
      target.transition
          (transport.stateEquiv
            (symmetry.stateEquiv (transport.stateEquiv.symm left)))
          (transport.stateEquiv
            (symmetry.stateEquiv (transport.stateEquiv.symm right))) ↔
          source.transition
            (symmetry.stateEquiv (transport.stateEquiv.symm left))
            (symmetry.stateEquiv (transport.stateEquiv.symm right)) :=
        transport.transition_iff _ _
      _ ↔ source.transition
          (transport.stateEquiv.symm left)
          (transport.stateEquiv.symm right) :=
        symmetry.transition_iff _ _
      _ ↔ target.transition
          (transport.stateEquiv (transport.stateEquiv.symm left))
          (transport.stateEquiv (transport.stateEquiv.symm right)) :=
        (transport.transition_iff _ _).symm
      _ ↔ target.transition left right := by simp
  observation_eq := by
    intro state
    calc
      target.observation
          (transport.stateEquiv
            (symmetry.stateEquiv (transport.stateEquiv.symm state))) =
          transport.observableEquiv
            (source.observation
              (symmetry.stateEquiv (transport.stateEquiv.symm state))) :=
        transport.observation_commutes _
      _ = transport.observableEquiv
          (source.observation (transport.stateEquiv.symm state)) :=
        congrArg transport.observableEquiv
          (symmetry.observation_eq _)
      _ = target.observation
          (transport.stateEquiv (transport.stateEquiv.symm state)) :=
        (transport.observation_commutes _).symm
      _ = target.observation state := by simp
  evidence_eq := by
    intro state
    calc
      target.evidence
          (transport.stateEquiv
            (symmetry.stateEquiv (transport.stateEquiv.symm state))) =
          transport.evidenceEquiv
            (source.evidence
              (symmetry.stateEquiv (transport.stateEquiv.symm state))) :=
        transport.evidence_commutes _
      _ = transport.evidenceEquiv
          (source.evidence (transport.stateEquiv.symm state)) :=
        congrArg transport.evidenceEquiv (symmetry.evidence_eq _)
      _ = target.evidence
          (transport.stateEquiv (transport.stateEquiv.symm state)) :=
        (transport.evidence_commutes _).symm
      _ = target.evidence state := by simp
  admissible_iff := by
    intro state
    calc
      target.admissible
          (transport.stateEquiv
            (symmetry.stateEquiv (transport.stateEquiv.symm state))) ↔
          source.admissible
            (symmetry.stateEquiv (transport.stateEquiv.symm state)) :=
        transport.admissible_iff _
      _ ↔ source.admissible (transport.stateEquiv.symm state) :=
        symmetry.admissible_iff _
      _ ↔ target.admissible
          (transport.stateEquiv (transport.stateEquiv.symm state)) :=
        (transport.admissible_iff _).symm
      _ ↔ target.admissible state := by simp

/-- Conjugation by the identity context arrow is neutral. -/
theorem conjugate_identity
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {mechanics : LocalMechanics State Observable Evidence}
    (symmetry : LocalSymmetry mechanics) :
    conjugate (identity mechanics) symmetry = symmetry := by
  apply LocalSymmetry.ext
  apply Equiv.ext
  intro state
  rfl

/-- Conjugation is functorial along composed exact context arrows. -/
theorem conjugate_comp
    {State₁ : Type uState}
    {Observable₁ : Type uObservable}
    {Evidence₁ : Type uEvidence}
    {State₂ : Type uState'}
    {Observable₂ : Type uObservable'}
    {Evidence₂ : Type uEvidence'}
    {State₃ : Type*}
    {Observable₃ : Type*}
    {Evidence₃ : Type*}
    {firstMechanics : LocalMechanics State₁ Observable₁ Evidence₁}
    {secondMechanics : LocalMechanics State₂ Observable₂ Evidence₂}
    {thirdMechanics : LocalMechanics State₃ Observable₃ Evidence₃}
    (later : ExactContextEquivalence secondMechanics thirdMechanics)
    (earlier : ExactContextEquivalence firstMechanics secondMechanics)
    (symmetry : LocalSymmetry firstMechanics) :
    conjugate (comp later earlier) symmetry =
      conjugate later (conjugate earlier symmetry) := by
  apply LocalSymmetry.ext
  apply Equiv.ext
  intro state
  rfl

/-- Conjugating to a context and back recovers the original symmetry. -/
theorem conjugate_inverse
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {State' : Type uState'}
    {Observable' : Type uObservable'}
    {Evidence' : Type uEvidence'}
    {source : LocalMechanics State Observable Evidence}
    {target : LocalMechanics State' Observable' Evidence'}
    (transport : ExactContextEquivalence source target)
    (symmetry : LocalSymmetry source) :
    conjugate (inverse transport) (conjugate transport symmetry) =
      symmetry := by
  apply LocalSymmetry.ext
  apply Equiv.ext
  intro state
  simp [conjugate, inverse]

/-- The conjugated action is exactly `transport ∘ symmetry ∘ transport⁻¹`. -/
theorem conjugate_apply
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    {State' : Type uState'}
    {Observable' : Type uObservable'}
    {Evidence' : Type uEvidence'}
    {source : LocalMechanics State Observable Evidence}
    {target : LocalMechanics State' Observable' Evidence'}
    (transport : ExactContextEquivalence source target)
    (symmetry : LocalSymmetry source)
    (state : State') :
    (conjugate transport symmetry).stateEquiv state =
      transport.stateEquiv
        (symmetry.stateEquiv (transport.stateEquiv.symm state)) := by
  rfl

end ExactContextEquivalence

/-!
## Context-indexed mechanics: the universal stabilizer/groupoid schema
-/

/-- A family of typed local mechanics indexed by declared contexts. -/
structure ContextIndexedMechanics (Context : Type uContext) where
  State : Context → Type uState
  Observable : Context → Type uObservable
  Evidence : Context → Type uEvidence
  atContext : ∀ context,
    LocalMechanics (State context) (Observable context) (Evidence context)

/-- The stabilizer attached to one declared context. -/
abbrev ContextStabilizer
    {Context : Type uContext}
    (system : ContextIndexedMechanics Context)
    (context : Context) :=
  LocalSymmetry (system.atContext context)

/-- An exact arrow between two contexts in an indexed mechanics. -/
abbrev ExactContextArrow
    {Context : Type uContext}
    (system : ContextIndexedMechanics Context)
    (source target : Context) :=
  ExactContextEquivalence (system.atContext source) (system.atContext target)

/--
Strongest unconditional symmetry schema established here: every context has an
identity stabilizer, and every exact context arrow transports local symmetries
by conjugation.  It is indexed; it does not identify non-equivalent contexts.
-/
theorem context_indexed_stabilizer_groupoid_schema
    {Context : Type uContext}
    (system : ContextIndexedMechanics Context) :
    (∀ context, Nonempty (ContextStabilizer system context)) ∧
      (∀ {source target}, ExactContextArrow system source target →
        ContextStabilizer system source →
          Nonempty (ContextStabilizer system target)) := by
  constructor
  · intro context
    exact ⟨LocalSymmetry.identity (system.atContext context)⟩
  · intro source target transport symmetry
    exact ⟨ExactContextEquivalence.conjugate transport symmetry⟩

/-- Exact context arrows preserve stabilizer composition by conjugation. -/
theorem exact_context_transport_preserves_symmetry_composition
    {Context : Type uContext}
    {system : ContextIndexedMechanics Context}
    {source target : Context}
    (transport : ExactContextArrow system source target)
    (second first : ContextStabilizer system source) :
    ExactContextEquivalence.conjugate transport
        (LocalSymmetry.comp second first) =
      LocalSymmetry.comp
        (ExactContextEquivalence.conjugate transport second)
        (ExactContextEquivalence.conjugate transport first) := by
  apply LocalSymmetry.ext
  apply Equiv.ext
  intro state
  simp [ExactContextEquivalence.conjugate, LocalSymmetry.comp]

/-!
## Observational refinement shrinks the stabilizer
-/

/-- A fine observation refines a coarse one when the coarse view factors through it. -/
structure ObservationRefinement
    {State : Type uState}
    {Coarse : Type uObservable}
    {Fine : Type uObservable'}
    (coarse : State → Coarse)
    (fine : State → Fine) where
  forget : Fine → Coarse
  factors : ∀ state, coarse state = forget (fine state)

/-- Re-observe the same transition, evidence and admissibility surfaces. -/
def LocalMechanics.reobserve
    {State : Type uState}
    {Observable : Type uObservable}
    {Evidence : Type uEvidence}
    (mechanics : LocalMechanics State Observable Evidence)
    {Observable' : Type uObservable'}
    (observation : State → Observable') :
    LocalMechanics State Observable' Evidence where
  transition := mechanics.transition
  observation := observation
  evidence := mechanics.evidence
  admissible := mechanics.admissible

/--
Any automorphism preserving the fine observation also preserves every coarse
observation factored through it.
-/
theorem observation_refinement_preserves_coarse
    {State : Type uState}
    {Coarse : Type uObservable}
    {Fine : Type uObservable'}
    {coarse : State → Coarse}
    {fine : State → Fine}
    (refinement : ObservationRefinement coarse fine)
    (stateEquiv : State ≃ State)
    (preservesFine : ∀ state, fine (stateEquiv state) = fine state) :
    ∀ state, coarse (stateEquiv state) = coarse state := by
  intro state
  calc
    coarse (stateEquiv state) =
        refinement.forget (fine (stateEquiv state)) :=
      refinement.factors (stateEquiv state)
    _ = refinement.forget (fine state) :=
      congrArg refinement.forget (preservesFine state)
    _ = coarse state := (refinement.factors state).symm

/--
Fine observational preservation implies coarse observational preservation,
but not conversely: Boolean negation preserves the unique `Unit` observation
while failing to preserve the identity observation.
-/
theorem coarse_observation_preservation_does_not_imply_fine_preservation :
    (∀ state : Bool,
      (fun _ : Bool => ()) (!state) =
        (fun _ : Bool => ()) state) ∧
      ¬ (∀ state : Bool,
        (id : Bool → Bool) (!state) =
          (id : Bool → Bool) state) := by
  constructor
  · intro state
    rfl
  · intro preserves
    have impossible := preserves false
    change (!false : Bool) = false at impossible
    simp at impossible

/--
With all non-observational mechanics held fixed, a fine-context stabilizer
embeds into the coarse-context stabilizer.  This is the precise monotonic
"more constraints, no more symmetries" theorem.
-/
def observation_refinement_can_only_shrink_symmetry
    {State : Type uState}
    {Coarse : Type uObservable}
    {Fine : Type uObservable'}
    {Evidence : Type uEvidence}
    (coarseMechanics : LocalMechanics State Coarse Evidence)
    (fineObservation : State → Fine)
    (refinement : ObservationRefinement
      coarseMechanics.observation fineObservation)
    (fineSymmetry : LocalSymmetry
      (coarseMechanics.reobserve fineObservation)) :
    LocalSymmetry coarseMechanics where
  stateEquiv := fineSymmetry.stateEquiv
  transition_iff := fineSymmetry.transition_iff
  observation_eq :=
    observation_refinement_preserves_coarse refinement
      fineSymmetry.stateEquiv fineSymmetry.observation_eq
  evidence_eq := fineSymmetry.evidence_eq
  admissible_iff := fineSymmetry.admissible_iff

/-!
## Boolean boundary model
-/

/-- Boolean negation as a state automorphism. -/
def boolNegationEquiv : Bool ≃ Bool where
  toFun := fun state => !state
  invFun := fun state => !state
  left_inv := by intro state; cases state <;> rfl
  right_inv := by intro state; cases state <;> rfl

/-- Equality dynamics with a completely coarse observation. -/
def boolCoarseMechanics : LocalMechanics Bool Unit Unit where
  transition := fun source target => source = target
  observation := fun _ => ()
  evidence := fun _ => ()
  admissible := fun _ => True

/-- The same dynamics with the state-separating identity observation. -/
def boolSeparatingMechanics : LocalMechanics Bool Bool Unit :=
  boolCoarseMechanics.reobserve id

/-- Boolean negation is a symmetry in the coarse context. -/
def boolNegationCoarseSymmetry : LocalSymmetry boolCoarseMechanics where
  stateEquiv := boolNegationEquiv
  transition_iff := by
    intro source target
    cases source <;> cases target <;>
      simp [boolCoarseMechanics, boolNegationEquiv]
  observation_eq := by intro state; rfl
  evidence_eq := by intro state; rfl
  admissible_iff := by intro state; rfl

/-- The separating observation removes Boolean negation from the stabilizer. -/
theorem boolNegation_not_separating_symmetry :
    ¬ ∃ symmetry : LocalSymmetry boolSeparatingMechanics,
      symmetry.stateEquiv = boolNegationEquiv := by
  rintro ⟨symmetry, underlying⟩
  have preservesFalse := symmetry.observation_eq false
  rw [underlying] at preservesFalse
  change (!false : Bool) = false at preservesFalse
  simp at preservesFalse

/-- The two observation regimes as an explicit context index. -/
inductive BoolObservationContext where
  | coarse
  | separating
deriving DecidableEq

/-- Context-dependent observable carrier for the Boolean boundary model. -/
def BoolContextObservable : BoolObservationContext → Type
  | .coarse => Unit
  | .separating => Bool

/-- The indexed Boolean mechanics has one state carrier but two stabilizers. -/
def boolContextIndexedMechanics :
    ContextIndexedMechanics BoolObservationContext where
  State := fun _ => Bool
  Observable := BoolContextObservable
  Evidence := fun _ => Unit
  atContext := fun context =>
    match context with
    | .coarse => boolCoarseMechanics
    | .separating => boolSeparatingMechanics

/-- A single state action is globally admissible only if every context realizes it locally. -/
def UniformStateSymmetry
    {Context : Type uContext}
    {State : Type uState}
    {Observable : Context → Type uObservable}
    {Evidence : Context → Type uEvidence}
    (mechanics : ∀ context,
      LocalMechanics State (Observable context) (Evidence context))
    (action : State ≃ State) : Prop :=
  ∀ context, ∃ symmetry : LocalSymmetry (mechanics context),
    symmetry.stateEquiv = action

/--
There is no context-free promotion of every coarse symmetry: the same Boolean
negation action is locally valid in the coarse context but not uniformly valid
across the coarse and separating contexts.
-/
theorem coarse_symmetry_need_not_extend_to_global_symmetry :
    ¬ UniformStateSymmetry
      (fun context => boolContextIndexedMechanics.atContext context)
      boolNegationEquiv := by
  intro uniform
  rcases uniform BoolObservationContext.separating with
    ⟨symmetry, underlying⟩
  exact boolNegation_not_separating_symmetry ⟨symmetry, underlying⟩

end OCKIndividuationMSpaceComposition
