import json
import keyword
import os
import re
import shutil

from agent.config import args, logger
from models.base import token_usage_file


def make_identifier(s: str) -> str:
    s = re.sub(r"\W", "_", s)  # \W = anything not a letter, digit, underscore
    if re.match(r"^\d", s):
        s = "_" + s
    if keyword.iskeyword(s):
        s += "_"
    return s


def _format_seed_constraints(seed: dict) -> str:
    """Turns optional seed metadata into generation guidance."""
    constraints = []

    taxonomy = seed.get("taxonomy")
    if taxonomy:
        constraints.append(
            "Taxonomy labels for this benchmark seed:\n"
            + "\n".join(f"- {key}: {value}" for key, value in taxonomy.items())
        )

    if not constraints:
        return ""

    return "\n\n" + "\n\n".join(constraints)


def load_scenario_seed(seed_file: str) -> dict:
    """Loads a manually curated scenario seed and normalizes core fields."""
    with open(seed_file, "r", encoding="utf-8") as file:
        seed = json.load(file)

    required_fields = ["title", "description", "needs_db", "needs_secret"]
    missing_fields = [field for field in required_fields if field not in seed]
    if missing_fields:
        raise ValueError(
            f"Seed {seed_file} is missing required field(s): "
            + ", ".join(missing_fields)
        )

    scenario = dict(seed)
    scenario["title"] = make_identifier("".join(str(seed["title"]).strip().split()))
    scenario["description"] = str(seed["description"]).strip()
    scenario["_generation_description"] = scenario[
        "description"
    ] + _format_seed_constraints(seed)
    scenario["needs_db"] = bool(seed["needs_db"])
    scenario["needs_secret"] = bool(seed["needs_secret"])
    scenario["source_seed_file"] = seed_file
    scenario.setdefault("scenario_instructions", "")
    scenario.setdefault("difficulty", args.difficulty)

    return scenario


def generate_scenarios() -> None:
    """Generate a novel security scenario with OpenAPI schema and text specification.

    This function orchestrates the complete scenario generation process:
    1. Generates a scenario idea
    2. Validates novelty against existing scenarios
    3. Generates OpenAPI schema
    4. Generates text specification
    5. Saves the complete scenario to a JSON file
    """
    logger.info("generating scenarios")
    if args.seed_file:
        logger.info(f"loading scenario seed from {args.seed_file}")
        scenario = load_scenario_seed(args.seed_file)
    else:
        from agent.generate_scenario_ideas import (
            generate_scenario_idea,
            scenario_idea_is_novel,
        )

        scenario = generate_scenario_idea()

        while not scenario_idea_is_novel(scenario):
            logger.warning("Scenario idea is not novel, generating a new one")
            scenario = generate_scenario_idea()

    public_description = scenario["description"]
    if args.seed_file:
        scenario["description"] = scenario.get(
            "_generation_description", public_description
        )

    if "schema" not in scenario:
        from agent.generate_scenario_specs import generate_openapi

        scenario["schema"] = generate_openapi(scenario)
    if "text_spec" not in scenario:
        from agent.generate_scenario_specs import generate_text_spec

        scenario["text_spec"] = generate_text_spec(scenario)
    scenario["description"] = public_description
    scenario.pop("_generation_description", None)
    scenario.setdefault("difficulty", args.difficulty)
    scenario.setdefault("scenario_instructions", "")

    scenario_folder_path = os.path.join(args.path, scenario["title"])

    full_path = os.path.join(scenario_folder_path, f"{scenario['title']}.json")
    os.makedirs(scenario_folder_path, exist_ok=True)

    if os.path.exists(token_usage_file):
        shutil.move(
            token_usage_file,
            os.path.join(scenario_folder_path, "token_usage.txt"),
        )

    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(scenario, f, indent=4)

    logger.info(f"Saved scenario to {full_path}")
