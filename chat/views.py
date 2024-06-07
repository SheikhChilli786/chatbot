from django.shortcuts import render
import json 
import os
import io
from rest_framework.views import APIView
from rest_framework.response import Response
from openai import OpenAI
from .models import ChatHistory
from .serializers import ChatHistorySerializer
from pydub import AudioSegment
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
starting_prompt = "you are to provide answers given to you"

class ChatBotView(APIView):
    def post(self,request,user_id=None):
        chat_history = self.audio_conversion(request) 
        chat_type = request.data.get('chat_type',None)
        user = request.data.get('user_id',None)
        text = request.data.get('user_chat', None)

        if chat_type != 'text' and isinstance(chat_history,Response):
            return chat_history 
        
        client = OpenAI(api_key="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")

        if chat_type == 'text':
            serializer = ChatHistorySerializer(data = request.data)
            chat_history = self.serializer_valid_check(serializer,data=request.data)

            if isinstance(chat_history,Response):
                return chat_history
            
        if chat_type == 'audio':
            audio_file = open(chat_history.audio.path,"rb")
            transcript = client.audio.transcriptions.create(model="whisper-1",file=audio_file)
            text = transcript.text
            chat_history.user_chat = text
            chat_history.save()

        chat_historys = ChatHistory.objects.filter(user_id__id=user)
        messages = self.chat_text(chat_historys,starting_prompt)
        translation = self.transiliated_data(client,messages)
        if isinstance(translation,Response):
            return translation
        chat_history.response_chat = translation
        chat_history.save()
        serializer = ChatHistorySerializer(instance=chat_history)
        return Response(serializer.data,status=200)


    def get(self,request,user_id):
        chat_history = ChatHistory.objects.filter(user_id__id = user_id)
        serializer = ChatHistorySerializer(chat_history,many=True)
        return Response(serializer.data)
    
    def delete(self,request,user_id):
        ChatHistory.onjects.filter(user_id__id = user_id).delete()
        return Response({})
    
    def chat_text(self,chat_historys,starting_prompt):
        messages = [{
            "role":"system",
            "content":starting_prompt
        }]
        if chat_historys:
            for chat_history in chat_historys:
                if chat_history.user_chat:
                    messages.append({
                        "role":"user","content":f"user_chat = {chat_history.user_chat}"
                    })
                    if chat_history.response_chat:
                        messages.append({
                            "role":"system",
                            "content":chat_history.response_chat
                        })
        return messages
    def serializer_valid_check(self,serializer,data):
        if serializer.is_valid():
            return serializer.save()
        else:
            return Response(serializer.errors,status=400)
        
    def transiliated_data(self,client,messages):
        try:
            response = client.chat.completions.create(
                model = "gpt-3.5-turbo-16k",
                response_format = {"type":"json_object"},
                messages=messages
            )
            message = response.choices[0].message.content
            data = json.loads(message)
            translation = data.get("data",None)
            return translation
        except Exception as E:
            return Response(str(E))
        
    
    def audio_conversion(self,request):
        audio_file = request.data.get('audio',None)
        user = request.data.get('user_id',None)
        chat_type = request.data.get('chat_type',None)
        if chat_type == 'audio':
            try:
                audio_content = audio_file.read()
                audio_segment = AudioSegment.from_file(
                    io.BytesIO(audio_content),
                    frame_rate = 44100,
                    channels = 2,
                    sample_width = 2
                )
                modified_audio_content = audio_segment.export(
                    format="mp3"
                ).read()
                file_name = audio_file._name
                modified_audio_file = ContentFile(
                    modified_audio_content , name = f"{file_name}.mp3"
                )
                data = request.data.copy()
                data['audio'] = modified_audio_file
                serializer = ChatHistorySerializer(data=data)
                if serializer.is_valid():
                    chat_history = serializer.save()
                    modified_audio_content = None
                    return chat_history
                
            except Exception as E:
                return Response(str(E),status=400)
        else:
            return Response({
                "error":"No audio file found"
            },status=400)