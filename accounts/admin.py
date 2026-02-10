from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Interest, UserInterest
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 1. 목록 화면에서 보여줄 필드 (username 제외)
    list_display = ('email', 'username', 'is_staff')
    
    # 2. 정렬 기준을 email로 변경 (에러 admin.E033 해결)
    ordering = ('email',)
    
    # 3. 상세 수정 화면 설정 (username 필드 제거)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('개인정보', {'fields': ('username',)}),
        ('권한', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('중요 날짜', {'fields': ('last_login', 'date_joined')}),
    )

    # 4. 유저 생성 시 보여줄 필드
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'username'),
        }),
    )

    # 이메일을 아이디로 쓰기 때문에 search_fields도 수정
    search_fields = ('email', 'username')

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type')
    list_filter = ('category_type',)
    search_fields = ('name',)

@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    # "점수판"
    list_display = ('user', 'interest', 'interest_score', 'weakness_score', 'last_viewed_at', 'last_wrong_at')
    # 유저별, 혹은 소분류별로 필터링해서 보기 편하게 설정
    list_filter = ('user', 'interest__category_type')
    search_fields = ('user__username', 'interest__name')