# GLOBAL IMPORTS (PYTHON PACKAGES)
import logging
# LOCAL IMPORTS
from Connection.connection import Connection
from Deck.deck import Deck
logger=logging.getLogger('flashcards.deckshandler')
class DecksHandler:
    """
    Short class for visualization of existing decks.
    """
    @classmethod
    def all_decks_printer(cls):
        """
        Returning all existing decks and printing them with their daily plans.
        """
        logger.info("Request to show all decks.")
        with Connection() as con:
            logger.debug("Connected to database successfully. Preparing all decks...")
            cursor = con.cursor()
            cursor.execute("SELECT name from decks")
            decks = cursor.fetchall()
        decks = [i[0] for i in decks]
        print("""DECKS (with number of cards left for today shown):
----------""")
        for i in decks:
            print(f"* {i}   ({Deck(i).daily_count_printer()})")
        print("----------")
        logger.info("Decks printed out.")
        return decks







