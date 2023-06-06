from pytube import YouTube

link = input("Enter a youtube video's URL") # 例如 https://youtu.be/dQw4w9WgXcQ

yt = Youtube(link)
yt.streams.first().download()

print("downloaded", link)
