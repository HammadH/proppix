from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

import views

urlpatterns = patterns('',
    # Examples:
    url(r'^cms/issmo_dbz/live/$', csrf_exempt(views.IssmoDubizzleLive.as_view()), name='issmo_dbz_live'),
    url(r'^cms/issmo_dbz/full/$', csrf_exempt(views.IssmoDubizzleFull.as_view()), name='issmo_dbz_full'),
    url(r'^cms/issmo_pf/live/$', csrf_exempt(views.IssmoPropertyFinderLive.as_view()), name='issmo_pf_live'),
    url(r'^cms/issmo_pf/full/$', csrf_exempt(views.IssmoPropertyFinderFull.as_view()), name='issmo_pf_full'),
    url(r'^cms/issmo_pf/live_v2/$', csrf_exempt(views.IssmoPropertyFinderLive_V2.as_view()), name='issmo_pf_live_v2'),
    url(r'^cms/issmo_platform/$', csrf_exempt(views.Platform.as_view()), name='issmo_platform'),
   # url(r'^cms/issmo_pf/full_v2/$', csrf_exempt(views.IssmoPropertyFinderFull_V2.as_view()), name='issmo_pf_full'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT}))