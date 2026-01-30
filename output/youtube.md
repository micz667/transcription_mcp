import yt_dlp

def download_youtube_video(video_url, output_path="."):
    ydl_opts = {
        'format': 'best',  # Selects the best available format
        'outtmpl': f'{output_path}/%(title)s.%(ext)s'  # Saves the video in the specified path
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

# Request video URL from user
video_url = input("Please enter the full URL of the YouTube video: ")
output_path = input("Please enter the folder path where you want to save the video (leave empty for current directory): ")

try:
    print(f"Downloading '{video_url}'...")
    download_youtube_video(video_url, output_path or ".")
    print("Download completed successfully.")
except Exception as e:
    print(f"An error has occurred: {e}")