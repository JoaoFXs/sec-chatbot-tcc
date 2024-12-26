from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Curso(models.Model):
    id_curso = models.AutoField(primary_key=True)
    nome_curso = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome_curso

class Turma(models.Model):
    sigla_turma = models.CharField(max_length=10, unique=True)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)

    def __str__(self):
        return self.sigla_turma
    

class AlunoManager(BaseUserManager):
    def create_user(self, ra, nome, password=None, **extra_fields):
        if not ra:
            raise ValueError('O RA deve ser definido')
        user = self.model(ra=ra, nome=nome, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, ra, nome, password=None, **extra_fields):
        """
        Create and return a superuser with a username and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(ra, nome, password, **extra_fields)

class Aluno(AbstractBaseUser, PermissionsMixin):
    ra = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    horas_complementares = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    username = models.CharField(max_length=30, unique=True)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, null=True, blank=True)  # Permitir nulo temporariamente
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, null=True, blank=True)  # Permitir nulo temporariamente
    situacao_matricula = models.CharField(max_length=30)
    semestre = models.DecimalField(max_digits=2, decimal_places=0, default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Necessário para superusuário
    is_superuser = models.BooleanField(default=False)  # Necessário para superusuário

    USERNAME_FIELD = 'ra'
    REQUIRED_FIELDS = ['nome']

    objects = AlunoManager()

    def __str__(self):
        return self.nome


class Materia(models.Model):
    id_materia = models.AutoField(primary_key=True)
    nome_materia = models.CharField(max_length=100, unique=True)
    ementa_materia = models.FileField(upload_to='ementa/')
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    turmas = models.ManyToManyField(Turma, related_name='materias')  # Alteração para ManyToMany

    def __str__(self):
        return self.nome_materia

class Professor(models.Model):
    rp = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=100)
    formacao = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    cursos = models.ManyToManyField(Curso, related_name='professores')
    turmas = models.ManyToManyField(Turma, related_name='professores')
    materia_lecionada = models.ManyToManyField(Materia, related_name='professores')
    def __str__(self):
        return self.nome

class Nota(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    trabalho_um = models.DecimalField(max_digits=5, decimal_places=2)
    trabalho_dois = models.DecimalField(max_digits=5, decimal_places=2)
    prova = models.DecimalField(max_digits=5, decimal_places=2)
    media = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f'{self.aluno.nome} - {self.materia.nome_materia}'

class HorarioAula(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()

    def __str__(self):
        return f'{self.turma.sigla_turma} - {self.materia.nome_materia} - {self.horario_inicio.strftime("%H:%M")} a {self.horario_fim.strftime("%H:%M")}'
    
class Calendario(models.Model):
    nome = models.CharField(max_length=100)
    arquivo = models.FileField(upload_to='calendarios/')
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
    
class DocumentoFaculdade(models.Model):
    nome = models.CharField(max_length=100)
    arquivo = models.FileField(upload_to='documentos_faculdades/')
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome