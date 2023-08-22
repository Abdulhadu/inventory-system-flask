from flask   import Flask, render_template, request, session,  redirect, flash , jsonify
from jinja2  import TemplateNotFound
from app import app
from app import db 
from app.models import Product, Category, User

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_data = request.json  # Get the JSON data from the request
        username = user_data.get('username')
        password = user_data.get('password')
        user = User.query.filter_by(u_name=username, password=password).first()
        if user:
            session['username'] = username
            return jsonify({"message": "Logged In"}), 200
        else:
            return jsonify({'error':'Invalid Credentials'}),401
    else:
        return jsonify({"message": "Login failed"}), 401


@app.route('/logout', methods=['POST'])
def logout():
    if 'username' in session:
        session.pop('username', None)  # Remove the 'username' key from the session
        return jsonify({"message": "Logged out"}), 200
    else:
        return jsonify({"message": "Not logged in"}), 401



@app.route('/filter-products', methods=['POST'])
def filter_products():
    if 'username' in session:
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
        return jsonify({"You are not Logged In"})


if __name__ == '__main__':
    app.run(debug=True)
    




