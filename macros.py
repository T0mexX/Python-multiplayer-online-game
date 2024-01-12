from bitarray import bitarray
from enum import Enum

DICT_EXT = {"redd": "red",
              "orng": "orange",
              "prpl": "purple",
              "yllw": "yellow",
              "blue": "blue",
              "lblu": "lightblue",
              "gren": "green",
              "whte": "white",
              "blck": "black",
              "gray": "gray",
              }

DICT_ABBRV = {"red": "redd",
              "orange": "orng",
              "purple": "prpl",
              "yellow": "yllw",
              "blue": "blue",
              "lightblue": "lblu",
              "green": "gren",
              "white": "whte",
              "black": "blck",
              "gray": "gray",
              }

LIST_COLORS = ["redd", 
               "whte",
               "prpl", 
               "gren", 
               "yllw", 
               "blue", 
               "lblu", 
               "gray", 
               "orng", 
               "blck"]

DICT_CARS: dict = {"redd": "graphics/cars/car_red.png", 
                   "gren": "graphics/cars/car_green.png", 
                   "yllw": "graphics/cars/car_yellow.png", 
                   "blue": "graphics/cars/car_blue.png", 
                   "whte": "graphics/cars/car_white.png",
                   "lblu": "graphics/cars/car_lightblue.png",
                   "gray": "graphics/cars/car_gray.png",
                   "orng": "graphics/cars/car_orange.png",
                   "blck": "graphics/cars/car_black.png",
                   "prpl": "graphics/cars/car_purple.png"
                   }

POLYNOM = bitarray() #bitarray(b'\x01\x04\x81\x1d\xb7', "big")
POLYNOM = ('100000100101000010001110110110111')

LIST_PLAYER_LOBBY_POS = [(600, 60), 
                              (600, 100), 
                              (600, 140), 
                              (600, 180), 
                              (600, 220), 
                              (600, 260),
                              (600, 300),
                              (600, 340),
                              (600, 380),
                              (600, 420) 
                              ]

TRACKS = [{},
          {"dir" : "graphics/track_1.png",
           "collision" : "graphics/track_1.png",
           "redd": (1812, 4400),
           "whte": (1812, 4500),
           "blck": (1812, 4600),
           "orng": (1812, 4700),
           "prpl": (1812, 4800),
           "gren": (1812, 4900),
           "yllw": (1812, 5000),
           "blue": (1712, 4650),
           "lblu": (1712, 4750),
           "gray": (1712, 4850),  
           "direction": (1, 0)
           },
           {"dir": "graphics/track_2.png",
            "collision" : "graphics/track_2_coll.png",
           "redd": (1812, 4400),
           "whte": (1812, 4500),
           "blck": (1812, 4600),
           "orng": (1812, 4700),
           "prpl": (1812, 4800),
           "gren": (1812, 4900),
           "yllo": (1812, 5000),
           "blue": (1712, 4650),
           "lblu": (1712, 4750),
           "gray": (1712, 4850),  
           "direction": (1, 0)
           }
          ]

CAR_DIMENSIONS = (50, 80)

TITLE = "KartLOL"

TRACK_TO_TEST = 1

class Comms():
    WHITE = "whte".encode()
    RED = "redd".encode()
    BLACK = "blck".encode()
    ORANGE = "orng".encode()
    YELLOW = "yllw".encode()
    BLUE = "blue".encode()
    LIGHTBLUE = "lblu".encode()
    GREEN = "gren".encode()
    GRAY = "gray".encode()
    PURPLE = "prpl".encode()

    LEADER = "lead".encode()
    USED = "used".encode()
    START = "strt".encode()
    FULL = "full".encode()
    TO_RACE = "torc".encode()
    STATUS = "stat".encode()
    START_TIME = "strt".encode()
    KILL = "kill".encode()
    FINAL_PLACE = "plce".encode()
    RACE_END = "endd".encode()
    LEAVE = "leav".encode()
    NAME = "name".encode()

    ACKNOWLEDGMENT = "ackn".encode()
    UPDATE = "updt".encode()
    CROSS = "cros".encode()
    POSITION = "poss".encode()
    
class GameParams():
    MAX_SPEED_FORWARD = 0.6             #default: 0.6
    MAX_SPEED_BACKWARD =  0.4           #default: 0.6
    MAX_ROTATION = 1                    #default: 1
    SPEED_FORWARD = 0.00072             #default: 0.00072
    SPEED_BACKWARD = 0.00048            #default: 0.00072
    SPEED_REDUCTION = 0.00036           #default: 0.00036
    STEERING = 0.018                    #default: 0.018
    STEERING_REDUCTION = 0.009          #default: 0.009
    COLLISION_BOUNCE_SCALAR = 0.5       #default: 0.5
    COLLISION_SLOWDOWN_SCALAR = 0.5     #default: 0.5

class Flags_Text_pop_up(Enum):
    ANTIAL = 1


