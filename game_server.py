import socket
from threading import Thread
from threading import Event
from queue import Queue
import pickle
from bitarray import bitarray
from bitarray.util import ba2int
from time import sleep
from time import time_ns
from time import time
import random
import macros
from macros import Comms
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("localhost", 12345)) #add
SERVER_IP = "localhost"
# sock.bind(("", 12345)) #"217.117.226.147"
# print(socket.gethostbyname(socket.gethostname()))
dict_players = dict()
queue_recv = Queue()




def is_decodable(bytes):    
    try:
        bytes.decode("utf-8")
        return True
    except:
        return False

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

def get_all_ports():
    timeout = 50
    port_count = len(dict_players)
    while timeout:
        if not port_count: return
        sleep(0.2)
        timeout -= 1
        if queue_recv.empty(): continue 
        messageIN, hport = queue_recv.get()
        if messageIN[:4] == Comms.NAME:
            sock.sendto(b'\x00\x00\x00\x01' + Comms.FULL + bytes(crc_division(b'\x00\x00\x00\x01' + "full".encode("utf-8") + b'\x00\x00\x00\x00', macros.POLYNOM)), hport)
            continue
        if messageIN == Comms.LEAVE:
            dict_players[hport]["ded_sock"].close()
            remove_from_lobby(hport)
            continue
        if messageIN[:5] == "port:".encode():
            port_count -= 1
            print("port recv")
            dict_players[hport]["player_hport"] = (hport[0], int(messageIN[5:]))
    for hport in dict_players:
        if not dict_players[hport]["player_hport"]:
            dict_players[hport]["ded_sock"].close()
            remove_from_lobby(hport)
    return

def func_sending_ack():
    while True:
        try:
            for address in dict_players:
                if not dict_players[address]["free_to_send"]: 
                    sock.sendto(dict_players[address]["out"], address)
                    
                elif not dict_players[address]["sending_queue"].empty():
                    bytesOUT = dict_players[address]["sending_queue"].get()
                    # print(bytesOUT, dict_players[address]["seq"])
                    if type(bytesOUT) == str: bytesOUT = bytesOUT.encode("utf-8")
                    dict_players[address]["out"] = dict_players[address]["seq"].to_bytes(4, "big") + bytesOUT + crc_division(dict_players[address]["seq"].to_bytes(4, "big") + bytesOUT + b'\x00\x00\x00\x00', macros.POLYNOM) 
                    sock.sendto(dict_players[address]["out"], address)
                    dict_players[address]["free_to_send"] = False
            sleep(0.5)
        except:
            continue;
    
        

def is_pickle_bytes(bytes):
    try:
        pickle.loads(bytes)
        return True
    except: return False

def func_receiving_ack():
    while True:
        bytes_recv, address = sock.recvfrom(4096)
        # print(bytes_recv)
        if  ba2int(crc_division(bytes_recv, macros.POLYNOM)) == 0:
            if address in dict_players:
                if len(bytes_recv) == 8:
                    if int.from_bytes(bytes_recv[:4], "big") == dict_players[address]["seq"] + 1:
                        dict_players[address]["free_to_send"] = True
                        dict_players[address]["seq"] += 1
                    continue
                if int.from_bytes(bytes_recv[:4], "big") == dict_players[address]["ack"]:
                    if is_pickle_bytes(bytes_recv[8:-4]) or is_pickle_bytes(bytes_recv[9:-4]):  
                        queue_recv.put((bytes_recv[4:-4], address))
                    else:
                        queue_recv.put((bytes_recv[4:-4], address))
                    dict_players[address]["ack"] += 1
                sock.sendto(dict_players[address]["ack"].to_bytes(4, "big") + crc_division(dict_players[address]["ack"].to_bytes(4, "big") + b'\x00\x00\x00\x00', macros.POLYNOM), address)
            else:
                sock.sendto(b'\x00\x00\x00\x02' + bytes(crc_division(b'\x00\x00\x00\x02' + b'\x00\x00\x00\x00', macros.POLYNOM)), address)
                queue_recv.put((bytes_recv[4:-4], address))

#rcv  ":" not in messages
# "4bytes:updt:ms_from_start:data"
# "4bytes:ackn"
#snd        colors: redd, orng, prpl, yllw, blue, lblu, gren, blck, whte, gray
# "4bytes:updt:colo:ms_from_start(4bytes):data"
# "4bytes:ackn:"

# "strt:16bytes"

# "kill:colo"

def remove_from_lobby(address):
    queue_color.put(dict_players[address]["color"])
    if address in dict_lobby: dict_lobby.pop(dict_players[address]["color"])
    if address in dict_players and dict_players[address]["leader"]: 
        dict_players.pop(address)
        if len(dict_players):
            dict_players[list(dict_players.keys())[0]]["leader"] = True
            dict_players[list(dict_players.keys())[0]]["sending_queue"].put(Comms.LEADER)
    elif address in dict_players:
        dict_players.pop(address)
    broadcast_ack(Comms.STATUS + pickle.dumps(dict_lobby), address)
    return


def retransmission(bytesOUT, seq_bytes, colr, color_sock, address):
    countdown = 100
    while countdown > 0:
        sleep(0.01)
        for elem in dict_connection_threads[colr][1]:
            if elem == seq_bytes: dict_connection_threads[colr][1].remove(elem)
            if dict_connection_threads[colr][2] > 0: dict_connection_threads[colr][2] -= 1
            return
        color_sock.sendto(bytesOUT, address)
        countdown -= 1
    dict_connection_threads[colr][2] += 1
    if dict_connection_threads[colr][2] >= 10 and colr in dict_kill_player:
        dict_kill_player[colr].set()
        print("KILL(retransmission())\n")
    countdown = 5
    while countdown > 0:
        if seq_bytes in dict_connection_threads[colr][1]:
            dict_connection_threads[colr][1].remove(seq_bytes)
    
    return
        
def color_send(colr, address, color_sock):
    seq_num = 0
    while game_active:
        if colr in dict_kill_player and dict_kill_player[colr].is_set(): return

        seq_bytes = seq_num.to_bytes(4, "big")
        temp = dict_connection_threads[colr][0].get()
        if temp[4:] == Comms.ACKNOWLEDGMENT:
            color_sock.sendto(temp, address)
            continue
        bytesOUT = seq_bytes + temp
        color_sock.sendto(bytesOUT, address)
        Thread(target = retransmission, args = (bytesOUT, seq_bytes, colr, color_sock, address), daemon = True).start()
        
def color_recv(colr, address, color_sock):
    colr_bytes = colr.encode("utf-8")
    
    while game_active:
        try:
            if dict_kill_player[colr].is_set(): return
        except: return
        bytesIN = color_sock.recvfrom(4096)[0]
        if bytesIN[4:8] == Comms.UPDATE:
            dict_connection_threads[colr][0].put(bytesIN[:4] + Comms.ACKNOWLEDGMENT)
            bytesOUT = Comms.UPDATE + colr_bytes + bytesIN[8:] 
            for col in dict_connection_threads:
                if col != colr:    
                    dict_connection_threads[col][0].put(bytesOUT)
                
        if bytesIN[4:8] == Comms.ACKNOWLEDGMENT:
            dict_connection_threads[colr][1].append(bytesIN[:4])



def game_control():
    global dict_kill_player
    global dict_progress
    dict_progress = dict()
    queue_delete = Queue()
    for colr in dict_lobby:
        tm = time()
        dict_progress[colr] = {"cros": 3,
                               "lap": 1,
                               "last": None,
                               "time": tm
                               }
    position = 1
    # try:
    while True:
        sleep (0.05)
        for colr in dict_progress:
            if time() - dict_progress[colr]["time"] > 10:
                queue_delete.put(colr)
                print("QUEUE KILL(game_control()1\n")
                continue
        while not queue_delete.empty():
            colr = queue_delete.get()
            if colr in dict_kill_player: dict_kill_player[colr].set()
            dict_progress.pop(colr)


        if not queue_recv.empty():
            
            messageIN, hport = queue_recv.get()
            if messageIN == Comms.LEAVE:
                dict_kill_player[dict_players[hport]["color"]].set()
                continue
            if messageIN[:4] == Comms.NAME:
                sock.sendto(b'\x00\x00\x00\x01' + Comms.FULL + bytes(crc_division(b'\x00\x00\x00\x01' + "full".encode("utf-8") + b'\x00\x00\x00\x00', macros.POLYNOM)), hport)
                continue
            if hport in dict_players and messageIN[:4] == Comms.CROSS:
                colr = dict_players[hport]["color"]

                line = messageIN[4]
                if colr in dict_progress and line == dict_progress[colr]["cros"]: 
                    temp_pos = pickle.loads(messageIN[5:])
                    if colr in dict_progress and dict_progress[colr]["last"] and (time() - dict_progress[colr]["time"])*1200 + 1 < (temp_pos - dict_progress[colr]["last"]).magnitude():
                        queue_delete.put(colr)
                        print("QUEUE KILL(game_control()2\n")
                    dict_progress[colr]["last"] =  temp_pos
                    dict_progress[colr]["time"] = time()
                    dict_progress[colr]["cros"] -= 1
                    
                    if dict_progress[colr]["cros"] == 0:
                        dict_progress[colr]["cros"] = 3
                        dict_progress[colr]["lap"] -= 1
                        if dict_progress[colr]["lap"] == 0:
                            dict_players[hport]["sending_queue"].put("plce" + str(position))
                            position += 1
                print(dict_progress)
            elif hport in dict_players and messageIN[:4] == Comms.POSITION:
                colr = dict_players[hport]["color"]
                temp_pos = pickle.loads(messageIN[4:])
                # if  colr in dict_progress and dict_progress[colr]["last"] and (time() - dict_progress[colr]["time"])*1200 + 1 < (temp_pos - dict_progress[colr]["last"]).magnitude():
                #     queue_delete.put(colr)
                #     print("QUEUE KILL(game_control()3\n")
                #     continue
                dict_progress[colr]["last"] = pickle.loads(messageIN[4:])
                dict_progress[colr]["time"] = time()
            while not queue_delete.empty():
                colr = queue_delete.get()
                dict_kill_player[colr].set()
                dict_progress.pop(colr)

            n = 0
            for colr in dict_progress:
                if dict_progress[colr]["lap"] == 0: n += 1
            if n == len(dict_progress):
                broadcast_ack(Comms.RACE_END)
                global game_active
                game_active = False
                del dict_progress
                return
    # except Exception as e: print(e)

        
            



def race():
    global game_active
    game_active = True
    global dict_connection_threads
    dict_connection_threads = dict()

    if (macros.TRACK_TO_TEST):
        track_num = macros.TRACK_TO_TEST
    else:
        track_num = random.randint(1, len(macros.TRACKS))
    for address in dict_players:
        dict_players[address]["sending_queue"].put("torc" + str(track_num))
        dict_connection_threads[dict_players[address]["color"]] = [Queue(), list(), int(0)]
        if not dict_players[address]["ded_sock"]:
            color_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            color_socket.bind((SERVER_IP, 0))
            dedicated_port = color_socket.getsockname()[1]
            dict_players[address]["ded_port"] = dedicated_port
            dict_players[address]["ded_sock"] = color_socket
        else:
            dedicated_port = dict_players[address]["ded_port"]
        dict_players[address]["sending_queue"].put("port:" + str(dedicated_port))


    global dict_kill_player 
    dict_kill_player = dict()
    for address in dict_players:
        dict_kill_player[dict_players[address]["color"]] = Event()
    ready = False
    while not ready:
        for address in dict_players:
            if not dict_players[address]["free_to_send"]:
                ready = False
                break
            else: ready = True
    get_all_ports()
    for address in dict_players:
        dict_players[address]["thread_recv"]  = Thread(target = color_recv, args = (dict_players[address]["color"], dict_players[address]["player_hport"], dict_players[address]["ded_sock"]), daemon = True)
        dict_players[address]["thread_send"]  = Thread(target = color_send, args = (dict_players[address]["color"], dict_players[address]["player_hport"], dict_players[address]["ded_sock"]), daemon = True)
        dict_players[address]["thread_recv"].start()
        dict_players[address]["thread_send"].start()
    global start_time
    start_time = time_ns() + 5*pow(10, 9) 
    print("starttme:", start_time)
    broadcast_ack("strt".encode("utf-8") + start_time.to_bytes(16, "big"))

    Thread(target = kill_player, daemon = True).start()
    game_control()
    return

def kill_player():
        queue_kill = Queue()
        while game_active == True:
            if len(dict_kill_player):
                for col in dict_kill_player:
                    if dict_kill_player[col].is_set():
                        print("broadcast: " , ("kill" + col))
                        broadcast_ack(("kill" + col).encode("utf-8"))
                        sleep(0.2)
                        queue_kill.put(col)
                        print("kill: ", col)
                        for address in dict_players:
                            if dict_players[address]["color"] == macros.DICT_EXT[col]:
                                remove_from_lobby(address)
                                break
                while not queue_kill.empty(): dict_kill_player.pop(queue_kill.get())
            else: return
            sleep(2)
        return

def broadcast_ack(message_bytes, addr_excluded = None):
    for key in dict_players:
        if key == addr_excluded: continue
        dict_players[key]["sending_queue"].put(message_bytes)
    return

def lobby():

    while True:
        messageIN, address = queue_recv.get()
        print("---->address: ", address)
        print(messageIN, " ||| lobby")
        if messageIN[:4] == Comms.START and dict_players[address]["leader"]:
            race()
            continue
        if messageIN[:4] == Comms.NAME:
            print("new name")
            if address in dict_players.keys():
                print("---->ALREADY IN\n")
                dict_players[address]["sending_queue"].put(dict_players[address]["color"])
                if dict_players[address]["leader"] == True:
                    dict_players[address]["sending_queue"].put(Comms.LEADER)
                continue
            for addr in dict_players:
                if dict_players[addr]["nickname"] == messageIN[4:].decode():
                    print("---->USED\n")
                    sock.sendto(b'\x00\x00\x00\x01' + Comms.USED + bytes(crc_division(b'\x00\x00\x00\x01' + "used".encode("utf-8") + b'\x00\x00\x00\x00', macros.POLYNOM)), address)
                    continue
            if len(dict_players) >= 10:
                print("---->FULL\n")
                sock.sendto(b'\x00\x00\x00\x01' + Comms.FULL + bytes(crc_division(b'\x00\x00\x00\x01' + "full".encode("utf-8") + b'\x00\x00\x00\x00', macros.POLYNOM)), address)
                continue
            print("---->address before dict: ", address)
            dict_players[address] = {"seq" : 1, 
                                     "ack" : 2, 
                                     "sending_queue": Queue(), 
                                     "free_to_send": True, 
                                     "out": b'', 
                                     "nickname": messageIN[4:].decode(), 
                                     "leader": False, 
                                     "player_hport": None, 
                                     "ded_sock": None, 
                                     "ded_port": None}
            if len(dict_players) == 1:
                dict_players[address]["sending_queue"].put(Comms.LEADER)
                dict_players[address]["leader"] = True
            color = queue_color.get()
            dict_players[address]["color"] = color
            dict_lobby[color] = messageIN[4:].decode()
            broadcast_ack(Comms.STATUS + pickle.dumps(dict_lobby))

            print(dict_players)
            continue

        if messageIN[:4] == Comms.LEAVE: remove_from_lobby(address)
        
queue_color = Queue(10)
[queue_color.put(color) for color in macros.LIST_COLORS]
dict_lobby = dict()


thread_send = Thread(target = func_sending_ack, daemon = True)
thread_send.start()
thread_recv = Thread(target = func_receiving_ack, daemon = True)
thread_recv.start()



game_active = False
counter_player = 0

lobby()



