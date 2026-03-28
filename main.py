import customtkinter as ctk
from tkinter import END
import json
import requests
from datetime import datetime, timedelta


API_KEY = "API_KEY"
EXERCISE_ENDPOINT = "https://api.calorieninjas.com/v1/nutrition"

DB_PATH = "daily_calories.json"
CUSTOM_FOODS_PATH = "custom_foods.json"


def load_database():
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_database(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=4)


def delete_item(key_to_delete):
    date_to_check = date_entry.get()
    try:
        db = load_database()
        if date_to_check in db:
            db[date_to_check].pop(key_to_delete, None)
            if not db[date_to_check]:
                del db[date_to_check]
            save_database(db)
            calculate_totals()
    except Exception as e:
        print(f"Delete Error: {e}")


def save_entry():
    date = date_entry.get()
    if not date.strip(): return
    food_query = food_entry.get().strip().lower()
    meal_choice = meal_var.get()

    try:
        with open(CUSTOM_FOODS_PATH, "r") as f:
            custom_db = json.load(f)
    except FileNotFoundError:
        custom_db = {}

    if food_query in custom_db:
        macros = custom_db[food_query]
        saved_food_name = f"{meal_choice} - {food_query.title()} (Custom)"
        new_data = {saved_food_name: macros}
    else:
        # Simulate API call
        saved_food_name = f"{meal_choice} - {food_query.title()}"
        new_data = {saved_food_name: {"Calories": 100, "Protein": 10, "Fats": 5, "Carbs": 2}}

    db = load_database()
    if date in db:
        db[date].update(new_data)
    else:
        db[date] = new_data
    save_database(db)
    food_entry.delete(0, END)
    calculate_totals()


def calculate_totals():
    date_to_check = date_entry.get()
    db = load_database()
    for widget in log_frame.winfo_children():
        widget.destroy()

    if date_to_check in db:
        daily_foods = db[date_to_check]
        total_cal = sum(int(m["Calories"]) for f, m in daily_foods.items() if isinstance(m, dict) and "Calories" in m)
        food_lbl.configure(text=f"CONSUMED\n{int(total_cal)}")

        for food, macros in daily_foods.items():
            if isinstance(macros, dict) and "Calories" in macros:
                row_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)
                ctk.CTkLabel(row_frame, text=f"• {food}: {macros['Calories']} kcal", font=("Arial", 14)).pack(
                    side="left", padx=5)
    else:
        ctk.CTkLabel(log_frame, text="No food logged for this date yet.", font=("Arial", 14, "italic")).pack(pady=20)
        food_lbl.configure(text="CONSUMED\n--")


#  THE UI ARCHITECTURE
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

window = ctk.CTk()
window.title("My Nutrition Tracker")
window.geometry("600x850")

title_label = ctk.CTkLabel(window, text="Daily Nutrition Tracker", font=("Arial", 24, "bold"))
title_label.pack(pady=(20, 5))

# Creating the core tab structure
tabview = ctk.CTkTabview(window, width=550, height=580)
tabview.pack(padx=20, pady=10)

tab_food = tabview.add("Food Logger")
tab_nutrients = tabview.add("Nutrients")
tab_body = tabview.add("Body Tracker")
tab_profile = tabview.add("Profile & Goals")

# Temporary placeholder label
placeholder = ctk.CTkLabel(tab_food, text="Food Logger UI coming soon...", font=("Arial", 16))
placeholder.pack(pady=50)

window.mainloop()