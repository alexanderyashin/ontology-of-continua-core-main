# Changelog

## [1.3.2] - 2026-04-26

### Added
- Release Machine v1 gates for public archival release readiness.
- Public release dossier, owner approval checkpoint, and no-send publish manifest.
- Research packet audit and manuscript staging queue for bounded scientific appendix material.

### Changed
- Metadata now distinguishes the previous canonical DOI from the pending v1.3.2 DOI.
- Release packaging now uses deterministic manifest and checksum conventions.

### Fixed
- Public release surfaces now carry explicit owner approval and no-send policy.
- Research packets are routed as support/frontier artifacts without canonical claim promotion.

### Metadata
- Added CodeMeta, RO-Crate, Zenodo metadata, and SWHID owner-action recording.

### Reproducibility
- Added package-level reproducibility, evidence, and metadata bundle sections.

### Integrity
- Added bundle manifest, checksums, PDF integrity checks, ZIP integrity checks, and public leak scans.

### Known limitations
- No external publication has occurred. SWHID remains an owner action unless a resolvable existing identifier is supplied.
