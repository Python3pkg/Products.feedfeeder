# -*- coding: utf-8 -*-
from zope import interface


class IFeedItemContentHandler(interface.Interface):
    """Content handler for feed items"""

    def apply(entry, contentNode):
        """Apply the content handler"""
