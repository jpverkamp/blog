---
title: "Automated transcripts from video with Whisper(.cpp)"
date: '2023-03-27 00:01:00'
programming/languages:
- Python
programming/topics:
- AI
- ML
- OpenAI
- Transcription
- ffmpeg
- Video
- Audio
- Text
- LLM
---
I tend to be something of a digital packrat. If there's interesting data somewhere, I'll collect it *just in case* I want to do something with it. 

Helpful? Usually not. But it does lead to some interesting scripts. 

In this case, I have a site that hosts videos. I want to download those videos and get a text based transcription of them. With new AI tools, that shouldn't be hard at all. Let's give it a try!

{{<toc>}}

<!--more-->

## Installing whisper.cpp

First up, [OpenAI's whisper](https://openai.com/research/whisper). It's a audio to text model that does exactly what I'm looking for. Really, there are two main wrappers around the model itself:

* [whisper](https://github.com/openai/whisper) - the original Python version
* [whisper.cpp](https://github.com/ggerganov/whisper.cpp) - a port using the same models, but in C++

I've used the Python version at first and it works fine. It's also a bit more compatible, it doesn't mind taking an mp3 in and will convert it behind the scenes. But I'm primarily writing this on an M1 mac. Out of the box, whisper.cpp supports the NEON chipset and (being C++) is just generally faster. 

So let's set that up instead, since (at least with my current setup) it's really not so bad:

```zsh
# Checkout
┌ ^_^ jp@Mercury ~/Projects
└ git clone git@github.com:ggerganov/whisper.cpp.git

Cloning into 'whisper.cpp'...
remote: Enumerating objects: 3024, done.
remote: Counting objects: 100% (46/46), done.
remote: Compressing objects: 100% (25/25), done.
remote: Total 3024 (delta 20), reused 38 (delta 19), pack-reused 2978
Receiving objects: 100% (3024/3024), 5.10 MiB | 18.40 MiB/s, done.
Resolving deltas: 100% (1864/1864), done.

# Build and download the base English model
┌ ^_^ jp@Mercury {git master} ~/Projects/whisper.cpp
└ make base.en

I whisper.cpp build info:
I UNAME_S:  Darwin
I UNAME_P:  arm
I UNAME_M:  arm64
I CFLAGS:   -I.              -O3 -DNDEBUG -std=c11   -fPIC -pthread -DGGML_USE_ACCELERATE
I CXXFLAGS: -I. -I./examples -O3 -DNDEBUG -std=c++11 -fPIC -pthread
I LDFLAGS:   -framework Accelerate
I CC:       Apple clang version 14.0.0 (clang-1400.0.29.202)
I CXX:      Apple clang version 14.0.0 (clang-1400.0.29.202)

cc  -I.              -O3 -DNDEBUG -std=c11   -fPIC -pthread -DGGML_USE_ACCELERATE   -c ggml.c -o ggml.o
c++ -I. -I./examples -O3 -DNDEBUG -std=c++11 -fPIC -pthread -c whisper.cpp -o whisper.o
c++ -I. -I./examples -O3 -DNDEBUG -std=c++11 -fPIC -pthread examples/main/main.cpp examples/common.cpp ggml.o whisper.o -o main  -framework Accelerate
./main -h

usage: ./main [options] file0.wav file1.wav ...

options:
  -h,        --help              [default] show this help message and exit
  -t N,      --threads N         [4      ] number of threads to use during computation
  -p N,      --processors N      [1      ] number of processors to use during computation
  -ot N,     --offset-t N        [0      ] time offset in milliseconds
  -on N,     --offset-n N        [0      ] segment index offset
  -d  N,     --duration N        [0      ] duration of audio to process in milliseconds
  -mc N,     --max-context N     [-1     ] maximum number of text context tokens to store
  -ml N,     --max-len N         [0      ] maximum segment length in characters
  -sow,      --split-on-word     [false  ] split on word rather than on token
  -bo N,     --best-of N         [5      ] number of best candidates to keep
  -bs N,     --beam-size N       [-1     ] beam size for beam search
  -wt N,     --word-thold N      [0.01   ] word timestamp probability threshold
  -et N,     --entropy-thold N   [2.40   ] entropy threshold for decoder fail
  -lpt N,    --logprob-thold N   [-1.00  ] log probability threshold for decoder fail
  -su,       --speed-up          [false  ] speed up audio by x2 (reduced accuracy)
  -tr,       --translate         [false  ] translate from source language to english
  -di,       --diarize           [false  ] stereo audio diarization
  -nf,       --no-fallback       [false  ] do not use temperature fallback while decoding
  -otxt,     --output-txt        [false  ] output result in a text file
  -ovtt,     --output-vtt        [false  ] output result in a vtt file
  -osrt,     --output-srt        [false  ] output result in a srt file
  -owts,     --output-words      [false  ] output script for generating karaoke video
  -fp,       --font-path         [/System/Library/Fonts/Supplemental/Courier New Bold.ttf] path to a monospace font for karaoke video
  -ocsv,     --output-csv        [false  ] output result in a CSV file
  -oj,       --output-json       [false  ] output result in a JSON file
  -of FNAME, --output-file FNAME [       ] output file path (without file extension)
  -ps,       --print-special     [false  ] print special tokens
  -pc,       --print-colors      [false  ] print colors
  -pp,       --print-progress    [false  ] print progress
  -nt,       --no-timestamps     [true   ] do not print timestamps
  -l LANG,   --language LANG     [en     ] spoken language ('auto' for auto-detect)
             --prompt PROMPT     [       ] initial prompt
  -m FNAME,  --model FNAME       [models/ggml-base.en.bin] model path
  -f FNAME,  --file FNAME        [       ] input WAV file path

bash ./models/download-ggml-model.sh base.en
Downloading ggml model base.en from 'https://huggingface.co/ggerganov/whisper.cpp' ...
ggml-base.en.bin                  100%[============================================================>] 141.11M   103MB/s    in 1.4s
Done! Model 'base.en' saved in 'models/ggml-base.en.bin'
You can now use it like this:

  $ ./main -m models/ggml-base.en.bin -f samples/jfk.wav


===============================================
Running base.en on all samples in ./samples ...
===============================================

----------------------------------------------
[+] Running base.en on samples/jfk.wav ... (run 'ffplay samples/jfk.wav' to listen)
----------------------------------------------

whisper_init_from_file_no_state: loading model from 'models/ggml-base.en.bin'
whisper_model_load: loading model
whisper_model_load: n_vocab       = 51864
whisper_model_load: n_audio_ctx   = 1500
whisper_model_load: n_audio_state = 512
whisper_model_load: n_audio_head  = 8
whisper_model_load: n_audio_layer = 6
whisper_model_load: n_text_ctx    = 448
whisper_model_load: n_text_state  = 512
whisper_model_load: n_text_head   = 8
whisper_model_load: n_text_layer  = 6
whisper_model_load: n_mels        = 80
whisper_model_load: f16           = 1
whisper_model_load: type          = 2
whisper_model_load: mem required  =  215.00 MB (+    6.00 MB per decoder)
whisper_model_load: adding 1607 extra tokens
whisper_model_load: model ctx     =  140.60 MB
whisper_model_load: model size    =  140.54 MB
whisper_init_state: kv self size  =    5.25 MB
whisper_init_state: kv cross size =   17.58 MB

system_info: n_threads = 4 / 8 | AVX = 0 | AVX2 = 0 | AVX512 = 0 | FMA = 0 | NEON = 1 | ARM_FMA = 1 | F16C = 0 | FP16_VA = 1 | WASM_SIMD = 0 | BLAS = 1 | SSE3 = 0 | VSX = 0 |

main: processing 'samples/jfk.wav' (176000 samples, 11.0 sec), 4 threads, 1 processors, lang = en, task = transcribe, timestamps = 1 ...


[00:00:00.000 --> 00:00:11.000]   And so my fellow Americans, ask not what your country can do for you, ask what you can do for your country.


whisper_print_timings:     load time =   117.99 ms
whisper_print_timings:     fallbacks =   0 p /   0 h
whisper_print_timings:      mel time =    20.57 ms
whisper_print_timings:   sample time =    11.74 ms /    27 runs (    0.43 ms per run)
whisper_print_timings:   encode time =   304.17 ms /     1 runs (  304.17 ms per run)
whisper_print_timings:   decode time =    72.67 ms /    27 runs (    2.69 ms per run)
whisper_print_timings:    total time =   544.48 ms
```

And that's really it. 

## Setting up a Python Poetry project

Next up, setting up a quick Python script. I've recently gotten a bit annoyed at requirements.txt files (not having a nice CLI and not locking versions by default) and am trying out [Poetry](https://python-poetry.org/). 

It's really quite easy as well:

```zsh
# Set up a new directory for the project
┌ ^_^ jp@Mercury ~/Projects
└ mkdir transcript-scraper

┌ ^_^ jp@Mercury ~/Projects
└ cd transcript-scraper

# Initialize poetry, just use the defaults
┌ ^_^ jp@Mercury ~/Projects/transcript-scraper
└ poetry init -q

# Install the libraries I'm going to use
┌ ^_^ jp@Mercury ~/Projects/transcript-scraper
└ poetry add bs4 requests

Creating virtualenv transcript-scraper-WqErZKPo-py3.10 in /Users/jp/Library/Caches/pypoetry/virtualenvs
Using version ^0.0.1 for bs4
Using version ^2.28.2 for requests

Updating dependencies
Resolving dependencies... (0.2s)

Writing lock file

Package operations: 8 installs, 0 updates, 0 removals

  • Installing soupsieve (2.4)
  • Installing beautifulsoup4 (4.12.0)
  • Installing certifi (2022.12.7)
  • Installing charset-normalizer (3.1.0)
  • Installing idna (3.4)
  • Installing urllib3 (1.26.15)
  • Installing bs4 (0.0.1)
  • Installing requests (2.28.2)
```

Et voila. 

## Scraping the page

Finally, the script itself. I did use Github Copilot to help accelerate some of this, but it got a bit more wrong than last time I tried it out. YMMV.

Our goals:

* Download the page
* For each video:
  * Extract date and title from this specific format
  * Generate the filenames we'll be using
  * Check if we've already generate the text file, if so skip
  * Otherwise:
    * Use `requests` with `stream=True` to download the mp4
    * Use `ffmpeg` to extract the audio as mp3 (this could be combined with the next step, but I wanted to keep the mp3 + text)
    * Use `ffmpeg` to convert to the mp3 to wav (whisper needs this; this is where Copilot failed, it didn't add the extra parameters to *actually* convert to a wav)
    * Use `whisper` to extract the text
    * Clean up the `mp4` and `wav`, keeping only the `mp3` and `txt` files

Something like this:

```python
import bs4
import datetime
import os
import requests
import sys
import urllib.parse

url = sys.argv[1]

print('Scraping', url)
response = requests.get(url)
soup = bs4.BeautifulSoup(response.text, 'html.parser')

for article in soup.select('article'):
    # Extract metadata
    time = article.select_one('.time').text.strip()
    title = article.select_one('h4 a').text.strip()
    href = article.select_one('.media a').attrs['href']

    # Convert date like Mar 05, 2023 to datetime
    # Copilot just wrote this line for me; how cool is that? 
    date = datetime.datetime.strptime(time, '%b %d, %Y')

    # Generate filename
    working_path = f'data/{date:%Y}/{date:%m}/'
    output_path = 'output'

    filename = f'{date:%Y-%m-%d} - {title}}'
    print(filename)

    os.makedirs(working_path, exist_ok=True)
    os.makedirs(output_path, exist_ok=True)

    mp4_filename = os.path.join(working_path, filename + '.mp4')
    mp3_filename = os.path.join(working_path, filename + '.mp3')
    wav_filename = os.path.join(working_path, filename + '.wav')
    txt_filename = os.path.join(output_path, filename + '.txt')

    # Skip if text already exists
    if os.path.exists(txt_filename):
        continue

    # Download href video
    if not os.path.exists(mp4_filename):
        print('- Downloading', mp4_filename)
        response = requests.get(href, stream=True)
        with open(filename + '.mp4', 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                f.write(chunk)

    # Convert to mp3 with ffmpeg
    if not os.path.exists(mp3_filename):
        print('- Converting', mp3_filename)
        os.system(f'ffmpeg -i "{mp4_filename}" "{mp3_filename}"')

    # Covert to wav with ffmpeg
    if not os.path.exists(wav_filename):
        print('- Converting', wav_filename)
        os.system(f'ffmpeg -i "{mp3_filename}" -acodec pcm_s16le -ac 1 -ar 16000 "{wav_filename}"')

    # Extract text with whisper
    if not os.path.exists(txt_filename):
        print('- Extracting text', txt_filename)
        os.system(f'~/Projects/whisper.cpp/main -m ~/Projects/whisper.cpp/models/ggml-base.en.bin -f "./{wav_filename}" --output-txt')
        os.rename(f'{wav_filename}.txt', txt_filename)

    # Once we have the text, we no longer need to keep the video or wav
    os.remove(mp4_filename)
    os.remove(wav_filename)
```

So I'm doing a few ugly things. 

For example, a lot of `os.system` calls instead of `subprocess.check_call` / `subprocess.check_output`. If there are any quotes in the filenames, I've opened myself right up for a command injection attack. 

And then there's the super ugly whisper command:

```text
~/Projects/whisper.cpp/main 
    -m ~/Projects/whisper.cpp/models/ggml-base.en.bin
    -f "./{wav_filename}"
    --output-txt
```

Having to specify the executable's full path made sense, I didn't put it on my Path. I'll probably fix that at some point, but not right now. 

But having to specify the full path to the model (rather than whisper knowing to check relative to first my working directory and then it's own directory) is a bit annoying. And if you don't have the `./` prefix on the file path, who knows where it's going to run from...

But other than that, worked great. 10 minutes of transcription in a few seconds. 

And that's it. Something I'll fire set up as a cronjob and just leave running until I decide to try to do something more with it. :smile:

Onward!