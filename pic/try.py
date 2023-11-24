import pyodbc
import datetime

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
    
updateHistory('truong')