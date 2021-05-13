# GLOBAL IMPORT (PYTHON PACKAGES)
import logging
# LOCAL IMPORTS
from DecksHandler.deckshandler import DecksHandler # all decks visualization
from Deck.deck import Deck # operations on specific deck
from Session.session import DailySession # session on specific deck
logger=logging.getLogger('flashcards.menu')
def menu():
    """
    menu() handles all of interactions with user. It 'connects' his decisions
    to corresponding functions created in all of the classes.
    Program is separated into main menu and specific deck menu. It always starts
    with main menu and if deck is selected or created successfully it switches
    to that deck's menu. If deck something goes wrong then or deck will be deleted
    program goes back to main menu which forms a loop.
    Loop can be stopped by quitting app.
    """
    main_commands="""Possible commands on main menu:
----------
> 'SELECT'-select one of existing decks,
> 'CREATE'-create new deck,
> 'QUIT_APP'-close app.
----------"""
    deck_commands="""Possible commands on picked deck:
----------
> 'ADD_CARDS'-add new cards from a .txt file,
> 'SESSION'-start learning session,
> 'CHANGE_OPTIONS'-change options,
> 'DELETE'-delete deck,
> 'SHOW_PLAN'-show learning plan for today,
> 'QUIT'-come back to main menu.
----------"""
    logger.info("Program launched by user.")
    print("Welcome to Flashcards Learner.")
    while True:
        decks=DecksHandler.all_decks_printer() # all decks shown with their daily plans
        first_choice=input("What do you want to do? Press '?' to see possible commands. ").strip().upper()
        while first_choice not in ['SELECT','CREATE']:
            if first_choice=="?": # commands shown
                print(main_commands)
                first_choice = input("What do you want to do? Press '?' to see possible commands. ").strip().upper()
            elif first_choice.strip().upper()=="QUIT_APP": # program closed
                logger.info("Program closed by user.")
                print("Thanks for using app. See you later!")
                quit()
            else:
                logger.warning(f"Invalid quest on main menu:{first_choice}.")
                first_choice=input("Invalid decision.\nWhat do you want to do? Press '?' to see possible commands.").strip().upper()
        logger.debug(f"USER typed: {first_choice}. Preparing deck...") # decision to SELECT/CREATE deck made successfully
        possible_outputs={"SELECT":("Select one of available decks.","No deck of given name.",False),
            "CREATE":("Type name of new deck.","That deck already exists.",True)}
        picked_deck=input(f"{possible_outputs[first_choice][0]} Press '?d' to load list of all decks.").strip().lower()
        while picked_deck=="?d" or (picked_deck in decks)==possible_outputs[first_choice][2]:
            if picked_deck == "?d": # all decks shown
                DecksHandler.all_decks_printer()
                picked_deck = input(f"{possible_outputs[first_choice][0]} Press '?d' to load list of all decks.").strip().lower()
            else:
                logger.warning(f"{picked_deck}:{possible_outputs[first_choice][1]}.") # trying to create existing deck or select non-existing deck
                picked_deck = input(f"{possible_outputs[first_choice][1]}\nSelect one of available decks. Press '?d' to load list of all decks. ").strip().lower()

        try:
            current_deck=Deck(picked_deck) # trying to call/create deck of given name
        except Exception: # name invalid for SQL Table
            logger.error(f"Name {picked_deck} is invalid. Back to main menu.")
            print('Given name is invalid. Name can only contain letters, numbers and underscores.')
        else:
            decisions={'ADD_CARDS':current_deck.add_cards,
                       'SESSION':DailySession(current_deck).full_study,
                       'CHANGE_OPTIONS':current_deck.change_options,
                       'DELETE':current_deck.delete,
                       'SHOW_PLAN':(lambda: print(current_deck.daily_count_printer())),
                       'QUIT':None}
            logger.info(f"{current_deck} was selected/created by user.")
            second_choice=input(f"{current_deck}\nWhat do you want to do? Press '?' to see possible commands. ").strip().upper()
            while True:
                while second_choice not in decisions.keys():
                    if second_choice=="?": # commands shown
                        print(deck_commands)
                        second_choice = input(f"{current_deck}\nWhat do you want to do? Press '?' to see possible commands. ").strip().upper()
                    else:
                        logger.warning(f"Invalid quest on main menu:{second_choice}.")
                        second_choice = input(f"{current_deck}\nInvalid decision.\nWhat do you want to do? Press '?' to see possible commands. ").strip().upper()
                if second_choice=='QUIT': # back to main menu
                    logger.info(f"User quit deck {current_deck}. Back to main menu.")
                    break
                logger.debug(f"USER typed: {second_choice}. Starting corresponding function...")
                decisions[second_choice]() # decision on deck made successfully
                input(f"Press ENTER to come back.")
                if second_choice=="DELETE": # deck was deleted, back to main menu then
                    break
                second_choice = input(f"{current_deck}\nWhat do you want to do? Press '?' to see possible commands. ").strip().upper()
        print("Back to main menu.")








