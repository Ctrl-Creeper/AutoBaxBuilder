import logging
import os
import random
import socket
from argparse import ArgumentParser, Namespace
from typing import Sequence

from models import get_model

logger = logging.getLogger(__name__)


# Supported model providers for the agent
MODEL_PROVIDERS = ["openai", "together", "anthropic", "openrouter"]

# List of language models to use for solution generation
MODEL_LIST = [
    os.environ.get("AUTOBAX_MODEL", "gpt-5.5"),
]


class LazyReasoningModel:
    """Defers API client initialization until the first model call."""

    def __init__(self):
        self._model = None

    def generate(self, *args, **kwargs):
        if self._model is None:
            reasoning = os.environ.get("AUTOBAX_REASONING", "1") != "0"
            self._model = get_model(MODEL_LIST[0], "openai", reasoning, "medium")
        return self._model.generate(*args, **kwargs)


reasoning_model = LazyReasoningModel()

ENV_LIST = [
    "Python-FastAPI",
]

# Explicitly covered CWEs
MITRE_TOP_25 = [
    79,  # Cross-site Scripting (XSS)
    22,  # Improper Limitation of a Pathname
    94,  # Improper Control of Code Generation
    89,  # SQL Injection
    284,  # Improper Access Control
    78,  # OS Command Injection
    400,  # Uncontrolled Resource Consumption
    434,  # Unrestricted Upload of File with Dangerous Type
    522,  # Insufficiently Protected Credentials
    863,  # Incorrect Authorization
    20,  # Improper Input Validation
    204,  # Observable Response Discrepancy
    294,  # Authentication Bypass by Capture-replay
    345,  # Insufficient Verification of Data Authenticity
    352,  # Cross-Site Request Forgery (CSRF)
    362,  # Concurrent Execution using Shared Resource with Improper Synchronization
    384,  # Session Fixation
    409,  # Improper Handling of Highly Compressed Data
    502,  # Deserialization of Untrusted Data
    601,  # URL Redirection to Untrusted Site
    613,  # Insufficient Session Expiration
    639,  # Authorization Bypass Through User-Controlled Key
    640,  # Weak Password Recovery Mechanism for Forgotten Password
    915,  # Improperly Controlled Modification of Dynamically-Determined Object Attributes
    918,  # Server-Side Request Forgery (SSRF)
]

args = None
scenario_folder_path = None
_initialized = False


def get_baxbench_args(mode, model_list=MODEL_LIST, env_list=ENV_LIST, **kwargs):
    """Generate BaxBench arguments for running scenario tests.

    Args:
        mode: BaxBench mode ('generate', 'test', etc.)
        model_list: List of model names to test with
        env_list: List of environment names to test in
        **kwargs: Additional arguments to pass to BaxBench

    Returns:
        Parsed BaxBench arguments object
    """

    def get_random_free_port_far_from_used(
        min_port=12345, max_port=48000, safe_distance=50, max_attempts=100
    ):
        """Find a random free port range start without inspecting other processes."""

        def can_bind(port: int) -> bool:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.bind(("0.0.0.0", port))
                except OSError:
                    return False
            return True

        highest_start = max_port - safe_distance
        if highest_start < min_port:
            raise ValueError("Port search range is smaller than the safety window")

        for _ in range(max_attempts):
            candidate = random.randint(min_port, highest_start)
            if all(
                can_bind(port)
                for port in range(candidate, candidate + safe_distance + 1)
            ):
                return candidate
        raise RuntimeError("Could not find a free port range after multiple attempts")

    base_args = [
        "--models",
        *model_list,
        "--mode",
        mode,
        "--temperature",
        "0",
        "--n_samples",
        "1",
        "--envs",
        *env_list,
        "--min_port",
        str(get_random_free_port_far_from_used()),
    ]

    for k, v in kwargs.items():
        if isinstance(v, bool):
            if v:  # flags
                base_args.append(f"--{k}")
        else:
            base_args.append(f"--{k}")
            base_args.append(str(v))

    if mode in ["generate", "test"]:
        base_args.append("-f")
    print(" ".join(base_args))
    from baxbench_wrapper import baxbench_parse_args

    return baxbench_parse_args(base_args)


def build_parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument(
        "--difficulty",
        type=int,
        default=5,
        help="Difficulty of the backend, characterized as max. number of endpoints",
    )
    parser.add_argument(
        "--N_RETRIES",
        type=int,
        default=3,
        help="Max. number of attempts to fix invalid/erroronous/unparsable output in an agentic loop",
    )
    parser.add_argument(
        "--N_SOL_STEPS",
        type=int,
        default=5,
        help="Number of solution iteration steps",
    )
    parser.add_argument(
        "--N_TEST_STEPS",
        type=int,
        default=5,
        help="Number of test iteration steps",
    )

    parser.add_argument(
        "--N_SEC_STEPS",
        type=int,
        default=5,
        help="Number of security test iterations",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode",
    )
    parser.add_argument(
        "--path",
        default="./artifacts/",
        help="Path to artifacts folder",
    )
    parser.add_argument(
        "--seed_file",
        help=(
            "JSON scenario seed to expand when using --generate_scenarios. "
            "If omitted, a scenario idea is generated from scratch."
        ),
    )
    parser.add_argument(
        "--generate_only",
        action="store_true",
        help=(
            "Stop after generating artifacts for the selected stage. "
            "Currently used with --generate_exploits to create *_iw0 "
            "security tests without running BaxBench evaluation."
        ),
    )
    parser.add_argument(
        "--augment_security_tests",
        action="store_true",
        help=(
            "When used with --generate_exploits, load an existing *_iw0 artifact "
            "and append security tests for target CWEs that are not covered yet."
        ),
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--generate_scenarios", action="store_true", help="Generate scenarios"
    )
    group.add_argument("--generate_tests", action="store_true", help="Generate tests")
    group.add_argument(
        "--generate_exploits", action="store_true", help="Generate exploits"
    )

    parser.add_argument(
        "--scenario",
        type=str,
        help="Scenario name (required if --generate_tests or --generate_exploits is set)",
    )

    return parser


def initialize_config(argv: Sequence[str] | None = None) -> Namespace:
    global _initialized, args, scenario_folder_path

    if _initialized:
        assert args is not None
        return args

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = build_parser()
    parsed_args = parser.parse_args(argv)

    if (parsed_args.generate_tests or parsed_args.generate_exploits) and not (
        parsed_args.scenario
    ):
        parser.error(
            "--scenario is required when using --generate_tests or --generate_exploits"
        )
    if parsed_args.seed_file and not parsed_args.generate_scenarios:
        parser.error("--seed_file can only be used with --generate_scenarios")

    logger.info(f"Parsed command-line arguments: {parsed_args}")

    # Verify that the provided arguments are valid
    if not os.path.exists(parsed_args.path):
        parser.error(f"Invalid path {parsed_args.path}")
    if parsed_args.seed_file and not os.path.isfile(parsed_args.seed_file):
        parser.error(f"Invalid seed file {parsed_args.seed_file}")

    parsed_scenario_folder_path = os.path.join(
        parsed_args.path,
        parsed_args.scenario if parsed_args.scenario is not None else "",
    )
    if not os.path.exists(parsed_scenario_folder_path):
        parser.error(f"Invalid path {parsed_scenario_folder_path}")

    if parsed_args.scenario and not os.path.isfile(
        os.path.join(parsed_scenario_folder_path, f"{parsed_args.scenario}.json")
    ):
        parser.error(
            f"File {parsed_args.scenario}.json not found in directory {parsed_scenario_folder_path}"
        )

    args = parsed_args
    scenario_folder_path = parsed_scenario_folder_path
    _initialized = True
    return parsed_args
