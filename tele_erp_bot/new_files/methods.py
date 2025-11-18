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
from datetime import date


# from erpnext.accounts.report.accounts_receivable.accounts_receivable import execute
from frappe.utils.xlsxutils import make_xlsx
from frappe.email.doctype.auto_email_report.auto_email_report import build_xlsx_data

# webhook_URL = "https://uncapable-yawnful-sherryl.ngrok-free.dev/api/method/tele_erp_bot.new_files.methods.webhook"
# print("Connected site:", frappe.local.site)
# print("Is connected:", frappe.db)


new_token = frappe.db.get_single_value("Token", "token")
# print(new_token)
bot = telebot.TeleBot(new_token)
# bot.remove_webhook()
# bot.set_wehook(webhook_URL)
item_price = frappe.db.sql(
	"Select item_name, price_list_rate from `tabItem Price` where price_list = 'Standard Selling'"
)
item_list = dict(item_price)

# glb_chat_id = 0


@bot.message_handler(commands=["start"])
def button_handler(message):
	frappe.init(site="erpnext.localhost")
	frappe.connect()
	chat_id = message.chat.id
	print("Start Message ", message)
	
	cust_chat_id = frappe.get_value(
		"Customer", message.from_user.first_name, "custom_chat_id"
	)

	print(cust_chat_id)

	if not cust_chat_id:
		doc1 = frappe.new_doc("Customer")
		doc1.customer_name =message.from_user.first_name
		doc1.custom_chat_id = chat_id
		doc1.insert()
		
		cust_chat_id = frappe.get_value(
			"Customer", message.from_user.first_name, "custom_chat_id"
		)
		bot.send_message(
		chat_id, f"Hi {message.from_user.first_name}!!!!New Customer Created"
		)
		frappe.db.commit()
	
	

	print(cust_chat_id)
	reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
	reply_keyboard.add(
		"Balance Payment", "Get Payable", "Get Item Price", "Update Profile"
	)
	bot.send_message(
		chat_id, "Check the following keyboard", reply_markup=reply_keyboard
	)


# @frappe.whitelist(allow_guest=True)
# def var():
#     cust_chat_id = frappe.get_value(
#         "Customer", "Sowmya arunachalam", "custom_chat_id"
#     )
#     return cust_chat_id


	# if not cust_chat_id:
	#     cust_chat_id = frappe.db.set_value(
	#         "Customer", "Sowmya", "custom_chat_id", "5680055111"
	#     )
	#     cust_chat_id = frappe.get_value(
	#     "Customer", "Sowmya", "custom_chat_id"
	# )
	# return cust_chat_id
@bot.message_handler(commands=["exit"])
def button_handler(message):
	chat_id = message.chat.id
	print(chat_id)
	bot.send_message(chat_id, "Thank You...", reply_markup=ReplyKeyboardRemove())


@bot.message_handler(func=lambda message: message.text == "Get Payable")
# @frappe.whitelist(allow_guest=True)
def handle_report(message):
	try:
		print(message)
		frappe.init(site="erpnext.localhost")
		frappe.connect()
		# frappe.log_error("------------------------------------")
		# bot.send_message(message.chat.id, "Thank You...")

		_json = {
			"company": "Google",
			"report_date": date.today(),
			"party_type": "Customer",
			"party": [message.from_user.full_name],
			# "party": ["Sowmya"],
			"ageing_based_on": "Due Date",
			"calculate_ageing_with": "Report Date",
			"range": "30, 60, 90, 120",
			"customer_group": [],
		}

		report = frappe.get_doc("Report", "Accounts Receivable")
		# print("Report", report)
		columns, data = report.get_data(filters=_json, as_dict=True)
		# print("COlumns", columns)
		# print("rows", data)
		columns.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))
		# print("After insert column", columns)
		for i in range(len(data)):
			data[i]["idx"] = i + 1
		# print("After insert data", data)

		if len(data) == 0:
			bot.send_message(message.chat.id, "No data in Accounts Receivable")
			
			return None

		report_data = frappe._dict()
		# print("Report Data",report_data)
		report_data["columns"] = columns
		# print("Report Data after columns",report_data)
		report_data["result"] = data
		# print("Report Data after data",report_data)

		# print()
		xlsx_data, column_widths = build_xlsx_data(
			report_data, [], 1, ignore_visible_idx=True
		)
		xlsx_file = make_xlsx(
			xlsx_data, "Auto Email Report", column_widths=column_widths
		)
		# pdf = get_pdf(xlsx_file)
		url = "https://api.telegram.org/bot8299952026:AAE9Fy7JBsXzOIQ6Fy-nw5n4JBJ85yByWHE/sendDocument"
		response = requests.post(
			url,
			data={"chat_id": message.chat.id},
			files={"document": (f"Account Receivable.xlsx", xlsx_file.getvalue())},
		)

		print(f"{message.from_user.full_name}Account Receivable.pdf")
		return response
		# import os
		# frappe.msgprint(f"Saving file to: {os.getcwd()}")
		# with open("report.xlsx", "wb") as f:
		#     f.write(xlsx_file.getvalue())
		# return xlsx_file.getvalue()
		return True
	except Exception as e:
		frappe.log_error("------------------------------------", frappe.get_traceback())


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
	if len(phone)!=10 and phone.isdigit():
		bot.send_message(chat_id, "Enter a Valid phone number...")
		return None
	doc1 = frappe.new_doc("Contact")
	doc1.first_name = message.from_user.first_name
	# doc1.city = address
	# doc1.address_title = address
	doc1.append(
		"links", {"link_doctype": "Customer", "link_name": message.from_user.first_name}
	)
	doc1.append("phone_nos", {"phone": phone})

	doc1.insert()
	frappe.db.commit()
	bot.send_message(chat_id, f"Address Created {doc1.name}")
	return {True, doc1.name}


@frappe.whitelist(allow_guest=True)
def pdf_generation(doc, method):
	url = "https://api.telegram.org/bot8299952026:AAE9Fy7JBsXzOIQ6Fy-nw5n4JBJ85yByWHE/sendDocument"
	print("Inside PDF generation-------------------------------------------")
	try:
		
		html = frappe.get_print(
			doc.doctype, doc.name, print_format="Standard", as_pdf=True
		)
		if doc.doctype == "Payment Entry":
			cust_chat_id = frappe.get_value("Customer", doc.party, "custom_chat_id")
		else:
			cust_chat_id = frappe.get_value("Customer", doc.customer, "custom_chat_id")

  

		if doc.doctype == "Sales Order":
	  
			bot.send_message(
				cust_chat_id,
				f"Hi {doc.customer}!!!\nOrder Details,\nOrder ID : {doc.name}\nDate : {doc.delivery_date}\nTotal Quantity: {doc.total_qty}\nAmount : ₹{doc.total}\nYour order has been Confirmed. Thank You!!",
				"Markdown"
			)
		elif doc.doctype == "Customer":
			bot.send_message(
				cust_chat_id,
				f"Hello {doc.customer_name}!!Customer Account Created..."
				"Markdown"
			)
		elif doc.doctype == "Delivery Note":
			print(cust_chat_id)

			bot.send_message(
				cust_chat_id,
				f"Hi {doc.customer}!!!\nDelivery Note Details,\nDelivery ID : {doc.name}\nDate : {doc.posting_date}\nTotal Quantity: {doc.total_qty}\nAmount : ₹{doc.total}\nYour Delivery Note has been Created. Thank You!!",
				"Markdown"
			)
		elif doc.doctype == "Payment Entry":
			cust_chat_id = frappe.get_value("Customer", doc.party, "custom_chat_id")
			
			print(cust_chat_id)

			bot.send_message(
				cust_chat_id,
				f"Hi {doc.party}!!!\nPayment Details,\nPayment ID : {doc.name}\nPosting Date : {doc.posting_date}\nMode of Payment: {doc.mode_of_payment}\nAmount : ₹{doc.total_allocated_amount}\nYour payment has been completed sucessfully. Thank You!!",
				"Markdown"
			)
		elif doc.doctype == "Sales Invoice":
			bot.send_message(
				cust_chat_id,
				f"Hi {doc.customer}!!!\nInvoice Details,\nInvoice ID : {doc.name}\nPosting Date : {doc.posting_date}\nTotal Quantity: {doc.total_qty}\nAmount : ₹{doc.total}\nYour Invoice has been Confirmed. Thank You!!",
				"Markdown"
			)
		# user_msg = requests.get(url)
		# data = user_msg.json()
		# user_name = data["result"]["first_name"]
		# print(data['result']['first_name'])

		response = requests.post(
			url,
			data={"chat_id": cust_chat_id},
			files={"document": (f"{doc.name}.pdf", html)},
		)

		print(f"{doc.name}.pdf")
		return {"ok": True}
	except Exception as e:
		frappe.log_error("Sending PDF Error", frappe.get_traceback())

		return {"ok": False, "error": str(e)}


@frappe.whitelist(allow_guest=True)
def user_details():
	try:
		frappe.init(site="erpnext.localhost")
		frappe.connect()
		url = f"https://api.telegram.org/bot8299952026:AAE9Fy7JBsXzOIQ6Fy-nw5n4JBJ85yByWHE/getChat"
  
		user_msg = requests.get(url)
		print(user_msg)
		data = user_msg.json()
		print(data)
		user_name = data["result"]["first_name"]
		# print(data['result']['first_name'])
		query = frappe.db.sql(
			"Select sum(outstanding_amount) from `tabSales Invoice` where customer = %s",
			user_name,
		)
		cust_chat_id = frappe.get_value("Customer", user_name, "custom_chat_id")
		url = "https://api.telegram.org/bot8299952026:AAE9Fy7JBsXzOIQ6Fy-nw5n4JBJ85yByWHE/sendMessage"
		new_req = requests.post(
			url,
			{
				"text": f"Hi {user_name}!! You need to pay {query[0][0]}.Thank You!!",
				"chat_id": cust_chat_id,
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


@frappe.whitelist(allow_guest=True)
def sales_order(message):
	try:
		# return type(message)
		print(message)
		# data = json.loads(message)
		data = frappe._dict(message)
		print(data)
		# data = data
		doc1 = frappe.new_doc("Sales Order")
		doc1.customer = data['customer']
		doc1.company = data['company']
		doc1.order_type = "Sales"
		doc1.currency = "INR"
		doc1.price_list = "Standard Selling"
		doc1.delivery_date = data["delivery_date"]

		for item in data["items"]:
				doc1.append("items",{
					"item_code": item["item_code"],
						"item_name": item.get("item_name"),
						"delivery_date": data["delivery_date"],
						"qty": item["qty"],
						"rate": item['rate'],
						"uom": "Nos",
						"uom_conversion_factor": 1,
						"parenttype": "Sales Order"
				})
		doc1.insert()
		frappe.db.commit()
	except Exception as e:
		frappe.logger("Error in Sales Order", frappe.get_traceback())
	