#!/usr/bin/python3
#coding=utf-8

"""
File: interact.py
Description: rule and callback functin pairs.
Author: 0x7F@knownsec404
Time: 2021.06.23
"""

import re

import rule

#**********************************************************************
# @Function: callback_debug_show(email, regx)
# @Description: the callback, using debug print email and regx informations
# @Parameter: emailbot, the EmailBot object
# @Parameter: email, the Email object include email content
# @Parameter: regx, the dict that include result matched by rule
# @Return: None
#**********************************************************************
def callback_debug_show(emailbot, email, regx):
    print("callback_debug_show()")
    print("Email=>")
    print(email)
    print("Regx=>")
    print(regx)
# end callback_func()


#**********************************************************************
# @Function: rule_get_namd_id(email)
# @Description: the rule, match email content "name" and "id"
# @Parameter: email, the Email object include email content
# @Return: (match, regx), return match result, and return extracted fields as dictionary
#**********************************************************************
def rule_get_namd_id(email):
    content = email.content
    name = re.search("name=(.*)", content, re.I)
    uid = re.search("id=(.*)", content, re.I)

    if name and uid:
        regx = {"name": name.groups()[0], "id": uid.groups()[0]}
        return True, regx
    else:
        return False, {}
# end rule_get_namd_id()
#**********************************************************************
# @Function: callback_return_name_id(email, regx)
# @Description: the callback, get "name" and "id" and send email
# @Parameter: emailbot, the EmailBot object
# @Parameter: email, the Email object include email content
# @Parameter: regx, the dict that include result matched by rule
# @Return: None
#**********************************************************************
def callback_return_name_id(emailbot, email, regx):
    print("callback_return_name_id()")
    print("name =>", regx["name"])
    print("id =>", regx["id"])

    print("send response email")
    content  = "get info:\n"
    content += "name => %s\n" % regx["name"]
    content += "id => %s\n" % regx["id"]
    content += "by emailbot"
    emailbot.send_email("test@test.com", "name_id_test", content)
# end callback_return_name_id()

# register emailbot receive email rule and callback function
INTERACTS = {
    # work_name: [Rule]
    "debug": rule.Rule(callback_debug_show),
}
