#! -*- coding: utf-8 -*-

##    Description    Flame Manage class
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
import tarfile
import json
import util.utils as utils

def action_new (model):
    ''' create a new model tree, using the given name. This creates the development version "dev", copying inside default child classes '''

    if not model:
        return False, 'empty model label'

    ndir = utils.model_tree_path(model)
    
    # check if there is already a tree for this endpoint
    if os.path.isdir (ndir):
        return False, 'This endpoint already exists'
    try:
        os.mkdir (ndir)
    except:
        return False,'unable to create directory : '+ndir

    ndir+='/dev'
    try:
        os.mkdir (ndir)
    except:
        return False,'unable to create directory '+ndir

    try:
        wkd = os.path.dirname(os.path.abspath(__file__))
        children_names = ['apply','idata','odata','learn']
        for cname in children_names:
            shutil.copy(wkd+'/children/'+cname+'_child.py',ndir+'/'+cname+'_child.py')
        shutil.copy(wkd+'/children/parameters.yaml',ndir)
    except:
        return False,'unable to copy children classes at '+ndir

    return True,'new endpoint '+model+' created'


def action_kill (model):
    ''' removes the model tree described by the argument '''

    if not model:
        return False, 'empty model label'

    ndir = utils.model_tree_path(model)
    
    if not os.path.isdir (ndir):
        return False, 'model not found'

    shutil.rmtree(ndir, ignore_errors=True)

    return True, 'model '+model+' removed'


def action_publish (model):
    ''' clone the development "dev" version as a new model version, assigning a sequential version number '''

    if not model:
        return False, 'empty model label'
    
    bdir = utils.model_tree_path(model)

    if not os.path.isdir(bdir):
        return False, 'model not found'

    v = None
    try:
        v = [int(x[-6:]) for x in os.listdir (bdir) if x.startswith("ver")]
    except:
        pass

    if not v:
        max_version = 0
    else:
        max_version = max(v)

    new_dir = bdir+'/ver%0.6d'%(max_version+1)

    if os.path.isdir(new_dir):
        return False, 'version already exists'

    shutil.copytree(bdir+'/dev', new_dir)
    
    return True, 'development version published as version '+str(max_version+1)


def action_remove (model, version):
    ''' Remove the version indicated as argument from the model tree indicated as argument '''

    if not model:
        return False, 'empty model label'

    if version == 0:
        return False, 'development version cannot be removed'

    rdir = utils.model_path(model, version)
    if not os.path.isdir(rdir):
        return False, 'version not found'

    shutil.rmtree(rdir, ignore_errors=True)

    return True, 'version '+str(version)+' of model '+model+' removed'


def action_list (*model):   # * makes the parameter optional
    ''' Lists available models (if no argument is provided) and model versions (if "model" is provided as argument) '''

    # TODO: if no argument is provided, also list all models
    if not model:
        rdir = utils.model_repository_path()
        print (rdir)
        
        num_models=0
        for x in os.listdir (rdir):
            num_models+=1
            print (x)

        return True, str(num_models)+' models found in the repository'

    bdir = utils.model_tree_path (model)

    num_versions = 0
    for x in os.listdir (bdir):
        if x.startswith("ver"):
            num_versions+=1
            print (model,':',x)

    return True, 'model '+model+' has '+str(num_versions)+' published versions'


def action_import (model):
    ''' Creates a new model tree from a tarbal file with the name "model.tgz" '''
    
    if not model:
        return False, 'empty model label'

    bdir = utils.model_tree_path (model)
    
    if os.path.isdir (bdir) :
        return False, 'endpoint already exists'

    importfile = os.path.abspath(model+'.tgz')
    
    if not os.path.isfile (importfile):
        return False, 'importing package '+importfile+' not found'
    
    try:
        os.mkdir(bdir)
        os.chdir(bdir)
    except:
        return False, 'error creating directory '+bdir
        
    with tarfile.open(importfile,'r:gz') as tar:
        tar.extractall()
    
    return True,'endpoint '+model+' imported OK' +bdir


def action_export (model):
    ''' Exports the whole model tree indicated in the argument as a single tarball file with the same name '''

    if not model:
        return False, 'empty model label'
        
    current_path = os.getcwd ()
    exportfile = current_path+'/'+model+'.tgz'
    
    bdir = utils.model_tree_path (model)

    if not os.path.isdir(bdir):
        return False, 'endpoint directory not found'

    os.chdir(bdir)
    
    itemend = os.listdir()
    itemend.sort()

    with tarfile.open(exportfile, 'w:gz') as tar:
        for iversion in itemend:
            if not os.path.isdir(iversion):
                continue
            tar.add(iversion)
    
    os.chdir(current_path)

    return True,'endpoint '+model+' exported as '+model+'.tgz'


## TODO: implement refactoring, starting with simple methods
def action_refactoring (file):
    ''' NOT IMPLEMENTED, call to import externally generated models (eg. in KNIME or R) '''

    print ('refactoring')

    return True, 'OK'


def action_dir ():
    ''' Returns a JSON with the list of models and versions '''

    results = []
    rdir = utils.model_repository_path()

    for imodel in os.listdir (rdir):

        # versions = ['dev']
        versions = [{'text':'dev'}]

        for iversion in os.listdir (utils.model_tree_path(imodel)):
            if iversion.startswith('ver'):
                # versions.append (iversion)
                versions.append( {'text':iversion})
                
        # results.append ((imodel,versions))
        results.append ( {'text':imodel, 'nodes': versions})

    print (json.dumps(results))
    
    return True, json.dumps(results)