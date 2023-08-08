"""
copy from https://gitee.com/huayunxm/huayun-sign-demo/blob/main/python/chinac/chinac_open_api.py

openapi接口
执行完do后会重置参数
不会重置设置的accessKeyId、accessKeySecret、openApiUrl
"""
import base64
import hashlib
import hmac
import json
import time
import urllib.parse
import urllib.request


class ChinacOpenApi:
    """初始化"""

    def __init__(self, access_key_id, access_key_secret):
        super(ChinacOpenApi, self).__init__()
        # 用户Access Key，可以通过用控新增、查看
        self._access_key_id = access_key_id

        # 用户Access Key Secret，可以通过用控新增、查看
        self._access_key_secret = access_key_secret

        # openapi通信地址地址，默认线上v2版，可以通过setOpenApiUrl修改
        # 结尾不含/
        self.open_api_url = 'https://api.chinac.com/v2'

        # 处理后的openapi通信地址
        self.request_url = ''

        # 请求方式，默认GET，可以通过setHttpMethod修改
        # 支持的有GET、POST、PUT等
        self.http_method = 'GET'

        # 请求操作Action名称，如DescribeInstances
        self.action = ''

        # 请求参数数组，键值对应请求参数名称和值，如：
        # {'Region': 'a', 'ProductStatus': 'NORMAL'}
        self.params = None

        # json参数，一般用于POST、PUT
        self.json_body = None

        # 请求头数组
        self.headers = {}

    # 修改openapi默认通信地址
    def set_open_api_url(self, open_api_url):
        self.open_api_url = open_api_url

    # 修改修改请求方式
    def set_http_method(self, http_method):
        self.http_method = http_method

    # 设置操作方法Action
    def set_action(self, action):
        self.action = action

    # 设置请求参数
    def set_request_params(self, params):
        self.params = params

    # 请求并返回结果
    def do(self):
        self._generate_headers()
        self._dealParams()
        res = self._request()
        self._refresh()
        return res

    # 生成请求头
    def _generate_headers(self):
        self.headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept-Encoding': '*',
            'Date': time.strftime("%Y-%m-%dT%H:%M:%S +0800", time.localtime())
        }

    # 处理参数，生成通信签名等
    def _dealParams(self):
        yparams = {
            'Action': self.action,
            'Version': '1.0',  # 目前固定1.0
            'AccessKeyId': self._access_key_id,
            'Date': self.headers['Date']
        }
        params = yparams.copy()
        if self.params:
            if self.http_method == 'GET':
                params.update(self.params)
            else:
                self.json_body = json.dumps(self.params).encode(encoding='UTF8')
        # 生成签名，更新url
        res = self._generate_signature(params)
        self.request_url = self.open_api_url + '?' + res['query'] + '&Signature=' + res['signature']

    # 生成签名
    def _generate_signature(self, params):
        sign_string = [self.http_method, "\n"]
        query = self._percent_urlencode_params(params)
        # md5加密参数
        m = hashlib.md5()
        m.update(bytearray(query, 'utf-8'))
        sign_string.append(m.hexdigest())
        sign_string.append("\n")
        sign_string.append(self.headers['Content-Type'])
        sign_string.append("\n")
        sign_string.append(self._percent_urlencode_str(self.headers['Date']))
        sign_string.append("\n")
        sign_string = ''.join(sign_string)
        signature = self._percent_urlencode_str(self._sha_hmac256_signature(sign_string))
        return {'query': query, 'signature': signature}

    # encodeurl参数
    def _percent_urlencode_params(self, params):
        urlstr = urllib.parse.urlencode(params)
        return self._percent_encode(urlstr)

    # encodeurl字符串
    def _percent_urlencode_str(self, urlstr):
        urlstr = urllib.parse.quote(urlstr)
        return self._percent_encode(urlstr)

    # 转成url通信标准RFC 3986
    @staticmethod
    def _percent_encode(urlstr):
        urlstr = urlstr.replace('+', '%20')
        urlstr = urlstr.replace('*', '%2A')
        urlstr = urlstr.replace('%7E', '~')
        return urlstr

    # base64 hmac256加密
    def _sha_hmac256_signature(self, sign_string):
        h = hmac.new(bytearray(self._access_key_secret, 'utf-8'), bytearray(sign_string, 'utf-8'), hashlib.sha256)
        signature = str(base64.encodebytes(h.digest()).strip(), 'utf-8')
        return signature

    # 请求通信
    def _request(self):
        req = urllib.request.Request(
            self.request_url,
            data=self.json_body,
            headers=self.headers,
            method=self.http_method)
        res = urllib.request.urlopen(req)
        return {'Status': res.getcode(), 'Info': res.read().decode('utf-8')}

    # 请求后重置参数
    def _refresh(self):
        self.request_url = ''
        self.http_method = 'GET'
        self.action = ''
        self.params = None
        self.json_body = None
        self.headers = {}
