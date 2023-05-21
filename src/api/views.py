from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from src.models import Category, Product, Cart
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.shortcuts import get_object_or_404
from rest_framework.permissions import (
    IsAuthenticated,
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from core.permissions import IsAdminUserOrReadOnly
from .serializers import (
    UserSerializer,
    CategorySerializer,
    ProductSerializer,
    CartSerializer,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        if self.request.user.role == "admin":
            return User.objects.all()
        else:
            return User.objects.none()

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def register(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response(
                {"error": "Please provide both username and password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username is already taken."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.create_user(username=username, password=password)
        return Response(
            {"message": "User registered successfully."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                "Inactive users cannot log in.", status=status.HTTP_403_FORBIDDEN
            )

        token = TokenObtainPairSerializer().get_token(user)
        return Response({"token": str(token.access_token)})

    @action(detail=True, methods=["patch"])
    def activate_status(self, request, pk=None):
        if not request.user.is_staff:
            return Response(
                {"detail": "Only admin users can activate or deactivate users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self.get_object()
        is_active = request.data.get("is_active", None)
        if is_active is None:
            return Response(
                {"detail": "Please provide 'is_active' field in the request data."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = is_active
        user.save()

        return Response(
            {"user": user.username, "is_active": user.is_active},
            status=status.HTTP_200_OK,
        )


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminUserOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminUserOrReadOnly]

    def list(self, request, *args, **kwargs):
        category_id = request.query_params.get("category_id")
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.exclude(amount_in_stock=0)

        if category_id:
            queryset = queryset.filter(category_id=category_id)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {
                "detail": "Product deleted successfully.",
                "product": self.serializer_class(instance).data,
            },
            status=status.HTTP_200_OK,
        )


class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAdminUserOrReadOnly]

    @action(detail=False, methods=["DELETE"])
    def clear_all(self, request):
        Cart.objects.all().delete()
        return Response({"message": "All carts cleared."})

    def create(self, request, *args, **kwargs):
        user = request.user
        if str(user.id) != request.data.get("user_id"):
            return Response(
                {"detail": "Invalid user_id. User does not match the request user."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_cart = Cart.objects.filter(user=user).first()

        if existing_cart:
            serializer = self.get_serializer(existing_cart)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=True, methods=["post"])
    def add_to_cart(self, request, pk=None):
        cart = self.get_object()
        product_ids = request.data.get("products", [])

        products = Product.objects.filter(id__in=product_ids)

        cart.products.add(*products)

        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def products(self, request, pk=None):
        try:
            cart = self.get_object()
            products = cart.products.all()
            serializer = ProductSerializer(products, many=True)
            return Response(serializer.data)
        except Cart.DoesNotExist:
            return Response(
                {"detail": "Cart not found."}, status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=["delete"])
    def remove_from_cart(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get("product_id", None)

        if not product_id:
            return Response(
                {"detail": "Please provide 'product_id' field in the request data."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        cart.products.remove(product)
        return Response(
            {"detail": "Product removed from cart.", "product_id": product_id},
            status=status.HTTP_204_NO_CONTENT,
        )
