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
        self.authToken = authResult.authenticationToken

        noteStoreUri =  noteStoreUriBase + user.shardId
        noteStoreHttpClient = THttpClient.THttpClient(noteStoreUri)
        noteStoreProtocol = TBinaryProtocol.TBinaryProtocol(noteStoreHttpClient)

        self.noteStore = NoteStore.Client(noteStoreProtocol)

        self.notebooks = None
        self.defaultNotebook = None

    def getNotebooks(self, filter):
        """
        get notebooks, set default and search for specified notebooks
        """
        self.notebooks = self.noteStore.listNotebooks(self.authToken)
        matchingNotebooks = []

        for notebook in self.notebooks:
            if notebook.defaultNotebook:
                self.defaultNotebook = notebook
            if filter is not None:
                nbRe = re.compile(filter, re.I)
                if re.search(nbRe, notebook.name) is not None:
                    matchingNotebooks.append(notebook)
        
        return matchingNotebooks

    def sendNote(self):
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


    def _getNotes(self, wantedNotes=False, notebook=None, list=False):
        filter = NoteStore.NoteFilter()
        
        if notebook is not None:
            filter.notebookGuid = notebook.guid
        else:
            filter.notebookGuid = self.defaultNotebook.guid

        #for tag in tags:
        #    if tag.name.find("test") >= 0:
        #        filter.tagGuids = [tag.guid]
        #        break

        noteList = self.noteStore.findNotes(self.authToken, filter, 0, 9999)
        notes = []

        for note in noteList.notes:
            if note.active is True:
                #TODO add more properties 
                if wantedNotes is False or\
                    wantedNotes is not False and note.guid in wantedNotes:

                    noteDic = {
                        "guid": note.guid,
                        "title": note.title,
                        "created": note.created,
                        "updated": note.updated,
                        "tags": note.tagNames
                    }
                    if list is False:
                        noteDic["content"] = self.noteStore.getNoteContent(
                            self.authToken, note.guid),
                    notes.append(noteDic)
        
        return notes


    def getNoteList(self, notebook=None):
        return self._getNotes(notebook=notebook, list=True)


    def getNotes(self, notes=False, notebook=None):
        return self._getNotes(wantedNotes=notes, notebook=notebook, list=False)



if len(sys.argv) < 3:
    print "Arguments:  <username> <password>";
    exit(1)

username = sys.argv[1]
password = sys.argv[2]
action = sys.argv[3]
if len(sys.argv) >= 5:
    wantedNotebook = sys.argv[4]
else:
    wantedNotebook = None

connector = EvernoteConnector(username, password, 
        consumerKey, consumerSecret, userStoreUri, 
        noteStoreUriBase)

connector.getNotebooks(wantedNotebook)
notes = connector.getNoteList()
print connector.getNotes([notes[0]["guid"], notes[1]["guid"]])
