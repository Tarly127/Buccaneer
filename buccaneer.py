from pytube import Playlist, YouTube
import sys
import os
import re
from moviepy.editor import *
from mutagen.mp3 import MP3  
from mutagen.easyid3 import EasyID3
from urllib.error import HTTPError
import json

MUSIC_STORAGE_DIR: str     = "/Users/tarly127/Desktop/Archives/Music/"
DEFAULT_SINGLE_DL_DIR: str = "/Users/tarly127/Desktop/"

def process_name(name: str) -> str:
    __name = name
    __name = re.sub(r"[ ]*\([0-9]+[ ]*[-]*[ ]*((Remaster(ed)?)|(Mix))[ ]*[0-9]+\)", "", __name, flags=re.IGNORECASE)
    __name = re.sub(r"Death Grips - ", "", __name, flags=re.IGNORECASE)
    __name = re.sub(r"Black Sabbath - ", "", __name, flags=re.IGNORECASE)
    __name = re.sub(r"\(Official ?(Music) [Vv]ideo\)", "", __name, flags=re.IGNORECASE)
    __name = re.sub(r"/", "", __name, flags=re.IGNORECASE)
    __name = re.sub(r"\(?HQ\)?", "", __name, flags=re.IGNORECASE)
    __name = re.sub(r"\(?[ ]*iron maiden[ ]*\)?\-?[ ]*","", __name, flags=re.IGNORECASE)

    return __name

def to_mp3(src: str) -> None:

    try:
        # Convert video into .wav file
        os.system(f'ffmpeg -loglevel quiet -i \"{src}.mp4\" \"{src}.wav\"')
        # Convert .wav into final .mp3 file
        os.system(f'lame --silent \"{src}.wav\" \"{src}.mp3\"')
        os.remove(f'{src}.wav')  # Deletes the .wav file
        os.remove(f'{src}.mp4')  # Deletes the original download

    except OSError as err:
        pass

def format_dest_dir(dest: str) -> str:
    output_dir = MUSIC_STORAGE_DIR + dest

    if not output_dir.endswith("/"):
        output_dir += "/"

    # create the output directory if it doesn't exist
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)

    return output_dir

def edit_album_tag(mp3_src: str, id: int, total: int, album_name: str) -> None:

    album  = album_name.split("-")[1][1:]
    artist = album_name.split("-")[0]
    artist = artist[:len(artist) - 1]

    # mp3 name (with directory) from filez  
    song = mp3_src 
    # turn it into an mp3 object using the mutagen library  
    mp3file = MP3(song, ID3=EasyID3)  
    # set the album name  
    mp3file['album'] = [album]  
    # set the albumartist name  
    mp3file['albumartist'] = [artist]  
    # set the track number with the proper format  
    mp3file['tracknumber'] = f"{id}/{total}"  
    # save the changes that we've made  
    mp3file.save() 

def download_single(video: YouTube, name: str, album_name: str = None, convert_mp3: bool = False, album_length: int = 1, video_id: int = None) -> None:    
    # download video as mp4
    video.streams.first().download(filename=name+".mp4")

    # convert to mp3 and edit the album tags
    if convert_mp3 and album_name is not None:
        # convert to mp3
        to_mp3(name)
        # edit album tag
        edit_album_tag(name + ".mp3", video_id, album_length, album_name)

def download_all(url: str, album_name: str = None, dest: str = DEFAULT_SINGLE_DL_DIR, ) -> None:
    # check if it's a yt link
    if re.search(r"youtube", url, flags=re.IGNORECASE):
        # check if it's a playlist
        if re.search(r"(play)?list", url, flags=re.IGNORECASE):
            # if so, download each video from it
            playlist: Playlist = Playlist(url)

            i = 1

            if Playlist is not None:
                for video in playlist.videos:
                    try:
                        name = video.title

                        # take out unwanted elements
                        name = process_name(name)

                        name = dest + name

                        print(f"- Downloading \"{video.title}\"...", end="", flush=True)

                        download_single(video, name=name, album_name=album_name, album_length=len(playlist), video_id=i, convert_mp3=True)

                        print(" Done!")    
                    except (HTTPError, FileNotFoundError, KeyError) as err:
                        print(f"- Error on {video.title}")
                        print(err)

                    i += 1
        else:
            # if not, download the video
            video: YouTube = YouTube(url)

            # Download the video
            print(f"Downloading \"{video.title}\"...", end="", flush=True)

            download_single(video, f"{dest}{video.title if not album_name else album_name}")

            print(" Done!")

def process_from_json(src: str) -> None:
    with open(src, "r") as f:
        album_lst = json.load(f)
        for album in album_lst:
            name = album["name"]

            print(f"Downloading {name}")

            download_all(url=album["url"], dest=format_dest_dir(album["name"]), album_name=album["name"])

            print(f"Finished downloading {name}")     

def main(args: list[str]) -> None:
    if len(args) > 0:
        match args[0]:
            case "json" | "-j":
                if len(args) > 1:
                    process_from_json(args[1])
                else:
                    print("Not enough arguments.\n Usage: python3 buccaneer.py json <path_to_json>")
            case "single" | "-s":
                if len(args) > 1:
                    download_all(*args[1:])
                else:
                    print("Not enough arguments.\n Usage: python3 buccaneer.py single <target_url> [name]")

if __name__ == "__main__":
    main(sys.argv[1:])