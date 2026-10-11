import OCMinimalObligationSpine.OddExponentInvolutionCollapse

namespace OCMinimalObligationSpine

universe u

/-!
Q042/Q009 terminal gate for the all-elements exponent quotient frontier.

The source-faithful AIM Problem 3.6 target is existential: is there one
sufficiently large exponent `p` for which the all-elements `p`-power
normal-closure quotient of `Out(F_n)` is infinite?  The source does not assert
an eventual result for every exponent above a threshold.

Existing kernels in `OddExponentInvolutionCollapse` already prove many local
constraints.  This file adds the missing terminal wrapper: a positive answer
must provide an all-elements exponent target with infinite image/range; a
negative answer must obstruct every admitted exponent target.  Linear shadows,
selected-power quotients, SQ-universality shadows and partial periodic
quotients are not terminal unless they pass this wrapper.
-/

/--
One-exponent Q042 witness over an abstract source group `G`.

This is the source-faithful witness shape.  The separate eventual-tail target
below is retained as a strictly stronger diagnostic, not as a restatement of
AIM Problem 3.6.
-/
structure Q042AdmittedExponentTarget
    (G : Type u) [Group G] (admissibleExponent : ℕ → Prop) where
  H : Type u
  instH : Group H
  witness : @AllElementsExponentQuotientWitnessData G H _ instH
  admissible_exponent : admissibleExponent witness.p

/-- The preserved historical target: a witness at one admitted exponent. -/
def Q042SingleExponentPositiveTarget
    (G : Type u) [Group G] (admissibleExponent : ℕ → Prop) : Prop :=
  Nonempty (Q042AdmittedExponentTarget G admissibleExponent)

/--
A genuine all-elements exponent target at one explicitly fixed exponent `p`.
The equality prevents a witness at some other admitted exponent from being
silently reused for the quantified tail.
-/
structure Q042ExponentTargetAt
    (G : Type u) [Group G] (p : ℕ) where
  H : Type u
  instH : Group H
  witness : @AllElementsExponentQuotientWitnessData G H _ instH
  exact_exponent : witness.p = p

/--
Source-faithful formalization of AIM Problem 3.6 after the informal phrase
`p ≫ 0` has been exposed as an explicit predicate supplied by the caller.
Only one sufficiently large exponent witness is required.
-/
def Q042AIMProblem36PositiveTarget
    (G : Type u) [Group G] (sufficientlyLarge : ℕ → Prop) : Prop :=
  ∃ p : ℕ, sufficientlyLarge p ∧ Nonempty (Q042ExponentTargetAt G p)

/-- Convert one exact-`p` witness into the preserved historical intake shape. -/
def Q042ExponentTargetAt.toAdmittedExponentTarget
    {G : Type u} [Group G] {admissibleExponent : ℕ → Prop} {p : ℕ}
    (target : Q042ExponentTargetAt G p)
    (h_admissible : admissibleExponent p) :
    Q042AdmittedExponentTarget G admissibleExponent where
  H := target.H
  instH := target.instH
  witness := target.witness
  admissible_exponent := by
    rw [target.exact_exponent]
    exact h_admissible

/-- The declared exponent class must contain arbitrarily large exponents. -/
def Q042AdmissibleExponentsUnbounded
    (admissibleExponent : ℕ → Prop) : Prop :=
  ∀ lowerBound : ℕ, ∃ p : ℕ, lowerBound ≤ p ∧ admissibleExponent p

/--
The stronger eventual-tail Q042 target.

There is one threshold `P` such that every admitted exponent `p ≥ P` has a
genuine infinite-range all-elements exponent-`p` target.  Cofinality of the
admitted exponent class is included explicitly so an empty eventual tail
cannot satisfy the theorem vacuously.  This is useful as a stronger diagnostic,
but it is not the source-faithful AIM Problem 3.6 quantifier.
-/
def Q042FullPositiveTarget
    (G : Type u) [Group G] (admissibleExponent : ℕ → Prop) : Prop :=
  ∃ threshold : ℕ,
    Q042AdmissibleExponentsUnbounded admissibleExponent ∧
      ∀ p : ℕ, threshold ≤ p → admissibleExponent p →
        Nonempty (Q042ExponentTargetAt G p)

/-- Direct construction payload for the full eventual Q042 target. -/
structure Q042DirectPositiveConstruction
    (G : Type u) [Group G] (admissibleExponent : ℕ → Prop) where
  threshold : ℕ
  admissible_exponents_unbounded :
    Q042AdmissibleExponentsUnbounded admissibleExponent
  target_at :
    ∀ p : ℕ, threshold ≤ p → admissibleExponent p →
      Q042ExponentTargetAt G p

/-- A direct eventual construction closes the full positive target. -/
theorem q042_full_target_of_direct_positive_construction
    {G : Type u} [Group G] {admissibleExponent : ℕ → Prop}
    (C : Q042DirectPositiveConstruction G admissibleExponent) :
    Q042FullPositiveTarget G admissibleExponent := by
  exact ⟨C.threshold, C.admissible_exponents_unbounded,
    fun p h_threshold h_admissible =>
      ⟨C.target_at p h_threshold h_admissible⟩⟩

/--
Any full Q042 construction forces the exact all-power quotient to be infinite
at every admitted exponent beyond the same threshold.
-/
theorem q042_positive_construction_forces_eventual_all_power_quotient_infinite
    {G : Type u} [Group G] {admissibleExponent : ℕ → Prop}
    (C : Q042DirectPositiveConstruction G admissibleExponent) :
    ∃ threshold : ℕ,
      ∀ p : ℕ, threshold ≤ p → admissibleExponent p →
        ¬ Set.Finite
          (Set.univ : Set (G ⧸ allPowerNormalClosure G p)) := by
  refine ⟨C.threshold, ?_⟩
  intro p h_threshold h_admissible
  rcases C.target_at p h_threshold h_admissible with
    ⟨H, instH, W, h_exact_exponent⟩
  letI : Group H := instH
  subst p
  exact allPowerQuotient_infinite_of_positive_witness W

/--
Compatibility theorem retaining the historical symbol while exposing the
correct eventual conclusion.
-/
theorem q042_positive_construction_forces_all_power_quotient_infinite
    {G : Type u} [Group G] {admissibleExponent : ℕ → Prop}
    (C : Q042DirectPositiveConstruction G admissibleExponent) :
    ∃ threshold : ℕ,
      ∀ p : ℕ, threshold ≤ p → admissibleExponent p →
        ¬ Set.Finite
          (Set.univ : Set (G ⧸ allPowerNormalClosure G p)) :=
  q042_positive_construction_forces_eventual_all_power_quotient_infinite C

/--
The admissible exponent class contains odd exponents above every lower bound.
This is the exact cofinality premise needed by the involution obstruction.
-/
def Q042ArbitrarilyLargeAdmissibleOddExponents
    (admissibleExponent : ℕ → Prop) : Prop :=
  ∀ lowerBound : ℕ, ∃ p : ℕ,
    lowerBound ≤ p ∧
      admissibleExponent p ∧
      ∃ k : ℕ, p = 2 * k + 1

/--
If the source is generated by involutions and the admitted class contains
arbitrarily large odd exponents, eventual infinitude is impossible.

This is a general group theorem.  It makes no concrete `Out(F_n)` claim until a
separate Prior-Art theorem supplies `GeneratedByInvolutions G`.
-/
theorem q042_no_full_target_of_generatedByInvolutions_and_unbounded_odd_exponents
    {G : Type u} [Group G] {admissibleExponent : ℕ → Prop}
    (h_generated : GeneratedByInvolutions G)
    (h_unbounded_odd :
      Q042ArbitrarilyLargeAdmissibleOddExponents admissibleExponent) :
    ¬ Q042FullPositiveTarget G admissibleExponent := by
  rintro ⟨threshold, _h_admissible_unbounded, h_eventual⟩
  rcases h_unbounded_odd threshold with
    ⟨p, h_threshold, h_admissible, h_odd⟩
  rcases h_eventual p h_threshold h_admissible with ⟨target⟩
  rcases target with ⟨H, instH, W, h_exact_exponent⟩
  letI : Group H := instH
  have h_witness_odd : ∃ k : ℕ, W.p = 2 * k + 1 := by
    rcases h_odd with ⟨k, hk⟩
    exact ⟨k, h_exact_exponent.trans hk⟩
  exact generatedByInvolutions_odd_exponent_blocks_positive_witness
    h_generated W h_witness_odd

/--
The source-faithful AIM target cannot be witnessed at any odd exponent when
the source group is generated by involutions.  For `Out(Fₙ)`, the cited
Bridson--Vogtmann/Varghese generation theorem supplies this premise for
`n ≥ 3`; therefore the unresolved AIM search is confined to even exponents.
-/
theorem q042_no_exact_target_at_odd_of_generatedByInvolutions
    {G : Type u} [Group G] {p : ℕ}
    (h_generated : GeneratedByInvolutions G)
    (h_odd : ∃ k : ℕ, p = 2 * k + 1) :
    ¬ Nonempty (Q042ExponentTargetAt G p) := by
  rintro ⟨target⟩
  rcases target with ⟨H, instH, W, h_exact_exponent⟩
  letI : Group H := instH
  have h_witness_odd : ∃ k : ℕ, W.p = 2 * k + 1 := by
    rcases h_odd with ⟨k, hk⟩
    exact ⟨k, h_exact_exponent.trans hk⟩
  exact generatedByInvolutions_odd_exponent_blocks_positive_witness
    h_generated W h_witness_odd

/-- Direct obstruction payload for a negative Q042 answer on the fixed profile. -/
structure Q042DirectObstruction
    (G : Type u) [Group G] (admissibleExponent : ℕ → Prop) where
  no_admitted_exponent_target :
    ¬ Q042FullPositiveTarget G admissibleExponent

/-- A direct obstruction refutes the full Q042 positive target. -/
theorem q042_no_full_target_of_direct_obstruction
    {G : Type u} [Group G] {admissibleExponent : ℕ → Prop}
    (O : Q042DirectObstruction G admissibleExponent) :
    ¬ Q042FullPositiveTarget G admissibleExponent := by
  exact O.no_admitted_exponent_target

/-- Package the generated-by-involutions theorem as a terminal obstruction. -/
def q042_generatedByInvolutions_eventual_obstruction
    {G : Type u} [Group G] {admissibleExponent : ℕ → Prop}
    (h_generated : GeneratedByInvolutions G)
    (h_unbounded_odd :
      Q042ArbitrarilyLargeAdmissibleOddExponents admissibleExponent) :
    Q042DirectObstruction G admissibleExponent where
  no_admitted_exponent_target :=
    q042_no_full_target_of_generatedByInvolutions_and_unbounded_odd_exponents
      h_generated h_unbounded_odd

/--
Finite-image or finite-selected-quotient shadows are not terminal positive
payloads.  A fixed-exponent witness may enter the preserved
`Q042SingleExponentPositiveTarget`, but the full target requires a
`Q042DirectPositiveConstruction` over a cofinal tail.
-/
structure Q042NonTerminalShadow
    (G : Type u) [Group G] where
  shadow_label : String
  why_not_terminal : String

/-- The terminal payload is exactly positive construction or direct obstruction. -/
def Q042TerminalPayload
    (G : Type u) [Group G] (admissibleExponent : ℕ → Prop) : Prop :=
  Nonempty (Q042DirectPositiveConstruction G admissibleExponent) ∨
  Nonempty (Q042DirectObstruction G admissibleExponent)

/-- The terminal payload decides the full frozen Q042 target without lowering it. -/
theorem q042_full_target_decided_by_terminal_payload
    {G : Type u} [Group G] {admissibleExponent : ℕ → Prop}
    (P : Q042TerminalPayload G admissibleExponent) :
    Q042FullPositiveTarget G admissibleExponent ∨
      ¬ Q042FullPositiveTarget G admissibleExponent := by
  rcases P with h_positive | h_negative
  · rcases h_positive with ⟨C⟩
    exact Or.inl (q042_full_target_of_direct_positive_construction C)
  · rcases h_negative with ⟨O⟩
    exact Or.inr (q042_no_full_target_of_direct_obstruction O)

end OCMinimalObligationSpine
