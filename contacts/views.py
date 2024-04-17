from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from contacts.integrations import close
import traceback

client_id = settings.CLOSE_CLIENT_ID
client_secret = settings.CLOSE_CLIENT_SECRET
username = settings.USERNAME

def index(request):
    return HttpResponse("Hello, Contacts")

@require_http_methods(['GET'])
def close_oauth(request):
    close_auth_url = close.initiate_oauth(username, client_id, client_secret)
    return redirect(close_auth_url)

@require_http_methods(['GET'])
def close_redirect(request):
    code = request.GET.get("code", "")
    if not code:
        error = request.GET.get("error", "")
        return JsonResponse({"success": False, "message": f"Error with Close Oauth: {error}"}, status=400)
    try:
        close.authenticate(code)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"success": False}, status=500)
    return JsonResponse({"success": True})

@require_http_methods(['POST'])
def close_create_contact(request):
    username = request.POST.get("username")
    contact_name = request.POST.get("contact_name")
    contact_title = request.POST.get("contact_title", "")
    contact_phones = request.POST.get("contact_phones", [])
    contact_emails = request.POST.get("contact_emails", [])
    contact_urls = request.POST.get("contact_urls", [])
    try:
        close.create_contact(username, contact_name, contact_title, contact_phones, contact_emails, contact_urls)
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"success": False}, status=500)
    return JsonResponse({"success": True})
