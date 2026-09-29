# Asset licensing policy — 2026-09-28

GREEN means the inspected asset's commercial copying/adaptation grant appears sufficient for this private experimental workflow. It is separate from label quality, native status, speaker identity and scientific adequacy. No inference of rights from availability, a category, or an uploader's unrelated files is allowed.

The implemented allowlist is **CC0-1.0 and CC BY 2.0/2.5/3.0/4.0**, including the inspected France/UK ports, with a matching Creative Commons license URL and no unresolved per-file restrictions. Actual acquired license counts are in [inventory.md](inventory.md) and [pilot-summary.json](pilot-summary.json). Public-domain assets require an explicit applicable basis; a generic “Public domain” short field alone does not pass this tool. No public-domain-government audio is accepted this pass.

CC BY permits commercial adaptations subject to its terms: preserve creator/recorder credit, title, canonical source link, license link and applicable notices; identify changes in any later adapted audio. CC0 does not require attribution, but this manifest retains provenance and credits. Originals are downloaded unchanged; waveform diagnostics are separate. No endorsement is implied. [CC BY 2.0 France](https://creativecommons.org/licenses/by/2.0/fr/), [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/), [CC0](https://creativecommons.org/publicdomain/zero/1.0/).

## Lingua Libre dual licensing

Some files have an API short license of CC BY-SA 4.0 but an actual file license section containing all three templates: `Multi-license`, `cc-by-sa-4.0`, and `cc-0`. The [Multi-license template](https://commons.wikimedia.org/wiki/Template:Multi-license) explicitly makes its listed licenses alternatives. The uploader [Luilui6666's own page](https://commons.wikimedia.org/wiki/User:Luilui6666) also describes the dual grant. We choose CC0 **only where the exact recording's license block offers it**, preserving that block's templates and revision ID in each pilot row. The uploader statement corroborates, but never substitutes for, the asset grant. A CC-Zero category is not sufficient evidence.

Single-license CC0 files also have a file-level API grant and/or `cc-zero` block. The manifest retains `api_license`, selected `license`, `license_templates`, `revision_id`, and `license_evidence_url`. For example, [this Luilui6666 file](https://commons.wikimedia.org/wiki/File:LL-Q9192_(cmn)-Luilui6666-17-45.wav) illustrates the dual grant but is a phrase and is **not** a pilot label.

## Exclusions

- **YELLOW / excluded:** CC BY-SA, GFDL and other copyleft grants whose implications for learned weights remain unresolved for this project. These are not described as noncommercial licenses.
- **RED / excluded:** NC, research-only or incompatible restrictions. ND is excluded from this crop/adaptation workflow; it is not mislabeled as a blanket commercial ban.
- **YELLOW / excluded:** missing/conflicting license evidence, unresolved asset restrictions, and generic public-domain assertions without a verified basis.
- The default implementation rejects all grants outside the explicit allowlist; it does not purport to decide every possible open license.

## Source-specific cautions

Shtooka's Commons documentation says collections have separate licenses. Its old `packs.shtooka.net` README host did not resolve. Actual pilot permission rests on each Commons file's explicit grant, with medium provenance confidence, rather than a blanket Shtooka license. Most inspected Yue Tan assets instead expose CC BY-SA 3.0 US and are excluded. [Shtooka on Commons](https://commons.wikimedia.org/wiki/Commons:Shtooka), [per-file CC BY example](https://commons.wikimedia.org/wiki/File:Zh-b%C4%81.ogg).

The FSI/DLI resource scan contains a DLIFLC rights warning; see [sources-audit.md](sources-audit.md). A mirror's public-domain footer does not resolve that primary conflict. No claim that every historical FSI course is restricted follows from this one edition.

The already installed **pypinyin 0.55.0** and upstream single-character pronunciation data publish MIT grants. No package was installed, no production resolver imported, and no optional dictionary extension loaded. [Pinned tool license](https://github.com/mozillazg/python-pinyin/blob/v0.55.0/LICENSE.txt), [dictionary license](https://github.com/mozillazg/pinyin-data/blob/master/LICENSE). Preserve those notices if redistributing substantial dictionary material. The small manifest records pronunciation facts and tool/version lineage.
