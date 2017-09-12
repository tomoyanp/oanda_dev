import smtplib
import json
from email.mime.text import MIMEText


class SendMail:

  def __init__(self, from_address, to_address):
    self.from_address = from_address
    self.to_address = to_address
    self.jp = 'iso-2022-jp'
    mail_properties = self.getMailProperty()
    smtp_server = mail_properties["smtp_server"]
    self.sender = smtplib.SMTP(smtp_server)
    self.mail_account = mail_properties["mail_account"]
    self.mail_pass = mail_properties["mail_pass"]

  def set_msg(self, msg):
    self.msg = msg

  def set_subject(self, subject):
    self.subject = subject

  def getMailProperty(self):
      mail_properties = open("mail.property", "r")
      jsonData = json.load(mail_properties)
      return jsonData

  def send_mail(self):
    self.sender.starttls()
    self.sender.login(self.mail_account, self.mail_pass)
    send_msg = MIMEText(self.msg.encode(self.jp), 'plain', self.jp,)
    #send_msg['Subject'] = self.subject
    send_msg['From'] = self.from_address
    send_msg['To'] = self.to_address
    self.sender.sendmail(self.from_address, self.to_address, send_msg.as_string())
    self.sender.quit()
