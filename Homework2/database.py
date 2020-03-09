import pyodbc as pyodbc

conn = pyodbc.connect(
    "Driver=SQL Server Native Client 11.0;"
    "Server=DESKTOP-AK3TG96\\SQLEXPRESS;"
    "Database=API_Database;"
    "Trusted_Connection=yes;"
)


def get_artist_by_id(conn, table,artist_id):
    cursor = conn.cursor()
    cursor.execute(f"select * from {table} WHERE id={artist_id}")
    return [row for row in cursor]

def get_all(conn,table):
    cursor = conn.cursor()
    cursor.execute(f'select * from {table}')
    return [row for row in cursor]

def get_albums_by_artist_id(conn,table,artist_id):
    cursor = conn.cursor()
    cursor.execute(f"select * from {table} WHERE fk_artist_id={artist_id}")
    return [row for row in cursor]


def create(conn, table, py_object):
    cursor = conn.cursor()
    sql = f'INSERT INTO {table}('
    values = 'values('
    for key, value in py_object.items():
        sql += f'{key}, '
        values += f"'{value}', "
    sql = sql[0: len(sql) - 2]
    values = values[0:len(values) - 2]
    sql += ') '
    values += ');'
    sql += values
    print(sql)
    cursor.execute(sql)


def update(conn, table, py_object,identifier_key,identifier,identifier2_key='',identifier2=''):
    cursor = conn.cursor()
    sql = f'UPDATE {table} SET '
    setters = ''
    values_list = []
    for key, value in py_object.items():
        if key=='id':
            continue
        setters += f'{key} =?, '
        values_list.append(value)
    setters = setters[0:len(setters) - 2]
    condition = f' WHERE {identifier_key}={identifier}'
    if identifier2!='' and identifier2_key!='':
        condition+= f' AND {identifier2_key}={identifier2}'
    sql += setters + condition + ';'
    cursor.execute(sql, tuple(values_list))
    print(sql)
    return cursor.rowcount


def check_exists(conn,table,obj_id):
    cursor = conn.cursor()
    sql = f'SELECT 1 FROM {table} WHERE id={obj_id}'
    cursor.execute(sql)
    results = [row for row in cursor]
    if results:
        return True
    return False

def delete(conn,table,identifier_key,identifier):
    cursor = conn.cursor()
    sql = f'DELETE FROM {table} WHERE {identifier_key}={identifier};'
    cursor.execute(sql)
    print(sql)
    print(cursor.rowcount)
    return cursor.rowcount

'''
GET /artists/{id}
    /artists/{id}/albums


PUT
    /artists/{id}/albums   collection
    /albums/{id}
DELETE
    /artists/{id}
    /artists/{id}/albums    collection
'''
