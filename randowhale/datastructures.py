from enum import Enum


class RefundReason(Enum):
    AUTHOR_IN_BLACKLIST = "Author is in blacklist"
    SENDER_IN_BLACKLIST = "Sender is in blacklist"
    POST_IS_ALREADY_VOTED = "Post is already voted"
    INVALID_ASSET = "Only STEEM is accepted."
    INVALID_URL = "Invalid URL"
    SLEEP_MODE = "randowhale is sleeping. Try again later"


class TransferStatus(Enum):
    VOTED = "voted"
    VOTE_FAILED = "vote_failed"
    BURN_FAILED = "burn_failed"
    REFUNDED = "refunded"
    READY_TO_PROCESS = "ready_to_process"
    REFUND_FAILED = "refund_failed"