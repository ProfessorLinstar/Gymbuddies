"""sends sms message. Makes sure that the number is valid"""

import os
from twilio.rest import Client

SEND_SMS = False

NEW_REQUEST_MESSAGE = "Hello from Gymbuddies. You have recieved a new match request from $netid$!"

FINALIZE_REQUEST_MESSAGE = "Hello from Gymbuddies. Congratulations, you have finalized your math with $netid$!"

def sendsms(number: str, message: str) -> bool:
    """sends sms message. Makes sure that the number is valid"""
    numberstr = "+" + number
    if len(numberstr) != 12:
        return False
    print(numberstr[1])
    if numberstr[1] != "1":
        return False
    try:
        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        from_number = os.environ['TWILIO_SMS_NUMBER']
        client = Client(account_sid, auth_token)
        message = client.messages.create(body=message, from_=from_number, to=number)
        print("got here")
        return True
    except Exception as ex:
        print(ex)
        return False
