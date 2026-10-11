import Mathlib.Logic.Relation
import Mathlib.Order.Defs.PartialOrder

/-!
# Partially ordered dynamics capability profiles

Capabilities form an inclusion order, not a privileged scalar ladder.  Two
profiles may be incomparable because each can support a capability absent from
the other.
-/

namespace OCMaturityCompletionCycle

/-- Observation modes, recorded as supported capabilities rather than a tier. -/
inductive ObservationCapability where
  | partialObservation
  | fullObservation
  deriving DecidableEq, Repr

/-- State-memory modes. -/
inductive MemoryCapability where
  | memoryless
  | historyDependent
  deriving DecidableEq, Repr

/-- Intervention modes. -/
inductive ControlCapability where
  | passive
  | controlled
  deriving DecidableEq, Repr

/-- Deterministic and stochastic dynamics are explicit, non-default modes. -/
inductive RandomnessCapability where
  | deterministic
  | stochastic
  deriving DecidableEq, Repr

/-- Boundary and recurrence modes. -/
inductive OpenSystemCapability where
  | closed
  | openBoundary
  | feedback
  deriving DecidableEq, Repr

/-- Context-indexing modes. -/
inductive ContextCapability where
  | fixed
  | indexed
  deriving DecidableEq, Repr

/-- Identity presentation modes; none is silently treated as universal. -/
inductive IdentityCapability where
  | functional
  | lineage
  | overlap
  deriving DecidableEq, Repr

/-- Exact and resource-bounded approximation modes. -/
inductive ApproximationCapability where
  | exact
  | approximate
  | resourceBounded
  deriving DecidableEq, Repr

/-- Composition modes with separately testable laws. -/
inductive CompositionCapability where
  | sequential
  | independentParallel
  | feedback
  deriving DecidableEq, Repr

/--
Typed disjoint union of declared capability axes.  A profile may support more
than one value on an axis, because support is not an exclusive classification.
-/
inductive DynamicsCapability where
  | observation (mode : ObservationCapability)
  | memory (mode : MemoryCapability)
  | control (mode : ControlCapability)
  | randomness (mode : RandomnessCapability)
  | openness (mode : OpenSystemCapability)
  | context (mode : ContextCapability)
  | identity (mode : IdentityCapability)
  | approximation (mode : ApproximationCapability)
  | composition (mode : CompositionCapability)
  deriving DecidableEq, Repr

/-- A profile is the proposition-valued set of capabilities it supports. -/
structure DynamicsCapabilityProfile where
  supports : DynamicsCapability → Prop

instance : LE DynamicsCapabilityProfile where
  le left right := ∀ capability, left.supports capability → right.supports capability

instance : PartialOrder DynamicsCapabilityProfile where
  le_refl profile capability := id
  le_trans left middle right leftMiddle middleRight capability :=
    middleRight capability ∘ leftMiddle capability
  le_antisymm := by
    intro left right leftRight rightLeft
    cases left with
    | mk leftSupports =>
      cases right with
      | mk rightSupports =>
        congr
        funext capability
        apply propext
        exact ⟨leftRight capability, rightLeft capability⟩

/-- The profile supporting exactly one named capability. -/
def singletonCapabilityProfile
    (capability : DynamicsCapability) : DynamicsCapabilityProfile :=
  ⟨fun candidate => candidate = capability⟩

/-- Distinct singleton capability profiles are incomparable in one direction. -/
theorem singletonCapabilityProfile_not_le
    (left right : DynamicsCapability)
    (different : left ≠ right) :
    ¬ singletonCapabilityProfile left ≤ singletonCapabilityProfile right := by
  intro included
  exact different (included left rfl)

/-- Distinct capabilities provide a concrete incomparable-profile witness. -/
theorem distinctCapabilities_yield_incomparable_profiles
    (left right : DynamicsCapability)
    (different : left ≠ right) :
    (¬ singletonCapabilityProfile left ≤ singletonCapabilityProfile right) ∧
      (¬ singletonCapabilityProfile right ≤ singletonCapabilityProfile left) := by
  exact ⟨singletonCapabilityProfile_not_le left right different,
    singletonCapabilityProfile_not_le right left different.symm⟩

/-- Genuine cross-axis witness that the profile order is not a scalar chain. -/
theorem fullObservation_and_feedbackProfiles_are_incomparable :
    (¬ singletonCapabilityProfile
        (.observation .fullObservation) ≤
      singletonCapabilityProfile
        (.composition .feedback)) ∧
    (¬ singletonCapabilityProfile
        (.composition .feedback) ≤
      singletonCapabilityProfile
        (.observation .fullObservation)) := by
  apply distinctCapabilities_yield_incomparable_profiles
  intro impossible
  cases impossible

end OCMaturityCompletionCycle
