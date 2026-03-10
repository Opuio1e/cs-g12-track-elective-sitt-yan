from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from main_app.models import Course, CustomUser, Session, Student


FIRST_NAMES = [
    "Aiden", "Liam", "Noah", "Ethan", "Mason", "Elijah", "Lucas", "James", "Henry", "Levi",
    "Olivia", "Emma", "Ava", "Sophia", "Mia", "Amelia", "Harper", "Evelyn", "Abigail", "Ella",
]

LAST_NAMES = [
    "Smith", "Johnson", "Brown", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin",
    "Garcia", "Clark", "Lewis", "Walker", "Hall", "Allen", "Young", "King", "Wright", "Scott",
]


class Command(BaseCommand):
    help = "Seed demo student accounts"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=25, help="Number of students to seed")
        parser.add_argument("--password", type=str, default="Student123!", help="Password for seeded students")

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]
        if count <= 0:
            self.stdout.write(self.style.WARNING("Count must be greater than zero."))
            return

        password = options["password"]
        course = self._ensure_course()
        session = self._ensure_session()

        created = 0
        reused = 0

        for idx in range(count):
            first_name = FIRST_NAMES[idx % len(FIRST_NAMES)]
            last_name = LAST_NAMES[idx % len(LAST_NAMES)]
            email = f"student{idx + 1:03d}@trinityschool.edu"

            user = CustomUser.objects.filter(email=email).first()
            if user is None:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    user_type=3,
                    first_name=first_name,
                    last_name=last_name,
                    gender="M" if idx % 2 == 0 else "F",
                    address=f"Seed Address {idx + 1}",
                    profile_pic="",
                )
                created += 1
            else:
                reused += 1

            student, _ = Student.objects.get_or_create(admin=user)
            student.course = course
            student.session = session
            student.save()

        self.stdout.write(self.style.SUCCESS(
            f"Seeding complete. Created: {created}, existing reused: {reused}, total requested: {count}."
        ))
        self.stdout.write(
            f"Course: {course.name} | Session: {session.start_year} to {session.end_year} | Password: {password}"
        )

    def _ensure_course(self):
        course, _ = Course.objects.get_or_create(name="Computer Science")
        return course

    def _ensure_session(self):
        start = date(date.today().year, 1, 1)
        end = date(date.today().year, 12, 31)
        session, _ = Session.objects.get_or_create(start_year=start, end_year=end)
        return session
