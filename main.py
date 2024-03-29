import functions_framework
import re
import yaml
from textwrap import wrap

import openai
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter


with open("env.yaml", "r") as f:
    env = yaml.safe_load(f)

openai.api_key = env['openai_key']

def summarise(chunk):
    """
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[
      {"role": "system", "content": "The user will provide a transcript in a series of messages. At the end, I will prompt you to provide a short summary."},
      {"role": "user", "content": c},
      {"role": "system", "content": "Now please summarise the above in under 20 words."}
    ], temperature=0, max_tokens=50)
    """
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[
      {"role": "system", "content": "Summarise the following transcript:"},
      {"role": "user", "content": chunk},
      {"role": "system", "content": "Summary in under 20 words:"}
    ], temperature=0, max_tokens=50)
    return response.choices[0].message.content.strip()

def characterise(chunk):
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[
      {"role": "system", "content": "The following content is of a particular presentation style and genre:"},
      {"role": "user", "content": chunk},
      {"role": "system", "content": "Presentation style and genre in under 20 words:"}
    ], temperature=0, max_tokens=50)
    return response.choices[0].message.content.strip()


@functions_framework.http
def youtube_summarise_transcript(request):
    return youtube_process_transcript(request, tldr=summarise)

@functions_framework.http
def youtube_characterise_transcript(request):
    return youtube_process_transcript(request, genre=characterise)


def youtube_process_transcript(request, **processors):
    origin = request.headers.get('origin')
    if '*' in env['allowed_origins']:
        origin = '*'

    if not origin:
        return ('', 401)
    if origin not in env['allowed_origins']:
        return ('', 401)

    headers = {
      'Access-Control-Allow-Origin': origin,
      'Access-Control-Allow-Methods': 'GET',
      'Vary': 'Origin',
    }
    if request.method == 'OPTIONS':
        return ('', 204, headers)

    video_id = request.args.get('video_id', '')
    if not re.match('[0-9A-Za-z_-]{11}', video_id):
        return ('', 400, headers)

    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    formatter = TextFormatter()
    transcript_text = formatter.format_transcript(transcript)

    chunks = wrap(transcript_text, 2000 * 4)  # aim for 2000 tokens per chunk

    response = {}
    for (field, processor) in processors.items():
        try:
            # TODO: check how much time we've got left
            results = [processor(c) for c in chunks]
            if len(results) == 1:
                response[field] = results[0]
            else:
                response[field] = summarise('\n'.join(results))

        except Exception as e:
            return ({"error": str(e)}, 500, headers)

    return (response, 200, headers)

