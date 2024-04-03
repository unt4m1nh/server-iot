from flask import Flask, request, jsonify, Blueprint
from pymongo import MongoClient
import time
import random
import string

app = Flask(__name__)

app1_blueprint = Blueprint('app1', __name__)    #booking
app2_blueprint = Blueprint('app2', __name__)    #reservation
app3_blueprint = Blueprint('app3', __name__)    #cancel

client = MongoClient('mongodb+srv://sparking:Az123456@dbs.bgpecdq.mongodb.net/?retryWrites=true&w=majority')
db = client['ATH_UET']
collection_parking = db['parking']
collection_users = db['users']
collection_session = db['session']

# Tạo sessionId
def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

# Lấy vị trí trống ở dbs parking đầu vào là tên bãi xe, thay đổi trường dữ liệu của vị trí đó từ 0 thành 2
def find_empty_parking(nameParking):
    query_parking = {'nameParking': nameParking}
    doc = collection_parking.find_one(query_parking)
    data = doc['SlotStatus']
    for item in data:
        if item['status'] == 0:
            query = {'SlotStatus.status': 0, 'nameParking': nameParking}
            update = {"$set": {"SlotStatus.$.status": 2}}
            result = collection_parking.update_one(query, update)
            return item['slot']

# Thay đổi trạng thái trên dbs user
def check_booking(idUser, reservation, time, parking):
    # Tìm user thông qua trường idUser
    query = {'idUser': idUser}

    # Nội dung update
    # update = {'$set': {'reservation': reservation, 'time_booking': time, 'parking': parking, 'booking':1 }}
    update = {'$set': {'booking':1 }}
    collection_users.update_one(query, update)

# Tạo session mới trên db Session
def createSession(sessionId, idUser, name, vehicle, parking, slot, timeBooking, date, status):
    newSession = {
        "sessionId": sessionId,
        "idUser": idUser,
        "name": name,
        "vehicle": vehicle,
        "parking": parking,
        "slot": slot,
        "timeBooking": timeBooking,
        "date": date,
        "status": status,
    }
    collection_session.insert_one(newSession)

# hủy đặt chỗ chính
def cancel_reservation(idUser, sessionId):    
    doc = collection_users.find_one({'idUser': idUser})  # truy vấn người dùng
    reservation = doc['reservation']    #chỗ trong bãi xe
    nameParking = doc['parking']    #tên bãi xe
    print('Hủy đặt vị trí', reservation, 'tại bãi xe: ', nameParking)
    parkdoc = collection_parking.find_one({'nameParking': nameParking})
    data = parkdoc['SlotStatus']
    update1 = {"$set": {"booking": 0}}
    collection_users.update_one({'idUser': idUser}, update1)
    collection_session.update_one({'sessionId': sessionId}, {"$set": {"status": 0}})
    # for item in data:
    #     if item['slot'] == reservation:
    #         query = {'SlotStatus': 2, 'nameParking': nameParking} #check xem có cần query vế trước ko
    #         update = {"$set": {"SlotStatus.$.status": 0}}  
    #         collection_parking.update_one(query, update)            
# đặt trước giờ

@app1_blueprint.route('/booking', methods = ['POST'])
# Hàm xử lý booking sau khi nhận request từ app
def booking():
    if request.method == 'POST':
        data = request.json
        response = process_booking(data)
        return jsonify(response)

def process_booking(data):
    try:
        name_parking = data.get('Parking')
        user = data.get('User')
        date = data.get('date')
        time = data.get('time') 

        # print(name_parking, user, time)
        reservation = find_empty_parking(name_parking)
        print(date, time)
        datetime = date + time
        check_booking(user, reservation, datetime, name_parking)
        print("Người dùng ", user, "Đã đặt trước vị trí ",reservation, "tại bãi xe", name_parking, "bắt đầu vào:", datetime)
        return {"Vị trí ô đỗ": reservation}
    except Exception as e:
        return {"error": str(e)}

@app2_blueprint.route('/reservation', methods = ['POST'])
#đặt chỗ ngay
def reservation():
    if request.method == 'POST':
        data = request.json
        response = process_reservation(data)
        return jsonify(response)
    
def process_reservation(data):
    try:
        name_parking = data.get('Parking')
        user_id = data.get('UserId')
        username = data.get('Username')
        time = data.get('TimeBooking') 
        date = data.get('Date') 
        reservation = find_empty_parking(name_parking)
        check_booking(user_id, reservation, time, name_parking)
        sessionId = generate_random_string(8)
        createSession(sessionId, user_id, username, 'Toyota Camry', name_parking, reservation, time, date, 1)
        print("Người dùng", username, "đã đặt vị trí",reservation, "tại bãi xe", name_parking)
        return {"Vị trí ô đỗ": reservation}
    except Exception as e:
        return {"error": str(e)}      

@app3_blueprint.route('/cancel', methods = ['POST'])

# hủy đặt chỗ hiện tại
def cancel():
    if request.method == 'POST':
        data = request.json
        print("đã đọc được", data)
        response = process_cancel(data)
        return jsonify(response)
    
def process_cancel(data):
    try:
        user = data.get('User')
        sessionId = data.get('sessionId')

        cancel_reservation(user, sessionId)
        print("Đã hủy đặt chỗ cho người dùng", user)
        return {"message": "Đã hủy thành công"}
    except Exception as e:
        return {"error": str(e)}          

# Đăng ký các ứng dụng vào ứng dụng chính
app.register_blueprint(app1_blueprint, url_prefix='/app1')
app.register_blueprint(app2_blueprint, url_prefix='/app2')
app.register_blueprint(app3_blueprint, url_prefix='/app3')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
    