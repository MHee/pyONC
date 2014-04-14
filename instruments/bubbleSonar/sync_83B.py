from pyONC.webservices import oncws # See also http://wiki.neptunecanada.ca/display/help/API
import os

f=oncws.ArchiveFiles()

updatedFiles=f.syncDirectory(syncDir=r'.\SonarData',
                    station='NC89',deviceCategory='MBROTARYSONAR',
                    dateFrom='2010-05-22T18:31:51.000Z',
                    dateTo='2010-05-23T22:31:51.000Z',
                    dataProductFormatId=66)

for updatedFile in updatedFiles:
    print('processing... %s' % updatedFile)
    result=os.system(r'DeltaT_Azimuth_v1_04_34.exe %s /b' % updatedFile)
    if not result == 0:
        print('Ooops, somethings wrong with %' % updatedFile)
    

#
# Check what kind of data products there are in AD...
#

#if 0:
#    lf=f.getList(station='NC89',deviceCategory='MBROTARYSONAR',returnOptions='all')
#    dataProductFormatIds=list()
#    for aFile in lf:
#        dataProductFormatId=aFile['dataProductFormatId']
#        if not dataProductFormatId in dataProductFormatIds:
#            dataProductFormatIds.append(dataProductFormatId)
#            print aFile
#    
#    print(dataProductFormatIds)



