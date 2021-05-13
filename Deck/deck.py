#  GLOBAL IMPORTS (PYTHON PACKAGES)
from re import findall, search # recognizing if file is .txt and patterns of cards in it
import psycopg2.errors as errors # handling errors with duplicates added to deck
from datetime import datetime #  setting LAST_DATE/LAST_TIME for a card and checking if it is ready to be studied
from collections import deque #  storing cards (deque to pop from left side)
import logging
from random import randrange #  checking random line from a .txt file (for debugging)
#  LOCAL IMPORTS
from Connection.connection import Connection #  connecting to SQL database
from Options.options import Options #  default parameters for studying deck
from Card.card import Card #  defining card as an object that can be modified
logger=logging.getLogger('flashcards.deck')
class Deck:
    """
    Deck is connected to SQL table that stores all of its cards.
    Every deck has its own changeable studying options (if not specified then set on default).
    Deck object provides cards of given status that are ready to be studied.
    It also counts how many cards should be seen during the current day.
    """
    # Defining Deck() object by its name and options
    def __init__(self, name:str):
        """
        Deck is defined by its name and options for studying cards (more in Options class).
        """
        logger.info(f"Deck '{name}' called.")
        default_options = Options.default_options
        available_name = "^[A-Za-z0-9_]+$"
        if not findall(available_name,name):
            logger.error(f"Name '{name}' is invalid (pattern in regex:{available_name}). Deck not created")
            raise Exception #  exception is 'caught' by the menu() function in 'menu.py'
        self.name=name
        #  checking if deck of that name already exists...
        with Connection() as con:
            logger.debug(f"Connected to database successfully. Looking for deck '{name}'...")
            cursor=con.cursor()
            cursor.execute(f"SELECT * from decks WHERE name='{name}'")
            our_deck=cursor.fetchall()
            logger.debug(f"Found {our_deck[0][0] if our_deck else None}.")
        # ...and if it does not then program creates one.
        # Program does not ask the user whether it was his intention to create a new deck or if it was a typing mistake.
        with Connection() as con:
            cursor = con.cursor()
            if not our_deck:
                logger.debug(f"Connected to database successfully. Creating new deck...")
                print(f'Creating new deck with name:{name}...')
                # Card in SQL table:
                    # front, back: text to be seen while studying card
                    # status: one of 'N'-new, 'NL'-fresh learner, 'LL'-lapse learner, 'R'-review
                    # interval: days interval for review card to come back
                    # learn_interval: minutes interval for learning card to come back
                    # add_time: date when the card was added to the deck
                    # last_date, last_time: last time the card seen
                    # ready_date, ready_time: last_date/last_time + interval/learn_interval
                    # ease_factor: extra interval bonus (modifier) for clicking 'GOOD' or 'EASY' on a review card
                # Every card is defined by its front and back, therefore there cannot be 2 cards with the same front and back in a single deck
                try:
                    cursor.execute(f"""CREATE TABLE {self.name}(
                                                                        FRONT VARCHAR(50), 
                                                                        BACK VARCHAR(50), 
                                                                        STATUS TEXT, 
                                                                        INTERVAL INT, 
                                                                        LEARN_INTERVAL INT, 
                                                                        ADD_DATE DATE,
                                                                        LAST_DATE DATE, 
                                                                        LAST_TIME TIME,
                                                                        READY_DATE DATE,
                                                                        READY_TIME TIME,
                                                                        EASE_FACTOR FLOAT, 
                                                                        PRIMARY KEY (FRONT, BACK))
                                                                        """)
                    # Putting deck's name into a deck's list to know that it already exists if called next time.
                    # Decks table also stores all of the options that can be changed. At the beginning they are at default (defined in Options class)
                    cursor.execute(f"""
                                        INSERT INTO decks VALUES(
                                        '{name}',
                                        {default_options['NEW_DAILY_COUNT']},
                                        {default_options['NEW_DAILY_COUNT']},
                                        NOW(),
                                        {default_options['EASE_FACTOR']},
                                        {default_options['EASY_BONUS']},
                                        {default_options['REVIEW_INTERVAL']},
                                        {default_options['EASY_REVIEW_INTERVAL']},
                                        {default_options['EARLY_LEARNING']},
                                        '{default_options['NEW_STEPS']}',
                                        '{default_options['LAPSE_STEPS']}')
                                        """)
                    # Defining view {deck's name}_plan as cards that are or will be ready in the current day
                    # Minding the limit for new cards to show.
                    cursor.execute(f"""CREATE VIEW {name}_plan AS (
                                                        SELECT * FROM (
                                                        (SELECT * FROM {name} WHERE READY_DATE<=CURRENT_DATE AND STATUS='N' ORDER BY ADD_DATE ASC LIMIT (SELECT LIMIT_LEFT FROM decks WHERE name='{name}'))
                                                        UNION ALL
                                                        (SELECT * FROM {name} WHERE READY_DATE<=CURRENT_DATE AND STATUS IN ('NL','LL','R') ORDER BY READY_DATE ASC, READY_TIME ASC)
                                                        ) AS foo)
                                                        """)
                except Exception as e:
                    logger.critical(e) #random error not caught earlier will crash the program
                    logger.critical(f"Unknown error occurred when adding new deck to SQL.\n{e}")
                    raise e
                logger.info(f"Deck '{name}' created.")
                print(f"Deck '{name}' created.")
            else:
                # If deck already exists and it's the first session of the day then reset LIMIT_LEFT to NEW_LIMIT
                cursor.execute(f"UPDATE DECKS SET LIMIT_LEFT=NEW_LIMIT, LAST_DATE=CURRENT_DATE WHERE name='{self.name}' AND LAST_DATE!=CURRENT_DATE")

    # String representation of a deck- its name.
    def __repr__(self):
        """
        String representation of a deck- its name.
        """
        return f"Deck({self.name})"

    # Providing summary of different cards types to study in a current day.
    # If there is no plan on adding new cards then the number of new and review cards can only go down during day
    # Number of learning cards for a day can grow if for example new card turns into a learning card
    def daily_count_printer(self):
        """
        Function provides the number of cards to be studied in a current day.
        It separates them by its status.
        If a new card or a review card is counted in the daily summary then it can be studied any time in that day.
        But when it comes to a learning card that was counted, it may be ready later during that day.
        For example: if a learning card is put at 1:00 PM on a 30 minutes interval (with the assumption that
        there is no early learning) then it will show up in the daily summary at 1:01 PM but it won't be
        ready to be studied till 1:10 PM that day.
        """
        logger.info("Request to get daily plan of card types.")
        with Connection() as con:
            logger.debug("Connected to database successfully. Getting daily plan...")
            cursor = con.cursor()
            cursor.execute(f"""
                (SELECT 'N', count(*) FROM {self.name}_plan WHERE status='N')
                UNION ALL
                (SELECT 'L', count(*) FROM {self.name}_plan WHERE status IN ('NL','LL'))
                UNION ALL
                (SELECT 'R', count(*) FROM {self.name}_plan WHERE status='R')
                """)
            x = cursor.fetchall()
        # Creating dict {'N':no. of new cards, 'L':no. of learning cards,'R':no. of reviews}
        count_dict =dict(x)
        logger.debug(f"Daily plan found: {count_dict}")
        # return print(f"PLAN FOR {datetime.today():%Y-%m-%d}\nNew cards: {count_dict['N']}\nLearning cards: {count_dict['L']}\nReviews: {count_dict['R']}")
        return f"N:{count_dict['N']} | L:{count_dict['L']} | R:{count_dict['R']}"
    def get_learners(self):
        """
        Function returns learning cards that are ready to be studied at that moment (with
        possible early learning option in mind). Function provides them as a deque od Card objects.
        """
        logger.info("Request to get ready learning cards.")
        early_learning=self.get_options()['EARLY_LEARNING']
        logger.debug(f"Early learning: {early_learning} minutes AS {type(early_learning)}")
        with Connection() as con:
            logger.debug("Connected to database successfully. Getting learning cards...")
            cursor = con.cursor()
            try:
                cursor.execute(f"""SELECT front,back,status FROM {self.name}_plan 
                            WHERE status IN ('NL','LL') AND 
                            (LAST_DATE<CURRENT_DATE OR CAST(READY_TIME-INTERVAL '{early_learning} MINUTES' AS TIME)<=CURRENT_TIME)
                            ORDER BY READY_DATE ASC,READY_TIME ASC
                            """)
            except Exception as e:
                logger.critical(f"Unknown error occurred when selecting data from deck {self.name}\n{e}")
                raise e
            learn_cards = cursor.fetchall()
        learn_cards = deque([Card(deck=self,front=card[0], back=card[1],status=card[2]) for card in learn_cards])
        logger.debug(f"Learning cards for now found: {learn_cards}")
        return learn_cards

    def get_new(self):
        """
        Function returns new cards that are ready to be studied at that moment
        (with set new cards daily limit in mind). Function provides them as a deque od Card objects.
        """
        logger.info("Request to get new cards.")
        with Connection() as con:
            logger.debug("Connected to database successfully. Getting new cards...")
            cursor = con.cursor()
            cursor.execute(
                f"SELECT front,back, status FROM {self.name}_plan WHERE status='N' ORDER BY ADD_DATE ASC")
            new_cards = cursor.fetchall()
        new_cards = deque([Card(deck=self,front=card[0], back=card[1],status=card[2]) for card in new_cards])
        logger.debug(f"New cards found: {new_cards}")
        return new_cards

    # Providing reviews that are ready to be studied now as a deque of Card() objects
    def get_reviews(self):
        """
        Function returns reviews that are ready to be studied at that moment
        (or in that day in general. Function provides them as a deque od Card objects.
        """
        logger.info("Request to get ready review cards.")
        with Connection() as con:
            logger.debug("Connected to database successfully. Getting reviews...")
            cursor=con.cursor()
            cursor.execute(f"SELECT front,back, status FROM {self.name}_plan WHERE status='R' ORDER BY READY_DATE") # providing reviews
            review_cards=cursor.fetchall()
        review_cards=deque([Card(deck=self,front=card[0], back=card[1],status=card[2]) for card in review_cards])
        logger.debug(f"Reviews found: {review_cards}")
        return review_cards

    # Inserting cards to SQL table from a .txt file with '/' as a separator
    def add_cards(self):
        """
        Function inserts cards to SQL table of a deck. It takes them from a .txt file
        where they are in different rows with a pattern "front/back".
        """
        logger.info("Request to add new cards from a file.")
        options = self.get_options()
        cards = input("Type .txt file name (for example 'dictionary.txt'): ")
        if not search("\.txt$",cards): #checking if file is a text one
            logger.error(f"Wrong file format-.txt expected but received: '{cards}'")
            return print("Wrong file format- .txt expected.")
        try:
            with open(cards,'r') as file:
                logger.debug(f"Opening {cards} file...")
                lines=[line.strip() for line in file.readlines()]
        except FileNotFoundError:
            logger.error(f"File '{cards}' not found.")
            return print('File not found. Make sure it is in the location you specified.')
        all_cards=len(lines)
        logger.debug(f"File with cards opened. {all_cards} possible cards found")
        logger.debug(f"Random line from file: {lines[randrange(0,all_cards)]}")
        # Looking for pattern of the front and back word separated with '/'
        word_pattern="[A-ZÓŁŚŻŹĆa-zęółśążźćń ']+"
        separator="/"
        logger.debug(f"Current separator: {separator}")
        pattern=f"^({word_pattern}){separator}({word_pattern})$"
        mistakes,duplicates=0,0
        logger.info("Adding cards to SQL table...")
        for pair in lines:
            with Connection() as con:
                logger.debug(f"Connected to database successfully. Trying to interpret '{pair}' as a card...")
                cursor = con.cursor()
                found=search(pattern,pair)
                if found:
                    card=Card(self,found.group(1).strip(),found.group(2).strip(),'N')
                    logger.debug(f"Pattern recognized. Adding {card} to deck...")
                    # Pattern was found, we have front and back of a card
                    try:
                        # Adding front, back if found, setting status as NEW
                        # Setting first learning_interval and the ease factor using deck's options
                        now = datetime.now()
                        cursor.execute(f"""INSERT INTO {self.name} VALUES(
                                        '{card.front}',
                                        '{card.back}',
                                        'N',
                                        NULL, 
                                        {options['NEW_STEPS'][0]},
                                        '{now:%Y-%m-%d}',
                                        NULL,
                                        NULL,
                                        '{now:%Y-%m-%d}',
                                        '{now:%H:%M}',
                                        {options['EASE_FACTOR']})
                                        """)
                    except errors.UniqueViolation:
                        # (front, back) had to already be in the table so we count it as a duplicate and rollback
                        duplicates+=1
                        logger.warning(f"{card} already in deck- counted as duplicate.")
                        print(f'{card} already in deck.')
                        con.rollback() # rollbacking not to crash the program
                    else:
                        logger.debug(f"{card} added successfully.")
                # Pattern was not found so we count it as a mistake
                else:
                    logger.warning(f"Pattern not recognized when received '{pair}'.")
                    mistakes+=1
                    print(f"'{pair}': unknown format")
        logger.info(f"{all_cards-mistakes-duplicates} new cards added to deck.")
        print(f"""Process finished.
        New cards added: {all_cards-mistakes-duplicates}
        Unknown formats: {mistakes}
        Duplicates (already in deck): {duplicates}""")

    def delete(self):
        """
        Function deletes the SQL table connected to the deck
        and pulls its name from all decks table.
        """
        logger.info(f"Request to delete deck '{self.name}'.")
        decision=input(f"Are you sure that you want to delete deck {self.name}? Type 'Y' if so, else type anything except 'Y'.")
        if decision=='Y':
            with Connection() as con:
                logger.debug("Connected to database successfully. Deleting all deck's data...")
                cursor=con.cursor()
                cursor.execute(f'DROP TABLE {self.name} CASCADE')
                cursor.execute(f"DELETE from decks where name='{self.name}'")
            logger.info("Deck deleted.")
            print(f'Deck {self.name} has been deleted.')
        else:
            print("Deck not deleted.")

    def change_options(self):
        """
        Function changes specific options of deck used for session purposes.
        """
        logger.info("Request to change deck's options.")
        options_changed=[]
        current_options=self.get_options()
        print("Type value if you want to change specific option. If not, press ENTER without typing. ")
        # NEW LIMIT
        new_limit = input(f"NEW_LIMIT={current_options['NEW_LIMIT']} cards | New value (positive integer): ").strip()
        if new_limit == '':
            pass
        else:
            try:
                new_limit=int(new_limit)
            except Exception:
                print('Invalid value. Option not changed.')
            else:
                if new_limit <= 0:
                    print('Invalid value. Option not changed.')
                else:
                    with Connection() as con:
                        logger.debug(f"Connected to database successfully. Updating NEW_LIMIT...")
                        cursor = con.cursor()
                        cursor.execute(f"UPDATE decks SET NEW_LIMIT={new_limit}, LIMIT_LEFT=LIMIT_LEFT+GREATEST(0,({new_limit}-NEW_LIMIT)) WHERE name='{self.name}'")
                    print(f'Value changed to {new_limit}.')
                    options_changed.append('NEW_LIMIT')
            #  EARLY_LEARNING
            new_el = input(
                    f"EARLY_LEARNING={current_options['EARLY_LEARNING']} minutes | New value (positive integer): ").strip()
            if new_el=="":
                pass
            else:
                try:
                    new_el=int(new_el)
                except Exception:
                    print('Invalid value. Option not changed.')
                else:
                    if new_el <= 0:
                        print('Invalid value. Option not changed.')
                    else:
                        with Connection() as con:
                            logger.debug(f"Connected to database successfully. Updating EARLY_LEARNING...")
                            cursor = con.cursor()
                            cursor.execute(f"UPDATE decks SET EARLY_LEARNING={new_el} WHERE name='{self.name}'")
                        print(f'Value changed to {new_el}.')
                        options_changed.append('EARLY_LEARNING')
        # INTERVALS
        for key in ['REVIEW_INTERVAL','EASY_REVIEW_INTERVAL']:
            new_days = input(f"{key}={current_options[key]} days | New value (positive integer): ").strip()
            if new_days=="":
                pass
            else:
                try:
                    new_days=int(new_days)
                except Exception:
                    print('Invalid value. Option not changed.')
                else:
                    if new_days<=0:
                        print('Invalid value. Option not changed.')
                    else:
                        with Connection() as con:
                            logger.debug(f"Connected to database successfully. Updating {key}...")
                            cursor = con.cursor()
                            cursor.execute(f"UPDATE decks SET {key}={new_days} WHERE name='{self.name}'")
                        print(f'Value changed to {new_days}.')
                        options_changed.append(key)
        # FACTORS
        for key in ['EASE_FACTOR', 'EASY_BONUS']:
            new_bonus =input(f"{key}={current_options[key]} | New value (number greater or equal than 1): ").strip()
            if new_bonus=="":
                pass
            else:
                try:
                    new_bonus=float(new_bonus)
                except Exception:
                    print('Invalid value. Option not changed.')
                else:
                    if new_bonus < 1:
                        print('Invalid value. Option not changed.')
                    else:
                        with Connection() as con:
                            logger.debug(f"Connected to database successfully. Updating {key}...")
                            cursor = con.cursor()
                            cursor.execute(f"UPDATE decks SET {key}={new_bonus} WHERE name='{self.name}'")
                        print(f'Value changed to {new_bonus}.')
                        options_changed.append(key)
        # STEPS
        for key in ['NEW_STEPS','LAPSE_STEPS']:
            new_steps=input((f"{key}={current_options[key]} steps in minutes | New value (positive integers separated by ', '): ")).strip()
            if new_steps=="":
                pass
            else:
                try:
                    new_steps=[int(i)for i in new_steps.split(',')]
                except Exception:
                    print('Invalid value. Option not changed.')
                else:
                    if min(new_steps)<=0:
                            print('One of the steps is invalid. Option not changed.')
                    else:
                        new_steps='{'+(',').join([str(i) for i in new_steps])+'}'
                        with Connection() as con:
                            logger.debug(f"Connected to database successfully. Updating {key}...")
                            cursor = con.cursor()
                            cursor.execute(f"UPDATE decks SET {key}='{new_steps}' WHERE name='{self.name}'")
                        print(f"Value changed to {new_steps}.")
                        options_changed.append(key)
        logger.info(f"Options: {', '.join(options_changed)} changed. ")
        print("No more options to be changed.")

    def any_cards(self):
        """
        Function works similarly to daily_count_printer(), but returns if there are any
        cards left for today. It is used when user wants to start a session to check if there
        is anything more for him to learn in that day.
        """
        logger.info("Request to show if there are any cards for today to learn.")
        with Connection() as con:
            logger.debug("Connected to database successfully. Counting all cards for today..")
            cursor = con.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {self.name}_PLAN")
            x=cursor.fetchall()[0][0]
        logger.debug(f"There are {x} cards still to be learned today.")
        return x>0 # tells if there are any cards left for today
    def get_options(self):
        """
        Function made for providing all deck's options as dictionary.
        """
        logger.info("Request to get deck's options.")
        with Connection() as con:
            logger.debug("Connected to database successfully. Loading all of deck's current options...")
            cursor=con.cursor()
            cursor.execute(f"SELECT NEW_LIMIT, EASE_FACTOR, EASY_BONUS,REVIEW_INTERVAL, EASY_REVIEW_INTERVAL, EARLY_LEARNING, NEW_STEPS, LAPSE_STEPS FROM decks WHERE name='{self.name}'")
            x=list(cursor.fetchall()[0])
        options_dict={i: j for i, j in zip(['NEW_LIMIT', 'EASE_FACTOR', 'EASY_BONUS', 'REVIEW_INTERVAL', 'EASY_REVIEW_INTERVAL', 'EARLY_LEARNING','NEW_STEPS', 'LAPSE_STEPS'], x)}
        logger.debug(f"Deck's options: {options_dict}")
        return options_dict







