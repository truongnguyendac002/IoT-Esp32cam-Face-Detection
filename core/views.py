from django.shortcuts import render, redirect
from django.conf import settings
import cv2
import face_recognition
import os
import requests
import shutil
import pyodbc
import time
from datetime import datetime
from azure.storage.blob import BlobServiceClient
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required



# Create your views here.
def index(request):
    image_list = get_image_list()
    history_list = get_history_as_list()
    return render(request, 'core/index.html', {
        'image_list' : image_list,
        'history_list': history_list
    })

@login_required
def open(request):
    image_list = get_image_list()
    history_list = get_history_as_list()
    return render(request, 'core/index.html', {
        'image_list' : image_list,
        'history_list': history_list
    })
def close(request):
    image_list = get_image_list()
    history_list = get_history_as_list()
    return render(request, 'core/index.html', {
        'image_list' : image_list,
        'history_list': history_list
    })

@login_required
def voice(request):
    image_list = get_image_list()
    history_list = get_history_as_list()
    return render(request, 'core/index.html', {
        'image_list' : image_list,
        'history_list': history_list
    })
    
def send(request):
    message = ""
    if download_image_from_esp():
        face_encodings, m = encode_check_image()
        message+=m
        match_found, m = compare_with_pic_folder(face_encodings)
        message+=m
        if not match_found:
            message += ("Không tìm thấy khuôn mặt khớp trong thư mục 'pic'")
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
    url = 'http://172.20.10.14'  # Replace with your ESP32's IP address
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
                    updateHistory(ten)
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
    now = datetime.now()
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

def updateHistory(ten):
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
            gio = datetime.datetime.now()
            cheDo = "Face"  # Giá trị mặc định cho CheDo

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



def logout_view(request):
    logout(request)

    return redirect('core:index')