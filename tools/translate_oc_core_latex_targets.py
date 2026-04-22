"""Translate OC Core LaTeX target drafts while preserving TeX structure.

This helper is intentionally conservative: it translates prose from the
English source file into an existing ``*_ru.tex`` or ``*_de.tex`` target while
protecting math, labels, references, paths, URLs, and TeX command names.  The
release-source mirror is then written byte-identically to the root target.
"""

from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path

from deep_translator import GoogleTranslator


TARGETS = {"ru": "russian", "de": "german"}
ROOT = Path(__file__).resolve().parents[1]
MIRROR_ROOT = ROOT / "releases" / "oc_core_1_3" / "monograph" / "source"


PROTECT_FULL_COMMANDS = {
    "label",
    "ref",
    "eqref",
    "autoref",
    "cref",
    "Cref",
    "cite",
    "citep",
    "citet",
    "url",
    "href",
    "path",
    "input",
    "include",
    "includegraphics",
    "bibliography",
    "addbibresource",
    "texorpdfstring",
}

MATH_ENV_RE = re.compile(
    r"\\begin\{(?:equation|equation\*|align|align\*|gather|gather\*|"
    r"multline|multline\*|split|cases|matrix|pmatrix|bmatrix|array|tabular|"
    r"longtable)\}.*?\\end\{(?:equation|equation\*|align|align\*|gather|"
    r"gather\*|multline|multline\*|split|cases|matrix|pmatrix|bmatrix|array|"
    r"tabular|longtable)\}",
    re.S,
)


def _placeholder(index: int) -> str:
    return f"⟦{index:04d}⟧"


class Protector:
    def __init__(self) -> None:
        self.values: list[str] = []

    def protect(self, text: str) -> str:
        text = self._protect_regex(text, MATH_ENV_RE)
        text = self._protect_regex(text, re.compile(r"\\\[.*?\\\]", re.S))
        text = self._protect_regex(text, re.compile(r"\\\(.*?\\\)", re.S))
        text = self._protect_regex(text, re.compile(r"\$\$.*?\$\$", re.S))
        text = self._protect_regex(text, re.compile(r"(?<!\\)\$[^$\n]*(?<!\\)\$"))
        text = self._protect_full_commands(text)
        text = self._protect_regex(text, re.compile(r"\\begin\{[^{}]+\}|\\end\{[^{}]+\}"))
        text = self._protect_regex(text, re.compile(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?"))
        text = self._protect_regex(text, re.compile(r"\\."))  # escaped symbols and spacing commands
        text = self._protect_regex(text, re.compile(r"\b[A-Za-z]+(?:_[A-Za-z0-9{}]+)+\b"))
        return text

    def restore(self, text: str) -> str:
        # Later placeholders can contain earlier placeholders when a full TeX
        # command wraps protected math.  Restore from the outside in, then make
        # one forward clean-up pass for nested values.
        for i in reversed(range(len(self.values))):
            text = text.replace(_placeholder(i), self.values[i])
        for i, value in enumerate(self.values):
            text = text.replace(_placeholder(i), value)
        return text

    def _save(self, value: str) -> str:
        idx = len(self.values)
        self.values.append(value)
        return _placeholder(idx)

    def _protect_regex(self, text: str, pattern: re.Pattern[str]) -> str:
        return pattern.sub(lambda m: self._save(m.group(0)), text)

    def _protect_full_commands(self, text: str) -> str:
        for command in sorted(PROTECT_FULL_COMMANDS, key=len, reverse=True):
            text = self._protect_command_instances(text, command)
        return text

    def _protect_command_instances(self, text: str, command: str) -> str:
        needle = "\\" + command
        out: list[str] = []
        i = 0
        while i < len(text):
            j = text.find(needle, i)
            if j == -1:
                out.append(text[i:])
                break
            if j > 0 and (text[j - 1].isalpha() or text[j - 1] == "\\"):
                out.append(text[i : j + len(needle)])
                i = j + len(needle)
                continue
            out.append(text[i:j])
            k = j + len(needle)
            if k < len(text) and text[k] == "*":
                k += 1
            while k < len(text) and text[k].isspace():
                k += 1
            while k < len(text) and text[k] == "[":
                k = self._balanced_end(text, k, "[", "]")
                while k < len(text) and text[k].isspace():
                    k += 1
            while k < len(text) and text[k] == "{":
                k = self._balanced_end(text, k, "{", "}")
                while k < len(text) and text[k].isspace():
                    k += 1
            out.append(self._save(text[j:k]))
            i = k
        return "".join(out)

    @staticmethod
    def _balanced_end(text: str, start: int, open_ch: str, close_ch: str) -> int:
        depth = 0
        i = start
        while i < len(text):
            ch = text[i]
            if ch == "\\":
                i += 2
                continue
            if ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        return len(text)


def should_translate(block: str) -> bool:
    stripped = block.strip()
    if not stripped:
        return False
    if all(line.lstrip().startswith("%") for line in stripped.splitlines()):
        return False
    letters = re.findall(r"[A-Za-z]{2,}", stripped)
    return len(letters) >= 2


def split_blocks(text: str) -> list[str]:
    parts = re.split(r"(\n\s*\n)", text)
    return [part for part in parts if part != ""]


def translate_text(text: str, lang: str, translator: GoogleTranslator) -> str:
    protector = Protector()
    protected = protector.protect(text)
    if not should_translate(protected):
        return text
    translated_parts: list[str] = []
    for chunk in chunk_text(protected, 4200):
        translated_parts.append(translator.translate(chunk))
    translated = "".join(translated_parts)
    return apply_glossary(protector.restore(translated), lang)


def apply_glossary(text: str, lang: str) -> str:
    if lang == "ru":
        replacements = {
            "государственное пространство": "пространство состояний",
            "государственного пространства": "пространства состояний",
            "государственному пространству": "пространству состояний",
            "государственным пространством": "пространством состояний",
            "государственном пространстве": "пространстве состояний",
            "пространство штатов": "пространство состояний",
            "пространства штатов": "пространства состояний",
            "состояние пространства": "пространство состояний",
            "состояния пространства": "пространства состояний",
            "вероятность оккупации": "вероятность заполнения",
            "занимаемая вероятность": "вероятность заполнения",
            "Онтология континуа": "Ontology of Continua",
            "онтология континуа": "Ontology of Continua",
        }
    else:
        replacements = {
            "Ontologie von Continua": "Ontology of Continua",
            "Ontologie der Continua": "Ontology of Continua",
            "Zustandsraum und -zeit": "Zustandsraum und Zeit",
            "Strömungsfeld": "Flussfeld",
            "Ebene $": "Ebene $",
            "Level $": "Ebene $",
            "Level ": "Ebene ",
            "am $K_": "auf $K_",
            "Stufen $K_": "Ebenen $K_",
        }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def chunk_text(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in text.splitlines(keepends=True):
        if current and current_len + len(line) > limit:
            chunks.append("".join(current))
            current = []
            current_len = 0
        if len(line) > limit:
            while line:
                chunks.append(line[:limit])
                line = line[limit:]
            continue
        current.append(line)
        current_len += len(line)
    if current:
        chunks.append("".join(current))
    return chunks


def wrap_soft(text: str) -> str:
    out: list[str] = []
    for paragraph in split_blocks(text):
        if paragraph.strip() == "":
            out.append(paragraph)
            continue
        if "\n\n" in paragraph or paragraph.lstrip().startswith("%"):
            out.append(paragraph)
            continue
        lines = paragraph.splitlines()
        if any(line.lstrip().startswith(("\\[", "\\]", "\\begin", "\\end")) for line in lines):
            out.append(paragraph)
            continue
        rebuilt: list[str] = []
        for line in lines:
            if len(line) <= 110 or line.lstrip().startswith(("\\", "%")):
                rebuilt.append(line.rstrip())
            else:
                indent = re.match(r"\s*", line).group(0)
                rebuilt.extend(
                    textwrap.wrap(
                        line.strip(),
                        width=94,
                        initial_indent=indent,
                        subsequent_indent=indent,
                        break_long_words=False,
                        break_on_hyphens=False,
                    )
                )
        out.append("\n".join(rebuilt))
    return "".join(out)


def source_for_target(target: Path, lang: str) -> Path:
    name = target.name
    source_name = name[: -len(f"_{lang}.tex")] + ".tex"
    return target.with_name(source_name)


def target_header(lang: str, source: Path) -> str:
    rel = source.relative_to(ROOT).as_posix()
    return (
        "% GENERATED_BY: translate_oc_core_latex_targets.py\n"
        "% AI_ASSISTED_TRANSLATION_DRAFT: TRUE\n"
        "% THEOREM_REVIEW_STATUS: PENDING\n"
        "% THEOREM_REVIEW_MODE: FORMAL_AI_GATE__LATEX_AWARE_MT\n"
        "% THEOREM_REVIEW_REVIEWER_ID: \n"
        "% THEOREM_REVIEW_AUTHORITY_CLASS: \n"
        "% THEOREM_REVIEWED_AT: \n"
        "% THEOREM_REVIEW_DOSSIER_REF: \n"
        "% SOURCE_LANGUAGE: EN\n"
        f"% TARGET_LANGUAGE: {lang.upper()}\n"
        f"% SOURCE_EN_REF: {rel}\n"
    )


def translate_target(target: Path, lang: str, translator: GoogleTranslator) -> None:
    source = source_for_target(target, lang)
    if not source.exists():
        raise FileNotFoundError(f"source missing for {target}: {source}")
    source_text = source.read_text(encoding="utf-8")
    blocks = split_blocks(source_text)
    translated = "".join(translate_text(block, lang, translator) for block in blocks)
    final = target_header(lang, source) + wrap_soft(translated).rstrip() + "\n"
    target.write_text(final, encoding="utf-8")
    mirror = MIRROR_ROOT / target.relative_to(ROOT)
    if mirror.exists():
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(final, encoding="utf-8")


def collect_targets(paths: list[str], lang: str) -> list[Path]:
    targets: list[Path] = []
    for raw in paths:
        p = (ROOT / raw).resolve()
        if p.is_dir():
            targets.extend(sorted(p.rglob(f"*_{lang}.tex")))
        elif p.name.endswith(f"_{lang}.tex"):
            targets.append(p)
        else:
            raise ValueError(f"not a {lang} target or directory: {raw}")
    unique: list[Path] = []
    seen: set[Path] = set()
    for p in targets:
        if MIRROR_ROOT in p.parents:
            continue
        if p not in seen:
            unique.append(p)
            seen.add(p)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", choices=sorted(TARGETS), required=True)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()

    translator = GoogleTranslator(source="en", target=args.lang)
    targets = collect_targets(args.paths, args.lang)
    for idx, target in enumerate(targets, start=1):
        print(f"[{idx}/{len(targets)}] {target.relative_to(ROOT)}")
        translate_target(target, args.lang, translator)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
