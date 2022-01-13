#!/usr/bin/python3
#coding=utf-8

"""
File: rule.py
Description: the emailbot rule implement, matching for receiving emails
Author: 0x7F@knownsec404
Time: 2021.06.23
"""

import re
import threading

from utils import logger

#**********************************************************************
# @Class: Rule
# @Description: manage and match rules, extract the content of received emails,
#   and call callback functions
#**********************************************************************
class Rule:
    #**********************************************************************
    # @Function: __init__(self, callback, sender="", subject="", content="", func=None):
    # @Description: Rule object initialize
    # @Parameter: callback, when the rule is successfully matched, the callback
    #   function that needs to be executed
    # @Parameter: sender="", regexp rule which match sender
    # @Parameter: subject="", regexp rule which match subject
    # @Parameter: content="", regexp rule which match content
    # @Parameter: func=None, custom rule match function
    # @Return: None
    #**********************************************************************
    def __init__(self, callback, sender="", subject="", content="", func=None):
        self.sender  = sender
        self.subject = subject
        self.content = content
        self.func    = func

        self.callback = callback
    # end __init__()

    #**********************************************************************
    # @Function: execute(self, emailbot, email):
    # @Description: match all rules, call the callback function after the match
    #   is successful; (multiple conditions are AND)
    # @Parameter: emailbot, the emailbot object
    # @Parameter: email, the email object
    # @Return: match, rule matched or not
    #**********************************************************************
    def execute(self, emailbot, email):
        try:
            match_sender  = re.search(self.sender, email.sender, re.M|re.I)
            match_subject = re.search(self.subject, email.subject, re.M|re.I)
            match_content = re.search(self.content, email.content, re.M|re.I)
            if self.func != None:
                match_func, regx = self.func(email)
            else:
                match_func, regx = True, {}
        except Exception as e:
            logger.error(e)
            return False

        # check each result (AND)
        if not (match_sender and match_subject and match_content and match_func):
            return False
        # matched and set regx dict
        regx["sender"] = match_sender.group()
        regx["subject"] = match_subject.group()
        regx["content"] = match_content.group()

        # execute callback
        logger.info("MATCH %s" % self)
        te = threading.Thread(target=self.callback, args=(emailbot, email, regx))
        te.start()
        return True
    # end check()

    #**********************************************************************
    # @Function: __repr__(self)
    # @Description: rewrite __str__ function, print complete "Rule" object informations
    # @Parameter: None
    # @Return: str
    #**********************************************************************
    def __repr__(self):
        if self.func == None:
            funcname = ""
        else:
            funcname = self.func.__name__
        return f"RULE ({self.callback.__name__}) <{self.sender}> [{self.subject}] {self.content} ({funcname})"
    # end __repr__()

    #**********************************************************************
    # @Function: __str__(self)
    # @Description: rewrite __str__ function, just call __repr__()
    # @Parameter: None
    # @Return: str
    #**********************************************************************
    def __str__(self):
        return self.__repr__()
    # end __str__()
# end class
