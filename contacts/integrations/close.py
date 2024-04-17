from typing import TypedDict, Literal
from django.conf import settings
from contacts.models import Customer
import requests, datetime

close_root_url = 'https://api.close.com/api/v1'
close_auth_url = 'https://api.close.com/oauth2/token'
username = settings.USERNAME

CloseContactMethodType = Literal["office", "mobile", "home", "direct", "fax", "url", "other"]

class CloseContactPhone(TypedDict):
    phone: str
    type: CloseContactMethodType

class CloseContactEmail(TypedDict):
    email: str
    type: CloseContactMethodType

class CloseContactUrl(TypedDict):
    url: str
    type: CloseContactMethodType

class UnauthorizedException(Exception):
    pass


def refresh_auth():
    customer = Customer.objects.get(username=username)
    integration = customer.integrations['close']
    data = {
        "client_id": integration['client_id'],
        "client_secret": integration['client_secret'],
        "grant_type": "refresh_token",
        "refresh_token": integration['refresh_token'],
    }
    response = requests.post(close_auth_url, data)
    response_json = response.json()
    customer.integrations['close'].update({
        "access_token": response_json.get("access_token"),
        "refresh_token": response_json.get("refresh_token"),
        "expires_at": (datetime.datetime.now() + datetime.timedelta(seconds=response_json.get("expires_in"))).isoformat(),
    })
    customer.save(update_fields=['integrations'])
    return

def refresh_access_token(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except UnauthorizedException:
            refresh_auth()
            return func(*args, **kwargs)
    return wrapper

def initiate_oauth(username: str, client_id: str, client_secret: str):
    customer, _ = Customer.objects.get_or_create(username=username)
    customer.integrations['close'] = {
        "client_id": client_id,
        "client_secret": client_secret,
    }
    customer.save(update_fields=["integrations"])
    close_auth_url = f"https://app.close.com/oauth2/authorize/?client_id={client_id}&response_type=code"
    return close_auth_url


def authenticate(code: str):
    customer = Customer.objects.get(username=username)
    integration = customer.integrations['close']
    data = {
        "client_id": integration['client_id'],
        "client_secret": integration['client_secret'],
        "grant_type": "authorization_code",
        "code": code,
    }
    response = requests.post(close_auth_url, data)
    response_json = response.json()
    customer.integrations['close'].update({
        "access_token": response_json.get("access_token"),
        "refresh_token": response_json.get("refresh_token"),
        "expires_at": (datetime.datetime.now() + datetime.timedelta(seconds=response_json.get("expires_in"))).isoformat(),
        "user_id": response_json.get("user_id"),
        "organization_id": response_json.get("organization_id"),
    })
    customer.save(update_fields=["integrations"])

@refresh_access_token
def create_contact(username: str, contact_name: str, contact_title: str = "", contact_phones: list[CloseContactPhone] = [], contact_emails: list[CloseContactEmail] = [], contact_urls: list[CloseContactUrl] = []):
    customer = Customer.objects.get(username=username)
    integration = customer.integrations['close']
    access_token = integration['access_token']
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    # get lead
    get_lead_url = f"{close_root_url}/lead/"
    response = requests.get(get_lead_url, params={"limit": 1}, headers=headers)
    if response.status_code == 401:
        raise UnauthorizedException()
    response_json = response.json()
    leads = response_json['data']
    if len(leads) == 0:
        raise Exception()
    lead_id = leads[0]['id']

    # create contact
    contact_data = {
        "lead_id": lead_id,
        "name": contact_name,
        "title": contact_title,
        "phones": contact_phones,
        "emails": contact_emails,
        "urls": contact_urls,
    }
    create_contact_url = f"{close_root_url}/contact/"
    contact_response = requests.post(create_contact_url, json=contact_data, headers=headers)
    if contact_response.status_code == 401:
        raise UnauthorizedException()
    if not contact_response.ok:
        raise Exception()
    return
