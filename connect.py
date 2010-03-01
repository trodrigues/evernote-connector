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

        self.getNotebooks(None)


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


    def newNote(self, notebook):
        note = Types.Note()
        
        if notebook is not False:
            note.notebookGuid = notebook.guid
        else:
            note.notebookGuid = self.defaultNotebook.guid

        return note


    def formatNoteContent(self, innerContent):
        content = '<?xml version="1.0" encoding="UTF-8"?>'
        content += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml.dtd">'
        content += '<en-note>' + innerContent
        content += '</en-note>'
        return content


    def createNote(self, title, content, notebook=False):
        note = self.newNote(notebook)
        note.title = title
        note.content = self.formatNoteContent(content)
        note.created = int(time.time() * 1000)
        note.updated = note.created

        return self.noteToDic(
                self.noteStore.createNote(self.authToken, note))


    def updateNote(self, guid, title=False, content=False, notebook=False):
        note = self.newNote(notebook)
        note.guid = guid

        #TODO fetch already existent title/content if not given
        note.title = title
        note.content = self.formatNoteContent(content)

        note.updated = int(time.time() * 1000)

        return self.noteToDic(
                self.noteStore.updateNote(self.authToken, note))

    
    def noteToDic(self, note):
         return {
            "guid": note.guid,
            "title": note.title,
            "created": note.created,
            "updated": note.updated,
            "tags": note.tagNames
        }


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

                    noteDic = self.noteToDic(note)
                    if list is False:
                        noteDic["content"] = self.noteStore.getNoteContent(
                            self.authToken, note.guid)
                    notes.append(noteDic)
        
        return notes


    def getNoteList(self, notebook=None):
        return self._getNotes(notebook=notebook, list=True)


    def getNotes(self, notes=False, notebook=None):
        return self._getNotes(wantedNotes=notes, notebook=notebook, list=False)

