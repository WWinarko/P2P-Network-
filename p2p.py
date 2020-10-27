#!/usr/bin/env python3
import sys
import time
from socket import *
import threading
from peerNode import PeerNode

# Funtion fot receiving ping 
def ping_recv():
    global t_lock
    global pingSocket
    global peer

    print('Peer Initialized')

    while 1:
        message, clientAddress = pingSocket.recvfrom(2048)
        clientPort = int(clientAddress[1])
        clientNo = clientPort - 8000
        message = message.decode()
        #get lock as we might me accessing some shared data structures
        with t_lock:
            # If the message we receive is ping request then we send back response 
            if('Ping request' in message):
                serverMessage = "Request accepted"
                pingSocket.sendto(serverMessage.encode(), clientAddress)
                print(f"Ping request message received from Peer {clientNo}\n")
                peer.setPred(message, clientNo)
            # If the message is the response then we reset the pingSent count to 0 
            elif(message == 'Request accepted'):
                print(
                    f"Ping response received from Peer {clientNo}\n")
                peer.resetPingSent(clientNo)
            else:
                print(message)                            
            #notify the thread waiting
            t_lock.notify()

# Function to send ping every ping_interval to successors
def ping_send():
    global t_lock
    global pingSocket
    global peer

    while 1:
        #get lock
        with t_lock:
            first_suc = peer.succs[0]["id"] 
            second_suc = peer.succs[1]["id"] 
            # Check if first successor quit abruptly
            if  peer.checkTimeOut(0):                    
                request = str(first_suc) + " " + str(peer.id) + " First successor request"
                request_send(request, second_suc + 8000)
            # If not, send ping request to successors    
            else:
                message = str(first_suc) + " " + \
                    str(second_suc) + " " + "Ping request"
                pingSocket.sendto(message.encode(), ("localhost", first_suc + 8000))
                peer.succs[0]["pingSent"] += 1
                pingSocket.sendto(message.encode(), ("localhost",second_suc + 8000))
                peer.succs[1]["pingSent"] += 1
                print(
                f"Ping requests sent to Peers {first_suc} and {second_suc}\n")

            #notify other thread
            t_lock.notify()
        #sleep for ping interval
        time.sleep(int(ping_interval))

# Function to handle all incoming tcp request
def request_handle():
    global peerSocket
    global t_lock
    global peer
    
    while 1:        
        connectionSocket, addr = peerSocket.accept()
        request = connectionSocket.recv(1024)
        request = request.decode()
        # If a peer want to join the network 
        if "Join" in request:
            with t_lock:
                peerID = int(request.split(" ")[0])
                # new peer got accepted 
                if "accepted" in request:
                    print("Join request has been accepted")
                    msgList = request.split(" ")
                    first_suc, second_suc = msgList[0], msgList[1]
                    peer.setNewSuccs(first_suc, second_suc)
                    
                # peer is the pred of new peer(correct position)  
                elif peer.check_succ(int(peerID)):
                    print(f"Peer {peerID} Join request received")
                    message = str(peer.succs[0]["id"]) + " " + str(peer.succs[1]["id"]) + " " + "Join request accepted"
                    request_send(message, peerID + 8000)
                    peer.setNewSuccs(peerID, peer.succs[0]["id"])
                    request = str(peer.id) + " " + str(peer.succs
                                                       [0]['id']) + " " + "Successor change request"
                    request_send(request, peer.pred + 8000)
                # Send peer join request to first succesor
                else:
                    first_port = peer.succs[0]["id"] + 8000
                    request_send(request, first_port)                    
                    print(f"Peer {peerID} Join request forwarded to my successor\n")
    
                t_lock.notify()
        # If successor's successors changed, update peer successors too
        elif "Successor change" in request:
            print("Successor Change request received\n")
            msgList = request.split(" ")
            first_suc, second_suc = msgList[0], msgList[1]
            peer.setNewSuccs(first_suc, second_suc)
        # If a peer is leaving the network gracefully, it sends its successors to pred     
        elif "Depart" in request:
            msgList =  request.split(" ")
            peerID = int(msgList[2])
            # If the peer has leaving peer as successor, update the successors and notify pred to change succs too
            if peerID == peer.succs[0]["id"] or peerID == peer.succs[1]["id"]:
                print(f"Peer {peerID} will depart from the network")
                first_suc, second_suc = msgList[0], msgList[1]
                peer.setNewSuccs(first_suc, second_suc)
                message = str(peer.id) + " " + str(peer.succs[0]["id"]) + " " + str(peerID) + " Depart"
                request_send(message, peer.pred + 8000)
        # If receive first succesor request due to pred peer depart abruptly
        elif "First successor request" in request:
            peerID = request.split(" ")[0] 
            requestedPeer = int(request.split(" ")[1])
            message = peerID + " " + str(peer.id) + " " + str(peer.succs[0]["id"]) + " Succesor request accepted"
            request_send(message, requestedPeer + 8000)
        # If the first pred of leaved peer is updated, it send it's id and first successor as message to its pred    
        elif "Succesor request accepted" in request:
            msgList = request.split(" ")
            peerID = msgList[0]
            first_suc, second_suc = msgList[1], msgList[2]
            print(f"Peer {peerID} no longer alive")
            peer.setNewSuccs(first_suc, second_suc)
            message = peerID + " " + str(peer.id) + " " + str(peer.succs[0]["id"]) + " Successor depart abruptly"
            request_send(message, peer.pred + 8000)
        # If the first pred of leaved peer is updated, it send it's id and first successor as message to its pred
        elif "Successor depart abruptly" in request:
            msgList = request.split(" ")
            peerID = msgList[0]
            first_suc, second_suc = msgList[1], msgList[2]
            print(f"Peer {peerID} no longer alive")
            peer.setNewSuccs(first_suc, second_suc)
            
        # If the input is store file
        elif "Store file request" in request:
            fileName = request.split(" ")[0]
            file_store(fileName)
        # If the input is retrieve file
        elif "Retrieve file request" in request:
            msgList = request.split(" ")
            peerID = int(msgList[0])
            fileName = msgList[1]
            hashKey = int(fileName) % 256
            if peer.checkHashKey(hashKey):
                print(f"File {fileName} is stored here")
                file_transfer(fileName, peerID + 8000)
                print(f"Sending file {fileName} to Peer {peerID}")
                message = str(peer.id) + " " + fileName + " File request received"
                request_send(message, peerID + 8000)
                print("The file has been sent")
            else:
                print(f"Request for File {fileName} has been received, but the file is not stored here")
                request_send(request, peer.succs[0]["id"] + 8000)
        # If the file sent to requested peer 
        elif "File request received" in request:
            msgList = request.split(" ")
            peerID = int(msgList[0])
            fileName = msgList[1]
            print(f"Peer {peerID} had File {fileName}")
            file_receive(connectionSocket)
            print(f"Receiving File {fileName} from Peer {peerID}")
            peer.addFile(fileName)
            print(f"File {fileName} received")
        else:
            print(request)     
        
        connectionSocket.close()
# Send request through tcp socket
def request_send(request, port):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect(("localhost", port))
    clientSocket.send(request.encode('utf-8'))
    clientSocket.close()

# Join p2p network
def peer_join(clientSocket):
    message = str(peer.id) + " " + "Join request"
    request_send(message, peer.known_peer + 8000)

# Store file to files list 
def file_store(fileName):
    hashKey = int(fileName) % 256
    # Check the correct file's location from hashkey
    if peer.checkHashKey(hashKey):
        # If the file already stored
        if fileName in peer.files:
            print(f"File already stored")
        # Else add file to files list
        else:
            print(f"Store {fileName} request accepted")
            peer.addFile(fileName)
            #print(peer.files)
    # If peer not the correct location, pass request to first successor
    else:
        print(f"Store {fileName} request forwarded to my successor")
        request = fileName + " Store file request"
        request_send(request, peer.succs[0]["id"] + 8000)

# Function to send file retrieval request
def file_retrieve(fileName):
    hashKey = int(fileName) % 256
    if peer.checkHashKey(hashKey):
        if fileName in peer.files:
            print("File already retrieved")
        elif fileName not in peer.files:
            print(f"There's no File {fileName} on the network")
    else:
        print(f"File request for {fileName} has been sent to my successor ")
        request = str(peer.id) + " " + fileName + " Retrieve file request"
        request_send(request, peer.succs[0]["id"] + 8000)

def file_transfer(fileName, port):

    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect(("localhost", port))

    file1 = fileName + ".pdf"
    fileObject = open(file1, "rb")
    data = fileObject.read(1024)
    #message = fileName + " data send " + str(data)
    clientSocket.sendall(data)
    # data = fileObject.read(1024)

    fileObject.close()
    clientSocket.close()

def file_receive(connectionSocket):
    data = connectionSocket.recv(1024)
    print(data)

runType = sys.argv[1]

if runType == "init":
    # Check no of arguments
    if len(sys.argv) != 6:
        print('Required arguments: <type> <peerID> <first_successor> <second_successor> <ping_interval>')
        sys.exit(1)

    # Define arguments as variables
    peerID, first_suc, second_suc, ping_interval = sys.argv[2:]

    # Check peer ID with first and second successor
    if peerID == first_suc or peerID == second_suc or first_suc == second_suc:
        print(f'peer ID, first and second successor should be unique')
        sys.exit(1)

    peer = PeerNode(peerID)
    peer.succs[0]["id"] = int(first_suc)
    peer.succs[1]["id"] = int(second_suc)

elif runType == "join":
    # Check no of arguments
    if len(sys.argv) != 5:
        print('Required arguments: <type> <peerID> <known_peer> <ping_interval>')
        sys.exit(1)

    # Define arguments as variables
    peerID, known_peer, ping_interval = sys.argv[2:]

    if peerID == known_peer:
        print(f'peer ID should not same with known peer')
        sys.exit(1)

    peer = PeerNode(peerID)
    peer.setKnownPeer(known_peer)

    clientSocket = socket(AF_INET, SOCK_STREAM)
    peer_join(clientSocket)

else:
    print(f'{runType} should either "init" or "join"')
    sys.exit(1)

t_lock = threading.Condition()

pingSocket = socket(AF_INET, SOCK_DGRAM)
pingSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
pingSocket.bind(('localhost', peer.port))

# Build TCP socket
peerSocket = socket(AF_INET, SOCK_STREAM)
peerSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
peerSocket.bind(('localhost', peer.port))
peerSocket.listen(5)

recv_thread = threading.Thread(name="RecvPing", target=ping_recv)
recv_thread.daemon = True
recv_thread.start()

req_thread = threading.Thread(name="ReqHandle", target=request_handle)
req_thread.daemon = True
req_thread.start()

send_thread = threading.Thread(name="SendPing", target=ping_send)
send_thread.daemon = True
send_thread.start()

#this is the main thread for waiting input 
while True:
    request = input("Enter a command:")
    # If the input is quit, send successors to predecessor for updating it successors
    if "Quit" in request:
        message = str(peer.succs[
            0]["id"]) + " " + str(peer.succs[1]["id"]) + " " + str(peer.id) + " Depart"
        request_send(message, peer.pred + 8000)
        sys.exit(1)
    # If the input is store, find correct peer to store the file
    elif "Store" in request:
        fileName = request.split(" ")[1]
        if not fileName.isdigit() or int(fileName) < 0 or int(fileName) > 9999:
            print("File name should be four-digits numbers")            
        file_store(fileName)
    # If the input is request, find the correct peer for sending the file to this peer
    elif "Request" in request:
        fileName = request.split(" ")[1]
        if not fileName.isdigit() or int(fileName) < 0 or int(fileName) > 9999:
            print("File name should be four-digits numbers")
        file_retrieve(fileName)
