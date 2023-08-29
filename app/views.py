from flask import Flask, render_template, request, session,  redirect, flash , jsonify, g, url_for
from jinja2  import TemplateNotFound
from app import app
from app import db 
from app.models import Product, Category, User, OrderItem, Order, Supplier, Admin, MacAddress
from flask_login import LoginManager , UserMixin , login_required ,login_user, logout_user,current_user
from sqlalchemy import insert, update, delete
from functools import wraps
import pyotp
import wmi
import netifaces
import pythoncom
from getmac import get_mac_address as gma
from blinker import Namespace


login_manager = LoginManager()
login_manager.init_app(app)

# ---------------------------------- Creating Signal ---------------------------
signal_namespace = Namespace()

product_added_signal = signal_namespace.signal('product-added')
def send_product_added_email(sender, product):
    print(f"Email sent for product added: {product}")


product_added_signal.connect(send_product_added_email, app)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/product", methods=['GET'])
def get_product():
    # allproducts = Product.query.all()
    # newProducts=[]
    # for product in allproducts:
    #     if product.quantity == 0:
    #         newQuantity="out of stock"
    #     else:
    #         newQuantity="In stock"
        
    #     modified_product = {
    #         "p_id": product.p_id,
    #         "c_id": product.c_id,
    #         "title": product.title,
    #         "description": product.description,
    #         "quantity": product.quantity,
    #         "size": product.size,
    #         "price": product.price,
    #         "status": newQuantity
    #     }
    #     newProducts.append(modified_product)

    # return jsonify({"products": newProducts})
    
#    2nd way 
    # sql_query = """
    # SELECT p_id, c_id, title, description, quantity, size, price,
    #        CASE WHEN quantity = 0 THEN 'out of stock' ELSE 'In stock' END AS status
    # FROM product
    # """
    
    # results = db.session.execute(sql_query) 

    # newProducts = [
    #     {
    #         "p_id": row.p_id,
    #         "c_id": row.c_id,
    #         "title": row.title,
    #         "description": row.description,
    #         "quantity": row.quantity,
    #         "size": row.size,
    #         "price": row.price,
    #         "status": row.status
    #     }
    #     for row in results
    # ]

    # return jsonify({"products": newProducts})

#    3rd way 
    stmt = (
        db.select(
            Product.p_id,
            Product.c_id,
            Product.title,
            Product.description,
            Product.quantity,
            Product.size,
            Product.price,
            db.case([(Product.quantity == 0, 'out of stock')], else_='In stock').label('status')
        )
        .order_by(Product.p_id)
    )
    results = db.session.execute(stmt)
    
    newProducts = [
        {
            "p_id": row.p_id,
            "c_id": row.c_id,
            "title": row.title,
            "description": row.description,
            "quantity": row.quantity,
            "size": row.size,
            "price": row.price,
            "status": row.status
        }
        for row in results
    ]
    return jsonify({"products": newProducts})

# -------------------------------- Loader ------------------------

# Prev Loader 
# @login_manager.user_loader
# def load_user(id):
#     return Admin.query.get(id)

@login_manager.user_loader
def load_user(user_id):
    # Load the user based on user_id from the database
    user = User.query.get(int(user_id))
    if user is None:
        user = Admin.query.get(int(user_id))
    return user

# --------------------------- Decorators --------------------------


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        print(current_user.__dict__)  # Print user attributes for debugging
        if current_user.is_authenticated and session.get('authenticated') and getattr(current_user, 'is_admin', False):
            stored_mac_address = session.get('mac_address')
            actual_mac_address = get_mac_address()

            if stored_mac_address and actual_mac_address and stored_mac_address == actual_mac_address:
                return view_func(*args, **kwargs)
            else:
                return jsonify({"message": "Access denied due to MAC address mismatch"}), 403
        else:
            return jsonify({"message": "This feature is authorized for admin users only"}), 401
    return wrapper

def user_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated and session.get('authenticated'):
            stored_mac_address = session.get('mac_address')
            actual_mac_address = get_mac_address()

            if stored_mac_address and actual_mac_address and stored_mac_address == actual_mac_address:
                return view_func(*args, **kwargs)
            else:
                return jsonify({"message": "Access denied due to MAC address mismatch"}), 403
        return jsonify({"message": "Login Required for Normal User"}), 401  
        
    return wrapper

# ---------------------------------- user Login Section ---------------

@app.route("/login")
def login_page():
    return render_template("login.html")



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # user_data = request.json  # Get the JSON data from the request
        # username = user_data.get('username')
        # password = user_data.get('password')
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(u_name=username).first()
        if user and user.password == password:
            mac_address = gma()
            print("mac address is: ", mac_address)

            existing_mac_address = MacAddress.query.filter_by(user_id=user.u_id, mac_address=mac_address).first()
            if existing_mac_address:
                flash("Device already registered.", "info")
            else:
                new_mac_address = MacAddress(user_id=user.u_id, mac_address=mac_address)
                db.session.add(new_mac_address)
                db.session.commit()
                flash("Device registered successfully.", "success")

                login_user(user)
            return redirect(url_for("login_2fa"))
        else:
            flash("You have supplied invalid login credentials!", "danger")
            return redirect(url_for("login"))
    else:
        return jsonify({"message": "Invalid Request Method"}), 401


def get_mac_address():
    pythoncom.CoInitialize() 
    c = wmi.WMI()
    wifi_interface = None

    for interface in c.Win32_NetworkAdapter():
        if interface.NetConnectionID and "Wi-Fi" in interface.NetConnectionID:
            print("Detected Wi-Fi interface:", interface.NetConnectionID)
            wifi_interface = interface
            break

    if wifi_interface:
        address = wifi_interface.MACAddress
        return address
    else:
        return None

def store_mac_address(user_id, mac_address):
    mac_entry = MacAddress(user_id=user_id, mac_address=mac_address)
    db.session.add(mac_entry)
    db.session.commit()
    
    
@app.route("/cookie", methods=['GET'])
def get_cookie():
    if current_user.is_authenticated:
        mac_address = session.get('mac_address')
        if mac_address:
            return jsonify(cookie_value= mac_address)
        else:
            return jsonify(message="Cookie not found")
    else:
        return jsonify(message="User is not authenticated")
    
    
    
@app.route("/login/2fa/")
def login_2fa():
    # generating random secret key for authentication
    secret = pyotp.random_base32()
    return render_template("login_2fa.html", secret=secret)


@app.route("/login/2fa/", methods=["POST"])
def login_2fa_form():
    # getting secret key used by user
    secret = request.form.get("secret")
    # getting OTP provided by user
    otp = int(request.form.get("otp"))

    # verifying submitted OTP with PyOTP
    if pyotp.TOTP(secret).verify(otp):
        response_data = {"success": True, "message": "The TOTP 2FA token is valid"}
        session["authenticated"] = True
        
    else:
        response_data = {"success": False, "message": "You have supplied an invalid 2FA token!"}
        
    return jsonify(response_data)

# Using Flask_login 
@app.route('/logout',methods=['POST'])
def logout():
    logout_user()
    return jsonify("logout")

# using Session 
# @app.route('/logout', methods=['GET','POST'])
# def logout():
    # if 'username' in session:
    #     session.pop('username', None)  # Remove the 'username' key from the session
    #     return jsonify({"message": "Logged out"}), 200
    # else:
    #     return jsonify({"message": "Not logged in"}), 401
    
    
# ------------------------------------- Admin Section ---------------------

@app.route('/admin', methods=['GET', 'POST'])
def login_Admin():
    if request.method == 'POST':
        admin_data = request.json  # Get the JSON data from the request
        email = admin_data.get('email')
        print(email)
        password = admin_data.get('password')
        print(password)
        admin = Admin.query.filter_by(email = email).first()
        if admin and admin.password == password:
            login_user(admin)
            return jsonify({"message": "Logged In"}), 200
        else:
            return jsonify({'error':'Invalid Credentials'}),401
    else:
        return jsonify({"message": "Invalid Request Method"}), 401


@app.route('/filter-products', methods=['POST'])
@user_required
def filter_products():
    criteria = request.json
    query = db.session.query(Product)
    if 'title' in criteria:
        query = query.filter(Product.title.like(f'%{criteria["title"]}%'))
    if 'category' in criteria:
        category_name = criteria['category']
        category_id = db.session.query(Category.c_id).filter(Category.c_name == category_name).scalar()
        if category_id:
            query = query.filter(Product.c_id == category_id)

    if 'quantity' in criteria:
            query = query.filter(Product.quantity >= criteria['quantity'])

    if 'price' in criteria:
            query = query.filter(Product.price <= criteria['price'])

    filtered_products = query.all()

    result = [
        {
            "p_id": product.p_id,
            "c_id": product.c_id,
            "title": product.title,
            "description": product.description,
            "quantity": product.quantity,
            "size": product.size,
            "price": product.price
        }
        for product in filtered_products
    ]

    return jsonify({"filtered_products": result})

    
# ---------------------------------- Product Section ------------------------
    
    
@app.route('/products', methods=['GET'])
@user_required
def get_products():
    # Using Searlizers
    return Product.fs_get_delete_put_post()
    # products = db.session.query(Product).all()
    # product_list = []
    # for product in products:
    #     product_data = {
    #         "p_id": product.p_id,
    #         "c_id": product.c_id,
    #         "title": product.title,
    #         "description": product.description,
    #         "quantity": product.quantity,
    #         "size": product.size,
    #         "price": product.price
    #     }
    #     product_list.append(product_data)
    
    # return jsonify(product_list)


@app.route('/addProducts', methods=['POST'])
@admin_required
def addProducts():
    # Using Searlizer 
    return Product.fs_get_delete_put_post()
    # if request.method == "POST":
    #     product= request.json  # Get the JSON data from the request
    #     c_id = product.get('c_id')
    #     title= product.get('title')
    #     description = product.get('description')
    #     quantity = product.get('quantity')
    #     size = product.get('size')
    #     price = product.get('price')
    #     db.session.add(product)
    #     db.session.commit()
    #     product_added_signal.send(app, product=product)
    #     return jsonify({"message": "Product added successfully"}), 201
    # else:
    #     return jsonify({"message": "Invalid request"}), 400

         
@app.route('/updateProduct/<int:sno>', methods=['PUT'])
@admin_required
def updateProducts(sno):
    return Product.fs_get_delete_put_post(sno)
    # if request.method == "PATCH":
    #     product = request.json 
    #     c_id = product.get('c_id')
    #     title = product.get('title')
    #     description = product.get('description')
    #     quantity = product.get('quantity')
    #     size = product.get('size')
    #     price = product.get('price')
    #     existing_product = Product.query.get(sno)
        
    #     if not existing_product:
    #         return jsonify({"error": "Category not found"}), 404
        
    #     if existing_product.p_id != sno:
    #         return jsonify({"error": "Provided product does not match sno"}), 400
    #     update_stmt = (update(Product)
    #         .where(Product.p_id == sno)
    #         .values(
    #             c_id=c_id,
    #             title=title,
    #             description=description,
    #             quantity=quantity,
    #             size=size,
    #             price=price
    #         )
    #     )
    #     db.session.execute(update_stmt)
    #     db.session.commit()
    #     return jsonify({"message": "Product added successfully"}), 201
    # else:
    #     return jsonify({"message": "Invalid request"}), 400  



@app.route('/deleteProduct/<int:sno>', methods=['DELETE'])
@admin_required
def deleteProduct(sno):
    return Product.fs_get_delete_put_post(sno)
        # delete_stmt = (delete(Product).where(Product.p_id == sno))
        # db.session.execute(delete_stmt)
        # db.session.commit()
        # return jsonify({'message': 'product deleted'})   
    
    
# ---------------------------------- Category Section ------------------------


    
@app.route('/category', methods=['GET'])
def get_category():
    categories = db.session.query(Category).all()
    
    category_list = []
    for category in categories:
        category_data = {
            "c_id": category.c_id,
            "name": category.c_name,
            "description": category.c_description
        }
        category_list.append(category_data)
    
    return jsonify(category_list)


@app.route('/addCategory', methods=['POST'])
@admin_required
def addCategory():
    if request.method == "POST":
        product= request.json  # Get the JSON data from the request
        c_name= product.get('c_name')
        c_description= product.get('c_description')
        stmt = insert(Category).values(c_name=c_name, c_description=c_description)
        db.session.execute(stmt)
        db.session.commit()
        
        return jsonify({"message": "Category added successfully"}), 201
    else:
        return jsonify({"message": "Invalid request"}), 400

         
@app.route('/updateCategory/<int:sno>', methods=['PATCH'])
@admin_required
def updateCategory(sno):
    if request.method == "PATCH":
        product = request.json 
        c_name= product.get('c_name')
        c_description= product.get('c_description')
        existing_category = Category.query.get(sno)
        
        if not existing_category:
            return jsonify({"error": "Category not found"}), 404
        
        if existing_category.c_id != sno:
            return jsonify({"error": "Provided c_id does not match sno"}), 400
        
        update_stmt = (update(Category).where(Category.c_id == sno).values(c_name=c_name, c_description=c_description)
        )
        db.session.execute(update_stmt)
        db.session.commit()
        
        return jsonify({"message": "Category added successfully"}), 201
    else:
        return jsonify({"message": "Invalid request"}), 400  



@app.route('/deleteCategory/<int:sno>', methods=['DELETE'])
@admin_required
def deleteCategory(sno):
        delete_stmt = (delete(Category).where(Category.c_id == sno))
        db.session.execute(delete_stmt)
        db.session.commit()
        return jsonify({'message': 'Category deleted'})   
    
# ---------------------------- Create user -------------------------------

    
@app.route('/user', methods=['GET'])
@admin_required
def get_user():
    users = db.session.query(User).all()
    user_list = []
    for user in users:
        user_data = {
            "name": user.u_name,
            "email": user.u_email,
            "details": user.u_details
        }
        user_list.append(user_data)
    
    return jsonify(user_list)



@app.route('/addUser', methods=['POST'])
def addUser():
    if request.method == "POST":
        product= request.json  # Get the JSON data from the request
        u_name= product.get('u_name')
        u_email= product.get('u_email')
        u_details= product.get('u_details')
        password= product.get('password')
        existing_user = User.query.filter_by(u_email=u_email).first()
        if existing_user:
            return jsonify({"error": "User Email already Found..! Try with another email address"})
        stmt = insert(User).values(u_name=u_name, u_email=u_email, u_details=u_details, password=password)
        db.session.execute(stmt)
        db.session.commit()
        return jsonify({"message": "User added successfully"}), 201
            
    else:
        return jsonify({"message": "Invalid request"}), 400

         
@app.route('/updateUser/<int:sno>', methods=['PATCH'])
@user_required
def updateUser(sno):
    if request.method == "PATCH":
        product = request.json 
        u_name= product.get('u_name')
        u_email= product.get('u_email')
        u_details= product.get('u_details')
        password= product.get('password')
        existing_user= User.query.get(sno)
        
        if not existing_user:
            return jsonify({"error": "User not found"}), 404
        
        if existing_user.u_id != sno:
            return jsonify({"error": "Provided userid does not match sno"}), 400
        
        new_user = User.query.filter_by(u_email=u_email).first()
        if new_user:
            return jsonify({"error": "User Email already Found..! Try with another email address"})
        
        update_stmt = (update(User).where(User.u_id == sno).values(u_name=u_name, u_email=u_email, u_details=u_details, password=password)
        )
        db.session.execute(update_stmt)
        db.session.commit()
        
        return jsonify({"message": "User added successfully"}), 201
    else:
        return jsonify({"message": "Invalid request"}), 400  



@app.route('/deleteUser/<int:sno>', methods=['DELETE'])
@admin_required
def deleteUser(sno):
        delete_stmt = (delete(User).where(User.u_id == sno))
        db.session.execute(delete_stmt)
        db.session.commit()
        return jsonify({'message': 'User deleted'})   
    
# ----------------------------- Order Iteems Section --------------------

@app.route('/orderItem', methods=['GET'])
@user_required
def get_orderItem():
    items = db.session.query(OrderItem).all()
    item_list = []
    for item in items:
        product = db.session.query(Product).filter_by(p_id=item.p_id).first()
        order_item = {
            "item_id": item.item_id,
            "product_id": None,
            "Quantity": item.quantity
        }
        if product:
            order_item["product"] = {
                "p_id": product.p_id,
                "title": product.title,
                "description": product.description,
                "quantity": product.quantity,
                "size": product.size,
                "price": product.price
            }
        item_list.append(order_item)
    
    return jsonify(item_list)



@app.route('/addOrderitem', methods=['POST'])
@user_required
def addItem():
    if request.method == "POST":
        product= request.json  # Get the JSON data from the request
        p_id= product.get('p_id')
        quantity= product.get('quantity')
        stmt = insert(OrderItem).values(p_id=p_id, quantity=quantity)
        db.session.execute(stmt)
        db.session.commit()
        return jsonify({"message": "OrderItem added successfully"}), 201
            
    else:
        return jsonify({"message": "Invalid request"}), 400

         
@app.route('/updateOrderitem/<int:sno>', methods=['PATCH'])
@user_required
def updateItem(sno):
    if request.method == "PATCH":
        product= request.json  # Get the JSON data from the request
        p_id= product.get('p_id')
        quantity= product.get('quantity')
        existing_item= OrderItem.query.get(sno)
        
        if not existing_item:
            return jsonify({"error": "OrderItem not found"}), 404
        
        if existing_item.item_id != sno:
            return jsonify({"error": "Provided Item id does not match sno"}), 400
        
        update_stmt = (update(OrderItem).where(OrderItem.item_id == sno).values(p_id=p_id, quantity=quantity)
        )
        db.session.execute(update_stmt)
        db.session.commit()
        
        return jsonify({"message": "Order Item added successfully"}), 201
    else:
        return jsonify({"message": "Invalid request"}), 400  



@app.route('/deleteOrderitem/<int:sno>', methods=['DELETE'])
@user_required
def deleteItem(sno):
        delete_stmt = (delete(OrderItem).where(OrderItem.item_id == sno))
        db.session.execute(delete_stmt)
        db.session.commit()
        return jsonify({'message': 'User deleted'})   
    
    
# ------------------------------ Create Order Section -------------------------



    
@app.route('/Order', methods=['GET'])
@user_required
def get_Order():
    Orders = db.session.query(Order).all()
    order_list = []
    for order in Orders:
        supplier = db.session.query(Supplier).filter_by(supplier_id=order.supplier_id).first()
        product = db.session.query(Product).join(OrderItem, OrderItem.p_id == Product.p_id).filter(OrderItem.item_id == order.item_id).first()
        user = db.session.query(User).filter_by(u_id=order.u_id).first()
        order_data = {
            "order_id": order.order_id,
            "product": None,
            "user": None,
            "supplier": None,
            "created_at": order.created_at
        }

        if product:
            order_data["product"] = {
                "p_id": product.p_id,
                "title": product.title,
                "description": product.description,
                "quantity": product.quantity,
                "size": product.size,
                "price": product.price
            }

        if user:
            order_data["user"] = {
                "u_name": user.u_name,
                "u_email": user.u_email,
                "u_details": user.u_details
            }

        if supplier:
            order_data["supplier"] = {
                "supplier_id": supplier.supplier_id,
                "name": supplier.name,
                "contact_info": supplier.contact_info
            }

        order_list.append(order_data)
    
    return jsonify(order_list)



@app.route('/addOrder', methods=['POST'])
@user_required
def addOrder():
    if request.method == "POST":
        product= request.json  # Get the JSON data from the request
        item_id= product.get('item_id')
        u_id= product.get('u_id')
        supplier_id= product.get('supplier_id')
        stmt = insert(Order).values(item_id=item_id, u_id=u_id, supplier_id=supplier_id)
        db.session.execute(stmt)
        db.session.commit()
        return jsonify({"message": "Order Created successfully"}), 201
            
    else:
        return jsonify({"message": "Invalid request"}), 400

# Order are not updated or deleted  

if __name__ == '__main__':
    app.run(debug=True)
    




