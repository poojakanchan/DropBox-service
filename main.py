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
import jinja2
import os
from base64 import b64encode
import time
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class FileInfo(db.Model):
    blob = blobstore.BlobReferenceProperty(required=True)
    uploaded_by = db.UserProperty(required=True)
    uploaded_at = db.DateTimeProperty(required=True, auto_now_add=True)
    type = db.StringProperty()
    url = db.StringProperty()
    #image= db.BlobProperty(required=True)

class BaseHandler(webapp.RequestHandler):
    def render_template(self, file, template_args):
        path = os.path.join(os.path.dirname(__file__), "templates", file)
        self.response.out.write(template.render(path, template_args))

  
class HomeHandler(BaseHandler):   
    def get(self):
        user = users.get_current_user()

        if user:
            url = users.create_logout_url("/")
            self.redirect("/userhome")
        else:
            url = users.create_login_url("/")
            self.response.out.write(template.render("home.html", {
            'login_url': url,
            }))

class FileUploadFormHandler(BaseHandler):
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
        type = self.request.get_all('type')[0]
     #   url=images.get_serving_url(blob_info.key(), size=None, crop=False, secure_url=None, filename=None, rpc=None)
        file_info = FileInfo(
                         blob=blob_info.key(),
                         uploaded_by=users.get_current_user(),
                         type=type,
                         url="/transform/?photo_key=%s" % (blob_info.key()))
                        # image=thumbnail)
        db.put(file_info)
        
        #self.redirect("/file/%d" % (file_info.key().id(),))
        self.redirect('/')
        
        #self.redirect("/file/%s" % (blob_info.key()))
class VideoInfoHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, file_id):
       # file_info = FileInfo.get_by_id(long(file_id))
        if not file_id:
            self.error(404)
            return
        file_info = FileInfo.get_by_id(long(file_id))
        if not file_info or not file_info.blob:
            self.error(404)
            return
        self.response.headers['Content-Type']= str(file_info.blob.content_type)
        self.send_blob(file_info.blob, save_as=True)
                 
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
        #self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.headers['Content-Type'] = str(file_info.blob.content_type)
        self.response.out.write(thumbnail)
        #self.response.out.write(template.render("info.html", {
        #'file_info': file_info,
        #'logout_url': users.create_logout_url('/'),
        # }))
class TransformHandler1(BaseHandler):
   def get(self, photo_key, width_new=None, rotate=None):
#        if not blobstore.get(photo_key):
#            self.error(404)
#        else:
            photo_key = self.request.GET['photo_key']
            img = images.Image(blob_key=photo_key)
            
            if 'width_new' in  self.request.GET:
                if width_new is not None:
                    width_new = int(self.request.GET['width_new'])
                    img.resize(width=width_new, height=width_new)
            else:
                img.resize(width=500, height=500)
                
            if 'rotate' in self.request.GET and rotate is not None:
                img.rotate(int(self.request.GET['rotate']))
            img.im_feeling_lucky()
            thumbnail = img.execute_transforms(output_encoding=images.JPEG)
            imageEnc = b64encode(thumbnail)
#            self.response.headers['Content-Type'] = 'image/jpeg'
#            self.response.out.write(thumbnail)            
           
            self.response.write("""
<img src="data:;base64,{0}"/>
<p>New width is {1}</p>

<form action="/transform/?" method="get">
    <input type="hidden" name="photo_key" value="{2}">
    <p>Resize: <input type="text" name="width_new"></p>
    <p>Rotate:<input type="text" name="rotate"></p>
    <input type="submit" name="submit" value="Transform">
</form>
            """.format(imageEnc, width_new, photo_key))
   
class TransformHandler(BaseHandler):
    def get(self, photo_key):
#        if not blobstore.get(photo_key):
#            self.error(404)
#        else:
        photo_key = self.request.GET['photo_key']
            
        img = images.Image(blob_key=photo_key)
            
        width = 500
            
        img.resize(width=width, height=width)
                
          
        thumbnail = img.execute_transforms(output_encoding=images.JPEG)
        imageEnc = b64encode(thumbnail)
#            self.response.headers['Content-Type'] = 'image/jpeg'
#            self.response.out.write(thumbnail)   
        time.sleep(0.5)            
        self.response.out.write(template.render("tranform.html", {
            'image': imageEnc,
            'photo_key':photo_key,  
        }))
            
class ResizeHandler(BaseHandler):
    def get(self, photo_key):
        photo_key = self.request.GET['photo_key']
      
        if not blobstore.get(photo_key):
            self.error(404)
            return
#        else:
            
        img = images.Image(blob_key=photo_key)
            
        width = 500
           
        if 'width_new' in self.request.GET and self.request.GET['width_new'] !='':
                width = int(self.request.GET['width_new'])
            
        img.resize(width=width, height=width)    
        thumbnail = img.execute_transforms(output_encoding=images.JPEG)
        imageEnc = b64encode(thumbnail)
#            self.response.headers['Content-Type'] = 'image/jpeg'
#            self.response.out.write(thumbnail)   
        time.sleep(0.5)            
        self.response.out.write(template.render("tranform.html", {
            'image': imageEnc,
            'photo_key':photo_key,
            }))
            
            
class RotateHandler(BaseHandler):
    def get(self, photo_key):
        
        photo_key = self.request.GET['photo_key']
        if not blobstore.get(photo_key):
            self.error(404)
            return
#        else:
       
            
        img = images.Image(blob_key=photo_key)
            
            
            
        img.resize(width=500, height=500)
        rotate =0 
        if 'rotate' in self.request.GET and self.request.GET['rotate'] != '':
            rotate = int(self.request.GET['rotate'])
            
        if rotate !=0 :
            img.rotate(rotate)
        thumbnail = img.execute_transforms(output_encoding=images.JPEG)
        imageEnc = b64encode(thumbnail)
#            self.response.headers['Content-Type'] = 'image/jpeg'
#            self.response.out.write(thumbnail)   
        time.sleep(0.5)            
        self.response.out.write(template.render("tranform.html", {
            'image': imageEnc,
            'photo_key':photo_key,
            }))
 
     
class HoriFlipHandler(BaseHandler):
    def get(self, photo_key):
        
        photo_key = self.request.GET['photo_key']
        if not blobstore.get(photo_key):
            self.error(404)
            return
        img = images.Image(blob_key=photo_key)
        img.resize(width=500, height=500)
        img.horizontal_flip()
        thumbnail = img.execute_transforms(output_encoding=images.JPEG)
        imageEnc = b64encode(thumbnail)
#            self.response.headers['Content-Type'] = 'image/jpeg'
#            self.response.out.write(thumbnail)   
        time.sleep(0.5)            
        self.response.out.write(template.render("tranform.html", {
            'image': imageEnc,
            'photo_key':photo_key,
            }))
      
      
class VertFlipHandler(BaseHandler):
    def get(self, photo_key):
        
        photo_key = self.request.GET['photo_key']
        if not blobstore.get(photo_key):
            self.error(404)
            return
        img = images.Image(blob_key=photo_key)
        img.resize(width=500, height=500)
        img.vertical_flip()
        thumbnail = img.execute_transforms(output_encoding=images.JPEG)
        imageEnc = b64encode(thumbnail)
#            self.response.headers['Content-Type'] = 'image/jpeg'
#            self.response.out.write(thumbnail)   
        time.sleep(0.5)            
        self.response.out.write(template.render("tranform.html", {
            'image': imageEnc,
            'photo_key':photo_key,
            }))
  
      
class EnhanceHandler(BaseHandler):
    def get(self, photo_key):
        
        photo_key = self.request.GET['photo_key']
        if not blobstore.get(photo_key):
            self.error(404)
            return
        img = images.Image(blob_key=photo_key)
        img.resize(width=500, height=500)
        img.im_feeling_lucky()
        thumbnail = img.execute_transforms(output_encoding=images.JPEG)
        imageEnc = b64encode(thumbnail)
#            self.response.headers['Content-Type'] = 'image/jpeg'
#            self.response.out.write(thumbnail)   
        time.sleep(0.5)            
        self.response.out.write(template.render("tranform.html", {
            'image': imageEnc,
            'photo_key':photo_key,
            }))  
        
class FileDisplayHandler(BaseHandler):
    def get(self):
        #file_info = db.GqlQuery('select * from FileInfo')
        file_info = db.GqlQuery("select * from FileInfo where type='image'")
            
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
        
class VideoDisplayHandler(BaseHandler):
    def get(self):
        #file_info = db.GqlQuery('select * from FileInfo')
        file_info = db.GqlQuery("select * from FileInfo where type='video'")
            
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
        
class AudioDisplayHandler(BaseHandler):
    def get(self):
        #file_info = db.GqlQuery('select * from FileInfo')
        file_info = db.GqlQuery("select * from FileInfo where type='audio'")
            
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
        
# [START image_handler]
class Image(webapp2.RequestHandler):
    def get(self, file_key):
        img = images.Image(blob_key=file_key)
        #img.resize(width=80, height=100)
        img.im_feeling_lucky()
        thumbnail = img.execute_transforms(output_encoding=images.JPEG)
         
        self.response.headers['Content-Type'] = 'image/jpeg'
        self.response.out.write(thumbnail)
       
# [END image_handler]   
class FileDownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, file_id):
        file_info = FileInfo.get_by_id(long(file_id))
        if not file_info or not file_info.blob:
            self.error(404)
            return
        #zf = zipfile.ZipFile("%d.zip" % (long(file_id)), "w")
        self.send_blob(file_info.blob, save_as=True)
        
class DeleteHandler(webapp2.RequestHandler):
    def get(self, file_id):
        file_info = FileInfo.get_by_id(long(file_id))
        if not file_info or not file_info.blob:
            self.error(404)
            return
        ftype = file_info.type 
        blobstore.delete([file_info.blob])
        db.delete(file_info)
        time.sleep(0.5)
        if ftype == "image":
            self.redirect('/images/all')
        elif ftype== "video":
            self.redirect("/videos/all")
        else:
            self.redirect("/audios/all")
        #zf = zipfile.ZipFile("%d.zip" % (long(file_id)), "w")
 
app = webapp2.WSGIApplication([
   ('/userhome', FileUploadFormHandler),
   ('/', HomeHandler),
    ('/upload', FileUploadHandler),
    ('/file/([0-9]+)', FileInfoHandler),
    ('/video/([0-9]+)', VideoInfoHandler),
    ('/file/([0-9]+)/download', FileDownloadHandler),
     ('/images/all', FileDisplayHandler),
     ('/audios/all', AudioDisplayHandler),
     ('/videos/all', VideoDisplayHandler),
     ('/img/([^/]+)?', Image),
     ('/transform/([^/]+)?', TransformHandler),
     ('/rotate/([^/]+)?', RotateHandler),
     ('/resize/([^/]+)?', ResizeHandler),
     ('/horiflip/([^/]+)?', HoriFlipHandler),
     ('/vertflip/([^/]+)?', VertFlipHandler),
     ('/enhance/([^/]+)?', EnhanceHandler),
     ('/delete/([0-9]+)', DeleteHandler),
     
], debug=True)
# [END all]
