from __future__ import print_function
from constants import *
import httplib2
import os
import random
import base64

from email.mime.text import MIMEText
from os.path import expanduser
from apiclient import discovery
from apiclient import errors
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
  import argparse
  flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
  flags = None


# Function used to extract file extenstion
def extract_file_extension(file_name):
  return os.path.splitext(file_name)[1]

# Function used to seup credentials needed to establish a connection to the GMAIL client
def establish_connection():
  global credentials
  credentials = get_credentials()
  global http
  http = credentials.authorize(httplib2.Http())
  global service 
  service = discovery.build('gmail', 'v1', http=http)
  global results
  results = service.users().labels().list(userId='me').execute()
  global msgs
  msgs = list_messages_with_labels(service, "me", "UNREAD")

# Google provided functions (Modified in order to fit the score of the project)

def get_credentials():
  # Gets valid user credentials from storage. 
  # If nothing has been stored, or if the stored credentials are invalid, the OAuth2 flow
  # is completed to obtain the new credentials
  # Returns: Credentails the obtained credential.

  home_dir = os.path.expanduser('~')
  credential_dir = os.path.join(home_dir, '.credentials')
  if not os.path.exists(credential_dir):
    os.makedirs(credential_dir)
  credential_path = os.path.join(credential_dir, 'gmail-python-quickstart.json')

  store = Storage(credential_path)
  credentials = store.get()
  if not credentials or credentials.invalid:
    flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
    flow.user_agent = APPLICATION_NAME
    if flags:
      credentials = tools.run_flow(flow, store, flags)
    else: # Needed only for compatibility with Python 2.6
      credentials = tools.run(flow, store)
    print('Storing credentials to ' + credential_path)
  return credentials

def modify_message(service, user_id, msg_id, msg_labels):
  # Modify the Labels on the given message

  # Args:
  #   service: Authorized Gmail API service instance.
  #   user_id: User's email address. The special value "me" can be used to indicate
  #   the authenticated user
  #   msg_id: The id of the message required
  #   msg_labels: The change in labels

  # Returns: Modified message, containing updated labelIds, id and threadId

  try:
    message = service.users().messages().modify(userId=user_id, id=msg_id, body=msg_labels).execute()

    label_ids = message['labelIds']

    print('Message ID: %s - With Label IDs %s' % (msg_id, label_ids))

    return message
  except errors.HttpError, error:
    print('An error occurred: %s' % error)

def list_messages_with_labels(service, user_id, label_ids=[]):
  # List all Messages of the user's mailbox with label_ids applied.

  # Args:
  #   service: Authorized Gmail API service instance.
  #   user_id: User's email address. The special value "me"
  #   can be used to indicate the authenticated user.
  #   label_ids: Only return Messages with these labelIds applied.

  # Returns:
  #   List of Messages that have all required Labels applied. Note that the
  #   returned list contains Message IDs, you must use get with the
  #   appropriate id to get the details of a Message.

  try:
    response = service.users().messages().list(userId=user_id, labelIds=label_ids).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id,
                                                 labelIds=label_ids,
                                                 pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError, error:
    print('An error occurred: %s' % error)

def get_message(service, user_id, msg_id):
  # Get a Message with given ID.

  # Args:
  #   service: Authorized Gmail API service instance.
  #   user_id: User's email address. The special value "me"
  #   can be used to indicate the authenticated user.
  #   msg_id: The ID of the Message required.

  # Returns:
  #   A Message.

  try:
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    return message
  except:
    print('An error occurred')

def modify_message(service, user_id, msg_id, msg_labels):
  # Modify the Labels on the given Message.

  # Args:
  #   service: Authorized Gmail API service instance.
  #   user_id: User's email address. The special value "me"
  #   can be used to indicate the authenticated user.
  #   msg_id: The id of the message required.
  #   msg_labels: The change in labels.

  # Returns:
  #   Modified message, containing updated labelIds, id and threadId.

  try:
    message = service.users().messages().modify(userId=user_id, id=msg_id, body=msg_labels).execute()

    label_ids = message['labelIds']

    #print('Message ID: %s - With Label IDs %s' % (msg_id, label_ids))
    return message
  except errors.HttpError, error:
    print('An error occurred: %s' % error)

def create_message(sender, to, subject, message_text):
  # Create a message for an email.

  # Args:
  #   sender: Email address of the sender.
  #   to: Email address of the receiver.
  #   subject: The subject of the email message.
  #   message_text: The text of the email message.

  # Returns:
  #   An object containing a base64url encoded email object.

  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject

  return {'raw': base64.urlsafe_b64encode(message.as_string())}


def send_message(service, user_id, message):
  # Send an email message.

  # Args:
  #   service: Authorized Gmail API service instance.
  #   user_id: User's email address. The special value "me"
  #   can be used to indicate the authenticated user.
  #   message: Message to be sent.

  # Returns:
  #   Sent Message.

  try:
    message = (service.users().messages().send(userId=user_id, body=message).execute())
    print('Message Id: %s' % message['id'])
    
    return message
  except errors.HttpError, error:
    print('An error occurred: %s' % error)


def get_attachment(service, user_id, msg_id):
  # Get and store attachment from Message with given id.
  
  # Args:
  #     service: Authorized Gmail API service instance.
  #     user_id: User's email address. The special value "me"
  #         can be used to indicate the authenticated user.
  #     msg_id: ID of Message containing attachment.
  #     store_dir: The directory used to store attachments.

   store_dir = expanduser("~") + "/Documents/Email Project/Downloads"

   try:
     message = service.users().messages().get(userId=user_id, id=msg_id).execute()
     parts = [message['payload']]
     while parts:
         part = parts.pop()
         if part.get('parts'):
             parts.extend(part['parts'])
         if part.get('filename'):
             if 'data' in part['body']:
                 file_data = base64.urlsafe_b64decode(part['body']['data'].encode('UTF-8'))
             elif 'attachmentId' in part['body']:
                 attachment = service.users().messages().attachments().get(
                     userId=user_id, messageId=message['id'], id=part['body']['attachmentId']
                 ).execute()
                 file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
             else:
                 file_data = None

             file_extension = extract_file_extension(str(part.get('filename'))).lower()
            
             if file_extension in PICTURE:
                store_dir = store_dir + "/PICTURES/"

             elif file_extension in CODE:
                store_dir = store_dir + "/CODE/"

             elif file_extension in MUSIC:
                store_dir = store_dir + "/MUSIC/"

             elif file_extension in VIDEO:
                store_dir = store_dir + "/VIDEOS/"

             elif file_extension in DOCUMENTS:
                store_dir = store_dir + "/DOCUMENTS/"

             if file_data:
                 path = ''.join([store_dir, part['filename']])
                 with open(path, 'w') as f:
                     f.write(file_data)
                 send_message(service, "me", create_message("Rasp Pi", "5593894857@txt.att.net", "File Downloaded", "The file " + str(part.get('filename')) + " was downloaded"))


   except errors.HttpError as error:
     print('An error occurred: %s' % error)


def main():

  establish_connection()

  secret = random.randint(0, 9999)
  
  send_message(service, "me", create_message("Gaston", "5593894857@txt.att.net", "New Code", str(secret)))

  while(True):
    for msg in msgs:
      headers = get_message(service, 'me', msg['id'])['payload']['headers']
      for header in headers:
        if header['name'] == 'Subject':
            try:
              head = int(header['value'])
              if int(header['value']) == secret:
                  print("Subject: %s" % header['value'])
                  modify_message(service, 'me', msg['id'], batch)
                  get_attachment(service, 'me', msg['id'])
                  secret = random.randint(0, 9999)
                  send_message(service, "me", create_message("Rasp Pi", "5593894857@txt.att.net", "New Code", str(secret)))
            except ValueError:
              pass


    establish_connection()



if __name__ == '__main__':
    main()

