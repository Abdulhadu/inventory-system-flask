from app import db
from flask_login import LoginManager , UserMixin , login_required ,login_user, logout_user,current_user
from datetime import datetime
from flask_serialize import FlaskSerialize


fs_mixin = FlaskSerialize(db)

class Product(db.Model, fs_mixin):
    p_id = db.Column(db.Integer, primary_key=True)
    c_id = db.Column(db.Integer, db.ForeignKey('category.c_id'))
    title = db.Column(db.String(128))
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer)
    size = db.Column(db.String(64))
    price = db.Column(db.Float)
    
    # serializer fields
    __fs_create_fields__ = __fs_update_fields__ = ['title', 'description', 'quantity', 'size', 'price']

    def __fs_can_delete__(self):
        if self.price == 1234:
            raise Exception('Deletion not allowed. Magic value!')
        return True

    def __fs_verify__(self, create=False):
        if len(self.title or '') < 1:
            raise Exception('Missing title')
        return True

    def __repr__(self):
        return f'<Product {self.p_id} {self.title}>'
    
    
    


class Category(db.Model):
    c_id = db.Column(db.Integer, primary_key=True)
    c_name = db.Column(db.String(128))
    c_description = db.Column(db.Text)

class User(UserMixin, db.Model):
    u_id = db.Column(db.Integer, primary_key=True)
    u_name = db.Column(db.String(128), unique=True, nullable=False) 
    u_email = db.Column(db.String(128),unique=True)
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
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128),unique=True, nullable=False)
    password = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=True)
    
    def get_id(self):
        return str(self.id) 
    
    
class MacAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(17))  # Length of MAC address string
    user_id = db.Column(db.Integer, db.ForeignKey('user.u_id'), nullable=False)
    

