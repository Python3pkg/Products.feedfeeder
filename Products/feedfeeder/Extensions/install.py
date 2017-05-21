from io import StringIO
from Products.CMFCore.utils import getToolByName


def install(site):
    out = StringIO()
    applyGenericSetupProfile(site, out)


def applyGenericSetupProfile(site, out):
    """Just apply our own extension profile.
    """

    our_profile = 'profile-Products.feedfeeder:default'
    setup_tool = getToolByName(site, 'portal_setup')
    print("Applying the generic setup profile for feedfeeder...", file=out)
    setup_tool.runAllImportStepsFromProfile(our_profile)
    print("Applied the generic setup profile for feedfeeder", file=out)
