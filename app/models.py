import csv
from .config import app, db

# Database model repr as python class
# Fields will be translated to cols in Db
class Car(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    car_id = db.Column(db.Integer, nullable=False)

    url = db.Column(db.String(256), unique=True, nullable=False)

    price = db.Column(db.Integer, nullable=False)

    mileage = db.Column(db.Integer, nullable=False)

    hp = db.Column(db.Integer, nullable=False)

    gearbox = db.Column(db.String(128), nullable=False)

    traffic_date = db.Column(db.String(128), nullable=False)

    owners = db.Column(db.Integer, nullable=False)

    fuel = db.Column(db.String(128), nullable=False)

    manufacturer = db.Column(db.String(128), nullable=False)

    model = db.Column(db.String(128), nullable=False)


def populate_database(path):
    """
    Populates database with entries from csv file in path.
    """
    with app.app_context():
        with open(path, 'r') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                car = Car(car_id=row['id'], 
                        url=row['url'], 
                        price=row['price'],
                        mileage=row['mileage'],
                        hp=row['hp'],
                        gearbox=row['gearbox'],
                        traffic_date=row['traffic_date'],
                        owners=row['owners'],
                        fuel=row['fuel'],
                        manufacturer=row['manufacturer'],
                        model=row['model'])
                db.session.add(car)

        db.session.commit()         


if __name__=="__main__":
    path = 'car_db_backup.csv'
    with app.app_context():
        db.create_all()

    populate_database(path)