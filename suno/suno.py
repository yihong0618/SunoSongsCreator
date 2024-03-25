import argparse
import contextlib
import json
import os
import time
from rich import print
from http.cookies import SimpleCookie

from curl_cffi import requests
from requests import get as rget
from requests import Session as rsession
from curl_cffi.requests import Cookies
from fake_useragent import UserAgent

ua = UserAgent(browsers=["edge"])


get_session_url = "https://clerk.suno.ai/v1/client?_clerk_js_version=4.70.5"
exchange_token_url = (
    "https://clerk.suno.ai/v1/client/sessions/{sid}/tokens/api?_clerk_js_version=4.70.0"
)

base_url = "https://studio-api.suno.ai"
browser_version = "edge101"

HEADERS = {
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) \
        Gecko/20100101 Firefox/117.0",
}


class SongsGen:
    def __init__(self, cookie: str) -> None:
        self.session: requests.Session = requests.Session()
        HEADERS["user-agent"] = ua.random
        self.cookie = cookie
        self.session.cookies = self.parse_cookie_string(self.cookie)
        auth_token = self._get_auth_token()
        HEADERS["Authorization"] = f"Bearer {auth_token}"
        self.session.headers = HEADERS
        self.sid = None
        self.retry_time = 0

    def _get_auth_token(self):
        response = self.session.get(get_session_url, impersonate=browser_version)
        data = response.json()
        sid = data.get("response").get("last_active_session_id")
        if not sid:
            raise Exception("Failed to get session id")
        self.sid = sid
        response = self.session.post(
            exchange_token_url.format(sid=sid), impersonate=browser_version
        )
        data = response.json()
        return data.get("jwt")

    def _renew(self):
        response = self.session.post(
            exchange_token_url.format(sid=self.sid), impersonate=browser_version
        )
        print(response.json())
        self.session.headers["Authorization"] = f"Bearer {response.json().get('jwt')}"

    @staticmethod
    def parse_cookie_string(cookie_string):
        cookie = SimpleCookie()
        cookie.load(cookie_string)
        cookies_dict = {}
        for key, morsel in cookie.items():
            cookies_dict[key] = morsel.value
        return Cookies(cookies_dict)

    def get_limit_left(self) -> int:
        self.session.headers["user-agent"] = ua.random
        r = self.session.get(
            "https://studio-api.suno.ai/api/billing/info/", impersonate=browser_version
        )
        return int(r.json()["total_credits_left"] / 5)

    def _fetch_songs_metadata(self, ids):
        id1, id2 = ids[:2]
        url = f"https://studio-api.suno.ai/api/feed/?ids={id1}%2C{id2}"
        response = self.session.get(url, impersonate=browser_version)
        try:
            data = response.json()[0]
        except:
            if response.json().get("detail", "") == "Unauthorized":
                print("Token expired, renewing...")
                self.retry_time += 1
                if self.retry_time > 3:
                    raise Exception("Token expired")
                self._renew()
                time.sleep(5)
                return
            data = response.json()
        if song_url := data.get("audio_url"):
            # TODO support all mp3 here
            return song_url
        else:
            return None

    def get_songs(self, prompt: str) -> list:
        url = f"{base_url}/api/generate/v2/"
        self.session.headers["user-agent"] = ua.random
        payload = {
            "gpt_description_prompt": prompt,
            "mv": "chirp-v3-0",
            "prompt": "",
            "make_instrumental": False,
        }
        response = self.session.post(
            url,
            data=json.dumps(payload),
            impersonate=browser_version,
        )
        if not response.ok:
            print(response.text)
            raise Exception(f"Error response {str(response)}")
        response_body = response.json()
        songs_meta_info = response_body["clips"]
        request_ids = [i["id"] for i in songs_meta_info]
        start_wait = time.time()
        print("Waiting for results...")
        sleep_time = 10
        while True:
            if int(time.time() - start_wait) > 600:
                raise Exception("Request timeout")
            # TODOs support all mp3 here
            song_url = self._fetch_songs_metadata(request_ids)
            # spider rule
            if sleep_time > 2:
                time.sleep(sleep_time)
                sleep_time -= 2
            else:
                time.sleep(2)
            if not song_url:
                print(".", end="", flush=True)
            else:
                return [song_url]

    def save_songs(
        self,
        prompt: str,
        output_dir: str,
    ) -> None:
        mp3_index = 0
        try:
            links = self.get_songs(prompt)
        except Exception as e:
            print(e)
            raise
        with contextlib.suppress(FileExistsError):
            os.mkdir(output_dir)
        print()
        for link in links:
            while os.path.exists(os.path.join(output_dir, f"suno_{mp3_index}.mp3")):
                mp3_index += 1
            print(link)
            # using bare requests here.
            response = rget(link, stream=True)
            if response.status_code != 200:
                raise Exception("Could not download song")
            # save response to file
            with open(
                os.path.join(output_dir, f"suno_{mp3_index}.mp3"), "wb"
            ) as output_file:
                for chunk in response.iter_content(chunk_size=1024):
                    # If the chunk is not empty, write it to the file.
                    if chunk:
                        output_file.write(chunk)
            mp3_index += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-U", help="Auth cookie from browser", type=str, default="")
    parser.add_argument(
        "--prompt",
        help="Prompt to generate songs for",
        type=str,
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        help="Output directory",
        type=str,
        default="./output",
    )

    args = parser.parse_args()

    # Create song generator
    # follow old style
    song_generator = SongsGen(
        os.environ.get("SUNO_COOKIE") or args.U,
    )
    print(f"{song_generator.get_limit_left()} songs left")
    song_generator.save_songs(
        prompt=args.prompt,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
