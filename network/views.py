from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
import json
from django.http import JsonResponse

from .models import User, Post, Follow, Like 


def remove_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    like = Like.objects.filter(user=user, post=post)
    like.delete()
    return JsonResponse({"message": "Like removed"}) 

def add_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    new_like = Like(user=user, post=post)
    new_like.save() 
    return JsonResponse({"message": "Like added"}) 

def edit(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body) 
        edit_post = Post.objects.get(pk=post_id)
        edit_post.content = data["content"]
        edit_post.save()
        return JsonResponse({"message": "Change successful", "data": data["content"]}) 

def index(request):
    all_posts = Post.objects.all().order_by("id").reverse()

    # Pagination
    paginator = Paginator(all_posts, 3 )
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)
    likes = Like.objects.all().order_by("id").reverse()

    user_likes = []
    try:
        for like in likes:
             if like.user.id == request.user.id:
                 user_likes.append(like.post.id)
    except:
        user_likes = []
                 

    return render(request, "network/index.html", {
        "all_posts": all_posts,
        "posts_of_the_page": posts_of_the_page,
        "user_likes": user_likes
    })



def new_post(request):
    if request.method == "POST":
        content = request.POST["content"]
        user = User.objects.get(pk=request.user.id)
        post = Post(content=content, user=user)
        post.save()
        return HttpResponseRedirect(reverse(index))
     

def profile(request, user_id):
    user = User.objects.get(pk=user_id)
    all_posts = Post.objects.filter(user=user).order_by("id").reverse()

    following = Follow.objects.filter(user=user)
    followers = Follow.objects.filter(user_follower=user)
    
    try:
        check_follow = followers.filter(user=User.objects.get(pk=request.user.id))
        if len(check_follow) != 0:
            is_following = True
        else:
            is_following = False
    except: 
        is_following = False

    # Pagination
    paginator = Paginator(all_posts, 3 )
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    return render(request, "network/profile.html", {
        "all_posts": all_posts,
        "posts_of_the_page": posts_of_the_page,
        "username": user.username,
        "following": following, 
        "followers": followers,
        "is_following": is_following,
        "user_profile": user
    })

def following(request):
    current_user = User.objects.get(pk=request.user.id)
    following_people = Follow.objects.filter(user=current_user)
    all_posts = Post.objects.all().order_by('id').reverse()

    following_posts = []

    for post in all_posts:
        for person in following_people:
            if person.user_follower == post.user:
                following_posts.append(post)

    # Pagination
    paginator = Paginator(following_posts, 3 )
    page_number = request.GET.get('page')
    posts_of_the_page = paginator.get_page(page_number)

    return render(request, "network/following.html", {
        "posts_of_the_page": posts_of_the_page
    })


def follow(request):
    user_follow = request.POST['user_follow']
    current_user = User.objects.get(pk=request.user.id)
    user_follow_data = User.objects.get(username=user_follow)
    f = Follow(user=current_user, user_follower=user_follow_data)
    f.save()
    user_id = user_follow_data.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id}))


def unfollow(request):
    user_follow = request.POST['user_follow']
    current_user = User.objects.get(pk=request.user.id)
    user_follow_data = User.objects.get(username=user_follow)
    f = Follow.objects.get(user=current_user, user_follower=user_follow_data)
    f.delete()
    user_id = user_follow_data.id
    return HttpResponseRedirect(reverse(profile, kwargs={'user_id': user_id})) 


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
