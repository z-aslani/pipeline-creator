import requests


class RequestUtil:
    @classmethod
    def send_post_request(cls, url, body=None, query_params=None, headers=None):
        response = requests.post(url, json=body, params=query_params, headers=headers)
        return response.json(), response.headers

    @classmethod
    def send_get_request(cls, url, headers, query_params=None):
        response = requests.get(url, params=query_params or {}, headers=headers)
        return response.json(), response.headers, response.status_code


class CloudflareClient:
    API_BASE_URL = 'https://api.cloudflar.com'
    X_AUTH_TOKEN = 'bTRPYxLRpGiszToEzMYw'

    @classmethod
    def foo(cls):
        pass
