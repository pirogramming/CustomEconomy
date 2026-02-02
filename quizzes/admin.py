from django.contrib import admin
from .models import Quiz, QuizChoice, QuizResult
# Register your models here.

class QuizChoiceInline(admin.TabularInline):
    """
    퀴즈 상세 페이지 안에서 선택지들을 바로 보여주고 수정하게 함
    """
    model = QuizChoice
    extra = 4  # 기본으로 보여줄 선택지 개수

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """
    퀴즈 관리 설정
    """
    list_display = ('id', 'type', 'category', 'question', 'article') # 목록에 보여질 항목
    list_filter = ('type', 'category') # 우측 필터 기능
    search_fields = ('question', 'explanation') # 검색창 기능
    inlines = [QuizChoiceInline] # 퀴즈 수정 페이지에서 선택지 같이 보기

@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    """
    유저들이 푼 결과 관리
    """
    list_display = ('user', 'quiz', 'selected_answer', 'is_correct', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('user__username', 'quiz__question')