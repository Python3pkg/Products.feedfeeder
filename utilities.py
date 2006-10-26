# -*- coding: utf-8 -*-
##code-section module-header #fill in your manual code here
import urllib2
import os
import md5
import tempfile
from xml.dom import minidom
import feedparser
from zope import component
from DateTime import DateTime
from Products.feedfeeder.interfaces.container import IFeedsContainer
from Products.feedfeeder.interfaces.contenthandler import IFeedItemContentHandler
##/code-section module-header

from Products.feedfeeder.interfaces.consumer import IFeedConsumer
from zope import interface

class FeedConsumer:
    """
    """
    # zope3 interfaces
    interface.implements(IFeedConsumer)

    ##code-section class-header_FeedConsumer #fill in your manual code here
    ##/code-section class-header_FeedConsumer

    def retrieveFeedItems(self, container):
        feedContainer = IFeedsContainer(container)
        for url in feedContainer.getFeeds():
            self._retrieveSingleFeed(feedContainer, url)


    def tryRenamingEnclosure(self, enclosure, feeditem):
        newId = enclosure.Title()
        for x in range(1, 10):
            if newId not in feeditem.objectIds():
                try:
                    feeditem.manage_renameObject(enclosure.getId(),
                                            newId)
                    break
                except:
                    pass
            newId = '%i_%s' % (x, enclosure.Title())


    def _retrieveSingleFeed(self, feedContainer, url):
        # feedparser doesn't understand proper file: url's
        if url.startswith('file://'):
            url = url[7:]
            if not os.path.exists(url):
                raise IOError("Couldn't locate %r" % url)
        parsed = feedparser.parse(url)
        for entry in parsed.entries:
            sig = md5.new(entry.id)
            id = sig.hexdigest()
            updated = DateTime(entry.updated)
            prev = feedContainer.getItem(id)

            if prev is None:
                # Completely new item, add it.
                addItem = feedContainer.addItem
            elif updated > prev.getFeedItemUpdated():
                # Refreshed item, replace it.
                addItem = feedContainer.replaceItem
            else:
                # Not new, not refreshed: let it be, laddy.
                continue

            obj = addItem(id)

            linkDict = getattr(entry, 'link', None)
            if linkDict:
                link = linkDict['href']
            else:
                linkDict = getattr(entry, 'links', [{'href': ''}])[0]
                link = linkDict['href']

            obj.update(id=id, title=entry.title,
                       feedItemAuthor=getattr(entry, 'author', ''),
                       feedItemUpdated=updated,
                       link=link)
            if hasattr(entry, 'content'):
                content = entry.content[0]
                if content['type'] in ('text/xhtml', 'application/xhtml+xml'):
                    # Warning: minidom.parseString needs a byte
                    # string, not a unicode one, so we need to
                    # encode it first.
                    # http://evanjones.ca/python-utf8.html
                    doc = minidom.parseString(content['value'].encode('utf-8'))
                    if len(doc.childNodes) > 0 and doc.firstChild.hasAttributes():
                        handler = None
                        top = doc.firstChild
                        cls = top.getAttribute('class')
                        if cls:
                            handler = component.queryAdapter(obj,
                                                             IFeedItemContentHandler,
                                                             name=cls)
                        if handler is None:
                            handler = component.queryAdapter(obj,
                                                             IFeedItemContentHandler)

                        if handler is None:
                            obj.update(text=content['value'])
                        else:
                            handler.apply(top)
                            # Grab the first non-<dl> node and treat
                            # that as the content.
                            actualContent = None
                            for node in top.childNodes:
                                if node.nodeName == 'div':
                                    actualContent = node.toxml()
                                    obj.update(text=actualContent)
                                    break
                    else:
                        obj.update(text=content['value'])
                else:
                    obj.update(text=content['value'])

            if hasattr(entry, 'links'):
                enclosures = [x for x in entry.links if x.rel == 'enclosure']
                real_enclosures = [x for x in enclosures if
                                   not self.isHTMLEnclosure(x)]

                for link in real_enclosures:
                    enclosureSig = md5.new(link.href)
                    enclosureId = enclosureSig.hexdigest()
                    enclosure = obj.addEnclosure(enclosureId)
                    enclosure.update(title=enclosureId)
                    updateWithRemoteFile(enclosure, link)
                    if enclosure.Title() != enclosure.getId():
                        self.tryRenamingEnclosure(enclosure, obj)


    def isHTMLEnclosure(self, enclosure):
        return enclosure.type == u'text/html'


##code-section module-footer #fill in your manual code here
import re
RE_FILENAME = re.compile('filename *= *(.*)')

def updateWithRemoteFile(obj, link):
    file = tempfile.TemporaryFile('w+b')
    try:
        remote = urllib2.urlopen(link.href.encode('utf-8'))
        info = remote.info()
        filename = None
        if link.href.startswith('file:'):
            pos = link.href.rfind('/')
            if pos > -1:
                filename = link.href[pos+1:]
            else:
                filename = link.href[5:]

        disp = info.get('Content-Disposition', None)
        if disp is not None:
            m = RE_FILENAME.search(disp)
            if m is not None:
                filename = m.group(1).strip()

        if filename is not None:
            obj.update(title=filename)

        max = 2048
        sz = max
        while sz == max:
            buffer = remote.read(max)
            sz = len(buffer)
            if sz > 0:
                file.write(buffer)

        file.flush()
        file.seek(0)
        obj.update_data(file, link.type)
        file.close()
    except urllib2.URLError, e:
        # well, if we cannot retrieve the data, the file object will
        # remain empty
        pass
    except  OSError, e:
        # well, if we cannot retrieve the data, the file object will
        # remain empty
        pass

##/code-section module-footer


