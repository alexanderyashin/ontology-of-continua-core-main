import OCKIndividuationMSpaceComposition.BridgeOntologyHypergraph

namespace OCKIndividuationMSpaceComposition

/-!
Finite decision kernel used by the real Logion LDM/PDM mapping slice.

The precedence is part of the contract: an undeclared pair is not a candidate;
a declared pair with no physical endpoint is LDM-ahead; a changed cut or digest
is stale before evidence is interpreted; failed evidence rejects; a valid but
non-unique inverse admits the forward relation and abstains in reverse.
-/

inductive RealMappingVerdict where
  | noCandidate
  | ldmAhead
  | stale
  | rejected
  | admitForwardAbstainAmbiguous
  | admitExactOnVerifiedImage
deriving DecidableEq, Repr

structure RealMappingObservation where
  declared : Bool
  physicalExists : Bool
  validatorPass : Bool
  digestMatch : Bool
  currentCut : Bool
  inverseUnique : Bool
deriving DecidableEq, Repr

def realMappingVerdict (observation : RealMappingObservation) : RealMappingVerdict :=
  if !observation.declared then .noCandidate
  else if !observation.physicalExists then .ldmAhead
  else if !observation.currentCut || !observation.digestMatch then .stale
  else if !observation.validatorPass then .rejected
  else if !observation.inverseUnique then .admitForwardAbstainAmbiguous
  else .admitExactOnVerifiedImage

theorem admit_exact_of_all_requirements
    (observation : RealMappingObservation)
    (declared : observation.declared = true)
    (physical : observation.physicalExists = true)
    (validated : observation.validatorPass = true)
    (digest : observation.digestMatch = true)
    (current : observation.currentCut = true)
    (unique : observation.inverseUnique = true) :
    realMappingVerdict observation = .admitExactOnVerifiedImage := by
  simp [realMappingVerdict, declared, physical, validated, digest, current, unique]

theorem undeclared_is_not_candidate
    (observation : RealMappingObservation)
    (undeclared : observation.declared = false) :
    realMappingVerdict observation = .noCandidate := by
  simp [realMappingVerdict, undeclared]

theorem missing_physical_is_ldm_ahead
    (observation : RealMappingObservation)
    (declared : observation.declared = true)
    (missing : observation.physicalExists = false) :
    realMappingVerdict observation = .ldmAhead := by
  simp [realMappingVerdict, declared, missing]

theorem changed_digest_is_stale
    (observation : RealMappingObservation)
    (declared : observation.declared = true)
    (physical : observation.physicalExists = true)
    (changed : observation.digestMatch = false) :
    realMappingVerdict observation = .stale := by
  simp [realMappingVerdict, declared, physical, changed]

theorem changed_cut_is_stale
    (observation : RealMappingObservation)
    (declared : observation.declared = true)
    (physical : observation.physicalExists = true)
    (changed : observation.currentCut = false) :
    realMappingVerdict observation = .stale := by
  simp [realMappingVerdict, declared, physical, changed]

theorem failed_evidence_is_rejected
    (observation : RealMappingObservation)
    (declared : observation.declared = true)
    (physical : observation.physicalExists = true)
    (digest : observation.digestMatch = true)
    (current : observation.currentCut = true)
    (failed : observation.validatorPass = false) :
    realMappingVerdict observation = .rejected := by
  simp [realMappingVerdict, declared, physical, digest, current, failed]

theorem nonunique_inverse_must_abstain
    (observation : RealMappingObservation)
    (declared : observation.declared = true)
    (physical : observation.physicalExists = true)
    (validated : observation.validatorPass = true)
    (digest : observation.digestMatch = true)
    (current : observation.currentCut = true)
    (ambiguous : observation.inverseUnique = false) :
    realMappingVerdict observation = .admitForwardAbstainAmbiguous := by
  simp [realMappingVerdict, declared, physical, validated, digest, current, ambiguous]

theorem admitted_exact_requires_all_conditions
    (observation : RealMappingObservation)
    (admitted : realMappingVerdict observation = .admitExactOnVerifiedImage) :
    observation.declared = true ∧
      observation.physicalExists = true ∧
      observation.validatorPass = true ∧
      observation.digestMatch = true ∧
      observation.currentCut = true ∧
      observation.inverseUnique = true := by
  simp only [realMappingVerdict] at admitted
  split at admitted <;> simp_all
  split at admitted <;> simp_all
  split at admitted <;> simp_all
  split at admitted <;> simp_all

/-- A bounded mapping View is current exactly when its required mapping is exact. -/
def mappingViewCurrent (verdict : RealMappingVerdict) : Bool :=
  verdict == .admitExactOnVerifiedImage

theorem view_current_iff_mapping_exact (verdict : RealMappingVerdict) :
    mappingViewCurrent verdict = true ↔ verdict = .admitExactOnVerifiedImage := by
  simp [mappingViewCurrent]

end OCKIndividuationMSpaceComposition
