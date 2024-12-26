from django.contrib import admin

# Register your models here.
from sec_chatbot.models import Aluno
from sec_chatbot.models import Professor
from sec_chatbot.models import Curso
from sec_chatbot.models import Turma
from sec_chatbot.models import Nota
from sec_chatbot.models import Materia
from sec_chatbot.models import HorarioAula
from sec_chatbot.models import Calendario
from sec_chatbot.models import DocumentoFaculdade
admin.site.register(Aluno)
admin.site.register(Professor)
admin.site.register(Curso)
admin.site.register(Turma)
admin.site.register(Nota)
admin.site.register(Materia)
admin.site.register(HorarioAula)
admin.site.register(Calendario)
admin.site.register(DocumentoFaculdade)
