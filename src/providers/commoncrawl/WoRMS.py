from Provider import Provider
import logging
from bs4 import BeautifulSoup
from urlparse import urlparse, parse_qs
import json
import re


logging.basicConfig(format='%(asctime)s - %(name)s: [%(levelname)s] =======> %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class WoRMS(Provider):

    def __init__(self, _name, _domain, _cc_index):
        Provider.__init__(self, _name, _domain, _cc_index)


    def getMetaData(self, _html, _url):
        """

        Parameters
        ------------------
        _html: string
            The HTML page that was extracted from Common Crawls WARC file.

        _url: string
            The url for the webpage.


        Returns
        ------------------
        A tab separated string which contains the meta data that was extracted from the HTML.

        """

        soup                = BeautifulSoup(_html, 'html.parser')
        otherMetaData       = {}
        src                 = None
        license             = None
        version             = None
        imageURL            = None
        formatted           = []

        self.clearFields()
        self.provider       = self.name
        self.source         = 'commoncrawl'

        urlInfo             = soup.find('div', {'id': 'photogallery_share'})
        if urlInfo:
            foreignURL      = urlparse(urlInfo.attrs['data-url'])
            foreignID       = parse_qs(foreignURL.query)['pic'], urlInfo.attrs['data-url']

            if len(foreignID) > 1 and foreignID[0]:
                self.foreignIdentifier = foreignID[0][0]

            if foreignURL:
                self.foreignLandingURL = urlInfo.attrs['data-url']
            else:
                self.foreignLandingURL = _url


        if 'p=image' in _url:
            #if on the image details page
            imgInfo = soup.find('div', {'id': 'photogallery_resized_img'})
            if imgInfo:
                #verify the license
                licenseInfo = imgInfo.findChild('meta', {'itemprop': 'license'})
                if licenseInfo:
                    ccURL               = urlparse(licenseInfo.attrs['content'])
                    license, version    = self.getLicense(ccURL.netloc, ccURL.path, _url)


                if not license:
                    logger.warning('License not detected in url: {}'.format(_url))
                    return None


                self.license        = license
                self.licenseVersion = version


                #get the image details
                imgDetails = imgInfo.findChild('img')
                if imgDetails:
                    self.url        = imgDetails.attrs['src']
                    self.width      = imgDetails.attrs['width']
                    self.height     = imgDetails.attrs['height']
                    self.thumbnail  = self.url.replace('resized', 'thumbs')
                    self.title      = imgDetails.attrs['title'].strip()

                else:
                    logger.warning('Image not detected in url: {}'.format(_url))
                    return None


            #get the meta-data

            #title   = soup.find('div', {'class': 'photogallery_caption photogallery_title'})
            #if title:
                #self.title = title.text.strip()

            desc    = soup.find('span', {'class': 'photogallery_caption photogallery_descr'})
            if desc:
                descText = desc.findChild('span', {'class': 'photogallery_caption photogallery_text'})
                if descText and descText.text.strip():
                    otherMetaData['description'] = descText.text.strip()


            authorInfo = soup.find('span', {'class': 'photogallery_caption photogallery_author'})
            if authorInfo:
                author = authorInfo.findChild('a')

                if author:
                    self.creator    = author.text.strip()
                    self.creatorURL = author.attrs['href']

                else:
                    author = authorInfo.findChild('span', {'class': 'photogallery_caption photogallery_text'})
                    if author and author.text.strip():
                        self.creator = author.text.strip()


            #taxa temporarily excluded. That info may not be from a verifiable source.

            if otherMetaData:
                self.metaData = otherMetaData


            formatted = list(self.formatOutput)
            print formatted
            print '................'

            return formatted

        elif 'p=taxdetails' in _url:
            #get the image tab on the taxonomy page
            return None #unable to verify the image license from this page (only text)

        else:
            return None
