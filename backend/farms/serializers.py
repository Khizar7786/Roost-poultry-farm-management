from rest_framework import serializers

from .models import Farm, Shed


class ShedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shed
        fields = ["id", "name", "capacity"]


class FarmSerializer(serializers.ModelSerializer):
    sheds = ShedSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    employee_count = serializers.SerializerMethodField()

    class Meta:
        model = Farm
        fields = ["id", "name", "location", "owner_name", "created_at", "sheds", "employee_count"]
        read_only_fields = fields

    def get_employee_count(self, obj):
        return obj.members.filter(role="EMPLOYEE", is_active_employee=True).count()
