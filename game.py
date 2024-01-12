import pygame as pg
from sys import exit
from threading import Thread
from threading import Event
from time import sleep
from time import time_ns
from queue import Queue
from bitarray import bitarray
from bitarray.util import ba2int
import socket
import pickle
import math
import macros
from macros import Comms
from macros import GameParams
from macros import Flags_Text_pop_up
import random

class Game_states():
    MENU = 0
    LOBBY = 1
    COUNTDOWN = 2
    RACE = 3
    FINISHED = 4


pg.init()
screen = pg.display.set_mode((1000, 700))
pg.display.set_caption("bo")
clock = pg.time.Clock()



wasd = [False, False, False, False]
player_position = pg.math.Vector2(500, 400)
player_position_center_surface = pg.math.Vector2(-610, -610)
sock = None
hostport = ("localhost", 12345)

queue_recv = Queue()

font_list_player = pg.font.Font(None, 30)
game_state = Game_states.MENU 
font_title = pg.font.Font("graphics/fonts/CCOverbyteOff-Italic.ttf", 80)
font_text_box = pg.font.Font(None, 50)
font_insert = pg.font.Font(None, 30)




class Enter_img(pg.sprite.Sprite):
    def __init__(self):
        super(). __init__()
        self.image = pg.transform.scale(pg.image.load("graphics/enter_key.png").convert_alpha(), (80, 80))
        self.rect = self.image.get_rect(center = (750, 400))

class Title(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = font_title.render(macros.TITLE, False, "aquamarine2")
        self.rect = self.image.get_rect(center = (500, 150))

class Sprite_insert(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = font_insert.render("Type your nickname", False, "white")
        self.rect = self.image.get_rect(center = (500, 480))

class Text_box(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = font_text_box.render(nickname, False, "aquamarine2")
        self.rect = self.image.get_rect(center = (500, 400))
    def update(self):
        self.image = font_text_box.render(nickname, False, "aquamarine2")
        self.rect = self.image.get_rect(center = (500, 400))

class Player_line_name(pg.sprite.Sprite):
    def __init__(self, coord, nickname = None):
        super().__init__()
        if nickname: self.image = font_list_player.render(nickname, False, "White")
        else: 
            self.image = pg.Surface((400, 60))
            self.image.fill("Black")
        self.rect = self.image.get_rect(topleft = coord)
        self.coord = coord
    def update(self, nickname): 
        self.image = font_list_player.render(nickname, False, "White")
        self.rect = self.image.get_rect(topleft = self.coord)

class Player_line_color(pg.sprite.Sprite):
    def __init__(self, coord, color = None):
        super().__init__()
        self.image = pg.Surface((30, 30))
        self.rect = self.image.get_rect(center = (coord[0] - 40, coord[1] + 10))
        if color: self.image.fill(color)
    def update(self, color):
        self.image.fill(macros.DICT_EXT[color]) 

class Text_pop_up(pg.sprite.Sprite):
    def __init__(self, text, coord, color = "white", font_style = None, final_size = 30, duration = 1000000000, hold_duration = 300000000, start_time = None,  **flags):
        super().__init__()
        self.text = text
        self.coord = coord
        self.color = color
        self.style = font_style
        self.final_size = final_size
        self.duration = duration
        self.hold_duration = hold_duration
        self.antial = (Flags_Text_pop_up.ANTIAL in flags)

        self.start_time = time_ns() if not start_time else start_time
        self.image = pg.font.Font(self.style, 0).render(self.text, self.antial, self.color)
        self.rect = self.image.get_rect(center = coord)
    def update(self):
        anim_stage = time_ns() - self.start_time
        if anim_stage < 0: return 
        if anim_stage < self.duration:
            self.image = pg.font.Font(self.style, int((anim_stage/self.duration)*self.final_size)).render(self.text, self.antial, self.color)
        else:
            anim_stage -= self.duration
            if anim_stage > self.hold_duration:
                self.kill()
            else:
                self.image = pg.font.Font(self.style, self.final_size).render(self.text, self.antial, self.color)
        
        self.rect = self.image.get_rect(center = self.coord)

class Lobby_status:
    def __init__(self, initial_dict):
        self.dict_players = initial_dict
        self.player_list = []
        for index in range(10):
            self.player_list.append(pg.sprite.Group())
            if index < len(initial_dict):
                self.player_list[index].add(Player_line_name(macros.LIST_PLAYER_LOBBY_POS[index], list(initial_dict.values())[index]))
                self.player_list[index].add(Player_line_color(macros.LIST_PLAYER_LOBBY_POS[index], list(initial_dict.keys())[index]))
            else:
                self.player_list[index].add(Player_line_name(macros.LIST_PLAYER_LOBBY_POS[index]))
                self.player_list[index].add(Player_line_color(macros.LIST_PLAYER_LOBBY_POS[index]))
            self.player_list[index].draw(screen)
            pg.draw.rect(screen, "gray65", list(self.player_list[index])[1].rect, 2)
    def update_lobby(self, new_dict):
        self.dict_players = new_dict
        for index in range(10):
            if index >= len(new_dict): break
            list(self.player_list[index])[0].update(list(new_dict.values())[index])
            list(self.player_list[index])[1].update(list(new_dict.keys())[index])
            self.player_list[index].draw(screen)
            pg.draw.rect(screen, "gray65", list(self.player_list[index])[1].rect, 2) 

class Back_ground(pg.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image =  pg.Surface((800, 400)).fill("black")
        self.rect = self.image

class Track(pg.sprite.Sprite):
    def __init__(self, track_num, color):
        super().__init__()
        self.base_image = pg.transform.scale(pg.image.load(macros.TRACKS[track_num]["dir"]).convert_alpha(), (10000, 6253))  # (4000, 2250))
        coll_img = pg.transform.scale(pg.image.load(macros.TRACKS[track_num]["collision"]).convert_alpha(), (10000, 6253))
        self.base_mask = pg.mask.from_surface(coll_img)
        self.image = self.base_image
        self.rect:  pg.Rect  # (1800, -1500))
        self.vect_player_pos = pg.math.Vector2(macros.TRACKS[track_num][color])
        self.vect_player = pg.math.Vector2(0,0)
        self.vect_player_norm = pg.math.Vector2(macros.TRACKS[track_num]["direction"])
        self.rotation_p = float(0)
        self.speed = float(0)
        self.degree = self.vect_player_norm.angle_to((0,1))
        self.traslation = pg.math.Vector2(0,0) 
        global main_player_packet
        main_player_packet = [self.vect_player_pos, self.speed, self.rotation_p, [False, False, False, False],  self.vect_player_norm, self.degree]
        print("track init")
    def check_collisions(self, interval):
        global collision_to_main
        for i in p6_collision_list:
            if self.base_mask.get_at(self.vect_player_pos + i):
                self.speed *= GameParams.COLLISION_SLOWDOWN_SCALAR
                self.traslation -= i*(max(abs(self.speed),min(self.traslation.magnitude(), 0.3)))*GameParams.COLLISION_BOUNCE_SCALAR
        if collision_to_main:
            self.traslation += collision_to_main
            self.speed *= GameParams.COLLISION_SLOWDOWN_SCALAR
            collision_to_main = pg.math.Vector2(0,0)
        if self.traslation:
            self.vect_player_pos += self.traslation
            self.traslation -= self.traslation*interval/250
        return          
    def update(self, w = False, a = False, s = False, d = False, interval = 0):
        if self.rotation_p > 0: self.rotation_p = max(self.rotation_p - GameParams.STEERING_REDUCTION*interval, 0)
        elif self.rotation_p < 0: self.rotation_p = min(self.rotation_p + GameParams.STEERING_REDUCTION*interval, 0)
        if self.speed > 0: self.speed = max(self.speed - GameParams.SPEED_REDUCTION*interval, 0) 
        elif self.speed < 0: self.speed = min(self.speed + GameParams.SPEED_REDUCTION*interval, 0)
        if a: self.rotation_p = min(self.rotation_p + GameParams.STEERING*interval, GameParams.MAX_ROTATION)
        if d: self.rotation_p = max(self.rotation_p - GameParams.STEERING*interval, -GameParams.MAX_ROTATION)
        if w: self.speed = min(self.speed + GameParams.SPEED_FORWARD*interval, GameParams.MAX_SPEED_FORWARD)
        if s: self.speed = max(self.speed - GameParams.SPEED_BACKWARD*interval, -GameParams.MAX_SPEED_BACKWARD)
        rotation = self.rotation_p*0.09*interval*(-pow((abs(self.speed) - 0.33) / 0.33, 2) + 1)
        if self.speed < 0: rotation = -rotation
        self.vect_player_norm = self.vect_player_norm.rotate(-rotation)
        self.vect_player = self.vect_player_norm.copy()
        self.vect_player.scale_to_length(self.speed*interval)
        self.degree -= rotation

        self.vect_player_pos += self.vect_player
        
        self.image = pg.transform.rotate(self.base_image.subsurface(self.vect_player_pos + player_position_center_surface,(1221, 1221)), self.degree)
        self.check_collisions(interval)
        global main_player_packet
        main_player_packet = [self.vect_player_pos, self.speed, self.rotation_p, [w, a, s, d], self.vect_player_norm, self.degree]
        self.rect = self.image.get_rect(center = player_position)

        return 

class Main_player(pg.sprite.Sprite):
    def __init__(self, color):
        super().__init__()
        self.image = pg.transform.scale(pg.image.load(macros.DICT_CARS[color]).convert_alpha(), macros.CAR_DIMENSIONS)
        self.rect = self.image.get_rect(center = (500, 400))
    # def update(self):
    #     #add animations

class Main_player_pred():
    def __init__(self, track_num, color):
        self.last_w = False
        self.last_a = False
        self.last_s = False
        self.last_d = False
        self.colr = color
        self.base_mask = list(track)[0].base_mask  #pg.mask.from_surface(self.base_image)
        self.vect_player_pos = pg.math.Vector2(macros.TRACKS[track_num][color])
        self.vect_player = pg.math.Vector2(0,0)
        self.vect_player_norm = pg.math.Vector2(macros.TRACKS[track_num]["direction"])
        self.rotation_p = float(0)
        self.speed = float(0)
        self.degree = self.vect_player_norm.angle_to((0,1))
        self.traslation = pg.math.Vector2(0,0)
    
    def update(self, interval):
        if self.rotation_p > 0: self.rotation_p = max(self.rotation_p - GameParams.STEERING_REDUCTION*interval, 0)
        elif self.rotation_p < 0: self.rotation_p = min(self.rotation_p + GameParams.STEERING_REDUCTION*interval, 0)
        if self.speed > 0: self.speed = max(self.speed - GameParams.SPEED_REDUCTION*interval, 0) 
        elif self.speed < 0: self.speed = min(self.speed + GameParams.SPEED_REDUCTION*interval, 0)
        if self.last_a: self.rotation_p = min(self.rotation_p + GameParams.STEERING*interval, GameParams.MAX_ROTATION)
        if self.last_d: self.rotation_p = max(self.rotation_p - GameParams.STEERING*interval, -GameParams.MAX_ROTATION)
        if self.last_w: self.speed = min(self.speed + GameParams.SPEED_FORWARD*interval, GameParams.MAX_SPEED_FORWARD)
        if self.last_s: self.speed = max(self.speed - GameParams.SPEED_BACKWARD*interval, -GameParams.MAX_SPEED_BACKWARD)
        rotation = self.rotation_p*0.09*interval*(-pow((abs(self.speed) - 0.33) / 0.33, 2) + 1)
        if self.speed < 0: rotation = -rotation
        self.vect_player_norm = self.vect_player_norm.rotate(-rotation)
        # print(self.vect_player_norm)
        self.vect_player = self.vect_player_norm.copy()
        self.vect_player.scale_to_length(self.speed*interval)
        self.degree -= rotation





        self.vect_player_pos += self.vect_player
        if game_state == 3 and (self.vect_player_pos - main_player_packet[0]).magnitude() > 5 or abs(self.degree - main_player_packet[5]) > 5:
            # print("in if")
            Thread(target = send_update, args = (self.colr,), daemon = True).start()  
            self.vect_player_pos = main_player_packet[0].copy()
            self.speed = main_player_packet[1]
            self.rotation_p = main_player_packet[2]
            temp_list = main_player_packet[3]
            self.vect_player_norm = main_player_packet[4].copy()
            self.degree = main_player_packet[5]#[elem for elem in main_player_packet]
            self.last_w, self.last_a, self.last_s, self.last_d = temp_list
        return
    def draw(self, bo):
        return

class Player(pg.sprite.Sprite):
    def __init__(self,track_num, color):
        super().__init__()
        self.colr = color
        self.base_image = pg.transform.scale(pg.image.load(macros.DICT_CARS[self.colr]).convert_alpha(), macros.CAR_DIMENSIONS)
        self.image = self.base_image
        self.vect_player_pos = pg.math.Vector2(macros.TRACKS[track_num][self.colr])
        print(main_player_packet)
        self.rect = self.image.get_rect(center = (self.vect_player_pos - main_player_packet[0]).rotate(- main_player_packet[5]) + (500, 400))
        self.vect_player_norm = pg.math.Vector2(macros.TRACKS[track_num]["direction"])
        self.degree = pg.math.Vector2(0,1).angle_to(macros.TRACKS[track_num]["direction"])
        self.vect_player: pg.math.Vector2
        self.last_buttons = [False, False, False, False]
        self.rotation_p = 0
        self.speed = 0
        self.traslation = pg.math.Vector2(0,0)
        self.base_mask = list(track)[0].base_mask  #pg.mask.from_surface(self.base_image)
        self.smoothing = False
        self.smooth_player_pos = pg.math.Vector2(0,0)
        self.smooth_interval = 0
    def check_collisions(self, interval):
        for i in p6_collision_list:
            if self.base_mask.get_at(self.vect_player_pos + i):
                self.speed *= GameParams.COLLISION_SLOWDOWN_SCALAR
                self.traslation -= i*(max(abs(self.speed),min(self.traslation.magnitude(), 0.3)))*GameParams.COLLISION_BOUNCE_SCALAR
        global collision_to_main
        vect_distance = self.vect_player_pos - main_player_packet[0]
        # print(type(vect_distance))
        if  vect_distance.magnitude() <= 70:
            # print(type(vect_distance))
            vect_distance.scale_to_length(max(abs(self.speed)*12, 5))
            # print(type(vect_bounce))
            # print(type(collision_to_main))
            collision_to_main -= vect_distance
            self.traslation += vect_distance
            self.speed *= GameParams.COLLISION_SLOWDOWN_SCALAR
        for col in dict_players_pos:
            if col == self.colr: 
                continue
            vect_distance = self.vect_player_pos - dict_players_pos[col]
            if vect_distance.magnitude() <= 70:
                self.traslation += vect_distance.scale_to_length(max(abs(self.speed)*12, 5))
                self.speed *= GameParams.COLLISION_SLOWDOWN_SCALAR
        if self.traslation:
            self.vect_player_pos += self.traslation
            self.traslation -= self.traslation*interval/250
        return          
    def smooth(self, interval):
        # print(self.vect_player_pos, self.smooth_player_pos, self.degree, self.smooth_rotation)
        self.smooth_interval -= interval
        if self.smooth_interval <= 0:
            interval += self.smooth_interval
            self.smoothing = False
        if self.smooth_rotation: self.degree += self.smooth_rotation*interval/500
        if self.smooth_player_pos: self.vect_player_pos += self.smooth_player_pos*interval/500
        if self.smooth_rotation == 0 and self.smooth_player_pos.magnitude() == 0:
            self.smoothing = False 

    def update(self, interval):
        if dict_updates[self.colr]:
            pack = dict_updates[self.colr]
            new_vect_player_pos = pack[0].copy()
            new_speed = pack[1]
            new_rotation_p = pack[2]
            self.last_buttons = pack[3]
            new_vect_player_norm = pack[4].copy()
            new_degree = -pack[5]
            time_sent = pack[6]
            interval_from_sent = ((time_ns()-start_time)/1000000) - time_sent 
            # if interval_from_sent < 500:
            #     interval_from_sent = max (0, interval_from_sent - 200)
            if new_rotation_p > 0: self.rotation_p = max(new_rotation_p - GameParams.STEERING_REDUCTION*interval_from_sent, 0)
            elif new_rotation_p < 0: self.rotation_p = min(new_rotation_p + GameParams.STEERING_REDUCTION*interval_from_sent, 0)
            if new_speed > 0: self.speed = max(new_speed - GameParams.SPEED_REDUCTION*interval_from_sent, 0) 
            elif new_speed < 0: self.speed = min(new_speed + GameParams.SPEED_REDUCTION*interval_from_sent, 0)
            if self.last_buttons[1]: self.rotation_p = min(self.rotation_p + GameParams.STEERING*interval_from_sent, GameParams.MAX_ROTATION)
            if self.last_buttons[3]: self.rotation_p = max(self.rotation_p - GameParams.STEERING*interval_from_sent, -GameParams.MAX_ROTATION)
            if self.last_buttons[0]: self.speed = min(self.speed + GameParams.SPEED_FORWARD*interval_from_sent, GameParams.MAX_SPEED_FORWARD)
            if self.last_buttons[2]: self.speed = max(self.speed - GameParams.SPEED_BACKWARD*interval_from_sent, -GameParams.MAX_SPEED_BACKWARD)
            # print("speed",self.speed)

            self.smooth_rotation = self.rotation_p*0.09*interval_from_sent*(-pow((abs(self.speed) - 0.33) / 0.33, 2) + 1)
            if self.speed < 0: self.smooth_rotation = -self.smooth_rotation
            self.vect_player_norm = new_vect_player_norm.copy()
            self.vect_player_norm = self.vect_player_norm.rotate(-self.smooth_rotation)
            # print("norm2", self.vect_player_norm)
            self.smooth_rotation =  new_degree - self.degree
            # print("vect_p", self.vect_player)
            self.vect_player = self.vect_player_norm.copy()
            # print("vect_p", self.vect_player)
            # print("*",self.speed*interval_from_sent)
            self.vect_player.scale_to_length(self.speed*interval_from_sent)
            # print("vect_p", self.vect_player)

            # # self.degree -= rotation
            # self.check_collisions(interval)
            self.smooth_player_pos = new_vect_player_pos - self.vect_player_pos 
            # print("smooth pos: ", self.smooth_player_pos, "smooth rot:", self.smooth_rotation)
            self.vect_player_pos += self.vect_player
            # print("vect_pla", self.vect_player)
            # print("smooth pos: ", self.smooth_player_pos, "smooth rot:", self.smooth_rotation)
            self.smoothing = True
            dict_updates[self.colr] = None 
            self.smooth_interval = 500
            self.smooth(interval)
            if abs((self.vect_player_pos - main_player_packet[0]).magnitude()) <= 650:
                self.image = pg.transform.rotate(self.base_image, main_player_packet[5] + self.degree)
                self.rect = self.image.get_rect(center = (self.vect_player_pos - main_player_packet[0]).rotate(-main_player_packet[5]) + (500, 400))
            return
        if self.smoothing: self.smooth(interval)
        if self.rotation_p > 0: self.rotation_p = max(self.rotation_p - GameParams.STEERING_REDUCTION*interval, 0)
        elif self.rotation_p < 0: self.rotation_p = min(self.rotation_p + GameParams.STEERING_REDUCTION*interval, 0)
        if self.speed > 0: self.speed = max(self.speed - GameParams.SPEED_REDUCTION*interval, 0) 
        elif self.speed < 0: self.speed = min(self.speed + GameParams.SPEED_REDUCTION*interval, 0)
        if self.last_buttons[1]: self.rotation_p = min(self.rotation_p + GameParams.STEERING*interval, GameParams.MAX_ROTATION)
        if self.last_buttons[3]: self.rotation_p = max(self.rotation_p - GameParams.STEERING*interval, -GameParams.MAX_ROTATION)
        if self.last_buttons[0]: self.speed = min(self.speed + GameParams.SPEED_FORWARD*interval, GameParams.MAX_SPEED_FORWARD)
        if self.last_buttons[2]: self.speed = max(self.speed - GameParams.SPEED_BACKWARD*interval, -GameParams.MAX_SPEED_BACKWARD)
        rotation = self.rotation_p*0.09*interval*(-pow((abs(self.speed) - 0.33) / 0.33, 2) + 1)
        if self.speed < 0: rotation = -rotation
        self.vect_player_norm = self.vect_player_norm.rotate(-rotation)
        self.vect_player = self.vect_player_norm.copy()
        self.vect_player.scale_to_length(self.speed*interval)
        self.degree += rotation
        self.check_collisions(interval)
        self.vect_player_pos += self.vect_player
        dict_players_pos[self.colr] = self.vect_player_pos
        if abs((self.vect_player_pos - main_player_packet[0]).magnitude()) <= 650:
            self.image = pg.transform.rotate(self.base_image, main_player_packet[5] + self.degree)
            self.rect = self.image.get_rect(center = (self.vect_player_pos - main_player_packet[0]).rotate(-main_player_packet[5]) + (500, 400))
        return


# tobedeleted
test_bg_rect = pg.Rect((0,0), (1000, 700))

#----------Functions:

def mod2_div(bitarr, poly):
    poly = bitarray(poly)
    for x in range(len(poly)):
        if bitarr[x] == poly[x]:
            bitarr[x] = False
        else:
            bitarr[x] = True
    return bitarr

def crc_division(message, poly):
    bit_message = bitarray()
    bit_message.frombytes(message)
    max_bit_division = len(bit_message)-33
    for i in range(max_bit_division):
        if bit_message[i] == True:
            bit_message[i:i + 33] = mod2_div(bit_message[i:i + 33], poly)
    return bit_message[max_bit_division + 1:]

updt = "updt".encode("utf-8")

def send_update(colr):
    pack = main_player_packet
    pack.append(int((time_ns() - start_time)/1000000))
    bytesOUT = updt + pickle.dumps(pack)
    gameplay_connection_to_server[0].put(bytesOUT)
    # print("updt sent")
    return
    

def process_updt(colr, bytesIN):
    dict_updates[colr] = pickle.loads(bytesIN)
    return

def gameplay_recv(gameplay_hostport, gameplay_sock):
    ackn = "ackn".encode("utf-8")
    updt = "updt".encode("utf-8")
    kill = "kill".encode("utf-8")
    while game_state > 1:
        bytesIN = gameplay_sock.recvfrom(4096)[0]
        if bytesIN[4:8] == updt:
            bytesOUT = bytesIN[:4] + ackn 
            colr = bytesIN[8:12].decode("utf-8")
            gameplay_connection_to_server[0].put(bytesOUT)
            print("to_process")
            process_updt(colr, bytesIN[12:])
                
        if bytesIN[4:8] == ackn:
            gameplay_connection_to_server[1].append(bytesIN[4:])

def retransmission(bytesOUT, seq_bytes, gameplay_sock, gameplay_hostport):
    countdown = 10
    
    while countdown > 0:
        sleep(0.1)
        for elem in gameplay_connection_to_server[1]:
            if elem == seq_bytes: gameplay_connection_to_server[1].remove(elem)
            if gameplay_connection_to_server[2] > 0: gameplay_connection_to_server[2] -= 1
            return
        gameplay_sock.sendto(bytesOUT, gameplay_hostport)
        countdown -= 1
    gameplay_connection_to_server[2] += 1
    if gameplay_connection_to_server[2] >= 10:    #IMPLEMENT KILL
        connection_lost()
        return
    countdown = 5
    while countdown > 0:
        if seq_bytes in gameplay_connection_to_server[1]:
            gameplay_connection_to_server[1].remove(seq_bytes)
        sleep(0.5)
    
    return
        
def gameplay_send(gameplay_hostport, gameplay_sock):
    # list_seq_to_del = list()
    # Thread(target = clean_list, args = ())
    seq_num = 0
    while game_state > 1:
        # print("hostport, sock", gameplay_hostport, gameplay_sock)
        seq_bytes = seq_num.to_bytes(4, "big")
        temp = gameplay_connection_to_server[0].get()
        if temp[4:] == Comms.ACKNOWLEDGMENT:
            gameplay_sock.sendto(temp, gameplay_hostport)
            continue
        bytesOUT = seq_bytes + temp
        gameplay_sock.sendto(bytesOUT, gameplay_hostport)
        # print("sent")
        Thread(target = retransmission, args = (bytesOUT, seq_bytes, gameplay_sock, gameplay_hostport), daemon = True).start()

def check_cross():
    cross = 3
    while 2 <= game_state <= 3:
            sleep(0.001)
            if  cross == 3 and main_player_packet[0][0] > 5000  and main_player_packet[0][1] > 3000:
                print("cross1")
                connection_to_server["sending_queue"].put(Comms.CROSS + cross.to_bytes(1, "big")+ pickle.dumps(main_player_packet[0]))  
                cross -= 1

            if cross == 2 and  main_player_packet[0][0] < 5000 and main_player_packet[0][1] < 3500:
                print("cross2")
                connection_to_server["sending_queue"].put(Comms.CROSS + cross.to_bytes(1, "big") + pickle.dumps(main_player_packet[0]))
                cross -= 1

            if cross == 1 and main_player_packet[0][0] > 1800 and main_player_packet[0][0] < 1840 and main_player_packet[0][1] > 3500:
                print("cross3")
                connection_to_server["sending_queue"].put(Comms.CROSS + cross.to_bytes(1, "big") + pickle.dumps(main_player_packet[0]))
                cross = 3

def keep_updated():
    global game_state
    while game_state > 1:
        sleep(0.5)
        # print("up")
        connection_to_server["sending_queue"].put(Comms.POSITION + pickle.dumps(main_player_packet[0]))
        if not queue_recv.empty():
            messageIN = queue_recv.get()
            if messageIN[:4] == Comms.KILL:

                colr = messageIN[4:8].decode()
                if macros.DICT_EXT[colr] in players_sprites:
                    players_sprites.pop(macros.DICT_EXTEN[colr])
                if colr in dict_players_pos:
                    dict_players_pos.pop(colr)
            if messageIN[:4] == Comms.FINAL_PLACE:
                
                global placement
                placement = int(messageIN[4])
                game_state = Game_states.FINISHED
                print("FINAL POSITION:", placement)
                group_pop_up.add(Text_pop_up("You arrived ", (500, 200), "white", None, 50, 1000000000, 10000000000, None))
                group_pop_up.add(Text_pop_up(str(placement-48), (500, 300), "white", None, 80, 1000000000, 10000000000, None))
                continue
            if game_state == Game_states.FINISHED and messageIN == Comms.RACE_END:
                for sprite in group_pop_up: sprite.kill()
                to_lobby()
                return


def to_game_active(track_num, dict_lobby):
    radius_collision = (macros.CAR_DIMENSIONS[0] + macros.CAR_DIMENSIONS[1])/5
    global p6_collision_list
    p6_collision_list = [pg.math.Vector2(-radius_collision, -radius_collision)*math.sqrt(2)/2, 
                         pg.math.Vector2(0, radius_collision),
                         pg.math.Vector2(radius_collision, -radius_collision)*math.sqrt(2)/2,
                         pg.math.Vector2(radius_collision, 0),
                         pg.math.Vector2(radius_collision, radius_collision)*math.sqrt(2)/2,
                         pg.math.Vector2(0, radius_collision),
                         pg.math.Vector2(-radius_collision, radius_collision)*math.sqrt(2)/2,
                         pg.math.Vector2(-radius_collision, 0)
                         ]
    
    # while not gameplay_hostport:
    #     sleep(0.01)
    #     continue
    
    print("3")
    global main_player_packet
    main_player_packet = []

    global collision_to_main
    collision_to_main = pg.math.Vector2(0,0)

    global dict_players_pos
    dict_players_pos = dict()
    print("4")
    global track
    track = pg.sprite.Group()
    global main_player
    main_player = pg.sprite.GroupSingle()
    for col in dict_lobby:
        if dict_lobby[col] == nickname:
            track.add(Track(track_num, col))
            main_player.add(Main_player(col))
        else:
            dict_players_pos[col] = (pg.math.Vector2(macros.TRACKS[track_num][col]))
        

    
    global dict_updates
    dict_updates = dict()
    global players_sprites
    players_sprites = dict()

    print(dict_lobby)

    for col in dict_lobby:
        dict_updates[col] = None
        if dict_lobby[col] == nickname: 
            players_sprites[col] = Main_player_pred(track_num, col)
            print("init")
        else: 
            players_sprites[col] = pg.sprite.GroupSingle()
            players_sprites[col].add(Player(track_num, col))
    # print(players_sprites)

    # sleep(30)

    global game_state
    game_state = 2
    Thread(target = keep_updated, daemon = True).start()
    Thread(target = check_cross, daemon = True).start()
    
    return pg.time.get_ticks() 

def to_lobby():
    global game_state
    game_state = Game_states.LOBBY

    global sock
    if not sock: 
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', random.randint(10000, 50000)))
        print(sock.getsockname())

    global connection_to_server
    if "connection_to_server" not in globals():
        connection_to_server = {"seq" : 1, "ack" : 1, "sending_queue": Queue(), "free_to_send": True}
        Thread(target = sending_function_ack, daemon = True).start()
        Thread(target = receiving_function_ack, daemon = True).start()
        messageOUT = Comms.NAME + nickname.encode()
        connection_to_server["sending_queue"].put(messageOUT)
    if "track" in globals(): track.empty()

    if "players_sprites" in globals():
        for sprite in players_sprites: 
            try: sprite.empty()
            except: pass
    if "main_player" in globals(): main_player.empty()
    if "dict_players_pos" in globals():
        global dict_players_pos
        del dict_players_pos
    if "collision_to_main" in globals():
        global collision_to_main
        del collision_to_main
    
    if "main_player_packet" in globals():
        global main_player_packet
        del main_player_packet
    if "p6_collision_list" in globals():
        global p6_collision_list
        del p6_collision_list
    if "dict_updates" in globals():
        global dict_updates
        del dict_updates
    if "title_group" in globals(): title_group.empty()
    if "rect_text_box" in globals():
        global rect_text_box
        del rect_text_box
    if "text_box" in globals():
        text_box.empty()    
    return 

def connection_lost():
    print("connection lost")
    to_menu()
    return

def receiving_function_ack():
    sock.settimeout(5)
    while game_state > 0:
        print("ack: ", connection_to_server["ack"])
        try:
            bytes_recv = sock.recvfrom(4096)[0]
        except:
            continue
        if  ba2int(crc_division(bytes_recv, macros.POLYNOM)) == 0:
            if len(bytes_recv) == 8:
                if int.from_bytes(bytes_recv[:-4], "big") == connection_to_server["seq"] + 1:
                    connection_to_server["seq"] += 1
                    connection_to_server["free_to_send"] = True
                continue
            if int.from_bytes(bytes_recv[:4], "big") == connection_to_server["ack"]:
                queue_recv.put(bytes_recv[4:-4])
                connection_to_server["ack"] += 1
            sock.sendto(connection_to_server["ack"].to_bytes(4, "big") + crc_division(connection_to_server["ack"].to_bytes(4, "big") + b'\x00\x00\x00\x00', macros.POLYNOM), hostport)

def sending_function_ack():
    messageOUT = ""
    counter_sending = 0
    while game_state > 0:
        print(sock.getsockname())
        if not connection_to_server["free_to_send"]:
            if counter_sending >= 10:
                connection_lost()
            if type(messageOUT) == str:
                bytesOUT = connection_to_server["seq"].to_bytes(4, "big") + messageOUT.encode("utf-8") + crc_division(connection_to_server["seq"].to_bytes(4, "big") + messageOUT.encode("utf-8") + b'\x00\x00\x00\x00', macros.POLYNOM)
            elif type(messageOUT) == bytes:
                bytesOUT = connection_to_server["seq"].to_bytes(4, "big") + messageOUT + crc_division(connection_to_server["seq"].to_bytes(4, "big") + messageOUT + b'\x00\x00\x00\x00', macros.POLYNOM)

            sock.sendto(bytesOUT, hostport)
            counter_sending += 1
            sleep(0.5)
        else:
            counter_sending = 0
            messageOUT = connection_to_server["sending_queue"].get()
            if type(messageOUT) == str:
                bytesOUT = connection_to_server["seq"].to_bytes(4, "big") + messageOUT.encode("utf-8") + crc_division(connection_to_server["seq"].to_bytes(4, "big") + messageOUT.encode("utf-8") + b'\x00\x00\x00\x00', macros.POLYNOM)
            elif type(messageOUT) == bytes:
                bytesOUT = connection_to_server["seq"].to_bytes(4, "big") + messageOUT + crc_division(connection_to_server["seq"].to_bytes(4, "big") + messageOUT + b'\x00\x00\x00\x00', macros.POLYNOM)
            sock.sendto(bytesOUT, hostport)
            print("seq: ", connection_to_server["seq"])
            connection_to_server["free_to_send"] = False
            sleep(0.3)
     
def to_menu():
    if "kill_ack" in globals(): kill_ack.set()
    global game_state
    game_state = 0

    global sock
    if sock: 
        sock.close()
        sock = None
    global connection_to_server
    if "connection_to_server" in globals():
        connection_to_server["sending_queue"].put(Comms.LEAVE)
        counter = 0
        while counter < 5:
            counter += 1
            sleep(0.5)
        del connection_to_server
    if "players_sprites" in globals():
        for sprite in players_sprites:
            try: sprite.empty()
            except: del sprite
    if "main_player" in globals(): main_player.empty()
    if "track" in globals(): track.empty()
    if "dict_players_pos" in globals():
        global dict_players_pos
        del dict_players_pos
    if "collision_to_main" in globals():
        global collision_to_main
        del collision_to_main
    if "main_player_packet" in globals():
        global main_player_packet
        del main_player_packet
    if "p6_collision_list" in globals():
        global p6_collision_list
        del p6_collision_list
    if "dict_updates" in globals():
        global dict_updates
        del dict_updates
    global text_box
    text_box = pg.sprite.GroupSingle()
    text_box.add(Text_box())

    global title_group
    title_group = pg.sprite.Group()
    title_group.add(Sprite_insert(), Text_box(), Sprite_insert(), Title(), Enter_img())
    global rect_text_box
    rect_text_box = pg.Rect((0,0), (400, 80))
    rect_text_box.center = (500, 400)
    return 

def is_in_queue(key_element, queue):
    try:
        for index in range(queue.qsize()):
            if key_element == queue.queue(index):
                return True
        return False
    except: return False




 #implement


#possibly unbound tua madre
# lobby = Lobby_status(dict)
# connection_to_server = dict()
# track = pg.sprite.GroupSingle()
# main_player = pg.sprite.GroupSingle()
# players_sprites = dict()
# time_0 = 0
#--------------------------

nickname = ""
gameplay_hostport = None
start_time = None
group_pop_up = pg.sprite.Group()
lobby = Lobby_status({})
to_menu()
while True:
    screen.fill("black")
    match game_state:
        case Game_states.MENU:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    exit()

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_BACKSPACE: 
                        if len(nickname) >= 1: nickname = nickname[:-1]
                    elif event.key == pg.K_RETURN: to_lobby()
                    elif len(nickname) <= 12 and "text_box" in globals(): 
                        nickname += event.unicode
                    if "text_box" in globals(): text_box.update()
            text_box.draw(screen)
            title_group.draw(screen)
            if "rect_text_box" in globals(): pg.draw.rect(screen, "gray65", rect_text_box, 2)



        case Game_states.LOBBY:
            
            if not queue_recv.empty():
                messageIN = queue_recv.get()
                if messageIN == Comms.FULL:
                    to_menu()

                if messageIN == Comms.LEADER:
                    print("leader")
                
                if messageIN[:4] == Comms.TO_RACE:
                    print("starting")
                    wasd = [False, False, False, False]
                    temp = messageIN.decode()
                    track_num = int(temp[4])
                    print("tracknum: ", track_num)
                    to_game_active(track_num, lobby.dict_players)
                
                if messageIN == Comms.USED:
                    to_menu()
                
                if messageIN[:4] == Comms.STATUS:
                    print("dict_update")

                    print(pickle.loads(messageIN[4:]))

                    lobby.update_lobby(pickle.loads(messageIN[4:]))

            else:
                for event in pg.event.get():
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN:
                            print("sending_start")
                            messageOUT = Comms.START
                            if not is_in_queue(messageOUT, connection_to_server["sending_queue"]):
                                connection_to_server["sending_queue"].put(messageOUT)
                    if event.type == pg.QUIT:
                        connection_to_server["sending_queue"].put(Comms.LEAVE)
                        timeout_counter = 0
                        while not connection_to_server["free_to_send"]:
                            timeout_counter += 0.5
                            if timeout_counter >= 8: break
                            sleep(0.5)
                        pg.quit()
                        exit()

            
            if lobby:
                for sprite in lobby.player_list: sprite.draw(screen)
                
        case Game_states.COUNTDOWN:
            try:
                track.update()
                track.draw(screen)
                main_player.draw(screen)
            
                for color in players_sprites:
                    Thread(target = players_sprites[color].update, args = [0], daemon = True).start()
                    players_sprites[color].draw(screen)
            except: print("blit err")
            
            if start_time and time_ns() >= start_time:
                time_0 = pg.time.get_ticks()
                game_state = Game_states.RACE
            
            if not queue_recv.empty():
                messageIN = queue_recv.get()
                if messageIN[:5] == "port:".encode("utf-8"):
                    gameplay_hostport = ((hostport[0], int(messageIN[5:].decode("utf-8"))))
                    gameplay_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    gameplay_sock.bind((hostport[0], 0))
                    
                    connection_to_server["sending_queue"].put("port:" + str(gameplay_sock.getsockname()[1]))

                    global gameplay_connection_to_server
                    gameplay_connection_to_server = [Queue(), list(), int(0)]
                    Thread(target = gameplay_recv, args = (gameplay_hostport, gameplay_sock), daemon = True).start()
                    Thread(target = gameplay_send, args = (gameplay_hostport, gameplay_sock), daemon = True).start()

                if messageIN[:4] == Comms.START_TIME:
                    start_time = int.from_bytes(messageIN[4:], "big")
                    group_pop_up.add(Text_pop_up("3", (500, 200), "white", None, 50, 1000000000, 300000000, start_time - 3000000000))
                    group_pop_up.add(Text_pop_up("2", (500, 200), "white", None, 50, 1000000000, 300000000, start_time - 2000000000))
                    group_pop_up.add(Text_pop_up("1", (500, 200), "white", None, 50, 1000000000, 300000000, start_time - 1000000000))
                    group_pop_up.add(Text_pop_up("GO", (500, 200), "white", None, 50, 1000000000, 300000000, start_time - 50000000))
                    print("start time:", start_time)
                

        case Game_states.RACE:
            for event in pg.event.get():
                if event.type == pg.KEYDOWN:
                    match event.key:
                        case pg.K_w:
                            wasd[0] = True
                        case pg.K_a:
                            wasd[1] = True
                        case pg.K_s:
                            wasd[2] = True
                        case pg.K_d:
                            wasd[3] = True
                if event.type == pg.KEYUP:
                    match event.key:
                        case pg.K_w:
                            wasd[0] = False
                        case pg.K_a:
                            wasd[1] = False
                        case pg.K_s:
                            wasd[2] = False
                        case pg.K_d:
                            wasd[3] = False
                if event.type == pg.QUIT:
                    connection_to_server["sending_queue"].put(Comms.LEAVE)
                    pg.quit()
                    exit()
            
            time_1 = pg.time.get_ticks()
            time_interval = time_1 - time_0 
            time_0 = time_1 
            try:
                degree = track.update(wasd[0], wasd[1], wasd[2], wasd[3], time_interval)
                track.draw(screen)
                main_player.draw(screen)
                for color in players_sprites:
                    Thread(target = players_sprites[color].update, args = (time_interval,), daemon = True).start()
                    players_sprites[color].draw(screen)
            except: print("blit err")


        case Game_states.FINISHED:
            
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    connection_to_server["sending_queue"].put(Comms.LEAVE)
                    pg.quit()
                    exit()

            if not queue_recv.empty():
                messageIN = queue_recv.get()
                print(messageIN)
                if messageIN[:4] == Comms.RACE_END:
                    to_lobby()
                    continue


            time_1 = pg.time.get_ticks()
            time_interval = time_1 - time_0 
            time_0 = time_1 
            try:
                track.draw(screen)
                for color in players_sprites: 
                    Thread(target = players_sprites[color].update, args = (time_interval,), daemon = True).start()
                    players_sprites[color].draw(screen)
            except: print("blit err")
    
    
    try:
        if len(group_pop_up.sprites()):
            group_pop_up.update()
            group_pop_up.draw(screen)
        
        pg.display.update()
    except pg.error as e: print("blit err")
    # print("fps: ",clock.get_fps())
    clock.tick(60)