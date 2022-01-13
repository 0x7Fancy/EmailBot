#!/usr/bin/python3
#coding=utf-8

"""
File: utils.py
Description: the utils function library
Author: 0x7F@knownsec404
Time: 2021.06.30
"""

import logging
import time

import config

#**********************************************************************
# @Function: logger_init()
# @Description: the global log object initialize function
# @Parameter: None
# @Return: None
#**********************************************************************
def logger_init():
    logger = logging.getLogger("emailbot")
    logger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    sh.setLevel(config.LOG_LEVEL)
    formatter = logging.Formatter(config.LOG_FORMAT)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    return logger
# end logger_init()
logger = logger_init()

#**********************************************************************
# @Function: get_format_date()
# @Description: get current time and format
# @Parameter: None
# @Return: str, the be formatted date string
#**********************************************************************
def get_format_date():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
# end get_date()

#**********************************************************************
# @Function: get_format_date()
# @Description: get current time and format
# @Parameter: None
# @Return: str, the be formatted date string
#**********************************************************************
def parse_args_server(serv):
    array = serv.split(":")
    if len(array) == 1:
        # return server address and default port 0
        return array[0], 0

    port = array[1]
    if port.isdigit():
        port = int(port)
    else:
        port = 0
    return array[0], port
# end parse_args_server()
