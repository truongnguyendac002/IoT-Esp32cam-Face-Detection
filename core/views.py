from django.shortcuts import render
from django.conf import settings
import cv2
import face_recognition
import os
import requests
import shutil
import time
import serial

# Create your views here.
def index(request):
  
    return render(request, 'core/index.html', {
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
    return render(request, 'core/index.html', {
        'message': message
    })
    


# Function to download image from ESP32
def download_image_from_esp():
    url = 'http://192.168.1.176'  # Replace with your ESP32's IP address
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

                if results[0]:
                    message+=(f"Khuôn mặt khớp với {filename} với độ chênh lệch: {faceDis[0]}")
                    # send_request_to_esp()  
                    return True, message

    return False, message


# def send_request_to_esp():
#     ser = serial.Serial('COM6', 9600)  # Thay đổi 'COM1' thành cổng serial của ESP32
#     ser.write(b'authentication_successful')  # Gửi thông điệp đến ESP32
#     ser.close()
