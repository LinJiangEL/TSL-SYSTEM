/*
 * Copyright (C) 2008 The Android Open Source Project
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *  * Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *  * Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
 * OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */

#pragma once

/**
 * @file utmp.h
 * @brief POSIX login records.
 */

#include <sys/cdefs.h>
#include <sys/types.h>
#include <time.h>

#define _PATH_UTMP      "/data/data/com.termux/files/usr/var/run/utmp"
#define _PATH_WTMP      "/data/data/com.termux/files/usr/var/log/wtmp"
#define _PATH_LASTLOG   "/data/data/com.termux/files/usr/var/log/lastlog"

#ifdef __LP64__
#define UT_NAMESIZE 32
#define UT_LINESIZE 32
#define UT_HOSTSIZE 256
#else
#define UT_NAMESIZE 8
#define UT_LINESIZE 8
#define UT_HOSTSIZE 16
#endif

#define EMPTY         0
#define RUN_LVL       1
#define BOOT_TIME     2
#define NEW_TIME      3
#define OLD_TIME      4
#define INIT_PROCESS  5
#define LOGIN_PROCESS 6
#define USER_PROCESS  7
#define DEAD_PROCESS  8
#define ACCOUNTING    9

struct lastlog {
  time_t ll_time;
  char ll_line[UT_LINESIZE];
  char ll_host[UT_HOSTSIZE];
};

struct exit_status {
  short int e_termination;
  short int e_exit;
};

struct utmp {
  short int ut_type;
  pid_t ut_pid;
  char ut_line[UT_LINESIZE];
  char ut_id[4];
  char ut_user[UT_NAMESIZE];
  char ut_host[UT_HOSTSIZE];

  struct exit_status ut_exit;

  long int ut_session;
  struct timeval ut_tv;

  int32_t ut_addr_v6[4];
  char unused[20];
};

#define ut_name ut_user
#define ut_time ut_tv.tv_sec
#define ut_addr ut_addr_v6[0]

__BEGIN_DECLS

/**
 * Does nothing.
 */
int utmpname(const char* __path);
/**
 * Does nothing.
 */
void setutent(void);
/**
 * Does nothing.
 */
struct utmp* getutent(void);
/**
 * Does nothing.
 */
struct utmp* pututline(const struct utmp* __entry);
/**
 * Does nothing.
 */
void endutent(void);

/**
 * [login_tty(3)](https://www.man7.org/linux/man-pages/man3/login_tty.3.html)
 * prepares for login on the given file descriptor.
 *
 * See also forkpty() which combines openpty(), fork(), and login_tty().
 *
 * Returns 0 on success and returns -1 and sets `errno` on failure.
 *
 * Available since API level 23.
 */

#if __ANDROID_API__ >= 23
int login_tty(int __fd) __INTRODUCED_IN(23);
#endif /* __ANDROID_API__ >= 23 */


__END_DECLS
