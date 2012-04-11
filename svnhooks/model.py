from trac.db.schema import Table, Column, Index
from datetime import datetime, timedelta
from trac.util.datefmt import from_utimestamp, to_utimestamp, utc

class SVNHooksModel(object):
    svnhooks_schema = [
                      Table('svnhooks', key='id')[
                        Column('id', type='int', auto_increment=True),
                        Column('path'),
                        Column('hook', type='text'),
                        Index(['path', 'hook'])]
                    ]  

    def __init__(self, env):
        self.env = env

    def _get_db(self, db=None):
        return db or self.env.get_read_db()
    
    def validate(self, path=None, hook=None):
        count = 0
        cursor = self._get_db().cursor()
        if path:
            cursor.execute("""SELECT count(*) FROM svnhooks WHERE path=%s and hook=%s""", (path, hook))
            (count, ) = cursor.fetchone()
        return count
    
    def get_by_id(self, id):
        cursor = self._get_db().cursor()
        cursor.execute("""SELECT path, hook FROM svnhooks WHERE id=%s""", (id,))
        return cursor.fetchone()
        
    def get_by_path(self, path):
        cursor = self._get_db().cursor()
        cursor.execute("""SELECT id, hook FROM svnhooks WHERE path=%s""", (path,))
        return list(cursor)
    
    def get_by_hook(self, hook):
        cursor = self._get_db().cursor()
        cursor.execute("""SELECT id, path FROM svnhooks WHERE hook=%s""", (hook,))
        return cursor.fetchone()
     
    def getall_path(self):
        data = {}
        cursor = self._get_db().cursor()
        cursor.execute("""SELECT * FROM svnhooks ORDER BY path, id""")
        for (id, path, hook) in cursor:
            if path not in data:
                data[path] = [(id, hook)]
            else:
                data[path].append((id, hook))
        return data

    def getall(self):
        data = {}
        cursor = self._get_db().cursor()
        cursor.execute("""SELECT * FROM svnhooks ORDER BY id, path""")
        for (id, path, hook) in cursor:
            if hook not in data:
                data[hook] = [(id, path)]
            else:
                data[hook].append((id, path))
        return data

    def insert(self, path, hook, db=None):
        @self.env.with_transaction(db)
        def do_insert(db):
            cursor = db.cursor()
            cursor.execute("""INSERT INTO svnhooks (path,hook) VALUES(%s,%s)""",\
                                 (path, hook))


    def update(self, new=None, old=None, db=None):
        @self.env.with_transaction(db)
        def do_update(db):
            cursor = db.cursor()
            if new and old:
                cursor.execute("""UPDATE svnhooks SET path=%s WHERE path=%s""", (new, old))
    
    def delete(self, id=None, db=None):
        @self.env.with_transaction(db)
        def do_delete(db):
            cursor = db.cursor()
            cursor.execute("DELETE FROM svnhooks WHERE id=%s", (id,))

