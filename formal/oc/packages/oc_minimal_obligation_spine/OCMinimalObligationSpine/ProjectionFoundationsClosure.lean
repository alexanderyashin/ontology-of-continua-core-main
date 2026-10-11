import OCMinimalObligationSpine.StableProjectionWorldModel
import OCMinimalObligationSpine.BranchKernelIncomparability

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

/-!
# Projection-foundations closure

This module adds only the generic mathematics required to transport the
existing OC projection kernel into an enterprise-domain framework.  It does
not introduce enterprise entities, claim empirical adequacy, identify local
serialization identifiers, or promote the graph K/ruler drafts to theorems.
-/

universe uSource uFine uCoarse uMiddle uIndex uView uEntity

/-! ## Refinement and factorization -/

/-- The coarse encoder is obtained by postcomposing the fine encoder. -/
def FactorsThrough
    {Source : Type uSource}
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    (fine : Source -> Fine)
    (coarse : Source -> Coarse) : Prop :=
  Exists fun factor : Fine -> Coarse => coarse = factor ∘ fine

/-- A total factorization always implies kernel refinement. -/
theorem factorsThrough_implies_kernelRefines
    {Source : Type uSource}
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    {fine : Source -> Fine}
    {coarse : Source -> Coarse}
    (factors : FactorsThrough fine coarse) :
    EncoderKernelRefines fine coarse := by
  rcases factors with ⟨factor, factorization⟩
  intro left right sameFine
  rw [factorization]
  exact congrArg factor sameFine

/-- The actual image of an encoder, separated from unused carrier values. -/
abbrev EncoderRange
    {Source : Type uSource}
    {Fine : Type uFine}
    (fine : Source -> Fine) :=
  { value : Fine // Exists fun source => fine source = value }

/--
Kernel refinement always constructs a factor on the *range* of the fine
encoder.  This is the assumption-free converse to the previous theorem.
-/
noncomputable def kernelFactorOnRange
    {Source : Type uSource}
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    {fine : Source -> Fine}
    (coarse : Source -> Coarse)
    (_refines : EncoderKernelRefines fine coarse) :
    EncoderRange fine -> Coarse :=
  fun value => coarse (Classical.choose value.property)

theorem kernelFactorOnRange_spec
    {Source : Type uSource}
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    {fine : Source -> Fine}
    {coarse : Source -> Coarse}
    (refines : EncoderKernelRefines fine coarse)
    (source : Source) :
    coarse source =
      kernelFactorOnRange coarse refines
        ⟨fine source, ⟨source, rfl⟩⟩ := by
  unfold kernelFactorOnRange
  have chosenSame :
      fine (Classical.choose (show Exists fun candidate =>
        fine candidate = fine source from ⟨source, rfl⟩)) = fine source :=
    Classical.choose_spec (show Exists fun candidate =>
      fine candidate = fine source from ⟨source, rfl⟩)
  exact (refines _ _ chosenSame).symm

theorem kernelRefines_iff_factorsThrough_range
    {Source : Type uSource}
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    {fine : Source -> Fine}
    {coarse : Source -> Coarse} :
    EncoderKernelRefines fine coarse <->
      Exists fun factor : EncoderRange fine -> Coarse =>
        forall source,
          coarse source = factor ⟨fine source, ⟨source, rfl⟩⟩ := by
  constructor
  · intro refines
    exact ⟨kernelFactorOnRange coarse refines,
      kernelFactorOnRange_spec refines⟩
  · rintro ⟨factor, factorizes⟩ left right sameFine
    calc
      coarse left = factor ⟨fine left, ⟨left, rfl⟩⟩ := factorizes left
      _ = factor ⟨fine right, ⟨right, rfl⟩⟩ := by
        congr 1
        exact Subtype.ext sameFine
      _ = coarse right := (factorizes right).symm

/--
If the coarse carrier is inhabited, the range factor extends to a total map
on the entire fine carrier.  Values outside the range are deliberately
arbitrary and have no observational meaning.
-/
noncomputable def totalKernelFactor
    {Source : Type uSource}
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    [Nonempty Coarse]
    {fine : Source -> Fine}
    (coarse : Source -> Coarse)
    (_refines : EncoderKernelRefines fine coarse) : Fine -> Coarse := by
  classical
  exact fun value =>
    if witness : Exists fun source => fine source = value then
      coarse (Classical.choose witness)
    else
      Classical.choice inferInstance

theorem totalKernelFactor_spec
    {Source : Type uSource}
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    [Nonempty Coarse]
    {fine : Source -> Fine}
    {coarse : Source -> Coarse}
    (refines : EncoderKernelRefines fine coarse)
    (source : Source) :
    coarse source = totalKernelFactor coarse refines (fine source) := by
  classical
  unfold totalKernelFactor
  rw [dif_pos (show Exists fun candidate =>
    fine candidate = fine source from ⟨source, rfl⟩)]
  have chosenSame :
      fine (Classical.choose (show Exists fun candidate =>
        fine candidate = fine source from ⟨source, rfl⟩)) = fine source :=
    Classical.choose_spec (show Exists fun candidate =>
      fine candidate = fine source from ⟨source, rfl⟩)
  exact (refines _ _ chosenSame).symm

theorem kernelRefines_implies_factorsThrough_of_coarse_nonempty
    {Source : Type uSource}
    {Fine : Type uFine}
    {Coarse : Type uCoarse}
    [Nonempty Coarse]
    {fine : Source -> Fine}
    {coarse : Source -> Coarse}
    (refines : EncoderKernelRefines fine coarse) :
    FactorsThrough fine coarse := by
  refine ⟨totalKernelFactor coarse refines, ?_⟩
  funext source
  exact totalKernelFactor_spec refines source

/--
Without a carrier condition, kernel refinement need not yield a *total*
factor map: an empty source admits encoders into `Unit` and `Empty`, while no
function `Unit -> Empty` exists.
-/
theorem kernelRefinement_does_not_force_unconditional_total_factor :
    Exists fun fine : Empty -> Unit =>
      Exists fun coarse : Empty -> Empty =>
        EncoderKernelRefines fine coarse ∧
          Not (FactorsThrough fine coarse) := by
  let fine : Empty -> Unit := fun source => nomatch source
  let coarse : Empty -> Empty := fun source => nomatch source
  refine ⟨fine, coarse, ?_, ?_⟩
  · intro left
    exact nomatch left
  · rintro ⟨factor, _⟩
    exact nomatch factor ()

/-! ## Declared intent, sufficiency and minimality -/

/--
An intent is represented only by its required observational equivalence.
Domain methods must justify how this setoid was elicited; OC does not infer it.
-/
def IntentSufficient
    {Source : Type uSource}
    {Carrier : Type uFine}
    (intent : Setoid Source)
    (encode : Source -> Carrier) : Prop :=
  forall {left right}, encode left = encode right -> intent.r left right

/-- Intent coverage is exactly sufficiency relative to the declared intent. -/
abbrev IntentCoverage := @IntentSufficient

/-- A carrier-heterogeneous projection candidate. -/
structure ProjectionCandidate (Source : Type uSource) where
  Carrier : Type uFine
  encode : Source -> Carrier

def CandidateIntentSufficient
    {Source : Type uSource}
    (intent : Setoid Source)
    (candidate : ProjectionCandidate.{uSource, uFine} Source) : Prop :=
  IntentSufficient intent candidate.encode

/--
A minimal-sufficient candidate is admissible and sufficient, and every
admissible sufficient coarsening has the same kernel.  This is "no strictly
coarser admissible sufficient factorization", not a claim of one literal
representation.
-/
def IsAdmissibleMinimalSufficient
    {Source : Type uSource}
    (intent : Setoid Source)
    (admissible : ProjectionCandidate.{uSource, uFine} Source -> Prop)
    (candidate : ProjectionCandidate.{uSource, uFine} Source) : Prop :=
  admissible candidate ∧
    CandidateIntentSufficient intent candidate ∧
    forall other,
      admissible other ->
      CandidateIntentSufficient intent other ->
      EncoderKernelRefines candidate.encode other.encode ->
      EncoderKernelRefines other.encode candidate.encode

/-- The mathematically honest selection result is a predicate/set of minima. -/
def AdmissibleMinimalSufficientSet
    {Source : Type uSource}
    (intent : Setoid Source)
    (admissible : ProjectionCandidate.{uSource, uFine} Source -> Prop) :
    ProjectionCandidate.{uSource, uFine} Source -> Prop :=
  IsAdmissibleMinimalSufficient intent admissible

theorem minimalSufficient_forbids_strictly_coarser_admissible_sufficient
    {Source : Type uSource}
    {intent : Setoid Source}
    {admissible : ProjectionCandidate.{uSource, uFine} Source -> Prop}
    {candidate other : ProjectionCandidate.{uSource, uFine} Source}
    (minimal : IsAdmissibleMinimalSufficient intent admissible candidate)
    (otherAdmissible : admissible other)
    (otherSufficient : CandidateIntentSufficient intent other) :
    Not (EncoderKernelStrictlyRefines candidate.encode other.encode) := by
  intro strict
  exact strict.2
    (minimal.2.2 other otherAdmissible otherSufficient strict.1)

/-! ## Typed composition and stability/sufficiency transport -/

theorem stable_projection_composition
    {Source : Type uSource}
    {Middle : Type uMiddle}
    {Target : Type uCoarse}
    {sourceTransition : Source -> Source}
    {middleTransition : Middle -> Middle}
    {targetTransition : Target -> Target}
    {first : Source -> Middle}
    {second : Middle -> Target}
    (firstStable :
      PreservesTypedDeterministicDynamics sourceTransition first
        middleTransition)
    (secondStable :
      PreservesTypedDeterministicDynamics middleTransition second
        targetTransition) :
    PreservesTypedDeterministicDynamics sourceTransition
      (second ∘ first) targetTransition := by
  intro source
  change second (first (sourceTransition source)) =
    targetTransition (second (first source))
  rw [firstStable source, secondStable (first source)]

theorem composed_sufficiency_implies_first_sufficiency
    {Source : Type uSource}
    {Middle : Type uMiddle}
    {Target : Type uCoarse}
    {intent : Setoid Source}
    {first : Source -> Middle}
    {second : Middle -> Target}
    (composedSufficient : IntentSufficient intent (second ∘ first)) :
    IntentSufficient intent first := by
  intro left right sameFirst
  apply composedSufficient
  exact congrArg second sameFirst

theorem injective_postcomposition_preserves_sufficiency
    {Source : Type uSource}
    {Middle : Type uMiddle}
    {Target : Type uCoarse}
    {intent : Setoid Source}
    {first : Source -> Middle}
    {second : Middle -> Target}
    (firstSufficient : IntentSufficient intent first)
    (secondInjective : Function.Injective second) :
    IntentSufficient intent (second ∘ first) := by
  intro left right sameComposed
  apply firstSufficient
  exact secondInjective sameComposed

/-- Equality is the sharp intent used by the finite sufficiency fixture. -/
def equalityIntent (Source : Type uSource) : Setoid Source where
  r := Eq
  iseqv := ⟨fun _ => rfl, Eq.symm, Eq.trans⟩

theorem identity_is_sufficient_for_equality_intent :
    IntentSufficient (equalityIntent Bool) (fun value : Bool => value) := by
  intro left right same
  exact same

/--
Sufficiency is not preserved by arbitrary postcomposition: erasing both Bool
values destroys the equality distinctions required by the intent.
-/
theorem noninjective_postcomposition_can_destroy_sufficiency :
    Not (IntentSufficient (equalityIntent Bool)
      ((fun _ : Bool => ()) ∘ (fun value : Bool => value))) := by
  intro sufficient
  have falseEqualsTrue : false = true :=
    sufficient (left := false) (right := true) rfl
  exact (by decide : false ≠ true) falseEqualsTrue

/-! ## Compatibility, conflict and cross-projection correspondence -/

namespace ProjectionFamily

/-- Conflict is failure of common realization for the declared full tuple. -/
def Conflict
    (family : ProjectionFamily Entity Index View)
    (views : (index : Index) -> View index) : Prop :=
  Not (family.Compatible views)

theorem compatible_not_conflict
    (family : ProjectionFamily Entity Index View)
    {views : (index : Index) -> View index}
    (compatible : family.Compatible views) :
    Not (family.Conflict views) := by
  exact fun conflict => conflict compatible

/--
A correspondence is typed evidence that two local projected values arise
from one target-side entity.  It does not compare or equate local IDs.
-/
structure CorrespondenceWitness
    (family : ProjectionFamily Entity Index View)
    (leftIndex rightIndex : Index)
    (left : View leftIndex)
    (right : View rightIndex) where
  entity : Entity
  left_matches : family.project leftIndex entity = left
  right_matches : family.project rightIndex entity = right

def Corresponds
    (family : ProjectionFamily Entity Index View)
    (leftIndex rightIndex : Index)
    (left : View leftIndex)
    (right : View rightIndex) : Prop :=
  Nonempty (CorrespondenceWitness family leftIndex rightIndex left right)

theorem one_entity_supplies_typed_correspondence
    (family : ProjectionFamily Entity Index View)
    (leftIndex rightIndex : Index)
    (entity : Entity) :
    family.Corresponds leftIndex rightIndex
      (family.project leftIndex entity)
      (family.project rightIndex entity) := by
  exact ⟨⟨entity, rfl, rfl⟩⟩

end ProjectionFamily

/-! ## Finite compatibility and reconstruction boundary fixtures -/

/-- Every view repeats the same Bool entity value. -/
def boolDiagonalProjectionFamily :
    ProjectionFamily Bool Bool (fun _ => Bool) where
  project := fun _ entity => entity

/-- The declared tuple asks the two indices to report different values. -/
def incompatibleBoolTuple : (index : Bool) -> Bool :=
  fun index => if index then true else false

theorem incompatible_tuple_has_no_common_realization :
    boolDiagonalProjectionFamily.Conflict incompatibleBoolTuple := by
  intro compatible
  rcases compatible with ⟨entity, realizes⟩
  have atFalse := congrFun realizes false
  have atTrue := congrFun realizes true
  cases entity <;>
    simp [ProjectionFamily.signature, boolDiagonalProjectionFamily,
      incompatibleBoolTuple] at atFalse atTrue

/-- A stable family that observes no distinction between Bool states. -/
def constantUnitProjectionFamily :
    ProjectionFamily Bool Unit (fun _ => Unit) where
  project := fun _ _ => ()

theorem constant_projection_dynamics_commute :
    constantUnitProjectionFamily.DynamicsCommute id id := by
  intro entity
  rfl

theorem constant_projection_not_jointly_separating :
    Not constantUnitProjectionFamily.JointlySeparates := by
  intro separates
  have sameSignature :
      constantUnitProjectionFamily.signature false =
        constantUnitProjectionFamily.signature true := by
    funext index
    cases index
    rfl
  have falseEqualsTrue : false = true := separates sameSignature
  exact (by decide : false ≠ true) falseEqualsTrue

end OCMinimalObligationSpine
