from rest_framework import serializers
from PrepWiser.models import Post, Comment
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework import status, permissions
from django.contrib.auth.models import User
from .serializers import UserSerializer
from rest_framework import serializers

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Include the username of the user
    post = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())  # Ensure post is handled correctly
    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'content', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'tags', 'votes', 'comments', 'created_at','created_by']


class PostVoteUpdate(APIView):
    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            post.votes = request.data['votes']
            post.save()
            return Response({'votes': post.votes}, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        except KeyError:
            return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
    
class PostList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        posts = Post.objects.all().order_by('-created_at')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PostDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        serializer = PostSerializer(post)
        return Response(serializer.data)

    def put(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        serializer = PostSerializer(post, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentList(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, post_pk):
        comments = Comment.objects.filter(post_id=post_pk)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, post_pk):
        post = get_object_or_404(Post, pk=post_pk)
        data = request.data.copy()  # Make a mutable copy of request.data
        data['post'] = post_pk  # Ensure post ID is passed correctly
        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save(user=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(request.data)
            print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CommentDetail(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, pk, post_pk):
        comment = get_object_or_404(Comment, pk=pk, post_id=post_pk)
        serializer = CommentSerializer(comment)
        return Response(serializer.data)

    def put(self, request, pk, post_pk):
        comment = get_object_or_404(Comment, pk=pk, post_id=post_pk)
        serializer = CommentSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, post_pk):
        comment = get_object_or_404(Comment, pk=pk, post_id=post_pk)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
