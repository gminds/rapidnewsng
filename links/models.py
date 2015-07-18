from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count
from django.core.urlresolvers import reverse
from django.utils.timezone import now


class LinkVoteCountManager(models.Manager):
    def get_query_set(self):
        return super(LinkVoteCountManager, self).get_query_set().annotate(votes=Count('vote')).order_by('-votes')

class Link(models.Model):
    title = models.CharField("Headline", max_length=100, unique=True)
    submitter = models.ForeignKey(User)
    linksource = models.CharField("Linksource", max_length=250)
    submitted_on = models.DateTimeField(auto_now_add=True)
    rank_score = models.FloatField(default=0.0)
    url = models.URLField("URL", max_length=250, blank=True)
    description = models.TextField(blank=True)
#    with_votes = LinkVoteCountManager()
    votes = models.IntegerField(default=1)
    objects = models.Manager() #default manager

    def __unicode__(self):
        return self.title

    def set_rank(self):
        # Based on HN ranking algo at http://amix.dk/blog/post/19574
        SECS_IN_HOUR = float(60*60)
        GRAVITY = 1.2

        delta = now() - self.submitted_on
        item_hour_age = delta.total_seconds() // SECS_IN_HOUR
        votes = self.votes - 1
        self.rank_score = votes / pow((item_hour_age+2), GRAVITY)
        self.save()

'''
    def votes(self):
        num_submissions = Submission.objects.filter(uploaded_by=self).count()
        return num_submissions
'''
    

class Vote(models.Model):
    voter = models.ForeignKey(User)
    link = models.ForeignKey(Link)
#    with_votes = Link.objects.count()
#    with_votes = Link.objects.filter(with_votes__gt=0).annotate(votes=Count('with_votes')).order_by('-votes')


    def __unicode__(self):
        return "%s upvoted %s" % (self.voter.username, self.link.title)

class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True)
    bio = models.TextField(null=True)

    def __unicode__(self):
        return "%s's profile" % self.user

def create_profile(sender, instance, created, **kwargs):
    if created:
        profile, created = UserProfile.objects.get_or_create(user=instance)

# Signal while saving user
from django.db.models.signals import post_save
post_save.connect(create_profile, sender=User)


def get_absolute_url(self):
    return reverse("link_detail", kwargs={"pk": str(self.id)})
