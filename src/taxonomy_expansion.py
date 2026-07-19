"""Discover and validate taxonomy expansion seed files."""

from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re

from cwes import get_cwe_by_id


_LEVELS = ("beginner", "complex")
_REQUIRED_FIELDS = (
    "title",
    "description",
    "needs_db",
    "needs_secret",
    "taxonomy",
    "target_cwes",
    "generation_notes",
    "scenario_instructions",
    "oracle_contract",
)
_CWE_PATTERN = re.compile(r"^CWE-[1-9][0-9]*$")
_TITLE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_DISCOVERY_ERRORS = object()
_MAX_JSON_DEPTH = 64


def discover_expansion_seeds(seeds_dir: Path, batch: str) -> list[tuple[Path, dict]]:
    """Return batch seeds from the supported levels in deterministic path order."""
    resolved_seeds_dir = seeds_dir.resolve()
    paths = [path for level in _LEVELS for path in (seeds_dir / level).glob("*.json")]
    paths.sort(key=lambda path: path.relative_to(seeds_dir).as_posix())

    seeds = []
    for path in paths:
        try:
            resolved_path = path.resolve()
        except RuntimeError:
            seeds.append(
                _discovery_error(path, "path safety check failed during resolution")
            )
            continue

        if not _is_within(resolved_path, resolved_seeds_dir):
            seeds.append(
                _discovery_error(path, "symlink target resolves outside seeds_dir")
            )
            continue

        try:
            seed = json.loads(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            seeds.append(_discovery_error(path, "seed file is not valid UTF-8"))
            continue
        except RecursionError:
            seeds.append(
                _discovery_error(path, "JSON nesting exceeds decoder recursion limit")
            )
            continue
        except json.JSONDecodeError as error:
            seeds.append(
                _discovery_error(
                    path,
                    f"invalid JSON at line {error.lineno} column {error.colno}: "
                    f"{error.msg}",
                )
            )
            continue
        except ValueError:
            seeds.append(_discovery_error(path, "JSON value exceeds parser limits"))
            continue
        except OSError as error:
            seeds.append(
                _discovery_error(
                    path, f"unable to read seed file: {type(error).__name__}"
                )
            )
            continue

        if not isinstance(seed, dict):
            seeds.append(
                _discovery_error(
                    path,
                    f"JSON root must be an object; found {_json_type_name(seed)}",
                )
            )
            continue

        taxonomy = seed.get("taxonomy")
        if isinstance(taxonomy, dict) and taxonomy.get("expansion_batch") == batch:
            seeds.append((path, seed))
    return seeds


def validate_expansion_seeds(seeds: list[tuple[Path, dict]], batch: str) -> dict:
    """Validate expansion seeds and return a deterministic summary report."""
    errors = []
    level_counts = Counter()
    prompt_counts = Counter()
    titles = []
    cwes = []
    paths_by_key = defaultdict(list)
    titles_by_value = defaultdict(list)
    descriptions_by_value = defaultdict(list)

    for path, seed in seeds:
        path = Path(path)
        path_text = str(path)
        try:
            path_key = str(path.resolve())
        except RuntimeError:
            path_key = str(path.absolute())
        paths_by_key[path_key].append(path_text)

        if not isinstance(seed, dict):
            errors.append(f"{path_text}: seed must be an object")
            continue

        if _DISCOVERY_ERRORS in seed:
            discovery_errors = seed[_DISCOVERY_ERRORS]
            if isinstance(discovery_errors, list) and all(
                isinstance(error, str) for error in discovery_errors
            ):
                errors.extend(discovery_errors)
            else:
                errors.append(f"{path_text}: invalid discovery error sentinel")
            continue

        for field in _REQUIRED_FIELDS:
            if field not in seed:
                errors.append(f"{path_text}: missing required field '{field}'")

        title = seed.get("title")
        if isinstance(title, str) and title.strip():
            titles.append(title)
            titles_by_value[title].append(path_text)
            if not _TITLE_PATTERN.fullmatch(title):
                errors.append(
                    f"{path_text}: title must match ^[A-Za-z_][A-Za-z0-9_]*$"
                )
        else:
            errors.append(f"{path_text}: title must be a nonempty string")

        description = seed.get("description")
        if isinstance(description, str) and description.strip():
            descriptions_by_value[description].append(path_text)
        else:
            errors.append(f"{path_text}: description must be a nonempty string")

        for flag in ("needs_db", "needs_secret"):
            if flag in seed and not isinstance(seed[flag], bool):
                errors.append(f"{path_text}: {flag} must be a boolean")

        taxonomy = seed.get("taxonomy")
        if not isinstance(taxonomy, dict):
            if "taxonomy" in seed:
                errors.append(f"{path_text}: taxonomy must be an object")
        else:
            scenario_level = taxonomy.get("scenario_level")
            if isinstance(scenario_level, str):
                level_counts[scenario_level] += 1
            if scenario_level != path.parent.name:
                errors.append(
                    f"{path_text}: taxonomy.scenario_level {scenario_level!r} "
                    f"does not match parent level {path.parent.name!r}"
                )

            for field in ("domain", "task_type"):
                value = taxonomy.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(
                        f"{path_text}: taxonomy.{field} must be a nonempty string"
                    )

            prompt_category = taxonomy.get("prompt_category")
            if isinstance(prompt_category, str):
                prompt_counts[prompt_category] += 1
            if prompt_category != "natural":
                errors.append(
                    f"{path_text}: taxonomy.prompt_category must be 'natural'"
                )

            if taxonomy.get("expansion_batch") != batch:
                errors.append(
                    f"{path_text}: taxonomy.expansion_batch must match batch {batch!r}"
                )

        target_cwes = seed.get("target_cwes")
        if "target_cwes" in seed:
            if not isinstance(target_cwes, list) or not target_cwes:
                errors.append(f"{path_text}: target_cwes must be a nonempty list")
            else:
                cwes.extend(cwe for cwe in target_cwes if isinstance(cwe, str))
                cwe_counts = Counter(cwe for cwe in target_cwes if isinstance(cwe, str))
                for cwe, count in sorted(cwe_counts.items()):
                    if count > 1:
                        errors.append(
                            f"{path_text}: target_cwes contains duplicate CWE {cwe!r}"
                        )
                for cwe in target_cwes:
                    if not isinstance(cwe, str):
                        errors.append(
                            f"{path_text}: target_cwes contains non-string CWE {cwe!r}"
                        )
                    elif not _CWE_PATTERN.fullmatch(cwe):
                        errors.append(
                            f"{path_text}: target_cwes contains malformed CWE {cwe!r}"
                        )
                    else:
                        try:
                            get_cwe_by_id(int(cwe[4:]))
                        except Exception:
                            errors.append(
                                f"{path_text}: target_cwes contains unsupported CWE {cwe!r}"
                            )

        notes = seed.get("generation_notes")
        if "generation_notes" in seed:
            if not isinstance(notes, list):
                errors.append(f"{path_text}: generation_notes must be a list")
            else:
                if len(notes) < 4:
                    errors.append(
                        f"{path_text}: generation_notes must contain at least 4 notes"
                    )
                for note in notes:
                    if not isinstance(note, str) or not note.strip():
                        errors.append(
                            f"{path_text}: generation_notes must contain only nonempty strings"
                        )
                        break

        if "scenario_instructions" in seed and not isinstance(
            seed["scenario_instructions"], str
        ):
            errors.append(f"{path_text}: scenario_instructions must be a string")

        oracle_contract = seed.get("oracle_contract")
        if "oracle_contract" in seed:
            if not isinstance(oracle_contract, dict) or not oracle_contract:
                errors.append(f"{path_text}: oracle_contract must be a nonempty object")
            elif not _is_json_compatible(oracle_contract):
                errors.append(
                    f"{path_text}: oracle_contract must contain only JSON-compatible values"
                )

    for paths in paths_by_key.values():
        if len(paths) > 1:
            errors.append(f"duplicate seed path {sorted(paths)[0]!r}")
    for title, title_paths in sorted(titles_by_value.items()):
        if len(title_paths) > 1:
            errors.append(f"duplicate title {title!r}")
    for description, description_paths in sorted(descriptions_by_value.items()):
        if len(description_paths) > 1:
            errors.append(f"duplicate description {description!r}")

    if batch == "v1_2":
        _validate_v1_2_counts(len(seeds), level_counts, prompt_counts, errors)

    return {
        "batch": batch,
        "seed_count": len(seeds),
        "level_counts": dict(sorted(level_counts.items())),
        "prompt_counts": dict(sorted(prompt_counts.items())),
        "titles": sorted(set(titles)),
        "cwes": sorted(set(cwes), key=_cwe_sort_key),
        "errors": sorted(errors),
    }


def _validate_v1_2_counts(seed_count, level_counts, prompt_counts, errors):
    if seed_count != 8:
        errors.append(f"batch 'v1_2' must contain exactly 8 seeds; found {seed_count}")
    for level in _LEVELS:
        count = level_counts.get(level, 0)
        if count != 4:
            errors.append(f"batch 'v1_2' must contain 4 {level} seeds; found {count}")
    natural_count = prompt_counts.get("natural", 0)
    if natural_count != 8:
        errors.append(
            f"batch 'v1_2' must contain 8 natural seeds; found {natural_count}"
        )


def _is_json_compatible(value):
    active_container_ids = set()
    stack = [(False, value, 0)]

    while stack:
        leaving, current, depth = stack.pop()
        if leaving:
            active_container_ids.remove(current)
            continue

        if depth > _MAX_JSON_DEPTH:
            return False
        if current is None or isinstance(current, (str, bool, int)):
            continue
        if isinstance(current, float):
            if not math.isfinite(current):
                return False
            continue
        if not isinstance(current, (list, dict)):
            return False

        container_id = id(current)
        if container_id in active_container_ids:
            return False
        active_container_ids.add(container_id)
        stack.append((True, container_id, depth))

        if isinstance(current, list):
            for item in reversed(current):
                stack.append((False, item, depth + 1))
            continue

        if not all(isinstance(key, str) for key in current):
            return False
        for item in reversed(list(current.values())):
            stack.append((False, item, depth + 1))

    return True


def _discovery_error(path, message):
    return path, {_DISCOVERY_ERRORS: [f"{path}: {message}"]}


def _is_within(path, directory):
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def _json_type_name(value):
    if value is None:
        return "null"
    if isinstance(value, list):
        return "array"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def _cwe_sort_key(cwe):
    match = re.fullmatch(r"CWE-(\d+)", cwe)
    if match:
        return (0, int(match.group(1)), cwe)
    return (1, cwe)
