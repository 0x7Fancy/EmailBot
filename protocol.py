#!/usr/bin/python3
#coding=utf-8

"""
File: protocol.py
Description: the email protocol wrapper, implement SMTP / POP3
Author: 0x7F@knownsec404
Time: 2021.06.23
"""

import smtplib
import poplib

import config
import mime
from utils import logger

#**********************************************************************
# @Class: SMTP
# @Description: implement and warpper SMTP protocol multi commands, and provide
#   external sending interface
#**********************************************************************
class SMTP:
    #**********************************************************************
    # @Function: __init__(self, address, port, ssl, user, passwd)
    # @Description: SMTP object initialize
    # @Parameter: address, the SMTP server address
    # @Parameter: port, the SMTP server port
    # @Parameter: ssl, ssl is required to connect to the SMTP
    # @Parameter: username, the mailbox username
    # @Parameter: password, the mailbox password
    # @Return: None
    #**********************************************************************
    def __init__(self, address, port, ssl, user, passwd):
        self.address = address
        self.port    = port
        self.ssl     = ssl
        self.user    = user
        self.passwd  = passwd

        # set value by "check_status()"
        self.status  = False
    # end __init__()

    #**********************************************************************
    # @Function: _login_server(self)
    # @Description: connect and login in SMTP server
    # @Parameter: None
    # @Return: smtp, the connectd SMTP object
    #**********************************************************************
    def _login_server(self):
        # connect smtp server
        try:
            if self.ssl:
                smtp = smtplib.SMTP_SSL(self.address, self.port)
            else:
                smtp = smtplib.SMTP(self.address, self.port)
        except Exception as e:
            logger.error(e)
            return False, None

        # if the log level is DEBUG
        import logging
        if config.LOG_LEVEL <= logging.DEBUG:
            smtp.set_debuglevel(1)

        # login in smtp server
        try:
            smtp.login(self.user, self.passwd)
        except Exception as e:
            smtp.close()
            logger.error(e)
            return False, None

        return True, smtp
    # end _login_server()

    #**********************************************************************
    # @Function: check_status(self)
    # @Description: check SMTP server and user/pass status
    # @Parameter: None
    # @Return: status, return True when SMTP server is ok and user/pass is authed
    #**********************************************************************
    def check_status(self):
        status, smtp = self._login_server()
        if status:
            self.status = True
            smtp.quit()
        return status
    # end check_status()

    #**********************************************************************
    # @Function: send(self, email)
    # @Description: send email through SMTP server
    # @Parameter: email, the mime email object
    # @Return: status, return True when email send success
    #**********************************************************************
    def send(self, email):
        # connect/auth smtp server and send
        status, smtp = self._login_server()
        if status == False:
            return False

        try:
            smtp.sendmail(email.sender, email.receiver, email.MIME.as_string())
            smtp.quit()
        except Exception as e:
            logger.error(e)
            smtp.close()
            return False
        return True
    # end send()
# end class

#**********************************************************************
# @Class: POP3
# @Description: implement and warpper POP3 protocol multi commands, and provide
#   external sending interface
#**********************************************************************
class POP3:
    #**********************************************************************
    # @Function: __init__(self, address, port, ssl, user, passwd)
    # @Description: POP3 object initialize
    # @Parameter: address, the POP3 server address
    # @Parameter: port, the POP3 server port
    # @Parameter: ssl, ssl is required to connect to the POP3
    # @Parameter: username, the mailbox username
    # @Parameter: password, the mailbox password
    # @Return: None
    #**********************************************************************
    def __init__(self, address, port, ssl, user, passwd):
        self.address = address
        self.port    = port
        self.ssl     = ssl
        self.user    = user
        self.passwd  = passwd

        # set value by "check_status()"
        self.status  = False
    # end __init__()

    #**********************************************************************
    # @Function: _login_server(self)
    # @Description: connect and login in POP3 server
    # @Parameter: None
    # @Return: pop3, the connectd POP3 object
    #**********************************************************************
    def _login_server(self):
        # connect pop3 server
        try:
            if self.ssl:
                pop3 = poplib.POP3_SSL(self.address, self.port)
            else:
                pop3 = poplib.POP3(self.address, self.port)
        except Exception as e:
            logger.error(e)
            return False, None

        # if the log level is DEBUG
        import logging
        if config.LOG_LEVEL <= logging.DEBUG:
            pop3.set_debuglevel(1)

        # login in pop3 server
        try:
            pop3.user(self.user)
            pop3.pass_(self.passwd)
        except Exception as e:
            logger.error(e)
            pop3.close()
            return False, None

        return True, pop3
    # end _login_server()

    #**********************************************************************
    # @Function: check_status(self)
    # @Description: check POP3 server and user/pass status
    # @Parameter: None
    # @Return: status, return True when POP3 server is ok and user/pass is authed
    #**********************************************************************
    def check_status(self):
        status, pop3 = self._login_server()
        if status:
            self.status = True
            pop3.quit()
        return status
    # end check_status()

    #**********************************************************************
    # @Function: stat(self)
    # @Description: get mailbox status, include message count and mailbox size,
    #   we just return message count
    # @Parameter: None
    # @Return: count, the message count, while error will return -1
    #**********************************************************************
    def stat(self):
        # connect/auth pop3 server
        status, pop3 = self._login_server()
        if status == False:
            return -1

        # get email status
        try:
            count, octets = pop3.stat()
            pop3.quit()
        except Exception as e:
            logger.error(e)
            pop3.close()
            return -1

        return count
    # end stat()

    #**********************************************************************
    # @Function: uidl(self, which=0)
    # @Description: get all message hash or get the hash of the mail with the
    #   specified id.
    # @Parameter: which=0, message id, when the value less than or equal to 0,
    #   return the specified mail hash.
    # @Return: result, the email hash list or hash string
    #   the single hash example: b'1 ZC3130-wi6DhoW5iDuIEDhYOkraUbh'
    #**********************************************************************
    def uidl(self, which=0):
        # connect/auth pop3 server
        status, pop3 = self._login_server()
        if status == False:
            return None

        # get all email message digest (unique id) list
        result = None
        try:
            if which > 0:
                # get the uuid of the specified mail
                line = pop3.uidl(which)
                # check response with "+OK"
                if line.decode("utf-8").startswith("+OK"):
                    result = line[4:]
            else:
                # get the uuid of all emails
                resp, lines, octets = pop3.uidl()
                # check response with "+OK"
                if resp.decode("utf-8").startswith("+OK"):
                    result = lines
            # end if-else
            pop3.quit()
        except Exception as e:
            logger.error(e)
            pop3.close()
            return None

        return result
    # end uidl()

    #**********************************************************************
    # @Function: recv(self, which)
    # @Description: get the email content of the specified id, the original
    #   content of the received email is parsed through MIME.
    # @Parameter: which, the email id
    # @Return: email, our internal warpper Email object
    #**********************************************************************
    def recv(self, which):
        # connect/auth pop3 server
        status, pop3 = self._login_server()
        if status == False:
            return None

        # get email message by id
        try:
            resp, lines, octets = pop3.retr(which)
            pop3.quit()
        except Exception as e:
            logger.error(e)
            pop3.close()
            return None

        # check resp
        if resp.decode("utf-8").startswith("-ERR"):
            logger.warning("pop3 response ERR: %s" % resp)
            return None
        # join each line of email message content and decode the data with
        # utf-8 charset encoding.  
        content = b'\r\n'.join(lines).decode("utf-8", "ignore")
        return mime.Email(source=content)
    # end recv()
# end class
