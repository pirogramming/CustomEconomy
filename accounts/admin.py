from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Interest, UserInterest

# Register your models here.

class UserInterestInline(admin.TabularInline):
    model = UserInterest
    extra = 0
    readonly_fields = ('interest', 'weakness_score')

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 1. 목록에 표시할 필드 (username 대신 email이나 실제 필드명 사용)
    # 하은님 모델에 email 필드가 있다면 아래와 같이 설정하세요.
    list_display = ('email', 'level', 'total_score', 'is_staff')
    
    # 2. 정렬 기준 설정 (에러 E033 해결)
    ordering = ('email',) 

    # 3. 상세 페이지 설정 (에러 방지를 위해 필수 필드만 먼저 구성)
    # UserAdmin.fieldsets를 그대로 쓰면 존재하지 않는 필드를 참조할 수 있으므로 직접 정의합니다.
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('개인정보', {'fields': ()}), # 이름이나 다른 필드가 있다면 추가
        ('권한', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('경제 학습 정보', {'fields': ('level', 'total_score', 'level_score')}),
    )
    
    # 필수 설정들
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password'),
        }),
    )
    search_fields = ('email',)
    inlines = [UserInterestInline]

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name',)