import configparser
import os

import pymysql
import pandas as pd
from datetime import datetime, timedelta
import xlsxwriter
import schedule
import time

config = configparser.ConfigParser()
config.read("database.ini")

db_config = {
    "host": config.get("database", "HW_SQL_ADD"),
    "user": config.get("database", "HW_SQL_USER"),
    "password": config.get("database", "HW_SQL_PWD"),
    "database": config.get("database", "HW_SQL_DATABASE"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def connect_db():
    connection = pymysql.connect(**db_config)
    return connection


# 查询数据函数
def fetch_user_session_count():
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = """SELECT uuser.userID, uuser.employeeNumber, uuser.displayNameEn, COUNT(uusersession.chatSessionID) AS session_count FROM userrolepermissions_user uuser left join userrolepermissions_usersession uusersession on uuser.userID=uusersession.userID group by uuser.userID order by uuser.userID"""  # 假设有一个users表
            cursor.execute(sql)
            result = cursor.fetchall()  # 获取所有结果
            print(result)
    finally:
        conn.close()
    return result


def fetch_file_count():
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = """SELECT uuser.userID, COUNT(afilesmanager.filesManagerID) AS file_count FROM userrolepermissions_user uuser left join aitoolsconfiguration_filesmanager afilesmanager on uuser.userID=afilesmanager.userID group by uuser.userID order by uuser.userID"""  # 假设有一个users表
            cursor.execute(sql)
            result = cursor.fetchall()  # 获取所有结果
            print(result)
    finally:
        conn.close()
    return result


def fetch_time():
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = """SELECT uuser.userID, MAX(uusersession.timestamp) AS latest_session_time FROM userrolepermissions_user uuser left join userrolepermissions_usersession uusersession on uuser.userID=uusersession.userID group by uuser.userID order by uuser.userID"""  # 假设有一个users表
            cursor.execute(sql)
            result = cursor.fetchall()  # 获取所有结果
            print(result)
    finally:
        conn.close()
    return result


def average_create_session_cycle():
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = """SELECT
            uuser.userID,
            COUNT(uusersession.chatSessionID) AS session_count,
            MIN(uusersession.timestamp) AS first_session_date,
            CURRENT_DATE() AS today,
            DATEDIFF(CURRENT_DATE(), MIN(uusersession.timestamp)) AS days_span,
            CASE
            WHEN COUNT(uusersession.chatSessionID) > 1 THEN DATEDIFF(CURRENT_DATE(), MIN(uusersession.timestamp)) / (COUNT(uusersession.chatSessionID))
            ELSE 0
            END AS average_creation_cycle
            FROM
            userrolepermissions_user uuser 
            left join
            userrolepermissions_usersession uusersession on uuser.userID=uusersession.userID
            GROUP BY
            uuser.userID
            order by 
            uuser.userID"""
            cursor.execute(sql)
            result = cursor.fetchall()  # 获取所有结果
            print("新建会话平均周期：", result)
    finally:
        conn.close()
    return result


def fetch_conversation_data():
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            # 查询 userID 和 conversationrecord
            sql = "SELECT uusersession.userID, uuser.employeeNumber, uuser.displayNameEn, uusersession.chatSessionID, uusersession.conversationrecord, uusersession.timestamp FROM userrolepermissions_usersession as uusersession left join userrolepermissions_user as uuser on uusersession.userID=uuser.userID"
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()


def parse_conversations(data):
    # 解析对话记录，计算每个会话的对话数
    results = []
    for record in data:
        # 解析记录
        try:
            # 将字符串转换为列表
            conversations = eval(record["conversationrecord"])
            count = len(conversations)
        except:
            count = 0  # 如果解析失败，对话数为0
        results.append(
            {
                "userID": record["userID"],
                "工号": record["employeeNumber"],
                "姓名": record["displayNameEn"],
                "sessionID": record["chatSessionID"],
                "对话论数": count,
                "日期": record["timestamp"],
            }
        )
    return results


def fetch_everyday_session_count():
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = """SELECT DATE(uusersession.timestamp) AS session_date, COUNT(*) AS session_count FROM userrolepermissions_usersession uusersession  group by DATE(uusersession.timestamp) order by DATE(uusersession.timestamp)"""  # 假设有一个users表
            cursor.execute(sql)
            result = cursor.fetchall()  # 获取所有结果
            print(result)
    finally:
        conn.close()
    return result


def generate_excel_report():
    user_ids = [item["userID"] for item in fetch_user_session_count()]
    employeeNumber = [item["employeeNumber"] for item in fetch_user_session_count()]
    displayNameEn = [item["displayNameEn"] for item in fetch_user_session_count()]
    session_count = [item["session_count"] for item in fetch_user_session_count()]
    file_count = [item["file_count"] for item in fetch_file_count()]
    average_create_session_cycle_final = [
        item["average_creation_cycle"] for item in average_create_session_cycle()
    ]
    sample_data = fetch_time()
    print(
        "Data type of 'latest_session_time':",
        type(sample_data[0]["latest_session_time"]),
    )
    latest_time = [item["latest_session_time"] for item in fetch_time()]
    now = datetime.now()
    time_since_last_session = [
        (now - time if time is not None else None) for time in latest_time
    ]
    days_since_last_session = [
        delta.days if delta is not None else None for delta in time_since_last_session
    ]

    daily_session_date = [
        item["session_date"] for item in fetch_everyday_session_count()
    ]
    daily_session_count = [
        item["session_count"] for item in fetch_everyday_session_count()
    ]

    print("user_ids:", user_ids)
    print("employeeNumber:", employeeNumber)
    print("displayNameEn:", displayNameEn)
    print("session_count:", session_count)
    print("file_count:", file_count)
    print("daily_session_date:", daily_session_date)
    print("daily_session_count:", daily_session_count)

    # 获取数据
    conversation_data = fetch_conversation_data()

    # 解析对话并计算对话条数
    parsed_data = parse_conversations(conversation_data)

    # 用户数据
    user_data = {
        "用户ID": user_ids,
        "工号": employeeNumber,
        "姓名": displayNameEn,
        "会话数量": session_count,
        "文件数量": file_count,
        "距今未登录天数": days_since_last_session,
        "平均新建会话周期": average_create_session_cycle_final,
    }

    user_df = pd.DataFrame(user_data)

    # 统计用户总数量
    total_users = len(user_df["用户ID"].unique())

    session_count = {
        "日期": daily_session_date,
        "会话数量": daily_session_count,
    }

    session_df = pd.DataFrame(session_count)
    session_record_df = pd.DataFrame(parsed_data)

    current_date = datetime.now().strftime("%Y-%m-%d")
    output_folder = "reports"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    file_path = os.path.join(output_folder, f"用户行为分析报告_{current_date}.xlsx")

    # 写入 Excel 文件
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        user_df.to_excel(writer, sheet_name="用户报告", index=False)
        session_record_df.to_excel(
            writer, sheet_name="session问答条数统计", index=False
        )
        session_df.to_excel(writer, sheet_name="每日会话数量", index=True)

        # 添加用户总数量的统计信息
        total_df = pd.DataFrame({"统计指标": ["总用户数量"], "值": [total_users]})
        total_df.to_excel(writer, sheet_name="总览统计", index=False)


schedule.every().day.at("16:19").do(generate_excel_report)

while True:
    schedule.run_pending()
    time.sleep(1)