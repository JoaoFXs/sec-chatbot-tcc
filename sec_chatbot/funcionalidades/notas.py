from ..models import Aluno, Professor, Materia, HorarioAula


def montarRetornoNota(aluno, lista_materias):
    boletim_completo = ""
    
    for nome_materia in lista_materias:
        try:
            materia = Materia.objects.get(nome_materia=nome_materia, turmas=aluno.turma)
            nota = materia.nota_set.get(aluno=aluno)
            
            # Verifica se cada nota existe, caso contrário insere "não lançado ainda"
            trabalho_um = nota.trabalho_um if nota.trabalho_um is not None else "não lançado ainda"
            trabalho_dois = nota.trabalho_dois if nota.trabalho_dois is not None else "não lançado ainda"
            prova = nota.prova if nota.prova is not None else "não lançado ainda"
            media = nota.media if nota.media is not None else "não lançado ainda"
            
            # Formata o boletim para a matéria
            montando_boletim = (
                f"****** {nome_materia.upper()} ******\n"
                f"Trabalho 1: {trabalho_um}\n"
                f"Trabalho 2: {trabalho_dois}\n"
                f"Prova: {prova}\n"
                f"Média: {media}\n"
            )
            
            boletim_completo += montando_boletim
        
        except Materia.DoesNotExist:
            boletim_completo += f"****** {nome_materia.upper()} ******\nMatéria não encontrada.\n{'*' * (10 + len(nome_materia))}\n"
        except Exception as e:
            boletim_completo += f"Erro ao buscar notas para {nome_materia}: {str(e)}\n"
    
    return boletim_completo



