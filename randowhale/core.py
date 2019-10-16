from lightsteem.client import Client
from lightsteem.helpers.amount import Amount
from lightsteem.datastructures import Operation
from lightsteem.helpers.amount import Amount
from dateutil.parser import parse

import time
import requests
import logging
from datetime import datetime, timedelta

from .datastructures import RefundReason, TransferStatus
from .vote_percent import VotePercent

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()


class TransferListener:

    def __init__(self, account, posting_key=None, active_key=None,
                 nodes=None, db=None, probability_dimensions=None,
                 min_age_to_vote=None, max_age_to_vote=None,
                 minimum_vp_to_vote=None, vote_price=None):
        self.db = db
        self.nodes = nodes or ["https://api.steemit.com"]
        self.account = account
        self.client = Client(loglevel=logging.INFO)
        self.vote_client = Client(keys=[posting_key, ], nodes=nodes)
        self.refund_client = Client(keys=[active_key, ], nodes=nodes)
        self.min_age_to_vote = min_age_to_vote or 300
        self.max_age_to_vote = max_age_to_vote or 43200
        self.minimum_vp_to_vote = minimum_vp_to_vote or 80
        self.vote_percent = VotePercent(
            probability_dimensions=probability_dimensions)
        self.vote_price = Amount(vote_price) or Amount("1.000 STEEM")

    def get_incoming_transfers(self):
        stop_at = datetime.now() - timedelta(hours=3)
        acc = self.client.account(self.account)
        transfers = []
        for _, transaction in acc.history(
                filter=["transfer"],
                only_operation_data=False,
                stop_at=stop_at,
        ):
            op = transaction["op"][1]
            if op["to"] != self.account:
                continue
            transfers.append(transaction)

        return transfers

    def poll_transfers(self):
        while True:
            try:
                for transfer in self.get_incoming_transfers():
                    self.process_transfer(transfer)
            except Exception as error:
                print(error)
            time.sleep(3)

    def in_global_blacklist(self, author):
        url = "http://blacklist.usesteem.com/user/" + author
        response = requests.get(url).json()
        return bool(len(response["blacklisted"]))

    def get_content(self, author, permlink, retries=None):
        if not retries:
            retries = 0

        try:
            content = self.client.get_content(author, permlink)
        except Exception as error:
            if retries > 5:
                raise
            return self.get_content(author, permlink, retries=retries+1)

        return content

    def get_active_votes(self, author, permlink, retries=None):
        if not retries:
            retries = 0

        try:
            active_votes = self.client.get_active_votes(author, permlink)
        except Exception as error:
            if retries > 5:
                raise
            return self.get_active_votes(author, permlink, retries=retries+1)

        return [v["voter"] for v in active_votes]

    def refund(self, to, amount, memo, incoming_trx_id):

        if self.db.database.transfers.count(
                {"incoming_trx_id": incoming_trx_id,
                 "status": TransferStatus.REFUNDED.value}):
            logger.info("Already refunded. (TRX id: %s)", incoming_trx_id)
            return

        try:
            op = Operation('transfer', {
                "from": self.account,
                "to": to,
                "amount": amount,
                "memo": memo,
            })
            self.refund_client.broadcast(op)
            status = TransferStatus.REFUNDED.value
        except Exception as e:
            print(e)
            status = TransferStatus.REFUND_FAILED.value

        self.db.database.transfers.update_one(
            {"incoming_tx_id": incoming_trx_id},
            {"$set": {"status": status}},
        )

    def process_transfer(self, transaction_data):

        op = transaction_data["op"][1]
        amount = Amount(op["amount"])

        # check if transaction is already registered in the database
        if self.db.is_transfer_already_registered(transaction_data["trx_id"]):
            logger.info(
                "Transaction is already registered. Skipping. (TRX: %s)",
                transaction_data["trx_id"])
            return

        # register the transaction into db
        self.db.register_incoming_transaction(
            op["from"],
            op["memo"],
            transaction_data["block"],
            transaction_data["trx_id"],
        )

        # check if the asset is valid
        if amount.symbol != "STEEM":
            logger.info(
                "Invalid asset. Refunding %s with %s. (TRX: %s)",
                op["from"],
                amount,
                transaction_data["trx_id"],
            )
            self.refund(
                op["from"],
                op["amount"],
                RefundReason.INVALID_ASSET.value,
                transaction_data["trx_id"],
            )
            return

        # check if the VP is suitable
        # Check the VP
        acc = self.client.account(self.account)
        if acc.vp() < self.minimum_vp_to_vote:
            print(acc.vp(), self.minimum_vp_to_vote)
            logger.info(
                "Rando is sleeping. Refunding. (TRX: %s)",
                transaction_data["trx_id"])
            self.refund(
                op["from"],
                op["amount"],
                RefundReason.SLEEP_MODE.value,
                transaction_data["trx_id"],
            )
            return

        # check vote price
        if amount.amount != self.vote_price.amount:
            logger.info(
                "Invalid amount. Refunding. (TRX: %s)",
                transaction_data["trx_id"])
            self.refund(
                op["from"],
                op["amount"],
                "Invalid amount. You need to send %s" % self.vote_price,
                transaction_data["trx_id"],
            )
            return

        # check if the sender is in a blacklist
        if self.in_global_blacklist(op["from"]):
            logger.info(
                "Sender is in blacklist. Refunding. (TRX: %s)",
                transaction_data["trx_id"])

            self.refund(
                op["from"],
                op["amount"],
                RefundReason.SENDER_IN_BLACKLIST.value,
                transaction_data["trx_id"],
            )
            return

        # check if the memo is valid
        memo = op["memo"]
        try:
            author = memo.split("@")[1].split("/")[0]
            permlink = memo.split("@")[1].split("/")[1]
        except IndexError as e:
            logger.info("Invalid URL. Refunding. Memo: %s", memo)
            self.refund(
                op["from"], op["amount"], RefundReason.INVALID_URL.value,
                transaction_data["trx_id"],
            )
            return

        # check if the author is in a blacklist
        if self.in_global_blacklist(author):
            logger.info(
                "Author is in blacklist. Refunding. (TRX: %s)",
                transaction_data["trx_id"])

            self.refund(
                op["from"],
                op["amount"],
                RefundReason.AUTHOR_IN_BLACKLIST.value,
                transaction_data["trx_id"],
            )
            return

        # check is the Comment is a valid Comment
        comment_content = self.get_content(author, permlink)
        if comment_content["id"] == 0:
            logger.info("Invalid post. Refunding. (TRX id: %s)",
                        transaction_data["trx_id"])
            self.refund(
                op["from"],
                op["amount"],
                RefundReason.INVALID_URL.value,
                transaction_data["trx_id"],
            )
            return

        # check comment is valid
        if comment_content.get("parent_author"):
            logger.info("Not a main post. Refunding. (TRX id: %s)",
                        transaction_data["trx_id"])
            self.refund(
                op["from"],
                op["amount"],
                RefundReason.INVALID_URL.value,
                transaction_data["trx_id"],
            )
            return

        # check if we've already voted for that post
        active_voters = self.get_active_votes(author, permlink)
        if self.account in active_voters:
            logger.info("Already voted. Refunding. (TRX id: %s)",
                        transaction_data["trx_id"])
            self.refund(
                op["from"],
                op["amount"],
                RefundReason.POST_IS_ALREADY_VOTED.value,
                transaction_data["trx_id"],
            )
            return

        # check if the Comment age is suitable
        created = parse(comment_content["created"])
        comment_age = (datetime.now() - created).total_seconds()
        if not (self.min_age_to_vote < comment_age < self.max_age_to_vote):
            self.refund(
                op["from"],
                op["amount"],
                f"Post age must be between {self.min_age_to_vote} and"
                f" {self.max_age_to_vote} seconds",
                transaction_data["trx_id"],

            )
            logger.info("Post age is invalid. Refunding. (TRX id: %s)",
                        transaction_data["trx_id"])
            return

        # vote
        self.vote(author, permlink, amount, transaction_data)

    def vote(self, author, permlink, amount, transaction_data):
        random_vote_weight = self.vote_percent.pick_percent()
        logger.info("Voting for %s/%s. Random vote weight: %%%s",
                    author, permlink, random_vote_weight)
        vote_op = Operation('vote', {
            "voter": self.account,
            "author": author,
            "permlink": permlink,
            "weight": random_vote_weight * 100,
        })

        burn_op = Operation('transfer', {
            "from": self.account,
            "to": "null",
            "amount": str(amount),
            "memo": f"Burning STEEM for {author}/{permlink}",
        })

        # vote
        try:
            self.vote_client.broadcast(vote_op)
            time.sleep(3)
            status = TransferStatus.VOTED.value
        except Exception as e:
            print(e)
            status = TransferStatus.VOTE_FAILED.value

        # burn
        try:
            self.refund_client.broadcast(burn_op)
            time.sleep(3)
        except Exception as e:
            print(e)
            status = TransferStatus.BURN_FAILED.value

        self.db.database.transfers.update_one(
            {"incoming_tx_id": transaction_data["trx_id"]},
            {"$set": {"status": status}},
        )