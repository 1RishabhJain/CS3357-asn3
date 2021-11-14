import socket
import os
import signal
import sys
import argparse
from urllib.parse import urlparse
import selectors

# Selector for helping us select incoming data from the server and messages typed in by the user.

sel = selectors.DefaultSelector()

# Socket for sending messages.

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# User name for tagging sent messages.

user = ''

# Signal handler for graceful exiting.  Let the server know when we're gone.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    message=f'DISCONNECT {user} CHAT/1.0\n'
    client_socket.send(message.encode())
    sys.exit(0)

# Simple function for setting up a prompt for the user.

def do_prompt(skip_line=False):
    if (skip_line):
        print("")
    print("> ", end='', flush=True)

# Read a single line (ending with \n) from a socket and return it.
# We will strip out any \r and \n in the process.

def get_line_from_socket(sock):

    done = False
    line = ''
    while (not done):
        char = sock.recv(1).decode()
        if (char == '\r'):
            pass
        elif (char == '\n'):
            done = True
        else:
            line = line + char
    return line

# Function to handle incoming messages from server.  Also look for disconnect messages to shutdown.

def handle_message_from_server(sock, mask):
    message=get_line_from_socket(sock)
    words=message.split(' ')
    # print(message)
    if words[0] == 'DISCONNECT':
        print('Disconnected from server ... exiting!')
        sys.exit(0)
    if words[0] == "!FileTransfer":
        # File transfer from client to server
        if words[2] == "fromClient":
            print(f"Attachment {words[1]} attached and distributed")
            do_prompt()
        elif words[2] == "fromServer":
            receiveFile(sock, words[1], words[3])
    else:
        print(message)
        do_prompt()

# Function to handle incoming messages from user.

def handle_keyboard_input(file, mask):
    line=sys.stdin.readline()
    if isAttach(line) == 0:
        attachFunction(line, client_socket)
    elif isAttach(line) == 1:
        print("A file with the name provided does not exist")
        do_prompt()
    else:
        message = f'@{user}: {line}'
        client_socket.send(message.encode())
        do_prompt()

def isAttach(line):
    words = line.split(' ')
    if words[0] == "!attach" and os.path.isfile(words[1].rstrip("\n")):
        return 0
    elif words[0] == "!attach":
        return 1

def attachFunction(line, sock):
    words = line.split(' ')
    line = line.rstrip("\n")
    fileName = words[1].rstrip("\n")
    outgoingFile = open(fileName, "rb")
    fileSize = os.path.getsize(fileName)
    message = "%s: %s %d\n" % (user, line, fileSize)
    # Send server message with username, inputted !attach command and the filesize
    sock.send(message.encode())
    sendFile(fileSize, fileName, outgoingFile, message, sock)
    do_prompt()

def sendFile(fileSize, fileName, outgoingFile, message, sock):
    sent = False
    remainingData = fileSize
    while not sent:
        if remainingData <= 1024:
            sendAmount = remainingData
            remainingData = 0
            sent = True
        else:
            sendAmount = 1024
        data = outgoingFile.read(sendAmount)
        sock.send(data)
    outgoingFile.close()
    waiting = True
    while waiting:
        try:
            wait = sock.recv(1024).decode()
            if wait == "!Done":
                waiting = False
            break
        except BlockingIOError as e:
            # print("waiting")
            waiting = True

def receiveFile(sock, filename, fileSize):
    fileSize = int(fileSize)
    folder = f"receivedFiles/clients/{user}"
    os.makedirs(folder, exist_ok=True)
    path = f"receivedFiles/clients/{user}/{filename}"
    incomingFile = open(path, 'wb')
    received = False
    remainingData = fileSize
    while not received:
        if remainingData <= 1024:
            receiveAmount = remainingData
            remainingData = 0
            received = True
        else:
            receiveAmount = 1024
            remainingData = remainingData - 1024
        data = sock.recv(receiveAmount)
        incomingFile.write(data)
        incomingFile.flush()
    incomingFile.close()
    sock.send("!Done".encode())
# Our main function.

def main():

    global user
    global client_socket

    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Check command line arguments to retrieve a URL.

    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="user name for this user on the chat service")
    parser.add_argument("server", help="URL indicating server location in form of chat://host:port")
    args = parser.parse_args()

    # Check the URL passed in and make sure it's valid.  If so, keep track of
    # things for later.

    try:
        server_address = urlparse(args.server)
        if ((server_address.scheme != 'chat') or (server_address.port == None) or (server_address.hostname == None)):
            raise ValueError
        host = server_address.hostname
        port = server_address.port
    except ValueError:
        print('Error:  Invalid server.  Enter a URL of the form:  chat://host:port')
        sys.exit(1)
    user = args.user

    # Now we try to make a connection to the server.

    print('Connecting to server ...')
    try:
        client_socket.connect((host, port))
    except ConnectionRefusedError:
        print('Error:  That host or port is not accepting connections.')
        sys.exit(1)

    # The connection was successful, so we can prep and send a registration message.
    
    print('Connection to server established. Sending intro message...\n')
    message = f'REGISTER {user} CHAT/1.0\n'
    client_socket.send(message.encode())
   
    # Receive the response from the server and start taking a look at it

    response_line = get_line_from_socket(client_socket)
    response_list = response_line.split(' ')
        
    # If an error is returned from the server, we dump everything sent and
    # exit right away.  
    
    if response_list[0] != '200':
        print('Error:  An error response was received from the server.  Details:\n')
        print(response_line)
        print('Exiting now ...')
        sys.exit(1)   
    else:
        print('Registration successful.  Ready for messaging!')

    # Set up our selector.

    client_socket.setblocking(False)
    sel.register(client_socket, selectors.EVENT_READ, handle_message_from_server)
    sel.register(sys.stdin, selectors.EVENT_READ, handle_keyboard_input)
    
    # Prompt the user before beginning.

    do_prompt()

    # Now do the selection.

    while(True):
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)    



if __name__ == '__main__':
    main()
