from django.core.management.base import BaseCommand
from django.db import transaction

from main_app.models import Course, CustomUser, Staff


FIRST_NAMES = [
    "Avery", "Jordan", "Riley", "Morgan", "Skyler", "Casey", "Quinn", "Reese", "Taylor", "Parker",
    "Cameron", "Blake", "Drew", "Rowan", "Hayden", "Logan", "Payton", "Finley", "Alex", "Sage",
]

LAST_NAMES = [
    "Bennett", "Carter", "Davis", "Edwards", "Foster", "Graham", "Hayes", "Ingram", "Jenkins", "Knight",
    "Lawson", "Mitchell", "Nelson", "Owens", "Price", "Reed", "Simmons", "Turner", "Vaughn", "Ward",
]


class Command(BaseCommand):
    help = "Seed demo staff accounts"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=8, help="Number of staff to seed")
        parser.add_argument("--password", type=str, default="Staff123!", help="Password for seeded staff")

    @transaction.atomic
    def handle(self, *args, **options):
        count = options["count"]
        if count <= 0:
            self.stdout.write(self.style.WARNING("Count must be greater than zero."))
            return

        password = options["password"]
        course = self._ensure_course()
        created = 0
        reused = 0

        for idx in range(count):
            first_name = FIRST_NAMES[idx % len(FIRST_NAMES)]
            last_name = LAST_NAMES[idx % len(LAST_NAMES)]
            email = f"staff{idx + 1:03d}@trinityschool.edu"

            user = CustomUser.objects.filter(email=email).first()
            if user is None:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    user_type=2,
                    first_name=first_name,
                    last_name=last_name,
                    gender="M" if idx % 2 == 0 else "F",
                    address=f"Staff Address {idx + 1}",
                    profile_pic="",
                )
                created += 1
            else:
                reused += 1

            staff, _ = Staff.objects.get_or_create(admin=user)
            staff.course = course
            staff.save()

        self.stdout.write(self.style.SUCCESS(
            f"Seeding complete. Created: {created}, existing reused: {reused}, total requested: {count}."
        ))
        self.stdout.write(f"Course: {course.name} | Password: {password}")

    def _ensure_course(self):
        course, _ = Course.objects.get_or_create(name="Computer Science")
        return course
