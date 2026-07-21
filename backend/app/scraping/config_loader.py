from pathlib import Path

import yaml

from app.scraping.config_models import SiteConfig

SITES_DIR = Path(__file__).parent / "sites"


def load_site_config(slug: str) -> SiteConfig:
    config_path = SITES_DIR / f"{slug}.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Site config not found: {config_path}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return SiteConfig(**data)


def list_available_sites() -> list[dict]:
    sites = []
    for config_path in sorted(SITES_DIR.glob("*.yaml")):
        if config_path.stem.startswith("_"):
            continue
        config = load_site_config(config_path.stem)
        sites.append(
            {
                "slug": config.site.slug,
                "name": config.site.name,
                "base_url": config.site.base_url,
            }
        )
    return sites
