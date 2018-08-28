#!/usr/bin/env python
from __future__ import print_function

import re
import datetime
import os
import sys
import requests
from requests.auth import HTTPBasicAuth
import qquery.query
import json

'''
This worker queries data products from unavco and submits them as a download job
'''

# Global constants
#url = "http://www.unavco.org/data/imaging/sar/data-access-methods/SarArchive/SarScene?"
url = "https://www.unavco.org/SarArchive/SarScene?"
#lreg= re.compile('"downloadUrl":"(.*?)"')
#fnreg = re.compile('.*/(.*?)\.tar\.gz')
dtreg = re.compile('CSK.*?_(\d{4})(\d{2})(\d{2})')

class unavco(qquery.query.AbstractQuery):
    '''
    UNAVCO query implementer
    '''
    def query(self,start,end,aoi,mapping="CSK_RAW"):
        '''
        Performs the actual query, and returns a list of (title, url) tuples
        @param start - start time stamp
        @param end - end time stamp
        @param aoi - area of interest
        @return: list of (title, url) pairs
        '''
        if mapping=="CSK_RAW":
            session = requests.session()
            # Build the Query
            qur = self.buildQuery(start,end,'slc',aoi['location']['coordinates'])
            return self.listAll(session,qur)
        else:
            return []
    
    @staticmethod   
    def getDataDateFromTitle(title):
        '''
        Returns the date typle (YYYY,MM,DD) give the name/title of the product
        @param title - title of the product
        @return: (YYYY,MM,DD) tuple
        '''
        match = dtreg.search(title)
        if match:
            return (match.group(1),match.group(2),match.group(3))
        return ("0000","00","00")

    @staticmethod
    def getFileType():
        '''
        What filetype does this download
        '''
        return "tgz"

    @classmethod
    def getSupportedType(clazz):
        '''
        Returns the name of the supported type for queries
        @return: type supported by this class
        '''
        return "unavco" 
        
    @staticmethod
    def buildQuery(start,end,type,bounds):
        '''
        Builds a query for the system
        @param start - start time in 
        @param end - end time in "NOW" format
        @param type - type in "slc" format
        @param bounds - bounds to query
        @return query for talking to the system
        '''
        bounds = bounds[0]
        ply = ",".join([" ".join([str(dig) for dig in point]) for point in bounds])
        q=url+"intersectsWith=polygon (("+ply+"))"
        # note that start dateime cannot include time. format: YYYY-MM-DD, time from 00h00m00s to 23h59m59.9s is implied
        # convert datetime, stripping any Z if it's appended
        start = datetime.datetime.strftime(datetime.datetime.strptime(start.rstrip('Z'),'%Y-%m-%dT%H:%M:%S%f'), '%Y-%m-%d')
        end = datetime.datetime.strftime(datetime.datetime.strptime(end.rstrip('Z'),'%Y-%m-%dT%H:%M:%S%f'), '%Y-%m-%d')
        q+="&start="+start+"&end="+end
        #q+="&processingType="+type.upper()
        #q+="&collectionname=Supersites"
        #q+="&collectionName=Supersites CSK Hawaii"
        q+="&platform=COSMO-SKYMED-1,COSMO-SKYMED-2"
        return q
        
    #Non-required helpers
    @staticmethod
    def listAll(session,query):
        '''
        Lists the server for all products matching a query. 
        NOTE: this function also updates the global JSON querytime persistence file
        @param session - session to use for listing
        @param query - query to use to list products
        @return list of (title,link) tuples
        '''
        print("Listing: "+query)
        response = session.get(query)
        print(response)
        if response.status_code != 200:
            print("Error: %s\n%s" % (response.status_code,response.text))
            raise QueryBadResponseException("Bad status")
        #parse the json for names and urls
        json_data = json.loads(response.text)
        found = []
        for item in json_data['resultList']:
            link = item['downloadUrl']
            if link.endswith('tar.gz'):
                filename, extension = os.path.splitext(os.path.basename(link))
                fn, ext = os.path.splitext(filename)
                found.append((fn, link))
        return found
