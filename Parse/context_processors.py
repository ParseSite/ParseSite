from rest_framework.utils import json

from blog.models import sendNotif
from users.models import profile as Profile
from django.db.models.functions import Lower
from django.db.models import Count


def add_variable_to_context(request):
    num = 0
    notifs = sendNotif.objects.all()
    try:
        for n in notifs:
            if n.seen is False:
                if n.type == "comment" or n.type == "rate":
                    if n.post.author == request.user:
                        num += 1
                elif n.comment_author_id == request.user.id:
                    num += 1
    except:
        num = 0

    profiles = list(Profile \
        .objects \
        .values('user__username', 'image') \
        .annotate(Count('user__username')) \
        .order_by(Lower('user__username')))

    return {
        'num': num,
        "profiles": json.dumps(profiles),
    }
