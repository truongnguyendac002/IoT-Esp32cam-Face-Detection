import cv2
import face_recognition
import os
import requests
import shutil
import time

# Function to download image from ESP32
def download_image_from_esp():
    url = 'http://192.168.1.176'  # Replace with your ESP32's IP address
    response = requests.get(f'{url}/capture?_cb={int(round(time.time() * 1000))}', stream=True)
    if response.status_code == 200:
        with open('check.jpg', 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        return True
    else:
        return False

# Load and encode face from "check.jpg"
def encode_check_image():
    imgCheck = face_recognition.load_image_file("check.jpg")
    imgCheck = cv2.cvtColor(imgCheck, cv2.COLOR_BGR2RGB)

    # Encode all faces found in the image
    face_encodings = face_recognition.face_encodings(imgCheck)
    return face_encodings

# Compare the downloaded image with images in the "pic" directory
def compare_with_pic_folder(face_encodings):
    pic_folder = "pic"
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
                    print(f"Khuôn mặt khớp với {filename} với độ chênh lệch: {faceDis[0]}")
                    return True

    return False


# Main execution
if download_image_from_esp():
    face_encodings = encode_check_image()
    match_found = compare_with_pic_folder(face_encodings)
    if not match_found:
        print("Không tìm thấy khuôn mặt khớp trong thư mục 'pic'")
else:
    print("Lỗi khi tải hình ảnh từ ESP32")
