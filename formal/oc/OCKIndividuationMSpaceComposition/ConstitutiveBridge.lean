import OCMinimalObligationSpine.MSpace
import OCMaturityCompletionCycle.CrossContextCoupling

namespace OCKIndividuationMSpaceComposition

open OCMinimalObligationSpine

universe
  uIndex uChild uParent uToken uView
  uLiftCarrier uLiftCandidate

/-- A typed joint configuration of an indexed family of child states. -/
abbrev JointConfiguration
    (Index : Type uIndex)
    (ChildState : Index → Type uChild) :=
  (index : Index) → ChildState index

/--
The minimal non-circular bridge schema. `realizes configuration parent` is the
bottom-up constitutive witness. Its fiber at `parent` is the top-down set of
child configurations allowed by that parent realization.

The structure deliberately contains no individuation axiom, source token,
physical boundary, or claim that every admissible configuration realizes a
parent.
-/
structure ConstitutiveBridge
    (Index : Type uIndex)
    (ChildState : Index → Type uChild)
    (ParentState : Type uParent) where
  admissible : JointConfiguration Index ChildState → Prop
  realizes : JointConfiguration Index ChildState → ParentState → Prop
  realizes_admissible : ∀ {configuration parent},
    realizes configuration parent → admissible configuration

/-- The parent-indexed child-configuration fiber. -/
def ParentConfigurationFiber
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    (bridge : ConstitutiveBridge Index ChildState ParentState)
    (parent : ParentState) :=
  {configuration : JointConfiguration Index ChildState //
    bridge.realizes configuration parent}

/-- Availability is constructive non-emptiness of one parent fiber. -/
def ParentConfigurationAvailable
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    (bridge : ConstitutiveBridge Index ChildState ParentState)
    (parent : ParentState) : Prop :=
  Nonempty (ParentConfigurationFiber bridge parent)

theorem parentFiber_member_is_admissible
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    {parent : ParentState}
    (member : ParentConfigurationFiber bridge parent) :
    bridge.admissible member.1 :=
  bridge.realizes_admissible member.2

/--
The empty realization model accepts exactly the supplied admissible
configurations but realizes no parent.  It is one half of the semantic
independence countermodel below.
-/
def emptyRealizationBridge
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    (admissible : JointConfiguration Index ChildState → Prop) :
    ConstitutiveBridge Index ChildState ParentState where
  admissible := admissible
  realizes := fun _ _ => False
  realizes_admissible := by simp

/--
The positive realization model has the same admissibility predicate as the
empty model, but its unit parent is realized by every admissible
configuration.
-/
def admissibleRealizationBridge
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    (admissible : JointConfiguration Index ChildState → Prop) :
    ConstitutiveBridge Index ChildState Unit where
  admissible := admissible
  realizes := fun configuration _ => admissible configuration
  realizes_admissible := by
    intro configuration parent realized
    exact realized

theorem emptyRealizationBridge_has_no_available_parent
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    (admissible : JointConfiguration Index ChildState → Prop)
    (parent : ParentState) :
    ¬ ParentConfigurationAvailable
      (emptyRealizationBridge admissible) parent := by
  intro available
  obtain ⟨member⟩ := available
  exact member.2

theorem admissibleRealizationBridge_has_available_parent
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    (admissible : JointConfiguration Index ChildState → Prop)
    (witness : ∃ configuration, admissible configuration) :
    ParentConfigurationAvailable
      (admissibleRealizationBridge admissible) () := by
  obtain ⟨configuration, accepted⟩ := witness
  exact ⟨⟨configuration, accepted⟩⟩

/--
Decisive countermodel to admissibility-only parent individuation: two bridges
have definitionally the same admissibility predicate, while one has no parent
realization and the other has one.  Therefore admissibility alone does not
determine parent existence in the minimal theory.
-/
theorem admissibility_is_insufficient_for_parent_existence
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    (admissible : JointConfiguration Index ChildState → Prop)
    (witness : ∃ configuration, admissible configuration) :
    ∃ absent present : ConstitutiveBridge Index ChildState Unit,
      absent.admissible = present.admissible ∧
      ¬ ParentConfigurationAvailable absent () ∧
      ParentConfigurationAvailable present () := by
  refine ⟨emptyRealizationBridge admissible,
    admissibleRealizationBridge admissible, rfl, ?_, ?_⟩
  · exact emptyRealizationBridge_has_no_available_parent admissible ()
  · exact admissibleRealizationBridge_has_available_parent admissible witness

/--
Two distinct parent tokens can have exactly the same realization fiber.  This
is the token-identity half of the semantic independence result.
-/
def duplicatedTokenBridge
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    (admissible : JointConfiguration Index ChildState → Prop) :
    ConstitutiveBridge Index ChildState Bool where
  admissible := admissible
  realizes := fun configuration _ => admissible configuration
  realizes_admissible := by
    intro configuration parent realized
    exact realized

theorem duplicatedTokenBridge_has_equal_parent_fibers
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    (admissible : JointConfiguration Index ChildState → Prop) :
    ParentConfigurationFiber (duplicatedTokenBridge admissible) false =
      ParentConfigurationFiber (duplicatedTokenBridge admissible) true := by
  rfl

theorem parent_fiber_is_insufficient_for_token_identity
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    (admissible : JointConfiguration Index ChildState → Prop)
    (witness : ∃ configuration, admissible configuration) :
    ∃ configuration,
      (duplicatedTokenBridge admissible).realizes configuration false ∧
      (duplicatedTokenBridge admissible).realizes configuration true ∧
      false ≠ true := by
  obtain ⟨configuration, accepted⟩ := witness
  exact ⟨configuration, accepted, accepted, Bool.false_ne_true⟩

/-- A constitutive transition preserves the realization witness, not merely admissibility. -/
structure ConstitutiveTransition
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    (bridge : ConstitutiveBridge Index ChildState ParentState) where
  childStep : (index : Index) → ChildState index → ChildState index
  parentStep : ParentState → ParentState
  preserves : ∀ {configuration parent},
    bridge.realizes configuration parent →
      bridge.realizes
        (fun index => childStep index (configuration index))
        (parentStep parent)

theorem constitutiveTransition_preserves_parentAvailability
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    (transition : ConstitutiveTransition bridge)
    {parent : ParentState}
    (available : ParentConfigurationAvailable bridge parent) :
    ParentConfigurationAvailable bridge (transition.parentStep parent) := by
  obtain ⟨member⟩ := available
  exact ⟨
    ⟨fun index => transition.childStep index (member.1 index),
      transition.preserves member.2⟩⟩

/-- Normative or operational validity is independent input, not realization. -/
abbrev NormativeValidity (ParentState : Type uParent) := ParentState → Prop

/-- A deliberately arbitrary strict filter: useful as a sufficiency countermodel. -/
def arbitraryBoolFilterBridge :
    ConstitutiveBridge Unit (fun _ => Bool) Unit where
  admissible configuration := configuration () = true
  realizes configuration _ := configuration () = true
  realizes_admissible := by
    intro configuration parent realized
    exact realized

def StrictlyConstrained
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    (bridge : ConstitutiveBridge Index ChildState ParentState) : Prop :=
  ∃ configuration, ¬ bridge.admissible configuration

theorem arbitraryBoolFilterBridge_is_strictlyConstrained :
    StrictlyConstrained arbitraryBoolFilterBridge := by
  refine ⟨(fun _ => false), ?_⟩
  simp [arbitraryBoolFilterBridge]

/-- A constitutively realized unit parent whose normative predicate is false. -/
def unitBridge : ConstitutiveBridge Unit (fun _ => Unit) Unit where
  admissible _ := True
  realizes _ _ := True
  realizes_admissible := by simp

def unitTransition : ConstitutiveTransition unitBridge where
  childStep := fun _ _ => ()
  parentStep := fun _ => ()
  preserves := by simp [unitBridge]

def impossibleNormativeValidity : NormativeValidity Unit := fun _ => False

theorem constitutive_continuation_does_not_imply_normative_validity :
    ∃ configuration parent,
      unitBridge.realizes configuration parent ∧
      unitBridge.realizes
        (fun index => unitTransition.childStep index (configuration index))
        (unitTransition.parentStep parent) ∧
      ¬ impossibleNormativeValidity (unitTransition.parentStep parent) := by
  refine ⟨(fun _ => ()), (), ?_⟩
  simp [unitBridge, unitTransition, impossibleNormativeValidity]

/-- A view occurrence carries its source token explicitly; view equality is separate. -/
structure ProjectedOccurrence
    (Token : Type uToken)
    (View : Type uView) where
  token : Token
  view : View

def SameSourceToken
    {Token : Type uToken}
    {View : Type uView}
    (left right : ProjectedOccurrence Token View) : Prop :=
  left.token = right.token

theorem isomorphic_view_types_do_not_imply_same_source_token :
    ∃ left right : ProjectedOccurrence Bool Bool,
      Nonempty (Bool ≃ Bool) ∧ ¬ SameSourceToken left right := by
  refine ⟨⟨false, false⟩, ⟨true, false⟩, ⟨Equiv.refl Bool⟩, ?_⟩
  simp [SameSourceToken]

def concreteTokenOf : Bool → Unit := fun _ => ()

theorem one_source_token_allows_nonisomorphic_projection_types :
    concreteTokenOf false = concreteTokenOf true ∧
      ¬ Nonempty (Bool ≃ Unit) := by
  constructor
  · rfl
  · intro equivalent
    obtain ⟨equivalence⟩ := equivalent
    exact Bool.false_ne_true
      (equivalence.injective (Subsingleton.elim _ _))

/--
An explicit adapter is required to interpret a representational M-fiber member
as a parent-configuration witness. Current `MSpaceFiber` does not manufacture
this bridge.
-/
structure MSpaceToParentFiberAdapter
    {K : CurrentK}
    (search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K)
    (distinction : TrajectoryDistinction K)
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    (constitutive : ConstitutiveBridge Index ChildState ParentState)
    (parent : ParentState) where
  mapMember : MSpaceFiber search distinction →
    ParentConfigurationFiber constitutive parent

theorem parentAvailable_of_mSpace_available_and_explicitAdapter
    {K : CurrentK}
    {search : LiftSearchClass.{uLiftCarrier, uLiftCandidate} K}
    {distinction : TrajectoryDistinction K}
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    {constitutive : ConstitutiveBridge Index ChildState ParentState}
    {parent : ParentState}
    (adapter : MSpaceToParentFiberAdapter
      search distinction constitutive parent)
    (available : AvailableLiftWithin search distinction) :
    ParentConfigurationAvailable constitutive parent := by
  obtain ⟨member⟩ := available
  exact ⟨adapter.mapMember member⟩

end OCKIndividuationMSpaceComposition
