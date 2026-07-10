"""Environment loading utilities."""

from pathlib import Path

from dotenv import load_dotenv


def load_environment() -> None:
    """Load environment variables from project-level .env files."""
    project_root = Path(__file__).resolve().parents[3]
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if env_file.exists():
        load_dotenv(env_file)
    elif env_example.exists():
        load_dotenv(env_example)
