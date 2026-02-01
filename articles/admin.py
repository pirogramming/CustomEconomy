from django.contrib import admin
from .models import Article, Category

# 1. 카테고리 관리 등록
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):  
    list_display = ['id', 'name']

# 2. 기사 관리 등록
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):  
    list_display = ['id', 'category', 'title', 'source', 'published_at']
    search_fields = ['title', 'content']
    list_filter = ['category', 'source']
    
admin.site.register(Article)
admin.site.register(Category)
