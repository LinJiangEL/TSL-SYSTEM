README Document  [English](/README.md) | [Chinese](/README_CN.md)

# TSL-SYSTEM
它是一个综合了多种学科功能的系统。

## 前言
出于对编程及开源的热爱，我将这个我写了将近两年的项目开源了，说是两年，实际上我一直在学校里面，只有在空闲的时候才会拿出一张纸一杆笔，坐在窗边独自构思它的功能，等到晚上回到家，再拿出手机打开Pydroid3，检查代码有没有bug。
在纸上写代码是我生活中最享受的乐趣之一，如果你也是这样，我很愿意和你做个朋友，互帮互助，共同进步。

## 安装和使用
***在开始所有安装和使用步骤之前，请确保您的python版本为3.9.6及更高版本，系统中安装了C运行库，并且可以正确安装该项目所依赖的包和模块。***

### Windows:
1. 将此存储库克隆到您的本地存储并进入到该目录。
2. 运行`python3 -m venv .venv`，它将创建一个虚拟终端。
   如果您已经部署了虚拟环境，您可以直接运行`run-venv.bat`
3. 请运行`pip3 install -r Temp\__prebuild__\win32\modlist.txt`，
   如果在安装过程中出现错误，您可以在线搜索解决方案。目前，我已经为在Windows环境中安装`pygobject`时出现的错误"msvc_recommended_pragmas.h not found"提供了[可行的解决方案](https://blog.csdn.net/qq_56086478/article/details/136005175) 。
4. 运行`python3 system.py`，输入用户名和密码登录系统终端。
   如果在系统自检过程中遇到不可忽视的错误，程序会立刻停止运行，所以请不要修改一些关键代码以防止程序崩溃，也不要删除源码目录下的文件，如果报错找不到库，请用`pip`安装那个库。

### Linux && Termux:
1. 将此存储库克隆到您的本地存储并进入到该目录。
2. 运行`python3 -m venv .venv`，它将创建一个虚拟终端。
   如果您已经部署了虚拟环境，您可以直接运行`source .venv/bin/activate`
3. 请运行`pip3 install -r Temp\__prebuild__\linux\modlist.txt`，
   如果在安装过程中出现错误，您可以在线搜索解决方案。
4. 运行`python3 system.py`，输入用户名和密码登录系统终端。
   如果在系统自检过程中遇到不可忽视的错误，程序会立刻停止运行，所以请不要修改一些关键代码以防止程序崩溃，也不要删除源码目录下的文件，如果报错找不到库，请用`pip`安装那个库。

这是初始用户名和密码。  
Username|Password|Mode
----|----|----
root|root|root
user|user|user

## 帮助文档
运行“python3 system.py”，输入用户名和密码登录系统终端。然后，您可以通过输入`help`或`help [command]`来打印帮助页面。

## 参考文献
- [Detailed Annotation on Python Regex](https://zhuanlan.zhihu.com/p/479731754)
- [Detailed Annotation on Python loguru](https://blog.csdn.net/Kangyucheng/article/details/112794185)
- [SymPy 1.12 documentation Solving Guidance](https://docs.sympy.org/latest/guides/solving/solving-guidance.html)
- [SymPy Symbol Calculation(1) ](https://zhuanlan.zhihu.com/p/599743326)
- [SymPy: symbolic computing in Python. PeerJ Computer Science](https://peerj.com/articles/cs-103)
