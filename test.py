from flask import Flask, request, jsonify, Blueprint
from pymongo import MongoClient
import time

app = Flask(__name__)

app1_blueprint = Blueprint('app1', __name__)
app2_blueprint = Blueprint('app2', __name__)
app3_blueprint = Blueprint('app3', __name__)

client = MongoClient('mongodb+srv://sparking:Az123456@dbs.bgpecdq.mongodb.net/?retryWrites=true&w=majority')
db = client['ATH_UET']
collection_parking = db['parking']
collection_users = db['users']

# Lấy vị trí trống ở dbs parking đầu vào là tên bãi xe, thay đổi trường dữ liệu của vị trí đó từ 0 thành 2
def find_empty_parking(nameParking):
    query_parking = {'nameParking': nameParking}
    doc = collection_parking.find_one(query_parking)
    data = doc['Slots']
    for item in data:
        if item['status'] == 0:
            query = {'Slots.status': 0, 'nameParking': nameParking}
            update = {"$set": {"Slots.$.status": 2}}
            result = collection_parking.update_one(query, update)
            return item['slot']

# Thay đổi trạng thái trên dbs user
def check_booking(idUser, reservation, time, parking):
    query = {'idUser': idUser}
    update = {'$set': {'reservation': reservation, 'time_booking': time, 'parking': parking, 'booking':1 }}
    collection_users.update_one(query, update)

# hủy đặt chỗ
def cancel_reservation(idUser):    
    doc = collection_users.find_one({'idUser': idUser})  # truy vấn người dùng
    reservation = doc['reservation']    #chỗ trong bãi xe
    nameParking = doc['parking']    #tên bãi xe
    parkdoc = collection_parking.find_one({'nameParking': nameParking})
    data = parkdoc['Slots']
    for item in data:
        if item['slot'] == reservation:
            query = {'Slots.status': 2, 'nameParking': nameParking} #check xem có cần query vế trước ko
            update = {"$set": {"Slots.$.status": 0}}
            result = collection_parking.update_one(query, update)            
# đặt trước giờ

# Hàm xử lý booking sau khi nhận request từ app
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
        print(datetime)
        check_booking(user, reservation, datetime, name_parking)
        print("Đã update đặt chỗ vị trí: ", reservation, "tại bãi xe ", name_parking)

        return {"reservation": reservation}
    except Exception as e:
        return {"error": str(e)}

#đặt chỗ trước giờ
def process_reservation(data):
    try:
        name_parking = data.get('Parking')
        user = data.get('User')
        time = data.get('TimeBooking')  

        reservation = find_empty_parking(name_parking)
        check_booking(user, reservation, time)
        print("đặt chỗ thành công")
        print(reservation)
        return {"reservation": reservation}
    except Exception as e:
        return {"error": str(e)}      

# hủy đặt chỗ hiện tại
def process_cancel(data):
    try:
        user = data.get('User')
        print(user)
        cancel_reservation(user)
        print("đã hủy")
        return {"message": 123456}
    except Exception as e:
        return {"error": str(e)}          

@app1_blueprint.route('/booking', methods = ['POST'])
@app2_blueprint.route('/reservation', methods = ['POST'])
@app3_blueprint.route('/cancel', methods = ['POST'])

def booking():
    if request.method == 'POST':
        data = request.json
        response = process_booking(data)
        return jsonify(response)

def reservation():
    if request.method == 'POST':
        print("aaaaa")
        data = request.json
        response = process_reservation(data)
        print(data)
        return jsonify(response)

def cancel():
    if request.method == 'POST':
        data = request.json
        print("đã đọc được", data)
        response = process_cancel(data)
        return jsonify(response)

# Đăng ký các ứng dụng vào ứng dụng chính
app.register_blueprint(app1_blueprint, url_prefix='/app1')
app.register_blueprint(app2_blueprint, url_prefix='/app2')
app.register_blueprint(app3_blueprint, url_prefix='/app3')
# server = app.server
if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=8080, debug=True)
    app.run(port = 8080, debug=False)