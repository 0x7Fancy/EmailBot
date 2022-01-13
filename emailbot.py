#!/usr/bin/python3
#coding=utf-8

"""
File: main.py
Description: the EmailBot entry point and main logic
Author: 0x7F@knownsec404
Time: 2021.06.21
"""

import argparse
import threading
import time

# patch import path
import os
import sys
module_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(module_path)

import config
import interact
import mime
import protocol
import rule
import utils
from utils import logger

VERSION = "EmailBot v0.1.1 (build 20220112)"

#**********************************************************************
# @Class: EmailBot
# @Description: the emailbox main schedule logic, handle the sending and
#   receiving of emails, as well as the judgment of the rules, and provide an
#   external calling interface
#**********************************************************************
class EmailBot:
    #**********************************************************************
    # @Function: __init__(self, smtp="", pop3="", smtp_port=0, pop3_port=0,
    #            smtp_ssl=False, pop3_ssl=False)
    # @Description: the EmailBot object initialize
    # @Parameter: smtp="", the SMTP server address, using configure if empty
    # @Parameter: pop3="", the POP3 server address, using configure if empty
    # @Parameter: smtp_port=0, the SMTP server port, using configure if empty
    # @Parameter: pop3_port=0, the POP3 server port, using configure if empty
    # @Parameter: smtp_ssl=False, ssl is required to connect to the SMTP,
    #             using configure if empty
    # @Parameter: pop3_ssl=False, ssl is required to connect to the POP3,
    #             using configure if empty
    # @Return: None
    #**********************************************************************
    def __init__(self, smtp="", pop3="", smtp_port=0, pop3_port=0,
                smtp_ssl=False, pop3_ssl=False):
        # initialize field
        self.smtp_address = smtp      if smtp else config.SMTP_SERVER
        self.smtp_port    = smtp_port if smtp_port else config.SMTP_PORT
        self.smtp_ssl     = smtp_ssl  if smtp_ssl else config.SMTP_SSL
        self.pop3_address = pop3      if pop3 else config.POP3_SERVER
        self.pop3_port    = pop3_port if pop3_port else config.POP3_PORT
        self.pop3_ssl     = pop3_ssl  if pop3_ssl else config.POP3_SSL

        # reset/initialize value by "self.login()"
        self.username = config.USERNAME
        self.password = config.PASSWORD
        self.smtp = None
        self.pop3 = None

        # email send/receive mananger
        self._send_queue = []
        self._mutex = threading.Lock()
        self._recv_cache = None

        # the rule list, add it by "interact.py" && "add_rule()"
        self.rule = []
        for name in interact.INTERACTS:
            logger.debug("load [%s] rule from config.py" % name)
            self.rule.append(interact.INTERACTS[name])
    # end __init__()

    #**********************************************************************
    # @Function: _send_manager(self)
    # @Description: send email manager, when the user sends a email, the email to
    #   be sent is added to the queue, and the manager will be sent one by one in
    #   order; when the sending is wrong, manager will automatically retry until it
    #   succeeds (usually due to network reasons or temporary failures, because
    #   login() check has been passed)
    # @Parameter: None
    # @Return: None
    #**********************************************************************
    def _send_manager(self):
        while True:
            # check and get the email waiting to be sent
            self._mutex.acquire()
            wait_count = len(self._send_queue)
            if wait_count > 0:
                e = self._send_queue[0]
            else:
                e = None
            self._mutex.release()

            if e == None:
                time.sleep(10)
                continue

            logger.info("send email [%s] to %s" % (e.subject, e.receiver))
            # send email, when it fails, we will not remove this email,
            # it will try again in the next loop
            result = self.smtp.send(e)
            if result == False:
                # wait a little longer
                time.sleep(60)
                continue
            
            # send success, remove this email
            self._mutex.acquire()
            self._send_queue = self._send_queue[1:]
            self._mutex.release()
        # end while
    # end _send_manager()

    #**********************************************************************
    # @Function: _recv_manager(self)
    # @Description: receiver email manager, each time the uidl() list is polled
    #   from the email server, the hash of the new and old emailing lists is
    #   compared to distinguish which are new emails. when new emails are received,
    #   they are parsed and the rules are matched, and call callback function.
    #
    #   Here we need to use hash to distinguish new emails, instead of using the
    #   number of emails directly, because:
    #     1.you can choose the time range for receiving email(eg: 30day / 90day /
    #     1year), when the time node is switched, the number of received email
    #     will change(reduce), 
    #     2.when we manually delete emails, the number of mailboxes will also change
    #   so the number of mailboxes cannot be directly used to determine new email
    #
    #   every time we poll the hash of the inbox mail through uidl(), if there are
    #   too many inbox mails and the time range for receiving mail is not set, it
    #   will cause additional resource cost; the user can manually set the time
    #   range for receiving mail in the mailbox to optimize the problem
    # @Parameter: None
    # @Return: None
    #**********************************************************************
    def _recv_manager(self):
        while True:
            old_cache = self._recv_cache
            self._recv_cache = self.pop3.uidl()

            # _recv_manager() need initialize or get uidl error
            if old_cache == None or self._recv_cache == None:
                time.sleep(10)
                continue
            # end if

            # find new email start position
            # we start to compare the last item of old_cache with the new
            # result. if it is not found, it means that the last email has been
            # deleted. use the previous item of old_cache to continue to find
            # the starting position of the new email.
            position = -1
            for oc in reversed(old_cache):
                for nc in reversed(self._recv_cache):
                    _, ohash = self._parse_uidl_line(oc)
                    nid, nhash = self._parse_uidl_line(nc)
                    if ohash == nhash:
                        position = nid
                        break
                # end for
                if position >= 0:
                    break
            # end for

            # receive or one or more emails
            for i in range(position+1, len(self._recv_cache)+1):
                # receive new email
                e = self.pop3.recv(i)
                if e == None:
                    continue
                logger.info("receive new email [%s] by %s" % (e.subject, e.sender))
                # rule check and execute
                self._route_by_rules(self, e)
            # end for
            time.sleep(60)
        # end while
    # end _recv_manager()

    #**********************************************************************
    # @Function: _parse_uidl_line(self, line)
    # @Description: parse uidl single line data
    #   the uidl() single response format: b'1 ZC3130-wi6DhoW5iDuIEDhYOkraUbh'
    # @Parameter: line, the single line uidl data
    # @Return: (id, hash), the email id and hash
    #**********************************************************************
    def _parse_uidl_line(self, line):
        # in the current context, the line has been checked, and the default
        # line is the correct format here 
        array = line.decode("utf-8").split(" ")
        return int(array[0]), array[1]
    # end _parse_uidl_line()

    #**********************************************************************
    # @Function: _route_by_rules(self, eb, e)
    # @Description: use all rules to match the content of new emails, when a rule
    #   is successfully matched, subsequent rules will no longer match.
    #   priority of routing rules, subject to the order of addition.
    #   between multiple conditions is AND
    # @Parameter: eb, the emailbot object
    # @Parameter: e, the email object
    # @Return: None
    #**********************************************************************
    def _route_by_rules(self, eb, e):
        for r in self.rule:
            if r.execute(eb, e):
                break
        # end for
    # end _route_by_rules()

    #**********************************************************************
    # @Function: login(self, username="", password="")
    # @Description: initialize user/pass and server status, and check status
    # @Parameter: username="", the mailbox username, using configure if empty
    # @Parameter: password="", the mailbox password, using configure if empty
    # @Return: status, all server and user/pass is ready
    #**********************************************************************
    def login(self, username="", password=""):
        if username != "":
            self.username = username
        if password != "":
            self.password = password

        result = False
        if self.smtp_address == "" and self.pop3_address == "":
            logger.error("at least one of smtp/pop3 needs to be started")
            return result

        # check smtp && pop3 server status and user auth status
        result = 1
        if self.smtp_address != "":
            self.smtp = protocol.SMTP(self.smtp_address, self.smtp_port,
                        self.smtp_ssl, self.username, self.password)
            if self.smtp.check_status():
                logger.info("smtp server is ready, user auth success")
            else:
                result = result & 0
        # end if
        if self.pop3_address != "":
            self.pop3 = protocol.POP3(self.pop3_address, self.pop3_port,
                        self.pop3_ssl, self.username, self.password)
            if self.pop3.check_status():
                logger.info("pop3 server is ready, user auth success")
            else:
                result = result & 0
        # end if

        return result == 1
    # end login()

    #**********************************************************************
    # @Function: add_rule(self, callback, sender="", subject="", content="", func=None)
    # @Description: add a rule for matching receive new email, when all the rules
    #   are empty, it means all match.
    # @Parameter: callback, when the rule is successfully matched, the callback
    #   function that needs to be executed
    # @Parameter: sender="", regexp rule which match sender
    # @Parameter: subject="", regexp rule which match subject
    # @Parameter: content="", regexp rule which match content
    # @Parameter: func=None, custom rule match function
    # @Return: None
    #**********************************************************************
    def add_rule(self, callback, sender="", subject="", content="", func=None):
        r = rule.Rule(callback, sender, subject, content, func)
        logger.debug("load [%s] rule by 'add_rule()'" % callback.__name__)
        self.rule.append(r)
    # end add_rule()

    #**********************************************************************
    # @Function: send_email(self, to, cc="", subject="", content="", attachment="", blocking=False)
    # @Description: the user calls this function to send email.
    #   if blocking=True, the email will be added to the queue to be sent, the
    #   email will auto sent and retry.
    #   if blocking=False, the email will send directly, and return send result
    # @Parameter: to, the email receiver
    # @Parameter: cc="", the email carbon copy
    # @Parameter: subject="", the email subject
    # @Parameter: content="", the email content
    # @Parameter: attachment="", the email attachment file path
    # @Parameter: blocking=False, blocking or not send mode
    # @Return: None
    #**********************************************************************
    def send_email(self, to, cc="", subject="", content="", attachment="", blocking=False):
        # check smtp object is ready
        if self.smtp == None:
            logger.error("smtp server not initialize")
            return

        # create mime Email object
        e = mime.Email(self.username, to, cc, subject, content, attachment)

        # blocking send mode
        if blocking:
            return self.smtp.send(e)

        # non-blocking send mode
        # add new email into send queue
        self._mutex.acquire()
        self._send_queue.append(e)
        self._mutex.release()
    # end send_email()

    #**********************************************************************
    # @Function: run(self, daemon=False)
    # @Description: the emailbot launch entrypoint
    # @Parameter: daemon=False, set background running, facilitate that emailbot
    #   can be run as a service or be called as a library.
    # @Return: None
    #**********************************************************************
    def run(self, daemon=False):
        # "login()" is not called, or neither smtp/pop3 is set
        if self.smtp_address == "" and self.pop3_address == "":
            logger.critical("at least one of smtp/pop3 needs to be started")
            return

        # user want to use smtp(send email)
        if self.smtp_address != "":
            if self.smtp == None or self.smtp.status == False:
                logger.error("smtp/user status is not ready")
                return
            logger.info("initialize send email manager")
            ts = threading.Thread(target=self._send_manager)
            ts.start()
        # end if

        # user want to use pop3(receive email)
        if self.pop3_address != "":
            if self.pop3 == None or self.pop3.status == False:
                logger.error("pop3/user status is not ready")
                return
            logger.info("initialize recv email manager")
            tr = threading.Thread(target=self._recv_manager)
            tr.start()
        # end if

        # set daemon
        if daemon == False:
            if self.smtp_address != "":
                ts.join()
            if self.pop3_address != "":
                tr.join()
        # end if
    # end run()
# end class

#**********************************************************************
# @Function: main()
# @Description: main entry point
# @Parameter: None
# @Return: None
#**********************************************************************
if __name__ == "__main__":
    # arguments parse
    parser = argparse.ArgumentParser(description="EmailBot launch arguments as service")
    parser.add_argument("-u", "--username", type=str, default="", help="the emailbox username")
    parser.add_argument("-p", "--password", type=str, default="", help="the emailbox password")

    parser.add_argument("--smtp",     type=str, default="", help="SMTP server address(address:port)")
    parser.add_argument("--smtpssl",  type=bool, default=False, help="connect SMTP server with ssl")
    parser.add_argument("--pop3",     type=str, default="", help="POP3 server address(address:port)")
    parser.add_argument("--pop3ssl",  type=bool, default=False, help="connect POP3 server with ssl")

    parser.add_argument("-v", "--version", help="print emailbot version", action="store_true")
    args = parser.parse_args()

    if args.version:
        print(VERSION)
        exit(0)
    # end if

    # parse smtp/pop3 server address and port
    smtp, smtpport = utils.parse_args_server(args.smtp)
    pop3, pop3port = utils.parse_args_server(args.pop3)

    # launch emailbot
    logger.info("launch Emailbot ...")
    eb = EmailBot(smtp=smtp, smtp_port=smtpport, smtp_ssl=args.smtpssl,
                  pop3=pop3, pop3_port=pop3port, pop3_ssl=args.pop3ssl)

    status = eb.login(args.username, args.password)
    if not status:
        logger.error("Emailbot check SMTP/POP3/USER failed") 
        exit(0)

    #eb.add_rule()
    eb.run()
# end main()
