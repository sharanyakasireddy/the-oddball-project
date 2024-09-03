from app import db, User

# Add test hospitals
hospital1 = User(username="hospital1", password="hospitalpass1", role="hospital")
hospital2 = User(username="hospital2", password="hospitalpass2", role="hospital")
hospital3 = User(username="hospital3", password="hospitalpass3", role="hospital")

# Add the hospitals to the session and commit them to the database
db.session.add(hospital1)
db.session.add(hospital2)
db.session.add(hospital3)
db.session.commit()

print("Test hospitals added successfully!")
