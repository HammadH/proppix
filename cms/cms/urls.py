from django.conf.urls import patterns, include, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

import views

urlpatterns = patterns('',
    # Examples:
    url(r'^cms/issmo/live/$', csrf_exempt(views.IssmoDubizzleLive.as_view()), name='issmo_dbz_live'),
    url(r'^cms/issmo/full/$', csrf_exempt(views.IssmoDubizzleFull.as_view()), name='issmo_dbz_full'),

    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    # static files (images, css, javascript, etc.)
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT}))