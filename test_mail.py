from send_mail import SendMail


sm = SendMail("tomoyanpy@gmail.com", "tomoyanpy@softbank.ne.jp")
sm.set_msg("test test")
sm.set_subject("test title")
sm.send_mail()
