
from django.contrib.auth.backends import ModelBackend
from .models import Aluno

class RAAuthBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        ra = kwargs.get('ra') or username
        try:
            user = Aluno.objects.get(ra=ra)          
            if user.password == password:
                return user
        except Aluno.DoesNotExist:
            return None
