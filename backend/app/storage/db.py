import json
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from app.storage.models import CompanyFilter, ScrapedData

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source TEXT NOT NULL,
    source_name TEXT,
    sector TEXT,
    sector_tags TEXT,
    description TEXT,
    website TEXT,
    contact_email TEXT,
    detail_url TEXT,
    application_status TEXT DEFAULT 'not_applied',
    notes TEXT DEFAULT '',
    scraped_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_source ON companies(source);",
    "CREATE INDEX IF NOT EXISTS idx_sector ON companies(sector);",
    "CREATE INDEX IF NOT EXISTS idx_status ON companies(application_status);",
    "CREATE INDEX IF NOT EXISTS idx_name ON companies(name);",
]


class DatabaseManager:
    def __init__(self, db_path: str = "techpark_hunter.db"):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_TABLE_SQL)
            for index_sql in CREATE_INDEXES_SQL:
                await db.execute(index_sql)
            await db.commit()

    async def upsert_companies(self, data: ScrapedData):
        async with aiosqlite.connect(self.db_path) as db:
            for company in data.companies:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO companies (
                        id, name, source, source_name, sector, sector_tags,
                        description, website, contact_email, detail_url,
                        application_status, notes, scraped_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        company.id,
                        company.name,
                        data.source,
                        data.source_name,
                        company.sector,
                        json.dumps(company.sector_tags),
                        company.description,
                        company.website,
                        company.contact_email,
                        company.detail_url,
                        company.application_status.value,
                        company.notes,
                        data.scraped_at.isoformat(),
                    ),
                )
            await db.commit()

    async def get_companies(self, filter: CompanyFilter) -> tuple[list[dict], int]:
        conditions = []
        params: list = []

        if filter.source:
            conditions.append("source = ?")
            params.append(filter.source)
        if filter.sector:
            conditions.append("sector = ?")
            params.append(filter.sector)
        if filter.status:
            conditions.append("application_status = ?")
            params.append(filter.status.value)
        if filter.search:
            conditions.append("(name LIKE ? OR description LIKE ?)")
            like = f"%{filter.search}%"
            params.extend([like, like])

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            count_cursor = await db.execute(
                f"SELECT COUNT(*) AS total FROM companies {where_clause}", params
            )
            count_row = await count_cursor.fetchone()
            total = count_row["total"]

            offset = (filter.page - 1) * filter.per_page
            rows_cursor = await db.execute(
                f"SELECT * FROM companies {where_clause} "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [filter.per_page, offset],
            )
            rows = await rows_cursor.fetchall()

            companies = []
            for row in rows:
                company = dict(row)
                company["sector_tags"] = json.loads(company["sector_tags"] or "[]")
                companies.append(company)

            return companies, total

    async def get_company(self, company_id: str) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM companies WHERE id = ?", (company_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            company = dict(row)
            company["sector_tags"] = json.loads(company["sector_tags"] or "[]")
            return company

    async def update_company_status(
        self, company_id: str, status: str, notes: str
    ) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                UPDATE companies
                SET application_status = ?, notes = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, notes, datetime.now(timezone.utc).isoformat(), company_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def delete_company(self, company_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM companies WHERE id = ?", (company_id,)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def update_contact_email(self, company_id: str, contact_email: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                UPDATE companies
                SET contact_email = ?, updated_at = ?
                WHERE id = ?
                """,
                (contact_email, datetime.now(timezone.utc).isoformat(), company_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_stats(self) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            total_cursor = await db.execute("SELECT COUNT(*) AS total FROM companies")
            total_row = await total_cursor.fetchone()
            total_companies = total_row["total"]

            by_source_cursor = await db.execute(
                "SELECT source, COUNT(*) AS count FROM companies GROUP BY source"
            )
            by_source_rows = await by_source_cursor.fetchall()
            by_source = {row["source"]: row["count"] for row in by_source_rows}

            by_status_cursor = await db.execute(
                "SELECT application_status, COUNT(*) AS count FROM companies "
                "GROUP BY application_status"
            )
            by_status_rows = await by_status_cursor.fetchall()
            by_status = {
                row["application_status"]: row["count"] for row in by_status_rows
            }

            return {
                "total_companies": total_companies,
                "by_source": by_source,
                "by_status": by_status,
            }
