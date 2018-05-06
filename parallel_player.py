import copy


class ParallelPlayer:

    def __init__(self, prototype, concurrent_games):
        self.instances = []
        for i in range(0, concurrent_games):
            self.instances.append(copy.deepcopy(prototype))

    def give_hand(self, cards):
        for i in range(0,  len(cards)):
            if cards[i] is not None:
                self.instances[i].give_hand(cards[i])

    def make_bid(self, bids):
        for i in range(0, len(bids)):
            if bids[i] is not None:
                self.instances[i].make_bid(bids[i])
    
    def play_card(self, tricks):
        results = []
        for i in range(0, len(tricks)):
            result = None
            if tricks[i] is not None:
                result = self.instances[i].play_card(tricks[i])
            results.append(result)
        return results

    def offer_blind_nill(self, bids):
        for i in range(0, len(bids)):
            if bids[i] is not None:
                self.instances[i].offer_blind_nill(bids[i])
    
    def receive_blind_nill_cards(self, game_id, cards):
        for i in range(len(cards)):
            if cards[i] is not None:
                self.instances[i].receive_blind_nill_cards(cards[i])

    def request_blind_nill_cards(self, requests):
        results = []
        for i in range(0, len(requests)):
            result = None
            if requests[i] is not None:
                result = self.instances[i].request_blind_nill_cards()
            results.append(result)

    def announce_bids(self, bids):
        for i in range(0, len(bids)):
            if bids[i] is not None:
                self.instances[i].announce_bids(bids[i])

    def announce_trick(self, tricks):
        for i in range(0, len(tricks)):
            if tricks[i] is not None:
                self.instances[i].announce_trick(tricks[i])

    def announce_score(self, scores):
        for i in range(0, len(scores)):
            if scores[i] is not None:
                self.instances[i].announce_score(scores[i])