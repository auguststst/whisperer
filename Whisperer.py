#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telebot
import time
import mysql.connector
import re
import logging
import boto3
from flask import Flask, request
import os


#options for S3 storage

ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
ACCESS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.environ.get('S3_BUCKET')
s3 = boto3.resource('s3',aws_access_key_id=ACCESS_KEY_ID,aws_secret_access_key=ACCESS_SECRET_KEY)


#connect to database, make class for it and constants
mydb = mysql.connector.connect(
    host='us-cdbr-iron-east-03.cleardb.net',
    user='be782ccb37582e',
    passwd='e50f673a',
    database='heroku_0de5aba48e0f2c9'
)


TOKEN = '801288104:AAFF3SCfE-iwEn9PDq6kAMSWdJ7OkyLZp7M'
bot = telebot.TeleBot(token=TOKEN)
usernames=[]  #new stroke
logging.basicConfig(level=logging.WARNING)
server = Flask(__name__)

@bot.message_handler(commands=['start'])

def handle_start(message):

            #############3check if user registered or not##############33

    username = message.from_user.username
    mycursor = mydb.cursor()
    sql = "SELECT * FROM users WHERE username='%s'" %(username)
    mycursor.execute(sql)
    allusers = mycursor.fetchall()
    count = len(allusers)
    if allusers:
        for x in range(0,count):
            if allusers[x][1].strip() == username.strip():
                print('this user already exists')


    else:
            ###########register user in this bot #####################3

        print("No such user")
        mycursor = mydb.cursor()
        mycursor.execute("insert into users(username) values(%s)", [username])

        mydb.commit()
        print(mycursor.rowcount, "record inserted.")

                #############make keyboard###############

    user_murkup = telebot.types.ReplyKeyboardMarkup(True)
    user_murkup.row('mine rumors','make rumor')
    bot.send_message(message.from_user.id, 'Добро пожаловать в Whisper...', reply_markup=user_murkup)


#new code


@bot.message_handler(func=lambda message: True)
def handle_text(message):

    if '@' in message.text:
        username = message.text
        if username[0] == '@':
            username = username[1:] #delete first element @ in otder to insert in db
            usernames.append(username)
        mycursor = mydb.cursor()
        sql = "SELECT * FROM info WHERE username='%s' LIMIT 20" %(username)
        mycursor.execute(sql)
        myresult = mycursor.fetchall()

        if not myresult:
            bot.send_message(message.chat.id, 'Нет слухов об этом человеке. \
                                               											  \
                                               но вы можете распрастранить слухи о нем нажав кнопку "пустить слух"')
        else:
            count = len(myresult)
            for x in range(0,count):
                #image ? sendImage : sendText
                if  re.match(pattern='.*jpg$', string=myresult[x][2]):
                     #photo = open('img/'+myresult[x][2], 'rb')
                     #photo = s3.Bucket(BUCKET_NAME).download_file(KEY, myresult[x][2])
                     #bot.send_photo(message.chat.id, photo)
                     bot.send_message(message.chat.id, 'everything good')
                     #bot.send_photo(message.chat.id, "FILEID")
                else:
                    bot.send_message(message.chat.id, myresult[x][2])


                        ####################    show my rumors  ######################


    elif message.text == 'mine rumors':
        user = message.from_user.username
        mycursor = mydb.cursor()   ###############################################
        sql = "SELECT * FROM info WHERE username='%s' LIMIT 20" %(user)
        mycursor.execute(sql)
        my = mycursor.fetchall()
        if not my:
           bot.send_message(message.chat.id, "Извините но о вас не ходят слухи")
        else:
           l = len(my)
           for x in range(0,l):
               if re.match(pattern='.*jpg$', string=my[x][2]):
                   #photo = open('img/'+my[x][2], 'rb')
                   #photo = s3.Bucket(BUCKET_NAME).download_file(KEY, my[x][2])
                   #bot.send_photo(message.chat.id, photo)
                   bot.send_message(message.chat.id, 'everything good')
                   #bot.send_photo(message.chat.id, "FILEID")
               else:
                   bot.send_message(message.chat.id, my[x][2])

    elif message.text == 'make rumor' and len(usernames) != 0:
        def isBlank(myString):
            if myString:
                #myString is not None AND myString is not empty or blank
                return False
                #myString is None OR myString is empty or blank
            return True


        def make_rumor(message):
          if isBlank(message.text):
              handle_photo(message)
          else:
              information = message.text
              if len(usernames) == 1:     ############ if users are in chat
                un = usernames[0]
              else:
                un = usernames[-1]
                mycursor = mydb.cursor()
                sql = "INSERT INTO info (username, information) VALUES (%s, %s)"
                val = (un, information)
                mycursor.execute(sql, val)
                mydb.commit()
                bot.send_message(message.chat.id, "Вы роспростронили слухи")
                print(mycursor.rowcount, "record inserted.")
                print(un)

        #correct bag
                #new code
        message = bot.send_message(message.chat.id, "Введите информацию о человеке")
        bot.register_next_step_handler(message,make_rumor)

    else:
        bot.send_message(message.chat.id, 'Введите username пользователя о котором хотите роспростронить слух')


@bot.message_handler(content_types=['photo','text'])
def handle_photo(message):


        un = ""
        if usernames and len(usernames) == 1:     ############ if users are in chat
            un = usernames[0]
        elif len(usernames) == 0:
            bot.send_message(message.chat.id, 'Вначале введите username пользователя о котором хотите роспростронить слух')
        else:
            un = usernames[-1]

            ###################inserting photo into server
        raw = message.photo[2].file_id
        path = raw+".jpg"
        file_info = bot.get_file(raw)
        downloaded_file = bot.download_file(file_info.file_path)
        #s3.Bucket(BUCKET_NAME).upload_file(downloaded_file, "./key")
        s3.Bucket(BUCKET_NAME).put_object(Key=path, Body=downloaded_file, ACL='public-read')

        if un:
            mycursor = mydb.cursor()
            name = raw+".jpg"
            count = len(name)
            textlookfor = r".*jpg$"
            photos = re.findall(textlookfor, name)
            for x in photos:
                mycursor.execute("INSERT INTO info (username, information) VALUES (%s, %s)", (un, x))
            mydb.commit()
            bot.send_message(message.chat.id, "Вы роспростронили слухи")


@server.route('/' + TOKEN, methods=['GET', 'POST'])
async def getMessage(request):
    request_body_dict = await request.json()
    update = telebot.types.Update.de_json(request_body_dict)
    bot.process_new_updates([update])

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://frozen-harbor-74862.herokuapp.com/' + TOKEN)
    return "!", 200


if __name__== "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT',5000)))
