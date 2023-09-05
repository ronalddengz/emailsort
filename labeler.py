from simplegmail import Gmail
from Google import Create_Service
from bs4 import BeautifulSoup
import requests
import re
import os

# looks for aBills and sBills in the email
def findBillNames(text):
    text = text.replace('=20',' ')
    pattern = r'\b[A|S]\s?[-.]?\s?\d{2,4}[A-Z]?[-]?\b' # god bless regex
    billNames = re.findall(pattern, content)
    billNames = list(set([name.upper() for name in billNames])) # get rid of duplicates, put it back into list form
    return billNames

# cleans up detected bills
def clean(name):
    name = name.replace('.','')
    name = name.replace('-','')
    name = name.replace(' ','')
    name = name.replace('\n','')
    return(name) # now everything is A000 or S000

# aBill --> sBill
def findSameAs(aBill):
    aBill = clean(aBill)
    if aBill[-1].isalpha():
       amnd = aBill[-1]
       aBill = aBill.replace(amnd,'')
       page = "https://www.nysenate.gov/legislation/bills/2023/" + aBill + "/amendment/" + amnd
    else:
        page = "https://www.nysenate.gov/legislation/bills/2023/" + aBill
    pageToScrape = requests.get(page)
    doc = BeautifulSoup(pageToScrape.text, "html.parser")

    vers = doc.find_all(string="See Senate Version of this Bill:")
    if(len(vers) != 0):
        branch = vers[0].parent.parent
        sBill = branch.find("a")
        sBill = clean(sBill.text)
        return(sBill)

# self explanatory
def makeLabel(name):
    existingLabels = service.users().labels().list(userId='me').execute() # these are all of the labels that are currently in bortbont BEFORE the new emails
    existingNames = [label['name'] for label in existingLabels.get('labels', [])] # names of all the labels (not ids)

    if name not in existingNames: # if the name doesn't exist yet...
        newLabel = {
            "name": name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show"
        }
        createdLabel = service.users().labels().create(userId='me', body=newLabel).execute()
        labelId = createdLabel['id']

##### gross authentication stuff ew ew ew #####

CLIENT_SECRET_FILE = '/Users/ronalddeng/Desktop/internship/presentation/emailsort/client_secret.json' # replace with path to client_secret.json on your device
API_NAME = 'gmail'
API_VERSION = 'v1'
SCOPES = ['https://mail.google.com/']

service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)

gmail = Gmail()

###############################################

messages = gmail.get_unread_inbox()

# get all the senate bills
for message in messages:
    
    sBills = set() # set of all sBills in an email
    
    content = message.plain
    bills = findBillNames(content)
    for bill in bills:
        if bill[0] == 'A': # aBill (grody)
            bill = findSameAs(bill) 
        else: # sBill (wahoo)
            bill = clean(bill)
        sBills.add(bill) # now we have a set of all the sBills in a single email
    message.mark_as_read() # mark as read

    print(sBills)
    
    for sBill in sBills:
        if sBill != None:
            print(sBill)
            #if not any(label.name == sBill for label in labels): # if a label with the name of a bill doesn't exist yet...
            makeLabel(sBill) # if a label with the name of a bill doesn't exist yet... make it!
            labels = gmail.list_labels() # these are all of the labels that are currently in bortbont BEFORE the new emails
            newLabel = list(filter(lambda x: x.name == sBill, labels))[0]
            message.add_label(newLabel) 

# donesies!
print("done!")
