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
from erpnext.accounts.report.accounts_receivable.accounts_receivable import execute

# print("Connected site:", frappe.local.site)
# print("Is connected:", frappe.db)

new_token = frappe.db.get_single_value("Token", "token")
# print(new_token)

bot = telebot.TeleBot(new_token)

item_price = frappe.db.sql(
    "Select item_name, price_list_rate from `tabItem Price` where price_list = 'Standard Selling'"
)
item_list = dict(item_price)


@bot.message_handler(commands=["start"])
def button_handler(message):
    frappe.init(site="erpnext.localhost")
    frappe.connect()
    # print("Start Message ", message)

    chat_id = message.chat.id
    
    cust_chat_id = frappe.get_value(
        "Customer", message.from_user.first_name, "custom_chat_id"
    )
    
    print(cust_chat_id)
    
    if not cust_chat_id:
        cust_chat_id = frappe.db.set_value(
        "Customer", message.from_user.first_name, "custom_chat_id", chat_id
    )
    print(cust_chat_id)
    reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
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
@frappe.whitelist(allow_guest=True)
def handle_report():
    filter_json =frappe._dict( {
        "company": "Google",
        "report_date": "2025-11-12",
        "party_type": "Customer",
        # "party": [message.from_user.full_name],
        "party": "Sowmya",
        "ageing_based_on": "Due Date",
        "calculate_ageing_with": "Report Date",
        "range": "30, 60, 90, 120",
        "customer_group": [],
    })

    # filters = json.loads()
    # return type(filter_json)
    # args = {
    # 	"account_type": "Receivable",
    # 	"naming_by": ["Selling Settings", "cust_master_name"],
    # }
    # # data = ReceivablePayableReport(filters).run(args)

    # data = frappe.get_list("Report","Accounts Receivable", filters, ignore_permissions =True)
    # print
    new_data = execute(filters=filter_json)
    print(new_data)
    return new_data


# def execute(filters=None):
# 	args = {
# 		"account_type": "Receivable",
# 		"naming_by": ["Selling Settings", "cust_master_name"],
# 	}
# 	return ReceivablePayableReport(filters).run(args)


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
    # print("below next step")


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


# @frappe.whitelist(allow_guest=True)
def update_address(message):
    frappe.init(site="erpnext.localhost")
    frappe.connect()

    address = message.json["text"]
    chat_id = message.from_user.id
    doc1 = frappe.new_doc("Address")

    doc1.address_line1 = address
    doc1.city = address
    doc1.address_title = address
    doc1.append(
        "links", {"link_doctype": "Customer", "link_name": message.from_user.first_name}
    )
    doc1.insert()
    frappe.db.commit()
    bot.send_message(chat_id, f"Address Created {doc1.name}")
    return {True, doc1.name}


def update_phone(message):
    frappe.init(site="erpnext.localhost")
    frappe.connect()

    phone = message.json["text"]
    chat_id = message.from_user.id
    doc1 = frappe.new_doc("Contact")

    doc1.first_name = message.from_user.first_name
    # doc1.city = address
    # doc1.address_title = address
    doc1.append("links", {"link_doctype": "Customer", "link_name": "Sowmya"})
    doc1.append("phone_nos", {"phone": phone})

    doc1.insert()
    frappe.db.commit()
    bot.send_message(chat_id, f"Address Created {doc1.name}")
    return {True, doc1.name}


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
    bot.process_new_updates([Update.de_json(update)])
    return "OK"
