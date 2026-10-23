from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.observability import guarded


class MongoAdapter:
    def __init__(self, settings):
        ms = int(settings.timeout_seconds*1000)
        self.client = MongoClient(settings.mongo_uri.get_secret_value(), connect=False,
                                  serverSelectionTimeoutMS=ms, connectTimeoutMS=ms,
                                  socketTimeoutMS=ms, timeoutMS=ms)
        self.collection = self.client[settings.mongo_database].equipos
        self.projection = dict.fromkeys(["codigo_fifa", "nombre", "confederacion", "entrenador", "ranking_fifa"], 1)

    @staticmethod
    def transform(document):
        return {"id": str(document.pop("_id")), **document}

    @guarded("mongodb", PyMongoError)
    def get_team(self, code):
        doc = self.collection.find_one({"codigo_fifa": code}, self.projection)
        return self.transform(doc) if doc else None

    @guarded("mongodb", PyMongoError)
    def list_teams(self, after, limit, confederation):
        filters = {"codigo_fifa": {"$gt": after}} if after else {}
        if confederation:
            filters["confederacion"] = confederation
        return [self.transform(doc) for doc in self.collection.find(filters, self.projection)
                .sort("codigo_fifa", 1).limit(limit+1)]

    @guarded("mongodb", PyMongoError)
    def ping(self):
        self.client.admin.command("ping")

    def close(self):
        self.client.close()
