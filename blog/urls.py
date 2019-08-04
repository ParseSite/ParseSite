from django.urls import path
from .views import (
    PostListView,
    PostDetailView,
    PostCreateView,
    PostUpdateView,
    PostDeleteView,
    UserPostListView,
)
from . import views

urlpatterns = [
    path('', PostListView.as_view(), name='blog-home'),
    # path('users/<str:username>', UserPostListView.as_view(), name='user-posts'),
    path('post/<pk>/', PostDetailView.as_view(), name='post-detail'),
    path('new_post/', PostCreateView.as_view(), name='post-create'),
    path('new_post/create_location/', views.create_location, name='create_location'),
    path('post/<int:pk>/update/', views.post_update, name='post-update'),
    path('post/<int:pk>/update/update_location/', views.update_location, name='update_location'),
    path('post/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    path('about/', views.about, name='blog-about'),
    path('search/', views.search, name='search'),
    path('blog/search/', views.blog_search, name='blog_search'),
    path('post/<int:pk>/save_post/', views.save_post, name='save_post'),
    path('post/<int:pk>/un_save_post/', views.un_save_post, name='un_save_post'),
    path('post/<int:pk>/update_save/', views.update_save, name='update_save'),
    path('post/<int:pk>/like_comment/', views.like_comment, name='like_comment'),
    path('post/<int:pk>/dislike_comment/', views.dislike_comment, name='dislike_comment'),
    path('post/<int:pk>/liked_or_disliked_comment/', views.liked_or_disliked_comment, name='liked_or_disliked_comment'),
    path('post/<int:pk>/delete_comment/<int:comment_pk>', views.delete_comment, name='delete_comment'),
    path('users/Notifications/', views.my_notif, name='my-notif'),
    path('post/<int:pk>/rate_post/', views.rate_post, name='rate_post'),
    path('post/<int:pk>/update_rating/', views.update_rating, name='update_rating'),
    path('blog/filter/', views.filter_search, name='filter_search'),
    path('filter_info', views.filter_info, name='filter_info'),
    path('category/<str:category>/', views.go_to_category, name='go_to_category'),
    path('location/<int:location_id>/', views.go_to_location, name='go_to_location'),
    path('map/location/<int:location_id>', views.show_in_map, name='show_in_map'),
]
