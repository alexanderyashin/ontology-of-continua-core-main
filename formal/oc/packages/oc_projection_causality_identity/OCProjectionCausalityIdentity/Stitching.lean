import OCProjectionCausalityIdentity.FiniteQuotientCycles

/-!
# Path lifting and the stitching obstruction

Existential image edges always contain the image of coherent micro paths, but
their transitive closure may concatenate witnesses that are merely in the same
assembly fiber.  `ZeroStitchingDefect` says exactly that this extra freedom does
not add macro reachability.
-/

namespace OCProjectionCausalityIdentity

universe uOccurrence uObject uCarrier uInvariant

/-- Every coherent positive micro path has a corresponding macro path. -/
theorem liftedMicroReachability_implies_macroReachability
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    {micro : Occurrence → Occurrence → Prop}
    {assemble : Occurrence → Object}
    {source target : Object}
    (lifted : LiftedMicroReachability micro assemble source target) :
    MacroReachability micro assemble source target := by
  rcases lifted with ⟨left, right, leftClass, rightClass, path⟩
  have macroPath := transGen_maps_to_macro (assemble := assemble) path
  simpa only [leftClass, rightClass] using macroPath

/--
Exact path-lifting characterization: zero stitching defect holds precisely when
existential macro reachability and coherent lifted micro reachability agree.
-/
theorem zeroStitchingDefect_iff_reachabilityEquality
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (micro : Occurrence → Occurrence → Prop)
    (assemble : Occurrence → Object) :
    ZeroStitchingDefect micro assemble ↔
      ∀ source target,
        MacroReachability micro assemble source target ↔
          LiftedMicroReachability micro assemble source target := by
  constructor
  · intro zeroDefect source target
    change (∀ ⦃source target⦄,
      MacroReachability micro assemble source target →
        LiftedMicroReachability micro assemble source target) at zeroDefect
    exact ⟨zeroDefect (source := source) (target := target),
      liftedMicroReachability_implies_macroReachability⟩
  · intro reachabilityEquality source target macroPath
    exact (reachabilityEquality source target).1 macroPath

/-- An edge invariant is preserved along every positive transitive path. -/
theorem transGen_preserves_invariant
    {α : Type uCarrier}
    {β : Type uInvariant}
    {relation : α → α → Prop}
    {invariant : α → β}
    (edgePreserves :
      ∀ ⦃left right⦄, relation left right → invariant left = invariant right)
    {left right : α}
    (path : Relation.TransGen relation left right) :
    invariant left = invariant right := by
  induction path with
  | single edge => exact edgePreserves edge
  | tail _ edge inductionHypothesis =>
      exact inductionHypothesis.trans (edgePreserves edge)

/-- Four tokens witnessing a spurious macro path caused by an unliftable stitch. -/
inductive SpuriousToken
  | source
  | firstMiddle
  | secondMiddle
  | target
  deriving DecidableEq, Fintype, Repr

inductive ThreeObject
  | a
  | b
  | c
  deriving DecidableEq, Fintype, Repr

def spuriousMicro : SpuriousToken → SpuriousToken → Prop
  | .source, .firstMiddle => True
  | .secondMiddle, .target => True
  | _, _ => False

def spuriousAssembly : SpuriousToken → ThreeObject
  | .source => .a
  | .firstMiddle => .b
  | .secondMiddle => .b
  | .target => .c

/-- Components separate the two disconnected causal edges. -/
def spuriousComponent : SpuriousToken → Bool
  | .source => false
  | .firstMiddle => false
  | .secondMiddle => true
  | .target => true

theorem spuriousMicro_preserves_component :
    ∀ ⦃left right⦄,
      spuriousMicro left right →
        spuriousComponent left = spuriousComponent right := by
  intro left right edge
  cases left <;> cases right <;>
    simp_all [spuriousMicro, spuriousComponent]

theorem spurious_macro_a_to_b :
    MacroEdge spuriousMicro spuriousAssembly .a .b := by
  exact ⟨.source, .firstMiddle, trivial, rfl, rfl⟩

theorem spurious_macro_b_to_c :
    MacroEdge spuriousMicro spuriousAssembly .b .c := by
  exact ⟨.secondMiddle, .target, trivial, rfl, rfl⟩

theorem spurious_macro_a_reaches_c :
    MacroReachability spuriousMicro spuriousAssembly .a .c := by
  exact (Relation.TransGen.single spurious_macro_a_to_b).tail
    spurious_macro_b_to_c

theorem spurious_no_lifted_a_to_c :
    ¬ LiftedMicroReachability spuriousMicro spuriousAssembly .a .c := by
  rintro ⟨left, right, leftClass, rightClass, path⟩
  have sameComponent : spuriousComponent left = spuriousComponent right :=
    transGen_preserves_invariant spuriousMicro_preserves_component path
  cases left <;> cases right <;>
    simp_all [spuriousAssembly, spuriousComponent]

/--
Negative fixture: two legitimate macro edges compose, but no single coherent
micro path lifts their composite because the two middle witnesses differ.
-/
theorem spurious_path_fixture :
    MacroReachability spuriousMicro spuriousAssembly .a .c ∧
      ¬ LiftedMicroReachability spuriousMicro spuriousAssembly .a .c ∧
      ¬ ZeroStitchingDefect spuriousMicro spuriousAssembly := by
  refine ⟨spurious_macro_a_reaches_c, spurious_no_lifted_a_to_c, ?_⟩
  intro zeroDefect
  exact spurious_no_lifted_a_to_c (zeroDefect spurious_macro_a_reaches_c)

end OCProjectionCausalityIdentity
