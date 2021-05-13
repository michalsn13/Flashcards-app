# LOCAL IMPORTS
from Connection.connection import Connection # connecting to SQL database
"""
    It's meant to be run only before using the project for the first time (or at least for the first time in
    a certain database (make sure you changed parameters in Connection/'con_parameters.py' file.
    """
with Connection() as con:
    cursor=con.cursor()
    cursor.execute('DROP TABLE IF EXISTS decks CASCADE')
    """
    Deck table: created for storing names and options of existing decks (for example to know if called deck has to be created)
    and managing daily new cards limits.
    """
    cursor.execute("""CREATE TABLE decks(
    name TEXT, 
    new_limit INT, 
    limit_left INT, 
    last_date DATE, 
    EASE_FACTOR FLOAT,
    EASY_BONUS FLOAT, 
    REVIEW_INTERVAL INT, 
    EASY_REVIEW_INTERVAL INT, 
    EARLY_LEARNING INT, 
    NEW_STEPS FLOAT[], 
    LAPSE_STEPS FLOAT[], 
    PRIMARY KEY (name))
    """)


