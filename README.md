# SunoSongsCreator
About High quality songs generation by https://www.suno.ai/. Reverse engineered API.

## How to
- Login to https://app.suno.ai/ and generate some songs.
- Use `Chrome` or other browsers to inspect the network requests (F12 -> XHR).
- Clone this REPO -> `git clone https://github.com/yihong0618/SunoSongsCreator.git`
- XHR find cookie in this url -> https://clerk.suno.ai/v1/client?_clerk_js_version=4.70.5 
- Copy the cookie.
- You can import the cookie using `export SUNO_COOKIE='<your-suno-cookie>'` or rename `.env.example` to `.env` and fill in `SUNO_COOKIE`.

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

Custom mode

```python
#you can use custom mode
from suno import SongsGen
i = SongsGen('cookie') # Replace 'cookie'
print(i.get_limit_left())
i.save_songs("大江东去，浪淘尽，千古风流人物。故垒西边，人道是、三国周郎赤壁。乱石穿空，惊涛拍岸，卷起千堆雪。江山如画，一时多少豪杰。遥想公瑾当年，小乔初嫁了，雄姿英发。", is_custom=True, title="custom", tags="轻松的R&B, BPM60, 小调, 电吉他、贝斯、键盘和轻鼓, 男性歌手") 
```

## Thanks

- All my 爱发电 sponsors https://afdian.net/a/yihong0618?tab=sponsor
