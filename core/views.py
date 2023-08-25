from django.shortcuts import render,redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Profile,Post,LikePost,FollowersCount
from itertools import chain 
import requests
import os


# Create your views here.

#DECLARING A GLOBAL VARIABLE


def weather_data(location) :
    
    BASE_URL = open("api.txt", 'r').read()
   

    print(BASE_URL)
    city = str(location)
    url = BASE_URL + city
    
    

    response =requests.get(url).json()


    def kelvin_celsius (kelvin):
        celsious = kelvin-273.15
        return celsious


    temp_kelvin =response['main']['temp']
    temp_celsius = round(kelvin_celsius(temp_kelvin),2)
    temp_min = round(kelvin_celsius(response['main']['temp_min']),2)
    temp_max = round(kelvin_celsius(response['main']['temp_max']),2)
    description= response['weather'][0]['description']

    context ={
        'city' : city,
        'temp_celsius' : temp_celsius,
        'description': description,
        'temp_min' : temp_min,
       'temp_max' : temp_max

    }
    return context



@login_required(login_url='signin')
def index(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    user_location =getattr(user_profile,'location')

    user_following_list =[]
    feed =[]

    user_following=FollowersCount.objects.filter(follower=request.user.username)

    for users in user_following :
        user_following_list.append(users.user)
    
    for usernames in user_following_list:
        feed_lists = Post.objects.filter(user=usernames)
        feed.append(feed_lists)

    feed_list =list(chain(*feed))
    weather_dict = weather_data(user_location)
    

    posts =Post.objects.all()
    return render(request, 'index.html',{'user_profile' : user_profile , 'posts':feed_list ,'weather' :weather_dict})

@login_required(login_url='signin')
def upload(request):

    if request.method =="POST" :
        user = request.user.username
        image = request.FILES.get("image_upload")
        caption= request.POST['caption']


        new_post=Post.objects.create(user=user,image=image,caption=caption)
        new_post.save()

        return redirect("/")    
    
    else:
        return redirect("/")
    
    return HttpResponse('<h1>Upload View</h1>')



@login_required(login_url='signin')
def like_post(request):
    username=request.user.username
    post_id = request.GET.get('post_id')
    
    post = Post.objects.get(id = post_id)
    
    like_filter = LikePost.objects.filter(post_id = post_id , username=username).first()

    if like_filter ==None :
        new_like = LikePost.objects.create(post_id=post_id , username=username)
        new_like.save()
        post.no_of_likes = post.no_of_likes + 1 
        post.save()
        return redirect('/')

    else:

        like_filter.delete()
        post.no_of_likes=post.no_of_likes - 1 
        post.save()
        return redirect('/')
        
@login_required(login_url='signin')
def profile(request,pk) :

    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    user_post_length = len(user_posts)

    follower= request.user.username
    user = pk

    if FollowersCount.objects.filter(follower=follower,user=user).first():
        button_text='Unfollow'
    else:
        button_text='Follow'

    user_followers =len(FollowersCount.objects.filter(user=pk))
    user_following = len(FollowersCount.objects.filter(follower=pk))


    context = {
        'user_object': user_object,
        'user_profile' : user_profile,
        'user_posts' : user_posts,
        'user_post_length' : user_post_length ,
        'button_text' : button_text,
        'user_followers': user_followers,
        'user_following' :user_following,

    }
    return render(request,'profile.html',context )

@login_required(login_url='signin')
def  follow(request):
    if request.method == 'POST' :

        follower = request.POST['follower']
        user = request.POST['user']

        if FollowersCount.objects.filter(follower=follower,user=user).first():
            delete_follower = FollowersCount.objects.get(follower=follower,user=user)
            delete_follower.delete()
            return redirect('/profile/' + user)
        else:
            new_follower=FollowersCount.objects.create(follower=follower,user=user)
            new_follower.save()
            return redirect('/profile/' + user)
    else:
        return redirect('/')
    



@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method =='POST':


            if request.FILES.get('image')==None:
                image=user_profile.profileimg
                bio = request.POST['bio']
                location = request.POST['location']


                user_profile.profileimg = image
                user_profile.bio =bio
                user_profile.location = location
                user_profile.save()

            if request.FILES.get('image') != None:
                image = request.FILES.get('image')
                bio = request.POST['bio']
                location = request.POST['location']


                user_profile.profileimg = image
                user_profile.bio =bio
                user_profile.location = location
                user_profile.save()
            


            return redirect('settings')
    return render(request,'setting.html', {'user_profile': user_profile})


def signup(request):
    
    if request.method == 'POST' :
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request,'Email Taken' )
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request,'Username Taken')
                return redirect('signup')
            else:
                user=User.objects.create_user(username=username,email=email,password=password)
                user.save()

                #Log in user and redirect to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request,user_login)



                #create a profile object for the new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model,id_user=user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request,'Password Not Matching')
            return redirect('signup')
    

    else:
        return render(request ,'signup.html')
    

def signin (request):

    if request.method =='POST' :
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username,password=password)

        if user is not None:
            auth.login(request,user)
            return redirect('/')
        else:
            messages.info(request,'Credentials Invalid')
            return redirect('signin')
        
    else :
        return render(request,'signin.html')
    
@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')

@login_required(login_url='signin')
def city(request):
    city_name = None  # Initialize the variable outside the if block

    if request.method == "POST":
        city_name = request.POST.get('city')  # Use get() to avoid KeyError

    if city_name:  # Only redirect if city_name is not None
        redirect_url = "https://openweathermap.org/find?q={}".format(city_name)
        return redirect(redirect_url)

    return render(request, 'index.html')  # Replace with your template name

    


