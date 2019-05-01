#!/usr/bin/env python
# -*- coding: utf-8 -*-

import telebot
import time
import mysql.connector
import re
import logging
import config

"""
    connect to database,
    make settings for it and constants
    ...
"""
mydb = mysql.connector.connect(
    host= config.config["host"],
    user= config.config["user"],
    passwd= config.config["passwd"],
    database= config.config["database"]
)

TOKEN = config.config["token"]
bot = telebot.TeleBot(token=TOKEN, threaded=False)
usernames=[]  #new stroke
logging.basicConfig(level=logging.WARNING)



#################   sending notification   ##################
def handle_notification(message):
    mycursor = mydb.cursor()
    sql = "SELECT username FROM info ORDER BY ID DESC LIMIT 1";
    mycursor.execute(sql)
    myresult = mycursor.fetchall()
    username = myresult[0][0]

    if username:
        sql = "SELECT chat_id FROM users WHERE username='%s'" %(username)
        mycursor.execute(sql)
        ch = mycursor.fetchall()
        chat_id = ch[0][0]
        bot.send_message(chat_id, "o вас ходят слухи...")



@bot.message_handler(commands=['start'])

def handle_start(message):
    """
    check function
    if user registered in Whisperer bot or not
    ...

    """
    username = message.from_user.username
    print(username)

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
            ###########register user in this bot #####################

        print("No such user")
        mycursor = mydb.cursor()
        mycursor.execute("insert into users(username,chat_id) values(%s,%s)", [username, message.chat.id])

        mydb.commit()
        print(mycursor.rowcount, "New user registered.")

    """
    keyboard
    general keyboard for Whisperer bot
    """

    user_murkup = telebot.types.ReplyKeyboardMarkup(True)
    user_murkup.row('обо мне','пустить слух')
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
                     photo = open('img/'+myresult[x][2], 'rb')
                     #photo = s3.Bucket(BUCKET_NAME).download_file(KEY, myresult[x][2])
                     bot.send_photo(message.chat.id, photo)

                     #bot.send_photo(message.chat.id, "FILEID")
                else:
                    bot.send_message(message.chat.id, myresult[x][2])


                        ####################    show my rumors  ######################


    elif message.text == 'обо мне'.decode('utf-8'):
        print "traffic..." + message.from_user.username
        user = message.from_user.username
        if user == None:
            bot.send_message(message.chat.id, "О вас не ходят слухи потому, что у вас нет username...")
        else:
            mycursor = mydb.cursor()   ###############################################
            sql = "SELECT * FROM info WHERE username='%s' LIMIT 20" %(user)
            mycursor.execute(sql)
            my = mycursor.fetchall()
            if not my:
                bot.send_message(message.chat.id, "О вас не ходят слухи...")
            else:
                l = len(my)
                for x in range(0,l):
                    if re.match(pattern='.*jpg$', string=my[x][2]):
                        photo = open('img/'+my[x][2], 'rb')
                        #photo = s3.Bucket(BUCKET_NAME).download_file(KEY, my[x][2])
                        bot.send_photo(message.chat.id, photo)
                        #bot.send_photo(message.chat.id, "FILEID")
                    else:
                        bot.send_message(message.chat.id, my[x][2])

    elif message.text == 'пустить слух'.decode('utf-8') and len(usernames) != 0:
        print "traffic..." + message.from_user.username
        me =  message.from_user.username
        print(me)
        print(usernames[-1])

        def isBlank(myString):
            if myString:
                #myString is not None AND myString is not empty or blank
                return False
                #myString is None OR myString is empty or blank
            return True

        def make_rumor(message):
          #if me == usernames[-1]:
          if isBlank(message.text):
              handle_photo(message)
          else:
              information = message.text
              if len(usernames) == 1:     ############ if users are in chat
                un = usernames[0]
              else:
                un = usernames[-1]

              if  information != 'пустить слух'.decode('utf-8') and information != 'обо мне'.decode('utf-8'):
                  mycursor = mydb.cursor()
                  sql = "INSERT INTO info (username, information) VALUES (%s, %s)"
                  val = (un, information)
                  mycursor.execute(sql, val)
                  mydb.commit()
                  bot.send_message(message.chat.id, "Вы роспростронили слухи")
                  print(mycursor.rowcount, "record inserted.")
                  handle_notification('dsdsd')
                  print(un)
              else:
                  message = bot.send_message(message.chat.id, "нужно вводить информацию, нажмите еще раз 'пустить слух' чтобы ввести")

        if str(me) == str(usernames[-1]):
            bot.send_message(message.chat.id, "Нельзя писать о себе, введите username другого человека")
        else:
            message = bot.send_message(message.chat.id, "Введите информацию о пользователе @%s" %(str(usernames[-1])))
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
        path = "img/"+raw+".jpg"
        file_info = bot.get_file(raw)
        downloaded_file = bot.download_file(file_info.file_path)
        #s3.Bucket(BUCKET_NAME).put_object(Key=path, Body=downloaded_file, ACL='public-read')
        with open(path,'wb') as new_file:
            new_file.write(downloaded_file)
        if un:
            mycursor = mydb.cursor()
            name = raw+".jpg"
            count = len(name)
            textlookfor = r".*jpg$"
            photos = re.findall(textlookfor, name)
            for x in photos:
                mycursor.execute("INSERT INTO info (username, information) VALUES (%s, %s)", (un, x))
            mydb.commit()
            bot.send_message(message.chat.id, "Вы распространили слухи")
            print(mycursor.rowcount, "photo inserted")


@bot.message_handler(content_types=['document', 'sticker', 'video', 'voice', 'location'])
def handle_text_doc(message):
    bot.send_message(message.chat.id, "это лишнее")

while True:
    try:
        #bot.infinity_polling(True)
        bot.polling(none_stop=True)
    except Exception:
        time.sleep(1)
