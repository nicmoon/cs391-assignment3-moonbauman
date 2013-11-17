"""Threads2.py
Provides examples of using threads with sockets."""

from socket import *
import threading, re, sys, os

class UDPServer (threading.Thread):
    peers = {}
    sequenceNumbers = {}

    def __init__(self, threadID, peerName, peerIP, serverPort, peerDict, filePath):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.peerName = peerName
        self.peerIP = peerIP
        self.serverPort = serverPort
        self.counter = 0
        self.done = False
        self.peers = peerDict
        self.filePath = filePath
        self.sequenceNumber = 0
        

    def controlledFlood(self, fileName, peerIP, peerPort, originatorIP, originatorPort):
        self.sequenceNumber += 1
        found = False
        for key, value in self.peers.iteritems():
            if found is not False:
                break
            for item in value:
                if (key == peerIP and item == peerPort) or (key == originatorIP and item == originatorPort):
                    continue # Not going to send to the peer we received from, or the originating peer
                clientSocket = socket(AF_INET, SOCK_DGRAM)
                clientSocket.sendto( " ".join( ("find", fileName, str(self.sequenceNumber), str(self.serverPort), originatorIP, originatorPort) ), (key, item) )
                modifiedMesg, serverAddress = clientSocket.recvfrom(2048)
                if re.match("^[ ]*found.*$", modifiedMesg):
                    found = modifiedMesg
                    break
        return found

    def run(self):
        print "Starting UDP server thread"
        serverSocket = socket(AF_INET,SOCK_DGRAM)
        serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSocket.bind(('',self.serverPort))
        print "The UDP server is ready to receive"
        while not(self.done):
            # recieves join, lookup requests, look up responses, quit requests
            mesg, clientAddress = serverSocket.recvfrom(2048)
            self.counter +=1
            modifiedMesg = ""
            
            if (re.match("^[ ]*join[ ]+[0-9]+$", mesg, re.I)):
                peerPort = re.split("[ ]+", mesg)[1]
                if clientAddress[0] in self.peers:
                    self.peers[clientAddress[0]].append(peerPort)
                else:
                    self.peers[clientAddress[0]] = [peerPort]

                self.sequenceNumbers[clientAddress[0] + "," + str(peerPort)] = 0
                modifiedMesg = "accepted"
                print("Accepted client " + clientAddress[0] + " with server port " + str(peerPort))

            if mesg == "peers":
                for key, value in self.peers.iteritems():
                    modifiedMesg += key + ": "
                    modifiedValue = map(str, value)
                    modifiedMesg += ", ".join(modifiedValue)
                    modifiedMesg += "\n"

            if mesg == "fileList":
                modifiedMesg = ", ".join(os.listdir(self.filePath))

            if ( re.match("^[ ]*find[ ]+(.+)[ ]+[0-9]+$", mesg, re.I)):
                command, filename, sequenceNumber, peerPort, originatorIP, originatorPort = re.split("[ ]+", mesg)

                if originatorIP == self.peerIP and int(originatorPort) == self.serverPort:
                    modifiedMesg = self.controlledFlood( filename, clientAddress[0], peerPort, originatorIP, originatorPort )
                else:
                    if self.sequenceNumbers[clientAddress[0] + "," + str(peerPort)] < sequenceNumber:
                        self.sequenceNumbers[clientAddress[0] + "," + str(peerPort)] = sequenceNumber
                        if filename in os.listdir(self.filePath):
                            modifiedMesg = " ".join( ("found", self.peerName, self.peerIP, str(self.serverPort), str(self.serverPort-1)) )
                        else:
                            modifiedMesg = self.controlledFlood( filename, clientAddress[0], peerPort, originatorIP, originatorPort )

            if mesg == "quit":
                self.done = True
                modifiedMesg = "quitting"

            serverSocket.sendto(str(modifiedMesg), clientAddress)

        print "Exiting UDP server thread"


class TCPServer (threading.Thread):
    def __init__(self, threadID, serverPort, filePath):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.serverPort = serverPort
        self.counter = 0
        self.done = False
        self.filePath = filePath
        
    def run(self):
        print "Starting TCP server thread"
        serverSocket = socket(AF_INET,SOCK_STREAM)
        serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSocket.bind(('',self.serverPort))
        serverSocket.listen(5)
        print "The TCP server is ready to receive"
        while not(self.done):
            connectionSocket,addr = serverSocket.accept()
            self.counter +=1
            mesg= connectionSocket.recv(2048)
            modifiedMesg = ""
            
            if mesg == "quit":
                self.done = True
                modifiedMesg = "quitting"

            if re.match("^get[ ]+(.+)[ ]+(.+)[ ]+([0-9]+)$", mesg):
                command, filename, targetPeerIP, targetPeerPort = re.split("[ ]+", mesg)
                if filename not in os.listdir(self.filePath):
                    modifiedMesg = False
                else:
                    f = open(self.filePath + "/" + filename, 'r')
                    modifiedMesg = f.read()


            connectionSocket.send(str(modifiedMesg))
            connectionSocket.close()        

        print "Exiting TCP server thread"


def runTCPClient(str, host, port):
    clientSocket = socket(AF_INET,SOCK_STREAM)
    clientSocket.connect((host, port))
    clientSocket.send(str)
    modifiedMesg,serverAddress = clientSocket.recvfrom(2048)
    clientSocket.close()
    return modifiedMesg
    
def runUDPClient(str, host, port):
    clientSocket = socket(AF_INET,SOCK_DGRAM)    
    clientSocket.sendto(str,(host, port))
    modifiedMesg,serverAddress = clientSocket.recvfrom(2048)
    return modifiedMesg

if __name__ == "__main__":
    if len(sys.argv) != 7 and len(sys.argv) != 5:
        print("Argument format is peer.py peerName peerIpAddress peerPort path [partnerIpAddress] [partnetPort].")
        sys.exit(1)

    name = sys.argv[1]
    ip = sys.argv[2]
    port = int(sys.argv[3])
    path = sys.argv[4]
    root = True
    sequenceNumber = 0

    partnerIpAddress = ""
    partnerPort = 0

    if len(sys.argv) == 7:
        partnerIpAddress = sys.argv[5]
        partnerPort = int(sys.argv[6])
        if runUDPClient("join " + str(port+1), partnerIpAddress, partnerPort) == "accepted":
            print("Joined P2P peer " + partnerIpAddress + " on UDP port " + str(partnerPort))
            root = False
        else:
            print("Unable to join P2P peer " + partnerIpAddress + " on UDP port " + str(partnerPort))

    # Create new threads
    transfer = TCPServer(1,port,path)

    # If we're not the root, then we have a peer to pass to the UDPServer
    if root is False:
        lookup = UDPServer(2, name, ip, port+1, { partnerIpAddress: [partnerPort] }, path)
    else:
        # We're the root, pass an empty dict
        lookup = UDPServer(2, name, ip, port+1, {}, path)

    # read all files in provided directory

    # Start new Threads
    transfer.start()
    lookup.start()

    choice = ""

    while not ( re.match("quit", choice, re.I) ):
        choice = raw_input("Choose an option--> status, find <filename>, get <filename> <taget-peer-ip> <target-file-transfer-port>, quit: ")
        if ( re.match("^[ ]*status[ ]*$", choice, re.I) ):
            # do status update
            print "===== STATUS ====="
            print "Peer list:"
            peerList = runUDPClient("peers", ip, port+1)
            print peerList
            print "File list:"
            fileList = runUDPClient("fileList", ip, port+1)
            print fileList
        elif ( re.match("^[ ]*find[ ]+(.+)$", choice, re.I) ):
            # str = raw_input("\tEnter a string to be echoed: ");
            # counter += 1
            # print "\tEchoed string is ",str
            print "find"
            command, filename = re.split("[ ]+", choice)
            sequenceNumber += 1
            findResult = runUDPClient( " ".join( ("find", filename, str(sequenceNumber), str(port+1), ip, str(port+1)) ), ip, port+1 )
            print findResult
        elif ( re.match("^get[ ]+(.+)[ ]+(.+)[ ]+([0-9]+)$", choice, re.I) ):
            # str = raw_input("\tEnter a string to be made uppercase: ");
            # mesg = runUDPClient(str,udpPort)
            # print "\tUppercase string is ",mesg
            print "get"
            command, filename, targetPeerIP, targetPeerPort = re.split("[ ]+", choice)
            getResult = runTCPClient( " ".join( ("get", filename, targetPeerIP, targetPeerPort) ), targetPeerIP, int(targetPeerPort) )
            f = open(path + "/" + filename, 'w')
            f.write(getResult)
            print "got " + filename
        elif not ( re.match("[ ]*quit[ ]*", choice, re.I)):
            # str = raw_input("\tEnter a string to be reversed: ");
            # mesg = runTCPClient(str,tcpPort)
            # print "\tReversed string is ",mesg
            print "unknown command"


    #Send stop message to threads
    transfer.done=True
    lookup.done=True

    #if blocking in thread1 and thread2, you can send "pings" from here to both those ports to force them out of blocking and check the loop condition
    runTCPClient("quit", ip, port)
    runUDPClient("quit", ip, port+1)

    print "Waiting for all threads to complete"
    transfer.join()
    lookup.join()

    print "Exiting Main Thread"