import json
import requests
from typing import Any


def chainable(method):
    def wrapper(self, *args, **kwargs):
        method(self, *args, **kwargs)
        return self

    return wrapper


class RequestBuilder:
    def __init__(self, executor=None):
        self.executor = requests.Session() if executor is None else executor
        self.url = None
        self.method = "GET"
        self.params = {}
        self.data = {}
        self.includes_ = []
        self.filters_ = {}

    @chainable
    def set_url(self, url) -> "RequestBuilder":
        self.url = url

    @chainable
    def set_method(self, method) -> "RequestBuilder":
        self.method = method

    @chainable
    def add_param(self, key, value) -> "RequestBuilder":
        self.params[key] = value

    @chainable
    def add_data(self, key, value) -> "RequestBuilder":
        self.data[key] = value

    @chainable
    def includes(self, value) -> "RequestBuilder":
        self.includes_.append(value)

    @chainable
    def filters(self, value) -> "RequestBuilder":
        self.filters_ = {**self.filters_, **value}

    def build(self) -> requests.PreparedRequest:
        json_params = json.dumps({"includes": self.includes_, "filters": self.filters_})
        self.add_param("json_params", json_params)
        return requests.Request(
            self.method, self.url, params=self.params, data=self.data
        ).prepare()

    def execute(self, cached=True) -> Any:
        return self.executor.send(self.build(), cached=cached)
