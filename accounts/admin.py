from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 1. 목록 화면에서 보여줄 필드 (username 제외)
    list_display = ('email', 'nickname', 'name', 'is_staff')
    
    # 2. 정렬 기준을 email로 변경 (에러 admin.E033 해결)
    ordering = ('email',)
    
    # 3. 상세 수정 화면 설정 (username 필드 제거)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('개인정보', {'fields': ('nickname', 'name', 'age', 'job')}),
        ('권한', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('중요 날짜', {'fields': ('last_login', 'date_joined')}),
    )

    # 4. 유저 생성 시 보여줄 필드
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'nickname', 'name', 'age', 'job'),
        }),
    )

    # 이메일을 아이디로 쓰기 때문에 search_fields도 수정
    search_fields = ('email', 'nickname')