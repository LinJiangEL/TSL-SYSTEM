README Document  [English](/README.md) | [Chinese](/README_CN.md)

# TSL-SYSTEM
它是一个综合了多种学科功能的系统。

## 前言
出于对编程及开源的热爱，我将这个我写了将近两年的项目开源了，说是两年，实际上我一直在学校里面，只有在空闲的时候才会拿出一张纸一杆笔，坐在窗边独自构思它的功能，等到晚上回到家，再拿出手机打开Pydroid3，检查代码有没有bug。
在纸上写代码是我生活中最享受的乐趣之一，如果你也是这样，我很愿意和你做个朋友，互帮互助，共同进步。

## 安装和使用
***在开始所有安装和使用步骤之前，请确保您的python版本为3.9.6或更高版本，系统中安装了C运行库，并且可以正确安装该项目所依赖的包和模块。***

### Windows:
1. 将此存储库克隆到您的本地存储并进入到该目录。
2. 运行`python3 -m venv .venv`，它将创建一个虚拟终端。
   如果您已经部署了虚拟环境，您可以直接运行`run-venv.bat`
3. 请运行`pip3 install -r Temp\__prebuild__\win32\modlist.txt`，
   如果在安装过程中出现错误，您可以在线搜索解决方案。目前，我已经为在Windows环境中安装`pygobject`时出现的错误"msvc_recommended_pragmas.h not found"提供了[可行的解决方案](https://blog.csdn.net/qq_56086478/article/details/136005175) 。
4. 运行`python3 system.py`，输入用户名和密码登录系统终端。
   如果在系统自检过程中遇到不可忽视的错误，程序会立刻停止运行，所以请不要修改一些关键代码以防止程序崩溃，也不要删除源码目录下的文件，如果报错找不到库，请用`pip`安装那个库。
5. 假如你只是测试它能否运行，那么*第3步*运行的内容改为`pip3 install -r runrequirements.txt`，之后再继续*第4步*。

### Linux && Termux:
1. 将此存储库克隆到您的本地存储并进入到该目录。
2. 运行`python3 -m venv .venv`，它将创建一个虚拟终端。
   如果您已经部署了虚拟环境，您可以直接运行`source .venv/bin/activate`
3. 请运行`pip3 install -r Temp\__prebuild__\linux\modlist.txt`，
   如果在安装过程中出现错误，您可以在线搜索解决方案。
4. 运行`python3 system.py`，输入用户名和密码登录系统终端。
   如果在系统自检过程中遇到不可忽视的错误，程序会立刻停止运行，所以请不要修改一些关键代码以防止程序崩溃，也不要删除源码目录下的文件，如果报错找不到库，请用`pip`安装那个库。
5. 假如你只是测试它能否运行，那么*第3步*运行的内容改为`pip3 install -r runrequirements.txt`，之后再继续*第4步*。

这是初始用户名和密码。  
Username|Password|Mode
----|----|----
root|root|root
user|user|user

## 帮助文档
运行“python3 system.py”，输入用户名和密码登录系统终端。然后，您可以通过输入`help`或`help [command]`来打印帮助页面。

## 更新日志
版本历史见 [CHANGELOG_CN.md](/CHANGELOG_CN.md)。

## 断点保护
系统由断点守护（breakpoint guard）保护。系统运行期间，守护会在`Temp/Breakpoint.state`中保存一个断点（当前用户、模式、pid、会话开始时间、命令数、最后一条命令和阶段）：
- 每条命令执行前都会重写断点，因此意外停止时可以准确知道是哪条命令被中断。
- 正常退出（`exit`、`logout`、`init`、关机）会解除守护。
- 如果进程被杀死或崩溃，状态文件仍然显示会话处于运行中，所以下一次运行`system.py`时会打印警告，并把最后的断点、故障时间、操作系统和Python版本以`CRITICAL`级别写入*断点记录文件*（`Temp/logs/log_breakpoint.log`）。
- 未捕获的异常、致命信号和线程异常都会连同完整的回溯（traceback）写入`Temp/logs/log_breakpoint.log`；`Temp/logs/log_fault.log`保存`faulthandler`产生的致命错误转储。
- `Ctrl-C`（`KeyboardInterrupt`）会被记录，终端继续运行；`throw`命令会故意以致命错误结束系统，用来测试这套机制。

所有操作日志（`INFO`级别及以上）都会写入`Temp/logs/log_YYYY-MM.log`；断点记录（`DEBUG`级别及以上）以及抛出的回溯都会写入`Temp/logs/log_breakpoint.log`。

## 音乐模块
本地音乐存放在`tools/Music/Musics`目录（可用环境变量`TSL_MUSIC_DIR`覆盖）。运行`execute Music`进入点歌台：`search KEYWORD`联网搜索，`get INDEX/KEYWORD`把选中的音乐下载到该目录并自动加入播放列表，`local`检索本地音乐，`list`、`queue`、`drop`、`clear`、`play`、`pause`、`stop`管理播放列表与播放。终端内可以使用`music play|stop|pause`、`music search KEYWORD`和`music get INDEX/KEYWORD`；播放由后台线程配合MCI（Windows）或`ffplay`（Linux）完成，不会阻塞终端，多个终端进程通过`Temp/MusicState.json`与`Temp/MusicControl.json`共享播放状态。受版权限制，匿名搜索通常只能获取翻唱或免费曲目。

## 网络模块
运行`execute Network`可使用网络探测与分析功能：`dns`（A/AAAA/MX/NS/TXT/CNAME，内置DNS客户端）、`ping`、`trace`（路由追踪）、`ports`（TCP端口扫描）、`http`（状态码、响应头、耗时与安全响应头）、`tls`（证书主体、颁发者、有效期、剩余天数与备用名称）、`whois`（RFC 3912）、`local`（网卡、网关、DNS与ARP表）、`public`（出口IP与归属地）、`speed`（下载测速）和`analyze HOST`（综合报告）。全部以标准库实现，`ping`/`tracert`依赖系统自带命令；如果网络屏蔽了ICMP，程序会给出明确的错误提示而不是静默失败。

## 许可证
TSL-SYSTEM 使用 [PolyForm Noncommercial License 1.0.0](/LICENSE) 授权，仅允许非商业用途；
如需商业使用，请与作者联系获取授权。

## 参考文献
- [Detailed Annotation on Python Regex](https://zhuanlan.zhihu.com/p/479731754)
- [Detailed Annotation on Python loguru](https://blog.csdn.net/Kangyucheng/article/details/112794185)
- [SymPy 1.12 documentation Solving Guidance](https://docs.sympy.org/latest/guides/solving/solving-guidance.html)
- [SymPy Symbol Calculation(1) ](https://zhuanlan.zhihu.com/p/599743326)
- [SymPy: symbolic computing in Python. PeerJ Computer Science](https://peerj.com/articles/cs-103)
