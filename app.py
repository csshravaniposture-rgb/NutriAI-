from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import re
import os
import json
 
from google import genai
from google.genai import types
 
 
app = Flask(__name__)
 
# =========================================================
# APP CONFIGURATION
# =========================================================
 
app.secret_key = os.environ.get(
    "NUTRIAI_SECRET_KEY",
    "nutriai-secret-key"
)
 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///nutriai.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
 
db = SQLAlchemy(app)
# =========================================================
# GEMINI AI CONFIGURATION
# =========================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

gemini_client = None

if GEMINI_API_KEY:
    gemini_client = genai.Client(
        api_key=GEMINI_API_KEY
    )
else:
    print("WARNING: GEMINI_API_KEY is not set.")
 
 
# =========================================================
# DATABASE MODELS
# =========================================================
 
class User(db.Model):
 
    id = db.Column(db.Integer, primary_key=True)
 
    name = db.Column(
        db.String(100),
        nullable=False
    )
 
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )
 
    password = db.Column(
        db.String(200),
        nullable=False
    )
 
    age = db.Column(db.Integer)
 
    height = db.Column(db.Float)
 
    weight = db.Column(db.Float)
 
    diet = db.Column(
        db.String(50)
    )
 
    goal = db.Column(
        db.String(50)
    )
 
 
class GroceryItem(db.Model):
 
    id = db.Column(
        db.Integer,
        primary_key=True
    )
 
    item = db.Column(
        db.String(100),
        nullable=False
    )
 
    quantity = db.Column(
        db.String(50),
        nullable=False
    )
 
    price = db.Column(
        db.Float,
        nullable=False
    )
 
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )
 
 
class MealProgress(db.Model):
 
    id = db.Column(
        db.Integer,
        primary_key=True
    )
 
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )
 
    meal_type = db.Column(
        db.String(50),
        nullable=False
    )
 
    food = db.Column(
        db.String(255),
        nullable=False
    )
 
    cost = db.Column(
        db.Float,
        default=0
    )
 
    completed = db.Column(
        db.Boolean,
        default=False
    )
 
    date = db.Column(
        db.Date,
        nullable=False
    )
    
# =========================================================
# AI GENERATED MEAL MODEL
# =========================================================
 
class GeneratedMeal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
 
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )
 
    meal_type = db.Column(
        db.String(50),
        nullable=False
    )
 
    name = db.Column(
        db.String(255),
        nullable=False
    )
 
    ingredients = db.Column(
        db.Text,
        nullable=False
    )
 
    instructions = db.Column(
        db.Text,
        nullable=False
    )
 
    calories = db.Column(
        db.Float,
        default=0
    )
 
    protein = db.Column(
        db.Float,
        default=0
    )
 
    carbs = db.Column(
        db.Float,
        default=0
    )
 
    fat = db.Column(
        db.Float,
        default=0
    )
 
    cost = db.Column(
        db.Float,
        default=0
    )
 
    date = db.Column(
        db.Date,
        nullable=False
    )
 
 
 
 
# =========================================================
# CREATE DATABASE
# =========================================================
 
with app.app_context():
    db.create_all()
 
# =========================================================
# SIMPLE INDIAN MEAL DATABASE
# =========================================================
 
vegetarian = [
 
    # -------------------------
    # BREAKFAST
    # -------------------------
 
    {
        "type": "Breakfast",
        "food": "Vegetable Poha + Tea",
        "cost": 25
    },
 
    {
        "type": "Breakfast",
        "food": "2 Idli + Sambar",
        "cost": 30
    },
 
    {
        "type": "Breakfast",
        "food": "Vegetable Upma",
        "cost": 25
    },
 
    {
        "type": "Breakfast",
        "food": "2 Roti + Curd",
        "cost": 30
    },
 
    {
        "type": "Breakfast",
        "food": "Besan Chilla + Curd",
        "cost": 35
    },
 
    # -------------------------
    # LUNCH
    # -------------------------
 
    {
        "type": "Lunch",
        "food": "Dal + Rice + Cucumber",
        "cost": 45
    },
 
    {
        "type": "Lunch",
        "food": "2 Roti + Dal + Sabzi",
        "cost": 50
    },
 
    {
        "type": "Lunch",
        "food": "Rajma Rice",
        "cost": 50
    },
 
    {
        "type": "Lunch",
        "food": "Vegetable Khichdi + Curd",
        "cost": 45
    },
 
    {
        "type": "Lunch",
        "food": "2 Roti + Chana Masala",
        "cost": 50
    },
 
    # -------------------------
    # SNACK
    # -------------------------
 
    {
        "type": "Snack",
        "food": "Banana + Roasted Chana",
        "cost": 20
    },
 
    {
        "type": "Snack",
        "food": "Sprouts Chaat",
        "cost": 25
    },
 
    {
        "type": "Snack",
        "food": "Roasted Makhana",
        "cost": 30
    },
 
    {
        "type": "Snack",
        "food": "Fruit Bowl",
        "cost": 30
    },
 
    {
        "type": "Snack",
        "food": "Peanuts + Tea",
        "cost": 20
    },
 
    # -------------------------
    # DINNER
    # -------------------------
 
    {
        "type": "Dinner",
        "food": "2 Roti + Dal + Sabzi",
        "cost": 50
    },
 
    {
        "type": "Dinner",
        "food": "Moong Dal Khichdi + Curd",
        "cost": 45
    },
 
    {
        "type": "Dinner",
        "food": "Vegetable Pulao + Raita",
        "cost": 50
    },
 
    {
        "type": "Dinner",
        "food": "2 Roti + Paneer Bhurji",
        "cost": 65
    },
 
    {
        "type": "Dinner",
        "food": "Dal + Rice + Salad",
        "cost": 45
    }
]
 
 
non_vegetarian = [
 
    # -------------------------
    # BREAKFAST
    # -------------------------
 
    {
        "type": "Breakfast",
        "food": "2 Boiled Eggs + 2 Roti",
        "cost": 35
    },
 
    {
        "type": "Breakfast",
        "food": "Egg Bhurji + 2 Roti",
        "cost": 40
    },
 
    {
        "type": "Breakfast",
        "food": "2 Egg Omelette + Toast",
        "cost": 40
    },
 
    # -------------------------
    # LUNCH
    # -------------------------
 
    {
        "type": "Lunch",
        "food": "Chicken Curry + Rice",
        "cost": 80
    },
 
    {
        "type": "Lunch",
        "food": "Chicken Curry + 2 Roti",
        "cost": 85
    },
 
    {
        "type": "Lunch",
        "food": "Egg Curry + Rice",
        "cost": 55
    },
 
    {
        "type": "Lunch",
        "food": "Chicken Pulao + Raita",
        "cost": 75
    },
 
    # -------------------------
    # SNACK
    # -------------------------
 
    {
        "type": "Snack",
        "food": "Boiled Eggs + Fruit",
        "cost": 35
    },
 
    {
        "type": "Snack",
        "food": "Egg Sandwich",
        "cost": 40
    },
 
    {
        "type": "Snack",
        "food": "Roasted Chana + Banana",
        "cost": 20
    },
 
    # -------------------------
    # DINNER
    # -------------------------
 
    {
        "type": "Dinner",
        "food": "Chicken Curry + 2 Roti",
        "cost": 85
    },
 
    {
        "type": "Dinner",
        "food": "Egg Curry + 2 Roti",
        "cost": 60
    },
 
    {
        "type": "Dinner",
        "food": "Chicken Rice Bowl",
        "cost": 75
    },
 
    {
        "type": "Dinner",
        "food": "Egg Bhurji + 2 Roti + Salad",
        "cost": 55
    }
]
 
 
vegan = [
 
    # -------------------------
    # BREAKFAST
    # -------------------------
 
    {
        "type": "Breakfast",
        "food": "Vegetable Poha",
        "cost": 25
    },
 
    {
        "type": "Breakfast",
        "food": "Vegetable Upma",
        "cost": 25
    },
 
    {
        "type": "Breakfast",
        "food": "Besan Chilla + Green Chutney",
        "cost": 30
    },
 
    {
        "type": "Breakfast",
        "food": "2 Roti + Vegetable Sabzi",
        "cost": 35
    },
 
    # -------------------------
    # LUNCH
    # -------------------------
 
    {
        "type": "Lunch",
        "food": "Dal + Rice + Salad",
        "cost": 45
    },
 
    {
        "type": "Lunch",
        "food": "Rajma Rice",
        "cost": 50
    },
 
    {
        "type": "Lunch",
        "food": "Chana Masala + 2 Roti",
        "cost": 50
    },
 
    {
        "type": "Lunch",
        "food": "Vegetable Khichdi",
        "cost": 40
    },
 
    # -------------------------
    # SNACK
    # -------------------------
 
    {
        "type": "Snack",
        "food": "Banana + Peanuts",
        "cost": 20
    },
 
    {
        "type": "Snack",
        "food": "Sprouts Chaat",
        "cost": 25
    },
 
    {
        "type": "Snack",
        "food": "Roasted Chana",
        "cost": 15
    },
 
    {
        "type": "Snack",
        "food": "Seasonal Fruit",
        "cost": 25
    },
 
    # -------------------------
    # DINNER
    # -------------------------
 
    {
        "type": "Dinner",
        "food": "Dal + 2 Roti + Sabzi",
        "cost": 50
    },
 
    {
        "type": "Dinner",
        "food": "Rajma Rice",
        "cost": 50
    },
 
    {
        "type": "Dinner",
        "food": "Vegetable Pulao",
        "cost": 45
    },
 
    {
        "type": "Dinner",
        "food": "Chana Masala + 2 Roti",
        "cost": 50
    }
]
 
 
eggetarian = [
 
    # -------------------------
    # BREAKFAST
    # -------------------------
 
    {
        "type": "Breakfast",
        "food": "2 Boiled Eggs + Poha",
        "cost": 40
    },
 
    {
        "type": "Breakfast",
        "food": "Egg Omelette + 2 Roti",
        "cost": 40
    },
 
    {
        "type": "Breakfast",
        "food": "Egg Bhurji + Toast",
        "cost": 40
    },
 
    {
        "type": "Breakfast",
        "food": "2 Idli + Sambar + Egg",
        "cost": 40
    },
 
    # -------------------------
    # LUNCH
    # -------------------------
 
    {
        "type": "Lunch",
        "food": "Dal + Rice + Boiled Egg",
        "cost": 50
    },
 
    {
        "type": "Lunch",
        "food": "Egg Curry + Rice",
        "cost": 55
    },
 
    {
        "type": "Lunch",
        "food": "2 Roti + Dal + Egg Bhurji",
        "cost": 55
    },
 
    {
        "type": "Lunch",
        "food": "Rajma Rice + Boiled Egg",
        "cost": 55
    },
 
    # -------------------------
    # SNACK
    # -------------------------
 
    {
        "type": "Snack",
        "food": "Boiled Eggs + Banana",
        "cost": 35
    },
 
    {
        "type": "Snack",
        "food": "Egg Sandwich",
        "cost": 40
    },
 
    {
        "type": "Snack",
        "food": "Roasted Chana + Fruit",
        "cost": 25
    },
 
    # -------------------------
    # DINNER
    # -------------------------
 
    {
        "type": "Dinner",
        "food": "Egg Curry + 2 Roti",
        "cost": 60
    },
 
    {
        "type": "Dinner",
        "food": "Egg Bhurji + 2 Roti + Salad",
        "cost": 55
    },
 
    {
        "type": "Dinner",
        "food": "Dal Rice + Boiled Eggs",
        "cost": 55
    },
 
    {
        "type": "Dinner",
        "food": "Vegetable Pulao + Egg",
        "cost": 55
    }
]
 
 
# =========================================================
# MEALS DATABASE
# =========================================================
 
meals_database = {
    "Vegetarian": vegetarian,
    "Non-Vegetarian": non_vegetarian,
    "Vegan": vegan,
    "Eggetarian": eggetarian
}
 
 
# =========================================================
# ESTIMATED MEAL PRICES
# =========================================================
 
meal_costs = {
    "Breakfast": 55,
    "Lunch": 95,
    "Snack": 35,
    "Dinner": 110,
    "Extra": 40
}
 
 
# =========================================================
# HOME
# =========================================================
 
@app.route("/")
def home():
    return render_template("index.html")
 
 
# =========================================================
# EMAIL VALIDATION
# =========================================================
 
def is_valid_email(email):
 
    email_pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    )
 
    return re.fullmatch(
        email_pattern,
        email
    ) is not None
 
 
# =========================================================
# PASSWORD VALIDATION
# =========================================================
 
def is_strong_password(password):
 
    if len(password) < 8:
        return False
 
    if len(password) > 128:
        return False
 
    if not re.search(r"[A-Z]", password):
        return False
 
    if not re.search(r"[a-z]", password):
        return False
 
    if not re.search(r"\d", password):
        return False
 
    if not re.search(
        r"[^A-Za-z0-9]",
        password
    ):
        return False
 
    return True
 
 
# =========================================================
# REGISTER
# =========================================================
 
@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():
 
    if request.method == "POST":
 
        name = request.form.get(
            "name",
            ""
        ).strip()
 
        email = request.form.get(
            "email",
            ""
        ).strip().lower()
 
        password = request.form.get(
            "password",
            ""
        )
 
        confirm_password = request.form.get(
            "confirm_password",
            ""
        )
 
        age = request.form.get(
            "age",
            ""
        )
 
        height = request.form.get(
            "height",
            ""
        )
 
        weight = request.form.get(
            "weight",
            ""
        )
 
        diet = request.form.get(
            "diet",
            ""
        ).strip()
 
        goal = request.form.get(
            "goal",
            ""
        ).strip()
 
 
        # NAME
 
        if not name:
 
            flash(
                "Please enter your full name."
            )
 
            return redirect(
                url_for("register")
            )
 
        if len(name) < 2:
 
            flash(
                "Name must contain at least 2 characters."
            )
 
            return redirect(
                url_for("register")
            )
 
        if len(name) > 100:
 
            flash(
                "Name is too long."
            )
 
            return redirect(
                url_for("register")
            )
 
        if not re.fullmatch(
            r"[A-Za-zÀ-ÿ\s.'-]+",
            name
        ):
 
            flash(
                "Please enter a valid name."
            )
 
            return redirect(
                url_for("register")
            )
 
 
        # EMAIL
 
        if not email:
 
            flash(
                "Please enter your email address."
            )
 
            return redirect(
                url_for("register")
            )
 
        if len(email) > 120:
 
            flash(
                "Email address is too long."
            )
 
            return redirect(
                url_for("register")
            )
 
        if not is_valid_email(email):
 
            flash(
                "Please enter a valid email address."
            )
 
            return redirect(
                url_for("register")
            )
 
 
        # PASSWORD
 
        if not password:
 
            flash(
                "Please create a password."
            )
 
            return redirect(
                url_for("register")
            )
 
        if not is_strong_password(password):
 
            flash(
                "Password must contain at least 8 characters, "
                "one uppercase letter, one lowercase letter, "
                "one number and one special character."
            )
 
            return redirect(
                url_for("register")
            )
 
 
        # CONFIRM PASSWORD
 
        if password != confirm_password:
 
            flash(
                "Passwords do not match."
            )
 
            return redirect(
                url_for("register")
            )
 
 
        # DUPLICATE EMAIL
 
        existing_user = User.query.filter_by(
            email=email
        ).first()
 
        if existing_user:
 
            flash(
                "An account with this email already exists. "
                "Please login."
            )
 
            return redirect(
                url_for("login")
            )
 
 
        # AGE / HEIGHT / WEIGHT
 
        try:
 
            age = int(age)
            height = float(height)
            weight = float(weight)
 
        except (
            ValueError,
            TypeError
        ):
 
            flash(
                "Please enter valid age, height and weight."
            )
 
            return redirect(
                url_for("register")
            )
 
 
        # HEALTH VALUES
 
        if age < 13 or age > 120:
 
            flash(
                "Age must be between 13 and 120."
            )
 
            return redirect(
                url_for("register")
            )
 
        if height < 50 or height > 250:
 
            flash(
                "Height must be between 50 and 250 cm."
            )
 
            return redirect(
                url_for("register")
            )
 
        if weight < 20 or weight > 300:
 
            flash(
                "Weight must be between 20 and 300 kg."
            )
 
            return redirect(
                url_for("register")
            )
 
 
        # DIET
 
        allowed_diets = [
            "Vegetarian",
            "Non-Vegetarian",
            "Vegan",
            "Eggetarian"
        ]
 
        if diet not in allowed_diets:
 
            flash(
                "Please select a valid diet preference."
            )
 
            return redirect(
                url_for("register")
            )
 
 
        # GOAL
 
        allowed_goals = [
            "Weight Loss",
            "Weight Gain",
            "Muscle Gain",
            "Maintain Weight"
        ]
 
        if goal not in allowed_goals:
 
            flash(
                "Please select a valid fitness goal."
            )
 
            return redirect(
                url_for("register")
            )
 
 
        # CREATE USER
 
        hashed_password = generate_password_hash(
            password,
            method="scrypt"
        )
 
        user = User(
            name=name,
            email=email,
            password=hashed_password,
            age=age,
            height=height,
            weight=weight,
            diet=diet,
            goal=goal
        )
 
 
        try:
 
            db.session.add(user)
            db.session.commit()
 
        except Exception:
 
            db.session.rollback()
 
            flash(
                "Something went wrong while creating your account. "
                "Please try again."
            )
 
            return redirect(
                url_for("register")
            )
 
 
        flash(
            "Account created successfully! Please login."
        )
 
        return redirect(
            url_for("login")
        )
 
 
    return render_template(
        "register.html"
    )
 
 
# =========================================================
# LOGIN
# =========================================================
 
@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():
 
    if request.method == "POST":
 
        email = request.form.get(
            "email",
            ""
        ).strip().lower()
 
        password = request.form.get(
            "password",
            ""
        )
 
 
        if not email or not password:
 
            flash(
                "Please enter your email and password."
            )
 
            return redirect(
                url_for("login")
            )
 
 
        if not is_valid_email(email):
 
            flash(
                "Please enter a valid email address."
            )
 
            return redirect(
                url_for("login")
            )
 
 
        user = User.query.filter_by(
            email=email
        ).first()
 
 
        if user and check_password_hash(
            user.password,
            password
        ):
 
            # Clear previous session
            session.clear()
 
            # Store logged-in user
            session["user_id"] = user.id
 
            # Permanent session
            session.permanent = True
 
            # Dashboard-only welcome message
            session["login_success"] = True
 
            return redirect(
                url_for("dashboard")
            )
 
 
        flash(
            "Invalid email or password."
        )
 
        return redirect(
            url_for("login")
        )
 
 
    return render_template(
        "login.html"
    )
 
 
# =========================================================
# DASHBOARD
# =========================================================
 
@app.route("/dashboard")
def dashboard():
 
    if "user_id" not in session:
 
        return redirect(
            url_for("login")
        )
 
 
    user = User.query.get(
        session["user_id"]
    )
 
 
    if user is None:
 
        session.clear()
 
        return redirect(
            url_for("login")
        )
 
 
    today = date.today()
 
 
    meals = MealProgress.query.filter_by(
        user_id=session["user_id"],
        date=today
    ).all()
 
 
    meal_status = {}
 
    for meal in meals:
 
        meal_status[
            meal.meal_type
        ] = meal.completed
 
 
    completed_meals = sum(
        1
        for meal in meals
        if meal.completed
        and meal.meal_type in [
            "Breakfast",
            "Lunch",
            "Snack",
            "Dinner"
        ]
    )
 
 
    meal_percentage = int(
        (completed_meals / 4) * 100
    )
 
 
    if meal_percentage > 100:
        meal_percentage = 100
 
 
    # Daily completed meal cost
    completed_cost = round(
        sum(
            meal.cost or 0
            for meal in meals
            if meal.completed
        ),
        2
    )
 
 
    # Login message appears only once
    show_welcome = session.pop(
        "login_success",
        False
    )
 
 
    return render_template(
        "dashboard.html",
        user=user,
        meals=meals,
        meal_status=meal_status,
        completed_meals=completed_meals,
        meal_percentage=meal_percentage,
        completed_cost=completed_cost,
        show_welcome=show_welcome,
        today=today
    )
 
 
# =========================================================
# COMPLETE / UNCOMPLETE MEAL
# =========================================================
 
@app.route(
    "/complete-meal/<meal_type>",
    methods=["POST"]
)
def complete_meal(meal_type):
 
    if "user_id" not in session:
 
        return redirect(
            url_for("login")
        )
 
 
    allowed_meals = [
        "Breakfast",
        "Lunch",
        "Snack",
        "Dinner"
    ]
 
 
    if meal_type not in allowed_meals:
 
        flash(
            "Invalid meal type."
        )
 
        return redirect(
            url_for("dashboard")
        )
 
 
    today = date.today()
 
 
    existing_meal = MealProgress.query.filter_by(
        user_id=session["user_id"],
        meal_type=meal_type,
        date=today
    ).first()
 
 
    if existing_meal:
 
        existing_meal.completed = (
            not existing_meal.completed
        )
 
    else:
 
        new_meal = MealProgress(
            user_id=session["user_id"],
            meal_type=meal_type,
            food="Meal completed",
            cost=meal_costs.get(
                meal_type,
                0
            ),
            completed=True,
            date=today
        )
 
        db.session.add(
            new_meal
        )
 
 
    db.session.commit()
 
 
    return redirect(
        url_for("dashboard")
    )
 
# =========================================================
# GEMINI AI MEAL PLANNER
# Generates MEAL + RECIPE + NUTRITION together
# =========================================================
 
def generate_ai_meal_plan(
    goal,
    diet,
    budget,
    meals_per_day
):
 
    if not gemini_client:
        print("Gemini Error: Gemini client is not initialized.")
        return None
 
    # -----------------------------------------------------
    # MEAL TYPES
    # -----------------------------------------------------
 
    if meals_per_day == 3:
 
        meal_types = [
            "Breakfast",
            "Lunch",
            "Dinner"
        ]
 
    elif meals_per_day == 4:
 
        meal_types = [
            "Breakfast",
            "Lunch",
            "Snack",
            "Dinner"
        ]
 
    elif meals_per_day == 5:
 
        meal_types = [
            "Breakfast",
            "Mid-Morning Snack",
            "Lunch",
            "Evening Snack",
            "Dinner"
        ]
 
    else:
        return None
 
    # -----------------------------------------------------
    # GEMINI PROMPT
    # -----------------------------------------------------
 
    prompt = f"""
You are NutriAI, an AI Indian meal planning assistant.
 
Create a complete one-day Indian meal plan for the user.
 
USER INFORMATION
 
Fitness Goal:
{goal}
 
Diet Preference:
{diet}
 
Daily Food Budget:
₹{budget}
 
Number of Meals:
{meals_per_day}
 
MEAL TYPES:
 
{", ".join(meal_types)}
 
IMPORTANT RULES:
 
1. Generate exactly {meals_per_day} meals.
 
2. Use exactly these meal types:
{", ".join(meal_types)}
 
3. Every meal MUST include a complete recipe.
 
4. Recipes must be simple Indian recipes.
 
5. Recipes should be suitable for a student.
 
6. Use affordable ingredients.
 
7. Use ingredients easily available in India.
 
8. Use approximately 3 to 8 ingredients per recipe.
 
9. Cooking time should normally be between 10 and 30 minutes.
 
10. Give simple beginner-friendly cooking instructions.
 
11. Respect the user's diet preference.
 
12. Consider the user's fitness goal.
 
13. Keep the complete day's meals within or close to the given budget.
 
14. Give realistic approximate cost in Indian Rupees.
 
15. Give realistic approximate nutrition values for the stated serving.
 
16. Do not make medical claims.
 
17. Do not suggest supplements.
 
18. Do not return markdown.
 
19. Do not return explanations outside JSON.
 
20. Return ONLY valid JSON.
 
RETURN EXACTLY THIS STRUCTURE:
 
[
    {{
        "type": "Breakfast",
        "food": "Vegetable Poha with Curd",
        "cost": 30,
 
        "ingredients": [
            "Poha - 1 cup",
            "Onion - 1 small",
            "Carrot - 1 small",
            "Green peas - 1/4 cup",
            "Oil - 1 teaspoon",
            "Curd - 1/2 cup"
        ],
 
        "instructions": [
            "Wash the poha and drain the water.",
            "Heat oil in a pan.",
            "Add onion and vegetables and sauté.",
            "Add poha and mix well.",
            "Cook for 3 to 5 minutes.",
            "Serve with curd."
        ],
 
        "nutrition": {{
            "calories": 320,
            "protein": 9,
            "carbs": 48,
            "fat": 10
        }}
    }}
]
 
JSON RULES:
 
- type must be one of the requested meal types.
- food must be the actual meal name.
- cost must be a number only.
- ingredients must be an array.
- instructions must be an array.
- nutrition must contain calories, protein, carbs and fat.
- All nutrition values must be numbers.
- Do not put ₹ inside cost.
- Do not use markdown.
- Do not add explanations.
- Return ONLY valid JSON.
"""
 
    # -----------------------------------------------------
    # CALL GEMINI
    # -----------------------------------------------------
 
    try:
 
        print("Sending request to Gemini...")
 
        response = gemini_client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
 
        # -------------------------------------------------
        # GET GEMINI RESPONSE
        # -------------------------------------------------
 
        response_text = response.text.strip()
 
        print("Gemini response received.")
 
        # -------------------------------------------------
        # CONVERT JSON TEXT TO PYTHON
        # -------------------------------------------------
 
        ai_plan = json.loads(response_text)
 
        if not isinstance(ai_plan, list):
            print("Gemini Error: Response is not a list.")
            return None
 
        # -------------------------------------------------
        # CLEAN PLAN
        # -------------------------------------------------
 
        cleaned_plan = []
 
        for meal in ai_plan:
 
            if not isinstance(meal, dict):
                continue
 
            meal_type = str(
                meal.get("type", "")
            ).strip()
 
            food = str(
                meal.get("food", "")
            ).strip()
 
            # ---------------------------------------------
            # COST
            # ---------------------------------------------
 
            try:
 
                cost = float(
                    meal.get("cost", 0)
                )
 
            except (
                ValueError,
                TypeError
            ):
 
                cost = 0
 
            # ---------------------------------------------
            # INGREDIENTS
            # ---------------------------------------------
 
            ingredients = meal.get(
                "ingredients",
                []
            )
 
            if not isinstance(
                ingredients,
                list
            ):
 
                ingredients = [
                    str(ingredients)
                ]
 
            ingredients = [
                str(item).strip()
                for item in ingredients
                if str(item).strip()
            ]
 
            # ---------------------------------------------
            # INSTRUCTIONS
            # ---------------------------------------------
 
            instructions = meal.get(
                "instructions",
                []
            )
 
            if not isinstance(
                instructions,
                list
            ):
 
                instructions = [
                    str(instructions)
                ]
 
            instructions = [
                str(step).strip()
                for step in instructions
                if str(step).strip()
            ]
 
            # ---------------------------------------------
            # NUTRITION
            # ---------------------------------------------
 
            nutrition = meal.get(
                "nutrition",
                {}
            )
 
            if not isinstance(
                nutrition,
                dict
            ):
 
                nutrition = {}
 
            try:
 
                calories = float(
                    nutrition.get(
                        "calories",
                        0
                    )
                )
 
            except (
                ValueError,
                TypeError
            ):
 
                calories = 0
 
            try:
 
                protein = float(
                    nutrition.get(
                        "protein",
                        0
                    )
                )
 
            except (
                ValueError,
                TypeError
            ):
 
                protein = 0
 
            try:
 
                carbs = float(
                    nutrition.get(
                        "carbs",
                        0
                    )
                )
 
            except (
                ValueError,
                TypeError
            ):
 
                carbs = 0
 
            try:
 
                fat = float(
                    nutrition.get(
                        "fat",
                        0
                    )
                )
 
            except (
                ValueError,
                TypeError
            ):
 
                fat = 0
 
            # ---------------------------------------------
            # VALID MEAL
            # ---------------------------------------------
 
            if (
                meal_type
                and food
                and meal_type in meal_types
            ):
 
                cleaned_plan.append({
 
                    "type": meal_type,
 
                    "food": food,
 
                    "cost": round(
                        cost,
                        2
                    ),
 
                    "ingredients": ingredients,
 
                    "instructions": instructions,
 
                    "nutrition": {
 
                        "calories": round(
                            calories,
                            1
                        ),
 
                        "protein": round(
                            protein,
                            1
                        ),
 
                        "carbs": round(
                            carbs,
                            1
                        ),
 
                        "fat": round(
                            fat,
                            1
                        )
                    }
                })
 
        # -------------------------------------------------
        # VALIDATE NUMBER OF MEALS
        # -------------------------------------------------
 
        if len(cleaned_plan) != meals_per_day:
 
            print(
                f"Gemini returned {len(cleaned_plan)} meals "
                f"instead of {meals_per_day}."
            )
 
            return None
 
        print(
            "Complete AI meal plan generated successfully."
        )
 
        return cleaned_plan
 
    # -----------------------------------------------------
    # ERROR
    # -----------------------------------------------------
 
    except json.JSONDecodeError as e:
 
        print(
            "Gemini JSON Error:",
            repr(e)
        )
 
        return None
 
    except Exception as e:
 
        print(
            "Gemini Meal Planner Error:",
            repr(e)
        )
 
        return None
 
 
 
 
# =========================================================
# MEAL PLANNER
# =========================================================
 
@app.route(
    "/mealplanner",
    methods=["GET", "POST"]
)
def mealplanner():
 
    if "user_id" not in session:
        return redirect(
            url_for("login")
        )
 
    user = User.query.get(
        session["user_id"]
    )
 
    if user is None:
        session.clear()
        return redirect(
            url_for("login")
        )
 
    # -----------------------------------------
    # DEFAULT VALUES
    # -----------------------------------------
 
    selected_goal = (
        user.goal
        or "Weight Loss"
    )
 
    selected_diet = (
        user.diet
        or "Vegetarian"
    )
 
    selected_budget = 300.0
    selected_meals = 4
    meal_plan = []
    error = None
 
    # -----------------------------------------
    # POST
    # -----------------------------------------
 
    if request.method == "POST":
 
        selected_goal = request.form.get(
            "goal",
            selected_goal
        ).strip()
 
        selected_diet = request.form.get(
            "diet",
            selected_diet
        ).strip()
 
        # -------------------------------------
        # VALIDATE GOAL
        # -------------------------------------
 
        allowed_goals = [
            "Weight Loss",
            "Weight Gain",
            "Muscle Gain",
            "Maintain Weight"
        ]
 
        if selected_goal not in allowed_goals:
            error = (
                "Please select a valid fitness goal."
            )
 
        # -------------------------------------
        # VALIDATE DIET
        # -------------------------------------
 
        allowed_diets = [
            "Vegetarian",
            "Non-Vegetarian",
            "Vegan",
            "Eggetarian"
        ]
 
        if (
            error is None
            and selected_diet not in allowed_diets
        ):
            error = (
                "Please select a valid diet preference."
            )
 
        # -------------------------------------
        # BUDGET
        # -------------------------------------
 
        try:
            selected_budget = float(
                request.form.get(
                    "budget",
                    300
                )
            )
 
        except (
            ValueError,
            TypeError
        ):
            error = (
                "Please enter a valid budget."
            )
 
        # -------------------------------------
        # MEALS
        # -------------------------------------
 
        try:
            selected_meals = int(
                request.form.get(
                    "meals",
                    4
                )
            )
 
        except (
            ValueError,
            TypeError
        ):
            error = (
                "Please select a valid number of meals."
            )
 
        # -------------------------------------
        # BUDGET VALIDATION
        # -------------------------------------
 
        if (
            error is None
            and selected_budget <= 0
        ):
            error = (
                "Daily budget must be greater than ₹0."
            )
 
        # -------------------------------------
        # MEAL COUNT VALIDATION
        # -------------------------------------
 
        if (
            error is None
            and (
                selected_meals < 3
                or selected_meals > 5
            )
        ):
            error = (
                "Meals per day must be between 3 and 5."
            )
 
        # -------------------------------------
        # GENERATE AI PLAN
        # -------------------------------------
 
        if error is None:
 
            print("\nGenerating AI meal plan...")
 
            meal_plan = generate_ai_meal_plan(
                selected_goal,
                selected_diet,
                selected_budget,
                selected_meals
            )
 
            # ---------------------------------
            # AI FAILED
            # ---------------------------------
 
            if not meal_plan:
 
                error = (
                    "AI meal generation is currently "
                    "unavailable. Please check your "
                    "Gemini API key and try again."
                )
 
            # ---------------------------------
            # AI SUCCESS
            # ---------------------------------
 
            else:
 
                print("AI meal plan generated successfully.")
 
                today = date.today()
 
                # Remove today's previous planned meals
                MealProgress.query.filter_by(
                    user_id=session["user_id"],
                    date=today
                ).delete()
 
                # =========================================
                # SAVE COMPLETE AI RECIPES
                # =========================================
 
                GeneratedMeal.query.filter_by(
                    user_id=session["user_id"],
                    date=today
                ).delete()
 
                for meal in meal_plan:
 
                    nutrition = meal.get("nutrition", {})
 
                    generated_meal = GeneratedMeal(
                        user_id=session["user_id"],
                        meal_type=meal.get("type", "Meal"),
                        name=meal.get("food", "AI Generated Meal"),
                        ingredients=json.dumps(meal.get("ingredients", [])),
                        instructions=json.dumps(meal.get("instructions", [])),
                        calories=float(nutrition.get("calories", 0)),
                        protein=float(nutrition.get("protein", 0)),
                        carbs=float(nutrition.get("carbs", 0)),
                        fat=float(nutrition.get("fat", 0)),
                        cost=float(meal.get("cost", 0)),
                        date=today
                    )
 
                    db.session.add(generated_meal)
 
                # Save newly generated AI meals to dashboard progress
                for meal in meal_plan:
 
                    meal_type = meal.get("type", "").strip()
                    food = meal.get("food", "").strip()
                    cost = float(meal.get("cost", 0))
 
                    # Dashboard currently tracks these 4 meal types
                    if meal_type in [
                        "Breakfast",
                        "Lunch",
                        "Snack",
                        "Dinner"
                    ]:
 
                        new_meal = MealProgress(
                            user_id=session["user_id"],
                            meal_type=meal_type,
                            food=food,
                            cost=cost,
                            completed=False,
                            date=today
                        )
 
                        db.session.add(new_meal)
 
                db.session.commit()
    # -----------------------------------------
    # CALCULATE TOTAL
    # -----------------------------------------
 
    if meal_plan is None:
        meal_plan = []
 
    total_cost = round(
        sum(
            float(
                item.get(
                    "cost",
                    0
                )
            )
            for item in meal_plan
        ),
        2
    )
 
    # -----------------------------------------
    # REMAINING BUDGET
    # -----------------------------------------
 
    remaining_budget = round(
        selected_budget - total_cost,
        2
    )
 
    # -----------------------------------------
    # BUDGET STATUS
    # -----------------------------------------
 
    budget_status = (
        "within"
        if remaining_budget >= 0
        else "over"
    )
 
    # -----------------------------------------
    # RENDER
    # -----------------------------------------
 
    return render_template(
        "mealplanner.html",
        user=user,
        meal_plan=meal_plan,
        selected_goal=selected_goal,
        selected_diet=selected_diet,
        selected_budget=selected_budget,
        selected_meals=selected_meals,
        total_cost=total_cost,
        remaining_budget=remaining_budget,
        budget_status=budget_status,
        error=error
    )
 
# =========================================================
# NUTRITION SCORE CALCULATOR
# =========================================================
def calculate_nutrition_score(
    calories,
    protein,
    carbs,
    fat
):
    score = 50

    # -----------------------------------------
    # PROTEIN
    # -----------------------------------------
    if protein >= 20:
        score += 20
    elif protein >= 10:
        score += 12
    elif protein >= 5:
        score += 6

    # -----------------------------------------
    # CALORIES
    # -----------------------------------------
    if calories <= 100:
        score += 15
    elif calories <= 200:
        score += 10
    elif calories <= 300:
        score += 5

    # -----------------------------------------
    # FAT
    # -----------------------------------------
    if fat <= 5:
        score += 10
    elif fat <= 15:
        score += 5

    # -----------------------------------------
    # CARBS
    # -----------------------------------------
    if carbs <= 30:
        score += 5

    # -----------------------------------------
    # LIMIT SCORE
    # -----------------------------------------
    score = max(
        0,
        min(score, 100)
    )

    # -----------------------------------------
    # SCORE MESSAGE
    # -----------------------------------------
    if score >= 85:
        message = (
            "Excellent nutritional profile. "
            "This food can fit well into a balanced diet."
        )

    elif score >= 70:
        message = (
            "Good nutritional profile. "
            "Pair it with other nutrient-rich foods "
            "for a balanced meal."
        )

    elif score >= 50:
        message = (
            "Moderate nutritional profile. "
            "Portion size and the rest of your meal matter."
        )

    else:
        message = (
            "This food is more calorie-dense or "
            "less protein-rich, so consider portion size."
        )

    return score, message


# =========================================================
# ADD MEAL INGREDIENTS TO GROCERY
# =========================================================
@app.route(
    "/add-meal-ingredients",
    methods=["POST"]
)
def add_meal_ingredients():

    # -----------------------------------------
    # CHECK LOGIN
    # -----------------------------------------
    if "user_id" not in session:
        return redirect(
            url_for("login")
        )

    # -----------------------------------------
    # GET INGREDIENTS
    # -----------------------------------------
    ingredients = request.form.getlist(
        "ingredients"
    )

    if not ingredients:
        flash(
            "No ingredients found.",
            "error"
        )
        return redirect(
            url_for("mealplanner")
        )

    # -----------------------------------------
    # ADD INGREDIENTS
    # -----------------------------------------
    added_count = 0

    for ingredient in ingredients:

        ingredient = ingredient.strip()

        if not ingredient:
            continue

        # -------------------------------------
        # CHECK DUPLICATE
        # -------------------------------------
        existing_item = GroceryItem.query.filter_by(
            user_id=session["user_id"],
            item=ingredient
        ).first()

        if existing_item:
            continue

        # -------------------------------------
        # CREATE GROCERY ITEM
        # -------------------------------------
        grocery_item = GroceryItem(
            item=ingredient,
            quantity="As needed",
            price=0,
            user_id=session["user_id"]
        )

        db.session.add(
            grocery_item
        )

        added_count += 1

    # -----------------------------------------
    # SAVE
    # -----------------------------------------
    db.session.commit()

    flash(
        f"🛒 {added_count} ingredient(s) added to your grocery list!",
        "success"
    )

    return redirect(
        url_for("grocery")
    )
 
 
 
 
# =========================================================
# NUTRITION ANALYZER
# =========================================================
@app.route("/nutrition", methods=["GET", "POST"])
def nutrition():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if user is None:
        session.clear()
        return redirect(url_for("login"))

    nutrition_data = None
    error = None

    if request.method == "POST":

        food = request.form.get("food", "").strip()
        quantity = request.form.get("quantity", "100").strip()

        if not food:
            error = "Please enter a food item."

        else:
            try:
                quantity = float(quantity)

                if quantity <= 0:
                    raise ValueError

            except ValueError:
                error = "Please enter a valid quantity."

            if not error:

                # -----------------------------------------
                # BASIC NUTRITION DATABASE
                # -----------------------------------------

                nutrition_db = {

                    "apple": {
                        "calories": 52,
                        "protein": 0.3,
                        "carbs": 14,
                        "fat": 0.2
                    },

                    "banana": {
                        "calories": 89,
                        "protein": 1.1,
                        "carbs": 23,
                        "fat": 0.3
                    },

                    "rice": {
                        "calories": 130,
                        "protein": 2.7,
                        "carbs": 28,
                        "fat": 0.3
                    },

                    "paneer": {
                        "calories": 265,
                        "protein": 18,
                        "carbs": 6
                        ,
                        "fat": 20
                    },

                    "egg": {
                        "calories": 155,
                        "protein": 13,
                        "carbs": 1.1,
                        "fat": 11
                    },

                    "chicken": {
                        "calories": 165,
                        "protein": 31,
                        "carbs": 0,
                        "fat": 3.6
                    }
                }

                food_key = food.lower()

                if food_key in nutrition_db:

                    base = nutrition_db[food_key]

                    multiplier = quantity / 100

                    calories = round(
                        base["calories"] * multiplier,
                        1
                    )

                    protein = round(
                        base["protein"] * multiplier,
                        1
                    )

                    carbs = round(
                        base["carbs"] * multiplier,
                        1
                    )

                    fat = round(
                        base["fat"] * multiplier,
                        1
                    )

                    score = min(
                        100,
                        max(
                            0,
                            round(
                                100
                                - (fat * 1.5)
                                + (protein * 1.5)
                            )
                        )
                    )

                    if score >= 80:
                        score_message = "Excellent nutritional choice!"

                    elif score >= 60:
                        score_message = "Good choice. Keep your meal balanced."

                    elif score >= 40:
                        score_message = "Moderate choice. Add more nutritious foods."

                    else:
                        score_message = "Try balancing this with healthier foods."

                    nutrition_data = {
                        "food": food.title(),
                        "quantity": quantity,
                        "calories": calories,
                        "protein": protein,
                        "carbs": carbs,
                        "fat": fat,
                        "score": score,
                        "score_message": score_message,
                        "summary": (
                            f"{food.title()} provides approximately "
                            f"{calories} calories for {quantity}g. "
                            f"It contains {protein}g protein, "
                            f"{carbs}g carbohydrates and "
                            f"{fat}g fat."
                        )
                    }

                else:
                    error = (
                        f"Nutrition information for '{food}' "
                        "is not available yet. "
                        "Try Apple, Banana, Rice, Paneer, Egg or Chicken."
                    )

    return render_template(
        "nutrition.html",
        user=user,
        nutrition_data=nutrition_data,
        error=error
    )

# =========================================================
# AI RECIPE GENERATOR
# =========================================================

def generate_ai_recipe(ingredients):
    """
    Generate a simple Indian recipe using Gemini.
    """

    if not gemini_client:
        print("Gemini Error: API key is not configured.")
        return None

    prompt = f"""
You are NutriAI, an AI recipe assistant.

The user has these ingredients:

{ingredients}

Create ONE simple, tasty and affordable Indian recipe using these ingredients.

IMPORTANT RULES:

1. Use the user's ingredients as the main ingredients.
2. You may add a few common ingredients such as salt, oil, spices,
   onion, garlic or water if needed.
3. If chicken is provided, the recipe can be non-vegetarian.
4. If only vegetarian ingredients are provided, keep the recipe vegetarian.
5. Keep the recipe suitable for a college student.
6. Keep the recipe simple and beginner-friendly.
7. Cooking time should normally be between 10 and 30 minutes.
8. Give realistic approximate nutrition values.
9. Give approximate cost in Indian Rupees.
10. Do not make medical claims.
11. Do not recommend supplements.
12. Return ONLY valid JSON.
13. Do not use markdown.
14. Do not add explanations outside JSON.

RETURN EXACTLY THIS JSON STRUCTURE:

{{
    "name": "Chicken Rice Bowl",
    "description": "A simple and affordable Indian-style chicken rice bowl.",
    "ingredients": [
        "Rice - 1 cup",
        "Chicken - 150 g",
        "Onion - 1 small",
        "Oil - 1 teaspoon",
        "Salt - as required",
        "Turmeric - 1/4 teaspoon",
        "Chilli powder - 1/2 teaspoon"
    ],
    "instructions": [
        "Wash and cook the rice.",
        "Heat oil in a pan.",
        "Add onion and sauté until soft.",
        "Add chicken and spices.",
        "Cook until the chicken is completely cooked.",
        "Add the cooked rice and mix well.",
        "Cook for another 2 to 3 minutes and serve hot."
    ],
    "cooking_time": "25 minutes",
    "servings": 1,
    "nutrition": {{
        "calories": 520,
        "protein": 32,
        "carbs": 58,
        "fat": 15
    }},
    "cost": 90
}}
"""

    try:
        print("Sending recipe request to Gemini...")

        response = gemini_client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        if not response or not response.text:
            print("Gemini returned an empty response.")
            return None

        response_text = response.text.strip()

        print("Gemini recipe response received:")
        print(response_text)

        recipe_data = json.loads(response_text)

        if not isinstance(recipe_data, dict):
            print("Gemini recipe response is not an object.")
            return None

        # Make sure required fields exist
        recipe_data.setdefault("name", "AI Generated Recipe")
        recipe_data.setdefault("description", "")
        recipe_data.setdefault("ingredients", [])
        recipe_data.setdefault("instructions", [])
        recipe_data.setdefault("cooking_time", "20 minutes")
        recipe_data.setdefault("servings", 1)
        recipe_data.setdefault("cost", 0)

        nutrition = recipe_data.get("nutrition", {})

        if not isinstance(nutrition, dict):
            nutrition = {}

        recipe_data["nutrition"] = {
            "calories": float(nutrition.get("calories", 0)),
            "protein": float(nutrition.get("protein", 0)),
            "carbs": float(nutrition.get("carbs", 0)),
            "fat": float(nutrition.get("fat", 0))
        }

        try:
            recipe_data["cost"] = float(
                recipe_data.get("cost", 0)
            )
        except (ValueError, TypeError):
            recipe_data["cost"] = 0

        return recipe_data

    except json.JSONDecodeError as e:
        print("Recipe JSON Error:", repr(e))
        return None

    except Exception as e:
        print("Gemini Recipe Error:", repr(e))
        return None


# =========================================================
# RECIPE GENERATOR
# =========================================================

@app.route("/recipe", methods=["GET", "POST"])
def recipe():

    if "user_id" not in session:
        return redirect(url_for("login"))

    recipe_data = None
    error = None
    ingredients = ""

    if request.method == "POST":

        ingredients = request.form.get(
            "ingredients",
            ""
        ).strip()

        # -----------------------------------------
        # EMPTY INPUT
        # -----------------------------------------

        if not ingredients:

            error = "Please enter at least one ingredient."

            return render_template(
                "recipe.html",
                recipe=recipe_data,
                ingredients=ingredients,
                error=error
            )

        # -----------------------------------------
        # LIMIT INPUT LENGTH
        # -----------------------------------------

        if len(ingredients) > 500:

            error = (
                "Please enter a shorter list of ingredients."
            )

            return render_template(
                "recipe.html",
                recipe=recipe_data,
                ingredients=ingredients,
                error=error
            )

        # -----------------------------------------
        # GENERATE RECIPE
        # -----------------------------------------

        print(
            f"\nGenerating recipe for: {ingredients}"
        )

        recipe_data = generate_ai_recipe(
            ingredients
        )

        # -----------------------------------------
        # AI FAILED
        # -----------------------------------------

        if not recipe_data:

            error = (
                "Recipe generation is currently unavailable. "
                "Please check your Gemini API key and try again."
            )

            print("Recipe generation failed.")

        # -----------------------------------------
        # AI SUCCESS
        # -----------------------------------------

        else:

            print(
                "Recipe generated successfully."
            )

    return render_template(
        "recipe.html",
        recipe=recipe_data,
        ingredients=ingredients,
        error=error
    )
 
# =========================================================
# GROCERY ASSISTANT
# =========================================================
 
@app.route(
    "/grocery",
    methods=["GET", "POST"]
)
def grocery():
 
    if "user_id" not in session:
 
        return redirect(
            url_for("login")
        )
 
 
    user = User.query.get(
        session["user_id"]
    )
 
 
    if user is None:
 
        session.clear()
 
        return redirect(
            url_for("login")
        )
 
 
    if request.method == "POST":
 
        item = request.form.get(
            "item",
            ""
        ).strip()
 
        quantity = request.form.get(
            "quantity",
            ""
        ).strip()
 
        price_text = request.form.get(
            "price",
            ""
        ).strip()
 
 
        if not item or not quantity or not price_text:
 
            return redirect(
                url_for("grocery")
            )
 
 
        try:
 
            price = float(
                price_text
            )
 
            if price < 0:
                raise ValueError
 
        except ValueError:
 
            return redirect(
                url_for("grocery")
            )
 
 
        new_item = GroceryItem(
            item=item,
            quantity=quantity,
            price=price,
            user_id=user.id
        )
 
 
        db.session.add(
            new_item
        )
 
        db.session.commit()
 
 
        return redirect(
            url_for("grocery")
        )
 
 
    grocery_items = GroceryItem.query.filter_by(
        user_id=user.id
    ).order_by(
        GroceryItem.id.desc()
    ).all()
 
 
    total = round(
        sum(
            item.price
            for item in grocery_items
        ),
        2
    )
 
 
    return render_template(
        "grocery.html",
        user=user,
        grocery_items=grocery_items,
        total=total
    )
 
 
# =========================================================
# DELETE GROCERY ITEM
# =========================================================
 
@app.route(
    "/delete-grocery/<int:item_id>"
)
def delete_grocery(item_id):
 
    if "user_id" not in session:
 
        return redirect(
            url_for("login")
        )
 
 
    item = GroceryItem.query.get_or_404(
        item_id
    )
 
 
    if item.user_id != session["user_id"]:
 
        return redirect(
            url_for("grocery")
        )
 
 
    db.session.delete(
        item
    )
 
    db.session.commit()
 
 
    return redirect(
        url_for("grocery")
    )
 
 
# =========================================================
# REPORT
# =========================================================
 
@app.route("/report")
def report():
 
    if "user_id" not in session:
 
        return redirect(
            url_for("login")
        )
 
 
    user = User.query.get(
        session["user_id"]
    )
 
 
    if user is None:
 
        session.clear()
 
        return redirect(
            url_for("login")
        )
 
 
    bmi = None
 
    bmi_status = ""
 
 
    if (
        user.height
        and user.weight
        and user.height > 0
    ):
 
        height_m = user.height / 100
 
 
        bmi = round(
            user.weight /
            (height_m * height_m),
            1
        )
 
 
        if bmi < 18.5:
 
            bmi_status = "Underweight"
 
        elif bmi < 25:
 
            bmi_status = "Healthy Range"
 
        elif bmi < 30:
 
            bmi_status = "Overweight"
 
        else:
 
            bmi_status = "Obesity Range"
 
 
    return render_template(
        "report.html",
        user=user,
        bmi=bmi,
        bmi_status=bmi_status
    )
 
 
# =========================================================
# PROFILE
# =========================================================
 
@app.route(
    "/profile",
    methods=["GET", "POST"]
)
def profile():
 
    if "user_id" not in session:
 
        return redirect(
            url_for("login")
        )
 
 
    user = User.query.get(
        session["user_id"]
    )
 
 
    if user is None:
 
        session.clear()
 
        return redirect(
            url_for("login")
        )
 
 
    if request.method == "POST":
 
        name = request.form.get(
            "name",
            ""
        ).strip()
 
 
        if name:
 
            user.name = name
 
 
        try:
 
            age = request.form.get(
                "age"
            )
 
            height = request.form.get(
                "height"
            )
 
            weight = request.form.get(
                "weight"
            )
 
 
            user.age = (
                int(age)
                if age
                else None
            )
 
 
            user.height = (
                float(height)
                if height
                else None
            )
 
 
            user.weight = (
                float(weight)
                if weight
                else None
            )
 
 
        except ValueError:
 
            return (
                "Please enter valid numbers."
            )
 
 
        user.diet = request.form.get(
            "diet",
            user.diet
        )
 
 
        user.goal = request.form.get(
            "goal",
            user.goal
        )
 
 
        db.session.commit()
 
 
        return redirect(
            url_for("profile")
        )
 
 
    edit = (
        request.args.get(
            "edit"
        ) == "true"
    )
 
 
    return render_template(
        "profile.html",
        user=user,
        edit=edit
    )
 
 
# =========================================================
# LOGOUT
# =========================================================
 
@app.route("/logout")
def logout():
 
    session.clear()
 
    return redirect(
        url_for("home")
    )
 
 
# =========================================================
# RUN APPLICATION
# =========================================================
 
if __name__ == "__main__":
 
    app.run(
        debug=True
    )
 
