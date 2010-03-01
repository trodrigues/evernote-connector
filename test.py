from connect import *
#TODO add a default settings.py with the following variables:
#consumerKey = "username"
#consumerSecret = "apikey"
#userStoreUri = "https://sandbox.evernote.com/edam/user"
#noteStoreUriBase = "http://sandbox.evernote.com/edam/note/"
from settings import *


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

if action == "get":
    notelist = connector.getNoteList()
    notes = connector.getNotes([notelist[0]["guid"], notelist[1]["guid"]])
    print notes[0]["guid"]
    print notes[0]["content"]

if action == "send":
    print connector.createNote("connector test", "creating a note for the connector test")

if action == "update":
    notelist = connector.getNoteList()
    notes = connector.getNotes(["670284a3-3420-4cff-9fd6-ea6e5ffa2bcd"])
    print connector.updateNote(notes[0]["guid"], title="connector test", content="new content for the note")
