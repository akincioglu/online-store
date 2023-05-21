from rest_framework import serializers
from src.models import User, Category, Product, Cart


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "password", "is_active", "role"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    category_id = serializers.UUIDField(source="category.id")

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "amount_in_stock",
            "price",
            "in_stock",
            "category_id",
        ]

    def create(self, validated_data):
        category_data = validated_data.pop("category", {})
        category_id = category_data.get("id")

        try:
            category = Category.objects.get(id=category_id)
            amount_in_stock = validated_data.get("amount_in_stock", 0)
            validated_data["in_stock"] = amount_in_stock > 0 and True
        except Category.DoesNotExist:
            raise serializers.ValidationError("Invalid category_id")

        validated_data["category"] = category
        return super().create(validated_data)


class CartSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="user.id")
    products = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Product.objects.all(), required=False
    )

    class Meta:
        model = Cart
        fields = ["id", "user_id", "products"]

    def create(self, validated_data):
        products_data = validated_data.pop("products", [])
        user = self.context["request"].user

        cart = Cart.objects.create(user=user)

        for product_data in products_data:
            product = Product.objects.get(id=product_data["id"])
            cart.products.add(product)

        return cart
