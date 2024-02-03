from typing import Any, Union

import requests
import requests_cache

from .builder import RequestBuilder


class TopLogger:
    def __init__(self):
        self.base_url = "https://api.toplogger.nu/v1"
        self.session = requests_cache.CachedSession()

    def send(self, request: requests.PreparedRequest, cached: bool) -> Any:
        if not cached:
            res = self.session.send(request, force_refresh=True)
        else:
            res = self.session.send(request)
        if res.status_code != 200:
            raise Exception(f"[{res.status_code}]: {res.text}")
        return res.json()

    def gyms(self):
        return RequestBuilder(self).set_url(f"{self.base_url}/gyms")

    def gym(self, gym_id: Union[int, str]):
        return RequestBuilder(self).set_url(f"{self.base_url}/gyms/{gym_id}")

    def user(self, user_id: Union[int, str]):
        return RequestBuilder(self).set_url(f"{self.base_url}/users/{user_id}")

    def user_ascends(self, user_id: Union[int, str]):
        return (
            RequestBuilder(self)
            .set_url(f"{self.base_url}/ascends")
            .filters({"user": {"uid": user_id}})
        )

    def climbs(self, gym_id: Union[int, str]):
        return RequestBuilder(self).set_url(f"{self.base_url}/gyms/{gym_id}/climbs")

    def climb_stats(self, gym_id: Union[int, str], climb_id: Union[int, str]):
        return RequestBuilder(self).set_url(
            f"{self.base_url}/gyms/{gym_id}/climbs/{climb_id}/stats"
        )

    def groups(self, gym_id: Union[int, str]):
        return (
            RequestBuilder(self)
            .set_url(f"{self.base_url}/groups")
            .filters({"gym_id": gym_id, "live": True})
        )
