import OCKIndividuationMSpaceComposition.ConstitutiveBridge
import OCKIndividuationMSpaceComposition.SymmetryNativeCausalFamilyClosure
import OCKIndividuationMSpaceComposition.SymmetryIntrinsicDimensionBoundary
import Mathlib.Data.Fin.Basic
import Mathlib.Tactic

namespace OCKIndividuationMSpaceComposition

universe uIndex uChild uParent uIntervention

/-!
# Native joint composition and its separation from one-root causal closure

`ConstitutiveBridge` is an existing OC primitive whose input is a typed joint
configuration.  This file makes the multi-source content explicit with the
smallest nontrivial witness: a Boolean parent is the conjunction of two
Boolean child states.

The parent `true` is realized by the joint `(true,true)` configuration, but no
single-support lift from the baseline `false` realizes it.  Thus genuine joint
generation is present in the constitutive layer, while the existing
`GeneratedKernel` family closure remains singleton-generated (as proved in the
companion boundary module).  The missing mathematical integration is now
precise: OC still needs a theorem mapping joint constitutive realizations into
the distinction/dependence closure used for intrinsic rank.

The witness contains no rank, exchange, vector, coordinate, or dimension field.
-/

namespace ConstitutiveBridge

abbrev TwoBitConfiguration := JointConfiguration (Fin 2) (fun _ => Bool)

/-! ## A concrete joint constitutive law -/

def twoBitAndBridge :
    ConstitutiveBridge (Fin 2) (fun _ => Bool) Bool where
  admissible := fun _ => True
  realizes := fun configuration parent =>
    parent = (configuration 0 && configuration 1)
  realizes_admissible := by
    intro configuration parent realized
    simp

def allOnesConfiguration : TwoBitConfiguration :=
  fun _ => true

def allFalseConfiguration : TwoBitConfiguration :=
  fun _ => false

@[simp] theorem twoBitAndBridge_joint_true :
    twoBitAndBridge.realizes allOnesConfiguration true := by
  simp [twoBitAndBridge, allOnesConfiguration]

/-! A single-support lift keeps every nonselected input at the explicit
baseline `false`; the baseline is a premise of this diagnostic, not hidden in
the constitutive bridge. -/

def singleSupportConfiguration
    (index : Fin 2) (state : Bool) : TwoBitConfiguration :=
  fun current => if current = index then state else false

def SingleSupportRealization (parent : Bool) : Prop :=
  ∃ index state,
    twoBitAndBridge.realizes
      (singleSupportConfiguration index state) parent

theorem twoBitAndBridge_true_not_singleSupport :
    ¬ SingleSupportRealization true := by
  rintro ⟨index, state, realized⟩
  fin_cases index <;> cases state <;>
    simp [singleSupportConfiguration, twoBitAndBridge] at realized

/-! ## Support semantics for a constitutive parent -/

/-- A configuration is supported by `support` relative to a baseline when all
indices outside the support retain their baseline state.  The baseline is
explicit data; support is not smuggled into the bridge definition. -/
def SupportConfiguration
    (baseline configuration : TwoBitConfiguration)
    (support : Finset (Fin 2)) : Prop :=
  ∀ index, index ∉ support → configuration index = baseline index

def SupportGenerates
    (baseline : TwoBitConfiguration)
    (support : Finset (Fin 2)) (parent : Bool) : Prop :=
  ∃ configuration,
    SupportConfiguration baseline configuration support ∧
      twoBitAndBridge.realizes configuration parent

theorem supportConfiguration_mono
    {baseline configuration : TwoBitConfiguration}
    {small large : Finset (Fin 2)}
    (supportSubset : small ⊆ large)
    (supported : SupportConfiguration baseline configuration small) :
    SupportConfiguration baseline configuration large := by
  intro index outsideLarge
  apply supported index
  intro outsideSmall
  exact outsideLarge (supportSubset outsideSmall)

theorem supportGenerates_mono
    {baseline : TwoBitConfiguration}
    {small large : Finset (Fin 2)}
    {parent : Bool}
    (supportSubset : small ⊆ large)
    (generated : SupportGenerates baseline small parent) :
    SupportGenerates baseline large parent := by
  obtain ⟨configuration, supported, realized⟩ := generated
  exact ⟨configuration, supportConfiguration_mono supportSubset supported, realized⟩

theorem allOnes_is_supported_by_both_indices :
    SupportConfiguration allFalseConfiguration allOnesConfiguration {0, 1} := by
  intro index indexNotMember
  fin_cases index <;> simp at indexNotMember

theorem twoBitAnd_pair_support_generates_true :
    SupportGenerates allFalseConfiguration {0, 1} true := by
  exact ⟨allOnesConfiguration, allOnes_is_supported_by_both_indices,
    twoBitAndBridge_joint_true⟩

theorem twoBitAnd_singleton_support_not_generates_true
    (index : Fin 2) :
    ¬ SupportGenerates allFalseConfiguration {index} true := by
  rintro ⟨configuration, supported, realized⟩
  fin_cases index
  · have otherFalse : configuration 1 = false := by
      apply supported 1
      simp
    simpa [twoBitAndBridge, otherFalse] using realized
  · have otherFalse : configuration 0 = false := by
      apply supported 0
      simp
    simpa [twoBitAndBridge, otherFalse] using realized

/-! The support pair is therefore genuinely joint under this explicit baseline:
the parent is generated by the pair, but by neither singleton member. -/

theorem twoBitAnd_pair_is_minimal_joint_support :
    SupportGenerates allFalseConfiguration {0, 1} true ∧
      ∀ index, ¬ SupportGenerates allFalseConfiguration {index} true := by
  constructor
  · exact twoBitAnd_pair_support_generates_true
  · exact twoBitAnd_singleton_support_not_generates_true

theorem twoBitAnd_true_support_contains_both
    {support : Finset (Fin 2)}
    (generated : SupportGenerates allFalseConfiguration support true) :
    ({0, 1} : Finset (Fin 2)) ⊆ support := by
  intro index _
  fin_cases index
  · by_contra missing
    obtain ⟨configuration, supported, realized⟩ := generated
    have firstFalse : configuration 0 = false := by
      apply supported 0
      exact missing
    simpa [twoBitAndBridge, firstFalse] using realized
  · by_contra missing
    obtain ⟨configuration, supported, realized⟩ := generated
    have secondFalse : configuration 1 = false := by
      apply supported 1
      exact missing
    simpa [twoBitAndBridge, secondFalse] using realized

theorem twoBitAnd_true_support_iff
    (support : Finset (Fin 2)) :
    SupportGenerates allFalseConfiguration support true ↔
      ({0, 1} : Finset (Fin 2)) ⊆ support := by
  constructor
  · exact twoBitAnd_true_support_contains_both
  · intro containsPair
    exact supportGenerates_mono containsPair
      twoBitAnd_pair_support_generates_true

theorem twoBitAnd_true_support_not_accessible :
    SupportGenerates allFalseConfiguration {0, 1} true ∧
      ∀ index, index ∈ ({0, 1} : Finset (Fin 2)) →
        ¬ SupportGenerates allFalseConfiguration ({0, 1} \ {index}) true := by
  constructor
  · exact twoBitAnd_pair_support_generates_true
  · intro index indexMember
    clear indexMember
    fin_cases index
    · have support_eq :
          ({0, 1} : Finset (Fin 2)) \ {0} = {1} := by
        ext j
        fin_cases j <;> simp
      convert twoBitAnd_singleton_support_not_generates_true (1 : Fin 2) using 1
    · have support_eq :
          ({0, 1} : Finset (Fin 2)) \ {1} = {0} := by
        ext j
        fin_cases j <;> simp
      convert twoBitAnd_singleton_support_not_generates_true (0 : Fin 2) using 1

/-! ## Native finite closure and the exchange boundary

The preceding support theorem can be presented as a finite distinction
closure with two source tokens and one jointly generated parent token.  This
is not a new axiom: the closure rule is exactly the proved characterization
of the AND support predicate.  Its failure of exchange is therefore a native
counterexample to importing matroid-style rank growth without an additional
exchange premise. -/

abbrev TwoBitNativeToken := Fin 3

def twoBitNativeClosure (seed : Finset TwoBitNativeToken) :
    Finset TwoBitNativeToken :=
  if (0 : TwoBitNativeToken) ∈ seed ∧ (1 : TwoBitNativeToken) ∈ seed then
    insert (2 : TwoBitNativeToken) seed
  else
    seed

theorem twoBitNativeClosure_parent_iff (seed : Finset TwoBitNativeToken)
    (parentAbsent : (2 : TwoBitNativeToken) ∉ seed) :
    (2 : TwoBitNativeToken) ∈ twoBitNativeClosure seed ↔
      ({0, 1} : Finset TwoBitNativeToken) ⊆ seed := by
  by_cases both : (0 : TwoBitNativeToken) ∈ seed ∧
      (1 : TwoBitNativeToken) ∈ seed
  · constructor
    · intro _ x hx
      simp only [Finset.mem_insert, Finset.mem_singleton] at hx
      rcases hx with rfl | hx
      · exact both.1
      · have xIsOne : x = (1 : TwoBitNativeToken) := by simpa using hx
        subst x
        exact both.2
    · intro _
      simp [twoBitNativeClosure, both]
  · constructor
    · intro generated
      by_cases parentInSeed : (2 : TwoBitNativeToken) ∈ seed
      · exact False.elim (parentAbsent parentInSeed)
      · simpa [twoBitNativeClosure, both, parentInSeed] using generated
    · intro pairSubset
      exfalso
      apply both
      constructor
      · exact pairSubset (by simp)
      · exact pairSubset (by simp)

theorem twoBitNativeClosure_extensive :
    IntrinsicDimensionBoundary.ClosureExtensive twoBitNativeClosure := by
  intro seed
  by_cases both : (0 : TwoBitNativeToken) ∈ seed ∧
      (1 : TwoBitNativeToken) ∈ seed
  · simp [twoBitNativeClosure, both]
  · simp [twoBitNativeClosure, both]

theorem twoBitNativeClosure_monotone :
    IntrinsicDimensionBoundary.ClosureMonotone twoBitNativeClosure := by
  intro first second subset
  by_cases firstBoth : (0 : TwoBitNativeToken) ∈ first ∧
      (1 : TwoBitNativeToken) ∈ first
  · have secondBoth : (0 : TwoBitNativeToken) ∈ second ∧
        (1 : TwoBitNativeToken) ∈ second :=
      ⟨subset firstBoth.1, subset firstBoth.2⟩
    simpa [twoBitNativeClosure, firstBoth, secondBoth] using
      (Finset.insert_subset_insert (2 : TwoBitNativeToken) subset)
  · by_cases secondBoth : (0 : TwoBitNativeToken) ∈ second ∧
        (1 : TwoBitNativeToken) ∈ second
    · simpa [twoBitNativeClosure, firstBoth, secondBoth] using
        subset.trans (Finset.subset_insert (2 : TwoBitNativeToken) second)
    · simpa [twoBitNativeClosure, firstBoth, secondBoth] using subset

theorem twoBitNativeClosure_idempotent :
    IntrinsicDimensionBoundary.ClosureIdempotent twoBitNativeClosure := by
  intro seed
  by_cases both : (0 : TwoBitNativeToken) ∈ seed ∧
      (1 : TwoBitNativeToken) ∈ seed
  · simp [twoBitNativeClosure, both]
  · simp [twoBitNativeClosure, both]

theorem twoBitNativeClosure_has_joint_generation :
    (2 : TwoBitNativeToken) ∈ twoBitNativeClosure {0, 1} ∧
      (2 : TwoBitNativeToken) ∉ twoBitNativeClosure {0} ∧
      (2 : TwoBitNativeToken) ∉ twoBitNativeClosure {1} := by
  decide

theorem twoBitNativeClosure_fails_exchange :
    ¬ IntrinsicDimensionBoundary.ClosureExchange twoBitNativeClosure := by
  intro exchange
  have generated :
      (2 : TwoBitNativeToken) ∈
        twoBitNativeClosure (insert (1 : TwoBitNativeToken) {0}) := by
    decide
  have fresh :
      (2 : TwoBitNativeToken) ∉ twoBitNativeClosure {0} := by
    decide
  have demanded := exchange {0} (2 : TwoBitNativeToken) (1 : TwoBitNativeToken)
    generated fresh
  have impossible :
      (1 : TwoBitNativeToken) ∉ twoBitNativeClosure
        (insert (2 : TwoBitNativeToken) {0}) := by
    decide
  exact impossible demanded

/-! ## The strict joint-generation witness -/

def JointOnlyRealization : Prop :=
  twoBitAndBridge.realizes allOnesConfiguration true ∧
    ¬ SingleSupportRealization true

theorem twoBitAndBridge_is_genuinely_joint :
    JointOnlyRealization := by
  exact ⟨twoBitAndBridge_joint_true,
    twoBitAndBridge_true_not_singleSupport⟩

/-! The constitutive bridge has no field connecting its parent realization to
causal response data.  The following explicit constant-response model proves
that the joint witness and swap law alone do not entail a `DifferenceWitness`.
This is a boundary theorem, not a claim that the two layers are unrelated in a
future enriched OC model. -/

def constantResponseModel :
    ActiveConstraintModel TwoBitConfiguration Unit Bool where
  response := fun _ _ => true
  responseWithout := fun _ _ _ => true
  port := fun _ => False

theorem constantResponseModel_has_no_difference
    (target support : TwoBitConfiguration) :
    ¬ Nonempty (DifferenceWitness constantResponseModel target support) := by
  rintro ⟨witness⟩
  exact witness.changes rfl

/-! A minimal, explicit response interpretation is sufficient to connect the
constitutive layer to the causal `DifferenceWitness` layer.  The response and
removal-response equations and their inequality are premises of this adapter;
they are not consequences of `ConstitutiveBridge.realizes`. -/

structure ConstitutiveResponseDifferenceAdapter
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    (Intervention : Type uIntervention)
    (bridge : ConstitutiveBridge Index ChildState ParentState) where
  model : ActiveConstraintModel
    (JointConfiguration Index ChildState) Intervention ParentState
  target : JointConfiguration Index ChildState
  support : JointConfiguration Index ChildState
  intervention : Intervention
  fullConfiguration : JointConfiguration Index ChildState
  reducedConfiguration : JointConfiguration Index ChildState
  fullParent : ParentState
  reducedParent : ParentState
  fullRealization : bridge.realizes fullConfiguration fullParent
  reducedRealization : bridge.realizes reducedConfiguration reducedParent
  response_full : model.response target intervention = fullParent
  response_without :
    model.responseWithout target support intervention = reducedParent
  outcomes_differ : fullParent ≠ reducedParent

def ConstitutiveResponseDifferenceAdapter.toDifferenceWitness
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    (Intervention : Type uIntervention)
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    (adapter : ConstitutiveResponseDifferenceAdapter Intervention bridge) :
    DifferenceWitness adapter.model adapter.target adapter.support where
  intervention := adapter.intervention
  changes := by
    rw [adapter.response_full, adapter.response_without]
    exact adapter.outcomes_differ

theorem differenceWitness_of_constitutiveResponseDifferenceAdapter
    {Index : Type uIndex}
    {ChildState : Index → Type uChild}
    {ParentState : Type uParent}
    (Intervention : Type uIntervention)
    {bridge : ConstitutiveBridge Index ChildState ParentState}
    (adapter : ConstitutiveResponseDifferenceAdapter Intervention bridge) :
    Nonempty (DifferenceWitness adapter.model adapter.target adapter.support) :=
  ⟨adapter.toDifferenceWitness⟩

def twoBitResponseModel :
    ActiveConstraintModel TwoBitConfiguration Unit Bool where
  response := fun _ _ => true
  responseWithout := fun _ _ _ => false
  port := fun _ => False

@[simp] theorem twoBitAndBridge_joint_false :
    twoBitAndBridge.realizes allFalseConfiguration false := by
  simp [twoBitAndBridge, allFalseConfiguration]

def twoBitConstitutiveResponseAdapter :
    ConstitutiveResponseDifferenceAdapter Unit twoBitAndBridge where
  model := twoBitResponseModel
  target := allOnesConfiguration
  support := allFalseConfiguration
  intervention := ()
  fullConfiguration := allOnesConfiguration
  reducedConfiguration := allFalseConfiguration
  fullParent := true
  reducedParent := false
  fullRealization := twoBitAndBridge_joint_true
  reducedRealization := twoBitAndBridge_joint_false
  response_full := rfl
  response_without := rfl
  outcomes_differ := by decide

theorem twoBitConstitutiveResponseAdapter_yields_difference :
    Nonempty (DifferenceWitness
      twoBitConstitutiveResponseAdapter.model
      twoBitConstitutiveResponseAdapter.target
      twoBitConstitutiveResponseAdapter.support) :=
  differenceWitness_of_constitutiveResponseDifferenceAdapter
    Unit
    twoBitConstitutiveResponseAdapter

/-! ## Symmetry of the joint law -/

def swapTwoBitConfiguration (configuration : TwoBitConfiguration) :
    TwoBitConfiguration :=
  fun index => configuration (if index = 0 then 1 else 0)

theorem twoBitAndBridge_swap_invariant
    (configuration : TwoBitConfiguration) (parent : Bool) :
    twoBitAndBridge.realizes (swapTwoBitConfiguration configuration) parent ↔
      twoBitAndBridge.realizes configuration parent := by
  by_cases first : configuration 0
  · by_cases second : configuration 1
    · simp [twoBitAndBridge, swapTwoBitConfiguration, first, second]
    · simp [twoBitAndBridge, swapTwoBitConfiguration, first, second]
  · by_cases second : configuration 1
    · simp [twoBitAndBridge, swapTwoBitConfiguration, first, second]
    · simp [twoBitAndBridge, swapTwoBitConfiguration, first, second]

theorem joint_constitutive_layer_does_not_entail_causal_difference :
    ∃ model : ActiveConstraintModel TwoBitConfiguration Unit Bool,
      (SupportGenerates allFalseConfiguration {0, 1} true ∧
        ∀ index, ¬ SupportGenerates allFalseConfiguration {index} true) ∧
      (twoBitAndBridge.realizes (swapTwoBitConfiguration allOnesConfiguration) true ↔
        twoBitAndBridge.realizes allOnesConfiguration true) ∧
      ∀ target support,
        ¬ Nonempty (DifferenceWitness model target support) := by
  refine ⟨constantResponseModel, ?_, ?_, ?_⟩
  · exact twoBitAnd_pair_is_minimal_joint_support
  · exact twoBitAndBridge_swap_invariant allOnesConfiguration true
  · exact constantResponseModel_has_no_difference

end ConstitutiveBridge

end OCKIndividuationMSpaceComposition
