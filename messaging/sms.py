import time
from Config.config import sms_to
from twilio.rest import Client

class MockSmsClient:
    def __init__(self, to=sms_to):
        self.to = to

    def send(self, message):
        time0 = time.strftime('%Y%m%d_%H%M%S')
        with open('logs/send_sms.log', 'a') as file:
            file.write(f"{time0} | To:{self.to} | \n{message}")
        print('[Mock sms] sent to', self.to)

class TwilioSmsClient:
    def __init__(self, sid, token, from_no, to=sms_to):
        self.client = Client(sid, token)
        self.from_no = from_no
        self.to = to

    def send(self, message):
        self.client.messages.create(body=message, from_=self.from_no, to=self.to)

def get_sms_client(cfg=None):
    if cfg is None:
        return MockSmsClient()
    if cfg.get('provider') == 'twilio':
        return TwilioSmsClient(cfg['sid'], cfg['token'], cfg['from'])
    return MockSmsClient()
