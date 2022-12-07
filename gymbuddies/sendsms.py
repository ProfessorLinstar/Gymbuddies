"""sends sms message. Makes sure that the number is valid"""

import os
from twilio.rest import Client

SEND_SMS = False

NEW_REQUEST_MESSAGE = "Hello from Gymbuddies. You have recieved a new match request from $netid$!"

FINALIZE_REQUEST_MESSAGE = "Hello from Gymbuddies. Congratulations, your match with $netid$! has been finalized"

MATCH_TERMINATE_MESSAGE = "Hello from Gymbuddies. Your match with $netid$ has been cancelled"

def sendsms(number: str, message: str) -> bool:
    """sends sms message. Makes sure that the number is valid"""
    numberstr = "+" + number
    print("got here 0")
    if len(numberstr) != 12:
        return False
    print("got here 1")
    if numberstr[1] != "1":
        return False
    print("got here 2")
    try:
        account_sid = os.environ['TWILIO_ACCOUNT_SID']
        auth_token = os.environ['TWILIO_AUTH_TOKEN']
        from_number = os.environ['TWILIO_SMS_NUMBER']
        client = Client(account_sid, auth_token)
        message = client.messages.create(body=message, from_=from_number, to=number)
        print("got here 3")
        return True
    except Exception as ex:
        print(ex)
        return False
