import sys
import hashlib
import time
import re
import thrift.protocol.TBinaryProtocol as TBinaryProtocol
import thrift.transport.THttpClient as THttpClient
import evernote.edam.userstore.UserStore as UserStore
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.notestore.NoteStore as NoteStore
import evernote.edam.type.ttypes as Types
import evernote.edam.error.constants as ErrorConstants

#TODO add a default settings.py with the following variables:
#consumerKey = "username"
#consumerSecret = "apikey"
#userStoreUri = "https://sandbox.evernote.com/edam/user"
#noteStoreUriBase = "http://sandbox.evernote.com/edam/note/"
from settings import *

class EvernoteConnector(object):
    def __init__(self, username, password, consumerKey, 
            consumerSecret, userStoreUri, noteStoreUriBase):
        self.username = username
        self.password = password

        # setup the basic connection stuff
        userStoreHttpClient = THttpClient.THttpClient(userStoreUri)
        userStoreProtocol = TBinaryProtocol.TBinaryProtocol(userStoreHttpClient)
        userStore = UserStore.Client(userStoreProtocol)

        versionOK = userStore.checkVersion("Python EDAMTest",
                                           UserStoreConstants.EDAM_VERSION_MAJOR,
                                           UserStoreConstants.EDAM_VERSION_MINOR)
        if not versionOK:
            raise ErrorConstants.EDAMSystemException(
                    ErrorConstants.EDAMErrorCode.UNKNOWN,
                    "EDAM protocol version not up to date ")

        authResult = userStore.authenticate(username, password,
                                            consumerKey, consumerSecret)
        user = authResult.user
        authToken = authResult.authenticationToken

        noteStoreUri =  noteStoreUriBase + user.shardId
        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUri)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)

        self.noteStore = NoteStore.Client(noteStoreProtocol)

        self.notebooks = None
        self.defaultNotebook = None

    def get_notebooks(self, filter):
        """
        get notebooks, set default and search for specified notebooks
        """
        self.notebooks = noteStore.listNotebooks(authToken)
        matchingNotebooks = []

        for notebook in self.notebooks:
            if notebook.defaultNotebook:
                self.defaultNotebook = notebook
            if filter is not None:
                nbRe = re.compile(filter, re.I)
                if re.search(nbRe, notebook.name) is not None:
                    matchingNotebooks.append(notebook)
        
        return matchingNotebooks

    def send_note(self):
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

    def get_note(self):
        filter = NoteStore.NoteFilter()
        filter.notebookGuid = defaultNotebook.guid

        tags = noteStore.listTags(authToken)
        for tag in tags:
            if tag.name.find("test") >= 0:
                filter.tagGuids = [tag.guid]
                break

        noteList = noteStore.findNotes(authToken, filter, 0, 9999)

        for note in noteList.notes:
            print "id: "+note.guid
            print "title :"+note.title
            print "content:"
            print noteStore.getNoteContent(authToken, note.guid)
            print "---------------------"
            print ""


if len(sys.argv) < 3:
    print "Arguments:  <username> <password>";
    exit(1)

username = sys.argv[1]
password = sys.argv[2]
action = sys.argv[3]
if len(sys.argv) >= 4:
    wantedNotebook = sys.argv[4]
else:
    wantedNotebook = None

connector = EvernoteConnector(username, password, 
        consumerKey, consumerSecret, userStoreUri, 
        noteStoreUriBase)

connector.get_notebooks(wantedNotebook)

