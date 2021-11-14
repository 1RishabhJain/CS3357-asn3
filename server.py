import errno
import re
import socket
import os
import signal
import sys
import selectors

# Selector for helping us select incoming data and connections from multiple sources.

sel = selectors.DefaultSelector()

# Client list for mapping connected clients to their connections.

client_list = []

# follow list dictionary
follow_list = {}

user_count = 0;


# Signal handler for graceful exiting.  We let clients know in the process so they can disconnect too.

def signal_handler(sig, frame):
    print('Interrupt received, shutting down ...')
    message = 'DISCONNECT CHAT/1.0\n'
    for reg in client_list:
        # Empty user's follow list on exit
        follow_list[reg[0]] = [""]
        reg[1].send(message.encode())
    sys.exit(0)


# Read a single line (ending with \n) from a socket and return it.
# We will strip out the \r and the \n in the process.

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


# Search the client list for a particular user.

def client_search(user):
    for reg in client_list:
        if reg[0] == user:
            return reg[1]
    return None


# Search the client list for a particular user by their socket.

def client_search_by_socket(sock):
    for reg in client_list:
        if reg[1] == sock:
            return reg[0]
    return None


# Add a user to the client list.

def client_add(user, conn):
    registration = (user, conn)
    client_list.append(registration)
    insert = f'@{user}'
    follow_list[user] = [insert, "@all"]


# Append term to follow list
def append_follow_list(user, term, sock):
    if term not in follow_list[user]:
        # if term starts with @ it could be a user
        if term.startswith('@', 0, 1):
            newTerm = term.lstrip("@")
            # if it matches
            if client_search(newTerm):
                follow_list[user].append(term)
                message = f'Now following {term}\n'
                sock.send(message.encode())
            # does not match, send message and dont add term
            else:
                message = "User does not exist and cannot be followed\n"
                sock.send(message.encode())
        # term does not start with @, so add regardless
        else:
            follow_list[user].append(term)
            message = f'Now following {term}\n'
            sock.send(message.encode())
    else:
        message = f"Term {term} is already in follow list\n"
        sock.send(message.encode())


# Remove term from follow list
def pop_follow_list(user, term, sock):
    if term in follow_list[user]:
        if term != f'@{user}' and term != "@all":
            follow_list[user].remove(term)
            message = f'No longer following {term}\n'
            sock.send(message.encode())
        else:
            message = f"The term {term} is required cannot be unfollowed\n"
            sock.send(message.encode())
    else:
        message = f"The term {term} does not exist and cannot be unfollowed\n"
        sock.send(message.encode())


# Remove a client when disconnected.

def client_remove(user):
    for reg in client_list:
        if reg[0] == user:
            # Empty user's follow list on remove
            follow_list[reg[0]] = [""]
            client_list.remove(reg)
            break


# return names of clients
def client_name():
    user_list = []
    for reg in client_list:
        user_list.append(reg[0])
    message = (', '.join(user_list))
    return message


# returns true if message contains a term that is followed
def followedMessage(message, userFollowList):
    message_parts = message.lower().strip("\n").split(" ")
    punctuation = "!@#$%^&*(){}[]_-+=~`:;'<>.,/?"
    for i in message_parts:
        i = i.rstrip(punctuation)
        if i in userFollowList or i == "@all":
            return True


# Function to read messages from clients.

def read_message(sock, mask):
    message = get_line_from_socket(sock)
    user = client_search_by_socket(sock)
    atUser = f'@{user}'
    words = message.split(' ')

    # Does this indicate a closed connection?

    if message == '':
        print('Closing connection')
        sel.unregister(sock)
        sock.close()

    # Check for client disconnections.
    elif words[0] == 'DISCONNECT':
        print('Disconnecting user ' + user)
        client_remove(user)
        sel.unregister(sock)
        sock.close()

    # Check for command messages (starting with "!")
    elif words[1].startswith('!', 0, 1):
        # List
        if words[1] == '!list':
            message = client_name() + '\n'
            sock.send(message.encode())

        # Exit
        elif words[1] == '!exit':
            print('Disconnecting user ' + user)
            message = 'DISCONNECT CHAT/1.0\n'
            sock.send(message.encode())
            client_remove(user)
            sel.unregister(sock)
            sock.close()

        # Follow command
        elif words[1] == "!follow?":
            user_list = []
            for item in follow_list[user]:
                user_list.append(item)
            message = (', '.join(user_list)) + '\n'
            sock.send(message.encode())

        # If message begins with ! and has three words could be a follow/unfollow term command
        elif words[1] == "!follow" and len(words) == 3:
            term = words[2]
            append_follow_list(user, term, sock)
        elif words[1] == "!unfollow" and len(words) == 3:
            term = words[2]
            pop_follow_list(user, term, sock)

        elif words[1] == "!attach" and len(words) >= 3:
            sel.unregister(sock)
            receiveFile(words, sock)

        # if it does not fall under previous category then it's an invalid command
        elif words[1] == "!attach" or words[1] == "!unfollow" or words[1] == "!follow":
            message = "Invalid Command\n"
            sock.send(message.encode())

    # If it is just a regular message then print it out on the server
    else:
        print(f'Received message from user {user}:  ' + message)
        # Send message to all users that follow a relevant term
        # Need to re-add stripped newlines here.
        for reg in client_list:
            if reg[0] == user:
                continue
            else:
                currentUsername = reg[0]
                userFollowList = follow_list[currentUsername]
                if atUser in userFollowList or followedMessage(message, userFollowList):
                    client_sock = reg[1]
                    forwarded_message = f'{message}\n'
                    client_sock.send(forwarded_message.encode())


def receiveFile(words, sock):
    filename = words[2]
    fileSize = int(words[-1])
    # setting up the folders to download the file to
    folder = "receivedFiles/server/"
    os.makedirs(folder, exist_ok=True)
    path = f"receivedFiles/server/{filename}"
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
    # Calls function to send the file out to other clients
    clientsToSend(words, sock)

# Function that will send the file to other clients
def clientsToSend(words, sock):
    user = client_search_by_socket(sock)
    atUser = f'@{user}'
    filename = words[2]
    fileSize = words[-1]
    # splits file around the dot
    filenameStrip = filename.split(".")
    # stores part before the dot in the term list
    termList = [atUser]
    # iterate through the terms entered and store them in the list
    for term in words[3:-1]:
        termList.append(term)
    # At least one client has been sent the file
    matchFound = False
    # Send message to clients who follow the terms related to the file
    for reg in client_list:
        if reg[0] == user:
            continue
        else:
            currentUsername = reg[0]
            if bool(set(follow_list[currentUsername]).intersection(termList)):
                matchFound = True
                client_sock = reg[1]
                fileMessage = f"Incoming file: {filename}\n"
                client_sock.send(fileMessage.encode())
                fileMessage = f"Origin: {user}\n"
                client_sock.send(fileMessage.encode())
                fileMessage = f"Content-length: {fileSize}\n"
                client_sock.send(fileMessage.encode())
                client_sock.send(f"!FileTransfer {filename} fromServer {fileSize}\n".encode())
                sendFile(client_sock, filename, fileSize, sock)
                sel.register(client_sock, selectors.EVENT_READ, read_message)
    # Will register the original sender of the file
    sel.register(sock, selectors.EVENT_READ, read_message)
    sock.send(f"!FileTransfer {filename} fromClient\n".encode())


# helper function to the file sending
def sendFile(client_sock, filename, fileSize, sock):
    sel.unregister(client_sock)
    outgoingFile = open(f"receivedFiles/server/{filename}", "rb")
    sent = False
    remainingData = int(fileSize)
    while not sent:
        if remainingData <= 1024:
            sendAmount = remainingData
            remainingData = 0
            sent = True
        else:
            sendAmount = 1024
            remainingData = remainingData - 1024
        data = outgoingFile.read(sendAmount)
        client_sock.send(data)
    outgoingFile.close()
    waiting = True
    while waiting:
        try:
            wait = sock.recv(1024).decode()
            if wait == "!Done":
                waiting = False
            break
        except BlockingIOError as e:
            waiting = True

# Function to accept and set up clients.

def accept_client(sock, mask):
    conn, addr = sock.accept()
    print('Accepted connection from client address:', addr)
    message = get_line_from_socket(conn)
    message_parts = message.split()

    # Check format of request.

    if ((len(message_parts) != 3) or (message_parts[0] != 'REGISTER') or (message_parts[2] != 'CHAT/1.0')):
        print('Error:  Invalid registration message.')
        print('Received: ' + message)
        print('Connection closing ...')
        response = '400 Invalid registration\n'
        conn.send(response.encode())
        conn.close()

    # If request is properly formatted and user not already listed, go ahead with registration.

    else:
        user = message_parts[1]
        if user == "all":
            print('Error:  Invalid registration message.')
            print('Connection closing ...')
            response = '400 Invalid registration\n'
            conn.send(response.encode())
            conn.close()

        elif (client_search(user) == None):
            client_add(user, conn)
            print(f'Connection to client established, waiting to receive messages from user \'{user}\'...')
            response = '200 Registration succesful\n'
            conn.send(response.encode())
            conn.setblocking(False)
            sel.register(conn, selectors.EVENT_READ, read_message)

        # If user already in list, return a registration error.

        else:
            print('Error:  Client already registered.')
            print('Connection closing ...')
            response = '401 Client already registered\n'
            conn.send(response.encode())
            conn.close()


# Our main function.

def main():
    # Register our signal handler for shutting down.

    signal.signal(signal.SIGINT, signal_handler)

    # Create the socket.  We will ask this to work on any interface and to pick
    # a free port at random.  We'll print this out for clients to use.

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', 0))
    print('Will wait for client connections at port ' + str(server_socket.getsockname()[1]))
    server_socket.listen(100)
    server_socket.setblocking(False)
    sel.register(server_socket, selectors.EVENT_READ, accept_client)
    print('Waiting for incoming client connections ...')

    # Keep the server running forever, waiting for connections or messages.

    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)


if __name__ == '__main__':
    main()
