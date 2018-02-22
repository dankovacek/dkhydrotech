"""Get a list of Messages from the user's mailbox.
"""

from apiclient import errors
import base64
import email
import datetime
import os
import sys
import math
import io
import pandas as pd

import gmail_api


def ListMessagesMatchingQuery(service, user_id, query=''):
    """List all Messages of the user's mailbox matching the query.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      query: String used to filter messages returned.
      Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

    Returns:
      List of Messages that match the criteria of the query. Note that the
      returned list contains Message IDs, you must use get with the
      appropriate ID to get the details of a Message.
    """
    try:
        response = service.users().messages().list(userId=user_id,
                                                   q=query).execute()
        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, q=query,
                                                       pageToken=page_token).execute()
            messages.extend(response['messages'])

        return messages
    except errors.HttpError as error:
        print('An error occurred: {}'.format(error))


def ListMessagesWithLabels(service, user_id, label_ids=[]):
    """List all Messages of the user's mailbox with label_ids applied.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      label_ids: Only return Messages with these labelIds applied.

    Returns:
      List of Messages that have all required Labels applied. Note that the
      returned list contains Message IDs, you must use get with the
      appropriate id to get the details of a Message.
    """
    try:
        # first get label IDs:
        results = service.users().labels().list(userId=user_id).execute()
        labels_result = results.get('labels', [])

        if not labels_result:
            print('No email labels found.')
            target_labels = []
            # should send admin email error here indicating label error
        else:
            target_labels = [label['id'] for label in labels_result if label['name']
                             in label_ids]

        response = service.users().messages().list(userId=user_id,
                                                   labelIds=target_labels).execute()

        messages = []
        if 'messages' in response:
            messages.extend(response['messages'])

        # get current time for message filtering
        # as we want to target most recent email

        now = datetime.datetime.now()
        date_day = int(now.day)
        time_search_start = now.strftime("%Y/%m/") + str(date_day - 1)
        time_search_end = now.strftime("%Y/%m/") + str(date_day + 1)

        time_search_string = 'after:{} before:{}'.format(
            time_search_start, time_search_end)

        print('what is time search string? = ', time_search_string
              )

        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id,
                                                       labelIds=label_ids,
                                                       pageToken=page_token,
                                                       q=time_search_string).execute()
            messages.extend(response['messages'])

        return messages
    except errors.HttpError as error:
        print('An error occurred: {}'.format(error))


def GetMessage(service, user_id, msg_id):
    """Get a Message with given ID.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      msg_id: The ID of the Message required.

    Returns:
      A Message.
    """
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id).execute()

        print('Message snippet: {}'.format(message['snippet']))

        return message
    except errors.HttpError as error:
        print('An error occurred: {}'.format(error))


def GetMimeMessage(service, user_id, msg_id):
    """Get a Message and use it to create a MIME Message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      msg_id: The ID of the Message required.

    Returns:
      A MIME Message, consisting of data from Message.
    """
    try:
        message = service.users().messages().get(userId=user_id, id=msg_id,
                                                 format='raw').execute()

        print('Message snippet: {}'.format(message['snippet']))

        msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

        mime_msg = email.message_from_string(msg_str)

        return mime_msg
    except errors.HttpError as error:
        print('An error occurred: {}'.format(error))


def GetMessageAttachment(service, message, user_id, msg_id):
    # now get message attachment
    try:
        for part in message['payload']['parts']:
            if part['filename']:
                if 'data' in part['body']:
                    data = part['body']['data']
                else:
                    attachment_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(
                        userId=user_id, messageId=msg_id, id=attachment_id).execute()
                    data = att['data']
                file_data = bytes.decode(
                    base64.urlsafe_b64decode(data.encode('UTF-8')))

                df = pd.read_csv(io.StringIO(file_data),
                                 header=0)

                # modify if datetime format changes on Unidata website
                # dayfirst=True
                df['DateTime'] = pd.to_datetime(
                    df['Date'] + ' ' + df['Time'], dayfirst=True)
                df = df.drop(['Date', 'Time'], axis=1)
                df = df.sort_values(['DateTime'], ascending=True)
                return df
    except errors.HttpError as error:
        print('An error occurred: {}'.format(error))
