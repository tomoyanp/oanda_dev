import smtplib
from email.mime.text import MIMEText


class SendMail:

  def __init__(self, from_address, to_address):
    self.from_address = from_address
    self.to_address = to_address
    self.jp = 'iso-2022-jp'
    self.sender = smtplib.SMTP('smtp.gmail.com')

  def set_msg(self, msg):
    self.msg = msg

  def set_subject(self, subject):
    self.subject = subject

  def send_mail(self):
    self.sender.starttls()
    self.sender.login('tomoyanpy@gmail.com', 'tomoyan180')
    send_msg = MIMEText(self.msg.encode(self.jp), 'plain', self.jp,)
    send_msg['Subject'] = self.subject
    send_msg['From'] = self.from_address
    send_msg['To'] = self.to_address
    self.sender.sendmail(self.from_address, self.to_address, send_msg.as_string())
    self.sender.quit()
