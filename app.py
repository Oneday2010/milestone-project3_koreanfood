import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_foods")
def get_foods():
    foods = list(mongo.db.foods.find())
    return render_template("foods.html", foods=foods)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    foods = list(mongo.db.foods.find({"$text": {"$search": query}}))
    return render_template("foods.html", foods=foods)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect(url_for(
                            "profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_recipes", methods=["GET", "POST"])
def add_recipes():
    if request.method == "POST":
        foods = {
            "category_name": request.form.get("category_name"),
            "food_name": request.form.get("food_name"),
            "food_description": request.form.get("food_description"),
            "created_by": session["user"],
            "recipe_ingredients": request.form.get("recipe_ingredients"),
            "recipe_method": request.form.get("recipe_method"),
            "cooking_level": request.form.get("cooking_level"),
            "food_img": request.form.get("food_img"),
        }
        mongo.db.foods.insert_one(foods)
        flash("Recipe Successfully Added")
        return redirect(url_for("get_foods"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_recipes.html", categories=categories)


@app.route("/edit_recipes/<foods_id>", methods=["GET", "POST"])
def edit_recipes(foods_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name"),
            "food_name": request.form.get("food_name"),
            "food_description": request.form.get("food_description"),
            "created_by": session["user"],
            "recipe_ingredients": request.form.get("recipe_ingredients"),
            "recipe_method": request.form.get("recipe_method"),
            "cooking_level": request.form.get("cooking_level"),
            "food_img": request.form.get("food_img"),
        }
        mongo.db.foods.update({"_id": ObjectId(foods_id)}, submit)
        flash("Recipes Successfully Updated")

    foods = mongo.db.foods.find_one({"_id": ObjectId(foods_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template(
        "edit_recipes.html", foods=foods, categories=categories)


@app.route("/delete_recipes/<foods_id>")
def delete_recipes(foods_id):
    mongo.db.foods.remove({"_id": ObjectId(foods_id)})
    flash("Recipes Successfully Deleted")
    return redirect(url_for("get_foods"))


@app.route("/get_categories")
def get_categories():
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
