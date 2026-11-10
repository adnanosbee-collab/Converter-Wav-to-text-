import getpass
import uuid

from sqlalchemy import select

from app.auth import hash_password
from app.database import SessionLocal
from app.models import User


def main():
    username = input("Username: ").strip().lower()

    if not username or len(username) > 80:
        raise SystemExit("Username must contain 1 to 80 characters.")

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")

    if password != confirm:
        raise SystemExit("Passwords do not match.")

    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(User.username == username)
        )

        if existing:
            raise SystemExit("That username already exists.")

        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password_hash=hash_password(password),
            is_active=True,
        )

        db.add(user)
        db.commit()

    print(f"Account created successfully for: {username}")


if __name__ == "__main__":
    main()
