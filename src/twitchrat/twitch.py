# local
from twitchrat.globals import twitch_auth_url, twitch_client_id, twitch_client_secret, twitch_base_api_url

# 3rd party
import requests

class Twitch:

    def __init__(self):
        # Auth only once per instance
        self.access_token = self.access_token_get()

    def _api(self, api: str, params: list):
        return requests.get(f"{twitch_base_api_url}/{api}",
                            params=params,
                            headers={"Authorization": f"Bearer {self.access_token}",
                                     "Client-Id": twitch_client_id})

    def access_token_get(self) -> int:
        data = {
            "client_id": twitch_client_id,
            "client_secret": twitch_client_secret,
            "grant_type": "client_credentials"
        }

        r = requests.post(twitch_auth_url, data=data)
        return r.json()["access_token"]

    def streamer_id_get(self, streamer:str) -> int:
        result = self._api(api="users", params={"login": streamer})
        return result.json()["data"][0]["id"]

    def stream_get(self, streamer: str) -> dict:
        streamer_id = self.streamer_id_get(streamer=streamer)
        result = self._api(api="streams", params={"user_id": streamer_id})
        json = result.json()
        if "data" in json:
            if len(json['data']):
                return json['data'][0]
        return {}

    def vods_get(self, streamer:str) -> list:
        streamer_id = self.streamer_id_get(streamer=streamer)
        result = self._api(api="videos", params={"user_id": streamer_id})
        return result.json()["data"]

