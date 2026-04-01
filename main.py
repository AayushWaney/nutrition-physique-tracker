import customtkinter as ctk
from tkinter import END
import json
import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import math
import os
from pathlib import Path
from dotenv import load_dotenv

# SECURE APP FOLDER & ENV
# 1. Create the safe folder
APP_DIR = Path.home() / "NutritionTrackerData"
APP_DIR.mkdir(parents=True, exist_ok=True)

# 2. Tell dotenv to look for the secret file inside that specific folder
ENV_PATH = APP_DIR / ".env"
load_dotenv(ENV_PATH)

# 3. Load the key
API_KEY = os.getenv("CALORIE_API_KEY")
EXERCISE_ENDPOINT = "https://api.calorieninjas.com/v1/nutrition"

# Define the absolute paths for databases
DB_PATH = APP_DIR / "daily_calories.json"
PROFILE_PATH = APP_DIR / "user_profile.json"
CUSTOM_FOODS_PATH = APP_DIR / "custom_foods.json"


# DATABASE HELPER FUNCTIONS
def load_database():
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_database(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=4)


def load_user_profile():
    try:
        with open(PROFILE_PATH, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"Age": 22, "Height": 172, "Weight": 68, "Gender": "Male", "Daily_Goal": 1600}


# DELETE ITEM ENGINE
def delete_item(key_to_delete):
    date_to_check = date_entry.get()
    try:
        db = load_database()
        if date_to_check in db:
            db[date_to_check].pop(key_to_delete, None)

            # If the day is completely empty after deleting, remove the date entirely.
            if not db[date_to_check]:
                del db[date_to_check]

            save_database(db)
            calculate_totals()
    except Exception as e:
        print(f"Delete Error: {e}")


# THE FOOD SAVE FUNCTION
def save_entry():
    date = date_entry.get()
    if not date.strip():
        return

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
        headers = {"X-Api-Key": API_KEY}
        parameters = {"query": food_query}

        try:
            response = requests.get(url=EXERCISE_ENDPOINT, params=parameters, headers=headers)
            response.raise_for_status()
            api_data = response.json()
        except Exception as e:
            print(f"API Error: {e}")
            return

        if not api_data.get("items"):
            print("Food not found in API.")
            return

        total_calories = total_protein = total_fats = total_carbs = 0
        total_fiber = total_sugar = total_sodium = total_cholesterol = 0

        for item in api_data["items"]:
            total_calories += item["calories"]
            total_protein += item["protein_g"]
            total_fats += item["fat_total_g"]
            total_carbs += item["carbohydrates_total_g"]
            total_fiber += item.get("fiber_g", 0)
            total_sugar += item.get("sugar_g", 0)
            total_sodium += item.get("sodium_mg", 0)
            total_cholesterol += item.get("cholesterol_mg", 0)

        saved_food_name = f"{meal_choice} - {food_query.title()}"
        new_data = {
            saved_food_name: {
                "Calories": total_calories, "Protein": total_protein, "Fats": total_fats,
                "Carbs": total_carbs, "Fiber": total_fiber, "Sugar": total_sugar,
                "Sodium": total_sodium, "Cholesterol": total_cholesterol
            }
        }

    db = load_database()
    if date in db:
        db[date].update(new_data)
    else:
        db[date] = new_data
    save_database(db)

    food_entry.delete(0, END)
    calculate_totals()


# BODY MEASUREMENTS SAVE FUNCTION
def save_measurements():
    date = date_entry.get()
    if not date.strip(): return

    daily_weight = weight_entry.get()
    daily_height = height_tracker_entry.get()
    daily_waist = waist_entry.get()
    daily_neck = neck_entry.get()

    new_data = {}
    if daily_weight: new_data["Daily_Weight_kg"] = daily_weight
    if daily_height: new_data["Height_cm"] = daily_height
    if daily_waist: new_data["Waist_cm"] = daily_waist
    if daily_neck: new_data["Neck_cm"] = daily_neck

    if not new_data: return

    db = load_database()
    if date in db:
        db[date].update(new_data)
    else:
        db[date] = new_data
    save_database(db)

    weight_entry.delete(0, END)
    waist_entry.delete(0, END)
    neck_entry.delete(0, END)

    update_physique_dashboard()


# STREAK MATH
def calculate_streak(database, starting_date_str):
    streak = 0
    try:
        target_date = datetime.strptime(starting_date_str, "%d-%m-%Y")
    except ValueError:
        return 0

    # Helper function: A day is only valid if the date exists AND has data inside it
    def has_data(d_str):
        return d_str in database and len(database[d_str]) > 0

    # If today has data, start counting from today.
    if has_data(target_date.strftime("%d-%m-%Y")):
        current_date = target_date
    else:
        # Morning-Proofing: If today is empty, check if yesterday has data before breaking the streak.
        current_date = target_date - timedelta(days=1)
        if not has_data(current_date.strftime("%d-%m-%Y")):
            return 0  # Neither today nor yesterday has data, the streak is truly broken.

    # Loop backwards to count consecutive days
    while True:
        date_str = current_date.strftime("%d-%m-%Y")
        if has_data(date_str):
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break

    return streak


# CALCULATE FUNCTION
def calculate_totals():
    date_to_check = date_entry.get()
    db = load_database()

    for widget in log_frame.winfo_children():
        widget.destroy()

    current_streak = calculate_streak(db, date_to_check)
    streak_label.configure(text=f"🔥 Streak: {current_streak} Days")

    if date_to_check in db:
        daily_foods = db[date_to_check]
        total_cal = total_pro = total_fat = total_carb = 0
        total_fib = total_sug = total_sod = total_chol = 0

        profile = load_user_profile()
        budget = profile["Daily_Goal"]

        for food, macros in daily_foods.items():
            if food in ["Daily_Weight_kg", "Height_cm", "Waist_cm", "Neck_cm"]: continue

            if isinstance(macros, dict) and "Calories" in macros:
                food_cal = int(macros["Calories"])
                total_cal += food_cal
                total_pro += float(macros.get("Protein", 0))
                total_fat += float(macros.get("Fats", 0))
                total_carb += float(macros.get("Carbs", 0))
                total_fib += float(macros.get("Fiber", 0))
                total_sug += float(macros.get("Sugar", 0))
                total_sod += float(macros.get("Sodium", 0))
                total_chol += float(macros.get("Cholesterol", 0))

                row_frame = ctk.CTkFrame(log_frame, fg_color="transparent")
                row_frame.pack(fill="x", pady=2)
                item_lbl = ctk.CTkLabel(row_frame, text=f"• {food}: {food_cal} kcal", font=("Arial", 14),
                                        wraplength=320, justify="left")
                item_lbl.pack(side="left", padx=5)
                del_btn = ctk.CTkButton(row_frame, text="❌", width=30, fg_color="#e74c3c", hover_color="#c0392b",
                                        command=lambda f=food: delete_item(f))
                del_btn.pack(side="right", padx=5)

        remaining = budget - total_cal
        budget_lbl.configure(text=f"BUDGET\n{budget}")
        food_lbl.configure(text=f"CONSUMED\n{int(total_cal)}")

        macro_summary_lbl.configure(
            text=f"Protein: {int(total_pro)}g  |  Fats: {int(total_fat)}g  |  Carbs: {int(total_carb)}g")

        nut_pro_lbl.configure(text=f"Protein: {int(total_pro)} g")
        nut_fat_lbl.configure(text=f"Fats: {int(total_fat)} g")
        nut_carb_lbl.configure(text=f"Carbs: {int(total_carb)} g")
        nut_fib_lbl.configure(text=f"Fiber: {int(total_fib)} g")
        nut_sug_lbl.configure(text=f"Sugar: {int(total_sug)} g")
        nut_sod_lbl.configure(text=f"Sodium: {int(total_sod)} mg")
        nut_chol_lbl.configure(text=f"Cholesterol: {int(total_chol)} mg")

        progress_val = total_cal / budget if budget > 0 else 0
        bar_color = "#2ecc71" if progress_val < 0.85 else "#f39c12" if progress_val < 1.0 else "#e74c3c"

        if remaining >= 0:
            under_lbl.configure(text=f"REMAINING\n{remaining}", text_color=bar_color)
            cal_progress.configure(progress_color=bar_color)
        else:
            under_lbl.configure(text=f"OVER\n{abs(remaining)}", text_color="#e74c3c")
            cal_progress.configure(progress_color="#e74c3c")

        cal_progress.set(min(max(progress_val, 0), 1))

    else:
        ctk.CTkLabel(log_frame, text="No food logged for this date yet.", font=("Arial", 14, "italic")).pack(pady=20)
        cal_progress.set(0)
        budget_lbl.configure(text="BUDGET\n--")
        food_lbl.configure(text="CONSUMED\n--")
        under_lbl.configure(text="REMAINING\n--", text_color="white")
        macro_summary_lbl.configure(text="Protein: 0g  |  Fats: 0g  |  Carbs: 0g")
        nut_pro_lbl.configure(text="Protein: -- g")
        nut_fat_lbl.configure(text="Fats: -- g")
        nut_carb_lbl.configure(text="Carbs: -- g")
        nut_fib_lbl.configure(text="Fiber: -- g")
        nut_sug_lbl.configure(text="Sugar: -- g")
        nut_sod_lbl.configure(text="Sodium: -- mg")
        nut_chol_lbl.configure(text="Cholesterol: -- mg")


# PHYSIQUE DASHBOARD ENGINE
def update_physique_dashboard():
    db = load_database()
    profile = load_user_profile()
    valid_dates = [d for d in db.keys() if "Daily_Weight_kg" in db[d]]

    if not valid_dates: return

    sorted_dates = sorted(valid_dates, key=lambda d: datetime.strptime(d, "%d-%m-%Y"))
    latest_date = sorted_dates[-1]

    current_w = float(db[latest_date]["Daily_Weight_kg"])
    waist = float(db[latest_date].get("Waist_cm", 0))
    neck = float(db[latest_date].get("Neck_cm", 0))
    height = float(db[latest_date].get("Height_cm", profile.get("Height", 172)))

    last_logged_lbl.configure(text=f"Last Logged: {latest_date}")
    curr_wt_lbl.configure(text=f"Current:\n{current_w} kg")

    if waist > 0 and neck > 0 and height > 0 and waist > neck:
        try:
            bf = 495 / (1.0324 - 0.19077 * math.log10(waist - neck) + 0.15456 * math.log10(height)) - 450
            bf_lbl.configure(text=f"Est. Body Fat:\n{round(bf, 1)} %")
        except ValueError:
            bf_lbl.configure(text="Est. Body Fat:\n-- %")
    else:
        bf_lbl.configure(text="Est. Body Fat:\n-- %")

    if len(sorted_dates) >= 2:
        start_w = float(db[sorted_dates[0]]["Daily_Weight_kg"])
        diff = start_w - current_w
        if diff > 0:
            motivation_lbl.configure(text=f"🔥 Dropped {round(diff, 1)} kg since {sorted_dates[0]}!",
                                     text_color="#2ecc71")
        elif diff < 0:
            motivation_lbl.configure(text=f"🥩 Gained {round(abs(diff), 1)} kg since {sorted_dates[0]}.",
                                     text_color="#3498db")
        else:
            motivation_lbl.configure(text="Weight has remained stable.", text_color="#f39c12")
    else:
        motivation_lbl.configure(text="First log saved! Keep logging daily.", text_color="#3498db")


# PROFILE MATH ENGINE
def calculate_targets():
    try:
        age = int(profile_age_entry.get())
        height = float(profile_height_entry.get())
        weight = float(profile_weight_entry.get())
        gender = profile_gender_var.get()

        bmr = (10 * weight) + (6.25 * height) - (5 * age)
        bmr = bmr + 5 if gender == "Male" else bmr - 161
        maintenance = int(bmr * 1.375)

        maint_label.configure(text=f"Maintenance: {maintenance} kcal")
        mild_loss_label.configure(text=f"Lose 0.25kg/wk: {maintenance - 275} kcal")
        agg_loss_label.configure(text=f"Lose 0.5kg/wk: {maintenance - 550} kcal")

        goal_entry.delete(0, END)
        goal_entry.insert(0, str(maintenance - 550))
    except ValueError:
        maint_label.configure(text="Error: Please enter numbers only!")


def save_profile():
    try:
        profile_data = {
            "Age": int(profile_age_entry.get()),
            "Height": float(profile_height_entry.get()),
            "Weight": float(profile_weight_entry.get()),
            "Gender": profile_gender_var.get(),
            "Daily_Goal": int(goal_entry.get())
        }
        with open(PROFILE_PATH, "w") as file:
            json.dump(profile_data, file, indent=4)
        save_profile_btn.configure(text="Profile Saved! ✅", fg_color="#2ecc71")
        update_physique_dashboard()
    except ValueError:
        save_profile_btn.configure(text="Error: Check Inputs", fg_color="#e74c3c")


# THE ANALYTICS ENGINE
def show_analytics():
    db = load_database()
    dates, calories, weights = [], [], []
    profile = load_user_profile()

    valid_dates = sorted(
        [d for d in db.keys() if (lambda x: True if datetime.strptime(x, "%d-%m-%Y") else False)(d) or True])[-7:]

    for d in valid_dates:
        dates.append(d[:5])
        day_data = db[d]
        w = float(day_data.get("Daily_Weight_kg", 0))
        weights.append(w if w > 0 else None)

        total_cal = sum(float(m["Calories"]) for f, m in day_data.items() if isinstance(m, dict) and "Calories" in m)
        calories.append(total_cal)

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.bar(dates, calories, color='#3498db', alpha=0.7, label='Calories')
    ax1.axhline(y=profile["Daily_Goal"], color='r', linestyle='--', linewidth=2, label='Goal')
    ax1.set_ylabel('Calories', color='#3498db', fontweight='bold')

    ax2 = ax1.twinx()
    ax2.plot(dates, weights, color='#2ecc71', marker='o', linewidth=3, markersize=8, label='Weight')
    ax2.set_ylabel('Weight (kg)', color='#2ecc71', fontweight='bold')

    plt.title('7-Day Analytics', fontsize=16, fontweight='bold')
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
    plt.tight_layout()
    plt.show()


# THE UI ARCHITECTURE

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

window = ctk.CTk()
window.title("Daily Nutrition Tracker")
window.geometry("600x850")

if not API_KEY:
    dialog = ctk.CTkInputDialog(text="Enter your free CalorieNinjas API Key to start:", title="First Run Setup")
    API_KEY = dialog.get_input()
    if API_KEY:
        with open(ENV_PATH, "w") as f:
            f.write(f"CALORIE_API_KEY={API_KEY}")


initial_profile = load_user_profile()

title_label = ctk.CTkLabel(window, text="Daily Nutrition Tracker", font=("Arial", 24, "bold"))
title_label.pack(pady=(20, 5))

date_label = ctk.CTkLabel(window, text="Date (DD-MM-YYYY):", font=("Arial", 14))
date_label.pack()
date_entry = ctk.CTkEntry(window, width=250, justify="center")
date_entry.insert(0, datetime.now().strftime("%d-%m-%Y"))
date_entry.pack(pady=(0, 10))

streak_label = ctk.CTkLabel(window, text="🔥 Streak: 0 Days", font=("Arial", 16, "bold"), text_color="#f39c12")
streak_label.pack(pady=(0, 10))

tabview = ctk.CTkTabview(window, width=550, height=580)
tabview.pack(padx=20, pady=10)

tab_food = tabview.add("Food Logger")
tab_nutrients = tabview.add("Nutrients")
tab_body = tabview.add("Body Tracker")
tab_profile = tabview.add("Profile & Goals")

# TAB 1: FOOD LOGGER
dash_frame = ctk.CTkFrame(tab_food, fg_color="transparent")
dash_frame.pack(fill="x", pady=(5, 5))
dash_frame.grid_columnconfigure((0, 4), weight=1)
budget_lbl = ctk.CTkLabel(dash_frame, text="BUDGET\n--", font=("Arial", 14, "bold"), text_color="#3498db")
budget_lbl.grid(row=0, column=1, padx=20)
food_lbl = ctk.CTkLabel(dash_frame, text="CONSUMED\n--", font=("Arial", 14, "bold"))
food_lbl.grid(row=0, column=2, padx=20)
under_lbl = ctk.CTkLabel(dash_frame, text="REMAINING\n--", font=("Arial", 14, "bold"), text_color="#2ecc71")
under_lbl.grid(row=0, column=3, padx=20)

cal_progress = ctk.CTkProgressBar(tab_food, width=450, height=12, progress_color="#2ecc71")
cal_progress.set(0)
cal_progress.pack(pady=(0, 5))

macro_summary_lbl = ctk.CTkLabel(tab_food, text="Protein: 0g  |  Fats: 0g  |  Carbs: 0g", font=("Arial", 12, "bold"),
                                 text_color="gray")
macro_summary_lbl.pack(pady=(0, 15))

input_frame = ctk.CTkFrame(tab_food, fg_color="transparent")
input_frame.pack(pady=5)
meal_var = ctk.StringVar(value="Breakfast")
ctk.CTkOptionMenu(input_frame, variable=meal_var, values=["Breakfast", "Lunch", "Dinner", "Snack"], width=110).grid(
    row=0, column=0, padx=5)
food_entry = ctk.CTkEntry(input_frame, width=220, placeholder_text="e.g., 2 boiled eggs")
food_entry.grid(row=0, column=1, padx=5)
ctk.CTkButton(input_frame, text="Add", command=save_entry, width=70).grid(row=0, column=2, padx=5)
ctk.CTkButton(tab_food, text="🔄 Refresh Data", command=calculate_totals, fg_color="#27ae60",
              hover_color="#2ecc71").pack(pady=10)

log_frame = ctk.CTkScrollableFrame(tab_food, width=450, height=160, label_text="Today's Log",
                                   label_font=("Arial", 14, "bold"))
log_frame.pack(pady=(5, 10), fill="both", expand=True)

ctk.CTkButton(tab_food, text="📊 View 7-Day Analytics", command=show_analytics, fg_color="#8e44ad",
              hover_color="#9b59b6").pack(pady=(0, 10))

# TAB 1.5: NUTRIENT BREAKDOWN
ctk.CTkLabel(tab_nutrients, text="📊 Daily Nutrient Breakdown", font=("Arial", 18, "bold"), text_color="#3498db").pack(
    pady=(20, 10))
mac_frame = ctk.CTkFrame(tab_nutrients, fg_color="#2c3e50", corner_radius=10)
mac_frame.pack(fill="x", padx=40, pady=10)
ctk.CTkLabel(mac_frame, text="Macronutrients", font=("Arial", 16, "bold", "underline")).pack(pady=(10, 5))
nut_pro_lbl = ctk.CTkLabel(mac_frame, text="Protein: -- g", font=("Arial", 14, "bold"), text_color="#2ecc71")
nut_pro_lbl.pack(pady=2)
nut_fat_lbl = ctk.CTkLabel(mac_frame, text="Fats: -- g", font=("Arial", 14, "bold"), text_color="#e74c3c")
nut_fat_lbl.pack(pady=2)
nut_carb_lbl = ctk.CTkLabel(mac_frame, text="Carbs: -- g", font=("Arial", 14, "bold"), text_color="#f39c12")
nut_carb_lbl.pack(pady=(2, 10))

mic_frame = ctk.CTkFrame(tab_nutrients, fg_color="#2c3e50", corner_radius=10)
mic_frame.pack(fill="x", padx=40, pady=10)
ctk.CTkLabel(mic_frame, text="Micronutrients", font=("Arial", 16, "bold", "underline")).pack(pady=(10, 5))
nut_fib_lbl = ctk.CTkLabel(mic_frame, text="Fiber: -- g", font=("Arial", 14))
nut_fib_lbl.pack(pady=2)
nut_sug_lbl = ctk.CTkLabel(mic_frame, text="Sugar: -- g", font=("Arial", 14))
nut_sug_lbl.pack(pady=2)
nut_sod_lbl = ctk.CTkLabel(mic_frame, text="Sodium: -- mg", font=("Arial", 14))
nut_sod_lbl.pack(pady=2)
nut_chol_lbl = ctk.CTkLabel(mic_frame, text="Cholesterol: -- mg", font=("Arial", 14))
nut_chol_lbl.pack(pady=(2, 10))

# TAB 2: BODY TRACKER
body_input_frame = ctk.CTkFrame(tab_body, fg_color="transparent")
body_input_frame.pack(pady=(15, 5))

weight_label = ctk.CTkLabel(body_input_frame, text="Current Weight (kg):", font=("Arial", 14))
weight_label.grid(row=0, column=0, padx=15, pady=10, sticky="e")
weight_entry = ctk.CTkEntry(body_input_frame, width=200, placeholder_text="e.g., 68")
weight_entry.grid(row=0, column=1, padx=15, pady=10, sticky="w")

height_tracker_label = ctk.CTkLabel(body_input_frame, text="Height (cm):", font=("Arial", 14))
height_tracker_label.grid(row=1, column=0, padx=15, pady=10, sticky="e")
height_tracker_entry = ctk.CTkEntry(body_input_frame, width=200, placeholder_text="e.g., 172.0")
height_tracker_entry.grid(row=1, column=1, padx=15, pady=10, sticky="w")

waist_label = ctk.CTkLabel(body_input_frame, text="Waist (cm):", font=("Arial", 14))
waist_label.grid(row=2, column=0, padx=15, pady=10, sticky="e")
waist_entry = ctk.CTkEntry(body_input_frame, width=200, placeholder_text="e.g., 80")
waist_entry.grid(row=2, column=1, padx=15, pady=10, sticky="w")

neck_label = ctk.CTkLabel(body_input_frame, text="Neck (cm):", font=("Arial", 14))
neck_label.grid(row=3, column=0, padx=15, pady=10, sticky="e")
neck_entry = ctk.CTkEntry(body_input_frame, width=200, placeholder_text="e.g., 38")
neck_entry.grid(row=3, column=1, padx=15, pady=10, sticky="w")

ctk.CTkButton(tab_body, text="Save Measurements", command=save_measurements, font=("Arial", 14, "bold")).pack(
    pady=(10, 15))

progress_frame = ctk.CTkFrame(tab_body, fg_color="#2c3e50", corner_radius=10)
progress_frame.pack(fill="x", padx=30, pady=5)
ctk.CTkLabel(progress_frame, text="📊 Physique Dashboard", font=("Arial", 16, "bold"), text_color="#3498db").pack(
    pady=(10, 5))
last_logged_lbl = ctk.CTkLabel(progress_frame, text="Last Logged: --", font=("Arial", 12))
last_logged_lbl.pack()

stats_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
stats_frame.pack(pady=5)
curr_wt_lbl = ctk.CTkLabel(stats_frame, text="Current:\n-- kg", font=("Arial", 14, "bold"))
curr_wt_lbl.grid(row=0, column=0, padx=30)
bf_lbl = ctk.CTkLabel(stats_frame, text="Est. Body Fat:\n-- %", font=("Arial", 14, "bold"), text_color="#f39c12")
bf_lbl.grid(row=0, column=1, padx=30)
motivation_lbl = ctk.CTkLabel(progress_frame, text="Save measurements to track progress!", font=("Arial", 14, "italic"),
                              text_color="#2ecc71", wraplength=400)
motivation_lbl.pack(pady=(10, 15))

# TAB 3: PROFILE & GOALS
profile_age_label = ctk.CTkLabel(tab_profile, text="Age:", font=("Arial", 14))
profile_age_label.grid(row=0, column=0, padx=20, pady=10, sticky="e")
profile_age_entry = ctk.CTkEntry(tab_profile, width=150)
profile_age_entry.grid(row=0, column=1, padx=20, pady=10, sticky="w")

profile_height_label = ctk.CTkLabel(tab_profile, text="Height (cm):", font=("Arial", 14))
profile_height_label.grid(row=1, column=0, padx=20, pady=10, sticky="e")
profile_height_entry = ctk.CTkEntry(tab_profile, width=150)
profile_height_entry.grid(row=1, column=1, padx=20, pady=10, sticky="w")

profile_weight_label = ctk.CTkLabel(tab_profile, text="Current Weight (kg):", font=("Arial", 14))
profile_weight_label.grid(row=2, column=0, padx=20, pady=10, sticky="e")
profile_weight_entry = ctk.CTkEntry(tab_profile, width=150)
profile_weight_entry.grid(row=2, column=1, padx=20, pady=10, sticky="w")

profile_gender_label = ctk.CTkLabel(tab_profile, text="Gender:", font=("Arial", 14))
profile_gender_label.grid(row=3, column=0, padx=20, pady=10, sticky="e")
profile_gender_var = ctk.StringVar(value="Male")
ctk.CTkOptionMenu(tab_profile, variable=profile_gender_var, values=["Male", "Female"]).grid(row=3, column=1, padx=20,
                                                                                            pady=10, sticky="w")

ctk.CTkButton(tab_profile, text="Calculate My Targets", command=calculate_targets, fg_color="#e67e22",
              hover_color="#d35400", font=("Arial", 14, "bold")).grid(row=4, column=0, columnspan=2, pady=(20, 10))
maint_label = ctk.CTkLabel(tab_profile, text="Maintenance: -- kcal", font=("Arial", 14))
maint_label.grid(row=5, column=0, columnspan=2, pady=(5, 2))
mild_loss_label = ctk.CTkLabel(tab_profile, text="Lose 0.25kg/wk: -- kcal", font=("Arial", 14))
mild_loss_label.grid(row=6, column=0, columnspan=2, pady=(2, 2))
agg_loss_label = ctk.CTkLabel(tab_profile, text="Lose 0.5kg/wk: -- kcal", font=("Arial", 14))
agg_loss_label.grid(row=7, column=0, columnspan=2, pady=(2, 10))

goal_label = ctk.CTkLabel(tab_profile, text="Set Daily Calorie Target:", font=("Arial", 16, "bold"),
                          text_color="#3498db")
goal_label.grid(row=8, column=0, padx=20, pady=15, sticky="e")
goal_entry = ctk.CTkEntry(tab_profile, width=150)
goal_entry.grid(row=8, column=1, padx=20, pady=15, sticky="w")
save_profile_btn = ctk.CTkButton(tab_profile, text="Save Profile", command=save_profile, font=("Arial", 14, "bold"))
save_profile_btn.grid(row=9, column=0, columnspan=2, pady=(10, 20))

# AUTO-FILL SECTION
profile_age_entry.insert(0, str(initial_profile["Age"]))
profile_height_entry.insert(0, str(initial_profile["Height"]))
profile_weight_entry.insert(0, str(initial_profile["Weight"]))
profile_gender_var.set(initial_profile["Gender"])
goal_entry.insert(0, str(initial_profile["Daily_Goal"]))

calculate_totals()
update_physique_dashboard()
window.mainloop()