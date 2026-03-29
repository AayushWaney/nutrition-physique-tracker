import customtkinter as ctk
from tkinter import END
import json
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import math

# SETUP
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


# THE PHYSIQUE DASHBOARD ENGINE
def update_physique_dashboard():
    db = load_database()
    valid_dates = [d for d in db.keys() if "Waist_cm" in db[d]]
    if not valid_dates: return

    latest_date = sorted(valid_dates, key=lambda d: datetime.strptime(d, "%d-%m-%Y"))[-1]

    waist = float(db[latest_date].get("Waist_cm", 0))
    neck = float(db[latest_date].get("Neck_cm", 0))
    height = 172  # Placeholder for now

    if waist > 0 and neck > 0 and waist > neck:
        try:
            bf = 495 / (1.0324 - 0.19077 * math.log10(waist - neck) + 0.15456 * math.log10(height)) - 450
            bf_lbl.configure(text=f"Est. Body Fat: {round(bf, 1)} %")
        except ValueError:
            bf_lbl.configure(text="Est. Body Fat: -- %")


# THE ANALYTICS ENGINE
def show_analytics():
    db = load_database()
    dates, calories = [], []

    valid_dates = sorted([d for d in db.keys() if (lambda x: True if datetime.strptime(x, "%d-%m-%Y") else False)(d)])[
        -7:]

    for d in valid_dates:
        dates.append(d[:5])
        day_data = db[d]
        total_cal = sum(float(m["Calories"]) for f, m in day_data.items() if isinstance(m, dict) and "Calories" in m)
        calories.append(total_cal)

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.bar(dates, calories, color='#3498db', alpha=0.7, label='Calories')
    ax1.set_ylabel('Calories', color='#3498db', fontweight='bold')
    plt.title('7-Day Analytics', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.show()


# THE UI ARCHITECTURE
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

window = ctk.CTk()
window.title("My Nutrition Tracker")
window.geometry("600x850")

title_label = ctk.CTkLabel(window, text="Daily Nutrition Tracker", font=("Arial", 24, "bold"))
title_label.pack(pady=(20, 5))

date_entry = ctk.CTkEntry(window, width=250, justify="center")
date_entry.insert(0, datetime.now().strftime("%d-%m-%Y"))
date_entry.pack(pady=(0, 10))

tabview = ctk.CTkTabview(window, width=550, height=580)
tabview.pack(padx=20, pady=10)

tab_food = tabview.add("Food Logger")
tab_nutrients = tabview.add("Nutrients")
tab_body = tabview.add("Body Tracker")
tab_profile = tabview.add("Profile & Goals")

# TAB 1: FOOD LOGGER
dash_frame = ctk.CTkFrame(tab_food, fg_color="transparent")
dash_frame.pack(fill="x", pady=(5, 5))
food_lbl = ctk.CTkLabel(dash_frame, text="CONSUMED\n--", font=("Arial", 14, "bold"))
food_lbl.pack()

input_frame = ctk.CTkFrame(tab_food, fg_color="transparent")
input_frame.pack(pady=5)
meal_var = ctk.StringVar(value="Breakfast")
ctk.CTkOptionMenu(input_frame, variable=meal_var, values=["Breakfast", "Lunch", "Dinner"], width=110).pack(side="left",
                                                                                                           padx=5)
food_entry = ctk.CTkEntry(input_frame, width=220, placeholder_text="e.g., 2 boiled eggs")
food_entry.pack(side="left", padx=5)
ctk.CTkButton(input_frame, text="Add", command=save_entry, width=70).pack(side="left", padx=5)

log_frame = ctk.CTkScrollableFrame(tab_food, width=450, height=160, label_text="Today's Log",
                                   label_font=("Arial", 14, "bold"))
log_frame.pack(pady=(5, 10), fill="both", expand=True)

# Analytics Button
ctk.CTkButton(tab_food, text="📊 View 7-Day Analytics", command=show_analytics, fg_color="#8e44ad",
              hover_color="#9b59b6").pack(pady=(0, 10))

# TAB 2: BODY TRACKER
ctk.CTkLabel(tab_body, text="📊 Physique Dashboard", font=("Arial", 16, "bold"), text_color="#3498db").pack(pady=(10, 5))
bf_lbl = ctk.CTkLabel(tab_body, text="Est. Body Fat:\n-- %", font=("Arial", 14, "bold"), text_color="#f39c12")
bf_lbl.pack(pady=20)

placeholder = ctk.CTkLabel(tab_profile, text="Profile & Targets coming in Day 4...", font=("Arial", 16))
placeholder.pack(pady=50)

calculate_totals()
window.mainloop()