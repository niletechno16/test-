from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile


# ---------------- ROLES ----------------
def get_role(user):
    try:
        return user.profile.role
    except:
        return None

def is_high_level(user):
    return get_role(user) in ['developer', 'owner']

def is_manager_level(user):
    return get_role(user) in ['developer', 'owner', 'admin']

def can_change_role(changer, target_role):
    changer_role = get_role(changer)
    protected = {'developer': ['owner'], 'owner': ['developer']}
    if changer_role in protected and target_role in protected[changer_role]:
        return False
    return True


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        # دخول كزائر
        if action == 'visitor':
            visitor_user, created = User.objects.get_or_create(username='visitor')
            if created:
                visitor_user.set_password('visitor123')
                visitor_user.save()

            # تأكد إن الـ profile موجود
            profile, profile_created = UserProfile.objects.get_or_create(
                user=visitor_user,
                defaults={
                    'agent_id': '0000000000',
                    'role': 'visitor',
                    'is_first_login': False,
                }
            )
            # لو الـ profile موجود بس الـ role مش visitor
            if not profile_created and profile.role != 'visitor':
                profile.role = 'visitor'
                profile.save()

            login(request, visitor_user)
            return redirect('home')

        # دخول عادي
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)

        if not user:
            try:
                profile = UserProfile.objects.get(agent_id=int(username))
                user = authenticate(request, username=profile.user.username, password=password)
            except (UserProfile.DoesNotExist, ValueError):
                pass

        if user:
            login(request, user)
            if user.profile.is_first_login:
                return redirect('change_password')
            return redirect('home')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')

    return render(request, 'users/login.html')


# ---------------- CHANGE PASSWORD ----------------
@login_required
def change_password(request):
    if request.method == 'POST':
        new_username = request.POST.get('new_username', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm      = request.POST.get('confirm_password', '').strip()

        error = False

        if new_username and new_username != request.user.username:
            if User.objects.filter(username=new_username).exists():
                messages.error(request, 'اسم المستخدم مستخدم بالفعل')
                error = True
            else:
                request.user.username = new_username
                request.user.save()

        if not error:
            if new_password != confirm:
                messages.error(request, 'كلمات المرور غير متطابقة')
                error = True
            elif len(new_password) < 6:
                messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل')
                error = True

        if not error:
            request.user.set_password(new_password)
            request.user.save()
            request.user.profile.is_first_login = False
            request.user.profile.save()
            update_session_auth_hash(request, request.user)
            return redirect('home')

    return render(request, 'users/change_password.html', {
        'current_username': request.user.username,
        'agent_id': request.user.profile.agent_id,
    })


# ---------------- PROFILE ----------------
@login_required
def profile(request):
    return render(request, 'users/profile.html', {
        'role':       get_role(request.user),
        'is_manager': is_manager_level(request.user),
        'agent_id':   request.user.profile.agent_id,
    })


# ---------------- MANAGE USERS ----------------
@login_required
def manage_users(request):
    if not is_high_level(request.user):
        return redirect('home')

    profiles = UserProfile.objects.select_related('user').exclude(role='visitor')

    if request.method == 'POST':
        agent_id = request.POST.get('agent_id', '').strip()
        name     = request.POST.get('name', '').strip()
        role     = request.POST.get('role', 'agent')
        phone    = request.POST.get('phone', '').strip()

        if UserProfile.objects.filter(agent_id=agent_id).exists():
            messages.error(request, 'هذا الـ Agent ID مسجل بالفعل')
        else:
            user = User.objects.create_user(
                username=str(agent_id),
                password=str(agent_id),
                first_name=name
            )
            UserProfile.objects.create(
                user=user,
                phone_number=phone or agent_id,
                agent_id=int(agent_id),
                role=role,
                is_first_login=True
            )
            messages.success(request, f'تم إضافة {name} — الـ ID: {agent_id} — الباسورد المؤقت: {agent_id}')

    return render(request, 'users/manage.html', {
        'profiles':     profiles,
        'is_manager':   True,
        'role_choices': UserProfile.ROLE_CHOICES,
    })


# ---------------- CHANGE ROLE ----------------
@login_required
def change_role(request, user_id):
    if not is_high_level(request.user):
        return redirect('home')

    if request.method == 'POST':
        new_role = request.POST.get('role')
        try:
            profile = UserProfile.objects.get(user_id=user_id)
            if can_change_role(request.user, profile.role):
                profile.role = new_role
                profile.save()
                messages.success(request, 'تم تغيير الصلاحية')
            else:
                messages.error(request, 'غير مسموح بتغيير صلاحية هذا المستخدم')
        except UserProfile.DoesNotExist:
            messages.error(request, 'المستخدم غير موجود')

    return redirect('manage_users')


# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    return redirect('login')