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

# Read token from settings file or create one

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

from lxml import etree as ET

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
        def wrapped_f(ServiceObj,**kwargs):
            """http://docs.python-requests.org/en/latest/user/quickstart/
            """
            URL=ServiceObj.baseURL+ServiceObj.servicename
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
            return f(r)
        return wrapped_f

class _ExposedResource(object):
    """Abstract base object with common properties inheritet by webservice resources"""
    def __init__(self,baseURL=baseURL,token=None):
        if verbose:
            print "Abstract init!!!"
            
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
    def __init__(self,baseURL=baseURL,token=None):
        super(ArchiveFiles,self).__init__(baseURL=baseURL,token=token)
        self.servicename='archivefiles'
        
    @ServiceMethod(required=['station','token'])
    def getList(Data):
        """r= f.getList(station='ENMEF.RA')"""
        return Data
        
    @ServiceMethod(required=['filename','token'])
    def getFile(Data):
        return Data

class Stations(_ExposedResource):
    """Interface to the stations service"""
    def __init__(self,baseURL=baseURL,token=None):
        super(Stations,self).__init__(baseURL=baseURL,token=token)
        self.servicename='stations'
        
    @ServiceMethod(required=['token'])
    def getTree(Data):
        """r= f.getList()"""
        return Data
        
    def printTree(self,showHidden="false"):
        nodeTree=self.getTree(showHidden=showHidden)
        for observatoryRoot in nodeTree.json():
            self._printNode(observatoryRoot)
            print " "
            
    def createMindmap(self,showHidden="false"):
        nodeId=0
        nodeTree=self.getTree(showHidden=showHidden)
        map=ET.Element('map')
        rootNode=ET.SubElement(map,'node',attrib={'TEXT':'Root','ID':'ID_'+str(nodeId)})
        for observatoryRoot in nodeTree.json:
            self._addNode(observatoryRoot,rootNode,nodeId)
        return map
            
    def _addNode(self,jsonNode,mapParent,nodeId):
        nodeId += 1
        newNode=ET.SubElement(mapParent,'node',attrib={'TEXT':jsonNode['name'],'ID':'ID_'+str(nodeId)})
        if not jsonNode.has_key('stationCode'):
            jsonNode['stationCode']=None
        ET.SubElement(newNode,'attribute',{'NAME':'code', 'VALUE': str(jsonNode['stationCode'])})
        if 0: #jsonNode.has_key('description'):
            desc=ET.SubElement(newNode,'richcontent',{'TYPE':"DETAILS"})
            desc.text=jsonNode['description']
        childNodes=jsonNode['els'] #.sort(key='desciption')
        for childNode in childNodes: 
            self._addNode(childNode,newNode,nodeId)
            
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
        
# Configureation files:
# http://stackoverflow.com/questions/7567642/where-to-put-a-configuration-file-in-python

# Python docsting guide:
# http://www.python.org/dev/peps/pep-0257/

# Python sytle guide:
# http://www.python.org/dev/peps/pep-0008/
# http://google-styleguide.googlecode.com/svn/trunk/pyguide.html

if __name__ == "__main__":
    pass