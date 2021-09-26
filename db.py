from pymongo import MongoClient, errors
from pymongo.cursor import Cursor

from typing import Optional, Union, Dict


class DataBase:
    def __init__(self, db_uri: str, db_name: str):
        try:
            self.client = MongoClient(db_uri, connect=False)
        except errors.ConnectionFailure:
            exit('Can\'t connect to server!')

        self.db = self.client[db_name]

    def add_user(self, user_id: int) -> str:
        return self.db.users.insert_one({'user_id': user_id, 'ashyq': {}}).inserted_id

    def get_user(self, user_id: Optional[int]=None) -> Union[Cursor, Dict]:
        if user_id:
            return self.db.users.find_one({'user_id': user_id})

        return self.db.users.find({})

    def edit_user(self, user_id: int, data: dict) -> int:
        return self.db.users.update_one({'user_id': user_id}, {'$set': data}).modified_count

    def delete_user(self, user_id: Optional[int]=None) -> int:
        if user_id:
            return self.db.users.delete_many({}).deleted_count

        return self.db.users.delete_one({'user_id': user_id}).deleted_count
