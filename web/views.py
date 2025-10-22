from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from web.filters import CourseFilter

from .models import CourseCategory, Basic_info, Slider, Course, Event, Project, CourseLevel, SingleVideo, Testimonial, \
    AboutUs, FAQ, UserMessage, Profile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse
from .forms import SignupForm, UserMessageForm, UserForm, ProfileForm, ContactForm, SubcriberForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import EmailMessage


def index(request):
    """Takdhum home page"""
    # Need for all view
    categories = CourseCategory.objects.all()
    basic_info = Basic_info.objects.first()

    sliders = Slider.objects.all()
    courses = Course.objects.all()[::-1]
    events = Event.objects.all().order_by('-upload_time')
    if len(events) > 3:
        events = events[0:3]
    projects = Project.objects.all().order_by('-upload_time')
    testimonials = Testimonial.objects.last()

    if request.method == 'POST':
        form = SubcriberForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'You successfully subscribe in Takdhum.')
    else:
        form = SubcriberForm()
    context = {
        'categories': categories,
        'slides': sliders,
        's': courses,
        'info': basic_info,
        'events': events,
        'projects': projects,
        't': testimonials,
        'form': form,
    }
    return render(request, 'takdhum/index.html', context)


def subscriber(request):
    if request.method == 'POST':
        form = SubcriberForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'You successfully subscribe in Takdhum.')
            return redirect('index')
        else:
            messages.error(request, 'Something Wrong!! Please try again.')
            return redirect('index')
    else:
        form = SubcriberForm()


class ProfilePage(generic.DetailView):
    model = User
    slug_field = 'username'
    template_name = 'takdhum/user_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = Basic_info.objects.first()
        context['categories'] = CourseCategory.objects.all()
        return context


@login_required
@transaction.atomic
def update_profile(request):
    categories = CourseCategory.objects.all()
    basic_info = Basic_info.objects.first()
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            user = request.user
            #messages.success(request, 'Your profile was successfully updated!')
            return redirect('user_profile', request.user)
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    return render(request, 'takdhum/profile_settings.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'info': basic_info,
        'categories': categories,
        'title': 'Update Profile',
    })


def drawing_course(request, category, level):
    categories = CourseCategory.objects.all()
    basic_info = Basic_info.objects.first()

    levels = CourseLevel.objects.all()
    course_level = get_object_or_404(CourseLevel, url=level)
    requested_category = get_object_or_404(CourseCategory, category_url=category)
    requested_category_course = Course.objects.filter(course_category=requested_category.id).filter(course_level=course_level.id).order_by('course_title')

    # courses = get_object_or_404(CourseCategory, category_url=category)

    context = {
        'categories': categories,
        # 'course_level': course_level,
        'level': levels,
        'info': basic_info,
        'tag': category,
        'heading': requested_category.category_name + ' ' + course_level.name,
        'courses': requested_category_course,
        'title': requested_category.category_name,
    }
    return render(request, 'takdhum/course_category.html', context)


def courseCategory(request, category=None):
    """Takdhum All course category, resent course, popular course etc."""
    # Need for all view
    categories = CourseCategory.objects.all()
    basic_info = Basic_info.objects.first()

    level = CourseLevel.objects.all()

    requested_category = get_object_or_404(CourseCategory, category_url=category)
    requested_category_course = Course.objects.filter(course_category=requested_category.id).order_by('course_title')

    # courses = get_object_or_404(CourseCategory, category_url=category)

    context = {
        'categories': categories,
        'level': level,
        'info': basic_info,
        'tag': category,
        'courses': requested_category_course,
        'title': requested_category.category_name,
    }
    if category == 'drawing':
        return render(request, 'takdhum/course_category.html', context)
    else:
        return render(request, 'takdhum/all_course.html', context)


def course(request, category, course):
    """All takdhum single course display here"""
    # Need for all view
    basic_info = Basic_info.objects.first()
    categories = CourseCategory.objects.all()

    course_category = get_object_or_404(CourseCategory, category_url=category)

    single_course = get_object_or_404(Course, course_url=course)
    allCourses = Course.objects.exclude(course_url=single_course.id).filter(course_category=course_category.id).order_by('course_title')
    course_videos = SingleVideo.objects.filter(course_name=single_course.id)

    all_videos = SingleVideo.objects.all()

    context = {
        'categories': categories,
        'course_name': single_course,
        'course_videos': course_videos,
        'all_Courses': allCourses,
        'all_videos': all_videos,
        'request_category': category,
        'info': basic_info,
        'title': course,
    }
    return render(request, 'takdhum/single_course.html', context)


def all_course(request):
    """Show takddhum all courses"""
    # Need for all view
    basic_info = Basic_info.objects.first()
    categories = CourseCategory.objects.all()

    level = CourseLevel.objects.all()
    courses = Course.objects.all().order_by('course_title')

    context = {
        'categories': categories,
        'level': level,
        'courses': courses,
        'info': basic_info,
        'tag': 'All',
        'title': 'All courses',
    }
    return render(request, 'takdhum/all_course.html', context)


def popular_course(request):
    """Show takdhum popular courses"""
    # Need for all view
    basic_info = Basic_info.objects.first()
    categories = CourseCategory.objects.all()

    level = CourseLevel.objects.all()
    courses = Course.objects.all().order_by('course_title')

    context = {
        'categories': categories,
        'level': level,
        'courses': courses,
        'info': basic_info,
        'tag': 'Popular',
        'title': 'Takdhum Popular Courses'
    }
    return render(request, 'takdhum/all_course.html', context)


def recent_course(request):
    """Show takdhum recent courses"""
    # Need for all view
    basic_info = Basic_info.objects.first()
    categories = CourseCategory.objects.all()

    level = CourseLevel.objects.all()
    courses = Course.objects.all().order_by('course_title')[::-1]

    context = {
        'categories': categories,
        'level': level,
        'courses': courses,
        'info': basic_info,
        'tag': 'Recent',
        'title': 'Takdhum Recent Courses'
    }
    return render(request, 'takdhum/all_course.html', context)


def event(request, event_id):
    """Takdhum single event page"""
    # Need for all view
    categories = CourseCategory.objects.all()
    basic_info = Basic_info.objects.first()

    requested_event = get_object_or_404(Event, id=event_id)

    context = {
        'categories': categories,
        'info': basic_info,
        'single_event': requested_event,
        'title': requested_event.title,
    }
    return render(request, 'takdhum/single_event.html', context)


def about_us(request):
    """Takdhum about us page"""
    # Need for all view
    basic_info = Basic_info.objects.first()
    categories = CourseCategory.objects.all()

    about = AboutUs.objects.first()
    context = {
        'info': basic_info,
        'categories': categories,
        'about': about,

    }
    return render(request, 'takdhum/about_us.html', context)


def contact(request):
    """Takdhum contact page"""
    # Need for all view
    basic_info = Basic_info.objects.first()
    categories = CourseCategory.objects.all()

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'You message send successfully.')
            redirect('contact_page')
        else:
            messages.error(request, 'Please try again!.')
            redirect('contact_page')
    else:
        form = ContactForm()
    context = {
        'info': basic_info,
        'categories': categories,
        'form': form,
        'title': 'Contact',
    }
    return render(request, 'takdhum/contact.html', context)


def user_message(request):
    basic_info = Basic_info.objects.first()
    categories = CourseCategory.objects.all()

    context = {
        'info': basic_info,
        'categories': categories,
    }
    if request.method == 'POST':
        form = UserMessageForm(request.POST or None)
        if form.is_valid():
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            message = request.POST.get('contact-message', '')
            user_message_obj = UserMessage(first_name=first_name, last_name=last_name, email=email, message=message)
            user_message_obj.save()
            messages.add_message(request, messages.SUCCESS, 'Message sent successfully!')
    else:
        messages.add_message(request, messages.ERROR, 'Something went wrong!')

    return render(request, 'takdhum/contact.html', context)


def faq(request):
    """Takdhum FAQ page"""
    # Need for all view
    basic_info = Basic_info.objects.first()
    categories = CourseCategory.objects.all()

    question_ans = FAQ.objects.all()
    context = {
        'info': basic_info,
        'categories': categories,
        'faq': question_ans,
    }
    return render(request, 'takdhum/faq.html', context)


def get_user_profile(request, name=None):
    if request.user.is_authenticated:
        basic_info = Basic_info.objects.first()
        categories = CourseCategory.objects.all()
        # login_user = get_object_or_404(User, username=name)
        # print(login_user)
        context = {
            'info': basic_info,
            'categories': categories,
            'title': 'Profile',
            # 'login_user': login_user,
        }
        return render(request, 'takdhum/user_profile.html', context)
    else:
        return redirect('login')


def get_login(request):
    if request.user.is_authenticated:
        return redirect('index')
    else:
        basic_info = Basic_info.objects.first()
        categories = CourseCategory.objects.all()
        form = SignupForm(request.POST or None)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            return redirect('login')

        context = {
            'categories': categories,
            'info': basic_info,
            'form': form,
            'title': 'Login'
        }
        if request.method == 'POST':
            user = request.POST.get('username')
            password = request.POST.get('password')
            auth = authenticate(request, username=user, password=password)
            if auth is not None:
                login(request, auth)
                # messages.add_message(request, messages.ERROR, 'Login Successful')
                # return redirect('profile')
                return redirect('profile')
            else:
                messages.add_message(request, messages.ERROR, 'Username or Password Wrong!')
    return render(request, 'takdhum/login-reg.html', context)


def get_logout(request):
    logout(request)
    return redirect('index')


def signup(request):
    basic_info = Basic_info.objects.first()
    categories = CourseCategory.objects.all()
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your Takdhum account.'
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            context = {
                'info': basic_info,
                'categories': categories,
                'form': form,
                'title': 'Sign up'
            }
            return render(request, 'takdhum/activation_message.html', context)
            # return HttpResponse('Please confirm your email address to complete the registration')
    else:
        form = SignupForm()
    context = {
        'info': basic_info,
        'categories': categories,
        'form': form,
        'title': 'Sign up'
    }

    return render(request, 'takdhum/register.html', context)


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('profile')
        # return HttpResponse('Thank you for your email confirmation. Now you can login your account.')
    else:
        # return HttpResponse('Your account will be activate within 6 hours.')
        return HttpResponse('Activation link is invalid!')


def get_sign_up(request):
    if request.user.is_authenticated:
        return redirect('login')
    else:
        form = SignupForm(request.POST or None)
        if form.is_valid():
            instance=form.save(commit=False)
            instance.save()
            messages.add_message(request, messages.INFO, 'Registration Successfully Completed!')
            return redirect('login')
        basic_info = Basic_info.objects.first()
        categories = CourseCategory.objects.all()
        context = {
            'info': basic_info,
            'categories': categories,
            'form': form,
            'title': 'Sign up'
        }
        return render(request, 'takdhum/register.html', context)


class EventListView(generic.ListView):
    template_name = 'takdhum/event_list.html'
    context_object_name = 'events'

    def get_queryset(self):
        return Event.objects.all().order_by('-upload_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['info'] = Basic_info.objects.first()
        context['categories'] = CourseCategory.objects.all()
        return context


def search(request):
    course_list = Course.objects.all()
    course_filter = CourseFilter(request.GET, queryset=course_list)
    basic_info = Basic_info.objects.first()
    categories = CourseCategory.objects.all()
    return render(request, 'takdhum/search/course_list.html', {'filter': course_filter,
                                                               'info': basic_info,
                                                               'categories': categories})
