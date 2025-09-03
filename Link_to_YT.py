import os
from pytubefix import YouTube
from moviepy import AudioFileClip

def download_youtube(url, output_format='mp4'):
    try:
        yt = YouTube(url)
        if output_format == 'mp4':
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            out_file = stream.download()
            print(f"Downloaded MP4: {out_file}")
        elif output_format == 'mp3':
            stream = yt.streams.filter(only_audio=True).first()
            out_file = stream.download()
            base, ext = os.path.splitext(out_file)
            mp3_file = base + '.mp3'
            audio_clip = AudioFileClip(out_file)
            audio_clip.write_audiofile(mp3_file)
            audio_clip.close()
            os.remove(out_file)
            print(f"Downloaded MP3: {mp3_file}")
        else:
            print("Unsupported format. Use 'mp4' or 'mp3'.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    url = input("Enter YouTube URL: ")
    fmt = input("Choose format (mp4/mp3): ").lower()
    download_youtube(url, fmt)