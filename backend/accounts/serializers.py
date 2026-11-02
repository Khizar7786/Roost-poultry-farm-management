from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from farms.models import Farm

from .models import Role, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "first_name", "last_name",
            "phone_number", "role", "farm", "is_active_employee",
        ]
        read_only_fields = ["id", "role", "farm"]


class RegisterFarmSerializer(serializers.Serializer):
    """UC-05: Register Farm/Account. A brand-new user provides their own
    details plus a farm name/location; this creates both the Farm and the
    OWNER User in one transaction."""

    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    farm_name = serializers.CharField(max_length=150)
    farm_location = serializers.CharField(max_length=255)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            # UC-05 alt. flow: email already registered -> notify + suggest reset.
            raise serializers.ValidationError(
                "This email is already registered. Try logging in or resetting your password."
            )
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is taken.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        farm_name = validated_data.pop("farm_name")
        farm_location = validated_data.pop("farm_location")
        first_name, _, last_name = full_name.partition(" ")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
            role=Role.OWNER,
        )
        farm = Farm.objects.create(name=farm_name, location=farm_location, owner=user)
        user.farm = farm
        user.save(update_fields=["farm"])
        return user


class RegisterEmployeeSerializer(serializers.Serializer):
    """An existing Owner creates a Farm Employee account
    attached to the owner's farm. Employees never self-register — this
    mirrors "System Admin manages ... user access" and keeps farm
    membership authoritative."""

    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        requesting_user = self.context["request"].user
        full_name = validated_data.pop("full_name")
        first_name, _, last_name = full_name.partition(" ")
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
            phone_number=validated_data.get("phone_number", ""),
            role=Role.EMPLOYEE,
            farm=requesting_user.farm,
        )
