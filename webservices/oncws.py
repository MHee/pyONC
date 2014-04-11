"""
.. module:: oncws
    :platform: Unix, Windows
    :synopsis: Interface to DMAS/ONC webservices

    Webservice documentation at http://internal.neptunecanada.ca/display/DS/file

.. moduleauthor: Martin Heesemann <mheesema@uvic.ca>
"""

verbose=False

#import webbrowser   # open browser window for token discovery
import requests     # external requirement: make HTTP easy
import os
import json
from functools import wraps # Make sure decorated functions have updated help
#
# Read token from settings file or create one
#
iniFile=os.path.expanduser(os.path.join('~','.onc.rc'))
if os.path.isfile(iniFile):
    # Read settings from users home directory
    with open(iniFile) as json_file:
        settings = json.load(json_file)
else:
    # Create settings
    settings={'version':0.1,'format':'JSON','profiles':{}}
    settings['profiles']['default']={'baseURL':'http://dmas.uvic.ca/api/'}
    settings['profiles']['qaqc']={'baseURL':'http://qaweb2.neptune.uvic.ca/api/'}
    settings['profiles']['default']['token']=raw_input('Please enter your token:')
    with open(iniFile, 'w') as outfile:
        json.dump(settings, outfile,indent=4,sort_keys=True)

token=settings['profiles']['default']['token']     
baseURL=settings['profiles']['default']['baseURL']

#
# HTTP Server status codes
#
status_msgs = {
    400: 'Bad request error. Check if the mandatory parameters are provided.',
    401: 'Unauthorized error. Check if the token is valid.',
    415: 'Unsupported error. Check if the parameters are given in the right format.',
    501: 'Not implemented error. Check if the given method is valid.'
} #500 internal server error

class ServiceMethod(object):
    """Decorator to map class methods to oncws methods.
    
    Python decoration tutorial:
    http://www.artima.com/weblogs/viewpost.jsp?thread=240845
    
    """
    def __init__(self, **kwargs):
        if verbose:
            print "ServiceMethod.__init__"
            print kwargs
        self.decorator_kwargs = kwargs
    
    def __call__(self, f):
        if verbose:
            print "ServiceMethod.__call__"
            print f.__name__
        
        @wraps(f)
        def wrapped_f(ServiceObj,**kwargs):
            """http://docs.python-requests.org/en/latest/user/quickstart/
            """
            URL=ServiceObj.baseURL+ServiceObj.servicename
            
            # Check for keyword arguments that should not be passed on to 
            # ONC webservice
            if 'returnFormat' in kwargs.keys():
                # Used return format specifically specified by the user
                returnFormat=kwargs['returnFormat'].lower()
                kwargs.pop('returnFormat')
            elif 'returnFormat' in self.decorator_kwargs.keys():
                # Use method specific return format default, e.g. "getFile"
                returnFormat=self.decorator_kwargs['returnFormat'].lower()
            else:
                # Use default that is set when service was initiated
                returnFormat=ServiceObj.returnFormat #'json'
                
            params = kwargs
            for pkey in params.keys():
                # remove unused parameters
                if params[pkey] == None:
                    params.pop(pkey)
            params['method'] = f.__name__
            params['token'] = ServiceObj.token
            
            if verbose:
                print URL
                print params
            r=requests.get(URL, params=params)
            if not r.ok:
                try:
                    print '%d: %s' % (r.status_code, status_msgs[r.status_code])
                except:
                    print '%d is not an expected status code...' % r.status_code
            if verbose:
                print r
                print "%s.%s wrapped" % (ServiceObj.__class__, f.__name__)
                print self.decorator_kwargs
                print r.url
                print ServiceObj.baseURL,ServiceObj.servicename, f.__name__,kwargs
                print kwargs
            
            if returnFormat == 'json':
                #if (f.__name__=='getFile' and ServiceObj.servicename == 'archivefiles'):
                #    return f(r.content)    
                #else:
                return f(r.json())
            elif returnFormat == 'content':
                return f(r.content)
            elif returnFormat == 'response':
                return f(r)
            else:
                print('Unknown return format %s' % returnFormat)
                return None
                
        return wrapped_f

class _ExposedResource(object):
    """Abstract base object with common properties inheritet by webservice resources"""
    def __init__(self,baseURL=baseURL,token=None,returnFormat=None):
        if verbose:
            print "Abstract init!!!"
        if returnFormat:
            self.returnFormat=returnFormat.lower()
        else:
           self.returnFormat='json'
            
        self.baseURL=baseURL
        if token:
            self.token=token
        else:
            self.getToken()
                    
    def getToken(self):
        """If the user access token is unkown help user to find it"""
        #webbrowser('https://dmas.uvic.ca/Profile')
        #print "Enter token:"
        self.token=token
        

        
class ArchiveFiles(_ExposedResource):
    """Interface to the file service"""
    def __init__(self,baseURL=baseURL,token=None,returnFormat='json'):
        super(ArchiveFiles,self).__init__(baseURL=baseURL,token=token,returnFormat=returnFormat)
        self.servicename='archivefiles'
        
    @ServiceMethod(required=['station','token'])
    def getList(Data):
        """l=f.getList(station='NC89', deviceCategory='MBROTARYSONAR')"""
        return Data
        
    @ServiceMethod(required=['filename','token'],returnFormat = 'content')
    def getFile(Data):
        return Data
        
    def syncDirectory(self,syncDir='.', station=None, deviceCategory=None,
                        dateFrom=None,dateTo=None,
                        dateArchivedFrom=None,dateArchivedTo=None,
                        dataProductFormatId=None):
        """Syncs a directory of files with files available in ONC archive."""
        fileList=self.getList(station=station,deviceCategory=deviceCategory,
                                dateFrom=dateFrom,dateTo=dateTo,
                                dateArchivedFrom=dateArchivedFrom,
                                dateArchivedTo=dateArchivedTo,
                                returnOptions='all')
        syncedList=list()
        for aFile in fileList:
            if dataProductFormatId and \
                    not aFile['dataProductFormatId'] == dataProductFormatId:
                continue

            fileName=os.path.join(syncDir,aFile['filename'])
            if not os.path.isfile(fileName):
                with open(fileName, 'wb') as outFile:
                    print('Writing %s (%f MB)' % 
                        (fileName,aFile['uncompressedFileSize']/(1024.*1024.)))
                         
                    outFile.write(self.getFile(filename=aFile['filename']))
                    syncedList.append(fileName)
        return syncedList

    #f=oncws.ArchiveFiles()
    #l=f.syncDirectory(station='NC89',deviceCategory='MBROTARYSONAR',dateFrom='2010-05-22T18:31:51.000Z',dateTo='2010-05-23T18:31:51.000Z')

class Stations(_ExposedResource):
    """Interface to the stations service"""
    def __init__(self,baseURL=baseURL,token=None,returnFormat='json'):
        super(Stations,self).__init__(baseURL=baseURL,token=token,returnFormat=returnFormat)
        self.servicename='stations'
        
    @ServiceMethod(required=['token'])
    def getTree(Data):
        """r= f.getList()"""
        return Data
        
    def printTree(self,showHidden="false"):
        nodeTree=self.getTree(showHidden=showHidden,returnFormat='json')
        for observatoryRoot in nodeTree:
            self._printNode(observatoryRoot)
            print " "
                        
    def _printNode(self,node,path=''):
        #print "Node: ", node
        for key in ['name', 'stationCode', 'description', 'deviceCategories', 'els']:
            if not node.has_key(key):
                #print 'missing key: %s !!!!' % key
                node[key]=None
        path += '%s/' % node['name']
        #deviceCategories=node['deviceCategories'].sort()
        #print '%s\t%s\t%s\t%s' % (path, node['name'], node['stationCode'],', '.join(node['deviceCategories']))
        if 'JB' in node['deviceCategories']:
            print path,', '.join(node['deviceCategories'])
        childNodes=node['els'] #.sort(key='desciption')
        for childNode in childNodes: 
            self._printNode(childNode,path=path)

#
# Turn station tree into mindmap  
# (Works, but adds dependencies and should be seperate module)       
#                

# from lxml import etree as ET
    #def createMindmap(self,showHidden="false"):
    #    nodeId=0
    #    nodeTree=self.getTree(showHidden=showHidden)
    #    map=ET.Element('map')
    #    rootNode=ET.SubElement(map,'node',attrib={'TEXT':'Root','ID':'ID_'+str(nodeId)})
    #    for observatoryRoot in nodeTree.json:
    #        self._addNode(observatoryRoot,rootNode,nodeId)
    #    return map
    #        
    #def _addNode(self,jsonNode,mapParent,nodeId):
    #    nodeId += 1
    #    newNode=ET.SubElement(mapParent,'node',attrib={'TEXT':jsonNode['name'],'ID':'ID_'+str(nodeId)})
    #    if not jsonNode.has_key('stationCode'):
    #        jsonNode['stationCode']=None
    #    ET.SubElement(newNode,'attribute',{'NAME':'code', 'VALUE': str(jsonNode['stationCode'])})
    #    if 0: #jsonNode.has_key('description'):
    #        desc=ET.SubElement(newNode,'richcontent',{'TYPE':"DETAILS"})
    #        desc.text=jsonNode['description']
    #    childNodes=jsonNode['els'] #.sort(key='desciption')
    #    for childNode in childNodes: 
    #        self._addNode(childNode,newNode,nodeId)
    #                    
                                        
# Configureation files:
# http://stackoverflow.com/questions/7567642/where-to-put-a-configuration-file-in-python

# Python docsting guide:
# http://www.python.org/dev/peps/pep-0257/

# Python sytle guide:
# http://www.python.org/dev/peps/pep-0008/
# http://google-styleguide.googlecode.com/svn/trunk/pyguide.html

if __name__ == "__main__":
    pass