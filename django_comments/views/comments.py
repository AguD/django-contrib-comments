from __future__ import absolute_import

from django import http
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.core.urlresolvers import reverse_lazy

import django_comments
from django_comments import signals
from django_comments.views.utils import next_redirect, confirmation_view
from common.views import AjaxifiedFormView, CsrfProtectMixin

class CommentPostBadRequest(http.HttpResponseBadRequest):
    """
    Response returned when a comment post is invalid. If ``DEBUG`` is on a
    nice-ish error message will be displayed (for debugging purposes), but in
    production mode a simple opaque 400 page will be displayed.
    """
    def __init__(self, why):
        super(CommentPostBadRequest, self).__init__()
        if settings.DEBUG:
            self.content = render_to_string("comments/400-debug.html", {"why": why})


@csrf_protect
@require_POST
def postt_comment(request, next=None, using=None):
    """
    Post a comment.

    HTTP POST is required. If ``POST['submit'] == "preview"`` or if there are
    errors a preview template, ``comments/preview.html``, will be rendered.
    """
    data = request.POST.copy()
    # Look up the object we're trying to comment about
    ctype = data.get("content_type")
    object_pk = data.get("object_pk")
    if ctype is None or object_pk is None:
        return CommentPostBadRequest("Missing content_type or object_pk field.")
    try:
        model = models.get_model(*ctype.split(".", 1))
        target = model._default_manager.using(using).get(pk=object_pk)
    except TypeError:
        return CommentPostBadRequest(
            "Invalid content_type value: %r" % escape(ctype))
    except AttributeError:
        return CommentPostBadRequest(
            "The given content-type %r does not resolve to a valid model." % \
                escape(ctype))
    except ObjectDoesNotExist:
        return CommentPostBadRequest(
            "No object matching content-type %r and object PK %r exists." % \
                (escape(ctype), escape(object_pk)))
    except (ValueError, ValidationError) as e:
        return CommentPostBadRequest(
            "Attempting go get content-type %r and object PK %r exists raised %s" % \
                (escape(ctype), escape(object_pk), e.__class__.__name__))
    # Do we want to preview the comment?
    preview = "preview" in data
    # Construct the comment form
    form = django_comments.get_form()(target, data=data)
    # Check security information
    if form.security_errors():
        return CommentPostBadRequest(
            "The comment form failed security verification: %s" % \
                escape(str(form.security_errors())))

    # If there are errors or if we requested a preview show the comment
    if form.errors or preview:
        template_list = [
            "comments/%s/%s/preview.html" % (model._meta.app_label, model._meta.module_name),
            "comments/%s/preview.html" % model._meta.app_label,
            "comments/preview.html",
        ]
        return render_to_response(
            template_list, {
                "comment": form.data.get("comment", ""),
                "form": form,
                "next": data.get("next", next),
            },
            RequestContext(request, {})
        )

    # Otherwise create the comment
    comment = form.get_comment_object()
    comment.ip_address = request.META.get("REMOTE_ADDR", None)
    if request.user.is_authenticated():
        comment.user = request.user

    # Signal that the comment is about to be saved
    responses = signals.comment_will_be_posted.send(
        sender=comment.__class__,
        comment=comment,
        request=request
    )
    for (receiver, response) in responses:
        if response == False:
            return CommentPostBadRequest(
                "comment_will_be_posted receiver %r killed the comment" % receiver.__name__)
    # Save the comment and signal that it was saved
    comment.save()
    signals.comment_was_posted.send(
        sender=comment.__class__,
        comment=comment,
        request=request
    )

    return next_redirect(request, fallback=next or 'comments-comment-done',
        c=comment._get_pk_val())

comment_done = confirmation_view(
    template="comments/posted.html",
    doc="""Display a "comment was posted" success page."""
)


class CommentView(CsrfProtectMixin, AjaxifiedFormView):
    http_method_names = ['post'] #Only accept post calls
    template_name = "comments/form.html"
    form_class = django_comments.get_form()
    next = None

    def post(self, request, *args, **kwargs):
        data = request.POST.copy()
        # Look up the object we're trying to comment about
        ctype = data.get("content_type")
        object_pk = data.get("object_pk")
        if ctype is None or object_pk is None:
            return CommentPostBadRequest("Missing content_type or object_pk field.")
        try:
            self.target_model = models.get_model(*ctype.split(".", 1))
            target = self.target_model._default_manager.get(pk=object_pk)
        except TypeError:
            return CommentPostBadRequest(
                "Invalid content_type value: %r" % escape(ctype))
        except AttributeError:
            return CommentPostBadRequest(
                "The given content-type %r does not resolve to a valid model." % \
                    escape(ctype))
        except ObjectDoesNotExist:
            return CommentPostBadRequest(
                "No object matching content-type %r and object PK %r exists." % \
                    (escape(ctype), escape(object_pk)))
        except (ValueError, ValidationError) as e:
            return CommentPostBadRequest(
                "Attempting go get content-type %r and object PK %r exists raised %s" % \
                    (escape(ctype), escape(object_pk), e.__class__.__name__))
        preview = "preview" in data
        form = django_comments.get_form()(target, data=data)
        # Check security information
        if form.security_errors():
            return CommentPostBadRequest(
                "The comment form failed security verification: %s" % \
                    escape(str(form.security_errors())))

        if form.is_valid():
            return self.form_valid(form)
        if form.errors or preview:
            return self.form_invalid(form)

    def form_invalid(self, form):
        template_list = [
            "comments/%s/%s/preview.html" % (self.target_model._meta.app_label, self.target_model._meta.module_name),
            "comments/%s/preview.html" % self.target_model._meta.app_label,
            "comments/preview.html",
        ]
        return render_to_response(
            template_list, {
                "comment": form.data.get("comment", ""),
                "form": form,
                "next": data.get("next", next),
            },
            RequestContext(request, {})
        )

    def form_valid(self, form):
        comment = form.get_comment_object()
        comment.ip_address = self.request.META.get("REMOTE_ADDR", None)
        if self.request.user.is_authenticated():
            comment.user = self.request.user
        # Signal that the comment is about to be saved
        responses = signals.comment_will_be_posted.send(
            sender=comment.__class__,
            comment=comment,
            request=self.request
        )
        for (receiver, response) in responses:
            if response == False:
                return CommentPostBadRequest(
                    "comment_will_be_posted receiver %r killed the comment" % receiver.__name__)
        # Save the comment and signal that it was saved
        comment.save()
        signals.comment_was_posted.send(
            sender=comment.__class__,
            comment=comment,
            request=self.request
        )
        self.object = comment
        http_response = next_redirect(self.request, fallback=self.next or 'comments-comment-done',
            c=comment._get_pk_val())
        self.success_url = http_response.get("location")
        return super(CommentView, self).form_valid(form)

    def ajax_response_valid(self, form):
        comment_html = render_to_string(
            template_name = 'comments/single_comment.html',
            dictionary = {
                'comment': self.object,
                'user': self.request.user,
                'faded': True
            }
        )
        return dict(success=True, comment_html=comment_html)

post_comment = CommentView.as_view()