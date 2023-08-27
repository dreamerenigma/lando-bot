import sqlite3

class DataBase:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.c = self.conn.cursor()

    def select_with_fetchone(self, cmd):
        self.c.execute(cmd)
        result = self.c.fetchone()
        return result

    def select_with_fetchall(self, cmd):
        self.c.execute(cmd)
        result = self.c.fetchall()
        return result

    def query(self, cmd):
        self.c.execute(cmd)
        self.conn.commit()