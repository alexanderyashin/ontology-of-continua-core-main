import OCKIndividuationMSpaceComposition.SymmetryRestrictedNaturalityClass

namespace OCKIndividuationMSpaceComposition

universe uCarrier

/-!
# The two-valued orientation quotient of the support stabilizer

For a primitive distinction, the support-preserving relabellings form the
exact naturality class from M46.  This layer packages that class as a subtype
and extracts only the endpoint orientation: `false` means the displayed
endpoints are fixed and `true` means they are exchanged.  The orientation
coordinate composes by Boolean xor, is unchanged by inverse, and realizes both
values.  It is therefore a genuine two-element quotient signal, while the
complement action remains deliberately unrecorded.
-/

namespace PrimitiveDistinction

variable {Carrier : Type uCarrier}

/-- A carrier equivalence together with the explicit proof that it preserves
the unordered support of a primitive distinction. -/
def SupportRelabelling (distinction : PrimitiveDistinction Carrier) :=
  {relabel : Carrier ≃ Carrier // PreservesPairSupport distinction relabel}

/-- Composition in the support-preserving relabelling class. -/
def SupportRelabelling.trans
    (distinction : PrimitiveDistinction Carrier)
    (left right : SupportRelabelling distinction) :
    SupportRelabelling distinction :=
  ⟨left.1.trans right.1,
    preservesPairSupport_trans distinction left.1 right.1 left.2 right.2⟩

/-- Inverse in the support-preserving relabelling class. -/
def SupportRelabelling.symm
    (distinction : PrimitiveDistinction Carrier)
    (relabel : SupportRelabelling distinction) :
    SupportRelabelling distinction :=
  ⟨relabel.1.symm, preservesPairSupport_symm distinction relabel.1 relabel.2⟩

/-- Identity in the support-preserving relabelling class. -/
def SupportRelabelling.identity
    (distinction : PrimitiveDistinction Carrier) :
    SupportRelabelling distinction :=
  ⟨Equiv.refl Carrier, preservesPairSupport_refl distinction⟩

/-- The endpoint-orientation quotient: `false` for fixed endpoints and
`true` for exchanged endpoints. -/
noncomputable def supportOrientation
    (distinction : PrimitiveDistinction Carrier)
    (relabel : SupportRelabelling distinction) : Bool :=
  by
    classical
    exact if relabel.1 distinction.first = distinction.first then false else true

theorem supportOrientation_eq_false_of_fixed
    (distinction : PrimitiveDistinction Carrier)
    (relabel : SupportRelabelling distinction)
    (fixed : relabel.1 distinction.first = distinction.first) :
    supportOrientation distinction relabel = false := by
  classical
  simp [supportOrientation, fixed]

theorem supportOrientation_eq_true_of_swapped
    (distinction : PrimitiveDistinction Carrier)
    (relabel : SupportRelabelling distinction)
    (swapped : relabel.1 distinction.first = distinction.second) :
    supportOrientation distinction relabel = true := by
  classical
  simp [supportOrientation, swapped, Ne.symm distinction.separated]

theorem supportOrientation_eq_false_iff_fixed
    (distinction : PrimitiveDistinction Carrier)
    (relabel : SupportRelabelling distinction) :
    supportOrientation distinction relabel = false ↔
      (relabel.1 distinction.first = distinction.first ∧
        relabel.1 distinction.second = distinction.second) := by
  classical
  constructor
  · intro orientation
    have firstFixed : relabel.1 distinction.first = distinction.first := by
      by_contra firstNotFixed
      simp [supportOrientation, firstNotFixed] at orientation
    rcases relabel.2 with fixed | swapped
    · exact ⟨firstFixed, fixed.2⟩
    · exfalso
      apply distinction.separated
      exact firstFixed.symm.trans swapped.1
  · rintro ⟨firstFixed, _⟩
    exact supportOrientation_eq_false_of_fixed distinction relabel firstFixed

theorem supportOrientation_eq_true_iff_swapped
    (distinction : PrimitiveDistinction Carrier)
    (relabel : SupportRelabelling distinction) :
    supportOrientation distinction relabel = true ↔
      (relabel.1 distinction.first = distinction.second ∧
        relabel.1 distinction.second = distinction.first) := by
  classical
  constructor
  · intro orientation
    have firstNotFixed : relabel.1 distinction.first ≠ distinction.first := by
      intro firstFixed
      have : supportOrientation distinction relabel = false :=
        supportOrientation_eq_false_of_fixed distinction relabel firstFixed
      exact Bool.noConfusion (orientation ▸ this)
    rcases relabel.2 with fixed | swapped
    · exfalso
      exact firstNotFixed fixed.1
    · exact swapped
  · rintro ⟨firstSwapped, _⟩
    exact supportOrientation_eq_true_of_swapped distinction relabel firstSwapped

theorem supportOrientation_trans
    (distinction : PrimitiveDistinction Carrier)
    (left right : SupportRelabelling distinction) :
    supportOrientation distinction (SupportRelabelling.trans distinction left right) =
      Bool.xor (supportOrientation distinction left)
        (supportOrientation distinction right) := by
  classical
  rcases left.2 with leftFixed | leftSwapped
  · rcases right.2 with rightFixed | rightSwapped
    · have compFirst :
          (SupportRelabelling.trans distinction left right).1 distinction.first =
            distinction.first := by
          simp [SupportRelabelling.trans, Equiv.trans_apply, leftFixed.1,
            rightFixed.1]
      rw [supportOrientation_eq_false_of_fixed distinction
            (SupportRelabelling.trans distinction left right) compFirst,
        supportOrientation_eq_false_of_fixed distinction left leftFixed.1,
        supportOrientation_eq_false_of_fixed distinction right rightFixed.1]
      rfl
    · have compFirst :
          (SupportRelabelling.trans distinction left right).1 distinction.first =
            distinction.second := by
          simp [SupportRelabelling.trans, Equiv.trans_apply, leftFixed.1,
            rightSwapped.1]
      rw [supportOrientation_eq_true_of_swapped distinction
            (SupportRelabelling.trans distinction left right) compFirst,
        supportOrientation_eq_false_of_fixed distinction left leftFixed.1,
        supportOrientation_eq_true_of_swapped distinction right rightSwapped.1]
      rfl
  · rcases right.2 with rightFixed | rightSwapped
    · have compFirst :
          (SupportRelabelling.trans distinction left right).1 distinction.first =
            distinction.second := by
          simp [SupportRelabelling.trans, Equiv.trans_apply, leftSwapped.1,
            rightFixed.2]
      rw [supportOrientation_eq_true_of_swapped distinction
            (SupportRelabelling.trans distinction left right) compFirst,
        supportOrientation_eq_true_of_swapped distinction left leftSwapped.1,
        supportOrientation_eq_false_of_fixed distinction right rightFixed.1]
      rfl
    · have compFirst :
          (SupportRelabelling.trans distinction left right).1 distinction.first =
            distinction.first := by
          simp [SupportRelabelling.trans, Equiv.trans_apply, leftSwapped.1,
            rightSwapped.2]
      rw [supportOrientation_eq_false_of_fixed distinction
            (SupportRelabelling.trans distinction left right) compFirst,
        supportOrientation_eq_true_of_swapped distinction left leftSwapped.1,
        supportOrientation_eq_true_of_swapped distinction right rightSwapped.1]
      rfl

theorem supportOrientation_symm
    (distinction : PrimitiveDistinction Carrier)
    (relabel : SupportRelabelling distinction) :
    supportOrientation distinction (SupportRelabelling.symm distinction relabel) =
      supportOrientation distinction relabel := by
  classical
  rcases relabel.2 with fixed | swapped
  · have symmFirst :
        (SupportRelabelling.symm distinction relabel).1 distinction.first =
          distinction.first := by
      change relabel.1.symm distinction.first = distinction.first
      calc
        relabel.1.symm distinction.first =
            relabel.1.symm (relabel.1 distinction.first) := by
              rw [fixed.1]
        _ = distinction.first := relabel.1.symm_apply_apply _
    rw [supportOrientation_eq_false_of_fixed distinction
          (SupportRelabelling.symm distinction relabel) symmFirst,
      supportOrientation_eq_false_of_fixed distinction relabel fixed.1]
  · have symmFirst :
        (SupportRelabelling.symm distinction relabel).1 distinction.first =
          distinction.second := by
      change relabel.1.symm distinction.first = distinction.second
      calc
        relabel.1.symm distinction.first =
            relabel.1.symm (relabel.1 distinction.second) := by
              rw [swapped.2]
        _ = distinction.second := relabel.1.symm_apply_apply _
    rw [supportOrientation_eq_true_of_swapped distinction
          (SupportRelabelling.symm distinction relabel) symmFirst,
      supportOrientation_eq_true_of_swapped distinction relabel swapped.1]

theorem supportOrientation_identity
    (distinction : PrimitiveDistinction Carrier) :
    supportOrientation distinction (SupportRelabelling.identity distinction) = false := by
  classical
  simp [supportOrientation, SupportRelabelling.identity]

/-- The primitive pair swap realizes the non-trivial orientation value. -/
theorem supportOrientation_pairSwap
    (distinction : PrimitiveDistinction Carrier) :
    supportOrientation distinction
        (⟨pairSwapEquiv distinction,
          Or.inr ⟨distinction.pairSwap_first, distinction.pairSwap_second⟩⟩ :
          SupportRelabelling distinction) = true := by
  classical
  change (if distinction.pairSwap distinction.first = distinction.first
    then false else true) = true
  rw [distinction.pairSwap_first]
  simp [Ne.symm distinction.separated]

theorem supportOrientation_surjective
    (distinction : PrimitiveDistinction Carrier) :
    Function.Surjective (@supportOrientation Carrier distinction) := by
  classical
  intro value
  cases value
  · exact ⟨SupportRelabelling.identity distinction, supportOrientation_identity distinction⟩
  · exact ⟨⟨pairSwapEquiv distinction,
      Or.inr ⟨distinction.pairSwap_first, distinction.pairSwap_second⟩⟩,
      supportOrientation_pairSwap distinction⟩

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
