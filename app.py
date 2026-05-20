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

    # Common headers to bypass YouTube 403 Forbidden block
    bypass_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Fetch-Mode': 'navigate',
    }

    # AUDIO DOWNLOAD CONFIGURATION
    if file_type == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'nocheckcertificate': True,
            'http_headers': bypass_headers,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]
        }
    # VIDEO DOWNLOAD CONFIGURATION
    else:
        ydl_opts = {
            'format': 'best', # 'bestvideo+bestaudio' ki jagah simple 'best' rakha hai taaki processing fast ho aur bypass aaram se ho
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'nocheckcertificate': True,
            'http_headers': bypass_headers
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

            # Adjust path extension if audio extraction changed it to mp3
            if file_type == "audio":
                file_path = os.path.splitext(file_path)[0] + ".mp3"

        response = send_file(file_path, as_attachment=True)

        # Automatically clean up the downloaded file from the server's disk storage after delivery
        @response.call_on_close
        def cleanup():
            if os.path.exists(file_path):
                os.remove(file_path)

        return response

    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == '__main__':
    # Looks for Railway's port variable, defaults to 5000 if not found
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
