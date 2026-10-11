import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionCommutation
import Mathlib.Algebra.Ring.BooleanRing
import Mathlib.Algebra.Group.Subgroup.Lattice
import Mathlib.GroupTheory.Perm.Support
import Mathlib.Data.Set.Card

namespace OCKIndividuationMSpaceComposition

universe uIndex uCarrier

namespace PrimitiveDistinction

/-!
# Where independent Boolean directions come from

A primitive distinction produces one local transposition.  Several such
transpositions do not automatically form independent directions: overlapping
transpositions can fail to commute.  This file gives a positive intrinsic
construction for a finite family whose endpoint supports are pairwise
disjoint.

For such a family, every Boolean mask determines the product of exactly the
selected local transpositions.  The resulting permutation representation is
faithful: a selected coordinate can be detected at its own first endpoint.
Consequently the externally presented Boolean cube used by the finite-rank
realization is not needed to obtain the Boolean transformation algebra.

The theorem deliberately stops before identifying disjointness as necessary.
Other compatible families may exist.  What is proved here is the exact
sufficient origin chain

`disjoint primitive distinctions -> commuting local reversals -> faithful
Boolean masks -> independent generated directions`.
-/

/-- A finite family of primitive distinctions whose displayed two-point
supports are pairwise disjoint.  No product carrier or coordinates are part of
the structure. -/
structure DisjointDistinctionFamily
    (Index : Type uIndex) (Carrier : Type uCarrier) where
  distinction : Index -> PrimitiveDistinction Carrier
  supportsDisjoint : Pairwise fun first second =>
    SupportsDisjoint (distinction first) (distinction second)

namespace DisjointDistinctionFamily

variable {Index : Type uIndex} {Carrier : Type uCarrier}

/-- Pairwise-disjoint primitive supports give disjoint permutation supports,
which is stronger than mere commutation. -/
theorem pairSwapEquiv_disjoint
    (family : DisjointDistinctionFamily Index Carrier)
    {first second : Index} (different : first ≠ second) :
    Equiv.Perm.Disjoint
      (pairSwapEquiv (family.distinction first))
      (pairSwapEquiv (family.distinction second)) := by
  intro point
  have disjoint := family.supportsDisjoint different
  by_cases pointFirst : point = (family.distinction first).first
  · right
    exact (family.distinction second).pairSwap_outside point
      (by simpa [pointFirst] using disjoint.1)
      (by simpa [pointFirst] using disjoint.2.1)
  · by_cases pointSecond : point = (family.distinction first).second
    · right
      exact (family.distinction second).pairSwap_outside point
        (by simpa [pointSecond] using disjoint.2.2.1)
        (by simpa [pointSecond] using disjoint.2.2.2)
    · left
      exact (family.distinction first).pairSwap_outside point
        pointFirst pointSecond

/-- Pairwise disjoint local reversals commute. -/
theorem pairSwapEquiv_commute
    (family : DisjointDistinctionFamily Index Carrier)
    {first second : Index} (different : first ≠ second) :
    Commute
      (pairSwapEquiv (family.distinction first))
      (pairSwapEquiv (family.distinction second)) :=
  (family.pairSwapEquiv_disjoint different).commute

variable [Fintype Index] [DecidableEq Index]
variable [Fintype Carrier] [DecidableEq Carrier]

/-! The involution law is needed by both the Boolean product and the later
singleton-generation boundary. -/

/-- Every primitive pair transposition is an involution in the ambient
permutation group. -/
theorem pairSwapEquiv_mul_self
    (distinction : PrimitiveDistinction Carrier) :
    (pairSwapEquiv distinction : Equiv.Perm Carrier) *
        pairSwapEquiv distinction = 1 := by
  ext point
  exact distinction.pairSwap_involutive point

/-! The endpoint witness used for faithfulness is independent of the chosen
finite family, so it is placed before both product presentations. -/

/-- A primitive pair swap moves its displayed first endpoint. -/
theorem first_mem_pairSwapEquiv_support
    (distinction : PrimitiveDistinction Carrier) :
    distinction.first ∈ Equiv.Perm.support
      (pairSwapEquiv distinction : Equiv.Perm Carrier) := by
  rw [Equiv.Perm.mem_support]
  simpa [pairSwapEquiv] using distinction.separated.symm

/-- An endpoint of one family member is fixed by every different family
member. -/
theorem pairSwapEquiv_fixes_other_first
    (family : DisjointDistinctionFamily Index Carrier)
    {first second : Index} (different : first ≠ second) :
    pairSwapEquiv (family.distinction second)
        (family.distinction first).first =
      (family.distinction first).first := by
  have disjoint := family.supportsDisjoint different
  exact (family.distinction second).pairSwap_outside _
    disjoint.1 disjoint.2.1

/-! ## The Boolean composition law -/

/-
The first version of this file used a filtered product only to exhibit the
finite image and its cardinality.  The following factorization makes the
algebraic operation explicit: an unselected coordinate contributes the group
unit, while a selected coordinate contributes its local pair swap.  This is
still derived from the family, not carried as an additional product action.
-/

/-- The local permutation factor contributed by one Boolean coordinate. -/
noncomputable def maskFactor
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index -> Bool) (index : Index) : Equiv.Perm Carrier :=
  if mask index = true then
    pairSwapEquiv (family.distinction index)
  else 1

/-- Distinct mask factors have disjoint supports, including identity factors. -/
theorem maskFactor_pairwise_disjoint
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index -> Bool) :
    ((Finset.univ : Finset Index) : Set Index).Pairwise
      (fun first second =>
        Equiv.Perm.Disjoint (maskFactor family mask first)
          (maskFactor family mask second)) := by
  intro first firstMember second secondMember different
  by_cases firstSelected : mask first = true
  · by_cases secondSelected : mask second = true
    · simpa [maskFactor, firstSelected, secondSelected] using
        family.pairSwapEquiv_disjoint different
    · simp [maskFactor, firstSelected, secondSelected]
  · by_cases secondSelected : mask second = true
    · simp [maskFactor, firstSelected, secondSelected]
    · simp [maskFactor, firstSelected, secondSelected]

/-- Distinct mask factors commute, as required by the unordered finite product. -/
theorem maskFactor_pairwise_commute
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index -> Bool) :
    ((Finset.univ : Finset Index) : Set Index).Pairwise
      (fun first second =>
        Commute (maskFactor family mask first) (maskFactor family mask second)) := by
  intro first firstMember second secondMember different
  by_cases firstSelected : mask first = true
  · by_cases secondSelected : mask second = true
    · simpa [maskFactor, firstSelected, secondSelected] using
        family.pairSwapEquiv_commute different
    · simp [maskFactor, firstSelected, secondSelected]
  · by_cases secondSelected : mask second = true
    · simp [maskFactor, firstSelected, secondSelected]
    · simp [maskFactor, firstSelected, secondSelected]

/-- The canonical unfiltered product of the factors selected by a mask. -/
noncomputable def maskPermutationProduct
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index -> Bool) : Equiv.Perm Carrier :=
  (Finset.univ : Finset Index).noncommProd
    (maskFactor family mask)
    (family.maskFactor_pairwise_commute mask)

/-- The unfiltered product has exactly the union of the supports of its
non-identity factors.  This is the support form of the Boolean product and
is the bridge to coordinate faithfulness. -/
theorem support_maskPermutationProduct
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index -> Bool) :
    (family.maskPermutationProduct mask).support =
      (Finset.univ : Finset Index).biUnion fun index =>
        (maskFactor family mask index).support := by
  unfold maskPermutationProduct
  apply Equiv.Perm.support_noncommProd
  exact family.maskFactor_pairwise_disjoint mask

/-- The all-false mask is the identity transformation. -/
theorem maskPermutationProduct_false
    (family : DisjointDistinctionFamily Index Carrier) :
    family.maskPermutationProduct (fun _ => false) = 1 := by
  classical
  unfold maskPermutationProduct
  rw [Finset.noncommProd_eq_pow_card _ _ _ 1]
  · simp
  · intro index _
    simp [maskFactor]

theorem maskPermutationProduct_pairwise_cross_commute
    (family : DisjointDistinctionFamily Index Carrier)
    (first second : Index -> Bool) :
    ((Finset.univ : Finset Index) : Set Index).Pairwise
      (fun left right =>
        Commute (maskFactor family second left)
          (maskFactor family first right)) := by
  intro left leftMember right rightMember different
  by_cases leftSelected : second left = true
  · by_cases rightSelected : first right = true
    · simpa [maskFactor, leftSelected, rightSelected] using
        family.pairSwapEquiv_commute different
    · simp [maskFactor, leftSelected, rightSelected]
  · by_cases rightSelected : first right = true
    · simp [maskFactor, leftSelected, rightSelected]
    · simp [maskFactor, leftSelected, rightSelected]

/-
The product law is the exact finite Boolean law.  At a coordinate the four
truth-table cases are: `1*1=1`, `swap*1=swap`, `1*swap=swap`, and
`swap*swap=1`.  The first three use only group identities; the last uses the
derived involution theorem for the corresponding primitive distinction.
-/
theorem maskPermutationProduct_mul_xor
    (family : DisjointDistinctionFamily Index Carrier)
    (first second : Index -> Bool) :
    family.maskPermutationProduct first *
        family.maskPermutationProduct second =
      family.maskPermutationProduct (fun index =>
        Bool.xor (first index) (second index)) := by
  let cross := family.maskPermutationProduct_pairwise_cross_commute first second
  calc
    family.maskPermutationProduct first *
          family.maskPermutationProduct second =
        (Finset.univ : Finset Index).noncommProd
          (maskFactor family first * maskFactor family second)
          (Finset.noncommProd_mul_distrib_aux
            (family.maskFactor_pairwise_commute first)
            (family.maskFactor_pairwise_commute second) cross) := by
      symm
      exact Finset.noncommProd_mul_distrib
        (maskFactor family first) (maskFactor family second)
        (family.maskFactor_pairwise_commute first)
        (family.maskFactor_pairwise_commute second) cross
    _ = family.maskPermutationProduct (fun index =>
          Bool.xor (first index) (second index)) := by
      apply Finset.noncommProd_congr rfl
      intro index _
      by_cases firstSelected : first index = true
      · by_cases secondSelected : second index = true
        · simp [maskFactor, Bool.xor, firstSelected, secondSelected,
            pairSwapEquiv_mul_self]
        · simp [maskFactor, firstSelected, secondSelected]
      · by_cases secondSelected : second index = true
        · simp [maskFactor, firstSelected, secondSelected]
        · simp [maskFactor, firstSelected, secondSelected]

/-- Membership of a family member's first endpoint in the aggregate support
detects exactly the corresponding Boolean coordinate, even in the unfiltered
product presentation. -/
theorem first_mem_support_maskPermutationProduct_iff
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index -> Bool) (index : Index) :
    (family.distinction index).first ∈
        (family.maskPermutationProduct mask).support ↔
      mask index = true := by
  classical
  rw [family.support_maskPermutationProduct mask]
  constructor
  · intro member
    rcases Finset.mem_biUnion.mp member with
      ⟨other, _, endpointMoved⟩
    by_cases same : other = index
    · subst other
      by_cases selected : mask index = true
      · exact selected
      · have impossible : False := by
          simpa [maskFactor, selected] using endpointMoved
        exact impossible.elim
    · by_cases selected : mask other = true
      · have moved : (family.distinction index).first ∈
            Equiv.Perm.support
              (pairSwapEquiv (family.distinction other) : Equiv.Perm Carrier) := by
          simpa [maskFactor, selected] using endpointMoved
        have fixed := family.pairSwapEquiv_fixes_other_first (Ne.symm same)
        exact False.elim ((Equiv.Perm.mem_support.mp moved) fixed)
      · have impossible : False := by
          simpa [maskFactor, selected] using endpointMoved
        exact impossible.elim
  · intro selected
    apply Finset.mem_biUnion.mpr
    refine ⟨index, Finset.mem_univ _, ?_⟩
    simpa [maskFactor, selected] using
      first_mem_pairSwapEquiv_support (family.distinction index)

/-! ## Faithfulness and finite size of the product presentation -/

/-- Distinct Boolean masks induce distinct ambient transformations in the
unfiltered product presentation. -/
theorem maskPermutationProduct_injective
    (family : DisjointDistinctionFamily Index Carrier) :
    Function.Injective family.maskPermutationProduct := by
  intro first second equal
  funext index
  apply Bool.eq_iff_iff.mpr
  constructor <;> intro selected
  · have moved :=
      (family.first_mem_support_maskPermutationProduct_iff first index).2 selected
    have supportEqual := congrArg Equiv.Perm.support equal
    rw [supportEqual] at moved
    exact (family.first_mem_support_maskPermutationProduct_iff second index).1 moved
  · have moved :=
      (family.first_mem_support_maskPermutationProduct_iff second index).2 selected
    have supportEqual := congrArg Equiv.Perm.support equal
    rw [← supportEqual] at moved
    exact (family.first_mem_support_maskPermutationProduct_iff first index).1 moved

/-! ## Canonical algebraic packaging -/

/-- The Boolean product is a genuine monoid homomorphism from pointwise
Boolean masks (viewed multiplicatively) into ambient permutations.  The
homomorphism is derived from the finite product law above; no group action or
coordinate product is supplied as an additional premise. -/
noncomputable def maskPermutationProductHom
    (family : DisjointDistinctionFamily Index Carrier) :
    Multiplicative (Index → Bool) →* Equiv.Perm Carrier where
  toFun := fun token => family.maskPermutationProduct
    (Multiplicative.toAdd token)
  map_one' := by
    change family.maskPermutationProduct (fun _ => false) = 1
    exact family.maskPermutationProduct_false
  map_mul' := by
    intro first second
    have law := maskPermutationProduct_mul_xor family
      (Multiplicative.toAdd first) (Multiplicative.toAdd second)
    change family.maskPermutationProduct
          (Multiplicative.toAdd (first * second)) =
      family.maskPermutationProduct (Multiplicative.toAdd first) *
        family.maskPermutationProduct (Multiplicative.toAdd second)
    rw [law]
    apply congrArg family.maskPermutationProduct
    funext index
    change (first * second).toAdd index =
      Bool.xor (first.toAdd index) (second.toAdd index)
    rfl
@[simp] theorem maskPermutationProductHom_apply
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index → Bool) :
    family.maskPermutationProductHom (Multiplicative.ofAdd mask) =
      family.maskPermutationProduct mask := by
  rfl

theorem maskPermutationProductHom_injective
    (family : DisjointDistinctionFamily Index Carrier) :
    Function.Injective family.maskPermutationProductHom := by
  intro first second equal
  apply Multiplicative.toAdd.injective
  change family.maskPermutationProduct (Multiplicative.toAdd first) =
      family.maskPermutationProduct (Multiplicative.toAdd second) at equal
  exact family.maskPermutationProduct_injective equal

/-- The product presentation therefore realizes exactly `2^n` distinct
transformations, with no external Boolean cube supplied as an assumption. -/
theorem card_maskPermutationProduct_range
    (family : DisjointDistinctionFamily Index Carrier) :
    Set.ncard (Set.range family.maskPermutationProduct) =
      2 ^ Fintype.card Index := by
  classical
  rw [Set.ncard_range_of_injective family.maskPermutationProduct_injective]
  simp [Nat.card_eq_fintype_card]

/-- Coordinates selected by a Boolean mask. -/
def selectedIndices (mask : Index -> Bool) : Finset Index :=
  Finset.univ.filter fun index => mask index = true

/-- The simultaneous transformation selected by a Boolean mask.  The product
is order-independent because the local transpositions commute. -/
noncomputable def maskPermutation
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index -> Bool) : Equiv.Perm Carrier :=
  (selectedIndices mask).noncommProd
    (fun index => pairSwapEquiv (family.distinction index))
    (by
      intro first _ second _ different
      exact family.pairSwapEquiv_commute different)

/-- The filtered presentation is exactly the unfiltered factor product.

The unfiltered action contributes the identity at every coordinate whose mask
bit is false.  Splitting `univ` into the selected coordinates and its
complement therefore yields the same permutation as the filtered
`maskPermutation` presentation.  This theorem is a consistency bridge
between the two APIs; it does not introduce a second action or a new
independence premise.
-/
theorem maskPermutationProduct_eq_maskPermutation
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index -> Bool) :
    family.maskPermutationProduct mask = family.maskPermutation mask := by
  classical
  unfold maskPermutationProduct maskPermutation
  let selected : Finset Index := selectedIndices mask
  let unselected : Finset Index := (Finset.univ : Finset Index) \ selected
  have h_union : selected ∪ unselected = (Finset.univ : Finset Index) := by
    ext index
    simp [selected, unselected]
  have h_disjoint : Disjoint selected unselected := by
    exact Finset.disjoint_sdiff
  have h_comm : ((selected ∪ unselected : Finset Index) : Set Index).Pairwise
      (fun first second =>
        Commute (maskFactor family mask first) (maskFactor family mask second)) := by
    rw [h_union]
    exact family.maskFactor_pairwise_commute mask
  have h_split := Finset.noncommProd_union_of_disjoint
    h_disjoint (maskFactor family mask) h_comm
  have h_split_univ :
      (Finset.univ : Finset Index).noncommProd (maskFactor family mask)
          (family.maskFactor_pairwise_commute mask) =
        selected.noncommProd (maskFactor family mask)
            (h_comm.mono <| Finset.coe_subset.2 Finset.subset_union_left) *
          unselected.noncommProd (maskFactor family mask)
            (h_comm.mono <| Finset.coe_subset.2 Finset.subset_union_right) := by
    simpa only [h_union] using h_split
  rw [h_split_univ]
  have h_selected :
      (selected : Finset Index).noncommProd (maskFactor family mask)
          (h_comm.mono <| Finset.coe_subset.2 Finset.subset_union_left) =
        selected.noncommProd
          (fun index => pairSwapEquiv (family.distinction index)) (by
            intro first _ second _ different
            exact family.pairSwapEquiv_commute different) := by
    apply Finset.noncommProd_congr rfl
    intro index hindex
    exact if_pos (Finset.mem_filter.mp hindex).2
  have h_unselected :
      unselected.noncommProd (maskFactor family mask)
          (h_comm.mono <| Finset.coe_subset.2 Finset.subset_union_right) = 1 := by
    let h_unselected_comm :=
      h_comm.mono <| Finset.coe_subset.2 Finset.subset_union_right
    calc
      unselected.noncommProd (maskFactor family mask) h_unselected_comm =
          (1 : Equiv.Perm Carrier) ^ unselected.card := by
        apply Finset.noncommProd_eq_pow_card unselected
          (maskFactor family mask) h_unselected_comm 1
        intro index hindex
        have hindex' : index ∈
            (Finset.univ : Finset Index) \ selected := by
          simpa [unselected] using hindex
        have not_selected : index ∉ selected :=
          (Finset.mem_sdiff.mp hindex').2
        have mask_not : ¬ mask index = true := by
          intro selectedValue
          exact not_selected (Finset.mem_filter.mpr
            ⟨Finset.mem_univ _, selectedValue⟩)
        simp [maskFactor, mask_not]
      _ = 1 := one_pow _
  rw [h_selected, h_unselected, mul_one]

/-- The support of a simultaneous mask action is exactly the union of the
supports of its selected local swaps. -/
theorem support_maskPermutation
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index -> Bool) :
    (family.maskPermutation mask).support =
      (selectedIndices mask).biUnion fun index =>
        Equiv.Perm.support
          (pairSwapEquiv (family.distinction index) : Equiv.Perm Carrier) := by
  apply Equiv.Perm.support_noncommProd
  intro first _ second _ different
  exact family.pairSwapEquiv_disjoint different

/-! ## Genuine multi-source generation

The next lemmas establish the smallest nontrivial native generation example.
The product of two independent local reversals belongs to the subgroup
generated by the pair, but belongs to neither singleton-generated subgroup.
Thus joint generation is not an equivalence relation or a renamed unary
dependency.
-/

/-- A singleton-generated subgroup of an involution contains only the
identity and that involution. No commutativity of the ambient group is used. -/
theorem closure_singleton_involution_cases
    {GroupCarrier : Type*} [Group GroupCarrier]
    (generator element : GroupCarrier)
    (involutive : generator * generator = 1)
    (generated : element ∈ Subgroup.closure ({generator} : Set GroupCarrier)) :
    element = 1 ∨ element = generator := by
  have inverseGenerator : generator⁻¹ = generator := by
    calc
      generator⁻¹ = generator⁻¹ * 1 := (mul_one _).symm
      _ = generator⁻¹ * (generator * generator) := by rw [involutive]
      _ = (generator⁻¹ * generator) * generator := by rw [mul_assoc]
      _ = generator := by simp
  induction generated using Subgroup.closure_induction with
  | mem current currentMember =>
      right
      simpa using currentMember
  | one => exact Or.inl rfl
  | mul first second _ _ firstCases secondCases =>
      rcases firstCases with firstOne | firstGenerator <;>
        rcases secondCases with secondOne | secondGenerator
      · left; simp [firstOne, secondOne]
      · right; simp [firstOne, secondGenerator]
      · right; simp [firstGenerator, secondOne]
      · left; simp [firstGenerator, secondGenerator, involutive]
  | inv current _ currentCases =>
      rcases currentCases with currentOne | currentGenerator
      · left; simp [currentOne]
      · right; simpa [currentGenerator, inverseGenerator]

/-- The product of two local reversals is generated jointly by them. -/
theorem twoSwapComposite_mem_pair_closure
    (family : DisjointDistinctionFamily Index Carrier)
    (first second : Index) :
    pairSwapEquiv (family.distinction first) *
        pairSwapEquiv (family.distinction second) ∈
      Subgroup.closure
        ({pairSwapEquiv (family.distinction first),
          pairSwapEquiv (family.distinction second)} :
          Set (Equiv.Perm Carrier)) := by
  exact Subgroup.mul_mem _
    (Subgroup.subset_closure (by simp))
    (Subgroup.subset_closure (by simp))

/-- The product of two disjoint nontrivial local reversals is not generated by
the first reversal alone. -/
theorem twoSwapComposite_not_mem_first_closure
    (family : DisjointDistinctionFamily Index Carrier)
    {first second : Index} (different : first ≠ second) :
    pairSwapEquiv (family.distinction first) *
        pairSwapEquiv (family.distinction second) ∉
      Subgroup.closure
        ({pairSwapEquiv (family.distinction first)} :
          Set (Equiv.Perm Carrier)) := by
  intro generated
  rcases closure_singleton_involution_cases
      (pairSwapEquiv (family.distinction first) : Equiv.Perm Carrier)
      (pairSwapEquiv (family.distinction first) *
        pairSwapEquiv (family.distinction second) : Equiv.Perm Carrier)
      (pairSwapEquiv_mul_self (family.distinction first)) generated with
    compositeOne | compositeFirst
  · have atSecond := congrArg
      (fun permutation : Equiv.Perm Carrier =>
        permutation (family.distinction second).first) compositeOne
    have disjoint := family.supportsDisjoint different
    have firstFixesSecondEndpoint :
        (family.distinction first).pairSwap
            (family.distinction second).second =
          (family.distinction second).second :=
      (family.distinction first).pairSwap_outside _
        (Ne.symm disjoint.2.1) (Ne.symm disjoint.2.2.2)
    change (family.distinction first).pairSwap
        ((family.distinction second).pairSwap
          (family.distinction second).first) =
      (family.distinction second).first at atSecond
    rw [(family.distinction second).pairSwap_first,
      firstFixesSecondEndpoint] at atSecond
    have moved : (family.distinction second).second =
        (family.distinction second).first := atSecond
    exact (family.distinction second).separated moved.symm
  · have cancelled :
      (pairSwapEquiv (family.distinction second) : Equiv.Perm Carrier) = 1 := by
      have cancellation := congrArg
        (fun permutation : Equiv.Perm Carrier =>
          (pairSwapEquiv (family.distinction first) : Equiv.Perm Carrier)⁻¹ *
            permutation) compositeFirst
      simpa [mul_assoc] using cancellation
    have atSecond := congrArg
      (fun permutation : Equiv.Perm Carrier =>
        permutation (family.distinction second).first) cancelled
    change (family.distinction second).pairSwap
        (family.distinction second).first =
      (family.distinction second).first at atSecond
    rw [(family.distinction second).pairSwap_first] at atSecond
    have moved : (family.distinction second).second =
        (family.distinction second).first := atSecond
    exact (family.distinction second).separated moved.symm

/-- Symmetrically, the joint composite is not generated by the second
reversal alone. -/
theorem twoSwapComposite_not_mem_second_closure
    (family : DisjointDistinctionFamily Index Carrier)
    {first second : Index} (different : first ≠ second) :
    pairSwapEquiv (family.distinction first) *
        pairSwapEquiv (family.distinction second) ∉
      Subgroup.closure
        ({pairSwapEquiv (family.distinction second)} :
          Set (Equiv.Perm Carrier)) := by
  have commute := family.pairSwapEquiv_commute different
  rw [commute.eq]
  exact family.twoSwapComposite_not_mem_first_closure (Ne.symm different)

/-- Membership of one first endpoint in the aggregate support detects exactly
the corresponding Boolean coordinate. -/
theorem first_mem_support_maskPermutation_iff
    (family : DisjointDistinctionFamily Index Carrier)
    (mask : Index -> Bool) (index : Index) :
    (family.distinction index).first ∈
        (family.maskPermutation mask).support ↔
      mask index = true := by
  classical
  rw [family.support_maskPermutation mask]
  constructor
  · intro member
    rcases Finset.mem_biUnion.mp member with
      ⟨first, firstSelected, endpointMoved⟩
    have selectedValue : mask first = true :=
      (Finset.mem_filter.mp firstSelected).2
    by_cases same : first = index
    · simpa [same] using selectedValue
    · have fixed := family.pairSwapEquiv_fixes_other_first (Ne.symm same)
      exact False.elim ((Equiv.Perm.mem_support.mp endpointMoved) fixed)
  · intro selected
    apply Finset.mem_biUnion.mpr
    refine ⟨index, ?_, first_mem_pairSwapEquiv_support _⟩
    exact Finset.mem_filter.mpr ⟨Finset.mem_univ _, selected⟩

/-- Distinct Boolean masks induce distinct ambient transformations.  This is
the faithful emergence theorem: no independent coordinate action was assumed. -/
theorem maskPermutation_injective
    (family : DisjointDistinctionFamily Index Carrier) :
    Function.Injective family.maskPermutation := by
  intro first second equal
  funext index
  apply Bool.eq_iff_iff.mpr
  constructor <;> intro selected
  · have moved :=
      (family.first_mem_support_maskPermutation_iff first index).2 selected
    have supportEqual := congrArg Equiv.Perm.support equal
    rw [supportEqual] at moved
    exact (family.first_mem_support_maskPermutation_iff second index).1 moved
  · have moved :=
      (family.first_mem_support_maskPermutation_iff second index).2 selected
    have supportEqual := congrArg Equiv.Perm.support equal
    rw [← supportEqual] at moved
    exact (family.first_mem_support_maskPermutation_iff first index).1 moved

/-- The family therefore realizes exactly `2^n` distinct admissible composite
reversals, where `n` is the number of primitive distinctions. -/
theorem card_maskPermutation_range
    (family : DisjointDistinctionFamily Index Carrier) :
    Set.ncard (Set.range family.maskPermutation) =
      2 ^ Fintype.card Index := by
  classical
  rw [Set.ncard_range_of_injective family.maskPermutation_injective]
  simp [Nat.card_eq_fintype_card]

end DisjointDistinctionFamily

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
