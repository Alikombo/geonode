# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import json
import logging
import traceback
from itertools import chain

from guardian.shortcuts import get_perms, get_objects_for_user

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import loader
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django_downloadview.response import DownloadResponse
from django.views.generic.edit import UpdateView, CreateView
from django.db.models import F
from django.forms.utils import ErrorList

from geonode.utils import resolve_object
from geonode.security.views import _perms_info_json
from geonode.people.forms import ProfileForm
from geonode.base.forms import CategoryForm, TKeywordForm
from geonode.base.models import (
    Thesaurus,
    TopicCategory)
from geonode.documents.models import Document, get_related_resources
from geonode.documents.forms import DocumentForm, DocumentCreateForm, DocumentReplaceForm
from geonode.documents.models import IMGTYPES
from geonode.utils import build_social_links
from geonode.groups.models import GroupProfile
from geonode.base.views import batch_modify
from geonode.monitoring import register_event
from geonode.monitoring.models import EventType
from geonode.security.utils import get_visible_resources

from dal import autocomplete

logger = logging.getLogger("geonode.documents.views")

ALLOWED_DOC_TYPES = settings.ALLOWED_DOCUMENT_TYPES

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this document")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this document.")
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this document")
_PERMISSION_MSG_METADATA = _(
    "You are not permitted to modify this document's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this document")


def _resolve_document(request, docid, permission='base.change_resourcebase',
                      msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the document by the provided primary key and check the optional permission.
    '''
    return resolve_object(request, Document, {'pk': docid},
                          permission=permission, permission_msg=msg, **kwargs)


def document_detail(request, docid):
    """
    The view that show details of each document
    """
    document = None
    try:
        document = _resolve_document(
            request,
            docid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)

    except Http404:
        return HttpResponse(
            loader.render_to_string(
                '404.html', context={
                }, request=request), status=404)

    except PermissionDenied:
        return HttpResponse(
            loader.render_to_string(
                '401.html', context={
                    'error_message': _("You are not allowed to view this document.")}, request=request), status=403)

    if document is None:
        return HttpResponse(
            'An unknown error has occured.',
            content_type="text/plain",
            status=401
        )

    else:
        # Add metadata_author or poc if missing
        document.add_missing_metadata_author_or_poc()

        related = get_related_resources(document)

        # Update count for popularity ranking,
        # but do not includes admins or resource owners
        if request.user != document.owner and not request.user.is_superuser:
            Document.objects.filter(
                id=document.id).update(
                popular_count=F('popular_count') + 1)

        metadata = document.link_set.metadata().filter(
            name__in=settings.DOWNLOAD_FORMATS_METADATA)

        group = None
        if document.group:
            try:
                group = GroupProfile.objects.get(slug=document.group.name)
            except ObjectDoesNotExist:
                group = None
        context_dict = {
            'perms_list': get_perms(
                request.user,
                document.get_self_resource()) + get_perms(request.user, document),
            'permissions_json': _perms_info_json(document),
            'resource': document,
            'group': group,
            'metadata': metadata,
            'imgtypes': IMGTYPES,
            'related': related}

        if settings.SOCIAL_ORIGINS:
            context_dict["social_links"] = build_social_links(
                request, document)

        if getattr(settings, 'EXIF_ENABLED', False):
            try:
                from geonode.documents.exif.utils import exif_extract_dict
                exif = exif_extract_dict(document)
                if exif:
                    context_dict['exif_data'] = exif
            except Exception:
                logger.error("Exif extraction failed.")

        if request.user.is_authenticated:
            if getattr(settings, 'FAVORITE_ENABLED', False):
                from geonode.favorite.utils import get_favorite_info
                context_dict["favorite_info"] = get_favorite_info(request.user, document)

        register_event(request, EventType.EVENT_VIEW, document)

        return render(
            request,
            "documents/document_detail.html",
            context=context_dict)


def document_download(request, docid):
    document = get_object_or_404(Document, pk=docid)

    if not request.user.has_perm(
            'base.download_resourcebase',
            obj=document.get_self_resource()):
        return HttpResponse(
            loader.render_to_string(
                '401.html', context={
                    'error_message': _("You are not allowed to view this document.")}, request=request), status=401)
    register_event(request, EventType.EVENT_DOWNLOAD, document)
    return DownloadResponse(document.doc_file)


class DocumentUploadView(CreateView):
    template_name = 'documents/document_upload.html'
    form_class = DocumentCreateForm

    def get_context_data(self, **kwargs):
        context = super(DocumentUploadView, self).get_context_data(**kwargs)
        context['ALLOWED_DOC_TYPES'] = ALLOWED_DOC_TYPES
        return context

    def form_invalid(self, form):
        if self.request.GET.get('no__redirect', False):
            out = {'success': False}
            out['message'] = ""
            status_code = 400
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=status_code)
        else:
            form.name = None
            form.title = None
            form.doc_file = None
            form.doc_url = None
            return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        # by default, if RESOURCE_PUBLISHING=True then document.is_published
        # must be set to False
        # RESOURCE_PUBLISHING works in similar way as ADMIN_MODERATE_UPLOADS,
        # but is applied to documents only. ADMIN_MODERATE_UPLOADS has wider
        # usage
        is_published = not (
            settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS)
        self.object.is_published = is_published
        self.object.save()
        form.save_many2many()
        self.object.set_permissions(form.cleaned_data['permissions'])

        abstract = None
        date = None
        regions = []
        keywords = []
        bbox = None

        out = {'success': False}

        if getattr(settings, 'EXIF_ENABLED', False):
            try:
                from geonode.documents.exif.utils import exif_extract_metadata_doc
                exif_metadata = exif_extract_metadata_doc(self.object)
                if exif_metadata:
                    date = exif_metadata.get('date', None)
                    keywords.extend(exif_metadata.get('keywords', []))
                    bbox = exif_metadata.get('bbox', None)
                    abstract = exif_metadata.get('abstract', None)
            except Exception:
                logger.error("Exif extraction failed.")

        if abstract:
            self.object.abstract = abstract
            self.object.save()

        if date:
            self.object.date = date
            self.object.date_type = "Creation"
            self.object.save()

        if len(regions) > 0:
            self.object.regions.add(*regions)

        if len(keywords) > 0:
            self.object.keywords.add(*keywords)

        if bbox:
            bbox_x0, bbox_x1, bbox_y0, bbox_y1 = bbox
            Document.objects.filter(id=self.object.pk).update(
                bbox_x0=bbox_x0,
                bbox_x1=bbox_x1,
                bbox_y0=bbox_y0,
                bbox_y1=bbox_y1)

        if getattr(settings, 'SLACK_ENABLED', False):
            try:
                from geonode.contrib.slack.utils import build_slack_message_document, send_slack_message
                send_slack_message(
                    build_slack_message_document(
                        "document_new", self.object))
            except Exception:
                logger.error("Could not send slack message for new document.")

        register_event(self.request, EventType.EVENT_UPLOAD, self.object)

        if self.request.GET.get('no__redirect', False):
            out['success'] = True
            out['url'] = reverse(
                'document_detail',
                args=(
                    self.object.id,
                ))
            if out['success']:
                status_code = 200
            else:
                status_code = 400
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=status_code)
        else:
            return HttpResponseRedirect(
                reverse(
                    'document_metadata',
                    args=(
                        self.object.id,
                    )))


class DocumentUpdateView(UpdateView):
    template_name = 'documents/document_replace.html'
    pk_url_kwarg = 'docid'
    form_class = DocumentReplaceForm
    queryset = Document.objects.all()
    context_object_name = 'document'

    def get_context_data(self, **kwargs):
        context = super(DocumentUpdateView, self).get_context_data(**kwargs)
        context['ALLOWED_DOC_TYPES'] = ALLOWED_DOC_TYPES
        return context

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save()
        register_event(self.request, EventType.EVENT_CHANGE, self.object)
        return HttpResponseRedirect(
            reverse(
                'document_metadata',
                args=(
                    self.object.id,
                )))


@login_required
def document_metadata(
        request,
        docid,
        template='documents/document_metadata.html',
        ajax=True):

    document = None
    try:
        document = _resolve_document(
            request,
            docid,
            'base.change_resourcebase_metadata',
            _PERMISSION_MSG_METADATA)

    except Http404:
        return HttpResponse(
            loader.render_to_string(
                '404.html', context={
                }, request=request), status=404)

    except PermissionDenied:
        return HttpResponse(
            loader.render_to_string(
                '401.html', context={
                    'error_message': _("You are not allowed to edit this document.")}, request=request), status=403)

    if document is None:
        return HttpResponse(
            'An unknown error has occured.',
            content_type="text/plain",
            status=401
        )

    else:
        # Add metadata_author or poc if missing
        document.add_missing_metadata_author_or_poc()
        poc = document.poc
        metadata_author = document.metadata_author
        topic_category = document.category

        if request.method == "POST":
            document_form = DocumentForm(
                request.POST,
                instance=document,
                prefix="resource")
            category_form = CategoryForm(request.POST, prefix="category_choice_field", initial=int(
                request.POST["category_choice_field"]) if "category_choice_field" in request.POST and
                request.POST["category_choice_field"] else None)
            tkeywords_form = TKeywordForm(request.POST)
        else:
            document_form = DocumentForm(instance=document, prefix="resource")
            category_form = CategoryForm(
                prefix="category_choice_field",
                initial=topic_category.id if topic_category else None)

            # Keywords from THESAURUS management
            doc_tkeywords = document.tkeywords.all()
            tkeywords_list = ''
            lang = 'en'  # TODO: use user's language
            if doc_tkeywords and len(doc_tkeywords) > 0:
                tkeywords_ids = doc_tkeywords.values_list('id', flat=True)
                if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
                    el = settings.THESAURUS
                    thesaurus_name = el['name']
                    try:
                        t = Thesaurus.objects.get(identifier=thesaurus_name)
                        for tk in t.thesaurus.filter(pk__in=tkeywords_ids):
                            tkl = tk.keyword.filter(lang=lang)
                            if len(tkl) > 0:
                                tkl_ids = ",".join(
                                    map(str, tkl.values_list('id', flat=True)))
                                tkeywords_list += "," + \
                                    tkl_ids if len(
                                        tkeywords_list) > 0 else tkl_ids
                    except Exception:
                        tb = traceback.format_exc()
                        logger.error(tb)

            tkeywords_form = TKeywordForm(instance=document)

        if request.method == "POST" and document_form.is_valid(
        ) and category_form.is_valid():
            new_poc = document_form.cleaned_data['poc']
            new_author = document_form.cleaned_data['metadata_author']
            new_keywords = document_form.cleaned_data['keywords']
            new_regions = document_form.cleaned_data['regions']

            new_category = None
            if category_form and 'category_choice_field' in category_form.cleaned_data and\
            category_form.cleaned_data['category_choice_field']:
                new_category = TopicCategory.objects.get(
                    id=int(category_form.cleaned_data['category_choice_field']))

            if new_poc is None:
                if poc is None:
                    poc_form = ProfileForm(
                        request.POST,
                        prefix="poc",
                        instance=poc)
                else:
                    poc_form = ProfileForm(request.POST, prefix="poc")
                if poc_form.is_valid():
                    if len(poc_form.cleaned_data['profile']) == 0:
                        # FIXME use form.add_error in django > 1.7
                        errors = poc_form._errors.setdefault(
                            'profile', ErrorList())
                        errors.append(
                            _('You must set a point of contact for this resource'))
                        poc = None
                if poc_form.has_changed and poc_form.is_valid():
                    new_poc = poc_form.save()

            if new_author is None:
                if metadata_author is None:
                    author_form = ProfileForm(request.POST, prefix="author",
                                              instance=metadata_author)
                else:
                    author_form = ProfileForm(request.POST, prefix="author")
                if author_form.is_valid():
                    if len(author_form.cleaned_data['profile']) == 0:
                        # FIXME use form.add_error in django > 1.7
                        errors = author_form._errors.setdefault(
                            'profile', ErrorList())
                        errors.append(
                            _('You must set an author for this resource'))
                        metadata_author = None
                if author_form.has_changed and author_form.is_valid():
                    new_author = author_form.save()

            document = document_form.instance
            if new_poc is not None and new_author is not None:
                document.poc = new_poc
                document.metadata_author = new_author
            document.keywords.clear()
            document.keywords.add(*new_keywords)
            document.regions.clear()
            document.regions.add(*new_regions)
            document.category = new_category
            document.save()
            document_form.save_many2many()

            register_event(request, EventType.EVENT_CHANGE_METADATA, document)
            if not ajax:
                return HttpResponseRedirect(
                    reverse(
                        'document_detail',
                        args=(
                            document.id,
                        )))

            message = document.id

            try:
                # Keywords from THESAURUS management
                # Rewritten to work with updated autocomplete
                if not tkeywords_form.is_valid():
                    return HttpResponse(json.dumps({'message': "Invalid thesaurus keywords"}, status_code=400))

                tkeywords_data = tkeywords_form.cleaned_data['tkeywords']

                thesaurus_setting = getattr(settings, 'THESAURUS', None)
                if thesaurus_setting:
                    tkeywords_data = tkeywords_data.filter(
                        thesaurus__identifier=thesaurus_setting['name']
                    )
                    document.tkeywords = tkeywords_data
            except Exception:
                tb = traceback.format_exc()
                logger.error(tb)

            return HttpResponse(json.dumps({'message': message}))

        # - POST Request Ends here -

        # Request.GET
        if poc is not None:
            document_form.fields['poc'].initial = poc.id
            poc_form = ProfileForm(prefix="poc")
            poc_form.hidden = True

        if metadata_author is not None:
            document_form.fields['metadata_author'].initial = metadata_author.id
            author_form = ProfileForm(prefix="author")
            author_form.hidden = True

        metadata_author_groups = []
        if request.user.is_superuser or request.user.is_staff:
            metadata_author_groups = GroupProfile.objects.all()
        else:
            try:
                all_metadata_author_groups = chain(
                    request.user.group_list_all(),
                    GroupProfile.objects.exclude(
                        access="private").exclude(access="public-invite"))
            except Exception:
                all_metadata_author_groups = GroupProfile.objects.exclude(
                    access="private").exclude(access="public-invite")
            [metadata_author_groups.append(item) for item in all_metadata_author_groups
                if item not in metadata_author_groups]

        if settings.ADMIN_MODERATE_UPLOADS:
            if not request.user.is_superuser:
                document_form.fields['is_published'].widget.attrs.update(
                    {'disabled': 'true'})

                can_change_metadata = request.user.has_perm(
                    'change_resourcebase_metadata',
                    document.get_self_resource())
                try:
                    is_manager = request.user.groupmember_set.all().filter(role='manager').exists()
                except Exception:
                    is_manager = False
                if not is_manager or not can_change_metadata:
                    document_form.fields['is_approved'].widget.attrs.update(
                        {'disabled': 'true'})

        register_event(request, EventType.EVENT_VIEW_METADATA, document)
        return render(request, template, context={
            "resource": document,
            "document": document,
            "document_form": document_form,
            "poc_form": poc_form,
            "author_form": author_form,
            "category_form": category_form,
            "tkeywords_form": tkeywords_form,
            "metadata_author_groups": metadata_author_groups,
            "TOPICCATEGORY_MANDATORY": getattr(settings, 'TOPICCATEGORY_MANDATORY', False),
            "GROUP_MANDATORY_RESOURCES": getattr(settings, 'GROUP_MANDATORY_RESOURCES', False),
        })


@login_required
def document_metadata_advanced(request, docid):
    return document_metadata(
        request,
        docid,
        template='documents/document_metadata_advanced.html')


def document_search_page(request):
    # for non-ajax requests, render a generic search page

    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    return render(
        request,
        'documents/document_search.html',
        context={'init_search': json.dumps(params or {}), "site": settings.SITEURL})


@login_required
def document_remove(request, docid, template='documents/document_remove.html'):
    try:
        document = _resolve_document(
            request,
            docid,
            'base.delete_resourcebase',
            _PERMISSION_MSG_DELETE)

        if request.method == 'GET':
            return render(request, template, context={
                "document": document
            })

        if request.method == 'POST':
            document.delete()

            register_event(request, EventType.EVENT_REMOVE, document)
            return HttpResponseRedirect(reverse("document_browse"))
        else:
            return HttpResponse("Not allowed", status=403)

    except PermissionDenied:
        return HttpResponse(
            'You are not allowed to delete this document',
            content_type="text/plain",
            status=401
        )


def document_metadata_detail(
        request,
        docid,
        template='documents/document_metadata_detail.html'):
    document = _resolve_document(
        request,
        docid,
        'view_resourcebase',
        _PERMISSION_MSG_METADATA)
    group = None
    if document.group:
        try:
            group = GroupProfile.objects.get(slug=document.group.name)
        except ObjectDoesNotExist:
            group = None
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    register_event(request, EventType.EVENT_VIEW_METADATA, document)
    return render(request, template, context={
        "resource": document,
        "group": group,
        'SITEURL': site_url
    })


@login_required
def document_batch_metadata(request, ids):
    return batch_modify(request, ids, 'Document')


class DocumentAutocomplete(autocomplete.Select2QuerySetView):

    def get_queryset(self):
        request = self.request
        permitted = get_objects_for_user(
            request.user,
            'base.view_resourcebase')
        qs = Document.objects.all().filter(id__in=permitted)

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return get_visible_resources(
            qs,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)