
from twilio.rest import Client
account_sid = ''
auth_token = ''
client = Client(account_sid, auth_token)

message = client.messages.create(
                              body='Hello there!',
                              from_='whatsapp:+14155238886',
                              to='whatsapp:+917013019722'
                          )

print(message.sid)
