from django.shortcuts import render, redirect
from django.conf import settings
import cv2
import face_recognition
import os,io
import requests
import shutil
import pyodbc
import time
import speech_recognition as sr
from datetime import datetime as dt
from azure.storage.blob import BlobServiceClient
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
import paho.mqtt.client as mqtt
import time



# Create your views here.
def on_publish(client, userdata, mid):
    print(f"Message {mid} published successfully")

def on_message(client, userdata, message):
    print(f"Received from ESP32-CAM: {message.payload.decode()}")

client = mqtt.Client()
client.on_publish = on_publish
client.on_message = on_message
client.connect("test.mosquitto.org", 1883, 60)
client.subscribe("door_control")
client.loop_start()


def index(request):
    image_list = get_image_list()
    history_list = get_history_as_list()
    return render(request, 'core/index.html', {
        'image_list' : image_list,
        'history_list': history_list
    })
    
@login_required
def auto(request):
    updateHistory(request.user.username + ' bật hồng ngoại', 'auto')
    image_list = get_image_list()
    history_list = get_history_as_list()
    result = client.publish("door_control", "bat_hong_ngoai")
    print(f"Result: {result.rc}")
    time.sleep(5)
    
    
    return render(request, 'core/index.html', {
        'image_list' : image_list,
        'history_list': history_list,
        'message': 'Cửa đã mở'
    })
    
@login_required
def stopauto(request):
    updateHistory(request.user.username + ' tắt hồng ngoại', 'auto')
    image_list = get_image_list()
    history_list = get_history_as_list()
    result = client.publish("door_control", "tat_hong_ngoai")
    print(f"Result: {result.rc}")
    time.sleep(5)
    
    
    return render(request, 'core/index.html', {
        'image_list' : image_list,
        'history_list': history_list,
        'message': 'Cửa đã mở'
    })
    
@login_required
def open(request):
    updateHistory(request.user.username + ' đã mở cửa', 'Manual')
    image_list = get_image_list()
    history_list = get_history_as_list()
    result = client.publish("door_control", "open_door")
    print(f"Result: {result.rc}")
    time.sleep(5)
    
    
    return render(request, 'core/index.html', {
        'image_list' : image_list,
        'history_list': history_list,
        'message': 'Cửa đã mở'
    })
def close(request):
    image_list = get_image_list()
    history_list = get_history_as_list()
    
    result = client.publish("door_control", "close_door")
    print(f"Result: {result.rc}")
    time.sleep(5)
    
    return render(request, 'core/index.html', {
        'image_list' : image_list,
        'history_list': history_list,
        'message': 'Cửa đã đóng'
    })

@login_required
def voice(request):
    

    # get audio from the microphone 
    r = sr.Recognizer() 
    with sr.Microphone() as source: 
        print('Speak:') 
        audio = r.listen(source)
    message = ''
    try:
        recognized_text = r.recognize_google(audio)
        message += ('Bạn đã nói: ' + recognized_text)
        if "open the door" in recognized_text.lower():
            
            result = client.publish("door_control", "open_door")
            print(f"Result: {result.rc}")
            time.sleep(5)
            updateHistory(request.user.username + ' đã mở cửa', 'Voice')

        elif "close the door" in recognized_text.lower():
            result = client.publish("door_control", "close_door")
            print(f"Result: {result.rc}")
            time.sleep(5)
        
    except sr.UnknownValueError:
        print('Không thể nhận diện giọng nói.')
    except sr.RequestError as e:
        print('Không xử lý được kết quả; {0}'.format(e))

    image_list = get_image_list()
    history_list = get_history_as_list()
    return render(request, 'core/index.html', {
        'image_list' : image_list,
        'history_list': history_list,
        'message':message
    })
    
def send(request):
    message = ""
    if download_image_from_esp():
        face_encodings, m = encode_check_image()
        message+=m
        match_found, m = compare_with_blob_images(face_encodings)
        message+=m
        if not match_found:
            message += ("Không tìm thấy khuôn mặt khớp trong cơ sở dữ liệu")
        
    else:
        message+=("Lỗi khi tải hình ảnh từ ESP32")
    
    image_list = get_image_list()
    history_list = get_history_as_list()
    return render(request, 'core/index.html', {
        'message': message,
        'image_list': image_list,
        'history_list':history_list
    })
    


# Function to download image from ESP32
def download_image_from_esp():
    url = 'http://192.168.1.176/'  # Replace with your ESP32's IP address
    response = requests.get(f'{url}/capture?_cb={int(round(time.time() * 1000))}', stream=True)
    if response.status_code == 200:
        with open(os.path.join(settings.MEDIA_ROOT, 'check.jpg'), 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        return True
    else:
        return False

# Load and encode face from "check.jpg"
def encode_check_image():
    check_image_path = os.path.join(settings.MEDIA_ROOT, 'check.jpg')
    imgCheck = face_recognition.load_image_file(check_image_path)
    imgCheck = cv2.cvtColor(imgCheck, cv2.COLOR_BGR2RGB)

    # Encode all faces found in the image
    face_encodings = face_recognition.face_encodings(imgCheck)
    message = ""
    if not face_encodings:
        message += ("Không tìm thấy khuôn mặt trong esp32. ")  # In ra thông điệp khi không tìm thấy khuôn mặt

    
    return face_encodings, message

# Compare the downloaded image with images in the "pic" directory
def compare_with_pic_folder(face_encodings):

    pic_folder = os.path.join(settings.MEDIA_ROOT, "pic")
    message = ""
    for filename in os.listdir(pic_folder):
        path = os.path.join(pic_folder, filename)
        imgUser = face_recognition.load_image_file(path)
        imgUser = cv2.cvtColor(imgUser, cv2.COLOR_BGR2RGB)

        # Encode all faces found in the image from the "pic" folder
        pic_face_encodings = face_recognition.face_encodings(imgUser)

        # Compare all face encodings from "check.jpg" with face encodings from "pic" folder
        for encodeCheck in face_encodings:
            for encodeUser in pic_face_encodings:
                results = face_recognition.compare_faces([encodeUser], encodeCheck)
                faceDis = face_recognition.face_distance([encodeUser], encodeCheck)

                if results[0] and faceDis[0] < 0.4:
                    message+=(f"Khuôn mặt cực khớp với {filename} với độ chênh lệch: {faceDis[0]}")
                    # send_request_to_esp()  
                    ten = filename.split('-')[0]
                    updatePicture(ten)
                    updateHistory(ten+' đã mở cửa', 'Face')
                    
                    result = client.publish("door_control", "open_door")
                    print(f"Result: {result.rc}")
                    time.sleep(5)
                    return True, message

                elif results[0]:
                    message+=(f"Khuôn mặt khớp với {filename} với độ chênh lệch: {faceDis[0]}")
                    # send_request_to_esp()  
                    return True, message

    return False, message



def updatePicture(ten):
    #enter credentials
    account_name = 'iotnhom12'
    account_key = 'i9TSMSjG1HbCj2Uz+3bbFeiMis2kSrS6P5Dm1le9C3mn99L4vTcFM6tHNzmnWL/B2Udk9Ggr/zvs+AStvTZO/w=='
    container_name = 'picture'

    #create a client to interact with blob storage
    connect_str = 'DefaultEndpointsProtocol=https;AccountName=' + account_name + ';AccountKey=' + account_key + ';EndpointSuffix=core.windows.net'
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    #use the client to connect to the container
    container_client = blob_service_client.get_container_client(container_name)

    
    blob_list = container_client.list_blobs()
    
    # Tìm số cuối cùng trong tên file để tăng lên một đơn vị
    
    # Lấy giờ và ngày hiện tại
    now = dt.now()
    hour = now.strftime("%I-%M%p")  # Giờ:PhútAM/PM
    date = now.strftime("%d-%m-%Y")  # Ngày-Tháng-Năm

    # Tạo tên file mới
    new_filename = f'{ten}-{hour}-{date}.jpg'
    # Đường dẫn tới file check.jsp
    local_file_path = os.path.join(settings.MEDIA_ROOT, 'check.jpg')

    # Tải file lên Blob Storage với tên mới đã tạo
    blob_client = container_client.get_blob_client(new_filename)
    with open(local_file_path, "rb") as data:
        blob_client.upload_blob(data)

def get_image_list():
    #enter credentials
    account_name = 'iotnhom12'
    account_key = 'i9TSMSjG1HbCj2Uz+3bbFeiMis2kSrS6P5Dm1le9C3mn99L4vTcFM6tHNzmnWL/B2Udk9Ggr/zvs+AStvTZO/w=='
    container_name = 'picture'

    #create a client to interact with blob storage
    connect_str = 'DefaultEndpointsProtocol=https;AccountName=' + account_name + ';AccountKey=' + account_key + ';EndpointSuffix=core.windows.net'
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    #use the client to connect to the container
    container_client = blob_service_client.get_container_client(container_name)

    blob_list = container_client.list_blobs()

    image_list = []
    for blob in blob_list:
        if blob.name.endswith('.jpg'):
            image_list.append(blob.name)

    return image_list

def updateHistory(ten, mode):
    server = 'iotnhom12.database.windows.net'
    database = 'iot-demo-nhom12'
    username = 'iotnhom12'
    password = 'Truong2072002'
    driver = '{ODBC Driver 17 for SQL Server}'

    # Tạo chuỗi kết nối đến cơ sở dữ liệu
    conn_str = 'DRIVER=' + driver + ';SERVER=tcp:' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password

    # Kết nối đến cơ sở dữ liệu
    with pyodbc.connect(conn_str) as conn:
        with conn.cursor() as cursor:
 
            ten = ten
            gio = dt.now()
            cheDo = mode  # Giá trị mặc định cho CheDo

            # Tạo câu lệnh SQL để chèn dữ liệu vào bảng History
            sql_query = f"INSERT INTO [dbo].[History] (Ten, Gio, CheDo) VALUES (?, ?, ?)"
            cursor.execute(sql_query, ten, gio, cheDo)
            conn.commit()  # Lưu thay đổi vào cơ sở dữ liệu
    

def get_history_as_list():
    server = 'iotnhom12.database.windows.net'
    database = 'iot-demo-nhom12'
    username = 'iotnhom12'
    password = 'Truong2072002'
    driver = '{ODBC Driver 17 for SQL Server}'

    # Tạo chuỗi kết nối đến cơ sở dữ liệu
    conn_str = 'DRIVER=' + driver + ';SERVER=tcp:' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password

    # Khởi tạo list để chứa các bản ghi từ bảng History
    history_list = []

    # Kết nối đến cơ sở dữ liệu
    with pyodbc.connect(conn_str) as conn:
        with conn.cursor() as cursor:
            # Truy vấn tất cả các hàng từ bảng History
            cursor.execute("SELECT * FROM [dbo].[History]")

            # Lấy tên cột từ cursor.description
            columns = [column[0] for column in cursor.description]

            # Lấy tất cả các hàng dữ liệu
            rows = cursor.fetchall()

            # Thêm dữ liệu hàng vào list dưới dạng dictionaries
            for row in rows:
                history_dict = dict(zip(columns, row))
                history_list.append(history_dict)

    return history_list

# Compare the downloaded image with images in the "pic" directory
def compare_with_blob_images(face_encodings):
    #enter credentials
    account_name = 'iotnhom12'
    account_key = 'i9TSMSjG1HbCj2Uz+3bbFeiMis2kSrS6P5Dm1le9C3mn99L4vTcFM6tHNzmnWL/B2Udk9Ggr/zvs+AStvTZO/w=='
    container_name = 'auth'

    #create a client to interact with blob storage
    connect_str = 'DefaultEndpointsProtocol=https;AccountName=' + account_name + ';AccountKey=' + account_key + ';EndpointSuffix=core.windows.net'
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)

    #use the client to connect to the container
    container_client = blob_service_client.get_container_client(container_name)
    # Get the list of image names from Azure Blob Storage
    image_list = get_image_list()

    message = ""
    for image_name in image_list:
        blob_client = container_client.get_blob_client(image_name)
        blob_data = blob_client.download_blob()
        img_data = blob_data.readall()

        # Load and decode the image from blob data
        imgUser = face_recognition.load_image_file(io.BytesIO(img_data))
        imgUser = cv2.cvtColor(imgUser, cv2.COLOR_BGR2RGB)

        # Encode all faces found in the image from Blob
        pic_face_encodings = face_recognition.face_encodings(imgUser)

        # Compare all face encodings from "check.jpg" with face encodings from Blob
        for encodeCheck in face_encodings:
            for encodeUser in pic_face_encodings:
                results = face_recognition.compare_faces([encodeUser], encodeCheck)
                faceDis = face_recognition.face_distance([encodeUser], encodeCheck)

                if results[0] and faceDis[0] < 0.4:
                    message += f"Khuôn mặt cực khớp với {image_name} với độ chênh lệch: {faceDis[0]}"
                    # Do something with the matched face
                    return True, message

                elif results[0]:
                    message += f"Khuôn mặt khớp với {image_name} với độ chênh lệch: {faceDis[0]}"
                    # Do something with the matched face
                    return True, message

    print(message)
    return False, message



def logout_view(request):
    logout(request)

    return redirect('core:index')

