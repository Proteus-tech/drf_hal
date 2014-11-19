from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),

    url(r'^choice', include('sample_app.choice_urls')),
    url(r'^poll', include('sample_app.poll_urls')),
    url(r'^channel', include('sample_app.channel_urls')),
    url(r'^partner', include('sample_app.partner_urls')),
    url(r'^user', include('sample_app.user_urls')),
)
