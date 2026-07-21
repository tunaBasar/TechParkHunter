from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel


class SiteInfo(BaseModel):
    name: str
    slug: str
    base_url: str
    company_list_url: str


class NavigationType(str, Enum):
    PAGINATION = "pagination"
    INFINITE_SCROLL = "infinite_scroll"
    LOAD_MORE = "load_more"


class NavigationConfig(BaseModel):
    type: NavigationType
    next_button: Optional[str] = None
    load_more_button: Optional[str] = None
    scroll_pause_ms: int = 1500
    max_pages: int = 50


class FieldSelector(BaseModel):
    selector: str
    type: Literal["text", "attribute", "html"]
    attribute: Optional[str] = None


class DetailPageConfig(BaseModel):
    link_selector: str
    fields: dict[str, FieldSelector]


class SelectorsConfig(BaseModel):
    company_container: str
    fields: dict[str, FieldSelector]
    detail_page: Optional[DetailPageConfig] = None


class FilterConfig(BaseModel):
    sector_keywords: dict[str, list[str]]


class SiteConfig(BaseModel):
    site: SiteInfo
    navigation: NavigationConfig
    selectors: SelectorsConfig
    filters: Optional[FilterConfig] = None
