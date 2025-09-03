import subprocess
import os
from pytubefix import YouTube
from urllib.error import URLError
from pathlib import Path

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def sanitize_filename(filename):
    """Sanitize filename for safe use and truncate to 50 characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:50]

def ensure_unique_filename(filepath):
    """Append a number to filename if it already exists."""
    base, ext = os.path.splitext(filepath)
    counter = 1
    new_filepath = filepath
    while os.path.exists(new_filepath):
        new_filepath = f"{base}_{counter}{ext}"
        counter += 1
    return new_filepath

def get_available_resolutions(yt):
    """Get list of available video resolutions for MP4 adaptive streams."""
    video_streams = yt.streams.filter(
        adaptive=True, file_extension="mp4", only_video=True
    ).order_by("resolution").desc()
    resolutions = sorted(set(stream.resolution for stream in video_streams if stream.resolution), reverse=True)
    return resolutions

def download_mp4(url, output_dir=None):
    """Download YouTube video as MP4 with merged video and audio."""
    if not check_ffmpeg():
        print("Error: FFmpeg is not installed or not in PATH. Please install FFmpeg.")
        return

    # Set default output directory to ~/Downloads/YouTube
    if output_dir is None:
        output_dir = os.path.join(Path.home(), "Downloads", "YouTube")
    os.makedirs(output_dir, exist_ok=True)

    try:
        yt = YouTube(url)
    except URLError:
        print("Error: Invalid URL or network issue.")
        return

    # Get available resolutions
    resolutions = get_available_resolutions(yt)
    if not resolutions:
        print("Error: No suitable video streams found.")
        return

    # Prompt user to select resolution
    print("Available resolutions:", ", ".join(resolutions))
    while True:
        selected_resolution = input("Choose a resolution (e.g., 720p): ").lower()
        if selected_resolution in resolutions:
            break
        print("Invalid resolution. Please choose from:", ", ".join(resolutions))

    # Get video stream for selected resolution
    video_stream = yt.streams.filter(
        adaptive=True, file_extension="mp4", only_video=True, resolution=selected_resolution
    ).first()

    if not video_stream:
        print(f"Error: No video stream found for {selected_resolution}.")
        return

    # Get highest quality audio stream
    audio_stream = yt.streams.filter(
        adaptive=True, only_audio=True
    ).order_by("abr").desc().first()

    if not audio_stream:
        print("Error: No suitable audio stream found.")
        return

    # Define file paths
    video_file = os.path.join(output_dir, "video_temp.mp4")
    audio_file = os.path.join(output_dir, "audio_temp.m4a")
    final_file = ensure_unique_filename(os.path.join(output_dir, f"{sanitize_filename(yt.title)}.mp4"))

    try:
        print(f"Downloading video: {video_stream.resolution}")
        video_stream.download(output_path=output_dir, filename="video_temp.mp4")

        print(f"Downloading audio: {audio_stream.abr}")
        audio_stream.download(output_path=output_dir, filename="audio_temp.m4a")

        # Merge using FFmpeg
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", video_file,
            "-i", audio_file,
            "-c:v", "copy",
            "-c:a", "mp3",
            "-b:a", "192k",
            final_file
        ]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        print(f"Download and merge complete: {final_file}")

    except subprocess.CalledProcessError as e:
        print(f"Error: FFmpeg merge failed: {e.stderr.decode()}")
    except Exception as e:
        print(f"Error during download/merge: {str(e)}")
    finally:
        # Clean up temporary files
        for temp_file in [video_file, audio_file]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    print(f"Warning: Could not delete temporary file {temp_file}")

def download_mp3(url, output_dir=None):
    """Download YouTube audio as MP3."""
    if not check_ffmpeg():
        print("Error: FFmpeg is not installed or not in PATH. Please install FFmpeg.")
        return

    # Set default output directory to ~/Downloads/YouTube
    if output_dir is None:
        output_dir = os.path.join(Path.home(), "Downloads", "YouTube")
    os.makedirs(output_dir, exist_ok=True)

    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
        if not stream:
            print("Error: No suitable audio stream found.")
            return

        temp_file = stream.download(output_path=output_dir)
        base, ext = os.path.splitext(temp_file)
        mp3_file = ensure_unique_filename(os.path.join(output_dir, f"{sanitize_filename(yt.title)}.mp3"))

        # Convert to MP3 using FFmpeg
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", temp_file,
            "-c:a", "mp3",
            "-b:a", "192k",
            mp3_file
        ]
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        print(f"Downloaded MP3: {mp3_file}")

    except subprocess.CalledProcessError as e:
        print(f"Error: FFmpeg conversion failed: {e.stderr.decode()}")
    except URLError:
        print("Error: Invalid URL or network issue.")
    except Exception as e:
        print(f"Error during download/conversion: {str(e)}")
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                print(f"Warning: Could not delete temporary file {temp_file}")

if __name__ == "__main__":
    try:
        url = input("Enter YouTube URL: ")
        fmt = input("Choose format (mp4/mp3): ").lower()
        output_dir = input("Enter output directory (press Enter for default ~/Downloads/YouTube): ").strip()
        if not output_dir:  # Use default if empty
            output_dir = None
        else:
            # Validate custom directory
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError:
                print("Error: Invalid output directory. Using default ~/Downloads/YouTube.")
                output_dir = None

        if fmt == "mp4":
            download_mp4(url, output_dir)
        elif fmt == "mp3":
            download_mp3(url, output_dir)
        else:
            print("Error: Invalid format. Please choose 'mp4' or 'mp3'.")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")