from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from itertools import chain
from django.db.models.functions import Lower
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView
)
from .models import Post, PostView, SavePost, Comment, LikeComment, DislikeComment, sendNotif, Score, Category, Location
from .forms import CommentForm, PostForm


from rest_framework.response import Response
from rest_framework.decorators import api_view


def send_comment_notif(request, post, comment):
    if Comment.objects.filter(id=comment.id).first():
        if request.user != post.author:
            post_id = post.id
            text = comment.content
            sn = sendNotif(post=Post.objects.get(id=post_id),
                           user=User.objects.get(id=request.user.id),
                           Text=text, type="comment", comment_id=comment.id)
            sn.save()
    return redirect(request.META.get('HTTP_REFERER'))


def delete_comment_notif(user, post, comment_id):
    if user != post.author:
        post_id = post.id
        user_id = user.id
        notif_type = "comment"
        comment = sendNotif.objects.filter(post_id=post_id, user_id=user_id, type=notif_type, comment_id=comment_id).first()
        if comment:
            comment.delete()


def send_rate_notif(user, post, score):
    if Score.objects.filter(id=score.id).first():
        if user != post.author:
            post_id = post.id
            user_id = user.id
            score_id = score.id
            text = str(score.score)
            sn = sendNotif(post=Post.objects.get(id=post_id),
                           user=User.objects.get(id=user_id),
                           dateposted=0, Text=text, type="rate", score_id=score_id)
            sn.save()
    return


def delete_rate_notif(user, post, score_id):
    if user != post.author:
        post_id = post.id
        user_id = user.id
        notif_type = "rate"
        rating = sendNotif.objects.filter(post_id=post_id, user_id=user_id, type=notif_type, score_id=score_id).first()
        if rating:
            rating.delete()


def send_like_comment_notif(user, post, like_comment):
    if like_comment is not None:
        if user != like_comment.comment.user:
            post_id = post.id
            user_id = user.id
            like_comment_id = like_comment.id
            comment_id = like_comment.comment.id
            text = like_comment.comment.content
            sn = sendNotif(post_id=post_id, user_id=user_id,
                           type="like_comment", Text=text,
                           like_comment_id=like_comment_id,
                           comment_id=comment_id, comment_author_id=like_comment.comment.user.id)
            sn.save()
    return


def delete_like_comment_notif(user, post, like_comment_id):
    print("like_comment_id:", like_comment_id)
    post_id = post.id
    user_id = user.id
    notif_type = "like_comment"
    rating = sendNotif.objects.filter(post_id=post_id, user_id=user_id,
                                      type=notif_type, like_comment_id=like_comment_id).first()
    if rating:
        rating.delete()


def send_dislike_comment_notif(user, post, dislike_comment):
    if user != dislike_comment.comment.user:
        post_id = post.id
        user_id = user.id
        dislike_comment_id = dislike_comment.id
        comment_id = dislike_comment.comment.id
        text = dislike_comment.comment.content
        sn = sendNotif(post_id=post_id, user_id=user_id,
                       type="dislike_comment", dislike_comment_id=dislike_comment_id,
                       comment_id=comment_id, Text=text, comment_author_id=dislike_comment.comment.user.id)
        sn.save()
    return


def delete_dislike_comment_notif(user, post, dislike_comment_id):
    print("dislike_comment_id:", dislike_comment_id)
    post_id = post.id
    user_id = user.id
    notif_type = "dislike_comment"
    rating = sendNotif.objects.filter(post_id=post_id, user_id=user_id,
                                      type=notif_type, dislike_comment_id=dislike_comment_id).first()
    if rating:
        rating.delete()


def my_notif(request):
    notifs = sendNotif.objects.all().order_by('-dateposted')
    notification = []
    for n in notifs:
        flag = False
        if (n.type == "comment" or n.type == "rate") and n.post.author == request.user:
            flag = True
            notification.append(n)
        elif (n.type == "like_comment" or n.type == "dislike_comment") and n.comment_author_id == request.user.id:
            flag = True
            notification.append(n)
        if n.seen is False:
            n.seen = flag
            n.save()

    context = {
        'notifications': notification
    }
    return render(request, 'blog/notif.html', context)


@api_view(['GET', 'POST', ])
def filter_info(request):
    categories = Category \
        .objects \
        .values('title') \
        .annotate(Count('title')) \
        .order_by(Lower('title'))
    locations = Location \
        .objects \
        .values('place') \
        .annotate(Count('place')) \
        .order_by(Lower('place'))

    data = {
        "categories": categories,
        "locations": locations,
    }
    return Response(data)


@api_view(['GET', 'POST', ])
def liked_or_disliked_comment(request, pk):
    comment_pk = request.GET.get('comment_pk', -1)
    userId = request.user.id

    liked = False
    if LikeComment.objects.filter(comment_id=comment_pk).filter(user_id=userId).first():
        liked = True
    disliked = False
    if DislikeComment.objects.filter(comment_id=comment_pk).filter(user_id=userId).first():
        disliked = True

    data = {
        "id": comment_pk,
        "liked": liked,
        "disliked": disliked
    }
    return Response(data)


@api_view(['GET', 'POST', ])
def like_comment(request, pk):
    comment_pk = request.GET.get('comment_pk', -1)
    userId = request.user.id
    flag = True
    if LikeComment.objects.filter(comment_id=comment_pk).filter(user_id=userId).first():
        flag = False
    if flag:
        flag2 = False
        if DislikeComment.objects.filter(comment_id=comment_pk).filter(user_id=userId).first():
            flag2 = True
        if flag2:
            disliked_comment = DislikeComment.objects.filter(comment_id=comment_pk).filter(user_id=userId).first()
            dislike_comment_id = disliked_comment.id
            disliked_comment.delete()
            delete_dislike_comment_notif(request.user, Post.objects.get(id=pk), dislike_comment_id)

        ap = LikeComment(comment=Comment.objects.get(id=comment_pk), user=User.objects.get(id=userId))
        ap.save()
        send_like_comment_notif(request.user, Post.objects.get(id=pk), ap)
    else:
        liked_comment = LikeComment.objects.filter(comment_id=comment_pk).filter(user_id=userId).first()
        like_comment_id = liked_comment.id
        liked_comment.delete()
        # print("%%%%%%%%%%%%%")
        delete_like_comment_notif(request.user, Post.objects.get(id=pk), like_comment_id)

    likes_count = LikeComment \
        .objects \
        .filter(comment_id=comment_pk) \
        .count()

    dislikes_count = DislikeComment \
        .objects \
        .filter(comment_id=comment_pk) \
        .count()

    data = {
        "id": comment_pk,
        "like": flag,
        "likes_count": likes_count,
        "dislikes_count": dislikes_count
    }
    return Response(data)


@api_view(['GET', 'POST', ])
def dislike_comment(request, pk):
    comment_pk = request.GET.get('comment_pk', -1)
    userId = request.user.id
    flag = True
    if DislikeComment.objects.filter(comment_id=comment_pk).filter(user_id=userId).first():
        flag = False
    if flag:
        flag2 = False
        if LikeComment.objects.filter(comment_id=comment_pk).filter(user_id=userId).first():
            flag2 = True
        if flag2:
            liked_comment = LikeComment.objects.filter(comment_id=comment_pk).filter(user_id=userId).first()
            like_comment_id = liked_comment.id
            liked_comment.delete()
            delete_like_comment_notif(request.user, Post.objects.get(id=pk), like_comment_id)

        ap = DislikeComment(comment=Comment.objects.get(id=comment_pk), user=User.objects.get(id=userId))
        ap.save()
        send_dislike_comment_notif(request.user, Post.objects.get(id=pk), ap)
    else:
        disliked_comment = DislikeComment.objects.filter(comment_id=comment_pk).filter(user_id=userId).first()
        dislike_comment_id = disliked_comment.id
        disliked_comment.delete()
        delete_dislike_comment_notif(request.user, Post.objects.get(id=pk), dislike_comment_id)

    dislikes_count = DislikeComment \
        .objects \
        .filter(comment_id=comment_pk) \
        .count()

    likes_count = LikeComment \
        .objects \
        .filter(comment_id=comment_pk) \
        .count()

    data = {
        "id": comment_pk,
        "dislike": flag,
        "dislikes_count": dislikes_count,
        "likes_count": likes_count
    }
    return Response(data)


@api_view(['GET', 'POST', ])
def rate_post(request, pk):
    rate_value = request.GET.get('rate_value', 0)
    userId = request.user.id
    flag = False
    if Score.objects.filter(post_id=pk, user_id=userId).first():
        flag = True
    if flag:
        score = Score.objects.filter(post_id=pk, user_id=userId).first()
        score.delete()
        delete_rate_notif(request.user, Post.objects.get(id=pk), score.id)

    ap = Score(user=User.objects.get(id=userId), post=Post.objects.get(id=pk), score=rate_value)
    ap.save()
    send_rate_notif(request.user, Post.objects.get(id=pk), ap)

    data = {
        "updated": flag
    }
    return Response(data)


@api_view(['GET', 'POST', ])
def update_rating(request, pk):
    post = Post.objects.get(id=pk)
    rate_value = post.get_score
    rate_count = post.get_scores_num

    data = {
        "rate_value": rate_value,
        "rate_count": rate_count
    }
    return Response(data)


@api_view(['GET', 'POST', ])
def update_save(request, pk):
    userId = request.user.id
    flag = True
    post = SavePost.objects.filter(post_id=pk, user_id=userId).first()
    if post:
        post.delete()
        flag = False
    else:
        ap = SavePost(post=Post.objects.get(id=pk), user=User.objects.get(id=userId))
        ap.save()
        flag = True

    data = {
        "save": flag,
    }
    return Response(data)


@api_view(['GET', 'POST', ])
def create_location(request):
    place_name = request.GET.get("place_name")
    place_id = request.GET.get("place_id")
    address = request.GET.get("address")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    added = False
    id = -1
    location = Location.objects.filter(place=place_name).first()
    if location:
        id = location.id
    else:
        added = True
        loc = Location.objects.create(place=place_name, lat=lat, lng=lng, place_id=place_id, address=address)
        loc.save()
        id = loc.id

    data = {
        "added": added,
        "id": id
    }
    return Response(data)


@api_view(['GET', 'POST', ])
def update_location(request, pk):
    place_name = request.GET.get("place_name")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    added = False
    id = -1
    location = Location.objects.filter(place=place_name).first()
    if location:
        id = location.id
    else:
        added = True
        loc = Location.objects.create(place=place_name, lat=lat, lng=lng)
        loc.save()
        id = loc.id

    data = {
        "added": added,
        "id": id
    }
    return Response(data)


def home(request):
    context = {
        'posts': Post.objects.all()
    }
    return render(request, 'blog/home.html', context)


def get_category_count():
    queryset = Post \
        .objects \
        .values('categories__title') \
        .annotate(Count('categories__title')) \
        .order_by('categories__title__count') \
        .reverse()
    return queryset


def delete_comment(request, pk, comment_pk):
    to_delete_comment = Comment.objects.filter(pk=comment_pk).first()
    to_delete_comment.delete()
    delete_comment_notif(request.user, Post.objects.get(id=pk), comment_pk)
    return redirect(request.META.get('HTTP_REFERER'))


def save_post(request, pk):
    userId = request.user.id
    flag = True
    for p in SavePost.objects.filter(post_id=pk):
        if p.user_id == userId:
            flag = False
    if flag:
        ap = SavePost(post=Post.objects.get(id=pk), user=User.objects.get(id=userId))
        ap.save()
    return redirect(request.META.get('HTTP_REFERER'))


def un_save_post(request, pk):
    userId = request.user.id
    saved_post = SavePost.objects.filter(post_id=pk).filter(user_id=userId).first()
    saved_post.delete()
    return redirect(reverse('post-detail', kwargs={'pk': pk}))


def post_is_saved(pk, user):
    queryset = SavePost \
        .objects \
        .filter(user=user) \
        .filter(post_id=pk)
    flag = False
    if queryset:
        flag = True
    return flag


def do_like_comment(userId, comments):
    return_value = [False] * len(comments)
    i = 0
    for c in comments:
        if LikeComment.objects.filter(comment_id=c.id).filter(user_id=userId).first():
            return_value[i] = True
        i += 1
    print('likes', return_value[::-1])
    return return_value[::-1]


def do_dislike_comment(userId, comments):
    return_value = [False] * len(comments)
    i = 0
    for c in comments:
        if DislikeComment.objects.filter(comment_id=c.id).filter(user_id=userId).first():
            return_value[i] = True
        i += 1
    print('dislikes', return_value[::-1])
    return return_value[::-1]


class PostListView(ListView):
    model = Post
    template_name = 'blog/home.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 6

    def get_context_data(self, **kwargs):
        category_count = get_category_count()[:3]
        most_recent = Post.objects.order_by('-date_posted')[:3]
        context = super().get_context_data(**kwargs)
        context['most_recent'] = most_recent
        context['category_count'] = category_count
        return context


class UserPostListView(ListView):
    model = Post
    template_name = 'blog/user_posts.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post.html'
    context_object_name = 'post'
    form = CommentForm()

    def get_object(self):
        obj = super().get_object()
        if self.request.user.is_authenticated:
            PostView.objects.get_or_create(
                user=self.request.user,
                post=obj
            )
        return obj

    def get_context_data(self, **kwargs):
        given_rating = 0
        is_saved = False
        do_like_comments = []
        do_like_comments2 = []
        do_dislike_comments = []
        if self.request.user.is_authenticated:
            post = self.get_object()
            given_rating = Score.objects.filter(post=post, user=self.request.user).first()
            is_saved = post_is_saved(post.pk, self.request.user)
            do_like_comments = do_like_comment(self.request.user.id, post.get_comments)
            do_like_comments2 = do_like_comment(self.request.user.id, post.get_comments)
            do_dislike_comments = do_dislike_comment(self.request.user.id, post.get_comments)
        context = super().get_context_data(**kwargs)
        context['given_rating'] = given_rating
        context['is_saved'] = is_saved
        context['do_like_comments'] = do_like_comments
        context['do_dislike_comments'] = do_dislike_comments
        context['do_like_comments2'] = do_like_comments2
        context['form'] = self.form
        return context

    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST)
        if form.is_valid():
            post = self.get_object()
            form.instance.user = request.user
            form.instance.post = post
            comment = form.save()
            send_comment_notif(request, post, comment)
            return redirect(reverse("post-detail", kwargs={
                'pk': post.pk
            }))


class PostCreateView(CreateView):
    model = Post
    template_name = 'blog/post_create.html'
    form_class = PostForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create'
        return context

    # def form_valid(self, form):
    #     form.instance.author = self.request.user
    #     form.save()
    #     return redirect(reverse("post-detail", kwargs={
    #         'pk': form.instance.pk
    #     }))

    def form_valid(self, form):
        form_dic = form.data.dict()

        val = form_dic.get('title')

        while val.find('$') >= 0:
            val = val[val.find('$') + 1:]

        title = form_dic.get('title')
        title = title[0:len(title) - len(val) - 1]

        val = int(val)

        post = Post(author=self.request.user, title=title, image=form.files.dict().get('image'),
                    content=form_dic.get('content'), location=Location.objects.filter(id=val).first())
        post.save()
        post.categories.set(form_dic.get('categories'))

        return redirect(reverse("post-detail", kwargs={
            'pk': post.pk
        }))


def post_create(request):
    title = 'Create'
    form = PostForm(request.POST or None, request.FILES or None)
    author = request.user
    if request.method == "POST":
        if form.is_valid():
            form.instance.author = author
            form.save()
            return redirect(reverse("post-detail", kwargs={
                'id': form.instance.id
            }))
    context = {
        'title': title,
        'form': form
    }
    return render(request, "blog/post_create.html", context)


class PostUpdateView(UpdateView):
    model = Post
    template_name = 'blog/post_create.html'
    form_class = PostForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Update'
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.save()
        return redirect(reverse("post-detail", kwargs={
            'pk': form.instance.pk
        }))


def post_update(request, pk):
    title = 'Update'
    post = get_object_or_404(Post, id=pk)
    form = PostForm(
        request.POST or None,
        request.FILES or None,
        instance=post)
    author = request.user
    if request.method == "POST":
        if form.is_valid():
            form_dic = form.data.dict()
            val = form_dic.get('title')

            while val.find('$') >= 0:
                val = val[val.find('$') + 1:]

            title = form_dic.get('title')
            title = title[0:len(title) - len(val) - 1]

            val = int(val)

            post = Post.objects.filter(id=pk).first()
            post.title = title
            if form.files:
                post.image = form.files.dict().get('image')
            post.content = form_dic.get('content')
            post.location = Location.objects.filter(id=val).first()
            post.categories.set(form_dic.get('categories'))

            # post = Post(author=self.request.user, title=title, image=form.files.dict().get('image'),
            #             content=form_dic.get('content'), location=Location.objects.filter(id=val).first())
            post.save()

            return redirect(reverse("post-detail", kwargs={
                'pk': post.pk
            }))
    context = {
        'title': title,
        'form': form,
        'location_id': post.location.id,
        'location_place': post.location.place,
        'location_lat': post.location.lat,
        'location_lng': post.location.lng,
    }
    return render(request, "blog/post_create.html", context)


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


def search(request):
    if request.method == 'GET':
        query = request.GET.get('q')
        query = query.strip()
        submitbutton = request.GET.get('submit')

        if query is not None:
            lookups = Q(username__icontains=query)

            results = User.objects.filter(lookups).distinct()

            if results:
                return redirect(reverse("user_page", kwargs={
                    'username': results[0].username
                }))

            context = {'results': results,
                       'submitbutton': submitbutton}
            return render(request, 'blog/search.html', context)

        else:
            return render(request, 'blog/search.html')

    else:
        return render(request, 'blog/search.html')


def blog_search(request):
    queryset = Post.objects.all().order_by('-date_posted')
    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        ).distinct()
    else:
        return redirect(request.META.get('HTTP_REFERER'))

    flag = False
    if request.GET.get('blog_search_submit') == 'blog_search':
        flag = True
    context = {
        'posts': queryset,
        'blog_search': flag
    }
    return render(request, 'blog/blog_search_results.html', context)


def about(request):
    return render(request, 'blog/about.html', {'title': 'About'})


def filter_search(request):
    queryset = Post.objects.all().order_by('-dateposted')
    query_loc = request.GET.get('l')
    # query_loc = "".join(query_loc.split())
    query_cat = request.GET.get('c')
    # query_cat = "".join(query_cat.split())

    if not(query_loc or query_cat):
        return redirect(request.META.get('HTTP_REFERER'))

    query_cat = query_cat.split(",")
    query_loc = query_loc.split(",")

    flag_cat = ''
    flag_loc = ''

    if query_cat and query_loc:
        flag_cat = request.GET.get('c')
        flag_loc = request.GET.get('l')
        qs = []
        for cat in query_cat:
            for loc in query_loc:
                the_loc = loc.strip()
                the_cat = cat.strip()
                q1 = queryset.filter(
                    Q(categories__title__contains=the_cat) &
                    Q(location__place__contains=the_loc)
                ).distinct()
                qs = list(chain(q1, qs))

        queryset = list(set(qs))

    elif query_cat:
        flag_cat = request.GET.get('c')
        qs = []
        for cat in query_cat:
            q1 = queryset.filter(
                Q(categories__title__contains=cat)
            ).distinct()
            qs = list(chain(q1, qs))
        queryset = list(set(qs))

    elif query_loc:
        flag_loc = request.GET.get('l')
        qs = []
        for loc in query_loc:
            q1 = queryset.filter(
                Q(location__place__contains=loc)
            ).distinct()
            qs = list(chain(q1, qs))
        queryset = list(set(qs))

    flag = False
    if request.GET.get('filter_search_submit') == 'filter_search':
        flag = True
    context = {
        'posts': queryset,
        'blog_search': False,
        'category': flag_cat,
        'location': flag_loc,
    }
    return render(request, 'blog/blog_search_results.html', context)


def go_to_category(request, category):
    context = {
        'posts': Post.objects.filter(categories__title=category).order_by('-dateposted'),
        'blog_search': False,
        'category': category,
    }
    return render(request, 'blog/blog_search_results.html', context)


def go_to_location(request, location_id):
    location_name = list(Location.objects.filter(id=location_id).values("place"))
    if location_name:
        location_name = location_name[0].get('place')
    context = {
        'posts': Post.objects.filter(location__place=location_name).order_by('-dateposted'),
        'blog_search': False,
        'location': location_name,
    }
    return render(request, 'blog/blog_search_results.html', context)


def show_in_map(request, location_id):
    location = list(Location.objects.filter(id=location_id).values("place_id", "lat", "lng", "id"))
    placeId = ''
    lat = 0
    lng = 0
    id = -1
    if location:
        placeId = location[0].get('place_id')
        lat = location[0].get('lat')
        lng = location[0].get('lng')
        id = location[0].get('id')
    context = {
        'placeId': placeId,
        'lat': lat,
        'lng': lng,
        'id': id,
    }
    return render(request, 'blog/map.html', context)
