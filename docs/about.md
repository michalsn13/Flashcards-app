## About the project

**1.Why was it made?**

I wanted to make a project that does not only have learning purposes but can also be helpful in something not programming related. Then, I got inspired by an app called ANKI 
that provides a well-developed learning plan for studying (mainly languages but not only). The idea of implementing that in Python didn't sound complicated, so after 
understanding how ANKI algorithm works, I have decided to give it a try.

**2.How does the program work from the user perspective?**

After starting with the program (more on that in *guide.md*) user has to create a deck (or select one if already exists) that is gonna store all of his studying cards. Then, if it's
empty, some cards must be added (try with *capitals.txt* as a sample cards file). That enables the user to start the main part of the app: a learning session. 
The session provides one side of the card and expects the user to recall the other side of it and then to determine how easy it was for him. If a card was easy to recall, it will come back later than a hard one 
(more on that in *Life of a card.pdf*). Every session is made of 3 parts: cards that are in the process of learning (learning cards), cards that were never seen before (new cards) and cards that are already learned and have to be reviewed (reviews). Every day has its plan on how many cards of those types should be seen and after
completing it the user has to wait for the next day (or to increase the limit for new cards). If the plan won't be completed, the cards will be postponed for the next day. 
Of course, there is a daily limit for new cards because after adding 100 new words, you don't want to see them all at once. It is important to take sessions every day because 
every omitted one will stack cards for the next day.
Besides adding new cards and taking sessions, the user can also change the deck's options (more on that in *Options/options.py* as well as in *Life of a card.pdf*) and delete the deck.

**3.What do those Python classes do?**

All of the classes are described before their methods in *.py* files so I won't go into details here. As the names suggest there are *Decks* filled with *Cards* and *Sessions* can be performed on them. *Options* present the default options for every created *Deck*. *Deckshandler* visualizes all existing decks with their studying plans. *Connection* is the bridge between
Python and user's inputs and SQL database. Without it (the database) user's studying progress will be erased every time the codes finishes running.

**4.Is it better than ANKI?**

I'd say that it's a simplification of the ANKI app as it does not have all of ANKI's features (for example single card parameters can only be seen through SQL- 
they cannot be visualized by the user). What makes it better for me is the fact I can modify the program to suits my studying preferences more.

**5.Are there any plans on updating the project?**

I'm thinking about the possibility to add only the fronts of cards and translating them to a given language automatically. For example, you have a deck of polish-english words and 
you come across a new polish word 'zegar'- it can be received by the program, translated to english (to 'clock') and added to the deck as a card.
From the Python perspective, I'd probably use scraping from any web dictionary.
