import requests

# Thay đổi URL và PORT tương ứng với ESP32-CAM của bạn
ESP32_CAM_URL = 'http://esp32_cam_ip_address'
ESP32_CAM_PORT = 'port_number'

# Hàm điều khiển servo thông qua ESP32-CAM
def control_servo(angle):
    # Gửi yêu cầu HTTP đến ESP32-CAM để điều khiển servo
    servo_control_url = f"{ESP32_CAM_URL}:{ESP32_CAM_PORT}/controlServo?angle={angle}"
    response = requests.get(servo_control_url)
    if response.status_code == 200:
        print(f"Đã gửi yêu cầu điều khiển servo với góc: {angle} độ")
    else:
        print("Không thể gửi yêu cầu")

# Hàm chạy chương trình
def main():
    while True:
        # Nhập góc muốn điều khiển servo từ Blynk hoặc bất kỳ nguồn nào khác
        angle = int(input("Nhập góc (0-180) muốn điều khiển servo: "))
        control_servo(angle)

# Chạy chương trình
if __name__ == "__main__":
    main()
