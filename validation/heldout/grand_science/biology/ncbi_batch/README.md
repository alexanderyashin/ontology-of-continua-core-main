# Biology NCBI/GEO Batch Factory

Verdict: `BLOCKED_ACQUISITION_READY_NCBI_GEO_BATCH`
Grand TOE support allowed: `False`
Rows: `1`
Minimum N: `20`
Missing official snapshots: `19`

## Open blockers
- `SOURCE_SEPARATION_MISSING::defaulting_to_snapshot_replay`
- `SOURCE_SEPARATION_MODE_NOT_ALLOWED::snapshot_replay`
- `TARGET_SEPARATION_NOT_REAL::snapshot_replay`
- `PRE_TARGET_LOCK_REQUIRED`
- `TARGET_HIDDEN_UNTIL_SCORING_REQUIRED`
- `SOURCE_SEPARATION_NOT_DECLARED_BEFORE_SCORING`
- `TRAINING_AND_TARGET_SOURCES_REQUIRED`
- `OFFICIAL_NCBI_GEO_PROVENANCE_MISSING::BIOLOGY-NCBI-GEO-BATCH-0001-F6B8F2D6A89F`
- `COMPARATOR_BASELINE_NOT_PREREGISTERED::BIOLOGY-NCBI-GEO-BATCH-0001-F6B8F2D6A89F`
- `COMPARATOR_BASELINE_NOT_PREREGISTERED`
- `OFFICIAL_NCBI_GEO_PROVENANCE_REQUIRED`
- `N_BELOW_MINIMUM::1/20`
- `CURRENT_RAW_DATA_TOO_THIN_FOR_NCBI_GEO_BATCH`
- `SOURCE_SEPARATION_MODE_NOT_ALLOWED`
- `N_BELOW_MINIMUM::20`
- `GRAND_TOE_SUPPORT_NOT_ALLOWED`

## No-Send Locks
- `no_send`: `True`
- `publish_allowed`: `False`
- `registry_write_allowed`: `False`

## Acquisition
- `validation/_raw/biology_ncbi_geo_gpl96_accession_retstart_000020_retmax_20.json` from `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term=GPL96%5BAccession%5D&retmode=json&retstart=20&retmax=20`
- `validation/_raw/biology_ncbi_geo_gpl96_accession_retstart_000040_retmax_20.json` from `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term=GPL96%5BAccession%5D&retmode=json&retstart=40&retmax=20`
- `validation/_raw/biology_ncbi_geo_gpl96_accession_retstart_000060_retmax_20.json` from `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term=GPL96%5BAccession%5D&retmode=json&retstart=60&retmax=20`
- `validation/_raw/biology_ncbi_geo_gpl96_accession_retstart_000080_retmax_20.json` from `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term=GPL96%5BAccession%5D&retmode=json&retstart=80&retmax=20`
- `validation/_raw/biology_ncbi_geo_gpl96_accession_retstart_000100_retmax_20.json` from `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=gds&term=GPL96%5BAccession%5D&retmode=json&retstart=100&retmax=20`
- `14` additional official snapshot requests listed in the acquisition packet
