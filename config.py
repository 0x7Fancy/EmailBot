#!/usr/bin/python3
#coding=utf-8

"""
File: config.py
Description: the EmailBot configure
Author: 0x7F@knownsec404
Time: 2022.01.10
"""

import logging

# set emailbot work log level
# level: NOTSET < DEBUG < INFO < WARNING < ERROR < CRITICAL
LOG_LEVEL = logging.INFO
# set emailbot work log format
LOG_FORMAT = "%(asctime)-15s %(levelname)-8s %(filename)s:%(lineno)d %(funcName)s: %(message)s"

# set smtp server address/port/ssl, using send email
SMTP_SERVER = "smtp.exmail.qq.com"
SMTP_PORT   = 465
SMTP_SSL    = True
# set pop3 server address/port/ssl, using receive email
POP3_SERVER = "pop.exmail.qq.com"
POP3_PORT   = 995
POP3_SSL    = True

# set email username and password
# Attention: the password is the email client password, not the account password
USERNAME = "test@test.com"
PASSWORD = "PASSWORD"
