from rest_framework import serializers
from PrepWiser.models import User
from PrepWiser.models import Roadmap, RoadmapStepStatus

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name')
        )
        return user

class ResourceStatusSerializer(serializers.Serializer):
    title = serializers.CharField()
    checked = serializers.BooleanField(default=False)

class RoadmapStepStatusSerializer(serializers.ModelSerializer):
    resource_status = ResourceStatusSerializer(many=True)
    class Meta:
        model = RoadmapStepStatus
        fields = ['step_number', 'resource_status']

class RoadmapSerializer(serializers.ModelSerializer):
    status = RoadmapStepStatusSerializer(many=True, read_only=True, source='roadmapstepstatus_set')

    class Meta:
        model = Roadmap
        fields = ['id', 'user', 'skill', 'roadmap_data', 'created_at', 'status']
        read_only_fields = ['id', 'user', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        roadmap = Roadmap.objects.create(user=user, **validated_data)
        return roadmap

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        steps = representation['roadmap_data']['steps']
        status = {item['step_number']: item['resource_status'] for item in representation['status']}

        for step in steps:
            step_number = step['step_number']
            if step_number in status:
                resource_status = status[step_number]
                for resource in step['resources']:
                    matching_status = next((item for item in resource_status if item['title'] == resource['title']), None)
                    if matching_status:
                        resource['checked'] = matching_status.get('checked', False)
                    else:
                        resource['checked'] = False
            else:
                for resource in step['resources']:
                    resource['checked'] = False

        return representation