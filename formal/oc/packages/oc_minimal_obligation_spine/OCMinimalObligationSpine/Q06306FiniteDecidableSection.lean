import Mathlib.Data.List.Basic

/-!
OC Core 1.4, Q063_Q006: an executable finite/decidable section theorem.

The source question is AIM's 2013 Computable Stability Theory problem-session
Question 6: for a stable theory and `M ≺ N`, is the section
`S₁(M) → S₁(N)` selecting the unique nonforking extension computable?

This file does not claim to settle that unrestricted question.  It proves the
precise finite-search fragment: once source and target types have effective
codes, the target search space is finite, restriction and nonforking are
decidable, and a unique represented nonforking extension exists for every
source code, exhaustive search is an executable total section.  Thus the
remaining general gap is not classical existence/uniqueness; it is the
effective representation and effective recognition/bounding needed to supply
these hypotheses.
-/

namespace OCMinimalObligationSpine

/-- Effective data sufficient for a finite exhaustive nonforking-section search. -/
structure Q06306FiniteDecidableSectionData : Type 1 where
  SourceCode : Type
  TargetCode : Type
  sourceCodeDecidableEq : DecidableEq SourceCode
  targetCandidates : List TargetCode
  representedTarget : TargetCode → Bool
  restriction : TargetCode → SourceCode
  nonforking : TargetCode → Bool
  uniqueRepresentedNonforkingExtension :
    ∀ p : SourceCode, ∃! q : TargetCode,
      q ∈ targetCandidates ∧
        representedTarget q = true ∧
        restriction q = p ∧
        nonforking q = true

/-- The fully decidable predicate searched by the executable section. -/
def q06306FiniteCandidateQualifies
    (data : Q06306FiniteDecidableSectionData)
    (p : data.SourceCode)
    (q : data.TargetCode) : Bool :=
  letI : DecidableEq data.SourceCode := data.sourceCodeDecidableEq
  data.representedTarget q &&
    decide (data.restriction q = p) &&
    data.nonforking q

theorem q06306_finite_candidate_qualifies_iff
    (data : Q06306FiniteDecidableSectionData)
    (p : data.SourceCode)
    (q : data.TargetCode) :
    q06306FiniteCandidateQualifies data p q = true ↔
      data.representedTarget q = true ∧
        data.restriction q = p ∧
        data.nonforking q = true := by
  letI : DecidableEq data.SourceCode := data.sourceCodeDecidableEq
  simp [q06306FiniteCandidateQualifies, and_assoc]

/--
Executable finite search.  `List.find?` inspects the declared target codes in
order and uses only the supplied Boolean tests and decidable code equality.
-/
def q06306FiniteSection?
    (data : Q06306FiniteDecidableSectionData)
    (p : data.SourceCode) : Option data.TargetCode :=
  data.targetCandidates.find? (q06306FiniteCandidateQualifies data p)

theorem q06306_finite_section_search_sound
    (data : Q06306FiniteDecidableSectionData)
    (p : data.SourceCode)
    (q : data.TargetCode)
    (h : q06306FiniteSection? data p = some q) :
    q ∈ data.targetCandidates ∧
      data.representedTarget q = true ∧
      data.restriction q = p ∧
      data.nonforking q = true := by
  have hmem :
      q ∈ data.targetCandidates :=
    List.mem_of_find?_eq_some h
  have hqual :
      q06306FiniteCandidateQualifies data p q = true :=
    List.find?_some h
  exact ⟨hmem, (q06306_finite_candidate_qualifies_iff data p q).mp hqual⟩

theorem q06306_finite_section_search_total
    (data : Q06306FiniteDecidableSectionData)
    (p : data.SourceCode) :
    ∃ q : data.TargetCode, q06306FiniteSection? data p = some q := by
  obtain ⟨q, hq, _⟩ := data.uniqueRepresentedNonforkingExtension p
  by_cases hsearch : q06306FiniteSection? data p = none
  · have hnone :
        ∀ r : data.TargetCode,
          r ∈ data.targetCandidates →
            ¬q06306FiniteCandidateQualifies data p r = true :=
      (List.find?_eq_none.mp hsearch)
    have hqual :
        q06306FiniteCandidateQualifies data p q = true :=
      (q06306_finite_candidate_qualifies_iff data p q).mpr hq.2
    exact False.elim ((hnone q hq.1) hqual)
  · cases hresult : q06306FiniteSection? data p with
    | none => exact False.elim (hsearch hresult)
    | some r => exact ⟨r, rfl⟩

theorem q06306_finite_section_search_isSome
    (data : Q06306FiniteDecidableSectionData)
    (p : data.SourceCode) :
    (q06306FiniteSection? data p).isSome = true := by
  exact Option.isSome_iff_exists.mpr
    (q06306_finite_section_search_total data p)

/--
The total executable section obtained from the proved-total finite search.
The proof argument to `Option.get` is erased; the returned code is computed by
`q06306FiniteSection?`.
-/
def q06306FiniteSection
    (data : Q06306FiniteDecidableSectionData)
    (p : data.SourceCode) : data.TargetCode :=
  (q06306FiniteSection? data p).get
    (q06306_finite_section_search_isSome data p)

theorem q06306_finite_section_spec
    (data : Q06306FiniteDecidableSectionData)
    (p : data.SourceCode) :
    q06306FiniteSection data p ∈ data.targetCandidates ∧
      data.representedTarget (q06306FiniteSection data p) = true ∧
      data.restriction (q06306FiniteSection data p) = p ∧
      data.nonforking (q06306FiniteSection data p) = true := by
  have hsome :
      q06306FiniteSection? data p =
        some (q06306FiniteSection data p) :=
    (Option.some_get (q06306_finite_section_search_isSome data p)).symm
  exact q06306_finite_section_search_sound data p
    (q06306FiniteSection data p) hsome

theorem q06306_finite_section_is_unique
    (data : Q06306FiniteDecidableSectionData)
    (p : data.SourceCode)
    (q : data.TargetCode)
    (hq :
      q ∈ data.targetCandidates ∧
        data.representedTarget q = true ∧
        data.restriction q = p ∧
        data.nonforking q = true) :
    q06306FiniteSection data p = q := by
  obtain ⟨w, hw, hunique⟩ :=
    data.uniqueRepresentedNonforkingExtension p
  have hsection :
      q06306FiniteSection data p = w :=
    hunique (q06306FiniteSection data p)
      (q06306_finite_section_spec data p)
  have hqeq :
      q = w :=
    hunique q hq
  exact hsection.trans hqeq.symm

/--
Source-faithful finite/decidable positive result: the computed map is a
right-inverse of restriction and selects exactly the unique represented
nonforking target code.
-/
theorem q06306_finite_decidable_unique_extensions_admit_executable_section
    (data : Q06306FiniteDecidableSectionData) :
    ∀ p : data.SourceCode,
      data.restriction (q06306FiniteSection data p) = p ∧
        data.representedTarget (q06306FiniteSection data p) = true ∧
        data.nonforking (q06306FiniteSection data p) = true := by
  intro p
  have h := q06306_finite_section_spec data p
  exact ⟨h.2.2.1, h.2.1, h.2.2.2⟩

end OCMinimalObligationSpine
