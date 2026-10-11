import OCKIndividuationMSpaceComposition.SymmetryPrimitiveDistinctionGlobalPolarityBoundary

namespace OCKIndividuationMSpaceComposition

universe uCarrier

namespace PrimitiveDistinction

/-!
# The covered-carrier bridge from a primitive pair to a global C₂ torsor

The primitive pair always supplies a local two-point axis.  The ambient
pair-swap becomes a global free C₂ torsor only under the already identified
coverage premise.  This module packages that implication in the existing R3
interface and connects it to the Boolean anti-invariant boundary.

The torsor is not built into `PrimitiveDistinction`: its `reverseFree` and
`pairTransitive` fields are proved from exact carrier coverage.  Conversely,
any R3 torsor whose reversal is the canonical pair-swap forces coverage by
freeness.  Thus the Boolean witness and the canonical global torsor have the
same boundary.  No global extension, intrinsic dimension, or canonical
orientation is inferred without coverage.
-/

/-- Under exact coverage, the canonical ambient pair-swap is an R3
two-point torsor on the whole carrier.  `Unit` keeps the axis and identity
observation layers typed without claiming that either is derived from the
bare pair. -/
noncomputable def pairSwapGlobalTorsor
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) :
    R3C2OrientationTorsorInterface Carrier Unit Unit where
  reverse := distinction.pairSwap
  reverseInvolutive := distinction.pairSwap_involutive
  reverseFree :=
    (distinction.pairSwap_fixedPointFree_iff_coversCarrier).mpr covers
  pairTransitive := by
    intro first second
    rcases covers first with firstIsFirst | firstIsSecond
    · subst first
      rcases covers second with secondIsFirst | secondIsSecond
      · subst second
        exact Or.inl rfl
      · subst second
        exact Or.inr distinction.pairSwap_first.symm
    · subst first
      rcases covers second with secondIsFirst | secondIsSecond
      · subst second
        exact Or.inr distinction.pairSwap_second.symm
      · subst second
        exact Or.inl rfl
  axisOf := fun _ => ()
  identityOf := fun _ => ()

@[simp] theorem pairSwapGlobalTorsor_reverse
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) (point : Carrier) :
    (pairSwapGlobalTorsor distinction covers).reverse point =
      distinction.pairSwap point := rfl

theorem pairSwapGlobalTorsor_involutive
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) (point : Carrier) :
    (pairSwapGlobalTorsor distinction covers).reverse
        ((pairSwapGlobalTorsor distinction covers).reverse point) = point :=
  (pairSwapGlobalTorsor distinction covers).reverseInvolutive point

theorem pairSwapGlobalTorsor_free
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) (point : Carrier) :
    (pairSwapGlobalTorsor distinction covers).reverse point ≠ point :=
  (pairSwapGlobalTorsor distinction covers).reverseFree point

theorem pairSwapGlobalTorsor_pairTransitive
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (covers : distinction.CoversCarrier) (first second : Carrier) :
    second = first ∨
      second = (pairSwapGlobalTorsor distinction covers).reverse first :=
  (pairSwapGlobalTorsor distinction covers).pairTransitive first second

/-- A global R3 torsor with exactly the canonical pair-swap as reversal exists
exactly when the primitive pair covers the ambient carrier.  The left side is
an existential structure with independently proved freeness and transitivity;
the equality only identifies its reversal with the already defined swap. -/
theorem exists_pairSwapGlobalC2Torsor_iff_coversCarrier
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier) :
    (∃ torsor : R3C2OrientationTorsorInterface Carrier Unit Unit,
      torsor.reverse = distinction.pairSwap) ↔
      distinction.CoversCarrier := by
  constructor
  · rintro ⟨torsor, reverse_eq⟩
    apply (distinction.pairSwap_fixedPointFree_iff_coversCarrier).mp
    intro point
    rw [← reverse_eq]
    exact torsor.reverseFree point
  · intro covers
    exact ⟨pairSwapGlobalTorsor distinction covers, rfl⟩

/-- The observable Boolean anti-invariant and the canonical covered-carrier
torsor are equivalent witnesses.  This is an integration theorem, not a
global-C₂ conclusion from a bare distinction: both sides fail on an extra
fixed point. -/
theorem exists_pairSwapBoolAntiInvariant_iff_exists_pairSwapGlobalC2Torsor
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier) :
    (∃ polarity : Carrier → Bool,
      PairSwapBoolAntiInvariant distinction polarity) ↔
      (∃ torsor : R3C2OrientationTorsorInterface Carrier Unit Unit,
        torsor.reverse = distinction.pairSwap) := by
  constructor
  · intro antiInvariant
    have covers : distinction.CoversCarrier :=
      (exists_pairSwapBoolAntiInvariant_iff_coversCarrier distinction).mp
        antiInvariant
    exact (exists_pairSwapGlobalC2Torsor_iff_coversCarrier distinction).mpr
      covers
  · intro torsor
    have covers : distinction.CoversCarrier :=
      (exists_pairSwapGlobalC2Torsor_iff_coversCarrier distinction).mp torsor
    exact (exists_pairSwapBoolAntiInvariant_iff_coversCarrier distinction).mpr
      covers

theorem no_pairSwapGlobalC2Torsor_without_coverage
    {Carrier : Type uCarrier} (distinction : PrimitiveDistinction Carrier)
    (notCovered : ¬ distinction.CoversCarrier) :
    ¬ ∃ torsor : R3C2OrientationTorsorInterface Carrier Unit Unit,
      torsor.reverse = distinction.pairSwap := by
  intro torsor
  exact notCovered
    ((exists_pairSwapGlobalC2Torsor_iff_coversCarrier distinction).mp torsor)

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
