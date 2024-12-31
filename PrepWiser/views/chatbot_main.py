from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers,status
from django.views import View
from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .forms import UploadFileForm, MessageForm
from langchain.docstore import InMemoryDocstore
import os
from .ingest_data import *
from .query_data import *
import pickle


class DocumentSerializer(serializers.Serializer):
    file = serializers.FileField()

class DocumentUploadView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = DocumentSerializer(data=request.data)
        if serializer.is_valid():
            uploaded_file = serializer.validated_data['file']
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'documents'))
            filename = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.path(filename)
            embed_doc(file_path)
            return Response({'message': 'Document uploaded and processed successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()

class ChatView(APIView):
    embeddings = OpenAIEmbeddings(api_key="")

    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            user_input = serializer.validated_data['message']
            if "vectorstore.pkl" in os.listdir("."):
                with open("vectorstore.pkl", "rb") as f:
                    data = pickle.load(f)
                    index = faiss.deserialize_index(data['index'])
                    docstore = InMemoryDocstore(data['docstore'])
                    vectorstore = FAISS(index=index, docstore=docstore, index_to_docstore_id=data['index_to_docstore_id'], embedding_function=self.embeddings)

                    chain = get_chain(vectorstore)
                    docs = vectorstore.similarity_search(user_input)
                    output = chain({"question": user_input, "chat_history": [], "context": docs[:2]})
                    
                    return Response({'answer': output["answer"]}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Vector data not available'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)