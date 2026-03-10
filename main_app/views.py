import json
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .EmailBackend import EmailBackend
from .face_auth import cosine_similarity, extract_face_embedding, image_data_to_bgr
from .forms import StudentForm
from .models import Attendance, CustomUser, FaceLoginProfile, Session, Subject

# Create your views here.


FACE_MATCH_THRESHOLD = 0.72


def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    return render(request, 'main_app/login.html')


def signup_page(request):
    if request.user.is_authenticated:
        return redirect(_redirect_for_user(request.user))

    form = StudentForm(request.POST or None, request.FILES or None)
    context = {
        'form': form,
    }

    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            course = form.cleaned_data.get('course')
            session = form.cleaned_data.get('session')
            passport = request.FILES.get('profile_pic')

            try:
                user = CustomUser.objects.create_user(
                    email=email,
                    password=password,
                    user_type=3,
                    first_name=first_name,
                    last_name=last_name,
                    profile_pic=passport,
                )
                user.gender = gender
                user.address = address
                user.student.course = course
                user.student.session = session
                user.save()
                user.student.save()
                login(request, user)
                messages.success(request, 'Your account has been created successfully.')
                return redirect(reverse('student_home'))
            except Exception:
                messages.error(request, 'Sign up failed. Please try again.')
        else:
            messages.error(request, 'Please correct the errors in the form.')

    return render(request, 'main_app/signup.html', context)


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        #Authenticate
        user = EmailBackend.authenticate(request, username=request.POST.get('email'), password=request.POST.get('password'))
        if user != None:
            login(request, user)
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("staff_home"))
            else:
                return redirect(reverse("student_home"))
        else:
            messages.error(request, "Invalid details")
            return redirect("/")


def _redirect_for_user(user):
    if user.user_type == '1':
        return reverse("admin_home")
    if user.user_type == '2':
        return reverse("staff_home")
    return reverse("student_home")


def _extract_embedding_from_payload(payload):
    image_data = payload.get("image_data")
    image = image_data_to_bgr(image_data)
    return extract_face_embedding(image)


@login_required
def face_id_settings(request):
    profile = FaceLoginProfile.objects.filter(user=request.user).first()
    context = {
        "page_title": "Face Login Setup",
        "profile": profile,
        "face_match_threshold": int(FACE_MATCH_THRESHOLD * 100),
    }
    return render(request, "main_app/face_id_settings.html", context)


@require_POST
@login_required
def face_id_register_begin(request):
    request.session["face_register_user"] = request.user.id
    return JsonResponse({"ok": True})


@require_POST
@login_required
def face_id_register_finish(request):
    body = json.loads(request.body.decode("utf-8"))
    user_id = request.session.get("face_register_user")
    if user_id != request.user.id:
        return JsonResponse({"error": "Registration session expired. Try again."}, status=400)

    try:
        embedding = _extract_embedding_from_payload(body)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    FaceLoginProfile.objects.update_or_create(
        user=request.user,
        defaults={
            "embedding": embedding,
        },
    )
    request.session.pop("face_register_user", None)
    return JsonResponse({"ok": True})


@require_POST
def face_id_login_begin(request):
    body = json.loads(request.body.decode("utf-8"))
    email = (body.get("email") or "").strip().lower()
    if not email:
        return JsonResponse({"error": "Enter your email first."}, status=400)
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return JsonResponse({"error": "No account found for this email."}, status=404)

    if not FaceLoginProfile.objects.filter(user=user).exists():
        return JsonResponse({"error": "Face ID is not enabled for this account yet."}, status=400)

    request.session["face_login_user"] = user.id
    return JsonResponse({"ok": True})


@require_POST
def face_id_login_finish(request):
    body = json.loads(request.body.decode("utf-8"))
    user_id = request.session.get("face_login_user")
    if not user_id:
        return JsonResponse({"error": "Authentication session expired. Try again."}, status=400)

    profile = get_object_or_404(FaceLoginProfile, user_id=user_id)
    try:
        probe_embedding = _extract_embedding_from_payload(body)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)

    score = cosine_similarity(profile.embedding, probe_embedding)
    if score < FACE_MATCH_THRESHOLD:
        return JsonResponse({"error": "Face match failed. Try again with good lighting and camera angle."}, status=401)

    user = profile.user
    login(request, user)
    request.session.pop("face_login_user", None)
    return JsonResponse({"ok": True, "redirect_url": _redirect_for_user(user), "score": round(score, 3)})



def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")


@csrf_exempt
def get_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(subject=subject, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                    "id": attd.id,
                    "attendance_date": str(attd.date),
                    "session": attd.session.id
                    }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None


def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in
// your app's Firebase config object.
// https://firebase.google.com/docs/web/setup#config-object
firebase.initializeApp({
    apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
    authDomain: "sms-with-django.firebaseapp.com",
    databaseURL: "https://sms-with-django.firebaseio.com",
    projectId: "sms-with-django",
    storageBucket: "sms-with-django.appspot.com",
    messagingSenderId: "945324593139",
    appId: "1:945324593139:web:03fa99a8854bbd38420c86",
    measurementId: "G-2F2RXTL9GT"
});

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
messaging.setBackgroundMessageHandler(function (payload) {
    const notification = JSON.parse(payload);
    const notificationOption = {
        body: notification.body,
        icon: notification.icon
    }
    return self.registration.showNotification(payload.notification.title, notificationOption);
});
    """
    return HttpResponse(data, content_type='application/javascript')
