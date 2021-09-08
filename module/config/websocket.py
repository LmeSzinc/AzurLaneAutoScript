import json
import sys
from json import JSONDecodeError
from sys import stdin, stdout

from module.config.db import Database

sys.stdin.reconfigure(encoding='utf-8')


class WebsocketServer(Database):
    def response_error(self, msg):
        self.response({'query': 'error', 'data': str(msg)})

    def response(self, data):
        data = json.dumps(data, ensure_ascii=True, sort_keys=False, default=str)
        print(data)
        stdout.flush()  # Remember to flush

    def parse_query(self, message):
        query = message.get('query', None)
        request = message.get('data', None)
        assert query, 'Empty query method'
        assert request, 'Empty query data'

        if query == 'select_function':
            response = self.select_function(request)
        elif query == 'upsert_config':
            response = self.upsert_config(request)
            query = 'select_function'
        elif query == 'select_menu':
            response = self.select_menu(request)
        elif query == 'select_db':
            response = self.select_db(request)
        elif query == 'upsert_db':
            response = self.upsert_db(request)
            query = 'select_function'
        else:
            raise AssertionError(f'Unknown query: `{query}`')

        self.config_clear(request)
        response = {'query': query, 'data': response}
        return response

    def parse(self, message):
        """
        Args:
            message (str): Such as `{"query": "select_function", "data": {...}}`

        Returns:
            str: Json dumps into string.
        """
        try:
            message = json.loads(message)
        except JSONDecodeError:
            self.response_error(f'Invalid json input: {message}')
            return False
        if not isinstance(message, dict):
            self.response_error(f'Invalid json input: {message}')
            return False

        try:
            response = self.parse_query(message)
            self.response(response)
        except Exception as e:
            self.response_error(e)

    def listen(self):
        while True:
            line = stdin.readline().strip()
            self.parse(line)


if __name__ == '__main__':
    server = WebsocketServer()
    res = server.parse('{"query":"upsert_db","data":{"task":"Main","group":"_info","arg":"_info","lang":"zh-CN","name":"中文","help":"Main._info._info.help","type":"","value":"","row":1,"option":{},"config":"alas"}}')
    print(res)
