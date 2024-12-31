from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from openai import OpenAI
import os, json
from django.conf import settings
from PrepWiser.models import Roadmap, RoadmapStepStatus
from django.contrib.auth.models import User
from .serializers import RoadmapSerializer, RoadmapStepStatusSerializer

class SkillRoadmapView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # permission_classes = []

    def get(self, request):
        try:
            roadmaps = Roadmap.objects.filter(user_id=request.user.id)
            serializer = RoadmapSerializer(roadmaps, many=True)
            # print("inside get call")
            # print("Roadmaps QuerySet:", roadmaps)
            # print("Serialized Data:", serializer.data)
            return Response({'roadmaps': serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            # print(str(e))
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def post(self, request):
        skill = request.data.get('skill', None)
        
        if not skill:
            return Response({'error': 'Skill parameter is missing.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = f"""
            Create a detailed roadmap for learning {skill} with atleast 8 steps. The roadmap should be structured as a JSON object where each step in the learning process is described. For each step, include the step number, the content describing what should be learned at that step, and any relevant resources such as links to courses, books, or articles. Each resource should be accompanied by a brief title (3 to 5 words) describing the content of the link. The roadmap should comprehensively cover key topics and provide a logical progression path. Only include resources that are widely recognized and verifiably existent, such as well-known courses, books, or articles. The roadmap should comprehensively cover key topics and provide a logical progression path. Please avoid creating fictitious links; only include links that are known to be valid and accessible. Aim for at least 8 steps but it may extend further based on the complexity of the skill. Give it in minified JSON format. Here's the format I want: {{"steps":[{{"step_number":1,"step_content":"Introduction to {skill}, understanding the basics and fundamental concepts.","resources":[{{"title":"Introductory Course","link":"Link to an introductory course on {skill}"}},{{"title":"Foundational Book","link":"Link to a foundational book on {skill}"}},{{"title":"Basic Concepts Article","link":"Link to an informative article on the basics of {skill}"}}]}},{{"step_number":2,"step_content":"Intermediate concepts in {skill}, building upon the basics by exploring more complex topics.","resources":[{{"title":"Intermediate Course","link":"Link to an intermediate course on {skill}"}},{{"title":"Detailed Guide","link":"Link to a detailed guide on intermediate concepts of {skill}"}},{{"title":"Case Study","link":"Link to a case study related to {skill}"}}]}},{{"step_number":3,"step_content":"Advanced {skill}, mastering the skill with advanced techniques and applications.","resources":[{{"title":"Advanced Course","link":"Link to an advanced course on {skill}"}},{{"title":"Comprehensive Book","link":"Link to a comprehensive book covering advanced topics in {skill}"}},{{"title":"Research Papers","link":"Link to industry research papers on {skill}"}}]}}]}}"""
            response = client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                temperature=0.5,
                max_tokens=4096 - len(prompt)
            )
            
            roadmap_text = response.choices[0].text.strip()
            print("roadmap_text", roadmap_text)
            roadmap_data = json.loads(roadmap_text)
            print("roadmap_data", roadmap_data)
            serializer = RoadmapSerializer(data={'skill': skill, 'roadmap_data': roadmap_data}, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                print("saved in database")
                return Response({'message': 'Roadmap generated successfully', 'roadmap': serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(str(e))
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SaveRoadmapProgressView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # permission_classes = []

    def post(self, request):
        roadmap_id = request.data.get('roadmap_id')
        steps = request.data.get('steps')

        try:
            roadmap = Roadmap.objects.get(id=roadmap_id, user=request.user)
            
            for step in steps:
                step_number = step.get('step_number')
                resource_status = step.get('resource_status')

                roadmap_step_status, created = RoadmapStepStatus.objects.get_or_create(
                    roadmap=roadmap,
                    step_number=step_number,
                    defaults={'resource_status': resource_status}
                )

                if not created:
                    roadmap_step_status.resource_status = resource_status
                    roadmap_step_status.save()

            return Response({'message': 'Progress saved successfully'}, status=status.HTTP_200_OK)
        except Roadmap.DoesNotExist:
            return Response({'error': 'Roadmap not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class UserRoadmapsView(APIView):
#     # permission_classes = [permissions.IsAuthenticated]
#     permission_classes = []

#     def get(self, request):
#         roadmaps = Roadmap.objects.filter(user=request.user)
#         serializer = RoadmapSerializer(roadmaps, many=True)
#         return Response({'roadmaps': serializer.data}, status=status.HTTP_200_OK)
