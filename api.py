
import json
import datetime
from flask import *
from flask_mongoengine import MongoEngine
from flask_cors import CORS

app = Flask(__name__)
app.config['MONGODB_SETTINGS'] = json.load(open("config.json", "r"))
db = MongoEngine(app)
CORS(app)

class User(db.Document):
	username = db.StringField(required=True, unique=True, max_length=100)
	email = db.EmailField(required=True, max_length=100)
	pwd = db.StringField(required=True, max_length=200)
	


class Recipe(db.Document):
	name = db.StringField(required=True, unique=True, max_length=50)
	ingredients = db.DictField(required=True)	# stored as {prodType:qty}
	instructions = db.StringField(required=True)

	def canMake(self):
		for key in self.ingredients:
			if Product.objects(prodType=key).count() < self.ingredients[key]:
				return False
		return True

	def clearIngredients(self):
		for key in self.ingredients:

			# if only one ingredient of this type used, simply delete
			if self.ingredients[key] == 1:
				Product.objects(prodType=key).delete()
			
			# otherwise get and delete number used
			else:
				for i in range(self.ingredients[key]):
					Product.objects(prodType=key).first().delete()

class Product(db.Document):
	prodType = db.StringField(required=True, max_length=50)	# stored as lowercase
	expDate = db.DateTimeField(required=True)
	note = db.StringField(max_length=50)

	def isExpired(self):
		currentDate = datetime.datetime.today()
		if self.expDate < currentDate:
			return True	
		else:
			return False

	def willExpireSoon(self):
		currentDate = datetime.datetime.today()
		targetDate = self.expDate - datetime.timedelta(days=3)
		if targetDate < currentDate < self.expDate:
			return True
		else:
			return False


# @app.route('/register', methods=['POST'])
# def add_user():
# 	json = 

@app.route('/', methods=['GET'])
def index():
	currentDate = datetime.datetime.today()
	return render_template("test.html", currentDate=currentDate)

@app.route('/products', methods=['GET'])
def getProducts():
	''' returns JSON of all documents in product collection
	'''

	data = Product.objects.order_by("prodType", "expDate")
	return jsonify(data)

@app.route('/recipes', methods=['GET'])
def getRecipes():
	''' returns JSON of all documents in recipes collection
	'''

	data = Recipe.objects.order_by("name")
	return jsonify(data)

@app.route('/expired', methods=['GET'])
def getExpired():
	''' returns JSON of all expired products
	'''

	expired = []
	# scans through all products
	for product in Product.objects:
		# if product is expired, add to JSON
		if product.isExpired():
			expired += [product]
	return jsonify(expired)

@app.route('/expiring', methods=['GET'])
def getExpiring():
	''' returns JSON of soon-to-expire products
	'''

	expiring = []
	# scans through all products
	for product in Product.objects:
		# if product is expiring, add to JSON
		if product.willExpireSoon():
			expiring += [product]
	return jsonify(expiring)

@app.route('/add-product', methods=['POST'])
def addProduct():
	''' takes in a product type, expiration date, any notes
		generates a new Product object. JSON format must be
		as follows:

		{
			"prodType" : "example name",
			"expDate": "1/1/1970",
			"note": "example note"
		}
	'''

	# recieve and parse incoming JSON data
	import datetime
	data = request.get_json()
	prodType = data["prodType"].lower()
	expDate = datetime.datetime.strptime(data["expDate"], '%m %d %Y')
	note = data["note"]

	# Creates new Product object and saves it to database
	if note == None:
		newProduct = Product(
			prodType=prodType,
			expDate=expDate,
		)
	else:
		newProduct = Product(
			prodType=prodType,
			expDate=expDate,
			note=note
		)
	newProduct.save()

	return jsonify(success=True)

@app.route('/add-recipe', methods=['POST'])
def addRecipe():
	''' adds recipe to database. JSON format must be
		as follows:

		{
			"rcpName": "example name",
			"ingredients": {
				"example ingredient name" : 4,
				"example ingredient name" : 2
			},
			"instructions": "example instructions"
		}
	'''

	# recieve and parse incoming JSON data
	data = request.get_json()
	rcpName = data["rcpName"]
	ingredients = data["ingredients"]
	instructions = data["instructions"]

	# Creates new Recipe object
	newRecipe = Recipe(
		name=rcpName,
		ingredients=ingredients,
		instructions=instructions
	)
	newRecipe.save()

	return jsonify(success=True)

@app.route('/delete-product', methods=['POST'])
def deleteProduct():
	''' deletes one or all items from inventory. JSON format must be
		as follows:

		{
			"prodId": "last four characters of Mongo _id"
		}
	'''

	# immediately returns if no products in db
	if Product.objects.count() == 0:
		return jsonify(success=False, message="No products in database.")

	# recieve and parse incoming JSON data
	data = request.get_json()
	prodId = data["prodId"]

	if prodId == "all":
		Product.objects.delete()
		return jsonify(success=True)
	else:
		# finds and deletes product after confirmation
		for product in Product.objects():
			targ = str(product.id)[-4:]
			if targ == prodId:
				product.delete()
				return jsonify(success=True)
		return jsonify(success=False, message="Invalid ID. Check inventory and make sure ID is correct.")

@app.route('/delete-recipe', methods=['POST'])
def deleteRecipe():
	''' deletes one or all recipes from database. JSON format must be
		as follows:

		{
			"rcpId": "last four characters of Mongo _id"
		}
	'''

	# immediately returns if no recipes in db
	if Recipe.objects.count() == 0:
		return jsonify(success=False, message="No recipes in database.")

	# recieve and parse incoming JSON data
	data = request.get_json()
	rcpId = data["rcpId"]

	if rcpId == "all":
		Recipe.objects.delete()
		return jsonify(success=True)
	else:
		# finds and deletes recipe after confirmation
		for recipe in Recipe.objects():
			targ = str(recipe.id)[-4:]
			if targ == rcpId:
				recipe.delete()
				return jsonify(success=True)
		return jsonify(success=False, message="Invalid ID. Check inventory and make sure ID is correct.")
	
def add_cors_headers(response):
	response.headers['Access-Control-Allow-Origin'] = '*'
	return response

if __name__ == "__main__":

	
	app.run(debug=True)
