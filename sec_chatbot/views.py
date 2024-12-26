from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.http import HttpResponse
import json
import pickle
import nltk
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import SGD
from nltk.stem import WordNetLemmatizer
import os
from .models import Aluno, Calendario, DocumentoFaculdade
# Create your views here.
from .forms import AlunoAuthenticationForm
from django.http import JsonResponse

def user_login(request):
    if request.method == 'POST':
        ##form = AlunoAuthenticationForm(request, data=request.POST)
        form = AlunoAuthenticationForm(request.POST)
       
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = AlunoAuthenticationForm()
    return render(request, 'sec_chatbot/pages/login.html', {'form': form})

    
@login_required
def home(request):
    try:
        aluno = Aluno.objects.get(ra=request.user.ra)
    except Aluno.DoesNotExist:
        aluno = None
    return render(request, 'sec_chatbot/pages/home.html', {'aluno': aluno})

def download_calendario(request):
    # Busca o calendário mais recente
    calendario = Calendario.objects.order_by('-data_upload').first()
    if calendario:
        # Abre o arquivo
        with open(calendario.arquivo.path, 'rb') as arquivo:
            response = HttpResponse(arquivo.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{calendario.arquivo.name}"'
            return response
    else:
        return HttpResponse("Desculpe, não foi encontrado um calendário acadêmico.", status=404)
    
def download_doc_estagio(request):
    # Busca o calendário mais recente
    docEstagio = DocumentoFaculdade.objects.filter(nome='exemplo-doc-estagio').first()
    if docEstagio:
        # Abre o arquivo
        with open(docEstagio.arquivo.path, 'rb') as arquivo:
            response = HttpResponse(arquivo.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{docEstagio.arquivo.name}"'
            return response
    else:
        return HttpResponse("Desculpe, não foi encontrado um documento de estagio.", status=404)    
@staff_member_required
def train(request):
    if request.method == 'POST':
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        intents_path = os.path.join(base_dir, 'sec_chatbot', 'templates', 'sec_chatbot', 'json', 'intents.json')
        lemmatizer = WordNetLemmatizer()
        words = []
        documents = []
        with open(intents_path, 'r', encoding='utf-8') as file:
            intents = json.load(file)
        classes = [i['tag'] for i in intents['intents']]
        ignore_words = ["!", "@", "#", "$", "%", "*", "?"]

        for intent in intents['intents']:
            for pattern in intent['patterns']:
                word_list = nltk.word_tokenize(pattern)
                words.extend(word_list)
                documents.append((word_list, intent['tag']))

        words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
        words = sorted(set(words))
        classes = sorted(set(classes))

        pickle.dump(words, open('words.pkl', 'wb'))
        pickle.dump(classes, open('classes.pkl', 'wb'))

        training = []
        output_empty = [0] * len(classes)
        for doc in documents:
            bag = [1 if lemmatizer.lemmatize(w.lower()) in [lemmatizer.lemmatize(word.lower()) for word in doc[0]] else 0 for w in words]
            output_row = list(output_empty)
            output_row[classes.index(doc[1])] = 1
            training.append([bag, output_row])

        max_bag_length = max(len(data[0]) for data in training)
        for data in training:
            while len(data[0]) < max_bag_length:
                data[0].append(0)
            if len(data[1]) != len(classes):
                data[1] = data[1] + [0] * (len(classes) - len(data[1]))

        training = np.array(training, dtype=object)
        x = np.array([data[0] for data in training])
        y = np.array([data[1] for data in training])

        model = Sequential()
        model.add(Dense(128, input_shape=(len(x[0]),), activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(64, activation='relu'))
        model.add(Dropout(0.5))
        model.add(Dense(len(y[0]), activation='softmax'))

        sgd = SGD(learning_rate=0.01, momentum=0.9, nesterov=True)
        model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

        model.fit(x, y, epochs=200, batch_size=5, verbose=1)
        model.save('model.h5')

        return JsonResponse({'status': 'success'})

    return render(request, 'sec_chatbot/pages/train_chatbot.html')