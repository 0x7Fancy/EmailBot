#!/usr/bin/python3
#coding=utf-8

"""
File: mime.py
Description: the MIME email parser, reference from:
    <https://www.dev2qa.com/python-parse-emails-and-attachments-from-pop3-server-example/>
Author: 0x7F@knownsec404
Time: 2021.06.25
"""

import mimetypes
import os
from email.header import decode_header, make_header
from email.message import EmailMessage
from email.parser import Parser

#**********************************************************************
# @Class: Email
# @Description: the emailbot warpped Email class, support mutual conversion
#   between MIME format and plaintext.
#**********************************************************************
class Email:
    #**********************************************************************
    # @Function: __init__(self, sender="", receiver="", cc="", subject="", content="",
    #            attachment="", source=""):
    # @Description: Email object initialize, and auto convert another format
    #   set plaintext email content, it will auto convert to MIME, otherwise.
    # @Parameter: sender="", the email sender
    # @Parameter: receiver="", the email receiver
    # @Parameter: cc="", the email carbon copy
    # @Parameter: subject="", the email subject
    # @Parameter: content="", the email content
    # @Parameter: attachment="", the email attachment file path
    # @Parameter: source="", the MIME email source data
    # @Return: None
    #**********************************************************************
    def __init__(self, sender="", receiver="", cc="", subject="", content="",
                attachment="", source=""):
        # initliaze field
        self.sender     = sender
        self.receiver   = receiver
        self.cc         = cc
        self.subject    = subject
        self.content    = content
        self.attachment = attachment
        self.source     = source
        # MIME object
        self.MIME       = None

        # convert email string to MIME, or MIME source to string
        if self.source == "":
            self._pack()
        else:
            self._unpack()
    # end __init()

    #**********************************************************************
    # @Function: _pack(self)
    # @Description: convert plaintext email to MIME email
    # @Parameter: None
    # @Return: None
    #**********************************************************************
    def _pack(self):
        # create the container email message.
        self.MIME = EmailMessage()
        # set email item into MIME format
        self.MIME['Subject'] = self.subject
        self.MIME['From'] = self.sender
        self.MIME['To'] = self.receiver
        self.MIME['Cc'] = self.cc
        self.MIME.set_content(self.content)
        
        # set attachment into MIME if need
        if self.attachment == None or self.attachment == "":
            return
        # read attachment content
        try:
            with open(self.attachment, "rb") as f:
                data = f.read()
        except Exception as e:
            logger.error(e)
            return
        # get attachment type
        types, _ = mimetypes.guess_type(self.attachment)
        if types == None:
            # no guess could be made, use a generic bag-of-bits type.
            types = 'application/octet-stream'
        # end if
        maintype, subtype = types.split('/')
        filename = os.path.basename(self.attachment)
        self.MIME.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)
    # end _pack()

    #**********************************************************************
    # @Function: _unpack(self)
    # @Description: convert MIME email to plaintext
    # @Parameter: None
    # @Return: None
    #**********************************************************************
    def _unpack(self):
        # parse the email string to a MIMEMessage object.
        msg = Parser().parsestr(self.source)

        # 1.parse header
        self.sender = self._get_header(msg, "From", "")
        self.receiver = self._get_header(msg, "To", "")
        self.cc = self._get_header(msg, "Cc", "")
        self.subject = self._get_header(msg, "Subject", "")

        # 2.parse body
        # if the email contains multiple part
        self.content = self._parse_content(msg)
    # end _unpack()

    #**********************************************************************
    # @Function: _get_header(self, msg, key, default)
    # @Description: parse email header data from MIME, and decode with UTF-8
    # @Parameter: msg, the MIME message object
    # @Parameter: key, the key of value
    # @Parameter: default, the default value
    # @Return: value, the value of header field
    #**********************************************************************
    def _get_header(self, msg, key, default):
        # get value by key with default
        value = msg.get(key, default)
        # decode default method
        return str(make_header(decode_header(value)))

    #**********************************************************************
    # @Function: _parse_content(self, msg)
    # @Description: parse email content data from MIME, and decode with UTF-8
    # @Parameter: msg, the MIME message object
    # @Return: result, the message plaintext content
    #**********************************************************************
    def _parse_content(self, msg):
        content_type = msg.get_content_type().lower()
        result = ""

        # if the message part is text part
        if content_type == "text/plain" or content_type == "text/html":
            # get text content.
            content = msg.get_payload(decode=True)
            charset = msg.get_charset()
            if charset == None:
                # set default charset "utf-8"
                charset = "utf-8"
                # get message "Content-Type" header value.
                ct = msg.get("Content-Type", "").lower()
                pos = ct.find("charset=")
                if pos >= 0:
                    charset = ct[pos+8:].strip()
                    pos = charset.find(";")
                    if pos >= 0:
                        charset = charset[0:pos]
                    # end if
                # end if
            # end if
            # the encoding in the email may be incorrect, we need to handle
            # with the exception
            try:
                result = content.decode(charset)
            except:
                logger.error("content decode failed (%s)" % str(content))
                result = ""

        # if this message part is still multipart such as:
        # 'multipart/mixed', 'multipart/alternative', 'multipart/related'
        elif content_type.startswith("multipart"):
            parts = msg.get_payload()
            # loop in the multiple part list.
            for part in parts:
                # parse each message part.
                result += self._parse_content(part)

        # if this message part is an attachment part that means it is a attached file
        elif content_type.startswith("image") or content_type.startswith("application"):
            # pass, we not to parse atttachment
            """
            # get message header 'Content-Disposition''s value and parse out attached file name.
            attach_file_info_string = msg.get('Content-Disposition')
            prefix = 'filename="'
            pos = attach_file_info_string.find(prefix)
            attach_file_name = attach_file_info_string[pos + len(prefix): len(attach_file_info_string) - 1]
            
            # get attached file content.
            attach_file_data = msg.get_payload(decode=True)
            # get current script execution directory path. 
            current_path = os.path.dirname(os.path.abspath(__file__))
            # get the attached file full path.
            attach_file_path = current_path + '/' + attach_file_name
            # write attached file content to the file.
            with open(attach_file_path,'wb') as f:
                f.write(attach_file_data)
            """
        else:
            # pass, we not to parse other type
            """
            result = msg.as_string()
            """
        # end if
        return result
    # end _parse_content()

    #**********************************************************************
    # @Function: __repr__(self)
    # @Description: rewrite __str__ function, print complete "Email" plaintext
    # @Parameter: None
    # @Return: str
    #**********************************************************************
    def __repr__(self):
        text  = f"Subject: {self.subject}\n"
        text += f"From: {self.sender}\n"
        text += f"To:   {self.receiver}\n"
        text += f"Cc:   {self.cc}\n"
        text += f"\n{self.content}\n"
        text += f"Attachment: {self.attachment}"
        return text
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
