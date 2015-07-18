from rest_framework.renderers import JSONRenderer, XMLRenderer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import mixins
from rest_framework import generics
from rest_framework.parsers import XMLParser
from StringIO import StringIO
from UserString import MutableString
from links.serializers import LinkSerializer, Wikifetch, UserSerializer, ItemSerializer
from django.template import Context, RequestContext
from django.shortcuts import render_to_response, get_object_or_404, render, redirect
from django import http
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
import urllib2, urllib
from django.views.generic import ListView, DetailView
from django.contrib.auth import get_user_model
from .models import UserProfile
from django.contrib.auth.models import User
from .models import Link, Vote
from django.views.generic.edit import UpdateView
from .forms import UserProfileForm
from django.core.urlresolvers import reverse
from django.views.generic.edit import CreateView
from .forms import LinkForm
from django.views.generic import DetailView
from django.core.urlresolvers import reverse_lazy
from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView
from django.contrib.comments.models import Comment
from django.views.generic.edit import FormView
from .forms import VoteForm
from .models import Vote
import json
from django.http import HttpResponse
from xml.etree import ElementTree as ET
from django.core.cache import cache
from django.views.decorators.cache import cache_control
import logging
from random import randrange
import re
import AppConfig
from google.appengine.api import urlfetch
from BeautifulSoup import BeautifulSoup
from urlparse import urlparse
from feedparser import parse
from HTMLParser import HTMLParser

TAG_RE = re.compile(r'<[^>]+>')

class rerank(APIView):
    # ...
    @csrf_exempt
    def get(self, request, format=None):
        def rank_all():
            for link in Link.objects.all().order_by('-votes'):
                link.set_rank()

        import time

        def show_all():
#        print "\n".join("%10s %0.2f" % (l.title, l.rank_score,
# #                            ) for l in Link.objects.all())
            print "----\n\n\n"
        rank_all()
        show_all()
        return Response('----------------------')

class derank(APIView):
    # ...
    @csrf_exempt
    def get(self, request, format=None):
        def derank_all():
            for link in Link.objects.all().order_by('rank_score', 'submitted_on')[:20] :
                link.delete()

        import time

        def show_all():
#        print "\n".join("%10s %0.2f" % (l.title, l.rank_score,
# #                            ) for l in Link.objects.all())
            print "----\n\n\n"
        derank_all()
        show_all()
        return Response('----------------------')
    
''' 
    if foo:
        return HttpResponseNotFound('<h1>Page not found</h1>')
    else:
        return HttpResponse('<h1>Page was found</h1>')
'''
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

class LinkListView(ListView):
    model = Link
#    queryset = Vote.with_votes.all()
    queryset = Link.objects.all().order_by('-rank_score', '-votes')
    paginate_by = 20
    def get_context_data(self, **kwargs):
        context = super(LinkListView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            voted = Vote.objects.filter(voter=self.request.user)
            links_in_page = [link.id for link in context["object_list"]]
            voted = voted.filter(link_id__in=links_in_page)
            voted = voted.values_list('link_id', flat=True)
            context["voted"] = voted
        return context

class LinkNewestView(ListView):
    model = Link
#    queryset = Vote.with_votes.all()
    queryset = Link.objects.all().order_by('-submitted_on')
    paginate_by = 20
    def get_context_data(self, **kwargs):
        context = super(LinkNewestView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            voted = Vote.objects.filter(voter=self.request.user)
            links_in_page = [link.id for link in context["object_list"]]
            voted = voted.filter(link_id__in=links_in_page)
            voted = voted.values_list('link_id', flat=True)
            context["voted"] = voted
        return context

class UserProfileDetailView(DetailView):
    model = get_user_model()
    slug_field = "username"
    template_name = "user_detail.html"

    def get_object(self, queryset=None):
        user = super(UserProfileDetailView, self).get_object(queryset)
        UserProfile.objects.get_or_create(user=user)
        return user

class UserProfileEditView(UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = "edit_profile.html"

    def get_object(self, queryset=None):
        return UserProfile.objects.get_or_create(user=self.request.user)[0]

    def get_success_url(self):
        return reverse("profile", kwargs={'slug': self.request.user})


class LinkCreateView(CreateView):
    model = Link
    form_class = LinkForm

    def form_valid(self, form):
        f = form.save(commit=False)
        f.rank_score = 0.0
        f.submitter = self.request.user
        f.save()

        return super(CreateView, self).form_valid(form)

class LinkUpdateView(UpdateView):
    model = Link
    form_class = LinkForm

class LinkDeleteView(DeleteView):
    model = Link
    success_url = reverse_lazy("home")

class LinkDetailView(DetailView):
    model = Link

	
	
	

class OldVoteFormView(FormView):
    form_class = VoteForm

    def form_valid(self, form):
        link = get_object_or_404(Link, pk=form.data["link"])
        user = self.request.user
        prev_votes = Vote.objects.filter(voter=user, link=link)
        has_voted = (prev_votes.count() > 0)

        if not has_voted:
            # add vote
            Vote.objects.create(voter=user, link=link)
            link.votes +=1
            link.save(update_fields=["votes"]) 
#            Link.objects.filter(link=link).update(views=F('views')+1)
#            n = Link.objects.update(votes=F('votes')+1)  
            print("voted")
            print(link.votes)
        else:
            # delete vote
            prev_votes[0].delete()
            link.votes -=1
            link.save(update_fields=["votes"]) 
            print("unvoted")
            print(link.votes)

        return redirect("home")

    def form_invalid(self, form):
        print("invalid")
        return redirect("home")

class JSONFormMixin(object):
    def create_response(self, vdict=dict(), valid_form=True):
        response = HttpResponse(json.dumps(vdict), content_type='application/json')
        response.status = 200 if valid_form else 500
        return response

class VoteFormBaseView(FormView):
    form_class = VoteForm
    

    @csrf_exempt
    def create_response(self, vdict=dict(), valid_form=True):
        response = HttpResponse(json.dumps(vdict))
        response.status = 200 if valid_form else 500
        return response

    def form_valid(self, form):
        link = get_object_or_404(Link, pk=form.data["link"])
        if self.request.user.is_authenticated():
            user = self.request.user
            prev_votes = Vote.objects.filter(voter=user, link=link)
            has_voted = (len(prev_votes) > 0)

            ret = {"success": 1}
            if not has_voted:
                # add vote
                v = Vote.objects.create(voter=user, link=link)
                link.votes +=1
                link.save(update_fields=["votes"]) 
                ret["voteobj"] = v.id
            else:
                # delete vote
                link.votes -=1
                link.save(update_fields=["votes"]) 
                prev_votes[0].delete()
                ret["unvoted"] = 1
            return self.create_response(ret, True)
        else:
            ret = {"location": 'login'}
        return self.create_response(ret, True)

    def form_invalid(self, form):
        if self.request.user.is_authenticated():
            ret = {"success": 0, "form_errors": form.errors }
            return self.create_response(ret, False)
        else:
            ret = {"location": 'login'}
        return self.create_response(ret, False)

class VoteFormView(JSONFormMixin, VoteFormBaseView):
    pass



class api(APIView):
    @csrf_exempt
    def get(self, request, format=None):
#    queryset = Vote.with_votes.all()
        MEMCACHE_GREETINGS = 'APILINKS'
        content = cache.get(MEMCACHE_GREETINGS)
        time = 1800 
        if content is None:
            content = Link.objects.all().order_by('-rank_score', '-votes')[:20]
            logging.debug("value of  user my var is %s", str(content))
            serializer = LinkSerializer(content)
            cache.add(MEMCACHE_GREETINGS, serializer.data, time)
            return Response(serializer.data)
        else:
            return Response(content)



class fetchRss(APIView):

#    renderer_classes = (XMLRenderer, JSONRenderer)
#    @cache_control(must_revalidate=True, max_age=3600)
    @csrf_exempt
    def get(self, request, format=None):
        content = MutableString()
        content = []
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/24.0')]
#        submitter = User.objects.get(username='test')
#        logging.debug("value of  user my var is %s", str(submitter.username))


        def load(durl, greet):
                def remove_tags(text):
                    text = TAG_RE.sub('', text)
                    text = re.sub("\n", "", text)
                    text = re.sub("\"", "\\\"", text)
                    return "" . join(filter(lambda x: ord(x)<128, text))
                content = MutableString()
                content = []
                opener = urllib2.build_opener()
                opener.addheaders = [('User-agent', 'Mozilla/24.0')]
                MEMCACHE_GREETINGS = greet
                data = cache.get(MEMCACHE_GREETINGS)
                time = 1800 
                if data is None:
                    file = urllib2.urlopen(durl)
                    data = file.read()
                    file.close()
                    cache.add(MEMCACHE_GREETINGS, data, time)
                doc = ET.fromstring(data)
#                logging.debug("value of  16 my var is %s", str(data))
                gg = doc.findall('channel/item')
#                logging.debug("value of  1 my var is %s", str(gg))
                for node in gg:
                    title = node.find('./title').text
                    description = node.find('./description').text
                    url = node.find('./link').text
                    info = {}
                    info['title'] = remove_tags(title)
                    info['description'] = remove_tags(description)
                    info['url'] = url
#                    submitterobj = User.objects.get(username='test')
#                    submitter = submitterobj.username
                    info['submitter'] = User.objects.filter(username='gminds')[0].id
                    info['linksource'] = urlparse(url).netloc
#                    info['submitter'] = User.objects.filter(is_superuser=1)[1].id
                    info['votes'] = randrange(20)
                    logging.debug("value of  user my var is %s", str(User.objects.filter(username='gminds')[0].get_username()))
#                    info[title] = Wikifetch(title, description, url)

                    content.append(info)
#                   logging.debug("value of  1 my var is %s", str(title))
#                    logging.debug("value of  2 my var is %s", str(link))
                return content


#        url_id = request.GET['wiki']
#        url = 'http://en.wikipedia.org/w/index.php?title='+url_id+'&action=history' medlineplus http://www.nlm.nih.gov/medlineplus/feeds/news_en.xml
# reuters http://feeds.reuters.com/reuters/healthNews webmd http://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC    medicinenet http://www.medicinenet.com/rss/dailyhealth.xml

#        data = 'http://google.com'
        channel = request.GET['channel']
#        logging.debug("value of  16 my var is %s", str(channel))
        if channel == 'BBC':

                MEMCACHE_GREETINGS = 'bbc'
                url = 'http://feeds.bbci.co.uk/news/health/rss.xml'
                content = load(url, MEMCACHE_GREETINGS)

        elif channel == 'MEDLINEPLUS':
                url = 'http://www.nlm.nih.gov/medlineplus/feeds/news_en.xml'
                MEMCACHE_GREETINGS = 'MEDLINEPLUS'
                content = load(url, MEMCACHE_GREETINGS)
        elif channel == 'PUNCH':
                url = 'http://www.latestnigeriannews.com/feed/punch/rss.xml'
                MEMCACHE_GREETINGS = 'PUNCH'
                content = load(url, MEMCACHE_GREETINGS)
        elif channel == 'VANGUARD':
                url = 'http://www.vanguardngr.com/feed/'
                MEMCACHE_GREETINGS = 'VANGUARD'
                content = load(url, MEMCACHE_GREETINGS)
        elif channel == 'SUNNEWS':
                url = 'http://sunnewsonline.com/new/?feed=rss2'
                MEMCACHE_GREETINGS = 'SUNNEWS'
                content = load(url, MEMCACHE_GREETINGS)
        elif channel == 'GUARDIAN':
                url = 'http://www.latestnigeriannews.com/feed/guardian/rss.xml'
                MEMCACHE_GREETINGS = 'GUARDIAN'
                content = load(url, MEMCACHE_GREETINGS)
        elif channel == 'THISDAY':
                url = 'http://www.latestnigeriannews.com/feed/thisday/rss.xml'
                MEMCACHE_GREETINGS = 'THISDAY'
                content = load(url, MEMCACHE_GREETINGS)
        elif channel == 'DAILYTIMES':
                url = 'http://www.dailytimes.com.ng/rss/articles/all'
                MEMCACHE_GREETINGS = 'DAILYTIMES'
                content = load(url, MEMCACHE_GREETINGS)
        else :
                url = 'http://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC'
                MEMCACHE_GREETINGS = 'WEBMD'
                content = load(url, MEMCACHE_GREETINGS)

        serializer2 = LinkSerializer(content, many=True)
        serializer = LinkSerializer(data=content)
#        submitterobj = User.objects.get(username='test') http://www.nairaland.com/feed
#        serializer2.object.submitter = submitterobj
        logging.debug("value of  27 my var is %s", str(serializer))
        if serializer.is_valid():
            serializer.save()
        return Response(serializer2.data)





class fetchRs2(APIView):

#    renderer_classes = (XMLRenderer, JSONRenderer)
#    @cache_control(must_revalidate=True, max_age=3600)
    @csrf_exempt
    def get(self, request, format=None):
        content = MutableString()
        content = []
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/24.0')]
#        submitter = User.objects.get(username='test')
#        logging.debug("value of  user my var is %s", str(submitter.username))


        def load(durl, greet):
                def remove_tags(text):
                    text = TAG_RE.sub('', text)
                    text = re.sub("\n", "", text)
                    text = re.sub("\"", "\\\"", text)
                    text = re.sub(u"(\u2018|\u2019)", "'", text)
                    return "" . join(filter(lambda x: ord(x)<128, text))
                content = MutableString()
                content = []

                def entry_to_link_dict(entry):
                    s = MLStripper()
                    s.feed(entry.description)
                    link = {
                       "title": remove_tags(entry.title),
                       "url": entry.link,
                       "linksource": urlparse(entry.link).netloc,
                       "votes": "1",
                       "description": remove_tags(s.get_data()),
                    }
                    return link
                try:
                    user_id = User.objects.filter(username='admin')[0].id
                except IndexError:
                    return
                for entry in parse(durl).entries:
                    link = entry_to_link_dict(entry)
                    link["submitter"] = user_id
                    info = link
                    logging.debug("value of  user my var is %s", str(User.objects.filter(username='admin')[0].get_username()))
#                    info[title] = Wikifetch(title, description, url)

                    content.append(info)
#                   logging.debug("value of  1 my var is %s", str(title))
#                    logging.debug("value of  2 my var is %s", str(link))
                return content


#        data = 'http://google.com'
        channel = request.GET['channel']
#        logging.debug("value of  16 my var is %s", str(channel))
        content = load(channel, channel)
        serializer2 = LinkSerializer(content, many=True)
        serializer = LinkSerializer(data=content)
#        submitterobj = User.objects.get(username='test') http://www.nairaland.com/feed
#        serializer2.object.submitter = submitterobj
        logging.debug("value of  27 my var is %s", str(serializer))
        if serializer.is_valid():
            serializer.save()
        return Response(serializer2.data)





    


