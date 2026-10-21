README Document  [English](/README.md) | [Chinese](/README_CN.md)

# TSL-SYSTEM
It is a system that integrates the functions of various disciplines.

## Foreword
Out of my love for programming and open source, I have decided to make this project I have been working on for almost two years open source. Although it has taken me nearly two years to develop, I have mostly been working on it during my spare time at my senior high school, when I would sit by the window with a pen and paper to brainstorm its functionalities. Then, I would check the code for bugs using Pydroid3 on my phone when I got home in the evening. Writing code on paper is one of my favourite pastimes, and if you share the same interest, I would be happy to become friends and learn from each other to make progress together.

## Install and Use
***Before all installation and use steps begin, please make sure that your python version is 3.9.6 or above, the C runtime is installed in the system, and the packages and modules that this project depends on can be installed correctly.***

### Windows:
1. Clone this reposity to your local storage and enter the directory.
2. run `python3 -m venv .venv`, it will create a virtual terminal.  
   If you have deployed a virtual environment, you can run `run-venv.bat` directly.
3. Run `pip3 install -r Temp\__prebuild__\win32\modlist.txt`.  
   If an error occurs during the installation process, you can search for a solution online. Currently, I have provided a [feasible solution](https://blog.csdn.net/qq_56086478/article/details/136005175) for the error 'msvc_recommended_pragmas.h not found' that occurs during the installation of `pygobject` in a Windows environment.
4. Run `python3 system.py` and log in to the system terminal by entering your username and password. 
   If you encounter any critical errors during the system self-check process, the program will immediately stop running. Therefore, please avoid modifying any critical code to prevent the program from crashing, and refrain from deleting any files under the source code directory. If you encounter any errors regarding missing modules, please use `pip` to install the required modules.
5. If you're just testing whether it can run normally, then in *step 3*, replace the command with `pip3 install -r runrequirements.txt`, and then proceed to *step 4*.

### Linux && Termux:
1. Clone this reposity to your local storage and enter the directory.
2. run `python3 -m venv .venv`, it will create a virtual terminal.  
   If you have deployed a virtual environment, you can run `source .venv/bin/activate` directly.
3. Run `pip3 install -r Temp\__prebuild__\linux\modlist.txt`.  
   If an error occurs during the installation process, you can search for a solution online.
4. Run `python3 system.py` and log in to the system terminal by entering your username and password. 
   If you encounter any critical errors during the system self-check process, the program will immediately stop running. Therefore, please avoid modifying any critical code to prevent the program from crashing, and refrain from deleting any files under the source code directory. If you encounter any errors regarding missing modules, please use `pip` to install the required modules.
5. If you're just testing whether it can run normally, then in *step 3*, replace the command with `pip3 install -r runrequirements.txt`, and then proceed to *step 4*.

Here is the initial username and password.  
Username|Password|Mode
----|----|----
root|root|root
user|user|user

## Help Document
After running `python3 system.py`, you can log in to the system terminal by entering your username and password. Then, you can print the help page by inputing `help` or `help [command]`.

## Changelog
The release history is documented in [CHANGELOG.md](/CHANGELOG.md).

## Breakpoint Protection
The system is protected by a breakpoint guard. While the system runs, the guard keeps a checkpoint in `Temp/Breakpoint.state` (current user, mode, pid, session start, command count, last command and phase):
- Before each command is executed, the checkpoint is rewritten, so an unexpected stop tells exactly which command was interrupted.
- Normal exits (`exit`, `logout`, `init`, shutdown) disarm the guard.
- If the process is killed or crashes, the state file still says the session is alive, so the next launch of `system.py` prints a warning, and the last checkpoints, the fault time, the operating system and the Python version are written to the *breakpoint record file* (`Temp/logs/log_breakpoint.log`) with the `CRITICAL` level.
- Uncaught exceptions, fatal signals and thread exceptions are written to `Temp/logs/log_breakpoint.log` together with their full traceback; `Temp/logs/log_fault.log` keeps the fatal-fault dumps produced by `faulthandler`.
- A `Ctrl-C` (`KeyboardInterrupt`) is recorded and the terminal keeps running. The `throw` command terminates the system on purpose with a fatal error to test this mechanism.

All the operation logs (`INFO` level and above) are written to `Temp/logs/log_YYYY-MM.log`; the breakpoint records (`DEBUG` level and above), including the thrown tracebacks, are written to `Temp/logs/log_breakpoint.log`.

## Music Module
Local music is stored in `tools/Music/Musics` (override it with the `TSL_MUSIC_DIR` environment variable). Run `execute Music` to open the point-song station: `search KEYWORD` searches online, `get INDEX/KEYWORD` downloads the selected music into that directory and queues it automatically, `local` searches local files, and `list`, `queue`, `drop`, `clear`, `play`, `pause` and `stop` manage the playlist and playback. In the terminal, `music play|stop|pause`, `music search KEYWORD` and `music get INDEX/KEYWORD` are available; playback runs on a background thread through MCI (Windows) or `ffplay` (Linux), so it never blocks the terminal, and several terminal processes share the playback state through `Temp/MusicState.json` and `Temp/MusicControl.json`. Because of copyright restrictions, anonymous searches usually return only covers or free tracks.

## Network Module
Run `execute Network` to use the network probing and analysis functions: `dns` (A/AAAA/MX/NS/TXT/CNAME with a built-in DNS client), `ping`, `trace` (traceroute), `ports` (TCP port scan), `http` (status code, headers, timings and security headers), `tls` (certificate subject, issuer, validity, days left and alternative names), `whois` (RFC 3912), `local` (interfaces, gateway, DNS and the ARP table), `public` (public IP and location), `speed` (download speed) and `analyze HOST` (a combined report). Everything is implemented with the standard library; `ping`/`tracert` rely on the commands shipped with the operating system, and when ICMP is blocked the tools report a clear error instead of failing silently.

## Citation Literature
- [Detailed Annotation on Python Regex](https://zhuanlan.zhihu.com/p/479731754)
- [Detailed Annotation on Python loguru](https://blog.csdn.net/Kangyucheng/article/details/112794185)
- [SymPy 1.12 documentation Solving Guidance](https://docs.sympy.org/latest/guides/solving/solving-guidance.html)
- [SymPy Symbol Calculation(1) ](https://zhuanlan.zhihu.com/p/599743326)
- [SymPy: symbolic computing in Python. PeerJ Computer Science](https://peerj.com/articles/cs-103)
