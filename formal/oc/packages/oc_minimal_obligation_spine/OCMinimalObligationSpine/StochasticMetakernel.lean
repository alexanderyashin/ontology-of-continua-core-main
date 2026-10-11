import OCMinimalObligationSpine.StableProjectionWorldModel

namespace OCMinimalObligationSpine

universe uState uQuotient uSignature uWeight

/--
A deliberately finite/typed skeleton for the stochastic metakernel bridge.

It is not a measure-theoretic Markov-kernel theorem.  The general theorem still
requires standard-Borel spaces, regular conditional probabilities, measurable
quotients, uncertainty propagation, and explicit countermodels.  This record
only captures the algebraic heart of the quotient obligation: once a quotient
kernel is declared by a lumpability witness, transition weights to quotient
states cannot depend on the chosen representative, and an exact quotient may not
identify states with distinct declared stochastic signatures.
-/
structure StochasticQuotientSkeleton
    (State : Type uState)
    (Q : Type uQuotient)
    (Signature : Type uSignature)
    (Weight : Type uWeight) where
  quotient : State -> Q
  signature : State -> Signature
  transitionWeightToQuotient : State -> Q -> Weight
  quotientTransitionWeight : Q -> Q -> Weight
  lumpable :
    forall state target,
      transitionWeightToQuotient state target =
        quotientTransitionWeight (quotient state) target
  exactSignatureProjection :
    forall {left right},
      quotient left = quotient right -> signature left = signature right

namespace StochasticQuotientSkeleton

theorem transition_weight_independent_of_representative
    (bridge :
      StochasticQuotientSkeleton State Q Signature Weight)
    {left right : State}
    (sameQuotient : bridge.quotient left = bridge.quotient right)
    (target : Q) :
    bridge.transitionWeightToQuotient left target =
      bridge.transitionWeightToQuotient right target := by
  calc
    bridge.transitionWeightToQuotient left target
        = bridge.quotientTransitionWeight (bridge.quotient left) target :=
          bridge.lumpable left target
    _ = bridge.quotientTransitionWeight (bridge.quotient right) target := by
          rw [sameQuotient]
    _ = bridge.transitionWeightToQuotient right target :=
          (bridge.lumpable right target).symm

theorem signature_distinction_refutes_quotient_collision
    (bridge :
      StochasticQuotientSkeleton State Q Signature Weight)
    {left right : State}
    (signatureDistinct : bridge.signature left ≠ bridge.signature right) :
    bridge.quotient left ≠ bridge.quotient right := by
  intro sameQuotient
  exact signatureDistinct (bridge.exactSignatureProjection sameQuotient)

end StochasticQuotientSkeleton

end OCMinimalObligationSpine
