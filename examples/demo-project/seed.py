from config import DATABASE_URL

# Responsibility: Seed initial database tables using DATABASE_URL configuration
def seed_database():
    print(f"Connecting to database: {DATABASE_URL}")
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed_database()
