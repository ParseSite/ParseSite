from django.db.models import Count
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from blog.models import Post, User, SavePost
from django.contrib.auth import  logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import EmailMessage
from django.contrib.auth.forms import AuthenticationForm
from .models import profile as Profile
from django.db.models.functions import Lower

from rest_framework.response import Response
from rest_framework.decorators import api_view


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            username = form.cleaned_data.get('username')
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your Parse account.'
            message = render_to_string('users/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()

            messages.success(request, f'Please confirm your email address to complete the registration')

            return redirect(request.META.get('HTTP_REFERER'))
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def myuser_login(request, pk=None):

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            # log in the user
            user = form.get_user()
            login(request, user)
            if pk is not None:
                return redirect(reverse('post-detail', kwargs={'pk': pk}))
            return redirect('blog-home')
    else:
        form = AuthenticationForm
    return render(request, 'users/login.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'users/profile.html', context)


def UserPageView(request, username):
    user = User.objects.filter(username=username).first()
    flag = False
    if request.user == user:
        flag = True

    context = {
        'user': user,
        'is_itself': flag,
        'posts': Post.objects.filter(author=user),
        'interest': SavePost.objects.filter(user=user)
    }

    return render(request, 'users/user_page.html', context)


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(request, f'Thank you for your email confirmation. Now you can login your account.')
        return redirect('login')
        # return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        return HttpResponse('Activation link is invalid!')


@api_view(['GET', 'POST', ])
def users_search(request):
    # profiles = Profile \
    #     .objects \
    #     .values('user__username') \
    #     .annotate(Count('user__username')) \
    #     .order_by(Lower('user__username'))

    profiles = Profile \
        .objects \
        .values('user__username', 'image') \
        .annotate(Count('user__username')) \
        .order_by(Lower('user__username'))
    data = {
        "profiles": profiles,
    }
    return Response(data)
