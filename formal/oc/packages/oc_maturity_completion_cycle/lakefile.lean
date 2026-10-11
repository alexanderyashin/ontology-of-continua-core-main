-- Modified for the portable OC release preview: local dependency paths and explicit OC audit roots.
-- Original recipe SHA256: 1e84eff0b10bba5999d57c2f8d5de96b4dd064a12344bb9502fcf4258b21f9cd
import Lake
open Lake DSL

package «oc_maturity_completion_cycle» where
  version := v!"0.1.0"

require oc_projection_causality_identity from "../oc_projection_causality_identity"

lean_lib OCMaturityCompletionCycle where
  roots := #[
    `OCMaturityCompletionCycle,
    `OCMaturityCompletionCycleA4A5Axioms,
    `OCMaturityCompletionCycleA4A5NegativeFixtures,
    `OCMaturityCompletionCycleA4A5Signatures,
    `OCMaturityCompletionCycleAudit,
    `OCMaturityCompletionCycleFullAudit,
    `OCMaturityCompletionCycleFullSignatures,
    `OCMaturityCompletionCycleIterativeDynamicsAxioms,
    `OCMaturityCompletionCycleIterativeDynamicsNegativeFixtures,
    `OCMaturityCompletionCycleIterativeDynamicsSignatures,
    `OCMaturityCompletionCycleIterativeDynamicsV2Axioms,
    `OCMaturityCompletionCycleIterativeDynamicsV2NegativeFixtures,
    `OCMaturityCompletionCycleIterativeDynamicsV2Signatures,
    `OCMaturityCompletionCyclePredictionAxioms,
    `OCMaturityCompletionCyclePredictionNegativeFixtures,
    `OCMaturityCompletionCyclePredictionR2Axioms,
    `OCMaturityCompletionCyclePredictionR2NegativeFixtures,
    `OCMaturityCompletionCyclePredictionR2Signatures,
    `OCMaturityCompletionCyclePredictionSignatures,
    `OCMaturityCompletionCycleSignatures,
    `OCMaturityCompletionCycleWaveCDAudit,
    `OCMaturityCompletionCycleWaveCDNegativeFixtures,
    `OCMaturityCompletionCycleWaveCDSignatures
  ]
