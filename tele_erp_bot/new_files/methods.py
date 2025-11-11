import frappe
import json
from frappe.integrations.utils import make_post_request
from frappe.utils.pdf import get_pdf
import requests
import telebot
import time
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    KeyboardButton,
)

# chat_id =0
# frappe.init(site='erpnext.localhost')   # or your actual site name (check bench sites folder)
# frappe.connect()
# print("Hiiiiiiiiii")
print("Connected site:", frappe.local.site)
print("Is connected:", frappe.db)


# --- Webhook endpoint ---

bot = telebot.TeleBot(token="8299952026:AAE9Fy7JBsXzOIQ6Fy-nw5n4JBJ85yByWHE")

item_price = frappe.db.sql(
    "Select item_name, price_list_rate from `tabItem Price` where price_list = 'Standard Selling'"
)
item_list = dict(item_price)


@bot.message_handler(commands=["start"])
def button_handler(message):
    print("Start Message ",message)

    chat_id = message.chat.id
    reply_keyboard = ReplyKeyboardMarkup(
        resize_keyboard=True, one_time_keyboard=False
    )
    reply_keyboard.add(
        ("Balance Payment"), ("Get Item Price"), ("Update Profile"), ("Get Payable")
    )
    bot.send_message(
        chat_id, "Check the following keyboard", reply_markup=reply_keyboard
    )

@bot.message_handler(commands=["exit"])
def button_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Thank You...", reply_markup=ReplyKeyboardRemove())

# @bot.message_handler(func=lambda message: message.text == "Get Payable")
# def handle_report(message):
#     chat_id = message.chat.id
#     user_name = message.chat.first_name
#     bot.send_message(chat_id, "Get Payable button is pressed.")

#     try:
#         html = frappe.get_print(
#             "Accounts Receivable", print_format="Standard", as_pdf=False
#         )

#         response = requests.post(
#             url,
#             data={"chat_id": 5680055111},
#             files={"document": (f"{doc.name}.pdf", html)},
#         )

#         print(f"{doc.name}.pdf")
#         return {"ok": True}
#     except Exception as e:
#         frappe.log_error("Sending PDF Error", frappe.get_traceback())

#     return {"ok": False, "error": str(e)}


@bot.message_handler(func=lambda message: message.text == "Balance Payment")
def handle_balance(message):
    frappe.init(site="erpnext.localhost")
    frappe.connect()
    chat_id = message.chat.id
    user_name = message.chat.first_name
    bot.send_message(chat_id, "Balance Payment button is pressed.")
    query = frappe.db.sql(
        "Select sum(outstanding_amount) from `tabSales Invoice` where customer = %s",
        (user_name,),
        as_list=True,
    )
    bot.send_message(
        chat_id, f"Hi {user_name}!! You need to pay {query[0][0]}.Thank You!!"
    )


@bot.message_handler(func=lambda message: message.text == "Get Item Price")
def handle_item_price(message):
    frappe.init(site="erpnext.localhost")
    frappe.connect()
    chat_id = message.chat.id
    inline_keyboard = InlineKeyboardMarkup(row_width=3)

    for key, value in item_list.items():
        new_btn = InlineKeyboardButton(text=key, callback_data=key)
        inline_keyboard.add(new_btn)

    bot.send_message(chat_id, "Welcome to the Bot!!", reply_markup=inline_keyboard)


@bot.message_handler(func=lambda message: message.text == "Update Profile")
def update_profile(message):
    chat_id = message.chat.id

    inline_keyboard = InlineKeyboardMarkup(row_width=3)

    phone = InlineKeyboardButton(text="Phone Number", callback_data="phone_no")
    address = InlineKeyboardButton(text="Address", callback_data="address")
    inline_keyboard.add(phone, address)
    bot.send_message(chat_id, "Choose your Option!!", reply_markup=inline_keyboard)


@bot.callback_query_handler(lambda call: call.data == "phone_no")
def handle_profile(call):
    chat_id = call.from_user.id
    msg = bot.send_message(chat_id, "Enter Your Phone Number..")
    bot.register_next_step_handler(msg, update_phone)


@bot.callback_query_handler(lambda call: call.data == "address")
def handle_address(call):
    chat_id = call.from_user.id
    msg = bot.send_message(chat_id, "Enter Your Address..")
    bot.register_next_step_handler(msg, update_address)
    print("below next step")

@bot.callback_query_handler(func=lambda call: True)
def stock_price(call):
    msg = call.data
    callback_id = call.id
    print("inside stock price")
    bot.answer_callback_query(
        callback_id,
        f"Price of {msg} is {item_list[msg]}",
        show_alert=True,
    )

@frappe.whitelist(allow_guest=True)
def update_address():
    # return {frappe.local.site, frappe.db}
    # print(message)
    frappe.init(site="erpnext.localhost")
    frappe.connect()
    print("****************")
    
    # address = message.json["text"]
    # chat_id = message.from_user.id
    address = "TUP"
    chat_id= 5680055111
    print("-----------------1")
    
        # address = "Tirupur"
        # bot.send_message(message.chat.id, f"Address {address}!")
    doc1 = frappe.new_doc("Address")
    print(doc1)

    doc1.address_line1 = address
    print("-----------------2")
    doc1.city = address
    print("-----------------3")
    doc1.address_title = address
    print("-----------------4")
    doc1.append("links",{
        "link_doctype": "Customer",
        "link_name": "Sowmya"
        }
    )
    print("-----------------")
    doc1.insert()
    print(doc1.name)
    frappe.db.commit()
    # bot.send_message(chat_id, f"Address Created {doc1.name}")
    return {True, doc1.name}

def update_phone(message):
    phone = message.text
    bot.send_message(message.chat.id, f"Phone Number {phone}!")

# def execute(filters=None):
# 	args = {
# 		"account_type": "Receivable",
# 		"naming_by": ["Selling Settings", "cust_master_name"],
# 	}
# 	return ReceivablePayableReport(filters).run(args)




@frappe.whitelist(allow_guest=True)
def pdf_generation(doc, method):
    url = "https://api.telegram.org/bot8299952026:AAE9Fy7JBsXzOIQ6Fy-nw5n4JBJ85yByWHE/sendDocument"

    try:
        html = frappe.get_print(
            doc.doctype, doc.name, print_format="Standard", as_pdf=False
        )

        response = requests.post(
            url,
            data={"chat_id": "5680055111"},
            files={"document": (f"{doc.name}.pdf", html)},
        )

        print(f"{doc.name}.pdf")
        return {"ok": True}
    except Exception as e:
        frappe.log_error("Sending PDF Error", frappe.get_traceback())

        return {"ok": False, "error": str(e)}


# weekly remainder for the balance payment
@frappe.whitelist(allow_guest=True)
def user_details():
    try:
        url = "https://api.telegram.org/bot8299952026:AAE9Fy7JBsXzOIQ6Fy-nw5n4JBJ85yByWHE/getChat?chat_id=5680055111"
        user_msg = requests.get(url)
        data = user_msg.json()
        user_name = data["result"]["first_name"]
        # print(data['result']['first_name'])
        query = frappe.db.sql(
            "Select sum(outstanding_amount) from `tabSales Invoice` where customer = %s",
            user_name,
        )

        url = "https://api.telegram.org/bot8299952026:AAE9Fy7JBsXzOIQ6Fy-nw5n4JBJ85yByWHE/sendMessage"
        new_req = requests.post(
            url,
            {
                "text": f"Hi {user_name}!! You need to pay {query[0][0]}.Thank You!!",
                "chat_id": "5680055111",
            },
        )

        print(query)
        return {"ok": True}
    except Exception as e:
        frappe.log_error("Sending Outstanding amount Error", frappe.get_traceback())

        return {"ok": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def webhook():
    update = json.loads(frappe.request.data)
    bot.process_new_updates([telebot.types.Update.de_json(update)])
    return "OK"