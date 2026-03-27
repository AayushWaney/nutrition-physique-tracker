import customtkinter as ctk


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