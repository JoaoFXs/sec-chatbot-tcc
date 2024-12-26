import random
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer
from tensorflow.keras.models import load_model
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
from .funcionalidades.notas import montarRetornoNota
from .models import Aluno, Professor, Materia, HorarioAula, Calendario, DocumentoFaculdade


# Carregue seu modelo e dados
model = load_model('model.h5')

# Defina palavras e classes
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
intents_path = os.path.join(base_dir, 'sec_chatbot', 'templates', 'sec_chatbot', 'json', 'intents.json')
ignore_words = ["!", "@", "#", "$", "%", "*", "?"]
lemmatizer = WordNetLemmatizer()

with open(intents_path) as file:
    with open(intents_path, 'r', encoding='utf-8') as file:
        intents = json.load(file)
    words = []
    classes = []
    for intent in intents['intents']:
        for pattern in intent['patterns']:
            word_list = nltk.word_tokenize(pattern.lower())
            words.extend(word_list)
        classes.append(intent['tag'])

    words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
    words = sorted(set(words))
    classes = sorted(set(classes))

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence.lower()) # Converte para minúsculas
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

def bag_of_words(sentence, words):
    sentence_words = clean_up_sentence(sentence)
    bag = [0]*len(words)  
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s: 
                bag[i] = 1
    return np.array(bag)

def predict_class(sentence, model):
    bow = bag_of_words(sentence, words)
   
    res = model.predict(np.array([bow]))[0]
   
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list

def get_response(intents_list, intents_json):
    tag = intents_list[0]['intent']
    
    if isinstance(intents_json, list):
        list_of_intents = [i for i in intents_json]
    else:
        list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if i['tag'] == tag:
            return random.choice(i['responses'])
    return "Desculpe, não entendi o que você disse."

def suggest_professors(name_part):
    """Sugere nomes de professores que contenham a parte do nome fornecida."""
    professors = Professor.objects.filter(nome__icontains=name_part).values_list('nome', flat=True)
    return list(professors)

@csrf_exempt
def chat(request):
    try:
        aluno = Aluno.objects.get(ra=request.user.ra)
    except Aluno.DoesNotExist:
        aluno = None
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            message = data.get('message')
           
            if message:
                # Verifica se o chatbot está aguardando o nome de um professor
                if request.session.get('awaiting_professor_name'):
                    professor_name = message.strip().title()
                    cont = 0
                    try:
                        professor = Professor.objects.get(nome=professor_name)
                        cursos = ', '.join([curso.nome_curso for curso in professor.cursos.all()])
                        turmas = ', '.join([turma.sigla_turma for turma in professor.turmas.all()])
                        materias = ', '.join([materia.nome_materia for materia in professor.materia_lecionada.all()])
                        # Formate a resposta com os dados do professor
                        res = (
                            f" - Nome do Professor: {professor.nome}\n"
                            f" - Curso Lecionado: {cursos}\n"
                            f" - Turmas: {turmas}\n"
                            f" - Materias Lecionadas:  {materias}\n"
                            f" - Formação:  {professor.formacao}\n"
                            f" - Email para contato:  {professor.email}"                            
                        )
                    except Professor.DoesNotExist:
                        # Sugere professores com nomes semelhantes
                        suggestions = suggest_professors(message.strip().lower())
                        if suggestions:
                            request.session['awaiting_professor_name'] = True
                            request.session.modified = True
                            cont = 1
                            res = f"Não encontrei o professor exato, mas encontrei os seguintes nomes semelhantes: {', '.join(suggestions)}."                          
                        else:
                            res = "Professor não encontrado. Por favor, verifique o nome e tente novamente."
                            cont = 0
                    # Reinicia o estado da sessão caso cont for igual a 0
                    if(cont == 0):
                        del request.session['awaiting_professor_name']
                        request.session.modified = True
                    
                    return JsonResponse({"response": res})
               # Verifica se o chatbot está aguardando a matéria para as notas
                elif request.session.get('awaiting_materia_nota'):
                    materia_name = message.strip().title()
                    request.session['materia_nota'] = materia_name
                    request.session['awaiting_materia_nota'] = False  # Limpa a variável
                    request.session['awaiting_nota_detail'] = True
                    request.session.modified = True
                    return JsonResponse({"response": "Você gostaria de saber a nota do Trabalho 1, Trabalho 2, Prova ou Média?"})
                
                # Verifica se o chatbot está aguardando o detalhe da nota (trabalho, prova ou média)
                elif request.session.get('awaiting_nota_detail'):
                    nota_detail = message.strip().lower()
                    materia_name = request.session.get('materia_nota')

                    # Valida o detalhe solicitado
                    if nota_detail in ['trabalho 1', 'trabalho 2', 'prova', 'média']:
                        try:
                            # Buscar a nota do aluno para a matéria e o detalhe específico
                            materia = Materia.objects.get(nome_materia=materia_name, turmas=aluno.turma)
                            if nota_detail == 'trabalho 1':
                                nota = materia.nota_set.get(aluno=aluno).trabalho_um
                            elif nota_detail == 'trabalho 2':
                                nota = materia.nota_set.get(aluno=aluno).trabalho_dois
                            elif nota_detail == 'prova':
                                nota = materia.nota_set.get(aluno=aluno).prova
                            elif nota_detail == 'média':
                                nota = materia.nota_set.get(aluno=aluno).media
                            res = f"Sua nota de {nota_detail} em {materia_name} é {nota}."
                        except (Materia.DoesNotExist, AttributeError):
                            res = "Não encontrei essa matéria ou as notas não estão disponíveis no momento."
                            
                        # Limpa o estado da sessão após a consulta
                        del request.session['awaiting_materia_nota']
                        del request.session['awaiting_nota_detail']
                        request.session.modified = True

                    else:
                        res = "Por favor, selecione entre Trabalho 1, Trabalho 2, Prova ou Média."

                 
                    return JsonResponse({"response": res})
                # Verifica se o chatbot está aguardando a matéria
                elif request.session.get('awaiting_materia'):
                    materia_name = message.strip().title()
                    request.session['materia'] = materia_name
                    request.session['awaiting_turma'] = True
                    request.session.modified = True
                    return JsonResponse({"response": "Por favor, informe a turma da matéria."})
                # Verifica se o chatbot está aguardando a Turma
                elif request.session.get('awaiting_materia_selection'):
                    selected_materia = message.strip().title()
                    materias_disponiveis = request.session.get('materias_disponiveis', [])

                    if selected_materia in materias_disponiveis:
                        try:
                            # Busca o horário da aula para a matéria selecionada e a turma do aluno
                            horario = HorarioAula.objects.filter(turma=aluno.turma, materia__nome_materia=selected_materia).first()

                            if horario:
                                res = (
                                    f"A aula de {selected_materia} para a turma {aluno.turma} "
                                    f"Ocorre às {horario.horario_inicio} -{horario.horario_fim} "
                                )
                            else:
                                res = "Não encontrei o horário dessa aula. Verifique os dados e tente novamente."
                        except Materia.DoesNotExist:
                            res = "Matéria não encontrada. Verifique os dados e tente novamente."
                    else:
                        res = "Matéria selecionada inválida. Por favor, escolha uma das opções fornecidas."

                    # Limpa o estado da sessão após a seleção da matéria
                    del request.session['materias_disponiveis']
                    del request.session['awaiting_materia_selection']
                    request.session.modified = True
                    
                    return JsonResponse({"response": res})
                
                else:
                    # Processamento normal da mensagem
                    ints = predict_class(message, model)
                    print(ints)
                    print(message)
                    res = get_response(ints, intents)
                    if "{{ aluno.ra }}" in res and aluno:
                        res = res.replace("{{ aluno.ra }}", aluno.ra)
                    
                    # Verifica se a intent é 'informacoes_professor'
                    if ints and ints[0]['intent'] == 'informacoes_professor':
                        # Define o estado para aguardar o nome do professor
                        request.session['awaiting_professor_name'] = True
                        request.session.modified = True
                        # Resposta para solicitar o nome do professor
                        res = "Por favor, informe o nome do professor que deseja obter informações."

                    # Verifica se a intent é 'nota_aluno'
                    if ints and ints[0]['intent'] == 'nota_aluno':
                        materias = Materia.objects.filter(turmas=aluno.turma)
                        # Cria uma lista de matérias disponíveis
                        materias_list = [materia.nome_materia for materia in materias]
                        materias_str = ', '.join(materias_list)
                        messageNota = message.lower()
                        boletim = True
                        if "todas" in messageNota or "boletim" in messageNota:
                            res = montarRetornoNota(aluno, materias_list)
                            boletim = False
                        if materias.exists() and boletim == True: 
                            # Armazena as matérias disponíveis na sessão para futura seleção
                            request.session['materias_disponiveis'] = materias_list
                            # Define o estado para aguardar o nome da matéria
                            request.session['awaiting_materia_nota'] = True
                            request.session.modified = True
                            res = f"Por favor, informe a matéria que deseja consultar as notas. Matérias disponiveis: {materias_str}"
                    # Verifica se a intent é 'consulta_calendario'
                    if ints and ints[0]['intent'] == 'consulta_calendario':
                        # Busca o calendário mais recente
                        calendario = Calendario.objects.order_by('-data_upload').first()
                        if calendario:
                        # Retorna o link de download do arquivo para o usuário
                            res = "Você pode baixar o calendário acadêmico aqui: \n\n\n<a href='/download-calendario/' style='color: #007bff; text-decoration: none; font-weight: bold; border: 1px solid #007bff; padding: 5px 10px; border-radius: 5px; transition: background-color 0.3s, color 0.3s;'>Baixar Calendário Acadêmico</a>"
                        else:
                            res = "Desculpe, não foi encontrado um calendário acadêmico."    

                    # Verifica se a intent é 'consulta_estagio'
                    if ints and ints[0]['intent'] == 'consulta_estagio':
                        # Busca o calendário mais recente
                        docEstagio = DocumentoFaculdade.objects.filter(nome='exemplo-doc-estagio').first()
                        if docEstagio:
                        # Retorna o link de download do arquivo para o usuário
                            res = (
                                "Olá! Sobre o estágio obrigatório:\n\n\n"
                                "• Você precisa realizar 350 horas obrigatórias de estágio.\n"
                                "• É necessário comprovar essas horas por meio de documentos, como relatórios de atividades ou declarações da empresa onde você está estagiando.\n"
                                "• Certifique-se de detalhar todas as atividades realizadas, especificando o que foi feito, quando foi feito e as horas correspondentes para cada tarefa.\n"
                                "• Caso tenha dúvidas sobre o processo ou os documentos necessários, entre em contato com a secretaria do curso ou o coordenador responsável pelo estágio.\n"
                                "• Caso queira usar como exemplo, segue modelo de relatório de estágio:\n\n\n\n\n"
                                "     <a href='/download-exemplo-estagio/' style='color: #007bff; text-decoration: none; font-weight: bold; border: 1px solid #007bff; padding: 5px 10px; border-radius: 5px; transition: background-color 0.3s, color 0.3s;'>Baixar exemplo estágio</a>")
                        else:
                            res = "Desculpe, não foi encontrado um calendário acadêmico."    
                    # Verifica se a intent é 'consulta_quantidade_horas_complementares'
                    if ints and ints[0]['intent'] == 'consulta_quantidade_horas_complementares':
                        horas_complementares = aluno.horas_complementares
                    
                        res = f"Você possui {horas_complementares} de 300 horas complementares."         
                    # Verifica se a intent é 'horario_aula'
                    if ints and ints[0]['intent'] == 'horario_aula':
                        # Obtém todas as matérias associadas à turma do aluno
                        materias = Materia.objects.filter(turmas=aluno.turma)
                        if materias.exists():
                            # Cria uma lista de matérias disponíveis
                            materias_list = [materia.nome_materia for materia in materias]
                            materias_str = ', '.join(materias_list)
                            # Armazena as matérias disponíveis na sessão para futura seleção
                            request.session['materias_disponiveis'] = materias_list
                            request.session['awaiting_materia_selection'] = True
                            request.session.modified = True
                            
                            # Resposta com as matérias disponíveis para o aluno escolher
                            res = f"Por favor, informe a matéria. Suas matérias disponiveis são: {materias_str}."
                        else:
                            res = "Não encontrei matérias para a sua turma. Por favor, entre em contato com o suporte."

                        return JsonResponse({"response": res})

                    return JsonResponse({"response": res})

            return JsonResponse({"error": "Mensagem não encontrada"}, status=400)
        except Exception as e:
            # Opcional: Log do erro para depuração
            print(f"Erro no chat: {e}")
            return JsonResponse({"error": "Erro ao processar a mensagem"}, status=500)
    
    return JsonResponse({"error": "Método não permitido"}, status=405)

