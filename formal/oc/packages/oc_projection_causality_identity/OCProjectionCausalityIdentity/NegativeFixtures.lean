import OCProjectionCausalityIdentity.OrderConvexity
import OCProjectionCausalityIdentity.Stitching

/-!
# Wave-1 negative fixtures

These finite witnesses prevent three invalid strengthenings:

* an acyclic micro relation need not have an acyclic existential quotient;
* convex fibers of a partial order do not suffice (unlike the proved total-order
  characterization);
* strong representative congruence is not necessary for quotient acyclicity;
* existential macro paths need not lift to coherent micro paths.
-/

namespace OCProjectionCausalityIdentity

theorem wave1_negative_fixture_bundle :
    (NoPositiveCycle threeTokenCausal ∧
      HasPositiveCycle (MacroEdge threeTokenCausal threeTokenAssembly)) ∧
    (FiberConvexFor twoChainLE twoChainAssembly ∧
      IsPartialOrderRelation twoChainLE ∧
      HasPositiveCycle (ExternalMacroEdge twoChainLT twoChainAssembly)) ∧
    (NoPositiveCycle (MacroEdge oneCrossEdge twoChainAssembly) ∧
      ¬ StrongQuotientCongruence oneCrossEdge twoChainAssembly) ∧
    (MacroReachability spuriousMicro spuriousAssembly .a .c ∧
      ¬ LiftedMicroReachability spuriousMicro spuriousAssembly .a .c) := by
  exact
    ⟨⟨threeTokenCausal_acyclic, threeToken_quotient_has_reciprocal_cycle⟩,
      partialOrder_convex_fibers_can_have_reciprocal_quotient,
      strongCongruence_is_not_necessary_for_macro_acyclicity,
      ⟨spurious_macro_a_reaches_c, spurious_no_lifted_a_to_c⟩⟩

end OCProjectionCausalityIdentity
