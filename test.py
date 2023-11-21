import cv2
import face_recognition
import os

# Load và mã hóa khuôn mặt từ "check.jpg"
imgCheck = face_recognition.load_image_file("check.jpg")
imgCheck = cv2.cvtColor(imgCheck, cv2.COLOR_BGR2RGB)
encodeCheck = face_recognition.face_encodings(imgCheck)[0]

# Đường dẫn đến thư mục chứa hình ảnh để so sánh
pic_folder = "pic"

# Lặp qua tất cả các hình ảnh trong thư mục "pic"
for filename in os.listdir(pic_folder):
    path = os.path.join(pic_folder, filename)
    imgUser = face_recognition.load_image_file(path)
    imgUser = cv2.cvtColor(imgUser, cv2.COLOR_BGR2RGB)
    encodeUser = face_recognition.face_encodings(imgUser)[0]

    # So sánh khuôn mặt từ "check.jpg" với khuôn mặt từ hình ảnh trong thư mục "pic"
    results = face_recognition.compare_faces([encodeUser], encodeCheck)
    faceDis = face_recognition.face_distance([encodeUser], encodeCheck)

    # Nếu có khuôn mặt khớp, hiển thị kết quả và dừng vòng lặp
    if results[0]:
        print(f"Khuôn mặt khớp với {filename} với độ chênh lệch: {faceDis[0]}")
        break
