from twilio.rest import Client


class TwilioAPI:
    #todo: support receive message
    def __init__(self, sid, auth, from_number):
        self.client = Client(sid, auth)
        self.from_number = from_number

    #number in form of string (e.g. +2127921122)
    def send_message(self,number,text): 
        message = self.client.messages.create(body=text,from_=self.from_number,to=number)
        if message.error_code:
            print(f"[Error TwilioAPI::send_message] Failed to send message [{text}] to [{number}]")