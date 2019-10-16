from randowhale.core import TransferListener
from randowhale.db import Database

import config_test as config

t = TransferListener(
    config.BOT_ACCOUNT,
    db=Database(),
    active_key=getattr(config, 'ACTIVE_KEY'),
    posting_key=getattr(config, 'POSTING_KEY'),
    max_age_to_vote=getattr(config, 'MAX_AGE_TO_VOTE', None),
    min_age_to_vote=getattr(config, 'MIN_AGE_TO_VOTE', None),
    minimum_vp_to_vote=getattr(config, 'MINIMUM_VP_TO_VOTE', None),
    nodes=getattr(config, 'NODES', None),
    probability_dimensions=getattr(config, 'PROBABILITY_DIMENSIONS', None),
    vote_price=getattr(config, 'VOTE_PRICE', None),
)
t.poll_transfers()
