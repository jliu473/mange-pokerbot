'''
Simple example pokerbot, written in Python.
'''
from skeleton.actions import FoldAction, CallAction, CheckAction, RaiseAction, BidAction
from skeleton.states import GameState, TerminalState, RoundState
from skeleton.states import NUM_ROUNDS, STARTING_STACK, BIG_BLIND, SMALL_BLIND
from skeleton.bot import Bot
from skeleton.runner import parse_args, run_bot
import random
import eval7


class Player(Bot):
    '''
    A pokerbot.
    '''

    def __init__(self):
        '''
        Called when a new game starts. Called exactly once.

        Arguments:
        Nothing.

        Returns:
        Nothing.
        '''
        self.num_rounds_learning = 50
        self.opp_raise_strengths = []
        self.opp_call_strengths = []
        self.opp_raise_threshold = 0.7
        # self.opp_call_threshold = 0.3
        self.opp_behavior = {'passive': 0, 'aggresive': 0}
        self.m_raise = 0
        self.m_call = 0


    def handle_new_round(self, game_state, round_state, active):
        '''
        Called when a new round starts. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        #my_bankroll = game_state.bankroll  # the total number of chips you've gained or lost from the beginning of the game to the start of this round
        #game_clock = game_state.game_clock  # the total number of seconds your bot has left to play this game
        round_num = game_state.round_num  # the round number from 1 to NUM_ROUNDS
        #my_cards = round_state.hands[active]  # your cards
        #big_blind = bool(active)  # True if you are the big blind

        self.round_num = round_num
        self.opp_actions = {0: [], 3: [], 4: [], 5: []}


    def handle_round_over(self, game_state, terminal_state, active):
        '''
        Called when a round ends. Called NUM_ROUNDS times.

        Arguments:
        game_state: the GameState object.
        terminal_state: the TerminalState object.
        active: your player's index.

        Returns:
        Nothing.
        '''
        #my_delta = terminal_state.deltas[active]  # your bankroll change from this round
        previous_state = terminal_state.previous_state  # RoundState before payoffs
        street = previous_state.street  # 0, 3, 4, or 5 representing when this round ended
        my_cards = previous_state.hands[active]  # your cards
        opp_cards = previous_state.hands[1-active]  # opponent's cards or [] if not revealed
        
        if self.round_num <= self.num_rounds_learning:  
            if len(opp_cards) >= 2:
                board_cards = previous_state.deck[:street]
                for st in [0, 3, 4, 5]:
                    opp_strength = 0 
                    if st == 0:
                        opp_strength_w_auction, opp_strength_wo_auction = self.calculate_strength(opp_cards[:2], st, board_cards[:st])
                        opp_strength = (opp_strength_w_auction + opp_strength_wo_auction) / 2
                    else:  
                        opp_strength_w_auction, opp_strength_wo_auction = self.calculate_strength(opp_cards, st, board_cards[:st])
                        if len(opp_cards) == 3:
                            opp_strength = opp_strength_w_auction
                        else:
                            opp_strength = opp_strength_wo_auction
                    
                    if RaiseAction in self.opp_actions[st]:
                        self.opp_raise_strengths.append(opp_strength)
                        if opp_strength > 0.3:
                            self.opp_behavior['aggresive'] += 1 - opp_strength
                    else:
                        if opp_strength > 0.6:
                            self.opp_behavior['passive'] += opp_strength

                    if st == 0 and active == 1:
                        self.opp_call_strengths.append(opp_strength)

        if self.round_num == self.num_rounds_learning:
            if len(self.opp_raise_strengths) > 0:
                self.opp_raise_threshold = sum(self.opp_raise_strengths) / len(self.opp_raise_strengths) * 0.9
                # self.opp_raise_threshold = self.opp_raise_strengths[int(len(self.opp_raise_strengths) * 0.4)]
            # if len(self.opp_call_strengths) > 0:
            #     self.opp_call_threshold = sum(self.opp_call_strengths) / len(self.opp_call_strengths)
            total_opp_behavior = self.opp_behavior['passive'] / (self.opp_behavior['aggresive'] + self.opp_behavior['passive'])
            self.m_raise = 1.05 + 0.65 * total_opp_behavior
            self.m_call = 0.4 + 0.55 * total_opp_behavior


    def get_action(self, game_state, round_state, active):
        '''
        Where the magic happens - your code should implement this function.
        Called any time the engine needs an action from your bot.

        Arguments:
        game_state: the GameState object.
        round_state: the RoundState object.
        active: your player's index.

        Returns:
        Your action.
        '''
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
        
        if self.round_num <= self.num_rounds_learning: 
            if BidAction in legal_actions:
                return BidAction(random.randint(1, 10))
            if CallAction in legal_actions:
                if continue_cost > 1:
                    self.opp_actions[street].append(RaiseAction)
                return CallAction()
            return CheckAction()

        return FoldAction()



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

if __name__ == '__main__':
    run_bot(Player(), parse_args())
