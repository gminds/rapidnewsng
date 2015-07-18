from django.conf.urls import *
from django.contrib import admin
import dbindexer
from django.views.generic import TemplateView
from links.views import LinkListView
from links.views import LinkNewestView
from links.views import UserProfileDetailView
from django.contrib.auth.decorators import login_required as auth
from links.views import UserProfileEditView
from links.views import LinkCreateView
from links.views import LinkDetailView
from links.views import LinkUpdateView
from links.views import LinkDeleteView
from links.views import VoteFormView
from links.views import fetchRss
from links.views import fetchRs2
from links.views import derank
from links.views import rerank
from links.views import api


handler500 = 'djangotoolbox.errorviews.server_error'

# django admin
admin.autodiscover()

# search for dbindexes.py in all INSTALLED_APPS and load them
dbindexer.autodiscover()



urlpatterns = patterns('',
    ('^_ah/warmup$', 'djangoappengine.views.warmup'),
    url(r'^$', LinkListView.as_view(), name='home'),
    url(r'^newest/$', LinkNewestView.as_view(), name='newest'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name="login"),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', name="logout"),
    url(r'^accounts/', include('registration.backends.simple.urls')),
    url(r'^users/(?P<slug>\w+)/$', UserProfileDetailView.as_view(), name="profile"),
    url(r'^edit_profile/$', auth(UserProfileEditView.as_view()), name="edit_profile"),
    url(r'^link/create/$', auth(LinkCreateView.as_view()),  name='link_create'),
    url(r'^link/(?P<pk>\d+)/$', LinkDetailView.as_view(),   name='link_detail'),
    url(r'^link/update/(?P<pk>\d+)/$', auth(LinkUpdateView.as_view()),  name='link_update'),
    url(r'^link/delete/(?P<pk>\d+)/$', auth(LinkDeleteView.as_view()),  name='link_delete'),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r'^vote/$', VoteFormView.as_view(), name="vote"),
    url(r'^rerank/$', rerank.as_view()),
    url(r'^derank/$', derank.as_view()),
    url(r'^fetchRss/$', fetchRss.as_view()),
    url(r'^fetchRs2/$', fetchRs2.as_view()),
    url(r'^api/$', api.as_view()),
#    (r'^blog/', include('blog.urls')),
#    (r'^', TemplateView.as_view(template_name="home.html")),
#    #url(r'^$', TemplateView.as_view("home.html")),
#    ('^$', 'django.views.generic.simple.direct_to_template', {'template': 'home.html'}),
    ('^admin/', include(admin.site.urls)),
)
