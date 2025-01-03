#  Copyright (c) 2024. L.J.Afres, All rights reserved.

import os
import os.path
import sys
from concurrent.futures import ThreadPoolExecutor
import signal
from functools import partial
from threading import Event
from typing import Iterable
from urllib.request import urlopen
from termcolor import colored
from rich.progress import BarColumn, DownloadColumn, Progress, TaskID, TextColumn, TimeRemainingColumn, TransferSpeedColumn


os.system("")

progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
)


done_event = Event()


def handle_sigint(signum, frame):
    done_event.set()
    return signum, frame


signal.signal(signal.SIGINT, handle_sigint)


def copy_url(task_id: TaskID, url: str, path: str) -> None:
    """Copy data from an url to a local file."""
    progress.console.log(f"Requesting {url}")
    response = urlopen(url)
    # This will break if the response doesn't contain content length
    progress.update(task_id, total=int(response.info()["Content-length"]))
    with open(path, "wb") as dest_file:
        progress.start_task(task_id)
        for data in iter(partial(response.read, 32768), b""):
            dest_file.write(data)
            progress.update(task_id, advance=len(data))
            if done_event.is_set():
                return
    progress.console.log(f"Downloaded {path}")


def download(urls: Iterable[str], dest_dir: str):
    """Download multiple files to the given directory."""

    with progress:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for url in urls:
                filename = url.split("/")[-1]
                dest_path = os.path.join(dest_dir, filename)
                task_id = progress.add_task("download", filename=filename, start=False)
                pool.submit(copy_url, task_id, url, dest_path)


if __name__ == "__main__":
    if sys.argv[1:]:
        download(sys.argv[1:], "./")
    else:
        print("")
        print(colored("TSL-URLDownloader V2.0", color="cyan"))
        print("\033[33mUsage:\033[0m python geturl.py URL1 URL2 URL3 ...")
