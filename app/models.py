from app import db
from flask_login import LoginManager , UserMixin , login_required ,login_user, logout_user,current_user

class Product(db.Model):
    p_id = db.Column(db.Integer, primary_key=True)
    c_id = db.Column(db.Integer, db.ForeignKey('category.c_id'))
    title = db.Column(db.String(128))
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer)
    size = db.Column(db.String(64))
    price = db.Column(db.Float)

class Category(db.Model):
    c_id = db.Column(db.Integer, primary_key=True)
    c_name = db.Column(db.String(128))
    c_description = db.Column(db.Text)

class User(UserMixin, db.Model):
    u_id = db.Column(db.Integer, primary_key=True)
    u_name = db.Column(db.String(128), unique=True, nullable=False) 
    u_email = db.Column(db.String(128))
    u_details = db.Column(db.Text)
    password = db.Column(db.String(128))
    
    def get_id(self):
        return str(self.u_id) 

class Supplier(UserMixin, db.Model):
    supplier_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    contact_info = db.Column(db.String(128))

class OrderItem(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    p_id = db.Column(db.Integer, db.ForeignKey('product.p_id'))
    quantity = db.Column(db.Integer)

class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('order_item.item_id'))
    u_id = db.Column(db.Integer, db.ForeignKey('user.u_id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.supplier_id'))
    created_at = db.Column(db.DateTime)
