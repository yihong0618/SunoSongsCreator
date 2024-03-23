import argparse
import contextlib
import json
import os
import re
import time
from http.cookies import SimpleCookie
from typing import Tuple

from curl_cffi import requests
from curl_cffi.requests import Cookies
from fake_useragent import UserAgent
from requests import get as rget
from rich import print

ua = UserAgent(browsers=["edge"])

get_session_url = "https://clerk.suno.ai/v1/client?_clerk_js_version=4.70.5"
exchange_token_url = (
    "https://clerk.suno.ai/v1/client/sessions/{sid}/tokens/api?_clerk_js_version=4.70.0"
)

base_url = "https://studio-api.suno.ai"
browser_version = "edge101"

HEADERS = {
    "Origin": base_url,
    "Referer": base_url + "/",
    "DNT": "1",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "TE": "trailers",
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

    def _get_auth_token(self):
        response = self.session.get(get_session_url,
                                    impersonate=browser_version)
        data = response.json()
        r = data.get("response")
        sid = None
        if r:
            sid = r.get("last_active_session_id")
        if not sid:
            raise Exception("Failed to get session id")
        response = self.session.post(
            exchange_token_url.format(sid=sid), impersonate=browser_version
        )
        data = response.json()
        return data.get("jwt")

    def _renew(self):
        auth_token = self._get_auth_token()
        HEADERS["Authorization"] = f"Bearer {auth_token}"
        self.session.headers = HEADERS

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

    def _parse_lyrics(self, data: dict) -> Tuple[str, str]:
        song_name = data.get('title', '')
        mt = data.get('metadata')
        if not mt or not song_name:
            return '', ''
        lyrics = re.sub(r"\[.*?\]", "", mt.get('prompt'))
        return song_name, lyrics

    def _fetch_songs_metadata(self, ids):
        id1, id2 = ids[:2]
        url = f"https://studio-api.suno.ai/api/feed/?ids={id1}%2C{id2}"
        response = self.session.get(url, impersonate=browser_version)

        try:
            data = response.json()[0]
        except:
            if response.json().get("detail", "") == "Unauthorized":
                print("Token expired, renewing...")
                self._renew()
                return None, None
        data = response.json()
        print(data)
        rs = {
            'song_name': '',
            'lyric': '',
            'song_urls': []
        }
        for d in data:
            if s_url := d.get('audio_url'):
                rs['song_urls'].append(s_url)
        song_name, lyric = self._parse_lyrics(data[0])
        rs['song_name'] = song_name
        rs['lyric'] = lyric
        return rs

    def get_songs(self, prompt: str) -> dict:
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
        try_index = 0
        while True:
            if int(time.time() - start_wait) > 600:
                raise Exception("Request timeout")
            # TODOs support all mp3 here
            song_info = self._fetch_songs_metadata(request_ids)
            # spider rule
            time.sleep(1)
            try_index += 1
            # if try_index % 6 == 0:
            #     self.session.headers["Authorization"] = (
            #         f"Bearer {self._get_auth_token()}"
            #     )
            if len(song_info['song_urls']) != 2:
                print(".", end="", flush=True)
            else:
                return song_info

    def save_songs(
            self,
            prompt: str,
            output_dir: str,
    ) -> None:
        mp3_index = 0
        try:
            song_name, lyric, links = self.get_songs(prompt).values()
        except Exception as e:
            print(e)
            raise
        with contextlib.suppress(FileExistsError):
            os.mkdir(output_dir)
        print()
        for link in links:
            print(link)
            response = rget(link, stream=True)
            if response.status_code != 200:
                raise Exception("Could not download song")
            # save response to file
            with open(
                    os.path.join(output_dir, f"{mp3_index + 1} {song_name}.mp3"),
                    "wb"
            ) as output_file:
                for chunk in response.iter_content(chunk_size=1024):
                    # If the chunk is not empty, write it to the file.
                    if chunk:
                        output_file.write(chunk)
            mp3_index += 1
        with open(
                os.path.join(output_dir, f'{song_name}.lrc'), 'w',
                encoding='utf-8'
        ) as lyric_file:
            lyric_file.write(f'{song_name}\n\n{lyric}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-U", help="Auth cookie from browser", type=str,
                        default="")
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
