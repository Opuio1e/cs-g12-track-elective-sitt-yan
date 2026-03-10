import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from main_app.models import (
    Attendance,
    AttendanceReport,
    Course,
    CustomUser,
    FeedbackStaff,
    FeedbackStudent,
    LeaveReportStaff,
    LeaveReportStudent,
    NotificationStaff,
    NotificationStudent,
    Session,
    Staff,
    Student,
    StudentAttendanceSelfReport,
    StudentResult,
    Subject,
)


class Command(BaseCommand):
    help = "Seed complete demo data: courses, sessions, users, subjects, attendance, and related records"

    def add_arguments(self, parser):
        parser.add_argument("--courses", type=int, default=4, help="Number of courses")
        parser.add_argument("--staff-per-course", type=int, default=3, help="Staff per course")
        parser.add_argument("--students-per-course", type=int, default=15, help="Students per course")
        parser.add_argument("--subjects-per-course", type=int, default=4, help="Subjects per course")
        parser.add_argument("--attendance-days", type=int, default=8, help="Attendance dates per subject")
        parser.add_argument("--staff-password", type=str, default="Staff123!", help="Password for seeded staff")
        parser.add_argument("--student-password", type=str, default="Student123!", help="Password for seeded students")

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(2026)
        courses_count = max(1, options["courses"])
        staff_per_course = max(1, options["staff_per_course"])
        students_per_course = max(1, options["students_per_course"])
        subjects_per_course = max(1, options["subjects_per_course"])
        attendance_days = max(1, options["attendance_days"])

        current_year = date.today().year
        session, _ = Session.objects.get_or_create(
            start_year=date(current_year, 1, 1),
            end_year=date(current_year, 12, 31),
        )

        course_names = [
            "Computer Science",
            "Business Studies",
            "Natural Sciences",
            "Humanities",
            "Information Technology",
            "Accounting",
            "Engineering",
            "Education",
        ]
        subject_roots = [
            "Mathematics",
            "English",
            "Programming",
            "Data Science",
            "Physics",
            "Chemistry",
            "Biology",
            "Economics",
            "History",
            "Civics",
            "Networks",
            "Statistics",
        ]

        first_names = [
            "Aiden", "Noah", "Liam", "Ethan", "James", "Lucas", "Henry", "Levi", "Jack", "Owen",
            "Olivia", "Emma", "Ava", "Sophia", "Mia", "Amelia", "Harper", "Evelyn", "Ella", "Aria",
            "Avery", "Jordan", "Taylor", "Riley", "Parker", "Morgan", "Quinn", "Casey", "Reese", "Logan",
        ]
        last_names = [
            "Smith", "Johnson", "Brown", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin",
            "Garcia", "Clark", "Lewis", "Walker", "Hall", "Allen", "Young", "King", "Wright", "Scott",
            "Bennett", "Carter", "Davis", "Edwards", "Foster", "Graham", "Hayes", "Jenkins", "Knight", "Turner",
        ]

        courses = []
        for idx in range(courses_count):
            name = course_names[idx] if idx < len(course_names) else f"Course {idx + 1}"
            course, _ = Course.objects.get_or_create(name=name)
            courses.append(course)

        seeded_staff = []
        seeded_students = []
        seeded_subjects = []
        created_counters = {
            "staff_users": 0,
            "student_users": 0,
            "subjects": 0,
            "attendance": 0,
            "attendance_reports": 0,
            "results": 0,
            "feedback": 0,
            "leave_reports": 0,
            "notifications": 0,
            "self_reports": 0,
        }

        for c_idx, course in enumerate(courses, start=1):
            for s_idx in range(1, staff_per_course + 1):
                email = f"staff{c_idx:02d}{s_idx:02d}@trinityschool.edu"
                first = first_names[(c_idx * 3 + s_idx) % len(first_names)]
                last = last_names[(c_idx * 7 + s_idx) % len(last_names)]
                user = CustomUser.objects.filter(email=email).first()
                if user is None:
                    user = CustomUser.objects.create_user(
                        email=email,
                        password=options["staff_password"],
                        user_type=2,
                        first_name=first,
                        last_name=last,
                        gender="M" if (c_idx + s_idx) % 2 == 0 else "F",
                        address=f"Staff Address {course.name} #{s_idx}",
                        profile_pic="",
                    )
                    created_counters["staff_users"] += 1
                staff, _ = Staff.objects.get_or_create(admin=user)
                if staff.course_id != course.id:
                    staff.course = course
                    staff.save()
                seeded_staff.append(staff)

            for st_idx in range(1, students_per_course + 1):
                email = f"student{c_idx:02d}{st_idx:03d}@trinityschool.edu"
                first = first_names[(c_idx * 5 + st_idx) % len(first_names)]
                last = last_names[(c_idx * 11 + st_idx) % len(last_names)]
                user = CustomUser.objects.filter(email=email).first()
                if user is None:
                    user = CustomUser.objects.create_user(
                        email=email,
                        password=options["student_password"],
                        user_type=3,
                        first_name=first,
                        last_name=last,
                        gender="M" if (c_idx + st_idx) % 2 == 0 else "F",
                        address=f"Student Address {course.name} #{st_idx}",
                        profile_pic="",
                    )
                    created_counters["student_users"] += 1
                student, _ = Student.objects.get_or_create(admin=user)
                updated = False
                if student.course_id != course.id:
                    student.course = course
                    updated = True
                if student.session_id != session.id:
                    student.session = session
                    updated = True
                if updated:
                    student.save()
                seeded_students.append(student)

        for c_idx, course in enumerate(courses, start=1):
            course_staff = [s for s in seeded_staff if s.course_id == course.id]
            for sub_idx in range(1, subjects_per_course + 1):
                subject_name = f"{subject_roots[(sub_idx + c_idx) % len(subject_roots)]} {c_idx}.{sub_idx}"
                staff = course_staff[(sub_idx - 1) % len(course_staff)]
                subject, created = Subject.objects.get_or_create(
                    name=subject_name,
                    course=course,
                    defaults={"staff": staff},
                )
                if created:
                    created_counters["subjects"] += 1
                elif subject.staff_id != staff.id:
                    subject.staff = staff
                    subject.save(update_fields=["staff", "updated_at"])
                seeded_subjects.append(subject)

        base_day = date.today() - timedelta(days=attendance_days + 2)
        for subject in seeded_subjects:
            course_students = [s for s in seeded_students if s.course_id == subject.course_id]
            for day_idx in range(attendance_days):
                attendance_date = base_day + timedelta(days=day_idx)
                attendance, created = Attendance.objects.get_or_create(
                    session=session,
                    subject=subject,
                    date=attendance_date,
                )
                if created:
                    created_counters["attendance"] += 1

                for student in course_students:
                    status = rng.random() > 0.12
                    report, created_report = AttendanceReport.objects.get_or_create(
                        attendance=attendance,
                        student=student,
                        defaults={"status": status},
                    )
                    if created_report:
                        created_counters["attendance_reports"] += 1
                    elif report.status != status:
                        report.status = status
                        report.save(update_fields=["status", "updated_at"])

                    result = StudentResult.objects.filter(student=student, subject=subject).first()
                    test_score = round(rng.uniform(8, 20), 1)
                    exam_score = round(rng.uniform(20, 80), 1)
                    if result is None:
                        StudentResult.objects.create(
                            student=student,
                            subject=subject,
                            test=test_score,
                            exam=exam_score,
                        )
                        created_counters["results"] += 1
                    else:
                        result.test = test_score
                        result.exam = exam_score
                        result.save(update_fields=["test", "exam", "updated_at"])

                    _, created_self_report = StudentAttendanceSelfReport.objects.get_or_create(
                        student=student,
                        date=attendance_date,
                        defaults={
                            "status": "present" if status else "absent",
                            "note": "Seeded auto report",
                        },
                    )
                    if created_self_report:
                        created_counters["self_reports"] += 1

        for student in seeded_students:
            if not FeedbackStudent.objects.filter(student=student, feedback__startswith="Seed feedback").exists():
                FeedbackStudent.objects.create(
                    student=student,
                    feedback="Seed feedback from student",
                    reply="Thanks for your feedback.",
                )
                created_counters["feedback"] += 1

            if not LeaveReportStudent.objects.filter(student=student, message__startswith="Seed leave").exists():
                LeaveReportStudent.objects.create(
                    student=student,
                    date=str(date.today()),
                    message="Seed leave request for testing",
                    status=0,
                )
                created_counters["leave_reports"] += 1

            if not NotificationStudent.objects.filter(student=student, message__startswith="Seed notification").exists():
                NotificationStudent.objects.create(student=student, message="Seed notification for student")
                created_counters["notifications"] += 1

        for staff in seeded_staff:
            if not FeedbackStaff.objects.filter(staff=staff, feedback__startswith="Seed feedback").exists():
                FeedbackStaff.objects.create(
                    staff=staff,
                    feedback="Seed feedback from staff",
                    reply="Feedback reviewed.",
                )
                created_counters["feedback"] += 1

            if not LeaveReportStaff.objects.filter(staff=staff, message__startswith="Seed leave").exists():
                LeaveReportStaff.objects.create(
                    staff=staff,
                    date=str(date.today()),
                    message="Seed leave request for staff testing",
                    status=0,
                )
                created_counters["leave_reports"] += 1

            if not NotificationStaff.objects.filter(staff=staff, message__startswith="Seed notification").exists():
                NotificationStaff.objects.create(staff=staff, message="Seed notification for staff")
                created_counters["notifications"] += 1

        self.stdout.write(self.style.SUCCESS("Full seed completed successfully."))
        self.stdout.write(
            "Created/updated summary: "
            + ", ".join(f"{key}={value}" for key, value in created_counters.items())
        )
        self.stdout.write(
            f"Totals now -> courses={Course.objects.count()}, sessions={Session.objects.count()}, "
            f"staff={Staff.objects.count()}, students={Student.objects.count()}, subjects={Subject.objects.count()}, "
            f"attendance={Attendance.objects.count()}, attendance_reports={AttendanceReport.objects.count()}, "
            f"results={StudentResult.objects.count()}"
        )
