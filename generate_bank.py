#!/usr/bin/env python3
"""Builds the fixed 50-tool bank and 20 scenarios used by run_experiment.py.

Deterministic, hand-authored content (no randomness here) -- the only
randomness in the whole experiment is the per-scenario decoy *fill order*
beyond each scenario's near-neighbor tools, which run_experiment.py seeds
explicitly for reproducibility.
"""
import json
import os

HERE = os.path.dirname(__file__)


def tool(name, description, params):
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": params,
            "required": list(params.keys()),
        },
    }


def p(desc, type_="string"):
    return {"type": type_, "description": desc}


# 50 tools across 15 everyday-assistant domains. Several domains deliberately
# contain 3-4 near-neighbor tools (e.g. send_email / draft_email / schedule_email
# / forward_email) so that even the 5-tool condition can include genuine
# confusable neighbors for the scenario under test, not just random dilution.
TOOLS = [
    # Email (4)
    tool("send_email", "Send an email immediately to one or more recipients.",
         {"to": p("recipient email address"), "subject": p("email subject"), "body": p("email body")}),
    tool("draft_email", "Save an email as a draft without sending it.",
         {"to": p("recipient email address"), "subject": p("email subject"), "body": p("email body")}),
    tool("schedule_email", "Send an email at a specific future date and time.",
         {"to": p("recipient email address"), "subject": p("email subject"), "send_at": p("ISO 8601 datetime")}),
    tool("forward_email", "Forward an existing email thread to a new recipient.",
         {"thread_id": p("ID of the email thread to forward"), "to": p("recipient email address")}),
    # Messaging (3)
    tool("send_sms", "Send a text message to a phone number.",
         {"phone_number": p("recipient phone number"), "message": p("message text")}),
    tool("send_slack_message", "Post a message to a Slack channel or user.",
         {"channel": p("Slack channel or user ID"), "message": p("message text")}),
    tool("send_whatsapp_message", "Send a WhatsApp message to a contact.",
         {"contact": p("WhatsApp contact name or number"), "message": p("message text")}),
    # Calendar (4)
    tool("create_calendar_event", "Create a new event on the user's calendar.",
         {"title": p("event title"), "start_time": p("ISO 8601 start datetime"), "duration_minutes": p("duration in minutes", "integer")}),
    tool("reschedule_calendar_event", "Move an existing calendar event to a new time.",
         {"event_id": p("ID of the event to move"), "new_start_time": p("ISO 8601 new start datetime")}),
    tool("cancel_calendar_event", "Cancel and remove an existing calendar event.",
         {"event_id": p("ID of the event to cancel")}),
    tool("check_calendar_availability", "Check whether the user is free during a given time window.",
         {"start_time": p("ISO 8601 window start"), "end_time": p("ISO 8601 window end")}),
    # Reminders / todos (3)
    tool("set_reminder", "Set a one-time reminder for a specific time.",
         {"text": p("reminder text"), "remind_at": p("ISO 8601 datetime")}),
    tool("create_todo", "Add a new item to the user's to-do list.",
         {"text": p("to-do item text"), "due_date": p("ISO 8601 due date, optional")}),
    tool("mark_todo_complete", "Mark an existing to-do item as done.",
         {"todo_id": p("ID of the to-do item")}),
    # Weather (3)
    tool("get_current_weather", "Get the current weather conditions for a city.",
         {"city": p("city name")}),
    tool("get_weather_forecast", "Get a multi-day weather forecast for a city.",
         {"city": p("city name"), "days": p("number of days to forecast", "integer")}),
    tool("get_air_quality_index", "Get the current air quality index for a city.",
         {"city": p("city name")}),
    # Currency / finance (3)
    tool("convert_currency", "Convert an amount from one currency to another using the current exchange rate.",
         {"amount": p("amount to convert", "number"), "from_currency": p("source currency code, e.g. USD"), "to_currency": p("target currency code, e.g. INR")}),
    tool("get_stock_price", "Get the current trading price of a stock ticker.",
         {"ticker": p("stock ticker symbol")}),
    tool("get_exchange_rate", "Get the current exchange rate between two currencies without converting an amount.",
         {"from_currency": p("source currency code"), "to_currency": p("target currency code")}),
    # Translation / language (2)
    tool("translate_text", "Translate a piece of text from one language to another.",
         {"text": p("text to translate"), "target_language": p("target language name or code")}),
    tool("detect_language", "Detect the language a piece of text is written in.",
         {"text": p("text to analyze")}),
    # Maps / directions (3)
    tool("get_directions", "Get driving or walking directions between two locations.",
         {"origin": p("starting location"), "destination": p("destination location")}),
    tool("get_travel_time", "Estimate travel time between two locations for a given mode of transport.",
         {"origin": p("starting location"), "destination": p("destination location"), "mode": p("transport mode: driving, walking, or transit")}),
    tool("find_nearby_places", "Find places of a given category near a location.",
         {"location": p("location to search near"), "category": p("place category, e.g. restaurant, pharmacy")}),
    # Unit conversion / calculation (2)
    tool("convert_units", "Convert a quantity from one unit of measurement to another.",
         {"value": p("numeric value", "number"), "from_unit": p("source unit"), "to_unit": p("target unit")}),
    tool("calculate_expression", "Evaluate a numeric or mathematical expression.",
         {"expression": p("math expression to evaluate")}),
    # Search / web (2)
    tool("web_search", "Search the public web for information on a query.",
         {"query": p("search query")}),
    tool("search_news", "Search for recent news articles on a topic.",
         {"topic": p("news topic to search for")}),
    # Files / storage (3)
    tool("upload_file", "Upload a local file to cloud storage.",
         {"file_path": p("local path of the file to upload"), "destination_folder": p("destination folder name")}),
    tool("share_file", "Share an existing cloud file with another user.",
         {"file_id": p("ID of the file to share"), "recipient_email": p("email of the person to share with")}),
    tool("delete_file", "Permanently delete a file from cloud storage.",
         {"file_id": p("ID of the file to delete")}),
    # Contacts (2)
    tool("add_contact", "Add a new contact to the address book.",
         {"name": p("contact name"), "phone_or_email": p("phone number or email address")}),
    tool("find_contact", "Look up an existing contact by name.",
         {"name": p("name to search for")}),
    # Notes (2)
    tool("create_note", "Create a new text note.",
         {"title": p("note title"), "content": p("note content")}),
    tool("append_to_note", "Append text to an existing note.",
         {"note_id": p("ID of the note"), "text": p("text to append")}),
    # Music / media (2)
    tool("play_music", "Play a song, artist, or playlist on the connected speaker.",
         {"query": p("song, artist, or playlist name")}),
    tool("set_volume", "Set the playback volume level.",
         {"level": p("volume level from 0 to 100", "integer")}),
    # Smart home (3)
    tool("set_thermostat_temperature", "Set the target temperature on a smart thermostat.",
         {"temperature": p("target temperature in Celsius", "number")}),
    tool("toggle_smart_light", "Turn a smart light on or off.",
         {"room": p("room name"), "state": p("on or off")}),
    tool("lock_smart_door", "Lock or unlock a smart door lock.",
         {"door": p("door name"), "state": p("lock or unlock")}),
    # Timezone (2)
    tool("get_current_time", "Get the current local time in a given timezone or city.",
         {"location": p("city or timezone name")}),
    tool("convert_timezone", "Convert a specific time from one timezone to another.",
         {"time": p("time to convert"), "from_timezone": p("source timezone"), "to_timezone": p("target timezone")}),
    # Shopping (2)
    tool("track_order", "Track the delivery status of an existing order.",
         {"order_id": p("order ID to track")}),
    tool("add_to_cart", "Add a product to the shopping cart.",
         {"product_name": p("name of the product"), "quantity": p("quantity to add", "integer")}),
    # Spreadsheet / data (2)
    tool("create_spreadsheet_row", "Append a new row to a spreadsheet.",
         {"sheet_id": p("spreadsheet ID"), "values": p("comma-separated row values")}),
    tool("get_spreadsheet_cell", "Read the value of a specific spreadsheet cell.",
         {"sheet_id": p("spreadsheet ID"), "cell": p("cell reference, e.g. A1")}),
    # Misc (3)
    tool("set_alarm", "Set an alarm for a specific time.",
         {"time": p("alarm time, e.g. 07:30")}),
    tool("flip_coin", "Flip a virtual coin and return heads or tails.",
         {}),
    tool("roll_dice", "Roll a dice with a given number of sides.",
         {"sides": p("number of sides on the dice", "integer")}),
]

assert len(TOOLS) == 50, f"expected 50 tools, got {len(TOOLS)}"
TOOL_NAMES = [t["name"] for t in TOOLS]
assert len(set(TOOL_NAMES)) == 50, "duplicate tool name"

# 20 scenarios. Each names its correct target tool and 2-4 "near_neighbors" --
# tools from the bank above that are genuinely plausible for the same request,
# so even the 5-tool condition contains real confusion risk, not just an easy
# target plus random noise. This matches ToolChoiceConfusion's own definition
# of the failure mode: tools that are "plausible but not appropriate."
SCENARIOS = [
    {"id": 1, "request": "Email Priya the Q3 numbers right now, subject 'Q3 Numbers'.",
     "target": "send_email", "near_neighbors": ["draft_email", "schedule_email", "forward_email"]},
    {"id": 2, "request": "Don't send it yet, just save the Q3 numbers email as a draft for Priya.",
     "target": "draft_email", "near_neighbors": ["send_email", "schedule_email", "forward_email"]},
    {"id": 3, "request": "Send that email to Priya at 9am tomorrow, not right now.",
     "target": "schedule_email", "near_neighbors": ["send_email", "draft_email"]},
    {"id": 4, "request": "Text Rohan that I'm running 10 minutes late.",
     "target": "send_sms", "near_neighbors": ["send_whatsapp_message", "send_slack_message"]},
    {"id": 5, "request": "Post in the #launch Slack channel that the build passed CI.",
     "target": "send_slack_message", "near_neighbors": ["send_sms", "send_whatsapp_message"]},
    {"id": 6, "request": "Book a 30-minute call with Priya next Tuesday at 3pm.",
     "target": "create_calendar_event", "near_neighbors": ["check_calendar_availability", "reschedule_calendar_event"]},
    {"id": 7, "request": "Move my 3pm Tuesday call with Priya to Wednesday at 11am instead.",
     "target": "reschedule_calendar_event", "near_neighbors": ["create_calendar_event", "cancel_calendar_event"]},
    {"id": 8, "request": "Cancel my 3pm Tuesday call with Priya, it's not happening anymore.",
     "target": "cancel_calendar_event", "near_neighbors": ["reschedule_calendar_event", "create_calendar_event"]},
    {"id": 9, "request": "Am I free Thursday afternoon between 2 and 5?",
     "target": "check_calendar_availability", "near_neighbors": ["create_calendar_event", "get_current_time"]},
    {"id": 10, "request": "Remind me to call the landlord at 6pm today.",
     "target": "set_reminder", "near_neighbors": ["create_todo", "set_alarm"]},
    {"id": 11, "request": "Add 'renew passport' to my to-do list, no specific deadline.",
     "target": "create_todo", "near_neighbors": ["set_reminder", "create_note"]},
    {"id": 12, "request": "What's the weather like in Tokyo right now?",
     "target": "get_current_weather", "near_neighbors": ["get_weather_forecast", "get_air_quality_index"]},
    {"id": 13, "request": "Give me the 5-day weather forecast for Tokyo.",
     "target": "get_weather_forecast", "near_neighbors": ["get_current_weather", "get_air_quality_index"]},
    {"id": 14, "request": "Convert 500 US dollars to Indian rupees.",
     "target": "convert_currency", "near_neighbors": ["get_exchange_rate", "get_stock_price"]},
    {"id": 15, "request": "What's the current exchange rate from USD to INR, I don't have an amount yet.",
     "target": "get_exchange_rate", "near_neighbors": ["convert_currency", "get_stock_price"]},
    {"id": 16, "request": "Translate 'where is the nearest pharmacy' into Spanish.",
     "target": "translate_text", "near_neighbors": ["detect_language", "find_nearby_places"]},
    {"id": 17, "request": "How long will it take to drive from my hotel to the airport right now?",
     "target": "get_travel_time", "near_neighbors": ["get_directions", "find_nearby_places"]},
    {"id": 18, "request": "Find pharmacies near my current hotel.",
     "target": "find_nearby_places", "near_neighbors": ["get_directions", "get_travel_time"]},
    {"id": 19, "request": "Convert 12 kilometers into miles.",
     "target": "convert_units", "near_neighbors": ["calculate_expression", "get_travel_time"]},
    {"id": 20, "request": "Track my order, the ID is ORD-48213.",
     "target": "track_order", "near_neighbors": ["add_to_cart", "find_contact"]},
]

assert len(SCENARIOS) == 20
for s in SCENARIOS:
    assert s["target"] in TOOL_NAMES, s
    for n in s["near_neighbors"]:
        assert n in TOOL_NAMES, n

if __name__ == "__main__":
    with open(os.path.join(HERE, "tools_bank.json"), "w") as f:
        json.dump(TOOLS, f, indent=2)
    with open(os.path.join(HERE, "scenarios.json"), "w") as f:
        json.dump(SCENARIOS, f, indent=2)
    print(f"Wrote {len(TOOLS)} tools and {len(SCENARIOS)} scenarios.")
