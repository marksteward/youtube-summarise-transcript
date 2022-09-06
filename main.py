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

@functions_framework.http
def youtube_summarise_transcript(request):
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

    def summarise(chunk):
        response = openai.Completion.create(model="text-davinci-002", prompt=f'Summarise:\n\n{chunk}\n\nSummary in under 20 words:', temperature=0, max_tokens=50)
        return response.choices[0].text.strip()

    summaries = [summarise(c) for c in chunks]
    if len(summaries) == 1:
        summary = summaries[0]
    else:
        summary = summarise('\n'.join(summaries))

    return ({"tldr": summary}, 200, headers)

