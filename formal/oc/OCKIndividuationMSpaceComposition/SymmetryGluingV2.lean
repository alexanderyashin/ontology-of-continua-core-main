import OCKIndividuationMSpaceComposition.ContextIndexedSymmetry

namespace OCKIndividuationMSpaceComposition

universe uContext uState uObservable uEvidence uGlobal uOverlap
universe uStateA uStateB uStateC uObservableA uObservableB uObservableC
universe uEvidenceA uEvidenceB uEvidenceC
universe uPatch uLocal uCechOverlap

/-!
# Local-to-global symmetry, descent, and holonomy

This module adds a finite-cover-style denominator without claiming a sheaf for
every domain.  A cover supplies global-to-local projections and typed overlap
maps.  Local stabilizers must agree through explicit overlap actions.  A global
action is a genuine equivalence whose every projection square commutes.

The restriction map from global actions to compatible local families makes the
two gluing questions exact: surjectivity is existence/descent, while
injectivity is separatedness/uniqueness.  Jointly separating projections imply
injectivity.  Existence remains conditional and can fail even when deliberately
coarse overlaps make local actions pairwise compatible.
-/

/-- Global carrier, local projections, and pairwise overlap presentations. -/
structure SymmetryCover
    {Context : Type uContext}
    (system : ContextIndexedMechanics Context) where
  GlobalState : Type uGlobal
  project : forall context, GlobalState -> system.State context
  Overlap : Context -> Context -> Type uOverlap
  leftOverlap : forall left right,
    system.State left -> Overlap left right
  rightOverlap : forall left right,
    system.State right -> Overlap left right

/-- The projections distinguish global states jointly. -/
def SymmetryCover.JointlySeparates
    {Context : Type uContext}
    {system : ContextIndexedMechanics Context}
    (cover : SymmetryCover system) : Prop :=
  forall {first second : cover.GlobalState},
    (forall context, cover.project context first = cover.project context second) ->
      first = second

/-- Local stabilizers plus one common action on every declared overlap. -/
structure CompatibleLocalSymmetryFamily
    {Context : Type uContext}
    {system : ContextIndexedMechanics Context}
    (cover : SymmetryCover system) where
  atContext : forall context, ContextStabilizer system context
  overlapAction : forall left right,
    cover.Overlap left right ≃ cover.Overlap left right
  left_commutes : forall left right state,
    cover.leftOverlap left right ((atContext left).stateEquiv state) =
      overlapAction left right (cover.leftOverlap left right state)
  right_commutes : forall left right state,
    cover.rightOverlap left right ((atContext right).stateEquiv state) =
      overlapAction left right (cover.rightOverlap left right state)

/-- A global equivalence realizing one compatible local family. -/
structure CoveredGlobalAction
    {Context : Type uContext}
    {system : ContextIndexedMechanics Context}
    (cover : SymmetryCover system) where
  globalEquiv : cover.GlobalState ≃ cover.GlobalState
  localFamily : CompatibleLocalSymmetryFamily cover
  restricts : forall context state,
    cover.project context (globalEquiv state) =
      (localFamily.atContext context).stateEquiv (cover.project context state)

/-- The actual restriction map whose surjectivity/injectivity are descent/separation. -/
def restrictGlobalAction
    {Context : Type uContext}
    {system : ContextIndexedMechanics Context}
    {cover : SymmetryCover system} :
    CoveredGlobalAction cover -> CompatibleLocalSymmetryFamily cover :=
  fun action => action.localFamily

/-- Every compatible local family descends exactly when restriction is surjective. -/
def SymmetryDescent
    {Context : Type uContext}
    {system : ContextIndexedMechanics Context}
    (cover : SymmetryCover system) : Prop :=
  Function.Surjective (@restrictGlobalAction Context system cover)

/-- Global realization is unique from local restrictions exactly when restriction is injective. -/
def SymmetrySeparated
    {Context : Type uContext}
    {system : ContextIndexedMechanics Context}
    (cover : SymmetryCover system) : Prop :=
  Function.Injective (@restrictGlobalAction Context system cover)

theorem CoveredGlobalAction.ext
    {Context : Type uContext}
    {system : ContextIndexedMechanics Context}
    {cover : SymmetryCover system}
    {first second : CoveredGlobalAction cover}
    (sameGlobal : first.globalEquiv = second.globalEquiv)
    (sameLocal : first.localFamily = second.localFamily) :
    first = second := by
  cases first
  cases second
  cases sameGlobal
  cases sameLocal
  rfl

/-- Joint state separation is a sufficient separatedness/uniqueness theorem. -/
theorem jointlySeparatingCover_is_symmetrySeparated
    {Context : Type uContext}
    {system : ContextIndexedMechanics Context}
    (cover : SymmetryCover system)
    (separates : cover.JointlySeparates) :
    SymmetrySeparated cover := by
  intro first second sameLocal
  change first.localFamily = second.localFamily at sameLocal
  apply CoveredGlobalAction.ext (sameLocal := sameLocal)
  apply Equiv.ext
  intro state
  apply separates
  intro context
  calc
    cover.project context (first.globalEquiv state) =
        (first.localFamily.atContext context).stateEquiv
          (cover.project context state) := first.restricts context state
    _ = (second.localFamily.atContext context).stateEquiv
          (cover.project context state) := by
        rw [sameLocal]
    _ = cover.project context (second.globalEquiv state) :=
      (second.restricts context state).symm

/--
Maximal existence characterization for one local family: it lifts precisely
when a global equivalence satisfying all projection squares is supplied.
-/
theorem localFamily_lifts_iff_global_commuting_equiv
    {Context : Type uContext}
    {system : ContextIndexedMechanics Context}
    (cover : SymmetryCover system)
    (family : CompatibleLocalSymmetryFamily cover) :
    (exists action : CoveredGlobalAction cover,
        restrictGlobalAction action = family) <->
      exists globalEquiv : cover.GlobalState ≃ cover.GlobalState,
        forall context state,
          cover.project context (globalEquiv state) =
            (family.atContext context).stateEquiv
              (cover.project context state) := by
  constructor
  · rintro ⟨action, restriction⟩
    refine ⟨action.globalEquiv, ?_⟩
    change action.localFamily = family at restriction
    intro context state
    have square := action.restricts context state
    simpa [restrictGlobalAction, restriction] using square
  · rintro ⟨globalEquiv, squares⟩
    exact ⟨⟨globalEquiv, family, squares⟩, rfl⟩

/-- Descent is the uniform version of the exact commuting-equivalence criterion. -/
theorem symmetryDescent_iff_every_family_has_commuting_equiv
    {Context : Type uContext}
    {system : ContextIndexedMechanics Context}
    (cover : SymmetryCover system) :
    SymmetryDescent cover <->
      forall family : CompatibleLocalSymmetryFamily cover,
        exists globalEquiv : cover.GlobalState ≃ cover.GlobalState,
          forall context state,
            cover.project context (globalEquiv state) =
              (family.atContext context).stateEquiv
                (cover.project context state) := by
  constructor
  · intro descent family
    exact (localFamily_lifts_iff_global_commuting_equiv cover family).1
      (descent family)
  · intro everyFamily family
    exact (localFamily_lifts_iff_global_commuting_equiv cover family).2
      (everyFamily family)

/-!
## Finite Cech matching families

The preceding `SymmetryCover` is a weak projection scaffold.  The following
finite construction makes the matching object itself explicit: a point is one
local state per patch together with all pairwise overlap equalities.
-/

/-- Finite patches, typed local carriers, and two restrictions to each overlap. -/
structure FiniteCechCover
    (Patch : Type uPatch) [Fintype Patch] where
  LocalState : Patch -> Type uLocal
  OverlapState : Patch -> Patch -> Type uCechOverlap
  restrictLeft : forall left right,
    LocalState left -> OverlapState left right
  restrictRight : forall left right,
    LocalState right -> OverlapState left right

/-- A local assignment satisfies every declared pairwise matching equation. -/
def FiniteCechCover.IsMatching
    {Patch : Type uPatch} [Fintype Patch]
    (cover : FiniteCechCover Patch)
    (assignment : forall patch, cover.LocalState patch) : Prop :=
  forall left right,
    cover.restrictLeft left right (assignment left) =
      cover.restrictRight left right (assignment right)

/-- The global matching object is the subtype of compatible local assignments. -/
abbrev FiniteCechMatchingFamily
    {Patch : Type uPatch} [Fintype Patch]
    (cover : FiniteCechCover Patch) :=
  {assignment : forall patch, cover.LocalState patch //
    cover.IsMatching assignment}

/-- A proposed global carrier with restrictions landing in the matching object. -/
structure FiniteCechGlobalPresentation
    {Patch : Type uPatch} [Fintype Patch]
    (cover : FiniteCechCover Patch) where
  GlobalState : Type uGlobal
  restrict : forall patch, GlobalState -> cover.LocalState patch
  restrictions_match : forall global,
    cover.IsMatching (fun patch => restrict patch global)

/-- Concrete restriction from proposed global states to the matching subtype. -/
def finiteCechRestrictGlobal
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (presentation : FiniteCechGlobalPresentation cover) :
    presentation.GlobalState -> FiniteCechMatchingFamily cover :=
  fun global =>
    ⟨fun patch => presentation.restrict patch global,
      presentation.restrictions_match global⟩

/-- Every matching family is realized by a proposed global state. -/
def FiniteCechDescent
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (presentation : FiniteCechGlobalPresentation cover) : Prop :=
  Function.Surjective (finiteCechRestrictGlobal presentation)

/-- Global states are determined by their complete matching family. -/
def FiniteCechSeparated
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (presentation : FiniteCechGlobalPresentation cover) : Prop :=
  Function.Injective (finiteCechRestrictGlobal presentation)

/-- Exact existence-and-uniqueness boundary for the global presentation. -/
theorem finiteCech_bijective_iff_separated_and_descent
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (presentation : FiniteCechGlobalPresentation cover) :
    Function.Bijective (finiteCechRestrictGlobal presentation) <->
      FiniteCechSeparated presentation /\ FiniteCechDescent presentation :=
  Iff.rfl

/-- Local equivalences compatible with the two restrictions on every overlap. -/
structure FiniteCechCompatibleSymmetry
    {Patch : Type uPatch} [Fintype Patch]
    (cover : FiniteCechCover Patch) where
  localEquiv : forall patch,
    cover.LocalState patch ≃ cover.LocalState patch
  overlapEquiv : forall left right,
    cover.OverlapState left right ≃ cover.OverlapState left right
  left_commutes : forall left right state,
    cover.restrictLeft left right (localEquiv left state) =
      overlapEquiv left right (cover.restrictLeft left right state)
  right_commutes : forall left right state,
    cover.restrictRight left right (localEquiv right state) =
      overlapEquiv left right (cover.restrictRight left right state)

/-- Compatibility is closed under coordinatewise inverse. -/
def FiniteCechCompatibleSymmetry.inverse
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (symmetry : FiniteCechCompatibleSymmetry cover) :
    FiniteCechCompatibleSymmetry cover where
  localEquiv := fun patch => (symmetry.localEquiv patch).symm
  overlapEquiv := fun left right => (symmetry.overlapEquiv left right).symm
  left_commutes := by
    intro left right state
    apply (symmetry.overlapEquiv left right).injective
    simpa using
      (symmetry.left_commutes left right
        ((symmetry.localEquiv left).symm state)).symm
  right_commutes := by
    intro left right state
    apply (symmetry.overlapEquiv left right).injective
    simpa using
      (symmetry.right_commutes left right
        ((symmetry.localEquiv right).symm state)).symm

/-- A compatible local symmetry maps matching families to matching families. -/
def FiniteCechCompatibleSymmetry.actOnMatching
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (symmetry : FiniteCechCompatibleSymmetry cover)
    (family : FiniteCechMatchingFamily cover) :
    FiniteCechMatchingFamily cover :=
  ⟨fun patch => symmetry.localEquiv patch (family.1 patch), by
    intro left right
    calc
      cover.restrictLeft left right
          (symmetry.localEquiv left (family.1 left)) =
        symmetry.overlapEquiv left right
          (cover.restrictLeft left right (family.1 left)) :=
            symmetry.left_commutes left right (family.1 left)
      _ = symmetry.overlapEquiv left right
          (cover.restrictRight left right (family.1 right)) :=
            congrArg (symmetry.overlapEquiv left right)
              (family.2 left right)
      _ = cover.restrictRight left right
          (symmetry.localEquiv right (family.1 right)) :=
            (symmetry.right_commutes left right (family.1 right)).symm⟩

/-- Coordinatewise compatible action is an equivalence of the matching object. -/
def FiniteCechCompatibleSymmetry.matchingEquiv
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (symmetry : FiniteCechCompatibleSymmetry cover) :
    FiniteCechMatchingFamily cover ≃ FiniteCechMatchingFamily cover where
  toFun := symmetry.actOnMatching
  invFun := symmetry.inverse.actOnMatching
  left_inv := by
    intro family
    apply Subtype.ext
    funext patch
    simp [FiniteCechCompatibleSymmetry.actOnMatching,
      FiniteCechCompatibleSymmetry.inverse]
  right_inv := by
    intro family
    apply Subtype.ext
    funext patch
    simp [FiniteCechCompatibleSymmetry.actOnMatching,
      FiniteCechCompatibleSymmetry.inverse]

@[simp] theorem FiniteCechCompatibleSymmetry.matchingEquiv_coordinate
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (symmetry : FiniteCechCompatibleSymmetry cover)
    (family : FiniteCechMatchingFamily cover)
    (patch : Patch) :
    (symmetry.matchingEquiv family).1 patch =
      symmetry.localEquiv patch (family.1 patch) :=
  rfl

/-- Any matching-object equivalence with these coordinates is the glued action. -/
theorem FiniteCechCompatibleSymmetry.matchingEquiv_unique
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (symmetry : FiniteCechCompatibleSymmetry cover)
    (candidate : FiniteCechMatchingFamily cover ≃
      FiniteCechMatchingFamily cover)
    (coordinates : forall family patch,
      (candidate family).1 patch =
        symmetry.localEquiv patch (family.1 patch)) :
    candidate = symmetry.matchingEquiv := by
  apply Equiv.ext
  intro family
  apply Subtype.ext
  funext patch
  exact coordinates family patch

/-- Bijective descent identifies a proposed global carrier with the matching object. -/
noncomputable def FiniteCechGlobalPresentation.restrictionEquiv
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (presentation : FiniteCechGlobalPresentation cover)
    (bijective : Function.Bijective
      (finiteCechRestrictGlobal presentation)) :
    presentation.GlobalState ≃ FiniteCechMatchingFamily cover :=
  Equiv.ofBijective (finiteCechRestrictGlobal presentation) bijective

/--
Under existence and uniqueness of global realization, the matching-object
symmetry conjugates to a genuine equivalence of the proposed global carrier.
-/
noncomputable def FiniteCechCompatibleSymmetry.glueToGlobal
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (symmetry : FiniteCechCompatibleSymmetry cover)
    (presentation : FiniteCechGlobalPresentation cover)
    (bijective : Function.Bijective
      (finiteCechRestrictGlobal presentation)) :
    presentation.GlobalState ≃ presentation.GlobalState :=
  ((presentation.restrictionEquiv bijective).trans
      symmetry.matchingEquiv).trans
    (presentation.restrictionEquiv bijective).symm

/-- The conjugated global symmetry has exactly the requested local coordinates. -/
theorem FiniteCechCompatibleSymmetry.glueToGlobal_restricts
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (symmetry : FiniteCechCompatibleSymmetry cover)
    (presentation : FiniteCechGlobalPresentation cover)
    (bijective : Function.Bijective
      (finiteCechRestrictGlobal presentation))
    (global : presentation.GlobalState) :
    finiteCechRestrictGlobal presentation
        (symmetry.glueToGlobal presentation bijective global) =
      symmetry.matchingEquiv
        (finiteCechRestrictGlobal presentation global) := by
  change
    (presentation.restrictionEquiv bijective)
        ((presentation.restrictionEquiv bijective).symm
          (symmetry.matchingEquiv
            ((presentation.restrictionEquiv bijective) global))) =
      symmetry.matchingEquiv
        ((presentation.restrictionEquiv bijective) global)
  exact (presentation.restrictionEquiv bijective).apply_symm_apply _

/-- A global equivalence with the same matching restriction is unique. -/
theorem FiniteCechCompatibleSymmetry.glueToGlobal_unique
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (symmetry : FiniteCechCompatibleSymmetry cover)
    (presentation : FiniteCechGlobalPresentation cover)
    (bijective : Function.Bijective
      (finiteCechRestrictGlobal presentation))
    (candidate : presentation.GlobalState ≃ presentation.GlobalState)
    (restricts : forall global,
      finiteCechRestrictGlobal presentation (candidate global) =
        symmetry.matchingEquiv
          (finiteCechRestrictGlobal presentation global)) :
    candidate = symmetry.glueToGlobal presentation bijective := by
  apply Equiv.ext
  intro global
  apply bijective.1
  exact (restricts global).trans
    (symmetry.glueToGlobal_restricts presentation bijective global).symm

/-!
## Cocycles, holonomy, and descent obstruction on the finite cover
-/

/-- Pairwise local transports before any cocycle law is assumed. -/
structure FiniteCechTransportData
    {Patch : Type uPatch} [Fintype Patch]
    (cover : FiniteCechCover Patch) where
  transport : forall source target,
    cover.LocalState source ≃ cover.LocalState target

/-- Identity and composition equations for a coherent transport cocycle. -/
def FiniteCechTransportData.Cocycle
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transportData : FiniteCechTransportData cover) : Prop :=
  (forall patch,
      transportData.transport patch patch =
        Equiv.refl (cover.LocalState patch)) /\
  (forall first second third,
      (transportData.transport first second).trans
          (transportData.transport second third) =
        transportData.transport first third)

/-- Transport accumulated around a three-patch cycle. -/
def finiteCechThreeHolonomy
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transportData : FiniteCechTransportData cover)
    (first second third : Patch) :
    cover.LocalState first ≃ cover.LocalState first :=
  ((transportData.transport first second).trans
      (transportData.transport second third)).trans
    (transportData.transport third first)

/-- A transport cocycle has identity holonomy on every three-patch loop. -/
theorem finiteCech_cocycle_trivializes_threeHolonomy
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transportData : FiniteCechTransportData cover)
    (cocycle : transportData.Cocycle)
    (first second third : Patch) :
    finiteCechThreeHolonomy transportData first second third =
      Equiv.refl (cover.LocalState first) := by
  calc
    finiteCechThreeHolonomy transportData first second third =
        (transportData.transport first third).trans
          (transportData.transport third first) := by
            exact congrArg
              (fun transport =>
                transport.trans (transportData.transport third first))
              (cocycle.2 first second third)
    _ = transportData.transport first first :=
      cocycle.2 first third first
    _ = Equiv.refl (cover.LocalState first) := cocycle.1 first

/--
Weak predecessor predicate: arbitrary pairwise transports respect one supplied
matching family.  The overlap-compatible layer below derives this predicate
from restriction laws instead of assuming it family by family.
-/
def FiniteCechTransportData.CarriesMatchingFamily
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transportData : FiniteCechTransportData cover)
    (family : FiniteCechMatchingFamily cover) : Prop :=
  forall source target,
    transportData.transport source target (family.1 source) =
      family.1 target

/-- Every transport-compatible matching family is fixed by cycle holonomy. -/
theorem finiteCech_holonomy_fixes_matchingFamily
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transportData : FiniteCechTransportData cover)
    (family : FiniteCechMatchingFamily cover)
    (carries : transportData.CarriesMatchingFamily family)
    (first second third : Patch) :
    finiteCechThreeHolonomy transportData first second third
        (family.1 first) = family.1 first := by
  change transportData.transport third first
      (transportData.transport second third
        (transportData.transport first second (family.1 first))) =
    family.1 first
  rw [carries first second, carries second third, carries third first]

/-- Nonfixed holonomy forbids a transport-compatible matching family at an anchor. -/
theorem finiteCech_nonfixedHolonomy_obstructs_anchored_matching
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transportData : FiniteCechTransportData cover)
    (first second third : Patch)
    (anchor : cover.LocalState first)
    (nonfixed : finiteCechThreeHolonomy transportData first second third
      anchor ≠ anchor) :
    Not (exists family : FiniteCechMatchingFamily cover,
      transportData.CarriesMatchingFamily family /\
        family.1 first = anchor) := by
  rintro ⟨family, carries, anchored⟩
  have fixed := finiteCech_holonomy_fixes_matchingFamily
    transportData family carries first second third
  rw [anchored] at fixed
  exact nonfixed fixed

/-- The proposed global restrictions are compatible with pairwise transport. -/
structure FiniteCechTransportDescent
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (presentation : FiniteCechGlobalPresentation cover)
    (transportData : FiniteCechTransportData cover) : Prop where
  carries_global : forall global source target,
    transportData.transport source target
        (presentation.restrict source global) =
      presentation.restrict target global

/-- Nonfixed holonomy obstructs a global state with the prescribed local anchor. -/
theorem finiteCech_nonfixedHolonomy_obstructs_global_anchor
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (presentation : FiniteCechGlobalPresentation cover)
    (transportData : FiniteCechTransportData cover)
    (descent : FiniteCechTransportDescent presentation transportData)
    (first second third : Patch)
    (anchor : cover.LocalState first)
    (nonfixed : finiteCechThreeHolonomy transportData first second third
      anchor ≠ anchor) :
    Not (exists global : presentation.GlobalState,
      presentation.restrict first global = anchor) := by
  rintro ⟨global, anchored⟩
  apply nonfixed
  change transportData.transport third first
      (transportData.transport second third
        (transportData.transport first second anchor)) = anchor
  rw [← anchored, descent.carries_global global first second,
    descent.carries_global global second third,
    descent.carries_global global third first]

/-- Nonidentity three-cycle holonomy is an explicit cocycle obstruction. -/
theorem finiteCech_nontrivialHolonomy_refutes_cocycle
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transportData : FiniteCechTransportData cover)
    (first second third : Patch)
    (nontrivial : finiteCechThreeHolonomy transportData first second third ≠
      Equiv.refl (cover.LocalState first)) :
    Not transportData.Cocycle := by
  intro cocycle
  exact nontrivial
    (finiteCech_cocycle_trivializes_threeHolonomy transportData cocycle
      first second third)

/-!
## Overlap-compatible transport and derived descent obstruction

`FiniteCechTransportData` alone is only a family of equivalences between local
carriers.  The following stronger structure ties every transport to the actual
declared overlap.  Its separation premise says that the target-side overlap
restriction determines a target local state.  This is a strong, explicit
domain premise; it is not inferred for an arbitrary cover.
-/

/--
Pairwise transport whose image has the same overlap restriction as its source,
with target states separated by that restriction.
-/
structure OverlapCompatibleFiniteCechTransport
    {Patch : Type uPatch} [Fintype Patch]
    (cover : FiniteCechCover Patch) where
  transportData : FiniteCechTransportData cover
  rightOverlap_separates : forall source target,
    Function.Injective (cover.restrictRight source target)
  transport_restricts : forall source target state,
    cover.restrictRight source target
        (transportData.transport source target state) =
      cover.restrictLeft source target state

/--
Overlap compatibility derives transport of every matching family; no separate
`CarriesMatchingFamily` witness is required.
-/
theorem OverlapCompatibleFiniteCechTransport.carriesMatchingFamily
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transport : OverlapCompatibleFiniteCechTransport cover)
    (family : FiniteCechMatchingFamily cover) :
    transport.transportData.CarriesMatchingFamily family := by
  intro source target
  apply transport.rightOverlap_separates source target
  calc
    cover.restrictRight source target
        (transport.transportData.transport source target
          (family.1 source)) =
      cover.restrictLeft source target (family.1 source) :=
        transport.transport_restricts source target (family.1 source)
    _ = cover.restrictRight source target (family.1 target) :=
      family.2 source target

/-- Cocycle law for the overlap-compatible transport's underlying arrows. -/
def OverlapCompatibleFiniteCechTransport.Cocycle
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transport : OverlapCompatibleFiniteCechTransport cover) : Prop :=
  transport.transportData.Cocycle

/-- Three-cycle holonomy of overlap-compatible transport. -/
def overlapCompatibleFiniteCechThreeHolonomy
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transport : OverlapCompatibleFiniteCechTransport cover)
    (first second third : Patch) :
    cover.LocalState first ≃ cover.LocalState first :=
  finiteCechThreeHolonomy transport.transportData first second third

/-- The derived cocycle still forces identity holonomy. -/
theorem overlapCompatible_cocycle_trivializes_threeHolonomy
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transport : OverlapCompatibleFiniteCechTransport cover)
    (cocycle : transport.Cocycle)
    (first second third : Patch) :
    overlapCompatibleFiniteCechThreeHolonomy transport first second third =
      Equiv.refl (cover.LocalState first) :=
  finiteCech_cocycle_trivializes_threeHolonomy
    transport.transportData cocycle first second third

/-- Every matching family is fixed by the overlap-derived cycle holonomy. -/
theorem overlapCompatible_holonomy_fixes_matchingFamily
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transport : OverlapCompatibleFiniteCechTransport cover)
    (family : FiniteCechMatchingFamily cover)
    (first second third : Patch) :
    overlapCompatibleFiniteCechThreeHolonomy transport first second third
        (family.1 first) = family.1 first :=
  finiteCech_holonomy_fixes_matchingFamily
    transport.transportData family (transport.carriesMatchingFamily family)
      first second third

/--
A nonfixed anchor now obstructs an ordinary matching family, without an extra
family-specific transport premise.
-/
theorem overlapCompatible_nonfixedHolonomy_obstructs_anchored_matching
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transport : OverlapCompatibleFiniteCechTransport cover)
    (first second third : Patch)
    (anchor : cover.LocalState first)
    (nonfixed : overlapCompatibleFiniteCechThreeHolonomy transport
      first second third anchor ≠ anchor) :
    Not (exists family : FiniteCechMatchingFamily cover,
      family.1 first = anchor) := by
  rintro ⟨family, anchored⟩
  have fixed := overlapCompatible_holonomy_fixes_matchingFamily
    transport family first second third
  rw [anchored] at fixed
  exact nonfixed fixed

/--
Every proposed global state restricts to a matching family, so the same
nonfixed anchor obstructs global realization without separately postulating
`FiniteCechTransportDescent`.
-/
theorem overlapCompatible_nonfixedHolonomy_obstructs_global_anchor
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (presentation : FiniteCechGlobalPresentation cover)
    (transport : OverlapCompatibleFiniteCechTransport cover)
    (first second third : Patch)
    (anchor : cover.LocalState first)
    (nonfixed : overlapCompatibleFiniteCechThreeHolonomy transport
      first second third anchor ≠ anchor) :
    Not (exists global : presentation.GlobalState,
      presentation.restrict first global = anchor) := by
  rintro ⟨global, anchored⟩
  have fixed := overlapCompatible_holonomy_fixes_matchingFamily
    transport (finiteCechRestrictGlobal presentation global)
      first second third
  change overlapCompatibleFiniteCechThreeHolonomy transport
      first second third (presentation.restrict first global) =
    presentation.restrict first global at fixed
  rw [anchored] at fixed
  exact nonfixed fixed

/--
If holonomy changes even one declared overlap image of the anchor, matching
descent at that anchor is impossible.
-/
theorem overlapCompatible_overlapVisibleHolonomy_obstructs_anchored_matching
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transport : OverlapCompatibleFiniteCechTransport cover)
    (first second third probe : Patch)
    (anchor : cover.LocalState first)
    (overlapChanges :
      cover.restrictLeft first probe
          (overlapCompatibleFiniteCechThreeHolonomy transport
            first second third anchor) ≠
        cover.restrictLeft first probe anchor) :
    Not (exists family : FiniteCechMatchingFamily cover,
      family.1 first = anchor) := by
  apply overlapCompatible_nonfixedHolonomy_obstructs_anchored_matching
    transport first second third anchor
  intro fixed
  exact overlapChanges (congrArg (cover.restrictLeft first probe) fixed)

/-- Overlap-visible nontrivial holonomy likewise obstructs a global anchor. -/
theorem overlapCompatible_overlapVisibleHolonomy_obstructs_global_anchor
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (presentation : FiniteCechGlobalPresentation cover)
    (transport : OverlapCompatibleFiniteCechTransport cover)
    (first second third probe : Patch)
    (anchor : cover.LocalState first)
    (overlapChanges :
      cover.restrictLeft first probe
          (overlapCompatibleFiniteCechThreeHolonomy transport
            first second third anchor) ≠
        cover.restrictLeft first probe anchor) :
    Not (exists global : presentation.GlobalState,
      presentation.restrict first global = anchor) := by
  apply overlapCompatible_nonfixedHolonomy_obstructs_global_anchor
    presentation transport first second third anchor
  intro fixed
  exact overlapChanges (congrArg (cover.restrictLeft first probe) fixed)

/-- Nonidentity overlap-compatible holonomy refutes its cocycle law. -/
theorem overlapCompatible_nontrivialHolonomy_refutes_cocycle
    {Patch : Type uPatch} [Fintype Patch]
    {cover : FiniteCechCover Patch}
    (transport : OverlapCompatibleFiniteCechTransport cover)
    (first second third : Patch)
    (nontrivial : overlapCompatibleFiniteCechThreeHolonomy transport
      first second third ≠ Equiv.refl (cover.LocalState first)) :
    Not transport.Cocycle := by
  intro cocycle
  exact nontrivial
    (overlapCompatible_cocycle_trivializes_threeHolonomy
      transport cocycle first second third)

/-!
## Exact context-loop holonomy
-/

/-- State action accumulated around a three-context exact loop. -/
def threeContextHolonomy
    {StateA : Type uStateA} {ObservableA : Type uObservableA}
    {EvidenceA : Type uEvidenceA}
    {StateB : Type uStateB} {ObservableB : Type uObservableB}
    {EvidenceB : Type uEvidenceB}
    {StateC : Type uStateC} {ObservableC : Type uObservableC}
    {EvidenceC : Type uEvidenceC}
    {mechanicsA : LocalMechanics StateA ObservableA EvidenceA}
    {mechanicsB : LocalMechanics StateB ObservableB EvidenceB}
    {mechanicsC : LocalMechanics StateC ObservableC EvidenceC}
    (ab : ExactContextEquivalence mechanicsA mechanicsB)
    (bc : ExactContextEquivalence mechanicsB mechanicsC)
    (ca : ExactContextEquivalence mechanicsC mechanicsA) : StateA ≃ StateA :=
  (ab.stateEquiv.trans bc.stateEquiv).trans ca.stateEquiv

/-- A loop is coherent exactly when its holonomy fixes every starting state. -/
theorem threeContextLoop_coherent_iff_pointwise_identity
    {StateA : Type uStateA} {ObservableA : Type uObservableA}
    {EvidenceA : Type uEvidenceA}
    {StateB : Type uStateB} {ObservableB : Type uObservableB}
    {EvidenceB : Type uEvidenceB}
    {StateC : Type uStateC} {ObservableC : Type uObservableC}
    {EvidenceC : Type uEvidenceC}
    {mechanicsA : LocalMechanics StateA ObservableA EvidenceA}
    {mechanicsB : LocalMechanics StateB ObservableB EvidenceB}
    {mechanicsC : LocalMechanics StateC ObservableC EvidenceC}
    (ab : ExactContextEquivalence mechanicsA mechanicsB)
    (bc : ExactContextEquivalence mechanicsB mechanicsC)
    (ca : ExactContextEquivalence mechanicsC mechanicsA) :
    threeContextHolonomy ab bc ca = Equiv.refl StateA <->
      forall state,
        threeContextHolonomy ab bc ca state = state := by
  constructor
  · intro coherent state
    rw [coherent]
    rfl
  · intro pointwise
    apply Equiv.ext
    exact pointwise

/-- Nonidentity holonomy is an exact obstruction to path-independent loop transport. -/
theorem nontrivialHolonomy_obstructs_coherence
    {StateA : Type uStateA} {ObservableA : Type uObservableA}
    {EvidenceA : Type uEvidenceA}
    {StateB : Type uStateB} {ObservableB : Type uObservableB}
    {EvidenceB : Type uEvidenceB}
    {StateC : Type uStateC} {ObservableC : Type uObservableC}
    {EvidenceC : Type uEvidenceC}
    {mechanicsA : LocalMechanics StateA ObservableA EvidenceA}
    {mechanicsB : LocalMechanics StateB ObservableB EvidenceB}
    {mechanicsC : LocalMechanics StateC ObservableC EvidenceC}
    (ab : ExactContextEquivalence mechanicsA mechanicsB)
    (bc : ExactContextEquivalence mechanicsB mechanicsC)
    (ca : ExactContextEquivalence mechanicsC mechanicsA)
    (nontrivial : threeContextHolonomy ab bc ca ≠ Equiv.refl StateA) :
    Not (forall state, threeContextHolonomy ab bc ca state = state) := by
  intro pointwise
  exact nontrivial
    ((threeContextLoop_coherent_iff_pointwise_identity ab bc ca).2 pointwise)

/-- Boolean negation is an exact self-equivalence of the coarse mechanics. -/
def boolNegationContextEquivalence :
    ExactContextEquivalence boolCoarseMechanics boolCoarseMechanics where
  stateEquiv := boolNegationEquiv
  observableEquiv := Equiv.refl Unit
  evidenceEquiv := Equiv.refl Unit
  transition_iff := by
    intro left right
    cases left <;> cases right <;>
      simp [boolCoarseMechanics, boolNegationEquiv]
  observation_commutes := by intro state; rfl
  evidence_commutes := by intro state; rfl
  admissible_iff := by intro state; rfl

/-- Three individually exact arrows can carry nontrivial loop holonomy. -/
theorem bool_exact_loop_has_nontrivial_holonomy :
    threeContextHolonomy
        (ExactContextEquivalence.identity boolCoarseMechanics)
        (ExactContextEquivalence.identity boolCoarseMechanics)
        boolNegationContextEquivalence ≠
      Equiv.refl Bool := by
  intro equal
  have atFalse := congrArg (fun action : Bool ≃ Bool => action false) equal
  change (!false : Bool) = false at atFalse
  simp at atFalse

/-!
## Pairwise-compatible but unglueable fixture
-/

inductive TwoPatch
  | left
  | right
deriving DecidableEq

def twoPatchSystem : ContextIndexedMechanics TwoPatch where
  State := fun _ => Bool
  Observable := fun _ => Unit
  Evidence := fun _ => Unit
  atContext := fun _ => boolCoarseMechanics

def twoPatchCover : SymmetryCover twoPatchSystem where
  GlobalState := Bool
  project := fun _ state => state
  Overlap := fun _ _ => Unit
  leftOverlap := fun _ _ _ => ()
  rightOverlap := fun _ _ _ => ()

def twoPatchConflictingFamily :
    CompatibleLocalSymmetryFamily twoPatchCover where
  atContext := fun context =>
    match context with
    | .left => LocalSymmetry.identity boolCoarseMechanics
    | .right => boolNegationCoarseSymmetry
  overlapAction := fun _ _ => Equiv.refl Unit
  left_commutes := by intro left right state; rfl
  right_commutes := by intro left right state; rfl

/-- Coarse overlap compatibility is insufficient for a global action. -/
theorem pairwiseCompatible_localFamily_need_not_glue :
    Not (exists action : CoveredGlobalAction twoPatchCover,
      restrictGlobalAction action = twoPatchConflictingFamily) := by
  rintro ⟨action, sameFamily⟩
  change action.localFamily = twoPatchConflictingFamily at sameFamily
  have leftSquare := action.restricts TwoPatch.left false
  have rightSquare := action.restricts TwoPatch.right false
  change action.globalEquiv false =
    (action.localFamily.atContext TwoPatch.left).stateEquiv false at leftSquare
  change action.globalEquiv false =
    (action.localFamily.atContext TwoPatch.right).stateEquiv false at rightSquare
  rw [sameFamily] at leftSquare rightSquare
  change action.globalEquiv false = false at leftSquare
  change action.globalEquiv false = true at rightSquare
  exact Bool.false_ne_true (leftSquare.symm.trans rightSquare)

/-!
## Gauge ambiguity when projections do not separate
-/

def onePatchSystem : ContextIndexedMechanics Unit where
  State := fun _ => Bool
  Observable := fun _ => Unit
  Evidence := fun _ => Unit
  atContext := fun _ => boolCoarseMechanics

def onePatchHiddenCover : SymmetryCover onePatchSystem where
  GlobalState := Bool × Bool
  project := fun _ state => state.1
  Overlap := fun _ _ => Unit
  leftOverlap := fun _ _ _ => ()
  rightOverlap := fun _ _ _ => ()

def onePatchIdentityFamily :
    CompatibleLocalSymmetryFamily onePatchHiddenCover where
  atContext := fun _ => LocalSymmetry.identity boolCoarseMechanics
  overlapAction := fun _ _ => Equiv.refl Unit
  left_commutes := by intro left right state; rfl
  right_commutes := by intro left right state; rfl

def onePatchGlobalIdentity : CoveredGlobalAction onePatchHiddenCover where
  globalEquiv := Equiv.refl (Bool × Bool)
  localFamily := onePatchIdentityFamily
  restricts := by intro context state; rfl

def onePatchGlobalHiddenSwap : CoveredGlobalAction onePatchHiddenCover where
  globalEquiv := hiddenBoolCoordinateSwapEquiv
  localFamily := onePatchIdentityFamily
  restricts := by intro context state; rfl

/-- Hidden gauge action makes restriction non-injective without separation. -/
theorem nonseparatingCover_has_nonunique_global_lifts :
    Not (SymmetrySeparated onePatchHiddenCover) := by
  intro separated
  have equalActions : onePatchGlobalIdentity = onePatchGlobalHiddenSwap :=
    separated rfl
  have equalGlobal := congrArg CoveredGlobalAction.globalEquiv equalActions
  exact fstIdentity_and_hiddenSwap_have_distinct_micro_actions equalGlobal

/-!
The generic boundary now has two layers.  The earlier projection scaffold
separates restriction, descent, and hidden-gauge ambiguity.  The finite Cech
layer constructs the actual matching subtype, glues every overlap-compatible
coordinate symmetry to a unique matching-object action, conjugates that action
to a unique proposed global action under bijective descent, and separates weak
carrier-only transport from overlap-compatible transport.  Only the latter
derives matching-family transport and hence anchor/global holonomy obstructions
from actual restriction equations.  A scientific domain must still supply its
finite cover, restrictions, transport/descent contract, overlap separation and
commutation when required, and evidence that the local actions are substantive
mechanics rather than encoding or relabeling controls.
-/

end OCKIndividuationMSpaceComposition
