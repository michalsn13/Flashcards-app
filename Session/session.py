# GLOBAL IMPORTS (PYTHON PACKAGES)
from time import time # measuring time for stats of user's performance
import logging
# LOCAL IMPORTS
from collections import deque # storing cards (deque to pop from left side)
logger=logging.getLogger('flashcards.session')
class DailySession:
    """
    DailySession is responsible for studying process and interacting with the user.
    It takes a deck with its cards and shows those that are ready for the user to decide how well he recalls them.
    """
    def __init__(self,deck):
        """
        Defining the session object with Deck() it will be performed on.
        """
        logger.info(f"Session called on deck '{deck.name}'.")
        self.deck=deck

    # I've decided to separate 3 stages of a full session:
    # * learning cards session
    # * reviews session
    # * new cards session
    # I've put those parts into separate functions/generators to be able to change its order in the full session.

    def __study_learners(self):
        """
        Learning cards part of the session. It is a function and it loops throught all of ready learning cards.
        I've not made a generator because I assume that learning cards part won't be mixed with any other part.
        """
        logger.info("Request to study learning cards.")
        fulltime=[]
        learners=self.deck.get_learners() # providing learning cards as Card() objects for the current session from a deck
        logger.info("Learning session starts...")
        while learners:
            card=learners.popleft()
            logger.info(f"{card} is being shown...")
            print(f"""
            -------------------------------
                        {card.front}
            -------------------------------""")
            t0=time()
            input('Press enter to show answer. ')
            time_passed=time()-t0
            fulltime.append(time_passed) # Storing 'recall times'-how long it took the user to recall a card.
            print(f"""
            -------------------------------
                        {card.back}
            -------------------------------""")
            # Possible actions on a Card() depending on user's choice (more in Card() class).
            # If a card came to learning cards from new cards then it's a 'NL'-new learning.
            # And if it came from reviews then it's a 'LL'-lapses.
            # There are differences between the treatment of those cards so I've made different functions for them (more in Card() class).
            decisions = {'NL': {'A': card.new_again, 'G': card.new_good, 'E': card.new_easy}, # functions for new learning cards

                         'LL': {'A': card.lapse_again, 'G': card.lapse_good, 'E': card.lapse_easy} # functions for lapses
                         }
            users_choice=input("Press: 'A'-again ; 'G'-good; 'E'-easy ('Q' to quit): ")
            logger.debug(f"User's choice on a card: '{users_choice}'.")
            # Assuming the user may mistype his choice- he gets infinite number of chances.
            while users_choice.strip().upper() not in ['A','E','G']:
                if users_choice.strip().upper()=='Q':
                    return 'quit_request'
                logger.warning(f"Invalid decision. Expected 'A','E' or 'G' ('Q' to quit).")
                print("Invalid decision. ")
                users_choice = input("Press: A'-again ; 'G'-good; 'E'-easy ('Q' to quit): ")
            decisions[card.status][users_choice.strip().upper()]()
        logger.info("Learning session ended.")
        return fulltime # Returning all 'recall times'


    def __study_reviews(self):
        """
        Reviews part of the full session. I've made it a generator so the session can be mixed with
        new cards part. Generator yields 'recall times' for every viewed card.
        """
        logger.info("Request to study reviews.")
        reviews = self.deck.get_reviews() # providing reviews as Card() objects for the current session from a deck
        while reviews:
            card = reviews.popleft()
            logger.info(f"{card} is being shown...")
            print(f"""
        -------------------------------
                    {card.front}
        -------------------------------""")
            t0 = time()
            input('Press enter to show answer. ')
            delta = time() - t0
            print(f"""
        -------------------------------
                    {card.back}
        -------------------------------""")
            # Possible actions on a Card() depending on user's choice (more in Card() class).
            decisions = {'A': card.review_again, 'H': card.review_hard, 'G': card.review_good, 'E': card.review_easy}
            users_choice = input("Press: 'A'-again; 'H'-hard; 'G'-good; 'E'-easy ('Q' to quit): ")
            logger.debug(f"User's choice on a card: '{users_choice}'.")
            # Assuming the user may mistype his choice- he gets infinite number of chances.
            while users_choice.strip().upper() not in ['A', 'E', 'G','H']:
                if users_choice.strip().upper()=='Q':
                    yield 'quit_request'
                logger.warning(f"Invalid decision. Expected 'A','E','G' or 'H' ('Q' to quit).")
                print("Invalid decision. ")
                users_choice = input("Press: 'A'-again; 'H'-hard; 'G'-good; 'E'-easy ('Q' to quit): ")
            decisions[users_choice.strip().upper()]()
            logger.debug('Review session stops.')
            yield delta # yielding to stop the generator before the next card comes up
        logger.info("No more reviews to be shown.")

    def __study_new(self):
        """
        New cards part of the full session. I've made it a generator so the session can be mixed with
        reviews part. Generator yields 'recall times' for every viewed card.
        """
        logger.info("Request to study new cards.")
        new=self.deck.get_new() # providing new cards as Card() objects for the current session from a deck
        while new:
            card = new.popleft()
            logger.info(f"{card} is being shown...")
            print(f"""
        -------------------------------
                   {card.front}
        -------------------------------""")
            t0 = time()
            input('Press enter to show answer. ')
            delta = time() - t0
            print(f"""
        -------------------------------
                    {card.back}
        -------------------------------""")
            decisions = {'A': card.new_again, 'G': card.new_good, 'E': card.new_easy}
            users_choice = input("Press: 'A'-again; 'G'-good; 'E'-easy ('Q' to quit): ")
            logger.debug(f"User's choice on a card: '{users_choice}'.")
            # Assuming the user may mistype his choice- he gets infinite number of chances.
            while users_choice.strip().upper() not in ['A', 'E', 'G']:
                if users_choice.strip().upper()=='Q':
                    yield 'quit_request'
                logger.warning(f"Invalid decision. Expected 'A','E' or 'G' ('Q' to quit).")
                print("Invalid decision. ")
                users_choice = input("Press: 'A'-again; 'G'-good; 'E'-easy ('Q' to quit): ")
            decisions[users_choice.strip().upper()]()
            logger.debug('New cards session stops.')
            yield delta # yielding to stop the generator before the next card comes up
        logger.info("No more new cards to be shown.")
    def full_study(self):
        """
        This function represents the actual session of studying. As I mentioned earlier it is made of
        3 parts depending of card types. Before the cards show up I present user's plan for the current day.
        Be aware that the fact that a learning card is prepared for that day does not mean it is ready at any time during that day.
        If user already studied all daily cards then the function informs him about that and ends.
        When it comes to the cards themselves: I've decided that learning cards are always prioritized so the session
        starts and ends with them. Between those learning parts there are new and review cards going after one another.
        At the end of the session average 'recall time' is presented and the function informs user how does the
        current daily plan looks. If there won't be any cards for today then user is being congratulated
        and he has to wait till the next day or increase the daily limit for new cards.
        """
        logger.info("Request to perform a full study.")
        if not self.deck.any_cards(): # If there are no cards to be seen today...
            logger.info(f"No more cards for today.")
            return print("You've already finished your session for today.") # User needs to wait till the next day or increase the new cards daily limit.
        plan=self.deck.daily_count_printer() # Providing summary of different cards types to study in a current day.
        # Presenting how many cards are there to be studied today.
        input(f"{plan}\nPress ENTER to start.")
        fulltime=self.__study_learners() # Getting started with learning cards as they are the most important part. In the process- saving all 'recall times' (or handling quit request).
        if fulltime=='quit_request':
            logger.info("Full session ended early.")
            return print("Full session ended early.")
        tasks=deque([self.__study_new(),self.__study_reviews()]) # Creating new cards and reviews part generators and putting them in a list.
        # Going through generators in turns untill any of them runs out, continuing with the other one then.
        while tasks:
            task=tasks.popleft()
            try:
                delta=next(task)
                if delta=='quit_request':
                    logger.info("Full session ended early.")
                    return print("Full session ended early.")
            except StopIteration:
                    pass
            else:
                fulltime.append(delta)
                tasks.append(task)
        # There are no reviews and new cards to be seen at the moment.
        # Ending with possibly multiple learning sessions till there won't be any learning cards to be studied at the moment.
        while True:
            time = self.__study_learners()
            if time:
                fulltime+=time
            else:

                break
        # If all card deques were empty then nothing was appended to fulltime and therefore there are no cards to be seen at the moment.
        if not fulltime:
            logger.info('No cards to be seen at the moment.')
            return print('No cards to be seen at the moment.')
        # At the very end of the session providing the average time spend on a single card (average 'recall time').
        # If there are still some cards to be seen today then the program ends with showing how many of them there are.
        # And if user completed his daily plan then he gets praise for it and has to wait till the next day or increase new cards daily limit.
        if not self.deck.any_cards():
            print(f"Average time spend on card: {round(sum(fulltime) / len(fulltime), 3)}\nCongratulation! No cards left for today.")
        else:
            plan=self.deck.daily_count_printer()
            print(f"Average time spend on card: {round(sum(fulltime)/len(fulltime),3)}\n{plan}")
        logger.info("Full session ended.")





























