namespace OCFullK

structure EmpiricalPacket where
  sourceBoundStatement : Prop
  lawfulDatasetManifest : Prop
  checksumRecorded : Prop
  replayScript : Prop
  thresholds : Prop
  falsifier : Prop
  dependencyClosure : Prop
  verification : Prop

def EmpiricalPacketClosed (P : EmpiricalPacket) : Prop :=
  P.sourceBoundStatement ∧ P.lawfulDatasetManifest ∧ P.checksumRecorded ∧
  P.replayScript ∧ P.thresholds ∧ P.falsifier ∧ P.dependencyClosure ∧
  P.verification

theorem empirical_packet_requires_dataset_manifest
    (P : EmpiricalPacket)
    (h : EmpiricalPacketClosed P) :
    P.lawfulDatasetManifest := by
  exact h.right.left

theorem empirical_packet_requires_replay
    (P : EmpiricalPacket)
    (h : EmpiricalPacketClosed P) :
    P.replayScript := by
  exact h.right.right.right.left

structure QueueState where
  activeAcquisitionRows : Nat
  remainingObligations : Nat
  fullEmpiricalCloseoutAllowed : Prop

def LawfulFullEmpiricalCloseout (Q : QueueState) : Prop :=
  Q.activeAcquisitionRows = 0 ∧ Q.remainingObligations = 0 ∧
  Q.fullEmpiricalCloseoutAllowed

theorem closeout_requires_no_active_acquisition
    (Q : QueueState)
    (h : LawfulFullEmpiricalCloseout Q) :
    Q.activeAcquisitionRows = 0 := by
  exact h.left

theorem closeout_requires_no_remaining_obligations
    (Q : QueueState)
    (h : LawfulFullEmpiricalCloseout Q) :
    Q.remainingObligations = 0 := by
  exact h.right.left

end OCFullK
