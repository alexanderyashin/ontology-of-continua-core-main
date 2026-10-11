import OCKIndividuationMSpaceComposition.ConstitutiveBridge

namespace OCKIndividuationMSpaceComposition

universe uIndex uChild uParent

namespace NativeConstitutiveNaturalityBoundary

open ConstitutiveBridge

variable {Index : Type uIndex}
variable {ChildState : Index → Type uChild}
variable {ParentState : Type uParent}

/-!
# Constitutive naturality and its admissibility-only boundary

The constitutive bridge has a typed configuration fiber at each parent.  This
slice adds an explicit relabeling interface on that bridge: a configuration
equivalence and a parent equivalence preserve both admissibility and
realization.  From those field-level premises, parent-fiber availability is
transported in both directions.

The boundary is constructive and concrete.  A bridge may preserve every
admissibility predicate while its parent realization is asymmetric under a
parent flip; then availability changes.  Thus admissibility symmetry alone is
not a constitutive symmetry theorem.

No causal dependency, action, rank, dimension, exchange, or continuum claim is
introduced.
-/

structure ConstitutiveRelabeling
    (bridge : ConstitutiveBridge Index ChildState ParentState) where
  configurationEquiv :
    JointConfiguration Index ChildState ≃ JointConfiguration Index ChildState
  parentEquiv : ParentState ≃ ParentState
  admissible_iff : ∀ configuration,
    bridge.admissible configuration ↔
      bridge.admissible (configurationEquiv configuration)
  realizes_iff : ∀ configuration parent,
    bridge.realizes configuration parent ↔
      bridge.realizes (configurationEquiv configuration)
        (parentEquiv parent)

def ConstitutiveRelabeling.symm
    (relabeling : ConstitutiveRelabeling bridge) :
    ConstitutiveRelabeling bridge where
  configurationEquiv := relabeling.configurationEquiv.symm
  parentEquiv := relabeling.parentEquiv.symm
  admissible_iff := by
    intro configuration
    simpa using
      (relabeling.admissible_iff (relabeling.configurationEquiv.symm configuration)).symm
  realizes_iff := by
    intro configuration parent
    simpa using
      (relabeling.realizes_iff
        (relabeling.configurationEquiv.symm configuration)
        (relabeling.parentEquiv.symm parent)).symm

theorem parentConfigurationAvailable_relabel
    (relabeling : ConstitutiveRelabeling bridge)
    {parent : ParentState} :
    ParentConfigurationAvailable bridge parent →
      ParentConfigurationAvailable bridge (relabeling.parentEquiv parent) := by
  rintro ⟨member⟩
  refine ⟨⟨relabeling.configurationEquiv member.1, ?_⟩⟩
  exact (relabeling.realizes_iff member.1 parent).mp member.2

theorem parentConfigurationAvailable_relabel_iff
    (relabeling : ConstitutiveRelabeling bridge)
    {parent : ParentState} :
    ParentConfigurationAvailable bridge parent ↔
      ParentConfigurationAvailable bridge (relabeling.parentEquiv parent) := by
  constructor
  · exact parentConfigurationAvailable_relabel relabeling
  · intro mapped
    have back := parentConfigurationAvailable_relabel (relabeling.symm)
      (parent := relabeling.parentEquiv parent) mapped
    simpa [ConstitutiveRelabeling.symm] using back

/-! ## Admissibility alone does not transport realization -/

def asymmetricParentBridge :
    ConstitutiveBridge Unit (fun _ => Bool) Bool where
  admissible := fun _ => True
  realizes := fun _ parent => parent = false
  realizes_admissible := by
    intro configuration parent realized
    trivial

def unitConfigurationEquiv :
    JointConfiguration Unit (fun _ => Bool) ≃
      JointConfiguration Unit (fun _ => Bool) :=
  Equiv.refl _

def parentFlip : Bool ≃ Bool where
  toFun := fun value => !value
  invFun := fun value => !value
  left_inv := by intro value; cases value <;> rfl
  right_inv := by intro value; cases value <;> rfl

theorem asymmetricParentBridge_admissibility_flip_invariant :
    ∀ configuration,
      asymmetricParentBridge.admissible configuration ↔
        asymmetricParentBridge.admissible (unitConfigurationEquiv configuration) := by
  intro configuration
  simp [asymmetricParentBridge, unitConfigurationEquiv]

theorem asymmetricParentBridge_availability_changes_under_flip :
    ParentConfigurationAvailable asymmetricParentBridge false ∧
      ¬ ParentConfigurationAvailable asymmetricParentBridge (parentFlip false) := by
  constructor
  · refine ⟨⟨fun _ => false, ?_⟩⟩
    rfl
  · intro available
    rcases available with ⟨⟨configuration, realized⟩⟩
    simpa [asymmetricParentBridge, parentFlip] using realized

theorem admissibility_symmetry_does_not_force_realization_symmetry :
    (∀ configuration,
      asymmetricParentBridge.admissible configuration ↔
        asymmetricParentBridge.admissible (unitConfigurationEquiv configuration)) ∧
    ¬ (∀ configuration parent,
      asymmetricParentBridge.realizes configuration parent ↔
        asymmetricParentBridge.realizes (unitConfigurationEquiv configuration)
          (parentFlip parent)) := by
  refine ⟨asymmetricParentBridge_admissibility_flip_invariant, ?_⟩
  intro realizationPreserved
  have mismatch := realizationPreserved (fun _ => false) false
  simpa [asymmetricParentBridge, unitConfigurationEquiv, parentFlip] using mismatch

end NativeConstitutiveNaturalityBoundary

end OCKIndividuationMSpaceComposition
