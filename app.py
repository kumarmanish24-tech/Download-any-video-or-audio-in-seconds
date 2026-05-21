from flask import Flask, render_template, request, send_file
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    file_type = request.form.get("type")

    if not url:
        return "Please enter a valid URL"

    bypass_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Fetch-Mode': 'navigate',
    }

    base_opts = {
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'http_headers': bypass_headers,
        # Using the iOS client is significantly more effective at bypassing the bot wall
        'extractor_args': {'youtube': {'player_client': ['ios'], 'skip': ['webpage']}},
        'youtube_include_dash_manifest': False,
    }

    # Automatically loads cookies if cookies.txt is present in your project directory
    if os.path.exists("cookies.txt"):
        base_opts['cookiefile'] = 'cookies.txt'

    if file_type == "audio":
        ydl_opts = {
            **base_opts,
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]
        }
    else:
        ydl_opts = {
            **base_opts,
            'format': 'best',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            # Fix: yt-dlp renames the file extension during post-processing
            if file_type == "audio":
                base_path = os.path.splitext(file_path)[0]
                file_path = base_path + ".mp3"
                
                # Double fallback check for custom double extensions (e.g. video.webm.mp3)
                if not os.path.exists(file_path) and os.path.exists(base_path + ".webm.mp3"):
                    file_path = base_path + ".webm.mp3"
                elif not os.path.exists(file_path) and os.path.exists(base_path + ".m4a.mp3"):
                    file_path = base_path + ".m4a.mp3"

        # Final check to verify the file safely exists before serving
        if not os.path.exists(file_path):
            return f"Error: Downloaded file could not be verified on the server path: {file_path}"

        response = send_file(file_path, as_attachment=True)

        @response.call_on_close
        def cleanup():
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass  # Silently skip if file is locked or already cleaned up

        return response

    except Exception as e:
        return f"Error running yt-dlp: {str(e)}"


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
