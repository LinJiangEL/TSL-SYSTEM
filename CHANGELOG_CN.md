CHANGELOG Document  [English](/CHANGELOG.md) | [Chinese](/CHANGELOG_CN.md)

# 更新日志
本文件记录 TSL-SYSTEM 的所有重要变更。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/spec/v2.0.0.html)。

## 7.5.0 - 2026-10-21

### 新增
- **音乐模块**（`tools/Music`）：本地音乐库、通过 `execute Music` 进入的点歌台
  （`search`、`local`、`list`、`info`、`get`、`queue`、`drop`、`clear`、`dir`、`play`、`pause`、`stop`），
  以及 Windows 下基于 MCI、Linux 下基于 `ffplay` 的后台播放，因此不会阻塞终端。
- **在线音乐爬虫**（`tools/Music/crawler.py`）：网易云音乐与酷狗两个音源，合并并去重的搜索结果，
  以 `.part` 临时文件加 `os.replace` 的流式下载，内容类型与大小校验，以及针对版权受限曲目的明确
  `CrawlerError` 提示。
- **终端音乐命令**：`music play|stop|pause`、`music search KEYWORD` 和 `music get INDEX/KEYWORD`；
  通过播放状态文件与控制文件，每个 TSL-SYSTEM 进程都能控制另一个进程所拥有的播放。
- **网络模块**（`tools/Network`）：标准库实现的 DNS 客户端（A/AAAA/CNAME/MX/NS/TXT/SRV/CAA）、
  `ping`、`trace`（路由追踪）、多线程 TCP `ports` 端口扫描、`http` 分析（状态码、响应头、重定向、
  耗时、安全响应头、Cookie）、`tls` 证书检查、RFC 3912 `whois`、`local` 网卡 / 网关 / ARP 检查、
  `public` 出口 IP 与归属地、`speed` 下载测速，以及综合报告 `analyze HOST`。
- **函数分析模式**（`tools/Mathematics/cal_function.py`）：在新控制台中打开的独立绘图 REPL
  （在 advanced 模式下输入 `@window`）。支持曲线 `y1=x+2`、函数 `f(x)=2x+1`、求值 `f(2)`、变量、
  `range`/`ylim` 视窗控制、重复曲线排除、导出 PNG，以及 ASCII 备用绘图。
- **断点保护**（`guard.py`）：在 `Temp/Breakpoint.state` 中保存断点，每条命令执行前重写；崩溃、
  中断、信号与线程异常记录写入 `Temp/logs/log_breakpoint.log`；`faulthandler` 转储写入
  `Temp/logs/log_fault.log`；下次启动时打印恢复警告；并新增 `throw` 命令用于主动测试该机制。
- **统一的终端界面工具**（`tools/__built_in__/style.py`）：横幅、分隔线、标题、标签，以及彩色的
  成功 / 警告 / 错误输出，已应用于 `terminal.py`、`system.py`、`loading.py`、`help` 表格和所有
  工具模块。
- **操作日志**：终端命令、用户管理、备份 / 恢复、升级，以及音乐、网络和数学模块的操作日志，
  使用 `[CMDINFO]`、`[USERINFO]`、`[PROCESSINFO]` 和 `[MUSICINFO]` 标记。

### 变更
- **数学模块**：统一结果块（`Expression`、`Result (2)`、`Digits`、`Fraction`、`Sqrt`），采用精确的
  `Fraction` 运算，对极大的精确值使用科学计数法；重写各模式 REPL，使用正则解析参数、支持命令别名，
  并统一为 `ErrorName: message.` 形式的错误。无参数命令必须以 `@` 开头（`@help`、`@exit`、`@flush`、
  `@window` 等），且 `@exit` 直接返回终端。
- **`trunc`** 恢复为超级用户的外部命令通道：原始命令行被转发给宿主系统（Windows 使用 `cmd /C`，
  Linux 使用 `/bin/sh -c`），并上报、记录退出码。
- **音乐存放位置** 从仓库根目录的 `Music/` 迁移到 `tools/Music/Musics`
  （仍可通过环境变量 `TSL_MUSIC_DIR` 覆盖）。
- **`execute`** 现在把 `Network` 列为可用模块；`Chemistry`、`MultiMedia` 和 `Philosophy` 仍处于开发中。
- `user@TSL-SYSTEM` 提示符保持原有的无颜色样式，而横幅、提示与消息使用彩色样式。
- **版本号** 从 `5.17.4` 更新为 `7.5.0`。

### 修复
- `trunc` 不再破坏带引号的参数：`trunc python -c "import os"`、含空格的路径以及管道现在都能正常工作，
  因为命令行作为一整条字符串交给 shell，而不是先被重新转义的参数列表。
- `music pause` 和 `music stop` 现在能作用于另一个 TSL-SYSTEM 进程所拥有的播放，MCI 的线程亲和性
  （错误 263）由专门的播放引擎线程处理。
- 当日志目录中存在额外的日志文件（例如 `log_breakpoint.log` 和 `log_fault.log`）时，
  `LoggerManager` 不再索引失败。
- 复合数学：一元正负号、括号、`^`、`//`、`%` 与运算符优先级都以精确分数正确求值，非法输入会抛出
  结构化错误而不是崩溃。
- 终端命令（`internal`、`backup`、`upgrade`）现在会如实上报并记录非零退出码，而不是声称执行成功。
- Windows 下 `trunc` 的退出状态会传递回终端提示符，不再被静默丢弃。

### 移除
- 数学模块选择菜单中的 `exit` 命令（请改用 `@exit`）。
- 音乐不再存放在仓库根目录的 `Music/` 目录，而是位于 `tools/Music/Musics`。

### 安全
- `trunc` 仍然仅限超级用户使用，且从不使用 `shell=True`。

## 更早的版本
`7.5.0` 之前的版本没有维护更新日志，其历史记录在 Git 提交历史中（`git log`，自 2024-05-01 的
初始提交起）。
