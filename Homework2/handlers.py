import datetime
import json

from Homework2_API import database


class Parser:
    # json. loads() takes in a string and returns a json object. json. dumps() takes in a json object and returns a string
    artist_keys = ['id', 'first_name', 'last_name', 'alias', 'birth_date']
    album_keys = ['id', 'name', 'release_date', 'fk_artist_id']

    def parse(self, py_object):
        json_string = json.dumps(py_object, default=self.converter)
        return json_string  # .encode()

    def converter(self, py_object):
        if isinstance(py_object, datetime.datetime):
            return str(py_object)

    def row_to_artist(self, row):
        artist = {}
        for index in range(len(row)):
            artist[self.artist_keys[index]] = row[index]
        return artist

    def row_to_album(self, row):
        album = {}
        for index in range(len(row)):
            album[self.album_keys[index]] = row[index]
        return album

    def rows_to_albums(self, rows):
        albums = []
        for row in rows:
            albums.append(self.row_to_album(row))
        return albums


class GET_handlers:
    def get_all(self, server_object, table):
        try:
            all_artists = []
            result = database.get_all(database.conn, table)
            if len(result) == 0:
                raise ValueError
            for row in result:
                row = parser.row_to_artist(row)
                all_artists.append(row)
            all_artists = parser.parse(all_artists)

            server_object.send_response(200)
            server_object.end_headers()
            server_object.wfile.write(all_artists.encode())
        except BaseException as e:
            print(e.with_traceback())
            server_object.send_response(404)
            server_object.end_headers()

    def artist_by_id(self, server_object, artist_id):
        try:
            result = database.get_artist_by_id(database.conn, 'artists', artist_id)[0]  # thorws idnexerror if not found
            artist = parser.row_to_artist(result)

            albums = database.get_albums_by_artist_id(database.conn, 'albums', artist_id)
            albums = parser.rows_to_albums(albums)

            artist['albums'] = albums
            artist = parser.parse(artist)

            artist = artist.encode()

            server_object.send_response(200)
            server_object.end_headers()
            server_object.wfile.write(artist)

        except IndexError as e:
            server_object.send_response(404)
            server_object.end_headers()

    def albums_by_artist_id(self, server_object, artist_id):
        try:
            if not database.check_exists(database.conn, 'artists', artist_id):
                raise Exception
            list_result = database.get_albums_by_artist_id(database.conn, 'albums', artist_id)
            albums = parser.rows_to_albums(list_result)
            albums = parser.parse(albums)
            albums = albums.encode()

            if len(albums) == 0:
                raise ValueError

            server_object.send_response(200)
            server_object.end_headers()
            server_object.wfile.write(albums)
        except ValueError as e:  # no albms
            server_object.send_response(204)
            server_object.end_headers()
        except Exception as e:  # no artist
            server_object.send_response(404)
            server_object.end_headers()


class POST_handlers():
    def post_albums(self, server_object, albums, artist_id):
        try:
            for album in albums:
                album['fk_artist_id'] = artist_id
                database.create(database.conn, 'albums', album)
            database.conn.commit()

            server_object.send_response(201)
            server_object.end_headers()
        except database.pyodbc.IntegrityError as e:  # artist not exists
            server_object.send_response(404)
            server_object.end_headers()
        except database.pyodbc.ProgrammingError as e:  # bad req
            server_object.send_response(400)
            server_object.end_headers()
        except:
            server_object.send_response(500)
            server_object.end_headers()

    def post_artist(self, server_object, artist):
        try:
            database.create(database.conn, 'artists', artist)
            database.conn.commit()

            server_object.send_response(201)
            server_object.end_headers()
        except database.pyodbc.ProgrammingError as e:  # bad req
            server_object.send_response(400)

    '''PUT
    /artists/{id}/albums   collection
    /albums/{id}'''


class PUT_handlers:
    def put_album(self, server_object, album, album_id):
        try:
            album = json.loads(album)
            print(album)
            affected_rows = database.update(database.conn, 'albums', album, 'id', album_id)
            database.conn.commit()
            if affected_rows <= 0:
                raise Exception

            server_object.send_response(204)
            server_object.end_headers()

        except database.pyodbc.ProgrammingError as e:  # bad req
            server_object.send_response(400)
            server_object.end_headers()
        except Exception as e:
            server_object.send_response(404)
            server_object.end_headers()

    def put_albums_by_artist_id(self, server_object, albums, artist_id):
        try:
            albums = json.loads(albums)
            affected_rows = 0
            for album in albums:
                print(album)
                affected_rows += database.update(database.conn, 'albums', album, 'fk_artist_id', artist_id, 'id',
                                                 album['id'])
            database.conn.commit()

            if affected_rows <= 0:
                raise Exception

            server_object.send_response(204)
            server_object.end_headers()

        except database.pyodbc.ProgrammingError as e:  # bad req
            server_object.send_response(400)
            server_object.end_headers()
        except Exception as e:
            server_object.send_response(404)
            server_object.end_headers()

    # /artists/{id}
    # /artists/{id}/albums    collection


class DELETE_handlers:
    def delete_artist_by_id(self, server_object, artist_id):
        try:
            affected_row = database.delete(database.conn, 'artists', 'id', artist_id)
            print(affected_row)
            if affected_row <= 0:
                raise database.pyodbc.IntegrityError
            database.conn.commit()
            server_object.send_response(204)
            server_object.end_headers()

        except database.pyodbc.IntegrityError as e:
            print(e)
            server_object.send_response(404)
            server_object.end_headers()
        except Exception as e:
            server_object.send_response(500)
            server_object.end_headers()

    def delete_albums_by_artist_id(self, server_object, artist_id):
        try:
            if not database.check_exists(database.conn, 'artists', artist_id):
                raise database.pyodbc.IntegrityError

            database.delete(database.conn, 'artists', 'fk_artist_id', artist_id)
            database.conn.commit()

            server_object.send_response(204)
            server_object.end_headers()

        except database.pyodbc.IntegrityError as e:  # not artist
            server_object.send_response(404)
            server_object.end_headers()
        except Exception as e:
            server_object.send_response(500)
            server_object.end_headers()


parser = Parser()
get_handler = GET_handlers()
post_handler = POST_handlers()
put_handler = PUT_handlers()
delete_handler = DELETE_handlers()
