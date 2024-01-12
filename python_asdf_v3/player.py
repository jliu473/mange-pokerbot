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
        pass

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

        card1 = my_cards[0]
        card2 = my_cards[1]
        rank1, suit1 = my_cards[0]
        rank2, suit2 = my_cards[1]
        chen_value = 0

        dict_shitter = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9' : 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

        value1, value2 = dict_shitter[rank1], dict_shitter[rank2]
        
        high_value = max(value1, value2)
        
        if high_value == 14:
            chen_value = 10
        elif 11 <= high_value <= 13:
            chen_value = high_value - 5
        else:
            chen_value = high_value / 2

        if value1 == value2:
            if value1 == 5:
                chen_value = 6
            else:
                chen_value = max(chen_value * 2, 5)

        if suit1 == suit2:
            chen_value += 2
        gap = abs(value1 - value2) 
        if gap == 2 or gap == 3:
            chen_value -= gap
        elif gap == 4:
            chen_value -= 4
        else:
            chen_value -= 5
        if high_value <= 11 and (gap == 1 or gap == 2):
            chen_value += 1

        self.chen_value = chen_value


        




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

        if street == 0: 
            if active == 1: #we are big blind
                if CheckAction in legal_actions:#they call
                    if self.chen_value >= 15:
                        r = random.random()
                        if r < 0.1:
                            return CheckAction()
                        elif r < 0.3:
                            return RaiseAction(max_raise)
                        return RaiseAction(random.randint(4, 30))
                    elif self.chen_value >= 12:
                        r = random.random()
                        if r < 0.05:
                            return CheckAction()
                        elif r < 0.15:
                            return RaiseAction(max_raise)
                        return RaiseAction(random.randint(4, 25))
                    elif self.chen_value >= 10:
                        return RaiseAction(random.randint(4, 20))
                    elif self.chen_value >= 7.5:
                        return RaiseAction(random.randint(4, 15))
                    elif self.chen_value >= 5:
                        return RaiseAction(random.randint(4, 10))
                    else:
                        return CheckAction()
            else: #they raised
                if self.chen_value >= 15:
                    return RaiseAction(min(5 * continue_cost, max_raise))
                elif self.chen_value >= 12:
                    if continue_cost > 25:
                        return FoldAction()
                    if continue_cost >= 13:
                        return CallAction()
                    return RaiseAction(random.randint(2 *continue_cost, 25))
                elif self.chen_value >= 10:
                    if continue_cost > 20:
                        return FoldAction()
                    if continue_cost >= 10:
                        return CallAction()
                    return RaiseAction(random.randint(2*continue_cost, 20))

                elif self.chen_value >= 7.5:
                    if continue_cost > 15:
                        return FoldAction()
                    if continue_cost >= 8:
                        return CallAction()
                    return RaiseAction(random.randint(2*continue_cost, 15))
                
                elif self.chen_value >= 5:
                    if continue_cost > 10:
                        return FoldAction()
                    if continue_cost >= 5:
                        return CallAction()
                    return RaiseAction(random.randint(2*continue_cost, 10))
                    
                else:
                    return FoldAction() # written by ivan


            if active == 0: # small blind
                if my_contribution == 1: #first action
                    if self.chen_value >= 15:
                        r  = random.random()
                        if r  < 0.3:
                            return RaiseAction(max_raise)
                        else: 
                            return RaiseAction(random.randint(4,40))
                    elif self.chen_value >= 12:
                            return RaiseAction(random.randint(4, 30))
                    elif self.chen_value >= 10:
                            return RaiseAction(random.randint(4, 20))
                    elif self.chen_value >= 7.5:
                            return RaiseAction(random.randint(4, 15))
                        
                    elif self.chen_value >= 5:
                            return RaiseAction(random.randint(4, 10))         
                    else:
                        return RaiseAction(min_raise) 

                else: #they raised
                    if self.chen_value >= 15:
                        return RaiseAction(min(5 * continue_cost, max_raise))
                    elif self.chen_value >= 12:
                        if continue_cost > 30:
                            return FoldAction()
                        if continue_cost >= 15:
                            return CallAction()
                        return RaiseAction(random.randint(2 *continue_cost, 35))
                    elif self.chen_value >= 10:
                        if continue_cost > 20:
                            return FoldAction()
                        if continue_cost >= 10:
                            return CallAction()
                        return RaiseAction(random.randint(2*continue_cost, 20))

                    elif self.chen_value >= 7.5:
                        if continue_cost > 15:
                            return FoldAction()
                        if continue_cost >= 8:
                            return CallAction()
                        return RaiseAction(random.randint(2*continue_cost, 15))
                    
                    elif self.chen_value >= 5:
                        if continue_cost > 10:
                            return FoldAction()
                        if continue_cost >= 5:
                            return CallAction()
                        return RaiseAction(random.randint(2*continue_cost, 10))
                        
                    else:
                        return FoldAction() # written by ivan



if __name__ == "__main__":
    run_bot(Player(), parse_args())
