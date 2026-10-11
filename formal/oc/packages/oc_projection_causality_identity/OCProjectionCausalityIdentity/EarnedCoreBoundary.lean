import OCProjectionCausalityIdentity.SeparatedTypes
import OCMinimalObligationSpine.StableProjectionWorldModel

/-!
# Exact boundary to the pinned OC 1.4 Earned Core

This module supplies only a conservative definitional translation: a selected
functional assembly can be viewed as a one-coordinate Earned Core projection
family.  It does not identify event causality, continuation evidence or object
persistence, and it does not promote an identity quotient to a world model.
-/

namespace OCProjectionCausalityIdentity

universe uOccurrence uObject

/-- A functional assembly represented as one Earned Core projection. -/
def assemblyProjectionFamily
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (assemble : Occurrence → Object) :
    OCMinimalObligationSpine.ProjectionFamily
      Occurrence Unit (fun _ => Object) where
  project := fun _ occurrence => assemble occurrence

theorem assemblyProjectionFamily_signature_at_unit
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (assemble : Occurrence → Object)
    (occurrence : Occurrence) :
    (assemblyProjectionFamily assemble).signature occurrence () =
      assemble occurrence := by
  rfl

/--
For the one-coordinate translation only, Earned Core joint separation is
exactly injectivity of the assembly.  Persistent assemblies are generally not
required to satisfy it; this is a boundary theorem, not an identity axiom.
-/
theorem assemblyProjectionFamily_jointlySeparates_iff_injective
    {Occurrence : Type uOccurrence}
    {Object : Type uObject}
    (assemble : Occurrence → Object) :
    (assemblyProjectionFamily assemble).JointlySeparates ↔
      Function.Injective assemble := by
  constructor
  · intro separates left right sameObject
    apply separates
    funext index
    cases index
    exact sameObject
  · intro injectiveAssembly left right sameSignature
    apply injectiveAssembly
    exact congrFun sameSignature ()

end OCProjectionCausalityIdentity
