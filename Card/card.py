# GLOBAL IMPORTS (PYTHON PACKAGES)
from datetime import datetime,timedelta # handling current datetime and ready datetime
import logging
# LOCAL IMPORTS
from Connection.connection import Connection # connecting to SQL database
logger=logging.getLogger('flashcards.card')
class Card:
    """
    Class Card represents a card to study (sic!). Functions of this class change some parameters
    on a card in SQL table of a deck it's in- for example all of them change LAST_DATE and LAST_TIME
    values (so I won't mention that every time I describe a function). As you will see those functions are strictly connected to
    card's status and user's decision on how well he recalled it during session.
    """
    def __init__(self,deck,front,back,status):
        """
        Card is defined by the deck it's in.
        It has front and back values (a word/phrase and its translation) and a status.
        Possible statuses (mentioned already while describing other classes).
        'N'-new card not seen before
        'NL'-new-learning card (was a new card)
        'LL'-lapse learning card/lapse card (was a review)
        'R'-review card (was a review or a new card that was put directly to reviews if user pressed EASY on it)
        """
        self.deck = deck
        self.front=front
        self.back=back
        self.status=status
    def __repr__(self):
        """
        String representation of a card- its front, back and status.
        """
        return f"Card({self.front},{self.back},{self.status})"
    """
    Card is new only before it's seen the first time. Then it becomes a new-learning card. Those are in a temporary state
    trying to pass all of the learning intervals and become a review. 
    """
    def new_again(self):
        logger.info("Request on a card:AGAIN")
        """
        Updating new or new-learning card when user pressed 'AGAIN' on it.
        If a card was new then its status changes to 'NL' (new-learning) and new cards daily limit use goes down by one.
        Card goes back to the first step of the learning interval steps.
        Ready datetime is also changed to current datetime + learning interval.
        """
        steps = self.deck.get_options()['NEW_STEPS']
        with Connection() as con:
            logger.debug("Connected to database successfully. Changing card's info...")
            cursor=con.cursor()
            now=datetime.now()
            ready=now+timedelta(minutes=steps[0])
            cursor.execute(f"UPDATE {self.deck.name} SET status='NL',LEARN_INTERVAL={steps[0]}, LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}',READY_DATE='{ready:%Y-%m-%d}',READY_TIME='{ready:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
            logger.debug(f"New learning interval set at {steps[0]} minutes.")
            if self.status=='N': # if it was a new card then the number of new cards left to be show in the current goes down by one
                cursor.execute(f"UPDATE decks SET limit_left=limit_left-1 WHERE name='{self.deck.name}'")
                logger.debug("Card put to learning pile.")
        logger.info("Card's info changed.")
    def new_good(self):
        """
        Updating new or new-learning card when user pressed 'GOOD' on it.
        If a card was new then its status changes to 'NL' (new-learning) and new cards daily limit use goes down by one.
        Card goes up by one learning interval step, and if it already was at the last one then it is moved to reviews
        with set starting interval (REVIEW_INTERVAL in options).
        Ready datetime/date is also changed to current datetime/date+learning interval/interval
        (depending on whether card was put into reviews).
        """
        logger.info("Request on a card:GOOD")
        options=self.deck.get_options()
        steps = options['NEW_STEPS'] # all of learning interval steps for a new card
        with Connection() as con:
            logger.debug("Connected to database successfully. Changing card's info...")
            cursor=con.cursor() # checking current learning interval step
            cursor.execute(f"SELECT LEARN_INTERVAL FROM {self.deck.name} WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
            learn_interval=cursor.fetchall()[0][0]
            if learn_interval==steps[-1]: # if it was the last one out of them then card gets put into reviews with default interval
                now = datetime.now()
                cursor.execute(f"UPDATE {self.deck.name} SET status='R', INTERVAL=ROUND({options['REVIEW_INTERVAL']}),LEARN_INTERVAL=NULL, LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
                cursor.execute(f"UPDATE {self.deck.name} SET READY_DATE=LAST_DATE+INTERVAL,READY_TIME=NULL WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
                logger.debug(f"First interval set at {options['REVIEW_INTERVAL']} days.")
                logger.debug("Card put to reviews pile.")
            else: # else, card goes up by one learning interval
                new_step=steps[steps.index(learn_interval)+1]
                now = datetime.now()
                ready = now+timedelta(minutes=new_step)
                cursor.execute(f"UPDATE {self.deck.name} SET status='NL', LEARN_INTERVAL={new_step}, LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}',READY_DATE='{ready:%Y-%m-%d}',READY_TIME='{ready:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
                logger.debug(f"New learning interval set at {new_step} minutes.")
            if self.status == 'N': # if it was a new card then the number of new cards left to be show in the current goes down by one
                cursor.execute(f"UPDATE decks SET limit_left=limit_left-1 WHERE name='{self.deck.name}'")
        logger.info("Card's info changed.")
    def new_easy(self):
        """
        Updating new or new-learning card when user pressed 'EASY' on it.
        Card goes straight to reviews with a special default interval (EASY_REVIEW_INTERVAL in options).
        Ready date is changed to current date+interval that was just set.
        """
        logger.info("Request on a card:EASY")
        options=self.deck.get_options()
        with Connection() as con:
            logger.debug("Connected to database successfully. Changing card's info...")
            cursor=con.cursor()
            now = datetime.now()
            cursor.execute(f"UPDATE {self.deck.name} SET status='R', INTERVAL=ROUND({options['EASY_REVIEW_INTERVAL']}), LEARN_INTERVAL=NULL, LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
            cursor.execute(f"UPDATE {self.deck.name} SET READY_DATE=LAST_DATE+INTERVAL,READY_TIME=NULL WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
            logger.debug(f"First interval set at {options['EASY_REVIEW_INTERVAL']} days.")
            if self.status == 'N': # if it was a new card then the number of new cards left to be show in the current goes down by one
                cursor.execute(f"UPDATE decks SET limit_left=limit_left-1 WHERE name='{self.deck.name}'")
        logger.debug("Card put to reviews pile.")
        logger.info("Card's info changed.")
    """
    Review is the quo status of a card. Card is meant to climb there from 
    being a new card and not fall back to a lapse.
    """
    def review_again(self):
        """
        Updating review card when user pressed 'AGAIN' on it.
        Card comes back to learning card as a lapse card. Future interval (when card will come back to reviews)
        is changed to its 75% +- random factor to avoid putting multiple cards on the same day
        (it's added every time the interval is changed and I won't mention that from now on).
        Learning interval is set at the first step of lapses learning intervals.
        Ease factor goes down by 0.2. Ready datetime is changed to current datetime+ first learning interval for lapses.
        """
        logger.info("Request on a card:AGAIN")
        options=self.deck.get_options()
        steps=options['LAPSE_STEPS']
        with Connection() as con:
            logger.debug("Connected to database successfully. Changing card's info...")
            cursor=con.cursor()
            now = datetime.now()
            ready = now + timedelta(minutes=steps[0])
            cursor.execute(f"UPDATE {self.deck.name} SET status='LL', INTERVAL=GREATEST(1,ROUND(0.75*INTERVAL+(2*RANDOM()-1)*INTERVAL*0.05)), LEARN_INTERVAL={steps[0]}, EASE_FACTOR=GREATEST(1,EASE_FACTOR-0.2), LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}',READY_DATE='{ready:%Y-%m-%d}',READY_TIME='{ready:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
            logger.debug(f"Lapse interval set at {steps[0]} minutes.")
        logger.debug("Card put to lapses pile.")
        logger.info("Card's info changed.")
    def review_hard(self):
        """
        Updating review card when user pressed 'HARD' on it.
        Card stays in the reviews but its new interval is set as the 120% of the previous one.
        Ease factor goes down by 0.15.
        Ready date is changed to current date+interval.
        """
        logger.info("Request on a card:HARD")
        with Connection() as con:
            logger.debug("Connected to database successfully. Changing card's info...")
            cursor=con.cursor()
            now = datetime.now()
            cursor.execute(f"UPDATE {self.deck.name} SET INTERVAL=GREATEST(1,ROUND(1.2*INTERVAL+(2*RANDOM()-1)*INTERVAL*0.05)), EASE_FACTOR=GREATEST(1,EASE_FACTOR-0.15), LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
            cursor.execute(f"UPDATE {self.deck.name} SET READY_DATE=LAST_DATE+INTERVAL WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
        logger.info("Card's info changed.")
    def review_good(self):
        """
        Updating review card when user pressed 'GOOD' on it.
        Card stays in reviews but its interval is multiplied by the ease factor.
        Ready date is changed as before.
        """
        logger.info("Request on a card:GOOD")
        with Connection() as con:
            logger.debug("Connected to database successfully. Changing card's info...")
            cursor=con.cursor()
            now = datetime.now()
            cursor.execute(f"UPDATE {self.deck.name} SET INTERVAL=GREATEST(1,ROUND(EASE_FACTOR*INTERVAL+(2*RANDOM()-1)*INTERVAL*0.05)), LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
            cursor.execute(f"UPDATE {self.deck.name} SET READY_DATE=LAST_DATE+INTERVAL WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
        logger.info("Card's info changed.")
    def review_easy(self):
        """
        Updating review card when user pressed 'EASY' on it.
        Card stays in reviews but its interval gets multiplied by the ease factor and the easy bonus.
        Also, ease factor gets extra 0.15.
        Ready date is changed as before.
        """
        logger.info("Request on a card:EASY")
        options = self.deck.get_options()
        with Connection() as con:
            logger.debug("Connected to database successfully. Changing card's info...")
            cursor=con.cursor()
            now = datetime.now()
            cursor.execute(f"UPDATE {self.deck.name} SET INTERVAL=GREATEST(1,ROUND(EASE_FACTOR*{options['EASY_BONUS']}*INTERVAL+(2*RANDOM()-1)*INTERVAL*0.05)), EASE_FACTOR=EASE_FACTOR+0.15, LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
            cursor.execute(f"UPDATE {self.deck.name} SET READY_DATE=LAST_DATE+INTERVAL WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
        logger.info("Card's info changed.")
    """
    Lapses work in a similar way to new/new-learning cards but with own learning interval steps.
    Also, they already have an interval (cause they were reviews) so it may be changed.
    """
    def lapse_again(self):
        """
        Updating lapse learning card when user pressed 'AGAIN' on it.
        Function is pretty much the same as the review_again() but without changing the ease_factor.
        """
        logger.info("Request on a card:AGAIN")
        options = self.deck.get_options()
        steps = options['LAPSE_STEPS']
        with Connection() as con:
            logger.debug("Connected to database successfully. Changing card's info...")
            cursor = con.cursor()
            now = datetime.now()
            ready = now+timedelta(minutes=steps[0])
            cursor.execute(
                f"UPDATE {self.deck.name} SET INTERVAL=GREATEST(1,ROUND(0.75*INTERVAL+(2*RANDOM()-1)*INTERVAL*0.05)), LEARN_INTERVAL={steps[0]}, LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}',READY_DATE='{ready:%Y-%m-%d}',READY_TIME='{ready:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
        logger.debug(f"Lapse interval set at {steps[0]} minutes.")
        logger.info("Card's info changed.")
    def lapse_good(self):
        """
        Updating lapse learning card when user pressed 'GOOD' on it.
        Card goes up by one learning interval step for lapses, and if it already was at the last one then it is moved to reviews
        with the its current interval.
        Ready datetime/date is also changed to current datetime/date+learning interval/interval
        (depending on whether card was put into reviews).
        """
        logger.info("Request on a card:GOOD")
        options = self.deck.get_options()
        steps = options['LAPSE_STEPS'] # all of learning interval steps for a new card
        with Connection() as con:
            logger.debug("Connected to database successfully. Changing card's info...")
            cursor=con.cursor()
            cursor.execute(f"SELECT LEARN_INTERVAL FROM {self.deck.name} WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
            learn_interval=cursor.fetchall()[0][0] # checking current learning interval step
            if learn_interval==steps[-1]: # if it was the last one out of them then card gets put into reviews with current interval
                now = datetime.now()
                cursor.execute(f"UPDATE {self.deck.name} SET status='R',LEARN_INTERVAL=NULL, LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
                cursor.execute(f"UPDATE {self.deck.name} SET READY_DATE=LAST_DATE+INTERVAL,READY_TIME=NULL WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
                logger.debug("Card put to reviews pile.")
            else: # else, card goes up by one learning interval
                new_step=steps[steps.index(learn_interval)+1]
                now = datetime.now()
                ready = now + timedelta(minutes=new_step)
                cursor.execute(f"UPDATE {self.deck.name} SET LEARN_INTERVAL={new_step}, LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}',READY_DATE='{ready:%Y-%m-%d}',READY_TIME='{ready:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
                logger.debug(f"Lapse interval set at {new_step} minutes.")
        logger.info("Card's info changed.")
    def lapse_easy(self):
        """
        Updating lapse-learning card when user pressed 'EASY' on it.
        Card goes straight to reviews with current interval.
        Ready date is changed to current date+interval that was just set.
        """
        logger.info("Request on a card:EASY")
        with Connection() as con:
            logger.debug("Connected to database successfully. Changing card's info...")
            cursor=con.cursor()
            now = datetime.now()
            cursor.execute(f"UPDATE {self.deck.name} SET status='R', LEARN_INTERVAL=NULL, LAST_DATE='{now:%Y-%m-%d}', LAST_TIME='{now:%H:%M}' WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
            cursor.execute(f"UPDATE {self.deck.name} SET READY_DATE=LAST_DATE+INTERVAL,READY_TIME=NULL WHERE (FRONT='{self.front}' AND BACK='{self.back}')")
        logger.debug("Card put to reviews pile.")
        logger.info("Card's info changed.")








