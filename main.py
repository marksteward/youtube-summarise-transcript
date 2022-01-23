import functions_framework
import re
import requests

from youtube_transcript_api._transcripts import TranscriptListFetcher

@functions_framework.http
def youtube_transcript_api(request):
    video_ids = request.args.get('video_ids', '')
    output = {}
    with requests.Session() as http_client:
        fetcher = TranscriptListFetcher(http_client)

        for video_id in video_ids.split(','):
            if not re.match('[0-9A-Za-z_-]{11}', video_id):
                continue
            html = fetcher._fetch_video_html(video_id)
            output[video_id] = fetcher._extract_captions_json(html, video_id)

    return output

