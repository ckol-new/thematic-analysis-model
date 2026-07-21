# managing data: Loading data, cleaning database
#   while other classes can interact with the data, update the data, and read from data, this is more for general data management.


# Loader class:
#   loads data, returns connection + lancedb tables. 
#   Generally, a single loader will be passed to other classes to enable them to make database connections. Rather than passing a bunch 
#   of connections around.


# Manager class:
#   Manages data, updates boolean flags, clears history to save space.
#   Manager can be passed to classes that require ability to alter database state, at a broad level.


