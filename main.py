# This is an example of PlusBox Flask. You can update it further!
# Created by FunctionError (updated on: 21-12-2024) Time : 2:30 am
# Example URLs:
# http://localhost:5000/channel/{channel_id}/playlist.m3u8
# http://localhost:5000/channel/ZeeBanglaHD/playlist.m3u8



from flask import Flask, Response, request
import requests
from typing import Optional, Dict
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class PlusBoxTV:
    def __init__(self):
        self.base_url = "http://plusbox.tv"
        self.stream_url = "http://plusbox.tv:8080"
        self.headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'http://plusbox.tv',
            'Referer': 'http://plusbox.tv/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        self.token_cache = {}
        self.media_info_cache = {}
        self.token_refresh_threshold = 50

    def get_token(self, channel_name: str) -> Optional[str]:
        try:
            response = requests.post(
                f"{self.base_url}/token.php",
                headers=self.headers,
                data={'ch_name': channel_name},
                timeout=10
            )
            response.raise_for_status()
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error getting token for {channel_name}: {e}")
            return None

    def get_media_info(self, channel_name: str, token: str) -> Optional[Dict]:
        try:
            response = requests.get(
                f"{self.stream_url}/{channel_name}/media_info.json",
                headers=self.headers,
                params={'token': token},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting media info for {channel_name}: {e}")
            return None

client = PlusBoxTV()

@app.route('/channel/<channel_id>/playlist.m3u8')
def get_stream(channel_id):
    try:
        token = client.get_token(channel_id)
        if not token:
            return "Failed to get token", 500

        media_info = client.get_media_info(channel_id, token)
        if not media_info:
            return "Failed to get media info", 500

        master_playlist = f"""#EXTM3U
#EXT-X-VERSION:6

#EXT-X-STREAM-INF:BANDWIDTH=2723000,RESOLUTION=1920x1080,CODECS="avc1.4d4028,mp4a.40.2"
{client.stream_url}/{channel_id}/tracks-v1/index.fmp4.m3u8?token={token}

#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",NAME="Audio",DEFAULT=YES,AUTOSELECT=YES,URI="{client.stream_url}/{channel_id}/tracks-a1/index.fmp4.m3u8?token={token}"
"""
        return Response(
            master_playlist,
            content_type='application/vnd.apple.mpegurl',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
            }
        )

    except Exception as e:
        logger.error(f"Error creating playlist for {channel_id}: {e}")
        return f"Error creating playlist: {str(e)}", 500

@app.route('/channel/<channel_id>/tracks-<track>/<path:segment>')
def get_segment(channel_id, track, segment):
    try:
        token = client.get_token(channel_id)
        if not token:
            return "Failed to get token", 500

        segment_url = f"{client.stream_url}/{channel_id}/tracks-{track}/{segment}"
        if '?' not in segment:
            segment_url += f"?token={token}"

        response = requests.get(
            segment_url,
            headers=client.headers,
            stream=True,
            timeout=10
        )
        response.raise_for_status()

        return Response(
            response.iter_content(chunk_size=8192),
            content_type=response.headers.get('content-type', 'application/octet-stream'),
            headers={
                'Access-Control-Allow-Origin': '*',
                'Cache-Control': 'no-cache',
            }
        )

    except Exception as e:
        logger.error(f"Error fetching segment {segment} for {channel_id}: {e}")
        return f"Error fetching segment: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
