from .models import *

def get_friend_request_or_false(sender, receiver):
    try:
        return FriendRequest.objects.get(sender = sender, receiver = receiver, is_pending = True)
    except FriendRequest.DoesNotExist:
        return False

from enum import Enum

class FriendRequestStatus(Enum):
    NO_REQUEST_SENT = -1
    INCOMING_REQUEST = 0
    OUTGOING_REQUEST = 1