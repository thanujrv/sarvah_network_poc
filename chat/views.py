from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import CommentForm, PostForm
from .models import Post
from .utils import s3

@login_required
def home(request):
	""" The home news feed page """

	# Get users whose posts to display on news feed and add users account
	_users = list(request.user.followers.all())
	_users.append(request.user)

	# Get posts from users accounts whose posts to display and order by latest
	posts = Post.objects.filter(user__in=_users).order_by('-posted_date')
	comment_form = CommentForm()
	return render(request, 'chat/home.html', {'posts': posts, 'comment_form': comment_form})


@login_required
def add_post(request):
	""" create a new posts to user """
	if request.method == 'POST':
		form = PostForm(request.POST, request.FILES)
		# validate form based on form definition
		if form.is_valid():
			# Check if any text field is empty (contains only whitespace)
			if any(not str(field).strip() for field in form.cleaned_data.values()):
				form.add_error(None, "All fields must be filled out")
			else:
				post = form.save(commit=False)
				post.user = request.user

				print(request.FILES)

				if 'picture' in request.FILES:
					success, result = s3.upload_to_s3(request.FILES['picture'],folder="sqn-data")

					if success:
						print(result)
					else:
						form.add_error(None, f"Failed to upload image: {result}")
						return render(request, 'chat/add_post.html', {'form': form})

				post.save()
				return redirect('chat:home')
	else:
		form = PostForm()
	return render(request, 'chat/add_post.html', {'form': form})


@login_required
@require_POST
def add_comment(request, post_id):
	""" Add a comment to a post """

	form = CommentForm(request.POST)
	if form.is_valid():
		# pass the post id to the comment save() method which was overriden
		# in the CommentForm implementation
		comment = form.save(Post.objects.get(id=post_id), request.user)
	return redirect(reverse('chat:home'))
