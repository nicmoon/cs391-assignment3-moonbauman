"""Threads2.py
Provides examples of using threads with sockets."""

from socket import *
import threading, re, sys

class UDPServer (threading.Thread):
    def __init__(self, threadID,serverPort):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.serverPort = serverPort
        self.counter = 0
        self.done = False
        
    def run(self):
        print "Starting UDP server thread"
        serverSocket = socket(AF_INET,SOCK_DGRAM)
        serverSocket.bind(('',self.serverPort))
        print "The UDP server is ready to receive"
        while not(self.done):
            # recieves join, lookup requests, look up responses, quit requests
            mesg, clientAddress = serverSocket.recvfrom(2048)
            self.counter +=1
            modifiedMesg = mesg.upper()
            serverSocket.sendto(modifiedMesg,clientAddress)

        print "Exiting UDP server thread"


class TCPServer (threading.Thread):
    def __init__(self, threadID,serverPort):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.serverPort = serverPort
        self.counter = 0
        self.done = False
        
    def run(self):
        print "Starting TCP server thread"
        serverSocket = socket(AF_INET,SOCK_STREAM)
        serverSocket.bind(('',self.serverPort))
        serverSocket.listen(5)
        print "The TCP server is ready to receive"
        while not(self.done):
            connectionSocket,addr = serverSocket.accept()
            self.counter +=1
            mesg= connectionSocket.recv(2048)
            modifiedMesg = mesg[::-1]
            connectionSocket.send(modifiedMesg)
            connectionSocket.close()        

        print "Exiting TCP server thread"


def runTCPClient(str,tcp):
    clientSocket = socket(AF_INET,SOCK_STREAM)
    clientSocket.connect(("localhost",tcp))
    clientSocket.send(str)
    modifiedMesg,serverAddress = clientSocket.recvfrom(2048)
    clientSocket.close()
    return modifiedMesg
    
def runUDPClient(str, udp):
    clientSocket = socket(AF_INET,SOCK_DGRAM)    
    clientSocket.sendto(str,("localhost",udp))
    modifiedMesg,serverAddress = clientSocket.recvfrom(2048)
    return modifiedMesg

if __name__ == "__main__":
    if len(sys.argv) != 7 and len(sys.argv) != 5:
        print("Argument format is peer.py peerName peerIpAddress peerPort path [partnerIpAddress] [partnetPort].")
        sys.exit(1)

    name = sys.argv[1]
    ip = sys.argv[2]
    port = sys.argv[3]
    path = sys.argv[4]
    root = True

    partnerIpAddress = ""
    partnerPort = 0

    if len(sys.argv) == 7:
        root = False
        partnerIpAddress = sys.argv[5]
        partnetPort = sys.argv[6]

    # Create new threads
    transfer = TCPServer(1,port)
    lookup = UDPServer(2,port+1)

    # read all files in provided directory

    # Start new Threads
    transfer.start()
    lookup.start()

    choice = ""

    while not ( re.match("quit", choice, re.I) ):
        choice = raw_input("Choose an option--> status, find <filename>, get <filename> <taget-peer-ip> <target-file-transfer-port>, quit: ")
        if ( re.match("^[ ]*status[ ]*$", choice, re.I) ):
            # do status update
            print "doing status"
        elif ( re.match("^[ ]*find[ ]+(.+)$", choice, re.I) ):
            # str = raw_input("\tEnter a string to be echoed: ");
            # counter += 1
            # print "\tEchoed string is ",str
            print "find"
        elif ( re.match("^get[ ]+(.+)[ ]+(.+)[ ]+([0-9]+)$", choice, re.I) ):
            # str = raw_input("\tEnter a string to be made uppercase: ");
            # mesg = runUDPClient(str,udpPort)
            # print "\tUppercase string is ",mesg
            print "get"
        elif not ( re.match("[ ]*quit[ ]*", choice, re.I)):
            # str = raw_input("\tEnter a string to be reversed: ");
            # mesg = runTCPClient(str,tcpPort)
            # print "\tReversed string is ",mesg
            print "unknown command"


    #Send stop message to threads
    transfer.done=True
    lookup.done=True

    #if blocking in thread1 and thread2, you can send "pings" from here to both those ports to force them out of blocking and check the loop condition
    runTCPClient("quit",port)
    runUDPClient("quit",port+1)

    print "Waiting for all threads to complete"
    transfer.join()
    lookup.join()

    print "Exiting Main Thread"