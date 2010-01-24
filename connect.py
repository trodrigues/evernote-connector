#
# To run (Unix):
#   export PYTHONPATH=../../lib/python; python EDAMTest.py myuser mypass
#

import sys
import hashlib
import time
import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types

from settings import *

#
# Configure these based on the API key you received from Evernote
#

if len(sys.argv) < 3:
    print "Arguments:  <username> <password>";
    exit(1)

username = sys.argv[1]
password = sys.argv[2]
action = sys.argv[3]

userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
userStore = UserStore.Client(userStoreProtocol)

versionOK = userStore.checkVersion("Python EDAMTest",
                                   UserStoreConstants.EDAM_VERSION_MAJOR,
                                   UserStoreConstants.EDAM_VERSION_MINOR)

print "Is my EDAM protocol version up to date? ", str(versionOK)
if not versionOK:
    exit(1)

authResult = userStore.authenticate(username, password,
                                    consumerKey, consumerSecret)
user = authResult.user
authToken = authResult.authenticationToken
print "Authentication was successful for ", user.username
print "Authentication token = ", authToken

noteStoreUri =  noteStoreUriBase + user.shardId
noteStoreHttpClient = THttpClient.THttpClient(noteStoreUri)
noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)
noteStore = NoteStore.Client(noteStoreProtocol)

notebooks = noteStore.listNotebooks(authToken)
print "Found ", len(notebooks), " notebooks:"
for notebook in notebooks:
    print "  * ", notebook.name
    if notebook.defaultNotebook:
        defaultNotebook = notebook

if(action == "send"):
    print
    print "Creating a new note in default notebook: ", defaultNotebook.name
    print

    # Create a note with one image resource in it ...

    note = Types.Note()
    note.notebookGuid = defaultNotebook.guid
    note.title = "Code Test note from EDAMTest.py"
    note.content = '<?xml version="1.0" encoding="UTF-8"?>'
    note.content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml.dtd">'
    note.content += '<en-note>Here is the Evernote logo:<br/>'
    note.content += '<p title="someclass">some text</p>'
    note.content += ''
    note.content += ''
    note.content += '</en-note>'
    note.created = int(time.time() * 1000)
    note.updated = note.created

    createdNote = noteStore.createNote(authToken, note)

    print "Created note: ", str(createdNote)

if(action == "get"):

    filter = NoteStore.NoteFilter()
    filter.notebookGuid = defaultNotebook.guid

    tags = noteStore.listTags(authToken)
    for tag in tags:
        if tag.name.find("test") >= 0:
            filter.tagGuids = [tag.guid]
            break

    noteList = noteStore.findNotes(authToken, filter, 0, 9999)

    for note in noteList.notes:
        print "title :"+note.title
        print "content:"
        print noteStore.getNoteContent(authToken, note.guid)
        print "---------------------"
        print ""
