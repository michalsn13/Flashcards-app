class Options:
    """
        Class is meant to show what options are changeable when it comes to studying.
        It shows the default options passed to every new deck defined (if its options are not specified
        by the user).
    """
    """
       Options explained:
       NEW_DAILY_COUNT=If you add multiple cards to a defined deck and you start your session then it wouldn't
       be a good idea to end the session only after you looked through all those new cards.
       That is why there is a limit on how many new cards can be passed to user during a single day.
       This option sets default limit and it can be changed later by the use of change_limit() function on a Deck object.

       EASE_FACTOR=If you press GOOD or EASY on a review then the current interval gets multiplied by the ease_factor.
       Also, pressing EASY adds extra 0.1 to the EASE_FACTOR, pressing HARD/AGAIN substracts 0.1/0.2 from it.

       EASY_BONUS=Extra multiplier of the interval if you press EASY on a review card.

       REVIEW_INTERVAL=Starting interval for a card that goes from learning to review having passed all of the learning interval
       steps one by one. Expressed in full days (counted "on a calendar", not always in full 24 hours).

       EASY_REVIEW_INTERVAL=Starting interval for a card that goes from learning to review by a shortcut of pressing EASY on it.
       Expressed in full days (counted "on a calendar", not always in full 24 hours).

       EARLY_LEARNING=Learning card can be seen (EARLY_INTERVAL) minutes earlier than the learning_interval suggests.
       Works only for learning cards with learning_interval which sets them ready on the same day as they were last seen.

       NEW_STEPS=List of learning_intervals for a card that came to learning from being new.
       New card starts at the first interval on the list and every time user clicks GOOD on it it goes to the next one.
       If all of them are passed card is put in reviews with REVIEW_INTERVAL as the interval. Also, if during that "journey" you press
       AGAIN then card has to start again at the first interval. And, if you press EASY card shortcut its way
       to reviews with EASY_REVIEW_INTERVAL as the interval.

       LAPSE_STEPS=Same idea as with the NEW_STEPS but for lapses (learning card which came from reviews after pressing AGAIN on them). 
    """
    default_options={'NEW_DAILY_COUNT':5, # CARDS
                     'EASE_FACTOR':2.5,
                     'EASY_BONUS':1.3,
                     'REVIEW_INTERVAL':1,# DAYS
                     'EASY_REVIEW_INTERVAL':3,# DAYS
                     'EARLY_LEARNING':20, # MINUTES
                     'NEW_STEPS':'{1,10,360}', # MINUTES
                     'LAPSE_STEPS':'{10}' # MINUTES
                     }








