from pymongo import MongoClient

from .datastructures import TransferStatus


class Database:

    def __init__(self, connection_uri=None, db_name=None):
        self.connection = MongoClient(connection_uri)
        db_name = db_name or "randowhale"
        self.database = self.connection[db_name]

    def register_refund(self, sender, incoming_tx_block_height, incoming_tx_id,
                        outgoing_transfer_block_height,
                        outgoing_transfer_tx_id):
        pass

    def is_transfer_already_registered(self, trx_id):
        return bool(self.database.transfers.find_one(
            {"incoming_tx_id": trx_id}))

    def register_incoming_transaction(self, sender, memo,
                             incoming_transfer_block_height,
                             incoming_transfer_tx_id):
        document = {
            "sender": sender,
            "memo": memo,
            "incoming_tx_block_height": incoming_transfer_block_height,
            "incoming_tx_id": incoming_transfer_tx_id,
            "status": TransferStatus.READY_TO_PROCESS.value,
        }
        self.database.transfers.insert_one(document)
