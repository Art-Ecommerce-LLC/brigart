from src.artapi.noco import Noco

class NocoDBManager:
    def __init__(self):
        self.noco_db = Noco()

    def get_noco_db(self):
        return self.noco_db

noco_db_manager = NocoDBManager()

def get_noco_db():
    return noco_db_manager.get_noco_db()