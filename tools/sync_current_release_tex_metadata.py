from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKER = ROOT / "releases" / "CURRENT_RELEASE.json"
OUTPUTS = [
    ROOT / "release_metadata.tex",
    ROOT / "releases" / "oc_core_1_3" / "monograph" / "source" / "release_metadata.tex",
]


def main() -> int:
    marker = json.loads(MARKER.read_text(encoding="utf-8"))
    version = str(marker["version"]).strip()
    body = "\n".join(
        [
            "% Generated from releases/CURRENT_RELEASE.json by tools/sync_current_release_tex_metadata.py.",
            "% This file is the TeX-facing release pointer surface. It may be regenerated",
            "% when the owner moves the public release pointer.",
            rf"\providecommand{{\ocpublicversion}}{{{version}}}",
            r"\providecommand{\ocpublicreleaselabel}{Core \ocpublicversion}",
            r"\providecommand{\ocpdftitle}{Ontology of Continua --- \ocpublicreleaselabel{} Canonical Master Monograph}",
            r"\providecommand{\ocpdfkeywords}{Ontology of Continua, \ocpublicreleaselabel, K-level hierarchy, theorem closure, empirical validation, falsifiability, practical utility}",
            r"\providecommand{\ocpdfproducer}{XeLaTeX with OC \ocpublicreleaselabel{} build scripts}",
            "",
        ]
    )
    for output in OUTPUTS:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(body, encoding="utf-8")
    print(f"SYNCED_RELEASE_TEX_METADATA version={version} outputs={len(OUTPUTS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
