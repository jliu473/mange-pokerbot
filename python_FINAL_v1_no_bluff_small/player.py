"""
Simple example pokerbot, written in Python.
"""
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction, BidAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot
import random
import eval7
import pickle


class Player(Bot):
    """
    A pokerbot.
    """

    def __init__(self):
        """
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        """
        self.raise_threshold = 0.7
        self.call_threshold = 0.6
        self.bluff_threshold = 0
        self.raise_mult = 1

        with open("hand_strengths.pkl", "rb") as file:
            self.starting_strengths = pickle.load(file)

    def handle_new_round(self, game_state, round_state, active):
        """
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        """
        # my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        # game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        # round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        my_cards = round_state.hands[active]  # your cards
        big_blind = bool(active)  # True if you are the big blind
        print("new round")
    

    def handle_round_over(self, game_state, terminal_state, active):
        """
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        """
        # my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        # previous_state = terminal_state.previous_state  # RoundState before payoffs
        # street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        # my_cards = previous_state.hands[active]  # your cards
        # opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed
        pass

    def get_action(self, game_state, round_state, active):
        """
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        """
        # May be useful, but you may choose to not use.
        legal_actions = round_state.legal_actions()  # the actions you are allowed to take
        street = round_state.street  # 0, 3, 4, or 5 representing pre-flop, flop, turn, or river respectively
        my_cards = round_state.hands[active]  # your cards
        board_cards = round_state.deck[:street]  # the board cards
        my_pip = round_state.pips[active]  # the number of chips you have contributed to the pot this round of betting
        opp_pip = round_state.pips[1-active]  # the number of chips your opponent has contributed to the pot this round of betting
        my_stack = round_state.stacks[active]  # the number of chips you have remaining
        opp_stack = round_state.stacks[1-active]  # the number of chips your opponent has remaining
        my_bid = round_state.bids[active]  # How much you bid previously (available only after auction)
        opp_bid = round_state.bids[1-active]  # How much opponent bid previously (available only after auction)
        continue_cost = opp_pip - my_pip  # the number of chips needed to stay in the pot
        my_contribution = STARTING_STACK - my_stack  # the number of chips you have contributed to the pot
        opp_contribution = STARTING_STACK - opp_stack  # the number of chips your opponent has contributed to the pot

        if RaiseAction in legal_actions:
           min_raise, max_raise = round_state.raise_bounds()  # the smallest and largest numbers of chips for a legal bet/raise
           min_cost = min_raise - my_pip  # the cost of a minimum bet/raise
           max_cost = max_raise - my_pip  # the cost of a maximum bet/raise

        won_auction = None
        if len(my_cards) == 3:
            won_auction = True
        if len(my_cards) == 2 and street >= 3 and not BidAction in legal_actions:
            won_auction = False

        if street == 0:
            strength_w_auction, strength_wo_auction = self.hand_to_strength(my_cards)
        else:
            # iters = 300
            # if won_auction is None:
            #     iters = 1200
            # strength_w_auction, strength_wo_auction = self.calculate_strength(my_cards, street, board_cards, won_auction, iters=iters)
            strength_w_auction, strength_wo_auction = self.calculate_strength(my_cards, street, board_cards, won_auction)
        
        strength = 0
        if won_auction == None:
            strength = (strength_w_auction + strength_wo_auction) / 2
        elif won_auction: 
            strength = strength_w_auction
        else:
            strength = strength_wo_auction

        pot = my_contribution + opp_contribution

        
        if BidAction in legal_actions:
            if strength_w_auction >= 0.99:
                return BidAction(my_stack)
            bid = (strength_w_auction - strength_wo_auction) / (1 - strength_w_auction) * pot
            bid = int(bid)
            bid = min(my_stack, bid)
            bid = max(0, bid)
            return BidAction(bid)

        if RaiseAction in legal_actions:
            raise_ammt, raise_cost = self.calc_raise(street, strength, pot, my_pip, continue_cost, min_raise, max_raise, self.raise_mult)
        
        # copy pasted
        if RaiseAction in legal_actions and raise_cost <= my_stack:
            raise_ammt = max(min_raise, raise_ammt)
            raise_ammt = min(max_raise, raise_ammt)
            commit_action = RaiseAction(raise_ammt)
        elif CallAction in legal_actions and continue_cost <= my_stack:
            commit_action = CallAction()
        else:
            commit_action = FoldAction()
        
        if continue_cost > 0:
            pot_odds = continue_cost/(continue_cost + pot)
            
            intimidation = 0
            if continue_cost/pot > 0.33:
                intimidation = -0.3
            strength += intimidation         

            if strength >= pot_odds:
                if strength > self.raise_threshold and random.random() < strength:
                    my_action = commit_action
                else:
                    my_action = CallAction()
            else:
                if my_contribution == 1: # always min raise as small blind (if bad hand)
                    return RaiseAction(min_raise)
                # if continue_cost <= 2: # call if small blind min raises
                #     return CallAction()
                if strength < self.bluff_threshold and random.random() < self.bluff_threshold/2 and RaiseAction in legal_actions:
                    my_action = commit_action
                else:
                    my_action = FoldAction()
        else:
            if strength > self.call_threshold and random.random() < strength:
                my_action = commit_action
            else:
                my_action = CheckAction()
        
        return my_action
        # end copy paste

    def calculate_strength(self, my_cards, street, board_cards, won_auction=None, iters=100):
        deck = eval7.Deck()
        my_cards = [eval7.Card(card) for card in my_cards]
        board_cards = [eval7.Card(card) for card in board_cards]
        for card in my_cards + board_cards:
            deck.cards.remove(card)
        wins_w_auction = 0
        wins_wo_auction = 0

        if won_auction == None:
            for _ in range(iters):
                deck.shuffle()
                opp = 3
                community = 5 - street
                draw = deck.peek(opp+community)
                opp_cards = draw[:opp]
                community_cards = board_cards + draw[opp:]

                our_hand = my_cards + community_cards
                opp_hand = opp_cards + community_cards

                our_hand_val = eval7.evaluate(our_hand)
                opp_hand_val = eval7.evaluate(opp_hand)

                if our_hand_val > opp_hand_val:
                    # We won the round
                    wins_wo_auction += 2
                if our_hand_val == opp_hand_val:
                    # We tied the round
                    wins_wo_auction += 1

            for _ in range(iters):
                deck.shuffle()
                opp = 2
                community = 5 - street
                auction = 1
                draw = deck.peek(opp+community+auction)
                opp_cards = draw[:opp]
                community_cards = board_cards + draw[opp: opp + community]
                auction_card = draw[opp+community:]
                our_hand = my_cards + auction_card + community_cards
                opp_hand = opp_cards + community_cards

                our_hand_val = eval7.evaluate(our_hand)
                opp_hand_val = eval7.evaluate(opp_hand)

                if our_hand_val > opp_hand_val:
                    # We won the round
                    wins_w_auction += 2
                elif our_hand_val == opp_hand_val:
                    # we tied the round
                    wins_w_auction += 1
        
        else: 
            if won_auction:
                for _ in range(iters):
                    deck.shuffle()
                    opp = 2
                    community = 5 - street
                    draw = deck.peek(opp+community)
                    opp_cards = draw[:opp]
                    community_cards = board_cards + draw[opp: opp + community]
                    our_hand = my_cards + community_cards
                    opp_hand = opp_cards + community_cards

                    our_hand_val = eval7.evaluate(our_hand)
                    opp_hand_val = eval7.evaluate(opp_hand)

                    if our_hand_val > opp_hand_val:
                        # We won the round
                        wins_w_auction += 2
                    elif our_hand_val == opp_hand_val:
                        # we tied the round
                        wins_w_auction += 1
            
            else:
                for _ in range(iters):
                    deck.shuffle()
                    opp = 3
                    community = 5 - street
                    draw = deck.peek(opp+community)
                    opp_cards = draw[:opp]
                    community_cards = board_cards + draw[opp:]

                    our_hand = my_cards + community_cards
                    opp_hand = opp_cards + community_cards

                    our_hand_val = eval7.evaluate(our_hand)
                    opp_hand_val = eval7.evaluate(opp_hand)

                    if our_hand_val > opp_hand_val:
                        # We won the round
                        wins_wo_auction += 2
                    if our_hand_val == opp_hand_val:
                        # We tied the round
                        wins_wo_auction += 1
            
        strength_w_auction = wins_w_auction / (2* iters)
        strength_wo_auction = wins_wo_auction/ (2* iters)

        return strength_w_auction, strength_wo_auction
    

    def hand_to_strength(self, my_cards): #AcKs, Jc9s

        card_1 = my_cards[0]
        card_2 = my_cards[1]

        rank_1, suit_1 = card_1
        rank_2, suit_2 = card_2

        rank_to_numeric = dict()

        for i in range(2,10):
            rank_to_numeric[str(i)] = i

        for num, rank in enumerate("TJQKA"): #[(0,T), (1,J), (2,Q) ...]
            rank_to_numeric[rank] = num + 10

        num_1 = rank_to_numeric[rank_1]
        num_2 = rank_to_numeric[rank_2]

        suited = 'o'
        if suit_1 == suit_2:
            suited = "s"

        if num_1 >= num_2:
            key = rank_1 + rank_2 + suited
        else:
            key = rank_2 + rank_1 + suited

        return self.starting_strengths[key]


    def calc_raise(self, street, strength, pot, my_pip, continue_cost, min_raise, max_raise, raise_mult):
        if street < 3:
            raise_ammt = my_pip + continue_cost + 0.3*pot
        else:
            raise_ammt = my_pip + continue_cost + 0.5*pot
        
        raise_ammt *= raise_mult
        raise_ammt = int(raise_ammt)
        raise_ammt = max(min_raise, raise_ammt)
        raise_ammt = min(max_raise, raise_ammt)
        raise_cost = raise_ammt - my_pip

        return raise_ammt, raise_cost
        
        # mult = 0 
        # if strength > 0.9:
        #     mult = 0.15
        # elif strength > 0.8:
        #     mult = 0.1
        # elif strength > 0.7:
        #     mult = 0.08
        # else:
        #     return min_raise, 0
        
        # mult *= raise_mult

        # raise_ammt = int(my_pip + continue_cost + mult/(1-strength)*pot)
        # raise_ammt = max(min_raise, raise_ammt)
        # raise_ammt = min(max_raise, raise_ammt)
        # raise_cost = raise_ammt - my_pip
        
        # return raise_ammt, raise_cost

        # mult = 0 
        # if strength > 0.9:
        #     mult = 1
        # elif strength > 0.8:
        #     mult = 0.75
        # elif strength > 0.7:
        #     mult = 0.5
        # else:
        #     mult = 0.25
        
        # mult *= raise_mult

        # raise_ammt = (my_pip + continue_cost + mult*pot) * random.uniform(0.8, 1.2)
        # raise_ammt = int(raise_ammt)
        # raise_ammt = max(min_raise, raise_ammt)
        # raise_ammt = min(max_raise, raise_ammt)
        # raise_cost = raise_ammt - my_pip
        
        # return raise_ammt, raise_cost

if __name__ == "__main__":
    run_bot(Player(), parse_args())
