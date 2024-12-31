from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from youtube_transcript_api import YouTubeTranscriptApi
import re
import requests
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from openai import OpenAI
import json
from django.conf import settings
from googleapiclient.discovery import build
import xml.etree.ElementTree as ET

def punctuate_online(text):
    API_ENDPOINT = "http://bark.phon.ioc.ee/punctuator"
    data = {'text': text}
    response = requests.post(url=API_ENDPOINT, data=data)
    return response.text

def get_video_details(video_id):
    
    key=""
    youtube = build('youtube', 'v3', developerKey="")
    request = youtube.videos().list(
        part="snippet",
        id=video_id
    )
    response = request.execute()

    if response['items']:
        title = response['items'][0]['snippet']['title']
        thumbnail_url = response['items'][0]['snippet']['thumbnails']['high']['url']
        video_link = f"https://www.youtube.com/watch?v={video_id}"
        print(title)
        print(thumbnail_url)
        return title, thumbnail_url, video_link
    return None, None, None


# def youtube_service(api_key):
#     return build('youtube', 'v3', developerKey=api_key)

# def get_captions(service, video_id):
#     # Get the list of available caption tracks
#     results = service.captions().list(part='snippet', videoId=video_id).execute()

#     # Check for at least one caption track
#     if results['items']:
#         # Get the first caption track ID
#         caption_id = results['items'][0]['id']
        
#         # Download the caption track
#         request = service.captions().download(
#             id=caption_id,
#             tfmt='ttml'  # Formats the output as TTML (XML-based format that includes timing)
#         )
#         # The response will be a file-like object.
#         # You can handle it as per your requirement.
#         ttml_caption_data = request.execute()

#         print(ttml_caption_data)  # This will print the XML content
#         return ttml_caption_data

#     else:
#         print("No captions found for this video.")

# def parse_ttml(ttml_data):
#     # Parse the TTML XML data
#     root = ET.fromstring(ttml_data)
    
#     # Namespace mapping, may need to adjust based on TTML data
#     ns = {'ttml': 'http://www.w3.org/ns/ttml'}
    
#     # Iterate over paragraph items which contain the timestamps and text
#     for para in root.findall('.//ttml:p', ns):
#         begin = para.get('begin')
#         end = para.get('end')
#         text = ''.join(para.itertext())
#         print(f"Start: {begin}, End: {end}, Text: {text}")




class SummarizerView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data
        video_link = data.get('video_link')
        if not video_link:
            return Response({'error': 'Video link is required'}, status=status.HTTP_400_BAD_REQUEST)

        video_id = video_link.strip().split('?v=')[-1]
        try:
            transcripts = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        textTranscripts = ""
        for t in transcripts:
            text = re.sub("[\(\[].*?[\)\]]", " ", t['text']).replace("-", "")
            text = " ".join(text.splitlines())
            text = re.sub('\s{2,}', ' ', text).strip()

            if len(text.strip()) > 3 and len(text.strip().split(" ")) > 1:
                textTranscripts += text + " "

        punctuatedTranscripts = punctuate_online(textTranscripts)
        parser = PlaintextParser.from_string(punctuatedTranscripts, Tokenizer("english"))
        summarizer = LsaSummarizer()
        summary_sentences = 20
        summary = summarizer(parser.document, summary_sentences)
        summary = '. '.join([str(sentence) for sentence in summary])

        title, thumbnail_url, video_link = get_video_details(video_id)
        if not title:
            return Response({'error': 'Failed to retrieve video details'}, status=status.HTTP_400_BAD_REQUEST)
 
        # service = youtube_service(api_key)
        # ttml_caption_data=get_captions(service, video_id)
        # # Example use inside get_captions function to replace print(ttml_caption_data)
        # parse_ttml(ttml_caption_data)

        client = OpenAI(api_key="")
        prompt = summary + " This is the summary of a video. Rephrase this and make it more technical and expand slightly on the key points. It should be coherent and easily understandable.",
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt= prompt,
            temperature=0.5,
            max_tokens= 3000,    #4096 - len(prompt),
        )
        final_summary = response.choices[0].text

        return Response({
            'video_title': title,
            'thumbnail_url': thumbnail_url,
            'summary': final_summary,
            'video_link':video_link,
            'transcript': punctuatedTranscripts
        }, status=status.HTTP_200_OK)
