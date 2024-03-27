**补充了如下图三个参数详见下面的python使用**

<img src="https://github.com/wlhtea/SunoSongsCreator/assets/115779315/03c0193f-2944-4199-b0fd-5152eae329f4" width="300">


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

Added three parameters: prompt, tags, and title. See the website for details and open Custom Mode to see the meaning of the three parameters.
The original prompt has been changed to gptprompt.
![image](https://github.com/wlhtea/SunoSongsCreator/assets/115779315/209b0d93-6e9c-4236-a3a3-88e782afd935)

```python
from suno import SongsGen
cookie = 'cookie'
i = SongsGen(cookie)
print(i.get_limit_left())
# i.save_songs(gptprompt="a blue cyber dream song", output_dir='./output')
i.save_songs(title="夏天好像不曾离开 Summer Never Left",tags="轻松的R&B, BPM60, 小调, 电吉他、贝斯、键盘和轻鼓, 男性歌手, 深情温暖的夏日风情\n",prompt=
"[Intro]\n(Instrumental)\n\n[Verse 1]\n城市的灯光慢慢亮起，\n夕阳在窗外悄悄退去。\n心中的热情从未减退，\n夏天的回忆，甜蜜温馨。\n\n[Chorus]\n夏天好像不曾离开，\n你的笑容照亮了我的世界。\n在这宁静的夜晚，\n感受自由，和你一起飞翔。\n\n[Verse 2]\n赤脚踏在温暖的沙滩，\n潮水轻拍，和风轻柔相伴。\n每个夏日黄昏都如此宁静，\n你的每一个吻，都是我的信仰。\n\n[Chorus]\n夏天好像不曾离开，\n温暖的怀抱，爱情的味道。\n在这自由的空气中，\n和你共舞，直到时间尽头。\n\n[Bridge]\nSunset fades, but love stays (夕阳消逝，爱永存),\nHand in hand, through endless days (手牵手，穿越无尽的日子).\nIn every breath, in every gaze (在每一次呼吸，每一次凝视),\nOur summer never fades away (我们的夏天永不消逝).\n\n[Outro]\n(Instrumental)", output_dir='./output')
```
or
```python
from suno import SongsGen
i = SongsGen('cookie') # Replace 'cookie'
print(i.get_limit_left())
i.save_songs(gptprompt="a blue cyber dream song") // The default save path is . /output
```


## Thanks

- All my 爱发电 sponsors https://afdian.net/a/yihong0618?tab=sponsor
