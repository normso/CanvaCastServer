from flask import Flask, render_template,request
from flask_sock import Sock
from flask_cors import CORS
import shortuuid
import os
import json

class attendee():
    def __init__(this,name,socket=None):
        this.name = name
        this.pen = 2
        this.color = "#000000"
        this.socket = socket

class board():
    def __init__(this,boardname,creator):
        this.boardname = boardname
        this.attendee = {}
        this.ids = 0
        this.creator = creator


    def addAttendee(this,attendee):
        this.attendee[this.ids] = attendee
        this.ids += 1
        return (str(this.ids-1),attendee.name)

    def addAdmin(this,sock):
        this.creator.socket = sock
        return this.addAttendee(this.creator)

app = Flask(__name__)
CORS(app)
sock = Sock(app)
boards = {} 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/createboard',methods=['POST'])
def createRoom():
    payload = request.get_json()
    print(payload)
    uuid = shortuuid.ShortUUID().random(length=6)
    creator = attendee(payload['pName'])
    newboard  = board(payload['bName'],creator)
    boards[uuid] = newboard
    return {"result":200,"boardid":uuid}

@app.route('/board/<boardid>')
def room(roomid):
    if roomid not in rooms:
        return "Bad request"
    return render_template('room.html')

@sock.route('/join/<boardid>')
def echo(sock,boardid):
    if boardid not in boards:
        return {"result":400}
    mid = None

    try:
        while True:
            data = json.loads(sock.receive())
            if data["a"] == "add":
                mes = {"a" : "added"}
                if data["r"] == "admin":
                    mid,name = boards[boardid].addAdmin(sock)
                    mes["n"] = name
                    mes["id"] = mid
                else:
                    new_attendee = attendee(data["n"],sock)
                    mid,name = boards[boardid].addAttendee(new_attendee)
                    mes["n"] = name
                    mes["id"] = mid
                for attendeeid,attendeeobj in boards[boardid].attendee.items() :
                    if attendeeobj.socket == sock :
                        mes['r'] = "you"
                    else:
                        mes['r'] = "other"
                    attendeeobj.socket.send(json.dumps(mes))

            elif data["a"] == "p":
                for attendeeid,attendeeobj in boards[boardid].attendee.items() :
                    if attendeeobj.socket != sock:
                        attendeeobj.socket.send(json.dumps(data))

            elif data["a"] == "list":
                mes = {"a" : "list","l":[]}
                for attendeeid,attendeeobj in boards[boardid].attendee.items() :
                    if str(attendeeid) != data["id"]:
                        mes["l"].append({"name" : attendeeobj.name ,"id": attendeeid})
                sock.send(json.dumps(mes))

    except:
        boards[boardid].attendee.pop(int(mid))
        mes = {
            "a" : "leaved",
            "id" : mid,
        }
        if len(boards[boardid].attendee) > 0:   
            for attendeeid,attendeeobj in boards[boardid].attendee.items() :
                attendeeobj.socket.send(json.dumps(mes))
        else:
            boards.pop(boardid)




    



        print(type(data),data)


# app.run(host="0.0.0.0:"+os.getenv("PORT"))
app.run(host="0.0.0.0",port=os.getenv("PORT", default=5000),debug=True)
