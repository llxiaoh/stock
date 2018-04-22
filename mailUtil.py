import smtplib
import re
from email.header import Header
from email.mime.text import MIMEText



# 仅用于本工具类记录日志或输出试用
class UtilLog:
    def info(self,msg):
        print(msg)
    def error(self,msg):
        print(msg)


class MailUtil:
    # 发送邮箱的用户名
    username = ""
    # 发送邮箱的密码
    password = ""
    # 邮件服务
    server = None
    # 邮件标题
    TITLE = "来来来，看看邮件有多温暖"
    # 日志记录
    log = UtilLog()

    def __init__(self, username, password):
        MailUtil.username = username
        MailUtil.password = password

    # 开启邮件发送服务
    def startServer(self):
        try:
            # 校验发送邮箱的信息是否正确
            if MailUtil.username == '':
                return 1, "开启服务失败，发送邮箱用户名为空"
            if MailUtil.password == '':
                return 2, "开启服务失败，发送邮箱密码为空s"

            # 开启服务
            server = smtplib.SMTP()
            smtp,port = MailUtil.getSMTPserver(MailUtil.username)
            server.connect(smtp,port)
            server.login(user=MailUtil.username, password=MailUtil.password)
            MailUtil.server = server
            MailUtil.log.info("邮件服务准备完毕")
        except Exception as e:
            MailUtil.log.error("准备邮件服务异常:{}".format(e))

    # 关闭邮件发送服务
    def close(self):
        if MailUtil.server is not None:
            MailUtil.server.quit()

    # 添加需要发送的mail
    # targetmail 目标邮箱地址 必须是有效的邮件地址
    # content 发送邮件的内容
    def addMail(self, targetmail, content):
        try:
            msg = MIMEText(content, 'plain', "utf-8")
            msg['From'] = MailUtil.username
            msg['To'] = targetmail
            msg['Subject'] = Header(MailUtil.TITLE, "utf-8")
            MailUtil.server.sendmail(MailUtil.username, targetmail, msg.as_string())
            MailUtil.log.info("邮件发送成功")
        except Exception as e:
            MailUtil.log.error("发送邮件异常[{}],{},{}".format(targetmail,content, e))

    # 校验地址是否为合法的邮箱地址
    @classmethod
    def validatemail(self, mail):
        result = re.search(".+@.+\.(com|cn|org|net)$", mail)
        if result is not None and len(result.group()) > 0:
            return 0, result.group()
        else:
            return 1, "校验失败"

    # 获取smtp服务地址
    @classmethod
    def getSMTPserver(self, mail):
        # 默认已校验过mail
        mailendstr = mail.split("@")[1]
        # QQ邮箱smtp端口库是465
        if "QQ" in mailendstr.upper():
            return "smtp." + mailendstr,465
        else:
            return "smtp." + mailendstr,25


if __name__ == "__main__":
    mail = MailUtil("发送邮箱","邮箱密码")
    mail.startServer()
    mail.addMail("接收邮箱", "邮件内容")
    mail.close()
