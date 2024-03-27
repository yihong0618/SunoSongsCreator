import argparse
import contextlib
import json
import os
import re
import time
from http.cookies import SimpleCookie
from typing import Tuple
import random

from curl_cffi import requests
from curl_cffi.requests import Cookies
from fake_useragent import UserAgent
from requests import get as rget
from rich import print
from typing import Union

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

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

MUSIC_GENRE_LIST = [
    "African",
    "Asian",
    "South and southeast Asian",
    "Avant-garde",
    "Blues",
    "Caribbean and Caribbean-influenced",
    "Comedy",
    "Country",
    "Easy listening",
    "Electronic",
    "Folk",
    "Hip hop",
    "Jazz",
    "Latin",
    "Pop",
    "R&B and soul",
    "Rock",
]


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
        # make the song_info_dict global since we can get the lyrics and song name first
        self.song_info_dict = {}
        # now data
        self.now_data = {}

    def _get_auth_token(self):
        response = self.session.get(get_session_url, impersonate=browser_version)
        data = response.json()
        r = data.get("response")
        sid = None
        if r:
            sid = r.get("last_active_session_id")
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
        return int(r.json()["total_credits_left"] / 10)

    def _parse_lyrics(self, data: dict) -> Tuple[str, str]:
        song_name = data.get("title", "")
        mt = data.get("metadata")
        if (
            not mt
        ):  # Remove checking for title because custom songs have no title if not specified
            return "", ""
        lyrics = re.sub(r"\[.*?\]", "", mt.get("prompt"))
        return song_name, lyrics

    def _fetch_songs_metadata(self, ids):
        id1, id2 = ids[:2]
        url = f"https://studio-api.suno.ai/api/feed/?ids={id1}%2C{id2}"
        response = self.session.get(url, impersonate=browser_version)
        data = response.json()
        if type(data) == dict:
            if data.get("detail", "") == "Unauthorized":
                print("Token expired, renewing...")
                self.retry_time += 1
                if self.retry_time > 2:
                    song_name, lyric = self._parse_lyrics(self.now_data[0])
                    self.song_info_dict["song_name"] = song_name
                    self.song_info_dict["lyric"] = lyric
                    self.song_info_dict["song_url"] = (
                        f"https://audiopipe.suno.ai/?item_id={id1}"
                    )
                    print("will sleep 30 and try to download")
                    time.sleep(30)
                    # Done here
                    return True
                self._renew()
                time.sleep(5)
                return False
            else:
                data = [data]
        # renew now data
        self.now_data = data
        try:
            for d in data:
                # only get one url for now TODO: See if possible for both urls
                # and early return
                if audio_url := d.get("audio_url"):
                    song_name, lyric = self._parse_lyrics(d)
                    self.song_info_dict["song_name"] = song_name
                    self.song_info_dict["lyric"] = lyric
                    self.song_info_dict["song_url"] = audio_url
                    return True
            return False
        except Exception as e:
            print(e)
            # since we only get the music_id is ok
            # so we can make the id here and sleep some time
            print("Will sleep 45s and get the music url")
            time.sleep(45)
            song_name, lyric = self._parse_lyrics(self.now_data[0])
            self.song_info_dict["song_name"] = song_name
            self.song_info_dict["lyric"] = lyric
            self.song_info_dict["song_url"] = (
                f"https://audiopipe.suno.ai/?item_id={id1}"
            )
            # Done here
            return True

    def get_songs(
        self,
        prompt: str,
        tags: Union[str, None] = None,
        title: str = "",
        is_custom: bool = False,
    ) -> dict:
        url = f"{base_url}/api/generate/v2/"
        self.session.headers["user-agent"] = ua.random
        payload = {
            "gpt_description_prompt": prompt,
            "mv": "chirp-v3-0",
            "prompt": "",
            "make_instrumental": False,
        }
        if is_custom:
            payload["prompt"] = prompt
            payload["gpt_description_prompt"] = ""
            payload["title"] = title
            if not tags:
                payload["tags"] = random.choice(MUSIC_GENRE_LIST)
            else:
                payload["tags"] = tags
            print(payload)
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
            song_info = self._fetch_songs_metadata(request_ids)
            # spider rule
            if sleep_time > 2:
                time.sleep(sleep_time)
                sleep_time -= 2
            else:
                time.sleep(2)

            if not song_info:
                print(".", end="", flush=True)
            else:
                break
        # keep the song info dict as old api
        return self.song_info_dict

    def save_songs(
        self,
        prompt: str,
        output_dir: str = "./output",
        tags: Union[str, None] = None,
        title: Union[str, None] = None,
        is_custom: bool = False,
    ) -> None:
        mp3_index = 0
        try:
            self.get_songs(
                prompt, tags=tags, title=title, is_custom=is_custom
            )  # make the info dict
            song_name = self.song_info_dict["song_name"]
            lyric = self.song_info_dict["lyric"]
            link = self.song_info_dict["song_url"]
        except Exception as e:
            print(e)
            raise
        with contextlib.suppress(FileExistsError):
            os.mkdir(output_dir)
        print()
        while os.path.exists(os.path.join(output_dir, f"suno_{mp3_index}.mp3")):
            mp3_index += 1
        print(link)
        response = rget(link, allow_redirects=False, stream=True)
        if response.status_code != 200:
            raise Exception("Could not download song")
        # save response to file
        with open(
            os.path.join(output_dir, f"suno_{mp3_index + 1}.mp3"), "wb"
        ) as output_file:
            for chunk in response.iter_content(chunk_size=1024):
                # If the chunk is not empty, write it to the file.
                if chunk:
                    output_file.write(chunk)
        if not song_name:
            song_name = "Untitled"
        with open(
            os.path.join(output_dir, f"{song_name.replace(' ', '_')}.lrc"),
            "w",
            encoding="utf-8",
        ) as lyric_file:
            lyric_file.write(f"{song_name}\n\n{lyric}")


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
    parser.add_argument(
        "--is_custom",
        dest="is_custom",
        action="store_true",
        help="use custom mode, need to provide title and tags",
    )
    parser.add_argument(
        "--title",
        help="Title of the song",
        type=str,
        default="",
    )
    parser.add_argument(
        "--tags",
        help="Tags of the song",
        type=str,
        default="",
    )

    args = parser.parse_args()

    # Create song generator
    # follow old style
    song_generator = SongsGen(
        os.environ.get("SUNO_COOKIE") or args.U,
    )
    print(f"{song_generator.get_limit_left()} times left")
    song_generator.save_songs(
        prompt=args.prompt,
        output_dir=args.output_dir,
        title=args.title,
        tags=args.tags,
        is_custom=args.is_custom,
    )


if __name__ == "__main__":
    main()
