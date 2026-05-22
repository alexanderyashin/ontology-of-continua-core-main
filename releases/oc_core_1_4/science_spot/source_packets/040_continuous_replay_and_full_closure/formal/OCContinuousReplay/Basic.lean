namespace OCContinuousReplay

structure EvidenceClosure where
  sourceStatement : Prop
  proposition : Prop
  lawfulDatasetOrProof : Prop
  replayOrProofArtifact : Prop
  falsifier : Prop
  dependencyClosure : Prop
  verification : Prop

def Promotable (E : EvidenceClosure) : Prop :=
  E.sourceStatement ∧ E.proposition ∧ E.lawfulDatasetOrProof ∧
  E.replayOrProofArtifact ∧ E.falsifier ∧ E.dependencyClosure ∧ E.verification

theorem promoted_requires_artifact
    (E : EvidenceClosure)
    (h : Promotable E) :
    E.replayOrProofArtifact := by
  exact h.right.right.right.left

theorem promoted_requires_falsifier
    (E : EvidenceClosure)
    (h : Promotable E) :
    E.falsifier := by
  exact h.right.right.right.right.left

structure ContinuousQueue where
  representedRows : Nat
  openRows : Nat
  closeoutAllowed : Prop

def LawfulCloseout (Q : ContinuousQueue) : Prop :=
  Q.representedRows = 63 ∧ Q.openRows = 0 ∧ Q.closeoutAllowed

theorem closeout_requires_zero_open_rows
    (Q : ContinuousQueue)
    (h : LawfulCloseout Q) :
    Q.openRows = 0 := by
  exact h.right.left

theorem closeout_requires_all_rows_represented
    (Q : ContinuousQueue)
    (h : LawfulCloseout Q) :
    Q.representedRows = 63 := by
  exact h.left

end OCContinuousReplay
