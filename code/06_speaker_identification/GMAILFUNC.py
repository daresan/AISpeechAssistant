from loguru import logger
import os
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email import encoders
from mimetypes import guess_type as guess_mime_type

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']
our_email = 'roy.batty.assistant@gmail.com'

class GMAILFUNC:

    def __init__(self):
        self.process = None
        self.outtext = None
      
    def gmail_authenticate(self):
        creds = None
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        # if there are no (valid) credentials availablle, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
        return build('gmail', 'v1', credentials=creds)
    
    # get the Gmail API service
    # service = gmail_authenticate()
    
    # Adds the attachment with the given filename to the given message
    def add_attachment(self, message, filename):
        if filename.lower().endswith(".mp4"):
            content_type = 'video/mp4'
            encoding = None
        else:
            content_type, encoding = guess_mime_type(filename)
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(filename, 'rb')
            msg = MIMEText(fp.read().decode(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(filename, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(filename, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'video':
            fp = open(filename, 'rb')
            msg = MIMEBase(filename, sub_type)
            msg.set_payload(fp.read())
            encoders.encode_base64(msg)
            fp.close()
        else:
            fp = open(filename, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(filename)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)
        return message
        
    def build_message(self, destination, obj, body, attachments=[]):
        if not attachments: # no attachments given
            message = MIMEText(body)
            message['to'] = destination
            message['from'] = our_email
            message['subject'] = obj
        else:
            message = MIMEMultipart()
            message['to'] = destination
            message['from'] = our_email
            message['subject'] = obj
            message.attach(MIMEText(body))
            for filename in attachments:
                self.add_attachment(message, filename)
        return {'raw': urlsafe_b64encode(message.as_bytes()).decode()}
    
    def send_message(self, service, destination, obj, body, attachments=[]):
        return service.users().messages().send(
          userId="me",
          body=self.build_message(destination, obj, body, attachments)
        ).execute()
    
    def search_messages(self, service, query):
        result = service.users().messages().list(userId='me',q=query).execute()
        messages = [ ]
        if 'messages' in result:
            messages.extend(result['messages'])
        while 'nextPageToken' in result:
            page_token = result['nextPageToken']
            result = service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
            if 'messages' in result:
                messages.extend(result['messages'])
        return messages
    
    # utility functions
    def get_size_format(self, b, factor=1024, suffix="B"):
        """
        Scale bytes to its proper byte format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if b < factor:
                return f"{b:.2f}{unit}{suffix}"
            b /= factor
        return f"{b:.2f}Y{suffix}"
    
    
    def clean(self, text):
        # clean text for creating a folder
        return "".join(c if c.isalnum() else "_" for c in text)
    
    def parse_parts(self, service, parts, folder_name, message):
        """
        Utility function that parses the content of an email partition
        """
        self.outtext = []
        if parts:
            #extract = input("Extract attachments? ")
            #if extract in ["y", "Y", "yes", "Yes", "YES"]:
            for part in parts:
                filename = part.get("filename")
                mimeType = part.get("mimeType")
                body = part.get("body")
                data = body.get("data")
                file_size = body.get("size")
                part_headers = part.get("headers")
                if part.get("parts"):
                    # recursively call this function when we see that a part
                    # has parts inside
                    parse_parts(service, part.get("parts"), folder_name, message)
                if mimeType == "text/plain":
                    # if the email part is text plain
                    if data:
                        text = urlsafe_b64decode(data).decode()
                        #print(text)
                        self.outtext.append(text)
                elif mimeType == "text/html":
                    # if the email part is an HTML content
                    # save the HTML file and optionally open it in the browser
                    if not filename:
                        filename = "index.html"
                    filepath = os.path.join(folder_name, filename)
                    print("Saving HTML to", filepath)
                    with open(filepath, "wb") as f:
                        f.write(urlsafe_b64decode(data))
                    text = urlsafe_b64decode(data).decode()
                    self.outtext.append(text)
                else:
                    # attachment other than a plain text or HTML
                    for part_header in part_headers:
                        part_header_name = part_header.get("name")
                        part_header_value = part_header.get("value")
                        if part_header_name == "Content-Disposition":
                            if "attachment" in part_header_value:
                                # we get the attachment ID 
                                # and make another request to get the attachment itself
                                print("Saving the file:", filename, "size:", self.get_size_format(file_size))
                                attachment_id = body.get("attachmentId")
                                attachment = service.users().messages() \
                                            .attachments().get(id=attachment_id, userId='me', messageId=message['id']).execute()
                                data = attachment.get("data")
                                filepath = os.path.join(folder_name, filename)
                                if data:
                                    with open(filepath, "wb") as f:
                                        f.write(urlsafe_b64decode(data))
                                    text = urlsafe_b64decode(data).decode()
                                    self.outtext.append(text)
            #else:
            #    print("No files extracted.")
        #print("Outtext: ", self.outtext)                        
        if self.outtext:
            #logger.debug("Rückgabetext:", self.outtext)
            return self.outtext
        else:
            logger.debug("Kein Rückgabetext!")
            return []
                                        
    def read_message(self, service, message):
        """
        This function takes Gmail API `service` and the given `message_id` and does the following:
            - Downloads the content of the email
            - Prints email basic information (To, From, Subject & Date) and plain/text parts
            - Creates a folder for each email based on the subject
            - Downloads text/html content (if available) and saves it under the folder created as index.html
            - Downloads any file that is attached to the email and saves it in the folder created
        """
        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        # parts can be the message body, or attachments
        payload = msg['payload']
        headers = payload.get("headers")
        parts = payload.get("parts")
        data = []
        if parts:
            for part in parts:
                body = part.get("body")
                if body:
                    data = body.get("data")
        folder_name = "email"
        has_subject = False
        subjects = []
        self.sender = []
        if headers:
            # this section prints email basic info & creates a folder for the email
            for header in headers:
                name = header.get("name")
                value = header.get("value")
                if name.lower() == 'from':
                    # we print the From address
                    print("From:", value)
                    self.sender = value
                if name.lower() == "to":
                    # we print the To address
                    print("To:", value)
                if name.lower() == "subject":
                    # make our boolean True, the email has "subject"
                    has_subject = True
                    # make a directory with the name of the subject
                    folder_name = self.clean(value)
                    # we will also handle emails with the same subject name
                    folder_counter = 0
                    while os.path.isdir(folder_name):
                        folder_counter += 1
                        # we have the same folder name, add a number next to it
                        if folder_name[-1].isdigit() and folder_name[-2] == "_":
                            folder_name = f"{folder_name[:-2]}_{folder_counter}"
                        elif folder_name[-2:].isdigit() and folder_name[-3] == "_":
                            folder_name = f"{folder_name[:-3]}_{folder_counter}"
                        else:
                            folder_name = f"{folder_name}_{folder_counter}"
                    os.mkdir(folder_name)
                    print("Subject:", value)
                if name.lower() == "date":
                    # we print the date when the message was sent
                    print("Date:", value)
        if not has_subject:
            # if the email does not have a subject, then make a folder with "email" name
            # since folders are created based on subjects
            if not os.path.isdir(folder_name):
                os.mkdir(folder_name)
        response = self.parse_parts(service, parts, folder_name, message)
        #print("Response: ", response)
        #print("Data: ", data)
        print("="*50)
        if response:
            if has_subject:
                #print("Hat ein Subjekt.")
                ret_val = [response, self.sender]
                print("return: ", ret_val)
                return ret_val
            else:
                response = "stop"
                return response
        elif data:
            return "stop"
        else:
            return []
    
    def delete_messages(self, service, query):
        messages_to_delete = self.search_messages(service, query)
        # it's possible to delete a single message with the delete API, like this:
        # service.users().messages().delete(userId='me', id=msg['id'])
        # but it's also possible to delete all the selected messages with one query, batchDelete
        if messages_to_delete:
            logger.debug("Lösche Nachrichten mit Betreff 'Video Request'")
            return service.users().messages().batchDelete(
              userId='me',
              body={
                  'ids': [ msg['id'] for msg in messages_to_delete]
              }
            ).execute()
        else:
            print("Keine Nachrichten zu löschen!")
            return []
    
# # test send email
# send_message(service, "daresan21@gmail.com", "Message from Roy Batty Assistant.", 
#             "Hello Daniel! This is your AI Assistant Roy Batty. Have a nice day! Yours, Roy", ["TTS.py", "main_06.py"])

# # get emails that match the query you specify
# results = search_messages(service, "Simsalabim")
# print(f"Found {len(results)} results.")
# # for each email matched, read it (output plain/text to console & save HTML and attachments)
# for msg in results:
#     read_message(service, msg)