# models/__init__.py
from .base import BaseModel

# Import model modules so mappers register
from .property import Property
from .property_analysis import PropertyAnalysis
from .listing import Listing
from .client import Client
from .saved_search import SavedSearch
from .search_listing_analysis import SearchListingAnalysis
from .saved_search_field import SavedSearchField
from .saved_search_match import SavedSearchMatch
from .client_notification_preference import ClientNotificationPreference
from .sent_notification import SentNotification

__all__ = [
    "Base",
    "BaseModel",
    "Property",
    "PropertyAnalysis",
    "Listing",
    "Client",
    "SavedSearch",
    "SearchListingAnalysis",
    "SavedSearchField",
    "SavedSearchMatch",
    "ClientNotificationPreference",
    "SentNotification",
]
