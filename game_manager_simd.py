import random
import card
from copy import deepcopy
from i_player import IPlayer
from trick import Trick
from bids import Bids
from score import Score

_BLIND_NILL_CHARACTER = "B"


class GameData:

    def __init__(self, players):
        assert len(players) == 4

        self.players = []
        self.player_offset = random.randint(0, 3)
        for i in range(4):
            self.players.append(players[i % self.player_offset])

        self.bids = [None, None, None, None]
        self.blind_player = None

        self.score = [0, 0]
        self.hands = []
        self.dealer = 4  # start at player 1
        self.deal_deck()

    def set_blind_player(self, player_x):
        assert 0 <= player_x < 4

        self.blind_player = player_x

    def set_bid_player(self, player_x, bid):
        assert 0 <= player_x < 4

        self.bids[player_x] = bid

    def has_blind_player(self):
        return self.blind_player is not None

    def is_player_x(self, player_x, player):
        return self.players[player_x] == player

    def is_blind_player(self, player_x):
        return self.blind_player == player_x

    def can_do_blind(self, player_x):
        assert 0 <= player_x < 4

        return self.score[player_x % 2] <= self.score[(player_x + 1) % 2] - 100 and self.blind_player is None

    def get_hand(self, player_x):
        assert 0 <= player_x < 4

        return *self.hands[player_x],

    def take_cards(self, player_x, cards):
        assert 0 <= player_x < 4
        assert len(cards) == 2
        assert cards[0] in self.hands[player_x]
        assert cards[1] in self.hands[player_x]

        self.hands[player_x].remove(cards[0])
        self.hands[player_x].remove(cards[1])

    def give_cards(self, player_x, cards):
        assert 0 <= player_x < 4
        assert len(cards) == 2

        self.hands[player_x] += cards

    def get_bid_announce(self, player):
        double_bids = self.bids + self.bids
        for i in range(len(self.players)):
            if self.players[i] == player:
                return double_bids[i:i+4]

    def deal_deck(self):

        deck = []
        for suit_id in range(4):
            for number_id in range(13):
                deck.append(card.Card(suit_id, number_id))
        random.shuffle(deck)

        for i in range(4):
            hand = deck[13 * i: 13 * (i + 1)]
            self.hands[i] = hand
        self.dealer = (self.dealer + 1) % 4



class GameManagerSIMD:

    def for_all(self, player, player_x, functor, param=None):
        """"
        Helper function to loop though all our games.
        """
        assert len(param) == len(self.gameData) or param is None

        data = [game_state if game_state.is_player_x(player_x, player) else None for game_state in self.gameData]
        if param is None:
            return [None if d is None else functor(d) for d in data]
        else:
            return [None if data[i] is None or param[i] is None else functor(data[i], param[i]) for i in range(len(data))]

    def __init__(self, players=[IPlayer()] * 4, playing_to=500):
        self.players = players
        self.gameData = []
        self.playing_to = playing_to
        self.score = Score()  # Players 0 and 2 form team 0, players 1 and 3 are team 1
        self.hands = {}
        self.dealer = 0
        self.bids = Bids()

    def get_blind_player_x(self, x):
        for player in self.players:
            known_bids = self.for_all(player, x, lambda gs: gs.bids if gs.can_do_blind(x) else None) # TODO: deep copy and make relative id.
            bids = player.offer_blind_nill(known_bids)
            self.for_all(player, x, lambda gs, bid: gs.set_blind_player(x) if gs.can_do_blind(x) and bid else None, bids)

    def set_hand_player_x(self, x):
        for player in self.players:
            hands = self.for_all(player, x, lambda gs: gs.get_hand(x))
            player.give_hand(hands)

    def get_bid_x(self, x):
        for player in self.players:
            known_bids = self.for_all(player, x, lambda gs: gs.bids if not gs.is_blind_player(x) else None) # TODO: deep copy and make relative id.
            bids = player.make_bid(known_bids)
            self.for_all(player, x, lambda gs, bid: gs.set_bid_player(x, bid) if not gs.is_blind_player(x) else None, bids)

    def announce_bids(self):
        for player in self.players:
            bids = [gs.get_bid_announce(player) for gs in self.gameData]
            player.announce_bids(bids)

    def swap_blind_player_cards(self, x):
        teammate_x = (x + 2) % 4
        for i in range(len(self.players)):
            player = self.players[i]
            team_player = self.players[(i+2) % 4]
            requests = self.for_all(player, x, lambda gs: True if gs.is_blind_player(x) else None)
            cards = player.request_blind_nill_cards(requests)
            self.for_all(player, x, lambda gs, c: gs.take_cards(x, c) if gs.is_blind_player(x) else None, cards)
            team_player.receive_blind_nill_cards(cards)
            self.for_all(team_player, teammate_x, lambda gs, c: gs.give_cards(teammate_x) if gs.is_blind_player(x) else None, cards)

    def swap_teammate_player_cards(self, x):
        blind_mate_x = (x + 2) % 4
        for i in range(len(self.players)):
            player = self.players[i]
            blind_player = self.players[(i+2) % 4]
            requests = self.for_all(player, x, lambda gs: True if gs.is_blind_player(blind_mate_x) else None)
            cards = player.request_blind_nill_cards(requests)
            self.for_all(player, x, lambda gs, c: gs.take_cards(x, c) if gs.is_blind_player(blind_mate_x) else None, cards)
            blind_player.receive_blind_nill_cards(cards)
            self.for_all(blind_player, blind_mate_x, lambda gs, c: gs.give_cards(blind_mate_x) if gs.is_blind_player(blind_mate_x) else None, cards)





    def deal_deck(self):
        """
        Shuffle the deck and deal 13 cards to each player.
        Note that for Blind Nill purposes, the handing out of cards happens during the bidding phase.
        """
        deck = []
        for suit_id in range(4):
            for number_id in range(13):
                deck.append(card.Card(suit_id, number_id))
        random.shuffle(deck)

        for i in range(4):
            hand = deck[13 * i: 13 * (i + 1)]
            self.hands[i] = hand
        self.dealer = (self.dealer + 1) % 4

    def get_bids(self):
        """"Get the bids of all players in order."""
        self.bids = Bids()
        blind_accepted = False
        for i in range(4):
            # The value of 'dealer' will have been incremented at the end of the deal
            # Hence, it's current value is the player who should start bidding
            active_player_id = (self.dealer + i) % 4
            # First, we have to check if a Blind Nill bid is allowed, and if so, offer the option
            if not blind_accepted and self.score.can_blind(active_player_id):
                if self.players[active_player_id].offer_blind_nill(self.bids.make_copy(active_player_id)):
                    blind_accepted = True
                    self.bids.add_bid(_BLIND_NILL_CHARACTER, active_player_id)
                    self.players[active_player_id].give_hand(deepcopy(self.hands[active_player_id]))
                    continue
            # Hand out the cards to the player and ask for a bid
            self.players[active_player_id].give_hand(deepcopy(self.hands[active_player_id]))
            player_bid = self.players[active_player_id].make_bid(self.bids.make_copy(active_player_id))
            # Make sure the bid is valid: between 0 and 13, and the sum with the teammate's bid does not exceed 13
            assert 0 <= player_bid <= 13
            teammate_id = (active_player_id + 2) % 4
            if teammate_id in self.bids and (self.bids[teammate_id] != "N" and self.bids[teammate_id] != "B"):
                assert self.bids[(active_player_id + 2) % 4] + player_bid <= 13
            self.bids.add_bid(player_bid, active_player_id)
        # When all bids have been made, inform all players about them
        for i, player in enumerate(self.players):
            player.announce_bids(self.bids.make_copy(i))

    def handle_card_exchange(self):
        """"Exchanges 2 cards between the players of the team running a Blind Nill."""
        assert self.bids.get_blinder_id() is not None
        blinder_id = self.bids.get_blinder_id()
        # Step 1: Get 2 cards from the person running the Blind Nill and give them to the teammate
        # Step 2: Get 2 cards from the teammate and give them to the person running the Blind Nill
        for i in [0, 2]:
            giver_id = (blinder_id + i) % 4
            receiver_id = (giver_id + 2) % 4
            offered_cards = deepcopy(self.players[giver_id].request_blind_nill_cards())
            # As always, don't trust the players, and check all conditions
            assert len(offered_cards) == 2
            for offered_card in offered_cards:
                assert offered_card in self.hands[giver_id]
                self.hands[giver_id].remove(offered_card)
            self.players[receiver_id].receive_blind_nill_cards(deepcopy(offered_cards))
            self.hands[receiver_id] += offered_cards

    def get_trick(self, starting_player, spades_broken):
        """"Play a trick by getting a card from each player in order."""
        current_trick = Trick()
        for i in range(4):
            player_id = (starting_player + i) % 4
            card_played = self.players[player_id].play_card(current_trick.make_copy(player_id),
                                                            self.get_valid_cards(player_id, current_trick,
                                                                                 spades_broken))
            assert self.verify_card_validity(card_played, player_id, current_trick, spades_broken)
            current_trick.add_card(card_played, player_id)
            self.hands[player_id].remove(card_played)
        return current_trick

    def verify_card_validity(self, played_card, player_id, trick, spades_broken):
        """"Verify that an offered card is valid to play."""
        try:
            # First off, a card can only be played if the player actually has it
            assert played_card in self.hands[player_id]
            # Secondly, check if the card is of the right suit
            # If the player starts the trick or matches the suit, all is fine
            if trick.suit is not None and played_card.suit != trick.suit:
                for hand_card in self.hands[player_id]:
                    assert hand_card.suit != trick.suit
            # Thirdly, a player may only start a trick with a spade if a spade has been played before,
            # or if the player only has spades left in his hand
            if trick.suit is None and played_card.suit == "S" and not spades_broken:
                for hand_card in self.hands[player_id]:
                    assert hand_card.suit == "S"
        except AssertionError:
            return False
        return True

    def get_valid_cards(self, player_id, trick, spades_broken):
        """"Generate a list of all cards in a player's hand that are valid to play for this trick."""
        valid_cards = []
        for hand_card in self.hands[player_id]:
            if self.verify_card_validity(hand_card, player_id, trick, spades_broken):
                valid_cards.append(hand_card)
        return deepcopy(valid_cards)

    def play_round(self):
        """"Play a round, consisting of 13 tricks."""
        # Set up the round
        spades_broken = False
        self.deal_deck()
        starting_player = self.dealer
        self.get_bids()
        trick_count = {0: 0, 1: 0, 2: 0, 3: 0}
        if self.bids.get_blinder_id() is not None:
            self.handle_card_exchange()
        # Play the round
        for i in range(13):
            current_trick = self.get_trick(starting_player, spades_broken)
            if current_trick.won_by_spade:
                spades_broken = True
            starting_player = current_trick.get_winner()
            trick_count[starting_player] += 1
            # Inform all players of the final result of the trick
            for i, player in enumerate(self.players):
                player.announce_trick(current_trick.make_copy(i))
        # Handle the scoring
        for i in [0, 1]:
            self.award_team_score(trick_count, i)
        # Inform all players about the new score
        for i, player in enumerate(self.players):
            player.announce_score(self.score.make_copy(i))

    def award_team_score(self, trick_count, team_id):
        """"Given the bids and a resulting trick count, decide the score for a team."""
        assert team_id == 0 or team_id == 1
        gained_score = 0
        handled = False

        player_1_id = 0 + team_id
        player_2_id = 2 + team_id
        # First, handle the situation of a player nilling
        if self.bids.team_has_nill(team_id):
            for player_id in [player_1_id, player_2_id]:
                bid = self.bids[player_id]
                tricks = trick_count[player_id]
                if bid == "N" or bid == "B":
                    multiplier = 1 + int(bid == "B")
                    if tricks == 0:
                        gained_score += 50 * multiplier
                    else:
                        gained_score -= 50 * multiplier
                else:
                    if bid <= tricks:
                        overtricks = tricks - bid
                        gained_score += 10 * bid + overtricks
                    else:
                        gained_score -= 10 * bid
        # If there were no nills on this team, carry on normally
        else:
            bid = self.bids.get_team_bid(team_id)[0]
            tricks = trick_count[player_1_id] + trick_count[player_2_id]
            if bid <= tricks:
                overtricks = tricks - bid
                gained_score += 10 * bid + overtricks
            else:
                gained_score -= 10 * bid

        # Lastly, check for sandbagging
        if (self.score[team_id] % 10) + (gained_score % 10) >= 10:
            gained_score -= 100

        self.score.add_score(gained_score, team_id)

    def play_game(self):
        """""Simulate one game of Spades with the given players."""
        assert len(self.players) == 4
        self.score = Score()
        self.dealer = 0
        # Give the players the starting score
        for i in range(4):
            self.players[i].announce_score(self.score.make_copy(i))
        # Play rounds until one side wins
        while -self.playing_to < self.score[0] < self.playing_to and -self.playing_to < self.score[1] < self.playing_to:
            self.play_round()
        return self.score
