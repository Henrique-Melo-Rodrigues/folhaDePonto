from __future__ import annotations

from functools import lru_cache

from django.conf import settings
from pymongo import ASCENDING, MongoClient


@lru_cache(maxsize=8)
def _get_collection(uri: str, db_name: str, collection_name: str):
    client = MongoClient(uri)
    collection = client[db_name][collection_name]
    collection.create_index(
        [("user_id", ASCENDING), ("date", ASCENDING)],
        unique=True,
    )
    return collection


class TimeRecordRepository:
    def __init__(
        self,
        mongo_uri: str | None = None,
        db_name: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        self.collection = _get_collection(
            mongo_uri or settings.MONGO_URI,
            db_name or settings.MONGO_DB_NAME,
            collection_name or settings.MONGO_COLLECTION,
        )

    def get_by_date(self, user_id: str, record_date: str) -> dict | None:
        document = self.collection.find_one({"user_id": user_id, "date": record_date})
        return self._without_mongo_id(document) if document else None

    def list_month(self, user_id: str, year: int, month: int) -> list[dict]:
        month_prefix = f"{year:04d}-{month:02d}-"
        cursor = self.collection.find(
            {"user_id": user_id, "date": {"$regex": f"^{month_prefix}"}}
        ).sort("date", ASCENDING)
        return [self._without_mongo_id(document) for document in cursor]

    def upsert(self, document: dict) -> dict:
        self.collection.replace_one(
            {"user_id": document["user_id"], "date": document["date"]},
            document,
            upsert=True,
        )
        return self._without_mongo_id(document)

    def delete(self, user_id: str, record_date: str) -> bool:
        result = self.collection.delete_one({"user_id": user_id, "date": record_date})
        return result.deleted_count == 1

    @staticmethod
    def _without_mongo_id(document: dict) -> dict:
        clean_document = dict(document)
        clean_document.pop("_id", None)
        return clean_document

