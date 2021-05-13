# GLOBAL IMPORTS (PYTHON PACKAGES)
import logging
# LOCAL IMPORTS
from menu import menu
logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S',
                    level=logging.DEBUG,
                    filename='logs.txt')
logger=logging.getLogger('flashcards')
menu() # starting app with menu() function










