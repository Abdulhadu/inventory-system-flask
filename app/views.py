from flask   import Flask, render_template, request, session,  redirect, flash , jsonify
from jinja2  import TemplateNotFound
from app import app
from app import db 
from app.models import Product, Category, User
from flask_login import LoginManager , UserMixin , login_required ,login_user, logout_user,current_user
from sqlalchemy import insert, update, delete

login_manager = LoginManager()
login_manager.init_app(app)



# App main route + generic routing
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


@login_manager.user_loader
def load_user(u_id):
    return User.query.get(u_id)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_data = request.json  # Get the JSON data from the request
        username = user_data.get('username')
        password = user_data.get('password')
        user = User.query.filter_by(u_name=username).first()
        if user and user.password == password:
            login_user(user)
            return jsonify({"message": "Logged In"}), 200
        else:
            return jsonify({'error':'Invalid Credentials'}),401
    else:
        return jsonify({"message": "Login failed"}), 401



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



@app.route('/filter-products', methods=['POST'])
def filter_products():
    if current_user.is_authenticated:
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
    else:
        return jsonify("You are not logged in")
    
    
# ---------------------------------- Product Section ------------------------
    
    
@app.route('/products', methods=['GET'])
def get_products():
    products = db.session.query(Product).all()
    
    product_list = []
    for product in products:
        product_data = {
            "p_id": product.p_id,
            "c_id": product.c_id,
            "title": product.title,
            "description": product.description,
            "quantity": product.quantity,
            "size": product.size,
            "price": product.price
        }
        product_list.append(product_data)
    
    return jsonify(product_list)


@app.route('/addProducts', methods=['POST'])
def addProducts():
    if request.method == "POST":
        product= request.json  # Get the JSON data from the request
        c_id = product.get('c_id')
        title= product.get('title')
        description = product.get('description')
        quantity = product.get('quantity')
        size = product.get('size')
        price = product.get('price')
        stmt = insert(Product).values(c_id=c_id, title=title, description=description, quantity=quantity, size=size, price=price)
        db.session.execute(stmt)
        db.session.commit()
        
        return jsonify({"message": "Product added successfully"}), 201
    else:
        return jsonify({"message": "Invalid request"}), 400

         
@app.route('/updateProduct/<int:sno>', methods=['PATCH'])
def updateProducts(sno):
    if request.method == "PATCH":
        product = request.json 
        c_id = product.get('c_id')
        title = product.get('title')
        description = product.get('description')
        quantity = product.get('quantity')
        size = product.get('size')
        price = product.get('price')
        existing_product = Product.query.get(sno)
        
        if not existing_product:
            return jsonify({"error": "Category not found"}), 404
        
        if existing_product.p_id != sno:
            return jsonify({"error": "Provided c_id does not match sno"}), 400
        
        update_stmt = (update(Product)
            .where(Product.p_id == sno)
            .values(
                c_id=c_id,
                title=title,
                description=description,
                quantity=quantity,
                size=size,
                price=price
            )
        )
        db.session.execute(update_stmt)
        db.session.commit()
        
        return jsonify({"message": "Product added successfully"}), 201
    else:
        return jsonify({"message": "Invalid request"}), 400  



@app.route('/deleteProduct/<int:sno>', methods=['DELETE'])
def deleteProduct(sno):
        delete_stmt = (delete(Product).where(Product.p_id == sno))
        db.session.execute(delete_stmt)
        db.session.commit()
        return jsonify({'message': 'product deleted'})   
    
    
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
def deleteCategory(sno):
        delete_stmt = (delete(Category).where(Category.c_id == sno))
        db.session.execute(delete_stmt)
        db.session.commit()
        return jsonify({'message': 'product deleted'})   
    
# ---------------------------- Create user -------------------------------


    
@app.route('/user', methods=['GET'])
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



# @app.route('/addUser', methods=['POST'])
# def addUser():
#     if request.method == "POST":
#         product= request.json  # Get the JSON data from the request
#         u_name= product.get('u_name')
#         u_email= product.get('u_email')
#         c_details= product.get('u_details')
#         password= product.get('password')
#         stmt = insert(User).values(u_name=u_name, u_email=u_email, c_details=c_details, password=password)
#         db.session.execute(stmt)
#         db.session.commit()
        
#         return jsonify({"message": "User added successfully"}), 201
#     else:
#         return jsonify({"message": "Invalid request"}), 400

         
# @app.route('/updateUser/<int:sno>', methods=['PATCH'])
# def updateUser(sno):
#     if request.method == "PATCH":
#         product = request.json 
#         u_name= product.get('c_name')
#         u_description= product.get('c_description')
#         existing_category = User.query.get(sno)
        
#         if not existing_category:
#             return jsonify({"error": "User not found"}), 404
        
#         if existing_category.u_id != sno:
#             return jsonify({"error": "Provided userid does not match sno"}), 400
        
#         update_stmt = (update(Category).where(Category.c_id == sno).values(c_name=c_name, c_description=c_description)
#         )
#         db.session.execute(update_stmt)
#         db.session.commit()
        
#         return jsonify({"message": "Category added successfully"}), 201
#     else:
#         return jsonify({"message": "Invalid request"}), 400  



# @app.route('/deleteCategory/<int:sno>', methods=['DELETE'])
# def deleteUser(sno):
#         delete_stmt = (delete(Category).where(Category.c_id == sno))
#         db.session.execute(delete_stmt)
#         db.session.commit()
#         return jsonify({'message': 'product deleted'})   
    

if __name__ == '__main__':
    app.run(debug=True)
    




