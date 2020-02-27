import http.client
import json
import time
from urllib import request
import urllib.parse as urlparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import re
from urllib.request import Request, urlopen


with open('config.json', 'r') as config_file:
    configuration = json.load(config_file)
    api_football_headers = configuration['api_football_headers']
    SOP_headers = configuration['SOP_headers']
    serie_a_headers = configuration['serie_a_headers']

serie_a_league_id = '891'  # 15-16 season
get_teams_url = f'https://api-football-v1.p.rapidapi.com/v2/teams/league/{serie_a_league_id}'



class Parser():
    # json. loads() takes in a string and returns a json object. json. dumps() takes in a json object and returns a string
    def parse_teams(self, object):  # gets ENCODED data, returns ENCODED
        object = object.decode('utf-8')
        object = json.loads(object)
        teams_list = []
        print(object)
        for team in object['api']['teams']:
            teams_list.append(team['name'])
        teams_list = json.dumps(teams_list)  # turn to json string
        print(teams_list)
        teams_list = teams_list.encode()
        print(teams_list)
        return teams_list

    def parse_players(self, big_object):  # UNENCODED, ENCODED
        # object = big_object.decode('utf-8')
        big_object = json.loads(big_object)
        players_list = []
        for json_object in big_object:  # two teams -> two objects
            for player in json_object['data']['players']:
                if player['name'] == '':
                    players_list.append(player['fullname'])
                elif player['fullname'] == '':
                    players_list.append(player['name'])
                else:
                    players_list.append(f"{player['name']} {player['fullname']}")
        players_list = json.dumps(players_list)
        players_list = players_list.encode()
        print(players_list)
        return players_list

    def parse_log(self, metrics):
        metrics_dict = {}  # avg_latency, total_requests
        for endpoint, latency in metrics:
            if endpoint not in metrics_dict:
                metrics_dict[endpoint] = {
                    "avg_latency": float(latency),
                    "total_requests": 1
                }
            else:
                metrics_dict[endpoint]['avg_latency'] *= metrics_dict[endpoint]['total_requests']
                metrics_dict[endpoint]['avg_latency'] += float(latency)
                metrics_dict[endpoint]['total_requests'] += 1
                metrics_dict[endpoint]['avg_latency'] /= metrics_dict[endpoint]['total_requests']
        return str(metrics_dict).encode() # send encoded

class Logger:
    def log(self, endpoint, latency, request_text, data):
        separator = '-----------------------'
        text_to_log = f'ENDPOINT=/{endpoint} LATENCY={latency}\n{request_text}RESPONSE={data}\n{separator}\n\n'
        with open('log.txt', 'a') as log_file:
            log_file.write(text_to_log)

    def log_api(self, api, latency, succes):
        with open('services_log.json', 'r+') as api_log:
            api_stats = json.load(api_log)
            api_log.seek(0)

            api_stats[api]['average-latency'] *= api_stats[api]['total-requests']  # total latency
            api_stats[api]['total-requests'] += 1
            api_stats[api]['average-latency'] += latency
            api_stats[api]['average-latency'] /= api_stats[api]['total-requests']  # updated
            if succes == 1:
                api_stats[api]['successful-requests'] += 1
            else:
                api_stats[api]['failed-requests'] += 1
            json.dump(api_stats, api_log, indent=4)


parser = Parser()
logger = Logger()

regex = re.compile('ENDPOINT=(/[a-zA-Z]*) LATENCY=([0-9]*\.[0-9]*)')


class FootballServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or '':
            self.send_html_file()
        elif self.path == '/teams':
            self.send_teams()
        elif self.path.count('players') > 0:
            self.send_players()
        elif self.path.count('stats') > 0:
            self.send_player_stats()
        elif self.path.count('metrics') > 0:
            self.send_metrics()

    def send_html_file(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(bytes(html_file_content, 'utf-8'))

    def send_teams(self):
        # print(self.)
        start = time.time()
        request_text = f'{self.raw_requestline.decode("utf-8")}{self.headers}'

        req = Request(get_teams_url)
        for key, value in api_football_headers.items():
            req.add_header(key, value)

        api_start = time.time()
        response = urlopen(req)
        if response.getcode() == 200:
            data = response.read()
            api_end = time.time()
            api_latency = api_end - api_start

            data = parser.parse_teams(data)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(data)
            end = time.time()
            latency = end - start
            endpoint = 'teams'
            logger.log(endpoint, latency, request_text, data)
            logger.log_api('api-football', api_latency, 1)

        else:  # failed
            api_end = time.time()
            api_latency = api_end - api_start
            data = 'Not Found'
            self.send_response(404)
            self.end_headers()
            self.wfile.write(data)
            end = time.time()
            latency = end - start
            endpoint = 'teams'
            logger.log(endpoint, latency, request_text, data)
            logger.log_api('api-football', api_latency, 0)

    def get_players(self, team_url, conn):
        api_start = time.time()
        conn.request("GET", team_url, headers=SOP_headers)
        res = conn.getresponse()
        data = res.read()
        api_end = time.time()
        api_latency = api_end - api_start
        return [data, api_latency]

    def send_players(self):
        start = time.time()
        request_text = f'{self.raw_requestline.decode("utf-8")}{self.headers}'
        conn = http.client.HTTPSConnection("sportsop-soccer-sports-open-data-v1.p.rapidapi.com")

        parsed_url = urlparse.urlparse(self.path)
        team1 = urlparse.parse_qs(parsed_url.query)['team1'][0]
        team2 = urlparse.parse_qs(parsed_url.query)['team2'][0]
        players_team1_url = f'/v1/leagues/serie-a/seasons/19-20/teams/{team1}/players'
        players_team2_url = f'/v1/leagues/serie-a/seasons/19-20/teams/{team2}/players'

        team1_players, api1_latency = self.get_players(players_team1_url, conn)[0:2]
        team2_players, api2_latency = self.get_players(players_team2_url, conn)[0:2]

        conn.close()
        json_string = ''
        if team1_players == '' or team2_players == '':
            if team1_players == '':
                logger.log_api('sop', api1_latency, 0)
            else:
                logger.log_api('sop', api1_latency, 1)
            if team1_players == '':
                logger.log_api('sop', api2_latency, 0)
            else:
                logger.log_api('sop', api2_latency, 1)

            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Players not found')
        else:
            json_string = f'[{team1_players.decode("utf-8")}, {team2_players.decode("utf-8")}]'
            json_string = parser.parse_players(json_string)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json_string)

        end = time.time()
        latency = end - start
        print(json_string)
        endpoint = 'players'
        logger.log(endpoint, latency, request_text, json_string)
        logger.log_api('sop', api1_latency, 1)
        logger.log_api('sop', api2_latency, 1)

    def send_player_stats(self):
        start = time.time()
        request_text = f'{self.raw_requestline.decode("utf-8")}{self.headers}'
        parsed_url = urlparse.urlparse(self.path)
        team1 = urlparse.parse_qs(parsed_url.query)['team1'][0]
        team2 = urlparse.parse_qs(parsed_url.query)['team2'][0]
        player_name = urlparse.parse_qs(parsed_url.query)['player_name'][0]
        player_name = player_name.replace(" ", "%20")

        conn = http.client.HTTPSConnection("heisenbug-seriea-live-scores-v1.p.rapidapi.com")

        api_start = time.time()
        conn.request("GET", f'/api/serie-a/match/player?player={player_name}&team1={team1}&team2={team2}',
                     headers=serie_a_headers)

        res = conn.getresponse()
        content = res.read()

        api_end = time.time()
        api_latency = api_end - api_start
        if res.getcode() == 200:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(content)
            logger.log_api('serie-a', api_latency, 1)
        else:
            self.send_response(404)
            self.end_headers()
            print(res.read())
            self.wfile.write(content)
            logger.log_api('serie-a', api_latency, 0)
        end = time.time()
        latency = end - start
        endpoint = 'stats'
        logger.log(endpoint, latency, request_text, content)

    def send_metrics(self):
        metrics = self.get_my_api_metrics()
        response = parser.parse_log(metrics)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(response)

    def get_my_api_metrics(self):
        with open('log.txt', 'r') as log_file:
            data = log_file.read()
            matches = regex.findall(data)
            return matches


html_file_content = ''
try:
    html_file_content = open('index.html').read()
except Exception as e:
    print(e)
print('Starting server')
http_football_server = HTTPServer(('localhost', 9000), FootballServer)
http_football_server.serve_forever()
