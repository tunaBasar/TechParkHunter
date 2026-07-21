from pathlib import Path

import yaml
from pydantic import BaseModel

PROFILE_PATH = Path(__file__).parent / "profile.yaml"


class CandidateProfile(BaseModel):
    name: str
    title: str
    experience_years: str
    core_skills: list[str] = []
    highlights: list[str] = []
    education: str
    languages: list[str] = []


class ProfileConfig(BaseModel):
    candidate: CandidateProfile


def load_profile() -> CandidateProfile:
    raw = yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))
    config = ProfileConfig(**raw)
    return config.candidate
