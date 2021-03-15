import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    urows = db.execute("SELECT cash FROM users WHERE id = :id;", id=session["user_id"])
    cash = int(urows[0]["cash"])
    srows = db.execute("SELECT symbol, SUM(quantity) FROM stock WHERE userid = :userid GROUP BY symbol;", userid=session["user_id"])
    holdings = []
    #curly braces mean dictionary
    totaloverall = cash
    for row in srows:
        stock = lookup(row["symbol"])
        holdings.append({
            "symbol": stock["symbol"],
            "name": stock["name"],
            "shares": row["SUM(quantity)"],
            "price": stock["price"],
            "total": stock["price"]*row["SUM(quantity)"]
        })
        totaloverall += stock["price"]*row["SUM(quantity)"]
    return render_template("index.html", holdings = holdings, cash=cash, totaloverall = totaloverall)
    #"""Show portfolio of stocks"""
    #return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
    #"""Buy shares of stock"""
        symbol = request.form.get("symbol")
        quantity = int(request.form.get("quantity"))
        stock = lookup(symbol)
        name = stock["name"]
        price = stock["price"]
        if stock == None:
            return apology("Invalid stock symbol", 403)
        cost = stock["price"] * quantity
        rows = db.execute("SELECT cash FROM users WHERE id = :id",
                          id=session["user_id"])
        cash = rows[0]["cash"]
        #should only be one row because one user, then select cash column from that row
        if cash < cost:
            return apology("not enough money", 403)
        db.execute("INSERT INTO stock (userid, name, symbol, quantity, price) VALUES(:userid, :name, :symbol, :quantity, :price)", userid = session["user_id"], name= name,
        symbol = symbol, quantity = quantity, price = price)
        updatecash = cash- cost
        db.execute("UPDATE users SET cash = :updatecash WHERE id = :id.", updatecash = updatecash, id = session["user_id"])
        return redirect("/")
    ##check if they have enough money
    ##use lookup function to determine price of stock X quantity
    ##if enough money, then purchase stock
    ##need to create a new table
    #return apology("TODO")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    #"""Show history of transactions"""
    rows = db.execute("SELECT symbol, quantity, price, transacted FROM stock WHERE userid = :userid", userid=session["user_id"])
    history = []
    #curly braces mean dictionary
    for row in rows:
        history.append({
            "symbol": row["symbol"],
            "quantity": row["quantity"],
            "price": row["price"],
            "transacted": row["transacted"]
        })
    return render_template("history.html", history = history)
    #return apology("TODO")

@app.route("/addcash", methods=["GET", "POST"])
@login_required
def addcash():
    if request.method == "POST":
        #"""Allow users to add cash"""
        newmoney = int(request.form.get("quantity"))
        rows = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        cash = rows[0]["cash"]
        updatecash = cash + newmoney
        db.execute("UPDATE users SET cash = :updatecash WHERE id = :id.", updatecash = updatecash, id = session["user_id"])
        return redirect("/")
    else:
        return render_template("addcash.html")
        #return apology("TODO")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        #will return number of rows that has username that matches the one the user typed in
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        #should return 1 (if user exists), if not should return 0
        # Ensure username exists and password is correct
        #database doesnt store actual passwords, but instead checks hash functioned version of it
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        # query should have only returned 1 row (i.e., row 0)
        # to access a column from that row, can use title of column
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    # all above code is post (assumnig user is trying to submit form)
    #if request is get, then should return the login page
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "POST":
        #when submit, return quote page
        symbol = request.form.get("symbol")
        stock = lookup(symbol)
        if stock == None:
            return apology("Invalid stock symbol", 403)
        return render_template("returnquote.html", stock = stock)
    #"""Get stock quote."""
    else:
        return render_template("getquote.html")
    #return apology("TODO")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        ##check if passwords match
        elif request.form.get("password") != request.form.get("passwordcheck"):
            return apology("passwords must match", 403)

        # Query database for username
        #will return number of rows that has username that matches the one the user typed in
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        #should return 1 (if user exists), if not should return 0
        # if already exists, tell them it already exists
        if len(rows) != 0:
            return apology("user already exists", 403)

        #save username
        username = request.form.get("username")

        #hash password
        password = request.form.get("password")
        passhash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        #insert user into database
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :passhash)", username = username, passhash = passhash)

        # Redirect user to home page
        return redirect("/login")

    # User reached route via GET (as by clicking a link or via redirect)
    # all above code is post (assumnig user is trying to submit form)
    #if request is get, then should return the register page
    else:
        return render_template("register.html")

    #return apology("TODO")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    srows = db.execute("SELECT symbol, SUM(quantity) FROM stock WHERE userid = :userid GROUP BY symbol;", userid=session["user_id"])
    holdings = []
    #curly braces mean dictionary
    for row in srows:
        holdings.append({
            "symbol": row["symbol"],
            "shares": row["SUM(quantity)"],
        })
    if request.method == "POST":
    #"""Sell shares of stock"""
        ##get list of stocks for form
        symbol = request.form.get("symbol")
        quantity = int(request.form.get("quantity"))
        stockrequest = db.execute("SELECT SUM(quantity) FROM stock WHERE userid = :userid AND symbol = :symbol GROUP BY symbol", userid =session["user_id"], symbol = symbol)
        if quantity > stockrequest[0]["SUM(quantity)"]:
                return apology("You can't sell more than you have", 403)
        stock = lookup(symbol)
        if stock == None:
            return apology("Invalid stock symbol", 403)
        ## render apology if user does own stock
        name = stock["name"]
        price = stock["price"]
        gain = stock["price"] * quantity
        ##add money to cash
        rows = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        cash = rows[0]["cash"]
        updatecash = cash + gain
        db.execute("UPDATE users SET cash = :updatecash WHERE id = :id.", updatecash = updatecash, id = session["user_id"])
        ##record transaction
        ##indicate sell with negative number
        quantityneg = -1 * quantity
        db.execute("INSERT INTO stock (userid, name, symbol, quantity, price) VALUES(:userid, :name, :symbol, :quantity, :price)", userid = session["user_id"], name= name,
        symbol = symbol, quantity = quantityneg, price = price)
        return redirect("/")
    ##check if they have enough money
    ##use lookup function to determine price of stock X quantity
    ##if enough money, then purchase stock
    ##need to create a new table
    #return apology("TODO")
    else:
        return render_template("sell.html", holdings = holdings)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
