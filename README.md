# TSL-SYSTEM
Explorer Lab. Built-in SYSTEM. It can only work on Windows(version >= 10) or Linux(kernel-version >= 5.9).

## 开发文档
### 开发背景
    随着计算机软硬件技术的高速发展和对需要高质量工作优化的方面逐渐增多，原有的探索系统V4.12.7已无法满足部内各项工作需求，
    计算精度修正程序也出现了大量异常，精度修正补丁本身也需要修正。为了避免部内计算机软硬件技术落后于现代，经各部代表匿名
    票选后，决定由XV101担任系统总工程师，负责新系统的一切开发工作，开发任务由ENL.接管，开发进程于2022年7月14日启动。

### 系统概况
    硬件资源暂缺，组内决定先从软件入手。
    系统名称为TSL-SYSTEM，开发版本为5.17.4。
    可运行在Windows10以上以及Debian, Ubuntu, CentOS等内核版本高于5.9的系统。

    TSL-SYSTEM采用了以python为主，C和nodejs为辅的搭建方式，利用python的跨平台性和可移植性，用C语言做速度优化，
    很大程度上提高了系统性能，简化了调用过程，并增加了日志记录模块。

### 关于作者
    作者笔名：临江词客，L.J.Afres
    联系方式：linjiangxv101@qq.com
    职位：学生，XV101，部内网络安全审计系统工程师（非正式），ENL.部长

> 当我听说这个项目从头至尾都由我一个人研发，甚至开发文档和技术文档都是由我编写时，我的心情是比较兴奋和忐忑不安的，
> 我很高兴能为实验室的发展去做出一些实质性的贡献。这个系统的开发难度绝不亚于我之前编写过的项目，为此我查阅了大量的资料，
> 争取能早日将它部署进实验室并向一直以来的支持者们免费提供API接口。
> 最后向为该系统的研发提供帮助的贡献值们表达诚挚的谢意！

### 引用文献
- [详解Python正则表达式（含丰富案例）](https://zhuanlan.zhihu.com/p/479731754)
- [SymPy 1.12 documentation Solving Guidance](https://docs.sympy.org/latest/guides/solving/solving-guidance.html)
- [SymPy符号运算(1) ](https://zhuanlan.zhihu.com/p/599743326)
- [SymPy: symbolic computing in Python. PeerJ Computer Science](https://peerj.com/articles/cs-103)
- [Python日志详解-loguru](https://blog.csdn.net/Kangyucheng/article/details/112794185)

# 技术文档
> 抱歉，由于一些特殊原因，系统源码暂时被部长Encrypted了，但是我们提供了二进制可执行文件，使用它之前只需要提供给它TSL-SYSTEM-APIKEY，执行时需要更高的权限来设置系统环境变量，如果没有权限的话，你需要手动设置，下次使用时程序会自动获取变量中的API值。由于系统以单个文件运行，所以可能会出现无法使用的情况，但鉴于目前系统仍处于开发阶段，所以还望各位海涵。

## 使用方法
### 1. 启动部分  
`Windows` 双击运行TSL-SYSTEM-V5.17.4.exe  
`Linux` 在命令行窗口输入sudo ./TSL-SYSTEM-V5.17.4后回车  
`通用` 若为源码包，则运行`python3 system.py`  
    
### 2. 程序部分（运行源码时参考此部分）  
  * 若程序为第一次启动并且环境变量中未设置TSL-SYSTEM-APIKEY，程序会提示需要输入TSL-SYSTEM-APIKEY，输入完成后回车，若密钥正确，则程序会将TSL-SYSTEM-APIKEY自动设置好并进入`第一个阶段-系统自检`，否则抛出cryptography.fernet.InvalidToken的异常，表示密钥错误，如图所示。
    ![Input-APIKey](doc/ask-apikey.png)
    ![Correct](doc/correct-apikey.png)
    ![Incorrect](doc/incorrect-apikey.png)
  * 自检完毕后，系统会导入用户数据库，系统默认有两个用户，在输入正确的用户密码后，系统调用terminal.py中的terminal函数并传入当前登录的用户信息，写入PwdUser后，进入系统终端。  
    ![LoginOk](doc/login-ok.png)
  * 用户名或密码错误，如图所示。  
    ![LoginFailed](doc/login-username-wrong.png)
    ![LoginFailed](doc/login-password-wrong.png)
  * 输入`help`可以查看命令帮助，输入`execute`可以进入内部功能界面。
    ![HelpPage](doc/helppage.png)
    ![ExecutePage](doc/execute-available.png)
### 3. 指令功能部分
  * help : 打印帮助页面。
  * sudo : 以SuperUser权限执行指令。
  * backup : 创建一份系统备份。
  * restore : 从已创建的系统备份中选择一个时间节点去还原系统。
  * execute : 进入内部模块终端。
  * user : 用户管理指令组。
  * trunc : 外部命令执行声明。
  * internal : 内部命令执行声明。
  * exit : 正常关闭系统，释放并初始化指令组。
---
以下是上面指令的一些使用示例。  
(1)**user**  
  
![add](doc/user-add-user.png)
![add](doc/user-add-root.png)
![list](doc/user-list.png)
![remove](doc/user-remove-others.png)
![remove](doc/user-remove-super-or-oneself.png)
![set](doc/user-set-username.png)
![set](doc/user-set-mode.png)
![set](doc/user-set-password.png)
![set](doc/user-set-root.png)
![info](doc/user-info.png)
  
(2)**trunc**
![trunc](doc/trunc.png)
  
(3)**internal**  
由于系统仍处于开发阶段，bin目录虽然框架搭建好了，但是内部命令还没有从旧系统迁入，所以internal目前属于`光杆标志`。

### 4. 模块功能部分（目前只提供下面模块的调用）
  * Passwd：调用了实验室信息处理机制，可以对信息进行可逆加密，得到的密文只有该工具可以执行解密，支持中英文和一些特定的表情符号还有特殊字符。
    ![EN](doc/Passwd-EN.png)
    ![CN](doc/Passwd-CN.png)
    ![Special](doc/Passwd-support-special.png)
  * Translate: 可以进行中英文翻译，调用了一些平台的API(如有道、百度、搜狗)，支持实时基于单词的发音播放。
    ![Common](doc/Translate-common.png)
    ![Senior](doc/Translate-senior.png)
    ![Reader](doc/Translate-reader.png)
  * Mathematics：支持一些基本的运算，高级运算目前只加入了解方程（组），系统运算精度为8bit，运算速度以搭载平台的性价比为准。
      
    (1)**basic**
    ![add](doc/Mathematics-basic-add.png)
    ![sub](doc/Mathematics-basic-sub.png)
    ![mul&div](doc/Mathematics-basic-mul-div.png)
    ![fdiv&mod](doc/Mathematics-basic-fdiv-mod.png)
    ![pow&sqrt](doc/Mathematics-basic-pow-sqrt.png)
    ![abs&sqr](doc/Mathematics-basic-abs-sqr.png)
      
    (2)**advanced**
    ![Equation(s)](doc/Mathematics-advanced-Solve_equation(s).png)

## 5. 系统原理
系统原理这部分内容要等到系统全部完成，源码开放之后再写，要不然刚写好，冒出好多bug，程序要改，技术文档也要改，不如完成之后再写这块内容。
