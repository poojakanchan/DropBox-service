# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Sample application that demonstrates how to use the App Engine Blobstore API.

For more information, see README.md.
"""

# [START all]
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api.images import get_serving_url
import logging
import webapp2
import os
import zipfile
import sys

class FileInfo(db.Model):
    blob = blobstore.BlobReferenceProperty(required=True)
    uploaded_by = db.UserProperty(required=True)
    uploaded_at = db.DateTimeProperty(required=True, auto_now_add=True)
    image= db.BlobProperty
   
   # image=ndb.BlobProperty(required=True)

class BaseHandler(webapp.RequestHandler):
    def render_template(self, file, template_args):
        path = os.path.join(os.path.dirname(__file__), "templates", file)
        self.response.out.write(template.render(path, template_args))

  
class FileUploadFormHandler(BaseHandler):
    @util.login_required    
    def get(self):
        self.response.out.write(template.render("upload.html", {
        'form_url': blobstore.create_upload_url('/upload'),
        'logout_url': users.create_logout_url('/'),
    }))

class FileUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        blob_info = self.get_uploads()[0]
        if not users.get_current_user():
            blob_info.delete()
            self.redirect(users.create_login_url("/"))
            return
     #   url=images.get_serving_url(blob_info.key(), size=None, crop=False, secure_url=None, filename=None, rpc=None)
        file_info = FileInfo(
                         blob=blob_info.key(),
                         uploaded_by=users.get_current_user(),
                         image=blob_info)
                        # image=thumbnail)
        db.put(file_info)
        logging.info("redirecting")
        #self.redirect("/file/%d" % (file_info.key().id(),))
        self.redirect('/files/all')
        #self.redirect("/file/%s" % (blob_info.key()))
        
class FileInfoHandler(BaseHandler):
    def get(self, file_id):
       # file_info = FileInfo.get_by_id(long(file_id))
        if not file_id:
            self.error(404)
            return
        file_info = FileInfo.get_by_id(long(file_id))
        if not file_info or not file_info.blob:
            self.error(404)
            return
        img = images.Image(blob_key=file_info.blob)
        #img.resize(width=80, height=100)
        img.im_feeling_lucky()
        thumbnail = img.execute_transforms(output_encoding=images.JPEG)
         
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(thumbnail)
              
        #self.response.out.write(template.render("info.html", {
        #'file_info': file_info,
        #'logout_url': users.create_logout_url('/'),
        # }))
class RotateHandler(BaseHandler):
    def get(self, file_id):
       # file_info = FileInfo.get_by_id(long(file_id))
        if not file_id:
            self.error(404)
            return
        file_info = FileInfo.get_by_id(long(file_id))
        if not file_info or not file_info.blob:
            self.error(404)
            return
        img = images.Image(blob_key=file_info.blob)
        #img.resize(width=80, height=100)
        #img.im_feeling_lucky()
        img.rotate(90);
       
        thumbnail = img.execute_transforms()
        #file_info.blob = thumbnail.decode('utf-8')
        file_info.put
        self.redirect("/files/all")
        
class FlipHandler(BaseHandler):
    def get(self, file_id):
       # file_info = FileInfo.get_by_id(long(file_id))
        if not file_id:
            self.error(404)
            return
        file_info = FileInfo.get_by_id(long(file_id))
        if not file_info or not file_info.blob:
            self.error(404)
            return
        img = images.Image(blob_key=file_info.blob)
        #img.resize(width=80, height=100)
        #img.im_feeling_lucky()
        img.rotate(90);
        thumbnail = img.execute_transforms()
      #  file_info.blob = img
        self.redirect("/files/all")
        
class FileDisplayHandler(BaseHandler):
    def get(self):
        #file_info = db.GqlQuery('select * from FileInfo')
        file_info = db.GqlQuery('select * from FileInfo')
            
        if not file_info:
            self.error(404)
            return
       
        values = {
            'file_info':file_info,
            'logout_url': users.create_logout_url('/')
        }
        self.response.out.write(
            template.render("display.html", values
        ))

     
# [END image_handler]   
class FileDownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, file_id):
        file_info = FileInfo.get_by_id(long(file_id))
        if not file_info or not file_info.blob:
            self.error(404)
            return
        #zf = zipfile.ZipFile("%d.zip" % (long(file_id)), "w")
        self.send_blob(file_info.blob, save_as=True)


app = webapp2.WSGIApplication([
   ('/', FileUploadFormHandler),
    ('/upload', FileUploadHandler),
    ('/file/([0-9]+)', FileInfoHandler),
    ('/file/([0-9]+)/download', FileDownloadHandler),
     ('/files/all', FileDisplayHandler),
     ('/rotate/([0-9]+)', RotateHandler),
     ('/flip/([0-9]+)', FlipHandler),
], debug=True)
# [END all]
