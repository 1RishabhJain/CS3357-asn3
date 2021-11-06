# CS3357-asn3
 
**Purpose of the Assignment**

The general purpose of this assignment is to continue to explore network programming and more advanced concepts by a extending the chat system built in Assignment #2.  This assignment is designed to give you further experience in:

- writing networked applications
- the socket API in Python
- writing software supporting an Internet protocol
- techniques for transferring files across the Internet

**Assigned**

Tuesday, October 19, 2021 (please check the main [course website](http://owl.uwo.ca) regularly for any updates or revisions)

**Due**

The assignment is due Tuesday, November 9th, 2021 by 11:55pm (midnight-ish) through an electronic submission through the [OWL site](http://owl.uwo.ca). If you require assistance, help is available online through [OWL](http://owl.uwo.ca).

**Late Penalty**

Late assignments will be accepted for up to two days after the due date, with weekends counting as a single day; the late penalty is 20% of the available marks per day. Lateness is based on the time the assignment is submitted.

**Individual Effort**

Your assignment is expected to be an individual effort. Feel free to discuss ideas with others in the class; however, your assignment submission must be your own work. If it is determined that you are guilty of cheating on the assignment, you could receive a grade of zero with a notice of this offence submitted to the Dean of your home faculty for inclusion in your academic record.

**What to Hand in**

Your assignment submission, as noted above, will be electronically through [OWL](http://owl.uwo.ca).  You are to submit all Python files required for your assignment.   If any special instructions are required to run your submission, be sure to include a README file documenting details.  (Keep in mind that if the TA cannot run your assignment, it becomes much harder to assign it a grade.)

**Assignment Task**

You are required to implement a more robust client-server chat application, leveraging the client and server you implemented as part of Assignment #2.  A sample implementation of Assignment #2 will be provided in the near future (after all submissions are in) that you can use as a basis for development in this assignment, if you would rather do that than use your own previous work.

For this assignment you will be adding a collection of new features to the chat application.  Users will be able to follow certain topics and certain users, instead of all messages being broadcast (though a new broadcast mechanism needs to be added too).  Users will be able to attach and send files if they want to do so.  Several commands will be added to allow the user to list active users on the server, update followed topics, and more!

**Some Particulars**

Here are some specific requirements and other important notes: 

- Your client and server are run the same as they were in Assignment #2.  (User name and server address as command line options to the client, etc.)
- Your client and server must now support a number of commands to do various things.  These commands all begin with an exclamation mark (!), entered at the prompt of the client.  The first of these commands is "!list".  When entered at the client, it is sent over to the server, and the server responds with a comma separated list of all users online at the moment.  For example, consider Alice's chat window below.

Alice's chat window:

- Your server now keeps track of a "follow list" for each online user.  This is a list of all of the terms the user is following, which can include user names as well.  (So user alice can follow the term @bob to receive every message sent by user bob, for example.). You can assume that each followed term is a single word, but you can handle more complex phrases if you like.  Only messages that contain followed terms are delivered to users; messages are not broadcast everywhere.  When a client sends a message to the server, the server scans the follow list for each online user to determine which user(s) will be forwarded a copy of the message.  The server simply scans each word of a message looking for follow terms, trailing punctuation still results in a match, but otherwise subwords do not count.  For example, suppose user alice is following the term "apple".  A message like "Would you like an apple?" would be forwarded to alice, but a message like "Do you want a pineapple?" would not.
- By default, each user follows themselves.  (So user alice follows @alice, user bob follows @bob, etc.). That way, each user will receive messages containing direct mentions of them.  
- There is now also a special reserved username:  "all".  Each user also by default follows @all, so any message containing @all is effectively broadcast to all users.  Users cannot choose to register as the "all" user; attempts to do so should result in an invalid registration response form the server.
- To manage their follow list, a number of commands can be executed by the user.  The first is "!follow?" ... when typed at a prompt at a client, this command is sent to the server, and the server responds with a comma separated list of all follow terms for the user.  The second is "!follow term", where "term" is another term to follow.  When received at the server, the server adds "term" to the follow list for the user, so that the user receives all messages containing the given term.  The last command is "!unfollow term", where "term" is a currently followed term.  On receiving this message, the server removes the term from the list of those followed by the user.  Any term can be unfollowed this way, except for @all and @username for the user.  Attempts to follow a term multiple times, attempts to remove a term not being followed, and attempts to remove terms that cannot be unfollowed should result in an error being returned to the client.  On success, appropriate messages are returned as well.  (Messages should be shown to the user appropriately.)  For example, consider the interactions between Alice and Bob, below.

Alice's chat window:

Bob's chat window:

- A new "!exit" command must also be supported.  When entered at a client's prompt, the client will be disconnected from the server.  For example, consider Alice's chat window below:

Alice's chat window:

- The last command is "!attach", or to be more precise "!attach filename terms".  This will send the file named "filename" to users following the given terms or the user sending the message.  This will involve reading the file chunk-by-chunk and sending each chunk to the appropriate recipients until the file is entirely sent.  To tell how much data to send and to receive, you will need to determine the size of the file and communicate that size in sending things.  (Much like the Content-Length header field of HTTP.). Any errors in the process (such as if "filename" does not exist) must be reported to the user.  On receipt of the file, the receiving clients will save it under the same name as what was given to the "!attach" command.  (This might mean you'll need to have your clients run from different directories, or else they could start clobbering files quite readily.)  For example, here is user alice sending a file to user bob:

Alice's chat window:

Bob's chat window:

- It is up to you to determine the flow of messages to implement the above commands and extensions to your chat application.  For example, when I implemented this myself, I kept the client simple and somewhat dumb.  It did absolutely no processing of commands itself, simply passing the text of the commands to the server and the server did all of the work.  Even "!attach" commands were driven by the server; the text of this command was sent to the server and the server issued the client a separate request for the file in question.  You can take a different approach however; as long as you deliver the required functionality, that's the main thing.

You are to provide all of the Python code for this assignment yourself, except for code used from the Assignment #2 implementation provided to you.  You are **not** allowed to use Python functions to execute other programs for you, nor are you allowed to use any libraries that haven't been explicitly allowed.  (If there is a particular library you would like to use/import, you must check first.)   All server code files must begin with *server* and* all client files must begin with *client*.  All of these files must be submitted with your assignment. 

As an important note, marks will be allocated for code style. This includes appropriate use of comments and indentation for readability, plus good naming conventions for variables, constants, and functions. Your code should also be well structured (i.e. not all in the main function). 

Please remember to test your program as well, since marks will obviously be given for correctness!  You should transfer several different files, including both text and binary files.   You can then use diff to compare the original files and the downloaded files to ensure the correct operation of your client and server.

