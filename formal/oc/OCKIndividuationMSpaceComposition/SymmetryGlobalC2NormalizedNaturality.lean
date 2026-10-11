import OCKIndividuationMSpaceComposition.SymmetryGlobalC2NormalizedDecomposition
import OCKIndividuationMSpaceComposition.SymmetryNativeReversalClosure
import Mathlib.Tactic.Ring

namespace OCKIndividuationMSpaceComposition

universe uCarrier uTargetCarrier uValue

namespace PrimitiveDistinction

/-!
# Naturality of the normalized global symmetry layers

The normalized even/odd projections are defined on a carrier together with a
primitive distinction.  This file proves that they are genuinely
representation-independent under a carrier equivalence: transporting both
the distinction and the observable conjugates the two projections exactly.
The even layer is preserved, while the odd layer is preserved as an
orientation-sensitive function on the relabelled carrier.  No coordinate,
metric, or quotient choice is introduced.
-/

namespace GlobalC2Naturality

variable {Carrier : Type uCarrier} {TargetCarrier : Type uTargetCarrier}
  {Value : Type uValue}
variable [Fintype Carrier] [DecidableEq Carrier]
variable [Fintype TargetCarrier] [DecidableEq TargetCarrier]
variable [Field Value] [CharZero Value]

/-! A value-valued observable transported along a carrier equivalence. -/
def transportObservable
    (relabel : Carrier ≃ TargetCarrier)
    (observable : Carrier → Value) : TargetCarrier → Value :=
  fun point => observable (relabel.symm point)

theorem transport_pairSwap_apply
    (relabel : Carrier ≃ TargetCarrier)
    (distinction : PrimitiveDistinction Carrier)
    (point : Carrier) :
    (NativeCarrierTransport.transportDistinction relabel distinction).pairSwap
        (relabel point) =
      relabel (distinction.pairSwap point) := by
  have transported := congrArg
    (fun permutation : Equiv.Perm TargetCarrier => permutation (relabel point))
    (NativeCarrierTransport.transport_pairSwap relabel distinction)
  simpa [NativeCarrierTransport.transportPermutation_apply, pairSwapEquiv]
    using transported.symm

theorem transport_carrierInvariantHalf
    (relabel : Carrier ≃ TargetCarrier)
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value) (point : Carrier) :
    (NativeCarrierTransport.transportDistinction relabel distinction).carrierInvariantHalf
        (transportObservable relabel observable) (relabel point) =
      distinction.carrierInvariantHalf observable point := by
  simp only [carrierInvariantHalf, transportObservable]
  rw [show (relabel.symm (relabel point)) = point from relabel.symm_apply_apply point]
  rw [transport_pairSwap_apply relabel distinction point]
  simp only [relabel.symm_apply_apply]

theorem transport_carrierAntiInvariantHalf
    (relabel : Carrier ≃ TargetCarrier)
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value) (point : Carrier) :
    (NativeCarrierTransport.transportDistinction relabel distinction).carrierAntiInvariantHalf
        (transportObservable relabel observable) (relabel point) =
      distinction.carrierAntiInvariantHalf observable point := by
  simp only [carrierAntiInvariantHalf, transportObservable]
  rw [show (relabel.symm (relabel point)) = point from relabel.symm_apply_apply point]
  rw [transport_pairSwap_apply relabel distinction point]
  simp only [relabel.symm_apply_apply]

theorem transport_carrierInvariantHalf_invariant
    (relabel : Carrier ≃ TargetCarrier)
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value) :
    CarrierInvariant
      (NativeCarrierTransport.transportDistinction relabel distinction)
      ((NativeCarrierTransport.transportDistinction relabel distinction).carrierInvariantHalf
        (transportObservable relabel observable)) :=
  carrierInvariantHalf_invariant
    (NativeCarrierTransport.transportDistinction relabel distinction)
    (transportObservable relabel observable)

theorem transport_carrierAntiInvariantHalf_antiInvariant
    (relabel : Carrier ≃ TargetCarrier)
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value) :
    CarrierAntiInvariant
      (NativeCarrierTransport.transportDistinction relabel distinction)
      ((NativeCarrierTransport.transportDistinction relabel distinction).carrierAntiInvariantHalf
        (transportObservable relabel observable)) :=
  carrierAntiInvariantHalf_antiInvariant
    (NativeCarrierTransport.transportDistinction relabel distinction)
    (transportObservable relabel observable)

/-! The split itself is preserved pointwise, not just each projection in
isolation. -/
theorem transport_normalized_reconstruction
    (relabel : Carrier ≃ TargetCarrier)
    (distinction : PrimitiveDistinction Carrier)
    (observable : Carrier → Value) (point : Carrier) :
    (NativeCarrierTransport.transportDistinction relabel distinction).carrierInvariantHalf
          (transportObservable relabel observable) (relabel point) +
        (NativeCarrierTransport.transportDistinction relabel distinction).carrierAntiInvariantHalf
          (transportObservable relabel observable) (relabel point) =
      observable point := by
  rw [transport_carrierInvariantHalf relabel distinction observable point,
    transport_carrierAntiInvariantHalf relabel distinction observable point]
  exact carrierInvariantHalf_add_carrierAntiInvariantHalf_eq_observable
    distinction observable point

end GlobalC2Naturality

end PrimitiveDistinction

end OCKIndividuationMSpaceComposition
