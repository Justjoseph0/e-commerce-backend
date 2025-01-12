from rest_framework.pagination import PageNumberPagination


class ProductPagination(PageNumberPagination):
    page_size = 15

class OrderPagination(PageNumberPagination):
    page_size = 8

class UserPagination(PageNumberPagination):
    page_size = 10
