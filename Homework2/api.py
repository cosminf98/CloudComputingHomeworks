import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import re
from Homework2_API import database
import json
from urllib.parse import parse_qs
from Homework2_API import handlers
from Homework2_API.handlers import parser, get_handler, put_handler, delete_handler, post_handler

# hardcored for auth testing/simulation purposes
bearer_token = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwibWVzc2FnZSI6Inl' \
               'vdSdyZSBhIGN1cmlvdXMgb25lLCBhcmVuJ3QgeW91IiwiaWF0IjoxNTE2MjM5MDIyfQ.KSMGSM1lhfQkxKpxOXlwZA3FRiv8VGLxcq-SBlLjtRE'


class My_Server(BaseHTTPRequestHandler):

    def do_GET(self):
        artist_id = self.path.split('/')[2]
        if re.match('/artists/([0-9]+)/albums', self.path):
            get_handler.albums_by_artist_id(self, artist_id)
        elif re.match('/artists/([0-9]+)', self.path):
            get_handler.artist_by_id(self, artist_id)
        elif re.match('/artists/all',self.path):
            get_handler.get_all(self,'artists')

        else:
            self.send_response(400)


    def do_POST(self):
        artist_id = self.path.split('/')[1]
        length = int(self.headers.get('Content-Length'))
        body = json.loads(self.rfile.read(length).decode())
        print(body)
        if re.match('/(\d+)/albums', self.path):                #{id}/albums
            post_handler.post_albums(self, body, artist_id)
        elif re.match('^/artists', self.path):                  #artists
            post_handler.post_artist(self, body)

    def do_PUT(self):
        length = int(self.headers.get('Content-Length'))
        body = self.rfile.read(length).decode()
        url_id = self.path.split('/')[2]

        if re.match('/albums/[0-9]+', self.path):
            put_handler.put_album(self, body, url_id)
        elif re.match('/artists/[0-9]+/albums', self.path):
            print('match')
            put_handler.put_albums_by_artist_id(self, body, url_id)

    def do_DELETE(self):
        auth = self.headers.get('Authorization')
        if not auth or auth != bearer_token:
            print('unauth')
            self.send_response(401)
            self.end_headers()
        else:  # IS AUTHENTICATED
            print('auth')
            artist_id = self.path.split('/')[2]
            if re.match('/artists/[0-9]+', self.path):
                delete_handler.delete_artist_by_id(self, artist_id)
            elif re.match('/artists/[0-9]+/albums', self.path):
                delete_handler.delete_albums_by_artist_id(self, artist_id)


print('Starting Server...')
My_Server = HTTPServer(('localhost', 9000), My_Server)
My_Server.serve_forever()
