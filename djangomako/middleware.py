#   Copyright (c) 2008 Mikeal Rogers
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import threading
import tempfile

from django.conf import settings
from django.template import RequestContext
from django.template.context import _builtin_context_processors
from django.utils.module_loading import import_by_path

from mako.lookup import TemplateLookup

REQUEST_CONTEXT = threading.local()

class MakoMiddleware(object):
    def __init__(self):
        """Setup mako variables and lookup object"""
        # Set all mako variables based on django settings
        global template_dirs, output_encoding, module_directory, encoding_errors
        directories      = getattr(settings, 'MAKO_TEMPLATE_DIRS', settings.TEMPLATE_DIRS)

        module_directory = getattr(settings, 'MAKO_MODULE_DIR', None)
        if module_directory is None:
            module_directory = tempfile.mkdtemp()

        output_encoding  = getattr(settings, 'MAKO_OUTPUT_ENCODING', 'utf-8')
        encoding_errors  = getattr(settings, 'MAKO_ENCODING_ERRORS', 'replace')

        global lookup
        lookup = TemplateLookup(directories=directories,
                                module_directory=module_directory,
                                output_encoding=output_encoding,
                                encoding_errors=encoding_errors,
                                )
        import djangomako
        djangomako.lookup = lookup

    def process_request(self, request):
        """ Process the middleware request. """
        REQUEST_CONTEXT.request = request

    def process_response(self, __, response):
        """ Process the middleware response. """
        REQUEST_CONTEXT.request = None
        return response

def get_template_context_processors():
    """
    Returns the context processors defined in settings.TEMPLATES.
    """
    context_processors = _builtin_context_processors
    context_processors += tuple(
        settings.DEFAULT_TEMPLATE_ENGINE['OPTIONS']['context_processors']
    )

    return tuple(import_by_path(path) for path in context_processors)

def get_template_request_context():
    """
    Returns the template processing context to use for the current request,
    or returns None if there is not a current request.
    """
    request = getattr(REQUEST_CONTEXT, 'request', None)
    if not request:
        return None
    context = RequestContext(request)

    for processor in get_template_context_processors():
        context.update(processor(request))

    return context
