# myapp/middleware.py
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import redirect
from zono import settings

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_timeout = getattr(settings, 'SESSION_EXPIRE_SECONDS', 3600)  # Default to 1 hour
        expire_after_last_activity = getattr(settings, 'SESSION_EXPIRE_AFTER_LAST_ACTIVITY', True)

        if request.session.get('last_activity'):
            last_activity_time_str = request.session.get('last_activity')
            last_activity_time = timezone.datetime.fromisoformat(last_activity_time_str)
            time_inactive = timezone.now() - last_activity_time
            if time_inactive > timedelta(seconds=session_timeout):
                # Expire session: session has been inactive for too long
                request.session.flush()  # Clear the session

                # Optionally, you can redirect the user to a login page or any other page
                if settings.SESSION_TIMEOUT_REDIRECT:
                    return redirect(settings.SESSION_TIMEOUT_REDIRECT)

        # Update the last activity time in ISO format (string)
        request.session['last_activity'] = timezone.now().isoformat()

        # Continue processing the request
        response = self.get_response(request)
        return response
