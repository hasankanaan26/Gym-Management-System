"""Seed the database with realistic sample data.

Usage:
    python -m app.seed
"""
import random
from datetime import datetime, time, timedelta, timezone

from app.core.db import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.enrollment import Enrollment
from app.models.gym_class import DayOfWeek, GymClass
from app.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)
from app.models.user import User, UserRole

MANAGER_EMAIL = "manager@gymapp.com"
MANAGER_PASSWORD = "manager123"

MEMBER_PASSWORD = "member123"

MEMBERS = [
    ("alice@gymapp.com", "Alice Nguyen"),
    ("bob@gymapp.com", "Bob Martinez"),
    ("charlie@gymapp.com", "Charlie O'Brien"),
    ("dana@gymapp.com", "Dana Schmidt"),
    ("eli@gymapp.com", "Eli Rahimi"),
    ("fatima@gymapp.com", "Fatima Haidari"),
    ("george@gymapp.com", "George Laurent"),
    ("hannah@gymapp.com", "Hannah Cohen"),
    ("ian@gymapp.com", "Ian Fitzgerald"),
    ("julia@gymapp.com", "Julia Rossi"),
    ("kai@gymapp.com", "Kai Nakamura"),
    ("leo@gymapp.com", "Leo Andersson"),
    ("mia@gymapp.com", "Mia Kowalski"),
    ("noah@gymapp.com", "Noah Petrov"),
    ("olivia@gymapp.com", "Olivia Dubois"),
    ("pedro@gymapp.com", "Pedro Alvarez"),
    ("quinn@gymapp.com", "Quinn Fletcher"),
    ("rosa@gymapp.com", "Rosa Delgado"),
    ("samir@gymapp.com", "Samir Qureshi"),
    ("tara@gymapp.com", "Tara Lindqvist"),
    ("umar@gymapp.com", "Umar Khan"),
    ("vera@gymapp.com", "Vera Volkova"),
    ("wesley@gymapp.com", "Wesley Carter"),
    ("xiu@gymapp.com", "Xiu Chen"),
    ("yasmin@gymapp.com", "Yasmin Al-Sayed"),
    ("zane@gymapp.com", "Zane Holloway"),
    ("amina@gymapp.com", "Amina Diallo"),
    ("bruno@gymapp.com", "Bruno Silva"),
    ("camille@gymapp.com", "Camille Fontaine"),
    ("dmitri@gymapp.com", "Dmitri Ivanov"),
    ("elena@gymapp.com", "Elena Marchetti"),
    ("finn@gymapp.com", "Finn O'Sullivan"),
    ("greta@gymapp.com", "Greta Jansen"),
    ("hugo@gymapp.com", "Hugo Bergström"),
    ("isabel@gymapp.com", "Isabel Navarro"),
    ("javier@gymapp.com", "Javier Cortez"),
    ("kenji@gymapp.com", "Kenji Yamamoto"),
    ("lena@gymapp.com", "Lena Horvath"),
    ("marco@gymapp.com", "Marco Bianchi"),
    ("nadia@gymapp.com", "Nadia Kowal"),
    ("omar@gymapp.com", "Omar Farouk"),
    ("priya@gymapp.com", "Priya Krishnan"),
    ("quentin@gymapp.com", "Quentin Dubois"),
    ("rania@gymapp.com", "Rania Mansour"),
    ("sergio@gymapp.com", "Sergio Ramos"),
    ("tomas@gymapp.com", "Tomas Novak"),
    ("uma@gymapp.com", "Uma Pillai"),
    ("viktor@gymapp.com", "Viktor Petrovic"),
    ("wendy@gymapp.com", "Wendy Zhao"),
    ("xander@gymapp.com", "Xander Brooks"),
    ("yara@gymapp.com", "Yara Haddad"),
    ("zoe@gymapp.com", "Zoe Whitaker"),
    ("anders@gymapp.com", "Anders Lindgren"),
    ("beatriz@gymapp.com", "Beatriz Carvalho"),
    ("cormac@gymapp.com", "Cormac Walsh"),
    ("diana@gymapp.com", "Diana Popescu"),
    ("esteban@gymapp.com", "Esteban Morales"),
    ("farida@gymapp.com", "Farida Amir"),
    ("gavin@gymapp.com", "Gavin Thornton"),
    ("helena@gymapp.com", "Helena Kovac"),
]

CLASSES = [
    ("Sunrise Yoga", "Gentle flow to start your day", "Priya Desai", DayOfWeek.MONDAY, time(7, 0), 60, 20),
    ("Spin Intervals", "High-energy indoor cycling", "Marcus Kane", DayOfWeek.MONDAY, time(18, 30), 45, 15),
    ("HIIT Blast", "Full-body high-intensity circuit", "Sofia Mendes", DayOfWeek.TUESDAY, time(12, 0), 30, 12),
    ("Strength 101", "Barbell basics for beginners", "Derrick Walsh", DayOfWeek.WEDNESDAY, time(17, 0), 60, 10),
    ("Pilates Core", "Mat-based core and mobility", "Anika Rao", DayOfWeek.THURSDAY, time(8, 0), 50, 14),
    ("Boxing Fundamentals", "Footwork, combos, pad work", "Luca Romano", DayOfWeek.FRIDAY, time(18, 0), 60, 16),
    ("Saturday Bootcamp", "Outdoor-style conditioning", "Marcus Kane", DayOfWeek.SATURDAY, time(9, 0), 60, 20),
    ("Sunday Stretch", "Recovery and mobility", "Priya Desai", DayOfWeek.SUNDAY, time(10, 0), 45, 25),
]


def reset(db):
    # Order matters because of FKs
    db.query(Enrollment).delete()
    db.query(Subscription).delete()
    db.query(GymClass).delete()
    db.query(User).delete()
    db.commit()


def run():
    # Make sure schema exists
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        reset(db)

        now = datetime.now(timezone.utc)

        manager = User(
            email=MANAGER_EMAIL,
            name="Gym Manager",
            password_hash=hash_password(MANAGER_PASSWORD),
            role=UserRole.MANAGER,
        )
        db.add(manager)

        members = []
        for i, (email, name) in enumerate(MEMBERS):
            u = User(
                email=email,
                name=name,
                password_hash=hash_password(MEMBER_PASSWORD),
                role=UserRole.MEMBER,
            )
            db.add(u)
            members.append(u)
        db.flush()

        # Give ~2/3 members an active sub, the rest expired
        for i, m in enumerate(members):
            if i % 3 == 0:
                started = now - timedelta(days=120)
                db.add(
                    Subscription(
                        user_id=m.id,
                        plan=SubscriptionPlan.MONTHLY,
                        status=SubscriptionStatus.EXPIRED,
                        started_at=started,
                        expires_at=started + timedelta(days=30),
                    )
                )
            else:
                plan = random.choice(
                    [SubscriptionPlan.MONTHLY, SubscriptionPlan.QUARTERLY, SubscriptionPlan.YEARLY]
                )
                duration = {
                    SubscriptionPlan.MONTHLY: 30,
                    SubscriptionPlan.QUARTERLY: 90,
                    SubscriptionPlan.YEARLY: 365,
                }[plan]
                db.add(
                    Subscription(
                        user_id=m.id,
                        plan=plan,
                        status=SubscriptionStatus.ACTIVE,
                        started_at=now - timedelta(days=5),
                        expires_at=now + timedelta(days=duration - 5),
                    )
                )

        classes = []
        for name, desc, trainer, day, start, duration, cap in CLASSES:
            c = GymClass(
                name=name,
                description=desc,
                trainer_name=trainer,
                day_of_week=day,
                start_time=start,
                duration_minutes=duration,
                capacity=cap,
            )
            db.add(c)
            classes.append(c)
        db.flush()

        # Enroll a handful of active-sub members in random classes
        random.seed(42)
        active_members = [m for i, m in enumerate(members) if i % 3 != 0]
        seen = set()
        for _ in range(120):
            m = random.choice(active_members)
            c = random.choice(classes)
            key = (m.id, c.id)
            if key in seen:
                continue
            seen.add(key)
            db.add(Enrollment(user_id=m.id, class_id=c.id))

        db.commit()

        print("=" * 60)
        print("Seeding complete.")
        print("=" * 60)
        print(f"Manager login:  {MANAGER_EMAIL} / {MANAGER_PASSWORD}")
        print(f"Member login:   alice@gymapp.com / {MEMBER_PASSWORD}   (and 14 others)")
        print(f"Classes:        {len(classes)}")
        print(f"Members:        {len(members)}")
        print(f"Enrollments:    {len(seen)}")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    run()
