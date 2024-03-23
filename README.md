# SunoSongsCreator
About High quality songs generation by https://www.suno.ai/. Reverse engineered API.

## How to
- Login to https://app.suno.ai/ and generate some songs.
- Use `Chrome` or other browsers to inspect the network requests (F12 -> XHR).
- Clone this REPO -> `git clone https://github.com/yihong0618/SunoSongsCreator.git`
- XHR find cookie in this url -> https://clerk.suno.ai/v1/client?_clerk_js_version=4.70.5 
- Copy the cookie.
- Export SUNO_COOKIE='xxxxx'.

## Usage

```
python -m suno --prompt 'a big red dream song'
```

or
```
pip install -U suno_songs
```

```python
from suno import SongsGen
i = SongsGen('cookie') # Replace 'cookie'
print(i.get_limit_left())
i.save_songs("a blue cyber dream song", './output')
```

## Thanks

- All my 爱发电 sponsors https://afdian.net/a/yihong0618?tab=sponsor
