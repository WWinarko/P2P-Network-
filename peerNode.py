#!/usr/bin/env python3

# This file contains peer node with the methods
#  
class PeerNode:
    def __init__(self, peerID):
        self.succs = [{"id": -1, "pingSent": 0, },
                      {"id": -1, "pingSent": 0, }]
        self.id = int(peerID)
        self.port = 8000 + int(peerID)
        self.pred = -1
        self.known_peer = -1
        self.files = []
    
    # set Predecessor
    def setPred(self, message, id):
        msgcontain = message.split(" ")
        if int(msgcontain[0]) == self.id:
            self.pred = int(id)
        return

    # Set known peer for join run type
    def setKnownPeer(self, known_peer):
        self.known_peer = int(known_peer)

    # Locate where to put the joined peer
    def check_succ(self, newID):
        # the new peer has biggest id then place it before the smallest nodeID
        if self.id > self.succs[0]["id"] and newID > self.id:
            return 1
        # the new peer has smallest id then place it before the smallest nodeID 
        elif self.id > self.succs[0]["id"] and newID < self.id:
            return 1
        # current peer < newID < first successor
        elif self.id < newID and newID < self.succs[0]["id"]:
            return 1
        else:
            return 0

    # Set new successors after a peer left or joined the network
    def setNewSuccs(self, first_suc, second_suc):
        self.succs[0]["id"], self.succs[1]["id"] = int(
            first_suc), int(second_suc)
        self.succs[0]["pingSent"] = 0
        self.succs[1]["pingSent"] = 0
        print(f"My first successor is Peer {self.succs[0]['id']}")
        print(f"My second successor is Peer {self.succs[1]['id']}\n")

    # Check whether the successor left the network abruptly
    def checkTimeOut(self, succID):
        if self.succs[succID]["pingSent"] == 3:
            return 1

        return 0

    # Reset the ping sent count after receive a ping response
    def resetPingSent(self, succID):
        if self.succs[0]["id"] == succID:
            self.succs[0]["pingSent"] = 0
        else:
            self.succs[1]["pingSent"] = 0

    # Append file to files list
    def addFile(self, fileName):
        self.files.append(fileName)

    # Locate where to put the hash key 
    def checkHashKey(self, hashKey):
        if self.id == hashKey:
            return 1
        # pred < hashKey < id
        elif self.pred < hashKey and hashKey < self.id:
            return 1
        # id < pred < hashKey
        elif self.id < self.pred and self.pred < hashKey:
            return 1
        # hashKey < id < pred
        elif hashKey < self.id and self.id < self.pred:
            return 1
        else:
            return 0
