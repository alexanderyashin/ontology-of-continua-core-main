import OCMinimalObligationSpine.UnifiedEntityProjection

namespace OCMinimalObligationSpine

open UnifiedEntityProjection

universe uState uReceiver uEffect uCarrier

/--
`CurrentK` is the declared state of a representation, not a certificate that the
representation is exact.  Keeping the laws outside the record lets the science
pipeline express, test, repair, or reject an inexact current K.
-/
structure CurrentK where
  State : Type uState
  Receiver : Type uReceiver
  Effect : Type uEffect
  Carrier : Type uCarrier
  stateTransition : State -> State
  receiverEffect : State -> Receiver -> Effect
  encode : State -> Carrier
  carrierTransition : Carrier -> Carrier
  decodeReceiverEffect : Carrier -> Receiver -> Effect

/-- Exactness of the particular decoder and encoded transition declared by K. -/
def HasExactDeclaredSemantics (K : CurrentK) : Prop :=
  PreservesTypedReceiverEffects
      K.receiverEffect K.encode K.decodeReceiverEffect /\
    PreservesTypedDeterministicDynamics
      K.stateTransition K.encode K.carrierTransition

/-- A concrete receiver effect that distinguishes two states at a finite step. -/
structure TrajectoryDistinction (K : CurrentK) where
  left : K.State
  right : K.State
  step : Nat
  receiver : K.Receiver
  effect_ne :
    K.receiverEffect
        (evolveState K.stateTransition step left) receiver ≠
      K.receiverEffect
        (evolveState K.stateTransition step right) receiver

/-- K expresses a concrete causal distinction exactly when its encoder separates it. -/
def Expresses (K : CurrentK) (d : TrajectoryDistinction K) : Prop :=
  K.encode d.left ≠ K.encode d.right

/-- Kernel faithfulness is weaker than exact declared semantics. -/
def TrajectoryKernelFaithful (K : CurrentK) : Prop :=
  forall {left right : K.State},
    K.encode left = K.encode right ->
      causalTrajectorySignature K.receiverEffect K.stateTransition left =
        causalTrajectorySignature K.receiverEffect K.stateTransition right

theorem exact_declared_semantics_implies_kernel_faithful
    (K : CurrentK)
    (hExact : HasExactDeclaredSemantics K) :
    TrajectoryKernelFaithful K := by
  intro left right collision
  exact exact_causal_dynamic_encoder_refines_trajectory_signature
    hExact.1 hExact.2 collision

theorem exact_declared_semantics_expresses
    (K : CurrentK)
    (hExact : HasExactDeclaredSemantics K)
    (d : TrajectoryDistinction K) :
    Expresses K d := by
  intro collision
  have sameTrajectory :=
    exact_causal_dynamic_encoder_refines_trajectory_signature
      hExact.1 hExact.2 collision
  exact d.effect_ne
    (congrFun (congrFun sameTrajectory d.step) d.receiver)

theorem unexpressed_distinction_refutes_exact_declared_semantics
    (K : CurrentK)
    (d : TrajectoryDistinction K)
    (hNotExpressed : Not (Expresses K d)) :
    Not (HasExactDeclaredSemantics K) := by
  intro hExact
  exact hNotExpressed (exact_declared_semantics_expresses K hExact d)

end OCMinimalObligationSpine
