#! -*- coding: utf-8 -*-

##    Description    Flame web-service
##
##    Authors:       Manuel Pastor (manuel.pastor@upf.edu)
##
##    Copyright 2018 Manuel Pastor
##
##    This file is part of Flame
##
##    Flame is free software: you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation version 3.
##
##    Flame is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License
##    along with Flame. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import shutil
import tempfile
import json
import re
import cherrypy
from cherrypy.lib.static import serve_file

# THIS PATH MUST BE DEFINED IN DEVELOPMENT ENVIRONMENTS WHERE FLAME
# WAS NOT INSTALLED AS A PACKAGE
sys.path.append('C:/Users/mpastor/Documents/soft/flame/flame')

import manage
import context
import util.utils as utils

#TODO: Validate names in server to prevent curl 'attacks' like curl -d "model=@@@@@@@@" -X POST http://0.0.0.0:8081/addModel
#The user cant addModels with rare characters

# # TEMP: only to allow EBI model to run
# def sensitivity(y_true, y_pred):
#     tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
#     return(tp / (tp+fn))

# def specificity(y_true, y_pred):
#     tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
#     return(tn / (tn+fp))

def numeric_version (text_version):
    version=0
    if text_version[:3]=='ver': 
        version = int(text_version[-6:]) ## get the numbers
    return version


class FlamePredict(object):
    @cherrypy.expose
    def index(self):
        return open('./templates/index.html')

    @cherrypy.expose
    def upload(self):

        filename = os.path.basename(cherrypy.request.headers['x-filename'])
        temp_dir = os.path.basename(cherrypy.request.headers['temp-dir'])

        if temp_dir != '':
            path = os.path.join(tempfile.gettempdir(),temp_dir)
            os.mkdir (path)
        else:
            path = tempfile.gettempdir()
            # path = './'
        
        destination = os.path.join(path, filename)
        
        with open(destination, 'wb') as f:
            shutil.copyfileobj(cherrypy.request.body, f)

@cherrypy.expose
class FlamePredictWS(object):
    @cherrypy.tools.accept(media='text/plain')

    def POST(self, ifile, model, version, temp_dir):
        
        ifile = os.path.join(tempfile.gettempdir(),temp_dir,ifile)
        # if version[:3]=='ver': 
        #     version = int(version[-6:]) ## get the numbers

        # version = utils.intver(version)

        # TODO: for now, only working for plain models (no external input sources)          
        model = {'endpoint' : model,
                 'version' : numeric_version(version),
                 'infile' : ifile}

        success, results = context.predict_cmd(model)
        
        return results

@cherrypy.expose
class FlameAddModel(object):
    @cherrypy.tools.accept(media='text/plain')
    def POST(self, model):
        if re.match('^[\w-]+$', model):
            result = manage.action_new(model)
            return str(result)
        else:
            return "Non alphanumeric character detected. Aborting operation"

@cherrypy.expose
class FlameExportModel(object):
    @cherrypy.tools.accept(media='text/plain')
    def GET(self, model):
        result = manage.action_export(model)
        return "true"

@cherrypy.expose
class Download(object):
    @cherrypy.tools.accept(media='text/plain')
    def GET(self, model):
        return cherrypy.lib.static.serve_file(os.path.abspath(model+".tgz"), "application/gzip", "attachment")

@cherrypy.expose
class FlameDeleteFamily(object):
    @cherrypy.tools.accept(media='text/plain')
    def POST(self, model):
        result = manage.action_kill(model)
        return result

@cherrypy.expose
class FlameDeleteVersion(object):
    @cherrypy.tools.accept(media='text/plain')
    def POST(self, model, version):
        # version = version.replace("ver", "")
        # version = version.lstrip( '0' )
        # result = manage.action_remove(model, int(version))
        result = manage.action_remove(model, numeric_version(version))
        return str(version)

@cherrypy.expose
class FlameCloneModel(object):
    @cherrypy.tools.accept(media='text/plain')
    def POST(self, model):
        result = manage.action_publish(model)
        return result

@cherrypy.expose
class FlameImportModel(object):
    @cherrypy.tools.accept(media='text/plain')
    def POST(self, model):
        model = os.path.join(tempfile.gettempdir(),model)
        # model = os.path.join('./',model)
        result = manage.action_import(model)
        return result

@cherrypy.expose
class FlameInfoWS(object):
    @cherrypy.tools.accept(media='text/plain')
    def POST(self):
        data = { "provider": utils.configuration['provider'],
                 "homepage": utils.configuration['homepage'],
                 "admin_name": utils.configuration['admin_name'],
                 "admin_email": utils.configuration['admin_email']
                }   
        return json.dumps(data)

@cherrypy.expose
class FlameModelInfo(object):
    @cherrypy.tools.accept(media='text/plain')
    def POST(self, model, version, output):
        # if version=="dev":
        #     version=0
        # else:
        #     version = version.replace("ver", "")
        #     version = version.lstrip( '0' )
        # version = utils.intver(version)
        result = manage.action_info(model, numeric_version(version), output)
        return result[1]

@cherrypy.expose
class FlameDirWS(object):
    @cherrypy.tools.accept(media='text/plain')
    def GET(self):

        success, results = manage.action_dir()

        if not success:
            return "no model found"
        return results

if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': False,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/info': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')]
        },
        '/dir': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')]
        },
        '/predict': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')]
        },
        '/download': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')]
        },
        '/addModel': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')]
        },
        '/exportModel': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')]
        },
        '/deleteFamily': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')]
        },
        '/deleteVersion': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')]
        },
        '/importModel': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')]
        },
        '/cloneModel': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')]
        },
        '/modelInfo': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'text/plain')]
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './public',
        },
        'global' : {
            'server.socket_host' : '0.0.0.0',
            'server.socket_port' : 8081,
            'server.thread_pool' : 8,
        }
    }

    webapp = FlamePredict()
    webapp.info = FlameInfoWS()
    webapp.dir = FlameDirWS()
    webapp.predict = FlamePredictWS()
    webapp.addModel = FlameAddModel()
    webapp.deleteFamily = FlameDeleteFamily()
    webapp.deleteVersion = FlameDeleteVersion()
    webapp.cloneModel = FlameCloneModel()
    webapp.importModel = FlameImportModel()
    webapp.modelInfo = FlameModelInfo()
    webapp.exportModel = FlameExportModel()
    webapp.download = Download()
    cherrypy.quickstart(webapp, '/', conf)