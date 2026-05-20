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

    # AUDIO DOWNLOAD CONFIGURATION
    if file_type == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]
        }
    # VIDEO DOWNLOAD CONFIGURATION
    else:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s'
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
    # Railway passes the port dynamically. Default to 5000 or 8080 for local development.
    port = int(os.environ.get('PORT', 8080))
    
    # Ensure it binds to 0.0.0.0 so it can accept external requests inside the container
    app.run(host='0.0.0.0', port=port)
